"""Utility Selenium per automazione procedure web INPS."""

import logging
import os

logger = logging.getLogger(__name__)
import time
import re
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def _risolvi_percorso(percorso):
    """Converte un path relativo (es. drivers/chromedriver.exe) in assoluto
    rispetto alla root del progetto."""
    p = Path(percorso)
    if p.is_absolute():
        return str(p)
    # Root del progetto: 2 livelli sopra paghe/automation.py
    root = Path(__file__).resolve().parent.parent
    return str(root / p)


def avvia_driver(chromedriver_exe=None, headless=False, window_size=None, download_dir=None):
    """Avvia Chrome in modalità visibile (default) con chromedriver specificato.
    
    Args:
        chromedriver_exe: path al chromedriver.exe (relativo o assoluto).
                          Se None, usa il default 'drivers/chromedriver.exe'.
        headless: se True, avvia senza finestra grafica.
        window_size: tuple (larghezza, altezza). Se None, usa --start-maximized.
        download_dir: path per download automatici. Se None, nessuna preferenza.
    
    Returns:
        webdriver.Chrome: istanza del driver pronta all'uso.
    
    Raises:
        FileNotFoundError: se chromedriver.exe non esiste.
        WebDriverException: se Chrome non viene avviato correttamente.
    """
    if chromedriver_exe is None:
        chromedriver_exe = 'drivers/chromedriver.exe'

    path = _risolvi_percorso(chromedriver_exe)
    if not os.path.exists(path):
        logger.info(f'[Chromedriver] Non trovato in: {path}. Download automatico...')
        try:
            import chromedriver_autoinstaller
            download_dir = os.path.dirname(path)
            os.makedirs(download_dir, exist_ok=True)
            result = chromedriver_autoinstaller.install(path=download_dir)
            if result:
                if result != path:
                    import shutil
                    shutil.copy2(result, path)
                logger.info(f'[Chromedriver] Scaricato: {path}')
            else:
                raise FileNotFoundError(
                    f"Chromedriver non trovato: {path}\n"
                    "Scarica chromedriver.exe in drivers/ o aggiorna il percorso "
                    "in Configurazioni Servizi Web."
                )
        except FileNotFoundError:
            raise
        except Exception as e:
            raise FileNotFoundError(
                f"Chromedriver non trovato e download fallito: {path}\n{e}"
            )

    service = Service(executable_path=path)
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('--headless=new')
    if window_size:
        options.add_argument(f'--window-size={window_size[0]},{window_size[1]}')
    else:
        options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)

    if download_dir:
        prefs = {
            'download.default_directory': download_dir,
            'download.directory_upgrade': True,
            'plugins.always_open_pdf_externally': True,
            'plugins.plugins_disabled': ['Chrome PDF Viewer'],
            'download.prompt_for_download': False,
            'safebrowsing.enabled': True,
            'profile.default_content_setting_values.automatic_downloads': 1,
            'profile.default_content_settings.popups': 0,
        }
        options.add_experimental_option('prefs', prefs)

    options.add_argument('--disable-features=PDFViewer,PDFViewerUIElements,PDFExtensionWebUI')

    driver = webdriver.Chrome(service=service, options=options)
    return driver


def chiudi_driver(driver, timeout=3):
    """Chiude il driver Chrome in modo sicuro.
    
    Args:
        driver: webdriver.Chrome da chiudere.
        timeout: secondi di attesa massima prima di forzare chiusura.
    """
    if driver is None:
        return
    try:
        driver.quit()
    except Exception:
        try:
            driver.close()
        except Exception:
            logger.warning("[PAGOPA] driver.close() fallita dopo driver.quit()")


def attendi_elemento(driver, by, valore, timeout=10):
    """Attende che un elemento sia presente e visibile nel DOM.
    
    Args:
        driver: webdriver.Chrome.
        by: selenium.webdriver.common.by.By (es. By.ID, By.CSS_SELECTOR).
        valore: valore del selettore.
        timeout: secondi massimi di attesa.
    
    Returns:
        WebElement trovato.
    
    Raises:
        TimeoutException: se l'elemento non compare entro timeout.
    """
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, valore))
    )


def attendi_e_click(driver, by, valore, timeout=10):
    """Attende un elemento e ci clicca sopra.
    
    Returns:
        WebElement cliccato.
    """
    el = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, valore))
    )
    el.click()
    return el


def attendi_e_scrivi(driver, by, valore, testo, timeout=10):
    """Attende un elemento, lo pulisce e scrive il testo.
    
    Returns:
        WebElement modificato.
    """
    el = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, valore))
    )
    el.clear()
    if testo:
        el.send_keys(testo)
    return el


def cattura_screenshot(driver, step_name=''):
    """Cattura screenshot della pagina corrente e restituisce bytes PNG + metadati.

    Returns:
        dict con chiavi: png (bytes), url (str), title (str), step_name (str), ts (str).
    """
    try:
        png_bytes = driver.get_screenshot_as_png()
    except Exception:
        png_bytes = b''
    return {
        'png': png_bytes,
        'url': driver.current_url,
        'title': driver.title,
        'step_name': step_name,
        'ts': time.strftime('%Y-%m-%d %H:%M:%S'),
    }


def salva_debug_step(driver, step_name='', cartella=None):
    """Salva HTML e analisi elementi della pagina per debug."""
    if cartella is None:
        cartella = os.path.join(os.path.dirname(__file__), '..', 'media', 'pagopa', 'DEBUG')
    try:
        os.makedirs(cartella, exist_ok=True)
        return  # DEBUG su disco disattivato (mantieni SCREENSHOT/)
        ts = time.strftime('%Y%m%d_%H%M%S')
        prefix = f'{ts}_{step_name}' if step_name else ts

        # HTML
        html = driver.page_source
        html_path = os.path.join(cartella, f'{prefix}.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)

        # Analisi elementi
        info = {
            'url': driver.current_url,
            'title': driver.title,
            'step': step_name,
            'ts': time.strftime('%Y-%m-%d %H:%M:%S'),
            'n_finestre': len(driver.window_handles),
        }
        try:
            inputs = driver.execute_script("""(function() {
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
            forms = driver.execute_script("""(function() {
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

        import json
        json_path = os.path.join(cartella, f'{prefix}.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)

        logger.info(f'[DEBUG] Salvato: {html_path}')
        logger.info(f'[DEBUG] Salvato: {json_path}')
        return html_path
    except Exception as e:
        logger.warning(f'[DEBUG] ERRORE salvataggio debug: {e}')
        return None


# =========================================================================
# FUNZIONI PAGOPA (Automazione bollettino INPS)
# =========================================================================

def pagopa_login(driver, url, cf_datore, cod_rapporto, timeout=10, delay=0.5):
    """Step 1: Naviga al sito INPS PagoPA e compila CF + Codice Rapporto.
    
    Si ferma dopo aver compilato i campi, in attesa che l'utente
    risolva il CAPTCHA manualmente nella finestra di Chrome.
    
    Args:
        driver: webdriver.Chrome avviato.
        url: URL completo della pagina INPS PagoPA.
        cf_datore: codice fiscale del datore.
        cod_rapporto: codice rapporto INPS del contratto.
        timeout: timeout attesa elementi.
        delay: pausa in secondi tra azioni.
    """
    driver.get(url)
    time.sleep(delay)

    attendi_e_scrivi(driver, By.NAME, 'codiceFiscaleUtente', cf_datore, timeout)
    attendi_e_scrivi(driver, By.NAME, 'codicePraticaUtente', cod_rapporto, timeout)

    # TAB per portare il focus sul campo CAPTCHA
    from selenium.webdriver.common.keys import Keys
    driver.find_element(By.NAME, 'codicePraticaUtente').send_keys(Keys.TAB)
    driver.switch_to.window(driver.current_window_handle)
    driver.execute_script('window.focus();')


def pagopa_prosegui_dopo_captcha(driver, timeout=120, delay=0.5):
    """Step 2: Inietta listener Ctrl+Invio nella pagina Chrome e attende
    che l'utente prema la combinazione per sottomettere il CAPTCHA.
    
    Returns:
        True se il submit è stato rilevato, False altrimenti.
    """
    import time

    # Inietta listener Ctrl+Invio che clicca il submit
    driver.execute_script("""
        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                var el = document.getElementById('submitLogin1');
                if (el) { el.click(); return; }
                var btn = document.querySelector(
                    'input[type="image"], input[type="submit"], button[type="submit"]'
                );
                if (btn) btn.click();
            }
        });
    """)

    # Attendi cambio pagina: URL diverso o elemento della pagina successiva
    current_url = driver.current_url
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if driver.current_url != current_url:
                return True
            el = attendi_elemento(driver, By.XPATH,
                "//input[@type='image' and @alt='Visualizza dati del bollettino']", timeout=1)
            if el is not None:
                return True
        except TimeoutException:
            pass
        except Exception:
            logger.warning("[PAGOPA] Eccezione nel loop attesa post-captcha")
        time.sleep(delay)

    return False


def pagopa_visualizza_bollettino(driver, timeout=10):
    """Step 3: Clicca 'Visualizza dati del bollettino' e attende il form
    sceltaTrimestre con i dropdown per Trimestre e Anno."""
    attendi_e_click(driver, By.XPATH,
        "//input[@type='image' and @alt='Visualizza dati del bollettino']", timeout)
    try:
        attendi_elemento(driver, By.ID, 'sceltaTrimestre', timeout)
        return True
    except TimeoutException:
        return False


def pagopa_seleziona_trimestre(driver, trimestre, anno, timeout=10):
    """Step 3b: Imposta Trimestre e Anno via JS (NON invia il form)."""
    import time

    trimestre_numero = int(
        trimestre.replace('Q', '')
    ) if isinstance(trimestre, str) and trimestre.startswith('Q') else int(trimestre)
    anno_int = int(anno)

    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, 'sceltaTrimestre'))
        )
    except TimeoutException:
        return False

    try:
        driver.execute_script("""
            var elTrim = document.getElementById('trimestreRetribuzione');
            var elAnno = document.getElementById('anno');
            if (elTrim) {
                elTrim.value = '%s';
                elTrim.dispatchEvent(new Event('change', {bubbles: true}));
                elTrim.dispatchEvent(new Event('input', {bubbles: true}));
            }
            if (elAnno) {
                elAnno.value = '%s';
                elAnno.dispatchEvent(new Event('change', {bubbles: true}));
                elAnno.dispatchEvent(new Event('input', {bubbles: true}));
            }
        """ % (str(trimestre_numero), str(anno_int)))
        time.sleep(0.5)
    except Exception as e:
        logger.warning(f'[PAGOPA] ERRORE JS sceltaTrimestre: {e}')
        return False

    return True


def pagopa_conferma_trimestre(driver, timeout=10):
    """Step 3c: Invia il form sceltaTrimestre e attende la pagina oreRetribuite."""
    import time

    try:
        driver.execute_script("""
            var form = document.getElementById('sceltaTrimestre');
            if (form) form.submit();
        """)
        # Aspetta la navigazione — attendi sceltaTrimestre scomparsa o oreRetribuite o carrello
        deadline = time.time() + timeout
        navigato = False
        while time.time() < deadline:
            try:
                WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.ID, 'oreRetribuite'))
                )
                logger.info(f'[PAGOPA] Navigato direttamente a #oreRetribuite.')
                return True
            except TimeoutException:
                pass
            current_url = driver.current_url.lower()
            if 'visualizzacarrello' in current_url:
                navigato = True
                break
            time.sleep(0.5)
        if not navigato:
            logger.info(f'[PAGOPA] TIMEOUT navigazione dopo submit trimestre.')
            return False
    except Exception as e:
        logger.warning(f'[PAGOPA] ERRORE submit/navigazione: {e}')
        return False

    # Se la pagina intermedia visualizzaCarrello, clicca Visualizza dati/Modifica
    try:
        logger.info(f'[PAGOPA] Pagina carrello. Cerco pulsante Visualizza dati/Modifica...')
        sel = (By.XPATH, "//input[@type='image' and (@alt='Visualizza dati del bollettino' or @title='Visualizza dati/Modifica')]")
        attendi_elemento(driver, *sel, timeout)
        driver.find_element(*sel).click()
        logger.info(f'[PAGOPA] Cliccato Visualizza dati/Modifica.')
        time.sleep(1)
    except Exception as e:
        logger.warning(f'[PAGOPA] ERRORE click Visualizza dati/Modifica: {e}')

    try:
        attendi_elemento(driver, By.ID, 'oreRetribuite', timeout)
        return True
    except TimeoutException:
        return False


def _estrai_totale_inps_selenium(driver):
    """Cerca il totale/importo nella pagina INPS dopo il calcolo contributi (Selenium)."""
    import re
    try:
        body_el = driver.find_element(By.TAG_NAME, 'body')
        body_text = body_el.text
    except Exception:
        return None

    candidati = []

    # 1) td.tdDesc
    try:
        tds = driver.find_elements(By.CSS_SELECTOR, 'td.tdDesc')
        for td in tds:
            txt = td.text.strip()
            for n in re.findall(r'[\d]{1,3}(?:\.[\d]{3})*(?:,\d{2})', txt):
                try:
                    v = float(n.replace('.', '').replace(',', '.'))
                    if 1 < v < 100000:
                        candidati.append(v)
                except ValueError:
                    continue
    except Exception:
        logger.warning("[PAGOPA] Estrazione td.tdDesc fallita in _estrai_totale_inps_selenium")

    # 2) Pattern €
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

    # 5) Il più grande è il totale
    if candidati:
        return max(candidati)

    # 5) Keyword "totale"/"importo" fallback
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

    # 2) Cerca pattern "€ X.XXX,XX" o "X.XXX,XX €"
    pattern_eur1 = r'€\s*([\d]{1,3}(?:[.,][\d]{3})*(?:[.,]\d{2}))'
    pattern_eur2 = r'([\d]{1,3}(?:[.,][\d]{3})*(?:[.,]\d{2}))\s*€'
    vals = []
    for p in [pattern_eur1, pattern_eur2]:
        for m in re.finditer(p, body_text):
            try:
                raw = m.group(1).replace('.', '').replace(',', '.')
                v = float(raw)
                if 1 < v < 100000:
                    vals.append(v)
            except ValueError:
                continue
    if vals:
        return max(vals)

    # 3) Cerca "totale" o "importo" e prende il numero successivo
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

    # 4) Fallback: tutti i numeri formato italiano nel body
    all_nums = re.findall(r'(?<!\d)[\d]{1,3}(?:\.[\d]{3})*(?:,\d{2})(?!\d)', body_text)
    for n in all_nums:
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
    
    Args:
        driver: webdriver.Chrome.
        ore_trim: ore trimestrali (int).
        paga_oraria: paga oraria INPS (float/string).
        codice_associazione: codice ente bilaterale (es. 'F', 'E').
        quota_trim: quota associativa trimestrale (float/string).
        trimestre: numero trimestre (1-4).
        anno: anno di riferimento (int/string).
        timeout: timeout attesa elementi.
        download_dir: cartella documenti (per screenshot in SCREENSHOT/).
        nome_file: nome file PAGOPA (per derivare nome screenshot).
    """
    attendi_e_scrivi(driver, By.ID, 'oreRetribuite', str(int(ore_trim)), timeout)
    attendi_e_scrivi(driver, By.ID, 'retribuzioneOrariaEffettiva',
        f'{paga_oraria:.2f}'.replace(',', '.'), timeout)

    # Seleziona associazione dal menu a tendina
    try:
            select_el = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.ID, 'codiceAssociazione'))
            )
            from selenium.webdriver.support.ui import Select
            select = Select(select_el)
            # Cerca l'opzione che contiene il codice associazione
            for opt in select.options:
                if opt.text.strip().startswith(codice_associazione):
                    select.select_by_visible_text(opt.text)
                    break
            else:
                # Fallback: primo elemento non vuoto
                for opt in select.options:
                    if opt.text.strip():
                        select.select_by_visible_text(opt.text)
                        break
    except Exception:
        logger.warning("[PAGOPA] Selezione #codiceAssociazione fallita")

    # Se esiste il campo quotaAssociativa
    try:
        driver.find_element(By.ID, 'quotaAssociativa')
        attendi_e_scrivi(driver, By.ID, 'quotaAssociativa',
            f'{quota_trim:.2f}'.replace(',', '.'), timeout)
    except Exception:
        logger.warning("[PAGOPA] Campo #quotaAssociativa non presente o errore")

    # Imposta trimestre e anno via JS, poi submit diretto bypassando AJAX/jQuery
    time.sleep(0.5)
    trimestre_numero = int(trimestre.replace('Q', '')) if isinstance(trimestre, str) and trimestre.startswith('Q') else int(trimestre)
    try:
        driver.execute_script("""
            var elTrim = document.getElementById('trimestreRetribuzione');
            var elAnno = document.getElementById('anno');
            var elTrimC = document.getElementById('trimestreRetribuzioneCorrente');
            var elAnnoC = document.getElementById('annoCorrente');
            if (elTrim) elTrim.value = '%s';
            if (elAnno) elAnno.value = '%s';
            if (elTrimC) elTrimC.value = '%s';
            if (elAnnoC) elAnnoC.value = '%s';
            var form = document.getElementById('rapportoLavoro');
            if (form) { form.submit(); return true; }
            return false;
        """ % (str(trimestre_numero), str(int(anno)), str(trimestre_numero), str(int(anno))))
        logger.info(f'[PAGOPA] Submit diretto: trimestre={trimestre_numero}, anno={anno}')
    except Exception as e:
        logger.warning(f'[PAGOPA] ERRORE submit diretto: {e}')

    # Attesa navigazione dopo submit (permette alla view di catturare schermata calcolaContributi.do in memoria)
    try:
        from selenium.webdriver.support.ui import WebDriverWait
        WebDriverWait(driver, timeout).until(
            lambda d: 'calcolaContributi' in d.current_url or 'gestioneCarrello' in d.current_url
        )
        logger.info(f'[PAGOPA] ✅ Navigazione completata dopo submit. URL: {driver.current_url[:150]}')
    except Exception as e:
        logger.warning(f'[PAGOPA] ⏭️ Navigazione dopo submit: {e}. URL: {driver.current_url[:150]}')

    # Estrai totale INPS dalla pagina (solo log, non affidabile — il vero totale è su gestioneCarrello.do)
    try:
        totale_inps = _estrai_totale_inps_selenium(driver)
        if totale_inps is not None:
            logger.info(f'[PAGOPA] 💰 Totale INPS su calcolaContributi: € {totale_inps:.2f} (non usato)')
    except Exception as e:
        logger.warning(f'[PAGOPA] ❌ ERRORE estrazione totale INPS: {e}')
    return None


def pagopa_avanti(driver, timeout=10, delay=0.5):
    """Step 5: Clicca 'Avanti' e attende 'Conferma modifica'.
    
    Se il form è già stato inviato (da pagopa_compila_bollettino con form.submit()),
    salta il click e attende direttamente 'Conferma modifica'.
    """
    import time

    time.sleep(delay)

    # Se già su Conferma modifica, salta click Avanti
    try:
        driver.find_element(By.XPATH, "//input[@type='image' and @alt='Conferma modifica']")
        logger.info('[PAGOPA] Già su Conferma modifica, salto click Avanti')
        return True
    except Exception:
        logger.warning("[PAGOPA] Check Conferma modifica fallito")

    # Prova con JavaScript: trova l'input con alt='Avanti' e cliccalo
    try:
        driver.execute_script("""
            var el = document.querySelector('input[alt="Avanti"]');
            if (el) { el.click(); return true; }
            el = document.querySelector('#sceltaTrimestre > input.linkImg:last-of-type');
            if (el) { el.click(); return true; }
            var all = document.querySelectorAll('#sceltaTrimestre input');
            if (all.length > 0) { all[all.length-1].click(); return true; }
            return false;
        """)
    except Exception:
        logger.warning("[PAGOPA] JS Avanti click fallito")

    # Fallback: attendi elemento con Selenium
    for by, sel in [
        (By.CSS_SELECTOR, 'input[alt="Avanti"]'),
        (By.CSS_SELECTOR, '#sceltaTrimestre > input.linkImg'),
        (By.XPATH, "//*[@id='sceltaTrimestre']/input[6]"),
    ]:
        try:
            WebDriverWait(driver, 3).until(EC.element_to_be_clickable((by, sel))).click()
            break
        except Exception:
            logger.debug("[PAGOPA] Selettore Avanti fallito nel loop")
            continue
    else:
        # Ultimate fallback: clicca l'ultimo input visibile dentro #sceltaTrimestre
        try:
            inputs = driver.find_elements(By.CSS_SELECTOR, '#sceltaTrimestre input')
            for inp in reversed(inputs):
                if inp.is_displayed():
                    driver.execute_script("arguments[0].click();", inp)
                    break
        except Exception:
            return False

    try:
        attendi_elemento(driver, By.XPATH,
            "//input[@type='image' and @alt='Conferma modifica']", timeout)
        return True
    except TimeoutException:
        return False


def pagopa_conferma_modifica(driver, timeout=10):
    """Step 6: Clicca 'Conferma modifica' e attende la navigazione.

    Dopo la navigazione, estrae il totale dalla pagina gestioneCarrello.do.
    Returns:
        float or None: importo totale estratto dalla pagina.
    """
    try:
        el = attendi_elemento(driver, By.XPATH,
            "//input[@type='image' and @alt='Conferma modifica']", timeout)
        old_url = driver.current_url
        el.click()
        WebDriverWait(driver, timeout).until(
            lambda d: d.current_url != old_url
        )
    except TimeoutException:
        return None

    # Estrai totale dalla pagina (gestioneCarrello.do)
    try:
        totale_inps = _estrai_totale_inps_selenium(driver)
        if totale_inps is not None:
            logger.info(f'[PAGOPA] 💰 Totale INPS da gestioneCarrello: € {totale_inps:.2f}')
        else:
            logger.info(f'[PAGOPA] 💰 Totale INPS non rilevato in gestioneCarrello.')
        return totale_inps
    except Exception as e:
        logger.warning(f'[PAGOPA] ❌ ERRORE estrazione totale INPS da gestioneCarrello: {e}')
        return None


def _estrai_pdf_da_nuova_scheda_selenium(driver, timeout=10):
    """Estrae URL PDF dalla finestra corrente (già switched)."""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
    except Exception:
        logger.warning("[PAGOPA] Attesa readyState fallita in _estrai_pdf_da_nuova_scheda_selenium")
    url = driver.current_url
    logger.info(f'[PAGOPA] Nuova finestra URL: {url}')
    if '.pdf' in url.lower():
        return url
    try:
        import re
        html = driver.page_source
        for sel in ['embed[type="application/pdf"]', 'object[type="application/pdf"]',
                    'embed[src*=".pdf"]', 'object[data*=".pdf"]']:
            try:
                el = driver.find_element(By.CSS_SELECTOR, sel)
                if el:
                    url_pdf = el.get_attribute('src') or el.get_attribute('data')
                    if url_pdf:
                        from urllib.parse import urljoin
                        logger.info(f'[PAGOPA] PDF da {sel}: {url_pdf}')
                        return urljoin(url, url_pdf)
            except Exception:
                logger.debug("[PAGOPA] Selettore embed/object fallito in _estrai_pdf")
                continue
        for m in re.finditer(r'<iframe[^>]+src=["\']([^"\']*\.pdf[^"\']*)["\']', html, re.I):
            return m.group(1)
        for m in re.finditer(r'(https?://[^"\'<>]+\.pdf[^"\'<>]*)', html):
            return m.group(1)
    except Exception as e:
        logger.warning(f'[PAGOPA] ERRORE estrazione PDF: {e}')
    return None


def pagopa_stampa_avviso(driver, timeout=10, delay=0.5):
    """Step 7: Click Stampa Avviso — genera il PDF.

    Flusso:
      1. Trova il pulsante su gestioneCarrello.do e clicca
      2. Se la pagina naviga a generaAvvisiPagamento.do, secondo click per aprire PDF
      3. Se si apre una nuova finestra, estrai URL PDF
      4. Se non succede nulla, ritorna True comunque — pagopa_switch_finestra_e_salva
         catturerà il PDF con strategie alternative
    """
    xpath = "//input[@type='image' and @alt='Stampa Avviso di Pagamento']"
    original_url = driver.current_url
    logger.info(f'[PAGOPA] Stampa Avviso. URL: {original_url}')

    # Trova pulsante
    try:
        attendi_elemento(driver, By.XPATH, xpath, timeout)
    except TimeoutException:
        logger.info(f'[PAGOPA] ERRORE: pulsante non trovato su {driver.current_url}')
        return False

    # Click con doppio tentativo (Selenium + nativo DOM)
    if 'generaAvvisiPagamento' in original_url:
        click_desc = 'Click su generaAvvisiPagamento.do (→ PDF)'
    else:
        click_desc = 'Click su gestioneCarrello.do (→ generea Avviso)'

    click_ok = False
    try:
        el = driver.find_element(By.XPATH, xpath)
        el.click()
        logger.info(f'[PAGOPA] {click_desc}: click Selenium eseguito.')
        click_ok = True
    except Exception as e:
        logger.info(f'[PAGOPA] {click_desc}: click Selenium fallito ({e}). Provo nativo...')
        try:
            driver.execute_script(
                "document.evaluate(arguments[0], document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue?.click()",
                xpath
            )
            logger.info(f'[PAGOPA] {click_desc}: click nativo eseguito.')
            click_ok = True
        except Exception as e2:
            logger.warning(f'[PAGOPA] {click_desc}: click nativo fallito ({e2})')

    if not click_ok:
        return False

    time.sleep(delay)

    # Se già su generaAvvisiPagamento.do, salva URL e termina
    if 'generaAvvisiPagamento' in original_url or 'generaAvvisiPagamento' in driver.current_url:
        driver.execute_script("window._pagopaPdfUrl = window.location.href;")
        logger.info(f'[PAGOPA] Già su generaAvvisiPagamento.do. URL salvato come fallback.')
        logger.info(f'[PAGOPA] Stampa Avviso completato.')
        return True

    # Polling breve per navigazione a generaAvvisiPagamento.do o nuova finestra
    wh_before = driver.window_handles
    finestra_originale = driver.current_window_handle
    navigato = False
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(0.5)
        try:
            # Cambio URL nella stessa finestra
            if 'generaAvvisiPagamento' in driver.current_url:
                logger.info(f'[PAGOPA] Navigato a generaAvvisiPagamento.do. URL: {driver.current_url}')
                # Secondo click per aprire il PDF
                try:
                    attendi_elemento(driver, By.XPATH, xpath, 5)
                    el = driver.find_element(By.XPATH, xpath)
                    el.click()
                    logger.info(f'[PAGOPA] Secondo click eseguito su generaAvvisiPagamento.do')
                except Exception:
                    driver.execute_script("window._pagopaPdfUrl = window.location.href;")
                    logger.info(f'[PAGOPA] Seconda pagina: URL corrente salvato come fallback.')
                navigato = True
                break

            # Nuova finestra aperta
            wh_ora = driver.window_handles
            if len(wh_ora) > len(wh_before):
                nuova_wh = [h for h in wh_ora if h not in wh_before][0]
                driver.switch_to.window(nuova_wh)
                logger.info(f'[PAGOPA] Nuova finestra rilevata. URL: {driver.current_url}')
                pdf_url = _estrai_pdf_da_nuova_scheda_selenium(driver, timeout=5)
                driver.switch_to.window(finestra_originale)
                if pdf_url:
                    escaped = pdf_url.replace("'", "\\'")
                    driver.execute_script(f"window._pagopaPdfUrl = '{escaped}';")
                    logger.info(f'[PAGOPA] PDF URL salvato da nuova finestra: {pdf_url}')
                navigato = True
                break
        except Exception:
            logger.debug("[PAGOPA] Eccezione nel polling navigazione Stampa Avviso")
            continue

    if not navigato:
        logger.info(f'[PAGOPA] Nessuna navigazione rilevata. Il PDF verrà catturato da pagopa_switch_finestra_e_salva.')

    logger.info(f'[PAGOPA] Stampa Avviso completato.')
    return True


def _scarica_pdf_da_url(driver, url, referer=None):
    """Scarica un PDF da URL assoluto usando i cookie di sessione di Chrome."""
    import requests
    import base64

    if url.startswith('data:application/pdf;base64,'):
        _, encoded = url.split(',', 1)
        logger.info(f'[PAGOPA] PDF da data URL (base64, {len(encoded)} chars)')
        return base64.b64decode(encoded)

    cookies = {c['name']: c['value'] for c in driver.get_cookies()}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    if referer:
        headers['Referer'] = referer
    logger.info(f'[PAGOPA] Scarico PDF da: {url[:200]}')
    r = requests.get(url, cookies=cookies, headers=headers, timeout=30)
    r.raise_for_status()
    return r.content


def pagopa_switch_finestra_e_salva(driver, nome_file, timeout=10, download_dir=None):
    """Step 8: Dopo 'Stampa Avviso', cattura il PDF.
    
    Strategia:
    1. Verifica window.open interceptor per URL catturato
    2. Controlla se l'URL corrente è cambiato (PDF diretto)
    3. Attesa nuova finestra con WebDriverWait
    4. Nella nuova finestra cerca URL PDF, embed/object, iframe
    5. Page.printToPDF sulla nuova finestra
    6. Fallback: iframe #frameStampa
    7. Fallback finale: Page.printToPDF sulla finestra originale
    
    Args:
        driver: webdriver.Chrome.
        nome_file: nome desiderato per il file PDF.
        timeout: timeout attesa elementi.
        download_dir: cartella dove salvare il PDF.
    
    Returns:
        str: nome finale del file.
    """
    import base64
    import requests
    from urllib.parse import urljoin

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

    # Salva sempre debug HTML della pagina dopo Stampa Avviso
    try:
        nome_html = nome_sicuro.rsplit('.', 1)[0] + '.html'
        with open(os.path.join(debug_dir, 'dopostampa_' + nome_html), 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        logger.info(f'[PAGOPA] HTML salvato: dopostampa_{nome_html}')
    except Exception as e:
        logger.warning(f'[PAGOPA] ERRORE salvataggio HTML: {e}')

    # TENTATIVO 0: URL catturato da _pagopaPdfUrl
    url_captured = None
    try:
        url_captured = driver.execute_script("return window._pagopaPdfUrl || null;")
    except Exception:
        logger.info("[PAGOPA] JS _pagopaPdfUrl non disponibile su finestra corrente")
    # Cerca anche su TUTTE le altre finestre
    if not url_captured:
        wh_originale = driver.current_window_handle
        for wh in driver.window_handles:
            if wh == wh_originale:
                continue
            try:
                driver.switch_to.window(wh)
                url_captured = driver.execute_script("return window._pagopaPdfUrl || null;")
                if url_captured:
                    logger.info(f'[PAGOPA] _pagopaPdfUrl trovato su altra finestra: {url_captured}')
                    break
            except Exception:
                continue
        try:
            driver.switch_to.window(wh_originale)
        except Exception:
            logger.warning("[PAGOPA] Switch a finestra originale fallito (1)")
    if url_captured:
        logger.info(f'[PAGOPA] URL catturato: {url_captured}')
        try:
            pdf_data = _scarica_pdf_da_url(driver, url_captured)
        except Exception as e:
            logger.warning(f'[PAGOPA] Download da _pagopaPdfUrl fallito: {e}')

    # TENTATIVO 0b: URL corrente cambiato (PDF diretto)
    url_corrente = driver.current_url
    logger.info(f'[PAGOPA] URL corrente dopo Stampa Avviso: {url_corrente}')
    if pdf_data is None and '.pdf' in url_corrente.lower():
        try:
            pdf_data = _scarica_pdf_da_url(driver, url_corrente)
            logger.info(f'[PAGOPA] PDF scaricato da URL corrente')
        except Exception as e:
            logger.warning(f'[PAGOPA] Download URL corrente fallito: {e}')

    # TENTATIVO 0c: estrae form stampaAvvisoDiPagamento e scarica PDF via richiesta diretta
    if pdf_data is None:
        try:
            csrf = None
            forms_data = driver.execute_script("""
                var form = document.querySelector('form[action*="stampaAvvisoDiPagamento"]');
                if (!form) return null;
                var action = form.getAttribute('action');
                var csrfInput = form.querySelector('input[name="csrfTokenClient"]');
                var csrf = csrfInput ? csrfInput.value : '';
                return { action: action, csrf: csrf };
            """)
            if forms_data and forms_data.get('action'):
                action = forms_data['action']
                csrf = forms_data.get('csrf', '')
                if not action.startswith('http'):
                    action = 'https://serviziweb2.inps.it' + action
                cookies = {c['name']: c['value'] for c in driver.get_cookies()}
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                params = {}
                if csrf:
                    params['csrfTokenClient'] = csrf
                logger.info(f'[PAGOPA] Richiesta PDF a: {action}')
                r = requests.get(action, params=params, cookies=cookies, headers=headers, timeout=30)
                if r.status_code == 200 and len(r.content) > 500:
                    content_type = r.headers.get('Content-Type', '')
                    if 'pdf' in content_type or r.content[:4] == b'%PDF':
                        pdf_data = r.content
                        logger.info(f'[PAGOPA] PDF scaricato da stampaAvvisoDiPagamento.do ({len(pdf_data)} bytes)')
                    else:
                        logger.info(f'[PAGOPA] Risposta da stampaAvvisoDiPagamento: {content_type}, {len(r.content)} bytes')
                else:
                    logger.info(f'[PAGOPA] Risposta HTTP {r.status_code} da stampaAvvisoDiPagamento')
        except Exception as e:
            logger.warning(f'[PAGOPA] ERRORE richiesta stampaAvvisoDiPagamento: {e}')

    # TENTATIVO 1: nuova finestra / tab
    finestre_iniziali = set(driver.window_handles)
    if pdf_data is None:
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: len(d.window_handles) > len(finestre_iniziali)
            )
            time.sleep(1)
        except TimeoutException:
            logger.info('[PAGOPA] Nessuna nuova finestra rilevata')

    finestre_dopo = set(driver.window_handles)
    nuove_handle = list(finestre_dopo - finestre_iniziali)

    if nuove_handle:
        nuova_handle = nuove_handle[0]
        driver.switch_to.window(nuova_handle)
        time.sleep(3)
        url_nuova = driver.current_url
        logger.info(f'[PAGOPA] Nuova finestra URL: {url_nuova}')

        # 1a: URL PDF diretto
        if pdf_data is None and '.pdf' in url_nuova.lower():
            try:
                pdf_data = _scarica_pdf_da_url(driver, url_nuova)
                logger.info(f'[PAGOPA] PDF scaricato da URL diretto (nuova finestra)')
            except Exception as e:
                logger.warning(f'[PAGOPA] Download URL diretto fallito: {e}')

        # 1b: cerca URL .pdf nella page_source
        if pdf_data is None:
            try:
                urls_pdf = re.findall(r'https?://[^"\'<>]+\.pdf[^"\'<>]*', driver.page_source)
                logger.info(f'[PAGOPA] Trovati {len(urls_pdf)} URL PDF in nuova finestra')
                for url_pdf in urls_pdf[:3]:
                    try:
                        pdf_data = _scarica_pdf_da_url(driver, url_pdf)
                        if pdf_data:
                            logger.info(f'[PAGOPA] PDF scaricato da URL in nuova finestra')
                            break
                    except Exception:
                        logger.debug("[PAGOPA] Download URL PDF fallito, prossimo tentativo")
                        continue
            except Exception:
                logger.info("[PAGOPA] Ricerca URL pdf in page source fallita")

        # 1c: embed/object
        if pdf_data is None:
            for sel in ['embed[type="application/pdf"]', 'object[type="application/pdf"]',
                        'embed[src*=".pdf"]', 'object[data*=".pdf"]']:
                try:
                    el = driver.find_element(By.CSS_SELECTOR, sel)
                    url = el.get_attribute('src') or el.get_attribute('data')
                    if url:
                        pdf_data = _scarica_pdf_da_url(driver, urljoin(url_nuova, url))
                        if pdf_data:
                            break
                except Exception:
                    logger.debug("[PAGOPA] Selettore embed/object fallito in nuova finestra")
                    continue

        # 1d: iframe → _scarica_pdf_da_url con Referer
        if pdf_data is None:
            try:
                iframe = driver.find_element(By.TAG_NAME, 'iframe')
                src = iframe.get_attribute('src')
                if src:
                    url_target = urljoin(url_nuova, src)
                    logger.info(f'[PAGOPA] iframe src: {url_target[:200]}')
                    logger.info(f'[PAGOPA] 🏠 Referer: {url_nuova[:200]}')
                    result = _scarica_pdf_da_url(driver, url_target, referer=url_nuova)
                    if result and result[:4] == b'%PDF':
                        pdf_data = result
                        logger.info(f'[PAGOPA] ✅ PDF da iframe Referer ({len(pdf_data)} bytes)')
                    elif result:
                        logger.info(f'[PAGOPA] ⚠️ Scaricati {len(result)} bytes ma non PDF')
                    else:
                        logger.info(f'[PAGOPA] ⏭️ _scarica_pdf_da_url None')
            except Exception as e:
                logger.warning(f'[PAGOPA] ❌ iframe Referer fallito: {e}')

        # 1e: Page.printToPDF sulla nuova finestra
        if pdf_data is None:
            try:
                logger.info('[PAGOPA] Page.printToPDF sulla nuova finestra...')
                result = driver.execute_cdp_cmd('Page.printToPDF', {
                    'printBackground': True, 'paperWidth': 21.0, 'paperHeight': 29.7,
                    'marginTop': 1.0, 'marginBottom': 1.0, 'marginLeft': 1.0, 'marginRight': 1.0,
                    'preferCSSPageSize': True,
                })
                pdf_data = base64.b64decode(result['data'])
            except Exception as e:
                logger.warning(f'[PAGOPA] Page.printToPDF nuova finestra fallito: {e}')

        # Torna alla finestra originale
        try:
            driver.close()
        except Exception:
            logger.warning("[PAGOPA] Chiusura nuova finestra fallita")
        try:
            finestra_originale = list(finestre_iniziali)[0] if finestre_iniziali else driver.window_handles[0]
            driver.switch_to.window(finestra_originale)
        except Exception:
            logger.warning("[PAGOPA] Switch a finestra originale fallito (2)")

    # TENTATIVO 2: cerca frame/embed/object PDF e scarica con Referer
    if pdf_data is None:
        logger.info(f'[PAGOPA] Tentativo 2: cerca frame/embed/object PDF con Referer...')
        pdf_url = None
        referer_url = driver.current_url
        # Cerca #frameStampa (IFrame INPS)
        try:
            iframe = WebDriverWait(driver, max(3, timeout // 2)).until(
                EC.presence_of_element_located((By.ID, 'frameStampa'))
            )
            pdf_url = iframe.get_attribute('src')
            if pdf_url:
                logger.info(f'[PAGOPA] iframe #frameStampa src: {pdf_url[:200]}')
        except Exception:
            logger.info("[PAGOPA] #frameStampa non trovato")
        # Fallback: cerca iframe/embed/object con PDF
        if not pdf_url:
            for sel, attr in [('iframe[src*="stampaAvviso"]', 'src'), ('iframe[src*=".pdf"]', 'src'),
                              ('embed[type="application/pdf"]', 'src'), ('object[type="application/pdf"]', 'data'),
                              ('embed[src*=".pdf"]', 'src'), ('object[data*=".pdf"]', 'data')]:
                try:
                    el = driver.find_element(By.CSS_SELECTOR, sel)
                    pdf_url = el.get_attribute(attr)
                    if pdf_url:
                        from urllib.parse import urljoin
                        pdf_url = urljoin(referer_url, pdf_url)
                        logger.info(f'[PAGOPA] {sel}: {pdf_url[:200]}')
                        break
                except Exception:
                    logger.debug("[PAGOPA] Selettore iframe/embed/object fallito in fallback")
                    continue
        if not pdf_url:
            logger.info(f'[PAGOPA] ☑️ Salto: nessun frame/embed/object PDF trovato')
            try:
                tags = driver.execute_script("""return Array.from(document.querySelectorAll('iframe, embed, object, a[href$=".pdf"]')).map(function(el){return{tag:el.tagName,src:el.src||el.getAttribute('src')||el.href||el.getAttribute('data')||'',id:el.id||'',cls:el.className||''}}).slice(0,20)""")
                logger.info(f'[PAGOPA] 🔎 Tag iframe/embed/object/a.pdf:')
                for t in (tags or []):
                    logger.info(f'[PAGOPA]     <{t["tag"]}> id="{t["id"]}" src="{t["src"][:150]}"')
            except Exception as e2:
                logger.warning(f'[PAGOPA]     ⚠️ Diagnostica fallita: {e2}')
        if pdf_url:
            try:
                logger.info(f'[PAGOPA] 🏠 Referer: {referer_url[:200]}')
                result = _scarica_pdf_da_url(driver, pdf_url, referer=referer_url)
                if result and result[:4] == b'%PDF':
                    pdf_data = result
                    logger.info(f'[PAGOPA] ✅ PDF originale ottenuto ({len(pdf_data)} bytes)')
                elif result:
                    logger.info(f'[PAGOPA] ⚠️ Scaricato {len(result)} bytes ma non è PDF. Primi 200: {result[:200]}')
                else:
                    logger.info(f'[PAGOPA] ⏭️ _scarica_pdf_da_url ha restituito None')
            except Exception as e:
                logger.warning(f'[PAGOPA] ❌ Download fallito: {e}')

    # TENTATIVO 3: Page.printToPDF sulla finestra originale (ultima risorsa)
    if pdf_data is None:
        try:
            logger.info('[PAGOPA] Page.printToPDF sulla finestra originale...')
            result = driver.execute_cdp_cmd('Page.printToPDF', {
                'printBackground': True, 'paperWidth': 21.0, 'paperHeight': 29.7,
                'marginTop': 1.0, 'marginBottom': 1.0, 'marginLeft': 1.0, 'marginRight': 1.0,
                'preferCSSPageSize': True,
            })
            pdf_data = base64.b64decode(result['data'])
        except Exception as e:
            logger.warning(f'[PAGOPA] Page.printToPDF originale fallito: {e}')

    # Salvataggio
    if pdf_data:
        destinazione = os.path.join(cartella, nome_sicuro)
        with open(destinazione, 'wb') as f:
            f.write(pdf_data)
        logger.info(f'[PAGOPA] PDF salvato: {os.path.basename(destinazione)} ({len(pdf_data)} bytes)')
    else:
        logger.info(f'[PAGOPA] ERRORE: impossibile catturare il PDF')

    return nome_sicuro