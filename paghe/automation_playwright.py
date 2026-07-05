"""Utility Playwright per automazione procedure web INPS."""

import logging
import os

logger = logging.getLogger(__name__)
import time
import re
import base64
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout


def _ms(t):
    """Converte secondi in millisecondi per Playwright."""
    return int(t * 1000)


def _page_info(page):
    """Restituisce URL e titolo della pagina per debug."""
    try:
        return f'URL: {page.url}, Titolo: "{page.title()}"'
    except Exception:
        return 'URL/Titolo: non disponibile (pagina chiusa o in navigazione)'


def avvia_driver(chromedriver_exe=None, headless=False, window_size=None, download_dir=None, minimized=False):
    """Avvia Chromium via Playwright.

    Playwright usa un event loop asincrono interno. Django interpreta la presenza
    di un event loop come contesto async e solleva SynchronousOnlyOperation.
    `DJANGO_ALLOW_ASYNC_UNSAFE` disabilita questo controllo per il thread corrente.

    Args:
        chromedriver_exe: ignorato (Playwright usa il proprio chromium).
        headless: non usato (la minimizzazione è gestita via CDP dopo login).
        window_size: tuple (larghezza, altezza).
        download_dir: path per download automatici. Se None, nessuna preferenza.
        minimized: non usato (la minimizzazione è gestita via CDP dopo login).

    Returns:
        tuple: (playwright, browser, context, page) — da passare come 'driver' nelle altre funzioni.
    """
    os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
    p = sync_playwright().start()
    launch_kw = {'headless': False}
    try:
        browser = p.chromium.launch(**launch_kw)
    except Exception:
        logger.info('[Playwright] Browser Chromium non disponibile. Installazione in corso...')
        import sys, subprocess
        subprocess.run(
            [sys.executable, '-m', 'playwright', 'install', 'chromium'],
            check=True, stdout=sys.stdout, stderr=sys.stderr
        )
        logger.info('[Playwright] Chromium installato. Riavvio...')
        p.stop()
        p = sync_playwright().start()
        browser = p.chromium.launch(**launch_kw)

    context_kw = {}
    if window_size:
        context_kw['viewport'] = {'width': window_size[0], 'height': window_size[1]}
    if download_dir:
        os.makedirs(download_dir, exist_ok=True)

    if not context_kw.get('viewport'):
        context_kw['viewport'] = {'width': 960, 'height': 1080}

    context = browser.new_context(**context_kw)
    page = context.new_page()

    logger.info(f'[PAGOPA] Browser Chromium avviato. Chromium path check: OK')
    # wrapper: (playwright, browser, context, page)
    return (p, browser, context, page)


def chiudi_driver(driver, timeout=3):
    """Chiude Chromium in modo sicuro.

    Args:
        driver: tuple (playwright, browser, context, page) restituita da avvia_driver.
    """
    if driver is None:
        logger.info('[PAGOPA] chiudi_driver: driver None, nulla da chiudere')
        return
    try:
        _, browser, context, page = driver
        logger.info(f'[PAGOPA] Chiusura context...')
        context.close()
        logger.info(f'[PAGOPA] Chiusura browser...')
        browser.close()
        logger.info(f'[PAGOPA] Browser chiuso.')
    except Exception as e:
        logger.info(f'[PAGOPA] ERRORE chiusura browser: {e}')
    try:
        p = driver[0]
        logger.info(f'[PAGOPA] Arresto Playwright...')
        p.stop()
        logger.info(f'[PAGOPA] Playwright arrestato.')
    except Exception as e:
        logger.info(f'[PAGOPA] ERRORE arresto Playwright: {e}')


def _estrai_page(driver):
    """Estrae l'ultima pagina aperta nel context (nuove finestre/tab incluse)."""
    context = driver[2]
    pages = context.pages
    return pages[-1] if pages else driver[3]


def _estrai_context(driver):
    """Estrae il context dal wrapper driver."""
    return driver[2]


def _estrai_browser(driver):
    """Estrae il browser dal wrapper driver."""
    return driver[1]


def _by_to_sel(by, valore):
    """Converte (By, valore) in selettore CSS o XPath per Playwright."""
    if by == 'id' or (hasattr(by, '__str__') and str(by) == 'id'):
        return f'#{valore}'
    if by == 'name' or (hasattr(by, '__str__') and str(by) == 'name'):
        return f'[name="{valore}"]'
    if by == 'css selector' or (hasattr(by, '__str__') and 'css' in str(by)):
        return valore
    if by == 'xpath' or (hasattr(by, '__str__') and 'xpath' in str(by)):
        return f'xpath={valore}'
    if by == 'tag name' or (hasattr(by, '__str__') and 'tag' in str(by)):
        return valore
    return valore


def attendi_elemento(driver, by, valore, timeout=10):
    """Attende che un elemento sia presente nel DOM.

    Returns:
        ElementHandle trovato.
    """
    page = _estrai_page(driver)
    sel = _by_to_sel(by, valore)
    return page.wait_for_selector(sel, timeout=_ms(timeout), state='attached')


def attendi_e_click(driver, by, valore, timeout=10):
    """Attende un elemento e ci clicca sopra."""
    page = _estrai_page(driver)
    sel = _by_to_sel(by, valore)
    el = page.wait_for_selector(sel, timeout=_ms(timeout), state='attached')
    if el:
        el.click()
    return el


def attendi_e_scrivi(driver, by, valore, testo, timeout=10):
    """Attende un elemento, lo pulisce e scrive il testo.

    Returns:
        ElementHandle modificato.
    """
    page = _estrai_page(driver)
    sel = _by_to_sel(by, valore)
    el = page.wait_for_selector(sel, timeout=_ms(timeout), state='attached')
    if el:
        el.fill('')
        if testo:
            el.fill(testo)
    return el


def cattura_screenshot(driver, step_name=''):
    """Cattura screenshot della pagina corrente e restituisce bytes PNG + metadati.

    Returns:
        dict con chiavi: png (bytes), url (str), title (str), step_name (str), ts (str).
    """
    page = _estrai_page(driver)
    try:
        png_bytes = page.screenshot(full_page=True)
    except Exception:
        try:
            png_bytes = page.screenshot()
        except Exception:
            png_bytes = b''
    return {
        'png': png_bytes,
        'url': page.url,
        'title': page.title() or '',
        'step_name': step_name,
        'ts': time.strftime('%Y-%m-%d %H:%M:%S'),
    }


def cattura_elemento_captcha(driver):
    """Screenshot solo dell'elemento CAPTCHA (immagine) e restituisce Base64."""
    import base64
    page = _estrai_page(driver)
    try:
        selettori = [
            'img[alt*="captcha" i]',
            'img[alt*="CAPTGRAPH" i]',
            'img#captcha_image',
            'img[src*="captcha"]',
            'img[src*="kaptcha"]',
            'img[src*="captchgraph"]',
            'img[src*="Kaptcha"]',
        ]
        captcha_el = None
        for sel in selettori:
            el = page.locator(sel).first
            if el.is_visible():
                captcha_el = el
                break
        if not captcha_el:
            tutte = page.locator('img')
            count = tutte.count()
            for i in range(count):
                el = tutte.nth(i)
                box = el.bounding_box()
                if box and box['width'] >= 100 and box['height'] >= 30:
                    captcha_el = el
                    break
        if not captcha_el:
            logger.warning('[PAGOPA] Elemento CAPTCHA non trovato.')
            return None
        captcha_el.wait_for(state='visible', timeout=5000)
        png_bytes = captcha_el.screenshot()
        return base64.b64encode(png_bytes).decode('utf-8')
    except Exception as e:
        logger.exception("Errore in cattura_elemento_captcha: %s", e)
        return None


def minimizza_finestra(driver):
    """Minimizza la finestra Chromium via CDP."""
    try:
        page = _estrai_page(driver)
        cdp = page.context.new_cdp_session(page)
        window_id = cdp.send("Browser.getWindowForTarget")["windowId"]
        cdp.send("Browser.setWindowBounds", {
            "windowId": window_id,
            "bounds": {"windowState": "minimized"}
        })
        logger.info('[Playwright] Finestra minimizzata via CDP')
    except Exception:
        logger.exception("Errore minimizzazione finestra")


def salva_debug_step(driver, step_name='', cartella=None):
    """Salva HTML e analisi elementi della pagina per debug."""
    page = _estrai_page(driver)
    if cartella is None:
        cartella = os.path.join(os.path.dirname(__file__), '..', 'media', 'pagopa', 'DEBUG')
    try:
        os.makedirs(cartella, exist_ok=True)
        return  # DEBUG su disco disattivato (mantieni SCREENSHOT/)
        ts = time.strftime('%Y%m%d_%H%M%S')
        prefix = f'{ts}_{step_name}' if step_name else ts

        # HTML
        html = page.content()
        html_path = os.path.join(cartella, f'{prefix}.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)

        # Analisi elementi
        info = {
            'url': page.url,
            'title': page.title() or '',
            'step': step_name,
            'ts': time.strftime('%Y-%m-%d %H:%M:%S'),
            'n_pagine_context': len(_estrai_context(driver).pages) if _estrai_context(driver) else 0,
        }
        try:
            inputs = page.evaluate("""(function() {
                const els = document.querySelectorAll('input[type="image"], input[type="submit"], button, a');
                return Array.from(els).map(el => ({
                    tag: el.tagName,
                    type: el.type || null,
                    name: el.name || null,
                    alt: el.alt || null,
                    title: el.title || null,
                    src: el.src || null,
                    href: el.href || null,
                    onclick: el.getAttribute('onclick') || null,
                    outer: el.outerHTML.substring(0, 500)
                }));
            })()""")
            info['elementi_interattivi'] = inputs
        except Exception as e:
            info['elementi_interattivi'] = f'errore: {e}'

        try:
            forms = page.evaluate("""(function() {
                return Array.from(document.forms).map(f => ({
                    action: f.action,
                    method: f.method,
                    target: f.target,
                    id: f.id,
                    name: f.name,
                    n_inputs: f.elements.length
                }));
            })()""")
            info['forms'] = forms
        except Exception as e:
            info['forms'] = f'errore: {e}'

        json_path = os.path.join(cartella, f'{prefix}.json')
        import json
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)

        logger.info(f'[DEBUG] Salvato: {html_path}')
        logger.info(f'[DEBUG] Salvato: {json_path}')
        return html_path
    except Exception as e:
        logger.warning(f'[DEBUG] ERRORE salvataggio debug: {e}')
        return None


def pagopa_login(driver, url, cf_datore, cod_rapporto, timeout=10, delay=0.5):
    """Step 1: Naviga al sito INPS PagoPA e compila CF + Codice Rapporto."""
    page = _estrai_page(driver)
    logger.info(f'[PAGOPA] 🌐 Navigo a: {url}')
    page.goto(url)
    logger.info(f'[PAGOPA] ✅ Pagina caricata. {_page_info(page)}')

    # Retry: se la pagina INPS è bloccata su cortesia/404/redirect,
    # riprova la navigazione fino a quando il form di login appare
    for tentativo in range(4):
        if page.locator('[name="codiceFiscaleUtente"]').is_visible(timeout=3000):
            break
        current_url = page.url
        if url not in current_url:
            logger.info(f'[PAGOPA] ⏳ Redirect imprevisto (tentativo {tentativo+1}/4): {current_url}')
            page.goto(url)
            page.wait_for_timeout(2000)
        else:
            page.wait_for_timeout(2000)
    page.wait_for_timeout(_ms(max(delay, 0.5)))

    logger.info(f'[PAGOPA] ✏️ Compilo campo [codiceFiscaleUtente] = "{cf_datore}"')
    attendi_e_scrivi(driver, 'name', 'codiceFiscaleUtente', cf_datore, timeout)
    logger.info(f'[PAGOPA] ✏️ Compilo campo [codicePraticaUtente] = "{cod_rapporto}"')
    attendi_e_scrivi(driver, 'name', 'codicePraticaUtente', cod_rapporto, timeout)

    page.keyboard.press('Tab')
    page.evaluate('window.focus()')
    logger.info(f'[PAGOPA] ⏹️ Login compilato, focus spostato su CAPTCHA. {_page_info(page)}')


def pagopa_prosegui_dopo_captcha(driver, timeout=120, delay=0.5):
    """Step 2: Inietta listener Ctrl+Invio nella pagina Chrome e attende
    che l'utente prema la combinazione per sottomettere il CAPTCHA.

    Returns:
        True se il submit è stato rilevato, False altrimenti.
    """
    page = _estrai_page(driver)
    context = _estrai_context(driver)
    n_pagine_iniziali = len(context.pages)
    logger.info(f'[PAGOPA] Attesa Ctrl+Invio. Pagine iniziali={n_pagine_iniziali}, timeout={timeout}s. {_page_info(page)}')

    # Listener Ctrl+Invio — clicca il bottone di submit senza preventDefault,
    # così se il listener non aggancia, il form può inviarsi naturalmente.
    page.evaluate("""
        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.key === 'Enter') {
                var el = document.getElementById('submitLogin1');
                if (el) { el.click(); }
                var btn = document.querySelector(
                    'input[type="image"], input[type="submit"], button[type="submit"]'
                );
                if (btn) btn.click();
            }
        });
        window._pagopaListenerInjected = true;
    """)
    injected = page.evaluate("window._pagopaListenerInjected")
    logger.info(f'[PAGOPA] Listener Ctrl+Invio: injected={injected}')

    current_url = page.url
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            # Nuova finestra/tab aperta (es. INPS apre nuova pagina dopo login)
            pagine_attuali = len(context.pages)
            if pagine_attuali > n_pagine_iniziali:
                logger.info(f'[PAGOPA] Rilevata nuova finestra/tab! Pagine: {n_pagine_iniziali} → {pagine_attuali}')
                return True

            # Cambio URL — solo per pagine post-login valide (non loginUtente.do)
            if page.url != current_url:
                if any(k in page.url for k in ['caricaTrimestre', 'gestioneCarrello', 'visualizzaCarrello', 'generaAvvisi']):
                    logger.info(f'[PAGOPA] URL cambiato → pagine post-login! {current_url} → {page.url}')
                    return True
                logger.info(f'[PAGOPA] URL cambiato (attesa ancora): {current_url} → {page.url}')
                current_url = page.url

            # Elementi che indicano l'avvenuta navigazione alla pagina successiva
            for sel in [
                'xpath=//input[@type="image" and @alt="Visualizza dati del bollettino"]',
                '#sceltaTrimestre',
                '#oreRetribuite',
            ]:
                try:
                    el = page.wait_for_selector(sel, timeout=1000, state='attached')
                    if el:
                        logger.info(f'[PAGOPA] Elemento trovato: {sel}')
                        return True
                except Exception:
                    logger.debug("[PAGOPA] wait_for_selector fallito nel loop captcha")
                    continue
        except Exception as ex:
            logger.warning(f'[PAGOPA] Eccezione nel loop: {ex}')
        page.wait_for_timeout(_ms(delay))

    # Grace period finale: se la navigazione è avvenuta subito dopo lo scadere del timeout,
    # diamo 2 secondi extra per catturarla
    logger.info(f'[PAGOPA] Timeout scaduto. Grace period di 2s... {_page_info(page)}')
    try:
        page.wait_for_timeout(2000)
        pagine_attuali = len(context.pages)
        if pagine_attuali > n_pagine_iniziali:
            logger.info(f'[PAGOPA] Grace: nuova finestra/tab! {n_pagine_iniziali} → {pagine_attuali}')
            return True
        if page.url != current_url and any(k in page.url for k in ['caricaTrimestre', 'gestioneCarrello', 'visualizzaCarrello', 'generaAvvisi']):
            logger.info(f'[PAGOPA] Grace: URL cambiato verso pagina post-login! {current_url} → {page.url}')
            return True
        for sel in [
            'xpath=//input[@type="image" and @alt="Visualizza dati del bollettino"]',
            '#sceltaTrimestre',
            '#oreRetribuite',
        ]:
            try:
                if page.wait_for_selector(sel, timeout=1000, state='attached'):
                    logger.info(f'[PAGOPA] Grace: elemento trovato: {sel}')
                    return True
            except Exception:
                logger.debug("[PAGOPA] Grace period wait_for_selector fallito")
                continue
    except Exception as ex:
        logger.warning(f'[PAGOPA] Grace period eccezione: {ex}')

    logger.info(f'[PAGOPA] CTRL+INVIO NON RILEVATO. {_page_info(page)}')
    return False


def pagopa_inserisci_captcha(driver, captcha_text, timeout=120, delay=0.5):
    """Inserisce il testo CAPTCHA nel campo input e clicca submit (background mode)."""
    page = _estrai_page(driver)
    try:
        # Aspetta che l'input CAPTCHA appaia nel DOM (non serve visibile)
        page.wait_for_selector('input[name="captcha"]', timeout=_ms(15))
        captcha_input = page.locator('input[name="captcha"]')
        if captcha_input.count() == 0:
            # Debug: logga tutti gli input visibili
            inputs = page.eval_on_selector_all('input', 'els => els.map(e => ({name: e.name, id: e.id, type: e.type, placeholder: e.placeholder, className: e.className}))')
            logger.warning('[PAGOPA] Campo CAPTCHA non trovato. Input sulla pagina: %s', inputs)
            return False
        captcha_input.first.fill(captcha_text)
        logger.info('[PAGOPA] CAPTCHA scritto: "%s"', captcha_text)
        time.sleep(delay)

        # Submit: cerca il pulsante di login INPS
        submit_sel = 'input#submitLogin1, input[type="submit"], button[type="submit"], input[type="image"]'
        submit = page.locator(submit_sel).first
        if submit.count() > 0:
            submit.click()
            logger.info('[PAGOPA] Click su pulsante submit')
        else:
            page.keyboard.press('Control+Enter')
            logger.info('[PAGOPA] Submit via Ctrl+Enter')

        timeout_ms = timeout * 1000
        page.wait_for_load_state('networkidle', timeout=timeout_ms)

        # Se il campo è ancora visibile, il CAPTCHA era errato
        if page.locator('input[name="captcha"]').is_visible(timeout=2000):
            logger.warning('[PAGOPA] CAPTCHA errato — ancora sulla pagina di login')
            return False
        return True
    except Exception as e:
        logger.exception("Errore in pagopa_inserisci_captcha: %s", e)
        return False


def pagopa_visualizza_bollettino(driver, timeout=10):
    """Step 3: Clicca 'Visualizza dati del bollettino' e attende
    sceltaTrimestre (o pagina già oltre)."""
    page = _estrai_page(driver)
    logger.info(f'[PAGOPA] 👁️ Visualizza bollettino. {_page_info(page)}')
    try:
        click_xpath = "//input[@type='image' and @alt='Visualizza dati del bollettino']"
        logger.info(f'[PAGOPA] 🔍 Cerco pulsante: xpath="{click_xpath}"')
        attendi_e_click(driver, 'xpath', click_xpath, timeout)
        logger.info(f'[PAGOPA] 👆 Cliccato "Visualizza dati del bollettino"')
    except Exception as e:
        logger.warning(f'[PAGOPA] ⏭️ "Visualizza dati" non trovato (forse già oltre): {e}')
    page = _estrai_page(driver)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            page.wait_for_selector('#sceltaTrimestre', timeout=2000, state='attached')
            logger.info(f'[PAGOPA] Trovato #sceltaTrimestre. {_page_info(page)}')
            return True
        except PwTimeout:
            pass
        try:
            page.wait_for_selector('#oreRetribuite', timeout=2000, state='attached')
            logger.info(f'[PAGOPA] Trovato #oreRetribuite. {_page_info(page)}')
            return True
        except PwTimeout:
            pass
        page.wait_for_timeout(500)
    logger.info(f'[PAGOPA] TIMEOUT: #sceltaTrimestre o #oreRetribuite non trovati. {_page_info(page)}')
    return False


def pagopa_seleziona_trimestre(driver, trimestre, anno, timeout=10):
    """Step 3b: Imposta Trimestre e Anno via JS (NON invia il form)."""
    page = _estrai_page(driver)
    logger.info(f'[PAGOPA] 📅 Selezione trimestre. Richiesto: {trimestre}/{anno}. {_page_info(page)}')

    trimestre_numero = int(
        trimestre.replace('Q', '')
    ) if isinstance(trimestre, str) and trimestre.startswith('Q') else int(trimestre)
    anno_int = int(anno)

    # Se già sulla pagina oreRetribuite, salta
    try:
        page.wait_for_selector('#oreRetribuite', timeout=2000, state='attached')
        logger.info(f'[PAGOPA] ⏭️ Già sulla pagina #oreRetribuite. Skipo selezione trimestre.')
        return True
    except PwTimeout:
        pass

    logger.info(f'[PAGOPA] ⏳ Attesa #sceltaTrimestre...')
    try:
        page.wait_for_selector('#sceltaTrimestre', timeout=_ms(timeout), state='attached')
        logger.info(f'[PAGOPA] ✅ #sceltaTrimestre trovato.')
    except PwTimeout:
        logger.info(f'[PAGOPA] ❌ TIMEOUT: #sceltaTrimestre non trovato.')
        return False

    try:
        js_code = "(function() { var elTrim = document.getElementById('trimestreRetribuzione'); var elAnno = document.getElementById('anno'); var form = document.getElementById('sceltaTrimestre'); var report = {}; if (elTrim) { report.trimBefore = elTrim.value; } if (elAnno) { report.annoBefore = elAnno.value; } if (elTrim) { elTrim.value = '%s'; elTrim.dispatchEvent(new Event('change', {bubbles: true})); elTrim.dispatchEvent(new Event('input', {bubbles: true})); } if (elAnno) { elAnno.value = '%s'; elAnno.dispatchEvent(new Event('change', {bubbles: true})); elAnno.dispatchEvent(new Event('input', {bubbles: true})); } if (elTrim) { report.trimAfter = elTrim.value; } if (elAnno) { report.annoAfter = elAnno.value; } report.formFound = !!form; return JSON.stringify(report); })()" % (str(trimestre_numero), str(anno_int))
        result = page.evaluate(js_code)
        logger.info(f'[PAGOPA] 🔄 JS sceltaTrimestre: {result}')
        page.wait_for_timeout(500)
    except Exception as e:
        logger.warning(f'[PAGOPA] ❌ ERRORE JS sceltaTrimestre: {e}')
        return False

    logger.info(f'[PAGOPA] ✅ Trimestre impostato: Q{trimestre_numero}/{anno} (no submit). {_page_info(page)}')
    return True


def _scansiona_pagine(context, url_substring=None, selector=None):
    """Cerca in TUTTE le pagine del context quella con URL/selector match.

    Returns:
        (page, match_type): pagina trovata e tipo match ('url'|'selector'), oppure (None, None).
    """
    for p in context.pages:
        try:
            p_url = p.evaluate('location.href')
        except Exception:
            p_url = ''
        try:
            if url_substring and url_substring in p_url.lower():
                return p, 'url'
            if selector and p.query_selector(selector):
                return p, 'selector'
        except Exception:
            logger.debug("[PAGOPA] Scansione pagina fallita")
            continue
    return None, None


def pagopa_conferma_trimestre(driver, timeout=10):
    """Step 3c: Invia il form sceltaTrimestre e attende la pagina oreRetribuite.

    Scansiona TUTTE le pagine del context invece di affidarsi a _estrai_page(),
    perché il form submit può aprire una nuova tab (target="_blank").
    """
    import time as _time
    context = _estrai_context(driver)
    page = _estrai_page(driver)
    logger.info(f'[PAGOPA] 📤 Conferma trimestre (invio form). {_page_info(page)}')

    # Tentativo 1: submit via JavaScript
    try:
        result = page.evaluate("(function() { var form = document.getElementById('sceltaTrimestre'); if (form) { form.submit(); return 'submitted'; } return 'form_not_found'; })()")
        logger.info(f'[PAGOPA] 📨 Submit JS: {result}')
    except Exception as e:
        logger.warning(f'[PAGOPA] ❌ ERRORE submit JS: {e}')

    # Loop attesa: scansiona TUTTE le pagine a ogni giro
    deadline = _time.time() + timeout
    navigato = False
    pagina_target = None
    click_nativo_tentato = False
    attesa_dopo_click = False
    while _time.time() < deadline:
        # 1) Scansiona tutte le pagine per #oreRetribuite
        pagina_target, match = _scansiona_pagine(context, selector='#oreRetribuite')
        if pagina_target:
            logger.info(f'[PAGOPA] ✅ #oreRetribuite trovato in una pagina. {_page_info(pagina_target)}')
            return True

        # 2) Scansiona tutte le pagine per visualizzaCarrello
        pagina_target, match = _scansiona_pagine(context, url_substring='visualizzacarrello')
        if pagina_target:
            logger.info(f'[PAGOPA] ✅ visualizzaCarrello rilevato: {pagina_target.url[:150]}')
            navigato = True
            page = pagina_target
            break

        # 3) Scansiona tutte le pagine per caricaPagamentoTrimestre (dopo submit JS)
        pagina_target, match = _scansiona_pagine(context, url_substring='caricapagamentotrimestre')
        if pagina_target:
            logger.info(f'[PAGOPA] ✅ caricaPagamentoTrimestre rilevato: {pagina_target.url[:150]}')
            navigato = True
            page = pagina_target
            break

        # 4) Click nativo fallback dopo 4s se nessuna pagina è navigata
        if not click_nativo_tentato and (_time.time() > deadline - timeout + 4):
            logger.info(f'[PAGOPA] 🔄 Submit JS non basta. Provo click nativo su input type="image"...')
            click_nativo_tentato = True
            pagina_form, _ = _scansiona_pagine(context, selector='#sceltaTrimestre')
            if not pagina_form:
                pagina_form = _estrai_page(driver)
            try:
                pagina_form.evaluate("(function() { var imgs = document.querySelectorAll('#sceltaTrimestre input[type=\"image\"]'); if (imgs.length > 0) { imgs[imgs.length-1].scrollIntoView(); return 'found ' + imgs.length; } return 'no_image_input'; })()")
                for sel in [
                    '#sceltaTrimestre input[type="image"]',
                    'xpath=//*[@id="sceltaTrimestre"]//input[@type="image"]',
                ]:
                    try:
                        el = pagina_form.query_selector(sel)
                        if el and el.is_visible():
                            logger.info(f'[PAGOPA] 👆 Clicco nativamente: {sel}')
                            el.click(timeout=5000)
                            logger.info(f'[PAGOPA] ✅ Click nativo eseguito.')
                            attesa_dopo_click = True
                            break
                    except Exception:
                        logger.debug("[PAGOPA] Click nativo selettore fallito in conferma_trimestre")
                        continue
            except Exception as e:
                logger.warning(f'[PAGOPA] ❌ Click nativo fallito: {e}')

        # 5) Dopo click nativo, attesa breve per permettere navigazione
        if attesa_dopo_click:
            _time.sleep(0.5)
            attesa_dopo_click = False
        else:
            page.wait_for_timeout(500)

    if not navigato:
        pagina_err = _estrai_page(driver)
        logger.info(f'[PAGOPA] ❌ TIMEOUT navigazione dopo submit trimestre. URL: {pagina_err.url}')
        return False

    # Se la pagina intermedia visualizzaCarrello, clicca Visualizza dati/Modifica
    logger.info(f'[PAGOPA] 🛒 Pagina carrello. Cerco pulsante Visualizza dati/Modifica...')
    xpath_sel = "//input[@type='image' and (@alt='Visualizza dati del bollettino' or @title='Visualizza dati/Modifica')]"
    try:
        el = page.wait_for_selector(f'xpath={xpath_sel}', timeout=_ms(timeout), state='attached')
        if el:
            logger.info(f'[PAGOPA] 👆 Clicco "Visualizza dati/Modifica"')
            el.click()
            logger.info(f'[PAGOPA] ✅ Cliccato Visualizza dati/Modifica.')
            page.wait_for_timeout(1000)
    except Exception as e:
        logger.warning(f'[PAGOPA] ❌ ERRORE click Visualizza dati/Modifica: {e}')

    logger.info(f'[PAGOPA] ⏳ Attesa #oreRetribuite dopo submit trimestre...')
    try:
        pagina_target, _ = _scansiona_pagine(context, selector='#oreRetribuite')
        if pagina_target:
            logger.info(f'[PAGOPA] ✅ #oreRetribuite trovato. {_page_info(pagina_target)}')
            return True
        page.wait_for_selector('#oreRetribuite', timeout=_ms(timeout), state='attached')
        logger.info(f'[PAGOPA] ✅ #oreRetribuite trovato. {_page_info(page)}')
        return True
    except PwTimeout:
        logger.info(f'[PAGOPA] ❌ TIMEOUT: #oreRetribuite non apparso dopo submit. {_page_info(page)}')
        return False


def _estrai_totale_inps(page):
    """Cerca il totale/importo nella pagina INPS dopo il calcolo contributi.

    Raccoglie TUTTI i numeri in formato italiano (X.XXX,XX) da tutta la pagina,
    sia da <td class="tdDesc">, pattern €, e keyword "totale"/"importo".
    Restituisce il numero PIÙ GRANDE (il totale è sempre il maggiore).
    Returns:
        float: importo trovato, oppure None.
    """
    import re
    try:
        body_text = page.evaluate("document.body.innerText")
    except Exception:
        return None

    candidati = []

    # 1) Numeri dentro td.tdDesc
    try:
        tds = page.evaluate("""() => {
            var els = document.querySelectorAll('td.tdDesc');
            return Array.from(els).map(function(el) { return el.innerText.trim(); });
        }""")
        for txt in tds:
            for n in re.findall(r'[\d]{1,3}(?:\.[\d]{3})*(?:,\d{2})', txt):
                try:
                    v = float(n.replace('.', '').replace(',', '.'))
                    if 1 < v < 100000:
                        candidati.append(v)
                except ValueError:
                    continue
    except Exception:
        logger.warning("[PAGOPA] Evaluate td.tdDesc fallita in _estrai_totale_inps")

    # 2) Pattern "€ X.XXX,XX" o "X.XXX,XX €"
    for p in [r'€\s*([\d]{1,3}(?:[.,][\d]{3})*(?:[.,]\d{2}))',
              r'([\d]{1,3}(?:[.,][\d]{3})*(?:[.,]\d{2}))\s*€']:
        for m in re.finditer(p, body_text):
            try:
                v = float(m.group(1).replace('.', '').replace(',', '.'))
                if 1 < v < 100000:
                    candidati.append(v)
            except ValueError:
                continue

    # 3) Pattern asterisco: "* 88,40" o "88,40 *" (candidati forti — quasi certamente il totale)
    candidati_forti = []
    for p in [r'\*\s*([\d]{1,3}(?:\.[\d]{3})*(?:,\d{2}))',
              r'([\d]{1,3}(?:\.[\d]{3})*(?:,\d{2}))\s*\*']:
        for m in re.finditer(p, body_text):
            try:
                v = float(m.group(1).replace('.', '').replace(',', '.'))
                if 1 < v < 100000:
                    candidati_forti.append(v)
            except ValueError:
                continue
    if candidati_forti:
        return max(candidati_forti)

    # 4) Tutti i numeri formato italiano nel body
    for n in re.findall(r'(?<!\d)[\d]{1,3}(?:\.[\d]{3})*(?:,\d{2})(?!\d)', body_text):
        try:
            v = float(n.replace('.', '').replace(',', '.'))
            if 1 < v < 100000:
                candidati.append(v)
        except ValueError:
            continue

    # 5) Se trovati, restituisci il più grande (totale è il numero maggiore)
    if candidati:
        return max(candidati)

    # 5) Fallback: cerca "totale"/"importo" e prende il numero sulla stessa riga
    for keyword in ['totale', 'importo', 'totale da pagare', 'totale contributi']:
        for line in body_text.split('\n'):
            if keyword in line.lower():
                nums = re.findall(r'[\d]{1,3}(?:\.[\d]{3})*(?:,\d{2})', line)
                for n in nums:
                    try:
                        v = float(n.replace('.', '').replace(',', '.'))
                        if 1 < v < 100000:
                            return v
                    except ValueError:
                        continue
    return None


def pagopa_compila_bollettino(driver, ore_trim, paga_oraria, codice_associazione, quota_trim, trimestre, anno, timeout=10, download_dir=None, nome_file=None):
    """Step 4: Compila il form con i dati contributivi trimestrali.

    Returns:
        float or None: importo totale estratto dalla pagina INPS dopo il submit.
    """
    page = _estrai_page(driver)
    logger.info(f'[PAGOPA] 📝 Compila bollettino. Input: ore={ore_trim}, paga={paga_oraria}, cassa={codice_associazione}, quota={quota_trim}. {_page_info(page)}')

    logger.info(f'[PAGOPA] ✏️ Campo [#oreRetribuite] ← {int(ore_trim)}')
    page.fill('#oreRetribuite', str(int(ore_trim)))
    logger.info(f'[PAGOPA] ✏️ Campo [#retribuzioneOrariaEffettiva] ← {paga_oraria:.2f}')
    page.fill('#retribuzioneOrariaEffettiva', f'{paga_oraria:.2f}'.replace(',', '.'))

    try:
        select_el = page.wait_for_selector('#codiceAssociazione', timeout=_ms(timeout), state='attached')
        if select_el:
            options = page.evaluate("""() => {
                var sel = document.getElementById('codiceAssociazione');
                return Array.from(sel.options).map(o => ({text: o.text.trim(), value: o.value}));
            }""")
            logger.info(f'[PAGOPA] 📋 Opzioni #codiceAssociazione trovate: {len(options)}')
            found = False
            for opt in options:
                if opt['text'].startswith(codice_associazione) and opt['value']:
                    logger.info(f'[PAGOPA] ✅ Seleziono cassa: text="{opt["text"]}", value="{opt["value"]}"')
                    page.select_option('#codiceAssociazione', value=opt['value'])
                    found = True
                    break
            if not found:
                logger.info(f'[PAGOPA] ⚠️ Cassa "{codice_associazione}" non trovata. Prima opzione disponibile.')
                for opt in options:
                    if opt['text'] and opt['value']:
                        logger.info(f'[PAGOPA] ▶️ Seleziono prima opzione: "{opt["text"]}" (value={opt["value"]})')
                        page.select_option('#codiceAssociazione', value=opt['value'])
                        break
    except Exception as e:
        logger.warning(f'[PAGOPA] ❌ ERRORE select #codiceAssociazione: {e}')

    try:
        if page.query_selector('#quotaAssociativa'):
            logger.info(f'[PAGOPA] ✏️ Campo [#quotaAssociativa] ← {quota_trim:.2f}')
            page.fill('#quotaAssociativa', f'{quota_trim:.2f}'.replace(',', '.'))
        else:
            logger.info(f'[PAGOPA] ⏭️ #quotaAssociativa non presente nel form (skip)')
    except Exception as e:
        logger.warning(f'[PAGOPA] ❌ ERRORE #quotaAssociativa: {e}')

    page.wait_for_timeout(500)
    trimestre_numero = int(trimestre.replace('Q', '')) if isinstance(trimestre, str) and trimestre.startswith('Q') else int(trimestre)
    try:
        js_code = "(function() { var elTrim = document.getElementById('trimestreRetribuzione'); var elAnno = document.getElementById('anno'); var elTrimC = document.getElementById('trimestreRetribuzioneCorrente'); var elAnnoC = document.getElementById('annoCorrente'); var report = {trimBefore: (elTrim||{}).value, annoBefore: (elAnno||{}).value}; if (elTrim) elTrim.value = '%s'; if (elAnno) elAnno.value = '%s'; if (elTrimC) elTrimC.value = '%s'; if (elAnnoC) elAnnoC.value = '%s'; var form = document.getElementById('rapportoLavoro'); report.trimAfter = (elTrim||{}).value; report.annoAfter = (elAnno||{}).value; report.formFound = !!form; if (form) { form.submit(); report.submitted = true; } else { report.submitted = false; } return JSON.stringify(report); })()" % (str(trimestre_numero), str(int(anno)), str(trimestre_numero), str(int(anno)))
        result = page.evaluate(js_code)
        logger.info(f'[PAGOPA] 📤 Submit JS form #rapportoLavoro: {result}')
    except Exception as e:
        logger.warning(f'[PAGOPA] ❌ ERRORE submit diretto: {e}')

    # Attesa navigazione dopo submit
    try:
        page.wait_for_load_state('networkidle', timeout=_ms(timeout))
        logger.info(f'[PAGOPA] ✅ wait_for_load_state. {_page_info(page)}')
    except Exception as e:
        logger.warning(f'[PAGOPA] ⏭️ wait_for_load_state: {e}')

    # Attendi URL effettivo: calcolaContributi o gestioneCarrello
    contesto = _estrai_context(driver)
    for tentativo in range(timeout * 2):
        pagina_target, _ = _scansiona_pagine(contesto, url_substring='calcolacontributi')
        if pagina_target:
            page = pagina_target
            logger.info(f'[PAGOPA] ✅ Navigato a calcolaContributi.do. {_page_info(page)}')
            break
        pagina_target, _ = _scansiona_pagine(contesto, url_substring='gestionecarrello')
        if pagina_target:
            page = pagina_target
            logger.info(f'[PAGOPA] ✅ Navigato a gestioneCarrello.do. {_page_info(page)}')
            break
        import time as _t
        _t.sleep(0.5)
    else:
        logger.info(f'[PAGOPA] ⏭️ Navigazione non rilevata. {_page_info(page)}')

    # Estrai totale INPS dalla pagina (solo log, non affidabile — il vero totale è su gestioneCarrello.do)
    try:
        totale_inps = _estrai_totale_inps(page)
        if totale_inps is not None:
            logger.info(f'[PAGOPA] 💰 Totale INPS su calcolaContributi: € {totale_inps:.2f} (non usato)')
    except Exception as e:
        logger.warning(f'[PAGOPA] ❌ ERRORE estrazione totale INPS: {e}')
    return None


def pagopa_avanti(driver, timeout=10, delay=0.5):
    """Step 5: Clicca 'Avanti' e attende 'Conferma modifica'."""
    page = _estrai_page(driver)
    page.wait_for_timeout(_ms(delay))
    logger.info(f'[PAGOPA] ⏩ Step 5: Click "Avanti". {_page_info(page)}')

    try:
        el = page.query_selector('xpath=//input[@type="image" and @alt="Conferma modifica"]')
        if el:
            logger.info('[PAGOPA] ⏭️ Già su Conferma modifica, salto click Avanti')
            return True
    except Exception as e:
        logger.warning(f'[PAGOPA] Check Conferma modifica fallito: {e}')

    logger.info('[PAGOPA] 🔍 Cerco pulsante "Avanti"...')
    try:
        result = page.evaluate("(function() { var log = []; var el = document.querySelector('input[alt=\"Avanti\"]'); if (el) { log.push('found input[alt=Avanti]'); el.click(); return log.join(', '); } el = document.querySelector('#sceltaTrimestre > input.linkImg:last-of-type'); if (el) { log.push('found linkImg last'); el.click(); return log.join(', '); } var all = document.querySelectorAll('#sceltaTrimestre input'); if (all.length > 0) { log.push('last input #sceltaTrimestre'); all[all.length-1].click(); return log.join(', '); } log.push('no element found'); return log.join(', '); })()")
        logger.info(f'[PAGOPA] 🖱️ JS Avanti: {result}')
    except Exception as e:
        logger.warning(f'[PAGOPA] JS Avanti eccezione: {e}')

    for sel in [
        'input[alt="Avanti"]',
        '#sceltaTrimestre > input.linkImg',
        'xpath=//*[@id="sceltaTrimestre"]/input[6]',
    ]:
        try:
            el = page.wait_for_selector(sel, timeout=3000, state='attached')
            if el:
                logger.info(f'[PAGOPA] 👆 Clicco "Avanti" via selettore: {sel}')
                el.click()
                break
        except Exception:
            logger.debug("[PAGOPA] Selettore Avanti fallito")
            continue
    else:
        logger.info('[PAGOPA] ⚠️ Avanti non trovato via selettori. Provo ultimo input visibile...')
        try:
            inputs = page.query_selector_all('#sceltaTrimestre input')
            for inp in reversed(inputs):
                if inp.is_visible():
                    logger.info(f'[PAGOPA] 👆 Clicco ultimo input visibile in #sceltaTrimestre')
                    inp.click()
                    break
        except Exception as e:
            logger.info(f'[PAGOPA] ❌ Fallito click ultimo input: {e}')
            return False

    logger.info(f'[PAGOPA] ⏳ Attesa pulsante "Conferma modifica"...')
    try:
        page.wait_for_selector(
            'xpath=//input[@type="image" and @alt="Conferma modifica"]',
            timeout=_ms(timeout), state='attached'
        )
        logger.info(f'[PAGOPA] ✅ "Conferma modifica" trovato! {_page_info(page)}')
        return True
    except PwTimeout:
        logger.info(f'[PAGOPA] ❌ TIMEOUT: "Conferma modifica" non trovato. {_page_info(page)}')
        return False


def pagopa_conferma_modifica(driver, timeout=10):
    """Step 6: Clicca 'Conferma modifica' e attende la navigazione.

    Dopo la navigazione, estrae il totale dalla pagina gestioneCarrello.do.
    Returns:
        float or None: importo totale estratto dalla pagina.
    """
    page = _estrai_page(driver)
    logger.info(f'[PAGOPA] ✅ Step 6: Click "Conferma modifica". {_page_info(page)}')

    xpath = "//input[@type='image' and @alt='Conferma modifica']"
    el = page.wait_for_selector(f'xpath={xpath}', timeout=_ms(timeout), state='attached')
    if not el:
        logger.info(f'[PAGOPA] ❌ ERRORE: pulsante "Conferma modifica" non trovato')
        return None
    logger.info(f'[PAGOPA] 👆 Clicco "Conferma modifica"...')
    with page.expect_navigation(timeout=_ms(timeout), wait_until='load'):
        el.click()
    logger.info(f'[PAGOPA] ✅ Navigazione completata dopo Conferma modifica. {_page_info(page)}')

    # Estrai totale dalla pagina (gestioneCarrello.do)
    try:
        totale_inps = _estrai_totale_inps(page)
        if totale_inps is not None:
            logger.info(f'[PAGOPA] 💰 Totale INPS da gestioneCarrello: € {totale_inps:.2f}')
        else:
            logger.info(f'[PAGOPA] 💰 Totale INPS non rilevato in gestioneCarrello.')
        return totale_inps
    except Exception as e:
        logger.warning(f'[PAGOPA] ❌ ERRORE estrazione totale INPS da gestioneCarrello: {e}')
        return None


def _estrai_pdf_da_nuova_scheda(nuova_pagina, timeout=10):
    """Estrae l'URL del PDF da una nuova scheda aperta dal click.

    Cerca nell'ordine:
    1. URL diretto .pdf
    2. iframe con type=application/pdf o src contenente .pdf
    3. embed/object con type=application/pdf
    4. Regex .pdf nella page source

    Returns:
        str: URL del PDF trovato, oppure None.
    """
    try:
        nuova_pagina.wait_for_load_state('load', timeout=_ms(timeout))
    except Exception:
        logger.warning("[PAGOPA] wait_for_load_state nuova scheda fallito in _estrai_pdf_da_nuova_scheda")

    url = nuova_pagina.url
    logger.info(f'[PAGOPA] Nuova scheda URL: {url}')

    if '.pdf' in url.lower():
        logger.info(f'[PAGOPA] URL diretto PDF')
        return url

    try:
        for iframe in nuova_pagina.frames:
            src = iframe.url
            if '.pdf' in src.lower():
                logger.info(f'[PAGOPA] PDF da iframe: {src}')
                return src
            if 'application/pdf' in (iframe.evaluate('document.contentType') if iframe.name or True else ''):
                pass
    except Exception:
        logger.warning("[PAGOPA] Ricerca PDF in iframe fallita")

    # Cerca iframe per selettore
    try:
        import re
        html = nuova_pagina.content()
        # iframe src con .pdf
        for m in re.finditer(r'<iframe[^>]+src=["\']([^"\']*\.pdf[^"\']*)["\']', html, re.I):
            return m.group(1)
        # embed/object con .pdf
        for sel in ['embed[type="application/pdf"]', 'object[type="application/pdf"]',
                    'embed[src*=".pdf"]', 'object[data*=".pdf"]']:
            el = nuova_pagina.query_selector(sel)
            if el:
                url_pdf = el.get_attribute('src') or el.get_attribute('data')
                if url_pdf:
                    logger.info(f'[PAGOPA] PDF da {sel}: {url_pdf}')
                    from urllib.parse import urljoin
                    return urljoin(url, url_pdf)
        # link .pdf generici
        for m in re.finditer(r'(https?://[^"\'<>]+\.pdf[^"\'<>]*)', html):
            return m.group(1)
    except Exception as e:
        logger.warning(f'[PAGOPA] ERRORE estrazione PDF da nuova scheda: {e}')

    logger.info(f'[PAGOPA] PDF non trovato nella nuova scheda')
    return None


def pagopa_stampa_avviso(driver, timeout=10, delay=0.5):
    """Step 7: Click Stampa Avviso — apre PDF in nuova scheda.

    Su gestioneCarrello.do: click → naviga a generaAvvisiPagamento.do
    Su generaAvvisiPagamento.do: click (target="_blank") → apre PDF in nuova scheda.
    Il PDF viene catturato da pagopa_switch_finestra_e_salva (step 8).
    """
    page = _estrai_page(driver)
    _estrai_context(driver)
    xpath = "//input[@type='image' and @alt='Stampa Avviso di Pagamento']"
    logger.info(f'[PAGOPA] Stampa Avviso. {_page_info(page)}')

    # Trova pulsante
    try:
        page.wait_for_selector(f'xpath={xpath}', timeout=_ms(timeout), state='attached')
    except Exception as e:
        logger.warning(f'[PAGOPA] ERRORE: pulsante Stampa Avviso non trovato su {page.url}: {e}')
        return False

    # Clicca il pulsante (Playwright + fallback nativo DOM)
    partenza = 'generaAvvisiPagamento.do' if 'generaAvvisiPagamento' in page.url else 'gestioneCarrello.do'
    logger.info(f'[PAGOPA] Cerco pulsante Stampa Avviso su {partenza}...')

    click_ok = False
    try:
        page.click(f'xpath={xpath}', no_wait_after=True, timeout=_ms(timeout))
        logger.info(f'[PAGOPA] 👆 Cliccato "Stampa Avviso" su {partenza} (Playwright)')
        click_ok = True
    except Exception as e:
        logger.info(f'[PAGOPA] ⚠️ Click Playwright su {partenza} fallito ({e}). Provo click nativo DOM...')
        try:
            el = page.query_selector(f'xpath={xpath}')
            if el:
                el.evaluate('el => el.click()')
                logger.info(f'[PAGOPA] 👆 Cliccato "Stampa Avviso" su {partenza} (nativo DOM)')
                click_ok = True
        except Exception as e2:
            logger.warning(f'[PAGOPA] ❌ Click nativo su {partenza} fallito ({e2})')

    if not click_ok:
        logger.info(f'[PAGOPA] ❌ ERRORE: impossibile cliccare "Stampa Avviso" su {partenza}')
        return False

    # Attendi navigazione a generaAvvisiPagamento.do se siamo partiti da gestioneCarrello
    if partenza == 'gestioneCarrello.do':
        try:
            page.wait_for_url("**/generaAvvisiPagamento.do**", timeout=_ms(timeout))
            logger.info(f'[PAGOPA] ✅ Navigato a generaAvvisiPagamento.do: {page.url}')
        except Exception:
            logger.info(f'[PAGOPA] ⏳ Navigazione a generaAvvisiPagamento.do non rilevata entro {timeout}s. URL: {page.url}')

    # Secondo click su generaAvvisiPagamento.do: apre PDF in nuova scheda (target="_blank")
    if 'generaAvvisiPagamento' in page.url:
        logger.info(f'[PAGOPA] 🔄 Secondo click su "Stampa Avviso" in generaAvvisiPagamento.do...')
        try:
            page.wait_for_selector(f'xpath={xpath}', timeout=_ms(timeout), state='attached')
            el = page.query_selector(f'xpath={xpath}')
            if el:
                el.evaluate('el => el.click()')
                logger.info(f'[PAGOPA] 👆 Secondo click su "Stampa Avviso" eseguito (nativo DOM)')
            else:
                logger.info(f'[PAGOPA] ❌ ERRORE: pulsante "Stampa Avviso" non trovato su generaAvvisiPagamento.do')
        except Exception as e:
            logger.warning(f'[PAGOPA] ❌ Secondo click fallito: {e}')
    else:
        logger.info(f'[PAGOPA] ⏭️ Non su generaAvvisiPagamento.do ({page.url}). Secondo click saltato.')

    logger.info(f'[PAGOPA] ✅ Step 7: Stampa Avviso completato. {_page_info(page)}')
    return True


def _scarica_pdf_da_url(driver, url):
    """Scarica un PDF da URL usando i cookie del context."""
    import requests as req

    if url.startswith('data:application/pdf;base64,'):
        _, encoded = url.split(',', 1)
        logger.info(f'[PAGOPA] PDF da data URL (base64, {len(encoded)} chars)')
        return base64.b64decode(encoded)

    context = _estrai_context(driver)
    cookies_playwright = context.cookies()
    cookies = {c['name']: c['value'] for c in cookies_playwright}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    logger.info(f'[PAGOPA] Scarico PDF da: {url[:200]}')
    r = req.get(url, cookies=cookies, headers=headers, timeout=30)
    r.raise_for_status()
    return r.content


def _trova_pagina_pdf(context, driver):
    """Trova la pagina giusta per il PDF: stampaAvvisoDiPagamento, poi non blank, poi ultima."""
    for p in context.pages:
        if 'stampaAvvisoDiPagamento' in p.url:
            logger.info(f'[PAGOPA] 📄 Pagina selezionata: stampaAvvisoDiPagamento')
            return p
    for p in context.pages:
        if 'about:blank' not in p.url and '127.0.0.1' not in p.url and 'localhost' not in p.url:
            logger.info(f'[PAGOPA] 📄 Pagina selezionata: {p.url[:150]}')
            return p
    p = _estrai_page(driver)
    logger.info(f'[PAGOPA] 📄 Pagina selezionata (fallback): {p.url[:150]}')
    return p


def pagopa_switch_finestra_e_salva(driver, nome_file, timeout=10, download_dir=None):
    """Step 8: Dopo 'Stampa Avviso', cattura il PDF.

    Strategies parallele a automation.py (Selenium).
    """
    context = _estrai_context(driver)

    cartella = download_dir or os.path.join(
        os.path.dirname(__file__), '..', 'media', 'pagopa')
    os.makedirs(cartella, exist_ok=True)

    nome_sicuro = re.sub(r'[^\w\-_. ]', '_', nome_file)
    if not nome_sicuro.lower().endswith('.pdf'):
        nome_sicuro += '.pdf'

    pdf_data = None

    debug_dir = os.path.join(cartella, 'SCREENSHOT')
    try:
        os.makedirs(debug_dir, exist_ok=True)
    except Exception:
        logger.warning("[PAGOPA] Creazione debug_dir fallita")

    # Info iniziali — conta pagine e attendi nuova tab (target="_blank" asincrono)
    n_pagine_context = len(context.pages)
    logger.info(f'[PAGOPA] 📊 Step 8: Cattura PDF. Pagine nel context: {n_pagine_context}')
    for i, p in enumerate(context.pages):
        logger.info(f'[PAGOPA]   Pagina {i}: {p.url[:150]}')

    if n_pagine_context <= 1:
        logger.info(f'[PAGOPA] ⏳ Attesa nuova tab (da target="_blank")...')
        from time import sleep
        for _ in range(timeout * 2):
            sleep(0.5)
            if len(context.pages) > 1:
                logger.info(f'[PAGOPA]   ✅ Nuova tab rilevata ({len(context.pages)} pagine)')
                break

    page = _trova_pagina_pdf(context, driver)

    # Attendi caricamento della pagina
    try:
        page.wait_for_load_state('load', timeout=_ms(timeout))
        logger.info(f'[PAGOPA] ✅ load state OK: {page.url[:200]}')
    except Exception as e:
        logger.warning(f'[PAGOPA] ⚠️ wait_for_load_state: {e}. URL: {page.url[:200]}')

    try:
        nome_html = nome_sicuro.rsplit('.', 1)[0] + '.html'
        with open(os.path.join(debug_dir, 'dopostampa_' + nome_html), 'w', encoding='utf-8') as f:
            f.write(page.content())
        logger.info(f'[PAGOPA] 💾 HTML della pagina salvato in debug')
    except Exception as e:
        logger.warning(f'[PAGOPA] ⚠️ ERRORE salvataggio HTML debug: {e}')

    # TENTATIVO 0: _pagopaPdfUrl
    logger.info(f'[PAGOPA] 🔍 Tentativo 0: _pagopaPdfUrl...')
    url_captured = None
    try:
        url_captured = page.evaluate("window._pagopaPdfUrl")
        if url_captured:
            logger.info(f'[PAGOPA]   ✅ _pagopaPdfUrl trovato su pagina corrente: {url_captured[:200]}')
    except Exception:
        logger.info("[PAGOPA]   Evaluate _pagopaPdfUrl non disponibile sulla pagina")
    if not url_captured:
        for p in context.pages:
            if p == page:
                continue
            try:
                url_captured = p.evaluate("window._pagopaPdfUrl")
                if url_captured:
                    logger.info(f'[PAGOPA]   ✅ _pagopaPdfUrl trovato su altra pagina: {url_captured[:200]}')
                    break
            except Exception:
                logger.debug("[PAGOPA] Evaluate _pagopaPdfUrl su altra pagina fallito")
                continue
    if url_captured:
        try:
            pdf_data = _scarica_pdf_da_url(driver, url_captured)
            if pdf_data:
                logger.info(f'[PAGOPA]   ✅ PDF scaricato da URL ({len(pdf_data)} bytes)')
            else:
                logger.info(f'[PAGOPA]   ❌ _scarica_pdf_da_url ha restituito None')
        except Exception as e:
            logger.warning(f'[PAGOPA]   ❌ Download da _pagopaPdfUrl fallito: {e}')
    else:
        logger.info(f'[PAGOPA]   ⏭️ _pagopaPdfUrl non trovato')

    # TENTATIVO 0b: URL corrente PDF
    url_corrente = page.url
    logger.info(f'[PAGOPA] 🔍 Tentativo 0b: URL corrente = {url_corrente}')
    if pdf_data is None:
        if '.pdf' in url_corrente.lower():
            logger.info(f'[PAGOPA]   ✅ URL contiene .pdf, tentativo download...')
            try:
                pdf_data = _scarica_pdf_da_url(driver, url_corrente)
                if pdf_data:
                    logger.info(f'[PAGOPA]   ✅ PDF scaricato ({len(pdf_data)} bytes)')
            except Exception as e:
                logger.warning(f'[PAGOPA]   ❌ Download URL corrente fallito: {e}')
        else:
            logger.info(f'[PAGOPA]   ⏭️ URL non contiene .pdf')

    # TENTATIVO 0c: stampaAvvisoDiPagamento form
    if pdf_data is None:
        logger.info(f'[PAGOPA] 🔍 Tentativo 0c: form stampaAvvisoDiPagamento...')
        try:
            import requests as req
            forms_data = page.evaluate("(function() { var form = document.querySelector('form[action*=\"stampaAvvisoDiPagamento\"]'); if (!form) return null; var action = form.getAttribute('action'); var csrfInput = form.querySelector('input[name=\"csrfTokenClient\"]'); var csrf = csrfInput ? csrfInput.value : ''; return { action: action, csrf: csrf }; })()")
            if forms_data and forms_data.get('action'):
                action = forms_data['action']
                csrf = forms_data.get('csrf', '')
                if not action.startswith('http'):
                    action = 'https://serviziweb2.inps.it' + action
                cookies_pw = context.cookies()
                cookies = {c['name']: c['value'] for c in cookies_pw}
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                params = {}
                if csrf:
                    params['csrfTokenClient'] = csrf
                logger.info(f'[PAGOPA]   Richiesta GET a: {action}')
                if csrf:
                    logger.info(f'[PAGOPA]   csrfTokenClient={csrf[:20]}...')
                r = req.get(action, params=params, cookies=cookies, headers=headers, timeout=30)
                ct = r.headers.get('Content-Type', '')
                logger.info(f'[PAGOPA]   Risposta: HTTP {r.status_code}, Content-Type={ct}, size={len(r.content)}')
                if r.status_code == 200 and len(r.content) > 500:
                    is_pdf = ct == 'application/pdf' or r.content[:4] == b'%PDF'
                    if is_pdf:
                        pdf_data = r.content
                        logger.info(f'[PAGOPA]   ✅ PDF scaricato ({len(pdf_data)} bytes)')
                    else:
                        logger.info(f'[PAGOPA]   ⚠️ Non è PDF. Primi 100 byte: {r.content[:100]}')
                else:
                    logger.info(f'[PAGOPA]   ⚠️ Risposta non valida: status={r.status_code}, size={len(r.content)}')
            else:
                logger.info(f'[PAGOPA]   ⏭️ Form stampaAvvisoDiPagamento non trovato nella pagina')
        except Exception as e:
            logger.warning(f'[PAGOPA]   ❌ ERRORE richiesta stampaAvvisoDiPagamento: {e}')

    # TENTATIVO 1: altre pagine del context
    if pdf_data is None:
        logger.info(f'[PAGOPA] 🔍 Tentativo 1: cerca PDF in altre pagine del context...')
        for altra_pagina in context.pages:
            if altra_pagina == page:
                continue
            nuova_pagina = altra_pagina
            url_nuova = nuova_pagina.url
            logger.info(f'[PAGOPA]   Pagina trovata: {url_nuova}')
            try:
                nuova_pagina.wait_for_load_state()
                logger.info(f'[PAGOPA]   ✅ Load state OK')
            except Exception as e:
                logger.warning(f'[PAGOPA]   ⚠️ wait_for_load_state: {e}')

            # 1a: URL PDF diretto
            if '.pdf' in url_nuova.lower():
                logger.info(f'[PAGOPA]   Tentativo 1a: URL PDF diretto...')
                try:
                    pdf_data = _scarica_pdf_da_url(driver, url_nuova)
                    if pdf_data:
                        logger.info(f'[PAGOPA]     ✅ OK ({len(pdf_data)} bytes)')
                        break
                except Exception as e:
                    logger.warning(f'[PAGOPA]     ❌ Fallito: {e}')

            # 1b: URL .pdf nella page source
            if pdf_data is None:
                logger.info(f'[PAGOPA]   Tentativo 1b: cerca URL .pdf nella page source...')
                try:
                    urls_pdf = re.findall(r'https?://[^"\'<>]+\.pdf[^"\'<>]*', nuova_pagina.content())
                    logger.info(f'[PAGOPA]     Trovati {len(urls_pdf)} URL .pdf')
                    for url_pdf in urls_pdf[:3]:
                        try:
                            pdf_data = _scarica_pdf_da_url(driver, url_pdf)
                            if pdf_data:
                                logger.info(f'[PAGOPA]     ✅ OK ({len(pdf_data)} bytes)')
                                break
                        except Exception as e:
                            logger.warning(f'[PAGOPA]     ❌ Fallito: {e}')
                except Exception as e:
                    logger.warning(f'[PAGOPA]     ⚠️ Errore: {e}')

            # 1c: embed/object
            if pdf_data is None:
                logger.info(f'[PAGOPA]   Tentativo 1c: embed/object...')
                for sel in ['embed[type="application/pdf"]', 'object[type="application/pdf"]',
                            'embed[src*=".pdf"]', 'object[data*=".pdf"]']:
                    try:
                        el = nuova_pagina.query_selector(sel)
                        if el:
                            url_pdf = el.get_attribute('src') or el.get_attribute('data')
                            if url_pdf:
                                from urllib.parse import urljoin
                                url_abs = urljoin(url_nuova, url_pdf)
                                logger.info(f'[PAGOPA]     Trovato {sel}: {url_abs[:200]}')
                                pdf_data = _scarica_pdf_da_url(driver, url_abs)
                                if pdf_data:
                                    logger.info(f'[PAGOPA]     ✅ OK ({len(pdf_data)} bytes)')
                                    break
                    except Exception as e:
                        logger.warning(f'[PAGOPA]     ❌ {sel}: {e}')

            # 1d: iframe → request.get con Referer
            if pdf_data is None:
                logger.info(f'[PAGOPA]   Tentativo 1d: iframe → request Referer...')
                try:
                    iframe = nuova_pagina.query_selector('iframe')
                    if iframe:
                        src = iframe.get_attribute('src')
                        if src:
                            from urllib.parse import urljoin
                            url_target = urljoin(url_nuova, src)
                            logger.info(f'[PAGOPA]     iframe src: {url_target[:200]}')
                            logger.info(f'[PAGOPA]     🏠 Referer: {nuova_pagina.url[:200]}')
                            resp = nuova_pagina.request.get(
                                url_target,
                                headers={'Referer': nuova_pagina.url},
                            )
                            ct = resp.headers.get('content-type', '')
                            body = resp.body()
                            logger.info(f'[PAGOPA]     📋 HTTP {resp.status} | Content-Type: {ct} | size: {len(body)}')
                            if resp.ok and len(body) > 1000:
                                if ct.startswith('application/pdf') or body[:4] == b'%PDF':
                                    pdf_data = body
                                    logger.info(f'[PAGOPA]     ✅ OK ({len(pdf_data)} bytes)')
                                else:
                                    logger.info(f'[PAGOPA]     ⚠️ Non PDF. Primi 200: {body[:200]}')
                            else:
                                logger.info(f'[PAGOPA]     ⚠️ HTTP {resp.status}, {len(body)} bytes. Primi 200: {body[:200]}')
                except Exception as e:
                    logger.warning(f'[PAGOPA]     ❌ Fallito: {e}')

            if pdf_data:
                logger.info(f'[PAGOPA]   ✅ PDF ottenuto da altra scheda')
                break
    else:
        logger.info(f'[PAGOPA]   ⏭️ Saltato (PDF già ottenuto)')

    # TENTATIVO 2: iframe #frameStampa → page.request.get() con Referer corretto
    if pdf_data is None:
        logger.info(f'[PAGOPA] 🔍 Tentativo 2: cerca frame/embed/object e request Referer...')
        pdf_url = None
        # Cerca #frameStampa (IFrame INPS)
        try:
            iframe_el = page.wait_for_selector('#frameStampa', timeout=_ms(max(3, timeout//2)), state='attached')
            if iframe_el:
                pdf_url = iframe_el.get_attribute('src')
                if pdf_url:
                    logger.info(f'[PAGOPA]   📎 iframe #frameStampa src: {pdf_url[:200]}')
        except Exception:
            logger.info("[PAGOPA]   #frameStampa non trovato")
        # Fallback: cerca iframe generico, embed, object (Chrome PDF viewer)
        if not pdf_url:
            for sel in ['embed[type="application/pdf"]', 'object[type="application/pdf"]',
                        'embed[src*=".pdf"]', 'object[data*=".pdf"]', 'iframe[src*=".pdf"]',
                        'iframe[src*="stampaAvviso"]', 'iframe[src*="/pdf"]']:
                try:
                    el = page.query_selector(sel)
                    if el:
                        pdf_url = el.get_attribute('src') or el.get_attribute('data')
                        if pdf_url:
                            from urllib.parse import urljoin
                            pdf_url = urljoin(page.url, pdf_url)
                            logger.info(f'[PAGOPA]   📎 {sel}: {pdf_url[:200]}')
                            break
                except Exception:
                    logger.debug("[PAGOPA] Selettore frame/embed/object fallito")
                    continue
        if not pdf_url:
            logger.info(f'[PAGOPA]   ☑️ Salto: nessun frame/embed/object PDF trovato nella pagina')
            # Diagnostica: log dei tag rilevanti
            try:
                tags = page.evaluate("""() => Array.from(document.querySelectorAll('iframe, embed, object, a[href$=\".pdf\"]')).map(el => ({tag:el.tagName, src:el.src||el.getAttribute('src')||el.href||el.getAttribute('data')||'', id:el.id||'', cls:el.className||''})).slice(0,20)""")
                logger.info(f'[PAGOPA]   🔎 Tag iframe/embed/object/a.pdf nella pagina:')
                for t in tags:
                    logger.info(f'[PAGOPA]     <{t["tag"]}> id="{t["id"]}" src="{t["src"][:150]}"')
                if not tags:
                    logger.info(f'[PAGOPA]     (nessuno)')
            except Exception as e2:
                logger.warning(f'[PAGOPA]     ⚠️ evaluate fallita: {e2}')
        if pdf_url:
            try:
                logger.info(f'[PAGOPA]   🏠 Referer: {page.url[:200]}')
                resp = page.request.get(
                    pdf_url,
                    headers={'Referer': page.url},
                )
                ct = resp.headers.get('content-type', '')
                body = resp.body()
                logger.info(f'[PAGOPA]   📋 HTTP {resp.status} | Content-Type: {ct} | size: {len(body)}')
                if resp.ok and len(body) > 1000:
                    if ct.startswith('application/pdf') or body[:4] == b'%PDF':
                        pdf_data = body
                        logger.info(f'[PAGOPA]   ✅ PDF originale ottenuto ({len(pdf_data)} bytes)')
                    else:
                        logger.info(f'[PAGOPA]   ⚠️ Content-Type non PDF. Primi 200: {body[:200]}')
                else:
                    logger.info(f'[PAGOPA]   ⚠️ Risposta non valida: HTTP {resp.status}, {len(body)} bytes. Primi 200: {body[:200]}')
            except Exception as e:
                logger.warning(f'[PAGOPA]   ❌ Download fallito: {e}')

    # TENTATIVO 3: page.pdf() sulla pagina originale
    if pdf_data is None:
        logger.info(f'[PAGOPA] 🔍 Tentativo 3: page.pdf() sulla pagina originale...')
        try:
            pdf_data = page.pdf(
                print_background=True,
                width='210mm', height='297mm',
                margin={'top': '10mm', 'bottom': '10mm', 'left': '10mm', 'right': '10mm'},
                prefer_css_page_size=True,
            )
            logger.info(f'[PAGOPA]   ✅ page.pdf() originale OK ({len(pdf_data)} bytes)')
        except Exception as e:
            logger.warning(f'[PAGOPA]   ❌ page.pdf() originale fallito: {e}')

    if pdf_data:
        destinazione = os.path.join(cartella, nome_sicuro)
        with open(destinazione, 'wb') as f:
            f.write(pdf_data)
        logger.info(f'[PAGOPA] ✅ PDF salvato: {os.path.basename(destinazione)} ({len(pdf_data)} bytes)')
    else:
        logger.info(f'[PAGOPA] ❌ ERRORE: impossibile catturare il PDF originale INPS')
        logger.info('[PAGOPA] Stack trace per debug:', stack_info=True)

    return nome_sicuro
