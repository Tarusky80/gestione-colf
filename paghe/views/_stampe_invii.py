"""Modulo _stampe_invii - generato automaticamente da views.py"""

from paghe.views._common_imports import *

logger = logging.getLogger(__name__)

from paghe.views._helpers import _get_cartella_documenti, _genera_pdf_da_testo_playwright, _stampa_pdf_windows, _assicura_cartella_stampe, _crea_pagina_bianca, _unisci_pdf_bytes
from paghe.views._constants import CARTELLA_STAMPE_TEMP
from paghe.views._calcoli_core import _calcola_busta_data, _calcola_busta_inversa_data, _calcola_busta_conviventi_ccnl_data
from paghe.views._buste_pdf import _genera_busta_completa_pdf_bytes
from paghe.views._testi import _risolvi_variabili_testo
from paghe.views._tfr_cessazione import _calcola_tfr_fino_a, _build_liquidazione_tfr_pdf_bytes
from paghe.views._invia_email import invia_documento_email




# --- ajax_apri_cartella_documenti ---
@login_required
@never_cache
@login_required
def ajax_apri_cartella_documenti(request):
    """Apre la cartella documenti in Explorer Windows."""
    import subprocess
    opzioni = get_opzioni()
    contratto_pk = request.GET.get('contratto_pk') or request.POST.get('contratto_pk')

    if contratto_pk:
        contratto = get_object_or_404(ContrattoAttivo, pk=contratto_pk)
        path = _get_cartella_documenti(contratto)
    elif opzioni and opzioni.cartella_documenti:
        path = opzioni.cartella_documenti
    else:
        return JsonResponse({'success': False, 'error': 'Cartella non configurata.'})

    if os.path.isdir(path):
        try:
            subprocess.Popen(['explorer', path])
            return JsonResponse({'success': True})
        except Exception as e:
            logger.exception("Errore in ajax_apri_cartella_documenti")
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Cartella non trovata.'})


# --- ajax_apri_cartella_download ---
@login_required
@never_cache
def ajax_apri_cartella_download(request):
    """Apre la cartella Download in Explorer Windows."""
    import subprocess
    download_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
    if os.path.isdir(download_folder):
        try:
            subprocess.Popen(['explorer', download_folder])
            return JsonResponse({'success': True})
        except Exception as e:
            logger.exception("Errore in ajax_apri_cartella_download")
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Cartella Download non trovata.'})


# --- configurazioni_servizi ---


@login_required
@never_cache
def configurazioni_servizi(request):
    import subprocess, os, re
    from pathlib import Path
    from paghe.models import ServizioWebConfig

    opzioni = get_opzioni()
    web_config = ServizioWebConfig.get_singleton()
    ctx = {'opzioni': opzioni, 'web_config': web_config}

    if request.method == 'POST':
        if 'chromedriver_exe' in request.POST:
            nuovo_path = request.POST.get('chromedriver_exe', '').strip()
            if opzioni and nuovo_path:
                opzioni.chromedriver_exe = nuovo_path
                opzioni.save()
                return redirect('configurazioni_servizi')
        if 'use_playwright' in request.POST:
            web_config.use_playwright = request.POST.get('use_playwright') == '1'
            web_config.save()
            return redirect('configurazioni_servizi')
        if 'delay_pausa' in request.POST or 'timeout_elementi' in request.POST:
            if 'delay_pausa' in request.POST:
                try:
                    val = request.POST.get('delay_pausa', '').strip().replace(',', '.')
                    if val:
                        web_config.delay_pausa = max(0.0, min(10.0, float(val)))
                except (ValueError, TypeError):
                    logger.warning("delay_pausa non valido: %s", request.POST.get('delay_pausa'))
            if 'timeout_elementi' in request.POST:
                try:
                    val = request.POST.get('timeout_elementi', '').strip()
                    if val:
                        web_config.timeout_elementi = max(1, min(120, int(val)))
                except (ValueError, TypeError):
                    logger.warning("timeout_elementi non valido: %s", request.POST.get('timeout_elementi'))
            web_config.save()
            return redirect('configurazioni_servizi')

    # Chromedriver status
    driver_path = Path(opzioni.chromedriver_exe) if opzioni and opzioni.chromedriver_exe else Path('drivers/chromedriver.exe')
    if not driver_path.is_absolute():
        driver_path = Path(__file__).resolve().parent.parent / driver_path
    ctx['driver_path'] = str(driver_path)
    ctx['driver_exists'] = driver_path.exists()
    if ctx['driver_exists']:
        try:
            r = subprocess.run([str(driver_path), '--version'], capture_output=True, text=True, timeout=5)
            ctx['driver_version'] = r.stdout.strip() or r.stderr.strip()
        except Exception:
            logger.exception("Errore in configurazioni_servizi")
            ctx['driver_version'] = 'Errore lettura versione'

    # Chrome version (Windows registry)
    chrome_version = None
    try:
        import winreg
        for key_path in [r'SOFTWARE\Google\Chrome\BLBeacon', r'SOFTWARE\WOW6432Node\Google\Chrome\BLBeacon']:
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as k:
                    chrome_version, _ = winreg.QueryValueEx(k, 'version')
                    break
            except Exception:
                logger.exception("Errore in configurazioni_servizi")
                continue
        if not chrome_version:
            for key_path in [r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe']:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as k:
                        chrome_path, _ = winreg.QueryValueEx(k, '')
                        r = subprocess.run([chrome_path, '--version'], capture_output=True, text=True, timeout=5)
                        chrome_version = r.stdout.strip()
                        break
                except Exception:
                    logger.debug("Chrome path non trovata in chiave registro: %s", key_path)
                    continue
    except Exception:
        logger.warning("Impossibile rilevare versione Chrome dal registro")
    ctx['chrome_version'] = chrome_version

    # Compatibility check (simple: same major version)
    if ctx.get('driver_version') and ctx.get('chrome_version'):
        dv = re.search(r'ChromeDriver\s+(\d+)', ctx['driver_version'])
        cv = re.search(r'(\d+)\.', ctx['chrome_version'])
        if dv and cv:
            ctx['compatible'] = dv.group(1) == cv.group(1)
        else:
            ctx['compatible'] = None

    # INPS links reachability test
    ctx['link_iscrizione_ok'] = None
    ctx['link_cessazione_ok'] = None
    ctx['link_iscrizione_ok'] = None
    ctx['link_cessazione_ok'] = None
    ctx['link_pagopa_ok'] = None
    if opzioni and opzioni.link_inps_iscrizione:
        try:
            import urllib.request
            r = urllib.request.urlopen(opzioni.link_inps_iscrizione, timeout=5)
            ctx['link_iscrizione_ok'] = r.status == 200
        except Exception:
            logger.debug("Test connettivita' iscrizione INPS fallito")
            ctx['link_iscrizione_ok'] = False
    if web_config and web_config.link_inps_cessazione:
        try:
            import urllib.request
            r = urllib.request.urlopen(web_config.link_inps_cessazione, timeout=5)
            ctx['link_cessazione_ok'] = r.status == 200
        except Exception:
            logger.debug("Test connettivita' cessazione INPS fallito")
            ctx['link_cessazione_ok'] = False
    if web_config and web_config.link_inps_pagopa:
        try:
            import urllib.request
            r = urllib.request.urlopen(web_config.link_inps_pagopa, timeout=5)
            ctx['link_pagopa_ok'] = r.status == 200
        except Exception:
            logger.debug("Test connettivita' PagoPA INPS fallito")
            ctx['link_pagopa_ok'] = False

    # Selenium package installed
    try:
        import selenium
        ctx['selenium_versione'] = selenium.__version__
    except ImportError:
        ctx['selenium_versione'] = None

    # Playwright status
    try:
        from importlib.metadata import version as _v
        ctx['playwright_versione'] = _v('playwright')
    except ImportError:
        ctx['playwright_versione'] = None
    ctx['playwright_chromium_ok'] = False
    if ctx.get('playwright_versione'):
        try:
            from playwright.sync_api import sync_playwright
            p = sync_playwright().start()
            executable_path = p.chromium.executable_path
            ctx['playwright_chromium_path'] = executable_path
            ctx['playwright_chromium_ok'] = True
            p.stop()
        except Exception:
            logger.warning("Playwright Chromium non disponibile per verifica")

    # Cartella documenti
    ctx['cartella_documenti'] = opzioni.cartella_documenti if opzioni and opzioni.cartella_documenti else '—'
    ctx['cartella_documenti_esiste'] = os.path.isdir(ctx['cartella_documenti']) if ctx['cartella_documenti'] != '—' else False
    ctx['cartella_screenshot'] = os.path.join(ctx['cartella_documenti'], 'SCREENSHOT') if ctx['cartella_documenti'] != '—' else '—'
    ctx['cartella_screenshot_esiste'] = os.path.isdir(ctx['cartella_screenshot']) if ctx['cartella_screenshot'] != '—' else False

    return render(request, 'paghe/configurazioni_servizi.html', ctx)


# --- _genera_documento_stampe ---


def _genera_documento_stampe(contratto, tipo_documento, mese=None, anno=None, template_pk=None, user=None, request=None):
    """Genera un PDF per il tipo documento specificato.
    Restituisce (doc_archiviato, pdf_bytes) oppure (None, errore_msg).
    """
    from paghe.models import DocumentoArchiviato, ModelloDocumentale
    from datetime import date

    # ---- BUSTE PAGA ----
    if tipo_documento in ('STANDARD', 'NON_CONVIVENTE', 'INVERSO', 'NOTTURNO', 'MALATTIA'):
        if mese is None or anno is None:
            return None, 'Mese e anno richiesti per buste paga'

        if tipo_documento == 'STANDARD':
            ctx = _calcola_busta_data(contratto, mese, anno, is_convivente=True)
        elif tipo_documento == 'NON_CONVIVENTE':
            ctx = _calcola_busta_data(contratto, mese, anno, is_convivente=False)
        elif tipo_documento == 'INVERSO':
            ctx = _calcola_busta_inversa_data(contratto, mese, anno)
        elif tipo_documento == 'NOTTURNO':
            ore_m = float(contratto.ore_mensili_calcolate)
            notturno = float(contratto.parametri_minimi.notturno) if contratto.parametri_minimi else 0
            ctx = _calcola_busta_data(contratto, mese, anno, is_convivente=contratto.is_convivente)
            if 'errore' not in ctx:
                ctx['tipo_calcolo'] = 'NOTTURNO'
                ctx['indennita'].append({'label': 'Indennità Notturna', 'orario': round(notturno / ore_m, 4) if ore_m > 0 else 0, 'importo': round(notturno, 4), 'totale': round(notturno, 4)})
                ctx['totale_indennita'] = ctx.get('totale_indennita', 0) + notturno
                ctx['totale_lordo'] = round(ctx.get('totale_lordo', 0) + notturno, 2)
        elif tipo_documento == 'MALATTIA':
            giorni_malattia = 1
            sostituzione = False
            ricoverato = False
            is_conv = contratto.is_convivente
            p = contratto.parametri_minimi
            retrib_sost = float(p.retribuzione_sostituzione) if p and float(p.retribuzione_sostituzione) > 0 else 0
            if retrib_sost > 0 and is_conv:
                sostituzione = True
            date(anno, mese, 1)
            ctx = _calcola_busta_data(contratto, mese, anno, is_convivente=is_conv, sostituzione=sostituzione)
            if 'errore' not in ctx:
                from calendar import monthrange
                _, gg_mese = monthrange(anno, mese)
                gg_lavorativi = gg_mese
                ore_m = float(contratto.ore_mensili_calcolate)
                if not sostituzione:
                    paga_base_gg = (float(p.paga_base) * ore_m) / gg_lavorativi if gg_lavorativi > 0 else 0
                else:
                    paga_base_gg = (retrib_sost * ore_m) / gg_lavorativi if gg_lavorativi > 0 else 0
                if ricoverato and is_conv:
                    indennita = paga_base_gg * giorni_malattia * 0.5
                else:
                    indennita = paga_base_gg * giorni_malattia
                ctx['tipo_calcolo'] = 'MALATTIA'
                ctx['indennita'].append({'label': 'Indennità Malattia', 'orario': round(indennita / ore_m, 4) if ore_m > 0 else 0, 'importo': round(indennita, 4), 'totale': round(indennita, 4)})
                ctx['totale_indennita'] = ctx.get('totale_indennita', 0) + indennita
                ctx['totale_lordo'] = round(ctx.get('totale_lordo', 0) + indennita, 2)

        if 'errore' in ctx:
            return None, ctx.get('errore', 'Errore generazione dati')

        pdf_bytes, _ = _genera_busta_completa_pdf_bytes(contratto, mese, anno, ctx_override=ctx)
        if pdf_bytes is None:
            return None, 'Errore generazione PDF busta paga'

        tipo_archivio_map = {
            'STANDARD': 'PAGA_STANDARD', 'NON_CONVIVENTE': 'NON_CONVIVENTE',
            'INVERSO': 'CALCOLO_INVERSO', 'NOTTURNO': 'NOTTURNO', 'MALATTIA': 'MALATTIA',
        }
        tipo_archivio = tipo_archivio_map.get(tipo_documento, 'BUSTA_MASSIVA')
        label = tipo_archivio.replace('_', ' ').title()
        titolo = f"{label} – {contratto.lavoratore} – {mese:02d}/{anno}" if mese and anno else f"{label} – {contratto.lavoratore}"
        safe_name = contratto.lavoratore.nome_cognome.replace(' ', '_').replace('/', '_') if contratto.lavoratore else f"contratto_{contratto.pk}"
        nome_file = f"{tipo_archivio.lower()}_{safe_name}_{mese:02d}_{anno}.pdf" if mese and anno else f"{tipo_archivio.lower()}_{safe_name}.pdf"

        cartella = _get_cartella_documenti(contratto)
        full_path = os.path.join(cartella, nome_file)
        with open(full_path, 'wb') as f:
            f.write(pdf_bytes)

        doc = DocumentoArchiviato.objects.create(
            tipo=tipo_archivio,
            titolo=titolo,
            file_path=full_path, file_size=os.path.getsize(full_path), file_name=nome_file,
            contratto=contratto, datore=contratto.datore, lavoratore=contratto.lavoratore,
            creato_da=user,
        )
        return doc, pdf_bytes

    elif tipo_documento == 'CONVIVENTI_CCNL':
        if mese is None or anno is None:
            return None, 'Mese e anno richiesti'
        ctx = _calcola_busta_conviventi_ccnl_data(contratto, mese, anno)
        if 'errore' in ctx:
            return None, ctx.get('errore', 'Errore generazione dati')
        pdf_bytes, _ = _genera_busta_completa_pdf_bytes(contratto, mese, anno, ctx_override=ctx)
        if pdf_bytes is None:
            return None, 'Errore generazione PDF'
        safe_name = contratto.lavoratore.nome_cognome.replace(' ', '_').replace('/', '_') if contratto.lavoratore else f"contratto_{contratto.pk}"
        nome_file = f"conviventi_ccnl_{safe_name}_{mese:02d}_{anno}.pdf"
        cartella = _get_cartella_documenti(contratto)
        full_path = os.path.join(cartella, nome_file)
        with open(full_path, 'wb') as f:
            f.write(pdf_bytes)
        doc = DocumentoArchiviato.objects.create(
            tipo='CONVIVENTI_CCNL',
            titolo=f"Busta Conviventi CCNL – {contratto.lavoratore} – {mese:02d}/{anno}",
            file_path=full_path, file_size=os.path.getsize(full_path), file_name=nome_file,
            contratto=contratto, datore=contratto.datore, lavoratore=contratto.lavoratore,
            creato_da=user,
        )
        return doc, pdf_bytes

    elif tipo_documento == 'TFR_LIQUIDAZIONE':
        data_fine = date.today()
        if contratto.data_assunzione:
            mesi, tfr_mensile, totale = _calcola_tfr_fino_a(contratto, data_fine)
            pdf_bytes = _build_liquidazione_tfr_pdf_bytes(contratto, contratto.data_assunzione, data_fine, mesi, tfr_mensile, totale, 0, 0, 1)
            if pdf_bytes is None:
                return None, 'Errore generazione PDF liquidazione TFR'
            safe_name = contratto.lavoratore.nome_cognome.replace(' ', '_').replace('/', '_') if contratto.lavoratore else f"contratto_{contratto.pk}"
            nome_file = f"liquidazione_tfr_{safe_name}.pdf"
            cartella = _get_cartella_documenti(contratto)
            full_path = os.path.join(cartella, nome_file)
            with open(full_path, 'wb') as f:
                f.write(pdf_bytes)
            doc = DocumentoArchiviato.objects.create(
                tipo='BUSTA_TFR',
                titolo=f"Liquidazione TFR – {contratto.lavoratore}",
                file_path=full_path, file_size=os.path.getsize(full_path), file_name=nome_file,
                contratto=contratto, datore=contratto.datore, lavoratore=contratto.lavoratore,
                creato_da=user,
            )
            return doc, pdf_bytes
        return None, 'Data assunzione non presente'

    # ---- CONTRATTO (via Playwright) ----
    elif tipo_documento == 'CONTRATTO':
        template = ModelloDocumentale.objects.filter(tipo='CONTRATTO').first()
        if template_pk:
            template = ModelloDocumentale.objects.filter(pk=template_pk, tipo='CONTRATTO').first() or template
        if not template:
            return None, 'Nessun template CONTRATTO trovato'

        corpo_risolto = _risolvi_variabili_testo(template.corpo_testo, contratto)
        oggetto_risolto = _risolvi_variabili_testo(template.titolo, contratto) if template.titolo else ''

        cartella = _get_cartella_documenti(contratto)
        safe_name = contratto.lavoratore.nome_cognome.replace(' ', '_').replace('/', '_') if contratto.lavoratore else f"contratto_{contratto.pk}"
        nome_file = f"contratto_{safe_name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        full_path = os.path.join(cartella, nome_file)

        _genera_pdf_da_testo_playwright(oggetto_risolto, corpo_risolto, full_path,
            font_family=template.font_family or 'Arial', font_size=template.font_size or 11)
        with open(full_path, 'rb') as f:
            pdf_bytes = f.read()

        doc = DocumentoArchiviato.objects.create(
            tipo='CONTRATTO',
            titolo=f"Contratto – {contratto.lavoratore}" if not oggetto_risolto else oggetto_risolto,
            file_path=full_path, file_size=os.path.getsize(full_path), file_name=nome_file,
            contratto=contratto, datore=contratto.datore, lavoratore=contratto.lavoratore,
            creato_da=user,
        )
        return doc, pdf_bytes

    # ---- GUIDE DOCUMENTALI ----
    elif tipo_documento in ('GUIDA_ASSUNZIONE', 'GUIDA_DECALOGO', 'GUIDA_CESSAZIONE'):
        from paghe.views._guide import _genera_guida_pdf
        slug_map = {
            'GUIDA_ASSUNZIONE': 'assunzione',
            'GUIDA_DECALOGO': 'decalogo_colloquio',
            'GUIDA_CESSAZIONE': 'cessazione',
        }
        label_map = {
            'GUIDA_ASSUNZIONE': "Guida all'Assunzione",
            'GUIDA_DECALOGO': 'Decalogo del Colloquio',
            'GUIDA_CESSAZIONE': "Guida alla Cessazione",
        }
        slug = slug_map[tipo_documento]
        pdf_bytes = _genera_guida_pdf(slug, request)
        if not pdf_bytes:
            return None, 'Errore generazione PDF guida'
        nome_file = f"{tipo_documento.lower()}_{contratto.pk}.pdf"
        cartella = _get_cartella_documenti(contratto)
        full_path = os.path.join(cartella, nome_file)
        with open(full_path, 'wb') as f:
            f.write(pdf_bytes)
        doc = DocumentoArchiviato.objects.create(
            tipo=tipo_documento,
            titolo=f"{label_map[tipo_documento]} \u2013 {contratto.lavoratore}",
            file_path=full_path, file_size=os.path.getsize(full_path), file_name=nome_file,
            contratto=contratto, datore=contratto.datore, lavoratore=contratto.lavoratore,
            creato_da=user,
        )
        return doc, pdf_bytes

    # ---- CCNL ----
    elif tipo_documento == 'CCNL':
        from paghe.views._ccnl import _genera_pdf_bytes as _genera_ccnl_pdf_bytes
        pdf_bytes = _genera_ccnl_pdf_bytes()
        if not pdf_bytes:
            return None, 'Errore generazione PDF CCNL'
        nome_file = f"ccnl_{contratto.pk}.pdf"
        cartella = _get_cartella_documenti(contratto)
        full_path = os.path.join(cartella, nome_file)
        with open(full_path, 'wb') as f:
            f.write(pdf_bytes)
        doc = DocumentoArchiviato.objects.create(
            tipo='CCNL',
            titolo=f"CCNL Lavoro Domestico \u2013 {contratto.lavoratore}",
            file_path=full_path, file_size=os.path.getsize(full_path), file_name=nome_file,
            contratto=contratto, datore=contratto.datore, lavoratore=contratto.lavoratore,
            creato_da=user,
        )
        return doc, pdf_bytes

    # ---- INQUADRAMENTO ----
    elif tipo_documento == 'INQUADRAMENTO':
        from paghe.views._inquadramento import _genera_inquadramento_pdf_bytes
        pdf_bytes = _genera_inquadramento_pdf_bytes(request)
        if not pdf_bytes:
            return None, 'Errore generazione PDF Inquadramento'
        nome_file = f"inquadramento_{contratto.pk}.pdf"
        cartella = _get_cartella_documenti(contratto)
        full_path = os.path.join(cartella, nome_file)
        with open(full_path, 'wb') as f:
            f.write(pdf_bytes)
        doc = DocumentoArchiviato.objects.create(
            tipo='INQUADRAMENTO',
            titolo=f"Inquadramento Lavoro Domestico \u2013 {contratto.lavoratore}",
            file_path=full_path, file_size=os.path.getsize(full_path), file_name=nome_file,
            contratto=contratto, datore=contratto.datore, lavoratore=contratto.lavoratore,
            creato_da=user,
        )
        return doc, pdf_bytes

    # ---- TABELLE RETRIBUTIVE ----
    elif tipo_documento == 'TABELLE_RETRIBUTIVE':
        from paghe.views._tabelle_retributive import _genera_tabelle_pdf_bytes
        pdf_bytes = _genera_tabelle_pdf_bytes(request)
        if not pdf_bytes:
            return None, 'Errore generazione PDF Tabelle'
        nome_file = f"tabelle_retributive_{contratto.pk}.pdf"
        cartella = _get_cartella_documenti(contratto)
        full_path = os.path.join(cartella, nome_file)
        with open(full_path, 'wb') as f:
            f.write(pdf_bytes)
        doc = DocumentoArchiviato.objects.create(
            tipo='TABELLE_RETRIBUTIVE',
            titolo=f"Tabelle Retributive \u2013 {contratto.lavoratore}",
            file_path=full_path, file_size=os.path.getsize(full_path), file_name=nome_file,
            contratto=contratto, datore=contratto.datore, lavoratore=contratto.lavoratore,
            creato_da=user,
        )
        return doc, pdf_bytes

    # ---- CONTRIBUTI INPS CCNL ----
    elif tipo_documento == 'CONTRIBUTI_CCNL':
        from paghe.views._contributi_ccnl import _genera_contributi_pdf_bytes
        pdf_bytes = _genera_contributi_pdf_bytes(request)
        if not pdf_bytes:
            return None, 'Errore generazione PDF Contributi INPS'
        nome_file = f"contributi_inps_ccnl_{contratto.pk}.pdf"
        cartella = _get_cartella_documenti(contratto)
        full_path = os.path.join(cartella, nome_file)
        with open(full_path, 'wb') as f:
            f.write(pdf_bytes)
        doc = DocumentoArchiviato.objects.create(
            tipo='CONTRIBUTI_CCNL',
            titolo=f"Contributi INPS CCNL \u2013 {contratto.lavoratore}",
            file_path=full_path, file_size=os.path.getsize(full_path), file_name=nome_file,
            contratto=contratto, datore=contratto.datore, lavoratore=contratto.lavoratore,
            creato_da=user,
        )
        return doc, pdf_bytes

    # ---- TEMPLATE-BASED (CUD, CARTELLINA, LETTERE, etc.) via Playwright ----
    else:
        tipo_testo = tipo_documento
        template = None
        if template_pk:
            template = ModelloDocumentale.objects.filter(pk=template_pk, tipo=tipo_testo).first()
        if not template:
            template = ModelloDocumentale.objects.filter(tipo=tipo_testo).first()
        if not template:
            return None, f'Nessun template trovato per tipo {tipo_testo}'

        corpo_risolto = _risolvi_variabili_testo(template.corpo_testo, contratto)
        oggetto_risolto = _risolvi_variabili_testo(template.titolo, contratto) if template.titolo else ''

        cartella = _get_cartella_documenti(contratto)
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        safe_name = contratto.lavoratore.nome_cognome.replace(' ', '_').replace('/', '_') if contratto.lavoratore else f"contratto_{contratto.pk}"
        periodo = f"_{mese:02d}_{anno}" if mese and anno else ""
        nome_file = f"{tipo_testo.lower()}_{safe_name}{periodo}_{timestamp}.pdf"
        full_path = os.path.join(cartella, nome_file)

        _genera_pdf_da_testo_playwright(oggetto_risolto, corpo_risolto, full_path,
            font_family=template.font_family or 'Arial', font_size=template.font_size or 11)
        with open(full_path, 'rb') as f:
            pdf_bytes = f.read()

        doc = DocumentoArchiviato.objects.create(
            tipo=tipo_testo,
            titolo=f"{template.codice} – {contratto.lavoratore}",
            file_path=full_path, file_size=os.path.getsize(full_path), file_name=nome_file,
            contratto=contratto, datore=contratto.datore, lavoratore=contratto.lavoratore,
            creato_da=user,
        )
        return doc, pdf_bytes


# --- stampe_invii ---
@login_required
@permesso_richiesto('buste.vedi')
@never_cache
def stampe_invii(request):
    """Pagina principale Stampe e Invii."""
    opzioni = get_opzioni()
    contratti = ContrattoAttivo.objects.filter(stato='ATTIVO').select_related(
        'datore', 'lavoratore', 'parametri_minimi__livello'
    ).prefetch_related('progetto__tipo', 'progetto__beneficiario').order_by('datore__nome_cognome', 'lavoratore__nome_cognome')

    datore_q = request.GET.get('datore', '').strip()
    if datore_q:
        contratti = contratti.filter(datore__nome_cognome__icontains=datore_q)
    lavoratore_q = request.GET.get('lavoratore', '').strip()
    if lavoratore_q:
        contratti = contratti.filter(lavoratore__nome_cognome__icontains=lavoratore_q)
    beneficiario_q = request.GET.get('beneficiario', '').strip()
    if beneficiario_q:
        contratti = contratti.filter(progetto__beneficiario__nome_cognome__icontains=beneficiario_q).distinct()
    livello_q = request.GET.get('livello', '').strip()
    if livello_q:
        contratti = contratti.filter(parametri_minimi__livello__codice__icontains=livello_q)

    templates_per_tipo = {}
    for t in ModelloDocumentale.objects.all().order_by('tipo', 'codice'):
        templates_per_tipo.setdefault(t.tipo, []).append(t)

    categorie_documenti = [
        {
            'id': 'BUSTE_PAGA', 'nome': 'Buste Paga', 'colore': '#5E6AD2',
            'tipi': [
                {'id': 'STANDARD', 'nome': 'Standard', 'usa_periodo': True, 'usa_template': False, 'icona': 'bi-file-earmark-text', 'descrizione': 'Busta paga mensile standard'},
                {'id': 'NON_CONVIVENTE', 'nome': 'Non Convivente', 'usa_periodo': True, 'usa_template': False, 'icona': 'bi-people', 'descrizione': 'Busta paga per collaboratore non convivente'},
                {'id': 'CONVIVENTI_CCNL', 'nome': 'Conviventi CCNL', 'usa_periodo': True, 'usa_template': False, 'icona': 'bi-house-heart', 'descrizione': 'Busta paga per collaboratore convivente'},
                {'id': 'INVERSO', 'nome': 'Calcolo Inverso', 'usa_periodo': True, 'usa_template': False, 'icona': 'bi-arrow-left-right', 'descrizione': 'Calcolo della paga a partire dal netto'},
                {'id': 'NOTTURNO', 'nome': 'Notturno', 'usa_periodo': True, 'usa_template': False, 'icona': 'bi-moon-stars', 'descrizione': 'Busta paga con indennità notturna'},
                {'id': 'MALATTIA', 'nome': 'Malattia', 'usa_periodo': True, 'usa_template': False, 'icona': 'bi-heart-pulse', 'descrizione': 'Busta paga per periodo di malattia'},
                {'id': 'TFR_LIQUIDAZIONE', 'nome': 'Liquidazione TFR', 'usa_periodo': False, 'usa_template': False, 'icona': 'bi-cash-stack', 'descrizione': 'Liquidazione del trattamento di fine rapporto'},
            ]
        },
        {
            'id': 'CONTRATTI', 'nome': 'Contratti', 'colore': '#10b981',
            'tipi': [{'id': 'CONTRATTO', 'nome': 'Stampa Contratto', 'usa_periodo': False, 'usa_template': True, 'icona': 'bi-file-earmark-check', 'descrizione': 'Stampa del contratto di assunzione'}]
        },
        {
            'id': 'LETTERE', 'nome': 'Lettere', 'colore': '#8b5cf6',
            'tipi': [
                {'id': 'LETTERA_ASSUNZIONE', 'nome': 'Lettera Assunzione', 'usa_periodo': False, 'usa_template': True, 'icona': 'bi-envelope-plus', 'descrizione': 'Lettera di assunzione per il collaboratore'},
                {'id': 'LETTERA_LICENZIAMENTO', 'nome': 'Lettera Licenziamento', 'usa_periodo': False, 'usa_template': True, 'icona': 'bi-envelope-minus', 'descrizione': 'Lettera di licenziamento per il collaboratore'},
                {'id': 'LETTERA_DIMISSIONI', 'nome': 'Lettera Dimissioni', 'usa_periodo': False, 'usa_template': True, 'icona': 'bi-envelope-open', 'descrizione': 'Lettera di dimissioni volontarie'},
                {'id': 'LETTERA_LIBERA', 'nome': 'Lettera Libera', 'usa_periodo': False, 'usa_template': True, 'icona': 'bi-envelope-paper', 'descrizione': 'Lettera a contenuto libero'},
                {'id': 'DEROGA_TFR', 'nome': 'Deroga TFR', 'usa_periodo': False, 'usa_template': True, 'icona': 'bi-file-earmark-excel', 'descrizione': 'Deroga alla modalità di calcolo del TFR'},
            ]
        },
        {
            'id': 'ALTRI_DOCUMENTI', 'nome': 'Altri Documenti', 'colore': '#f59e0b',
            'tipi': [
                {'id': 'CARTELLINA', 'nome': 'Cartellina', 'usa_periodo': False, 'usa_template': True, 'icona': 'bi-folder', 'descrizione': 'Cartellina riepilogativa del collaboratore'},
                {'id': 'RICEVUTA', 'nome': 'Ricevuta', 'usa_periodo': False, 'usa_template': True, 'icona': 'bi-receipt', 'descrizione': 'Ricevuta di pagamento'},
                {'id': 'RICHIESTA_CUD', 'nome': 'Richiesta CUD', 'usa_periodo': True, 'usa_template': True, 'icona': 'bi-file-earmark-spreadsheet', 'descrizione': 'Richiesta di Certificazione Unica'},
                {'id': 'RIEPILOGO_RAPPORTO', 'nome': 'Riepilogo Rapporto', 'usa_periodo': False, 'usa_template': True, 'icona': 'bi-journal-text', 'descrizione': 'Riepilogo completo del rapporto di lavoro'},
                {'id': 'PDF_INIZIO', 'nome': 'Inizio Rapporto', 'usa_periodo': False, 'usa_template': True, 'icona': 'bi-play-circle', 'descrizione': 'Comunicazione di inizio rapporto'},
                {'id': 'PDF_FINE', 'nome': 'Fine Rapporto', 'usa_periodo': False, 'usa_template': True, 'icona': 'bi-stop-circle', 'descrizione': 'Comunicazione di fine rapporto'},
                {'id': 'PDF_RISCONTRO', 'nome': 'Riscontro Comune', 'usa_periodo': False, 'usa_template': True, 'icona': 'bi-check-circle', 'descrizione': 'Riscontro da parte del comune'},
            ]
        },
        {
            'id': 'GUIDE_DOCUMENTI', 'nome': 'Guide e CCNL', 'colore': '#e67e22',
            'tipi': [
                {'id': 'GUIDA_ASSUNZIONE', 'nome': 'Guida all\'Assunzione', 'usa_periodo': False, 'usa_template': False, 'icona': 'bi-book', 'descrizione': 'Check-list completa per l\'assunzione'},
                {'id': 'GUIDA_DECALOGO', 'nome': 'Decalogo del Colloquio', 'usa_periodo': False, 'usa_template': False, 'icona': 'bi-chat-dots', 'descrizione': '10 consigli per il colloquio di selezione'},
                {'id': 'GUIDA_CESSAZIONE', 'nome': 'Guida alla Cessazione', 'usa_periodo': False, 'usa_template': False, 'icona': 'bi-box-arrow-right', 'descrizione': 'Procedure per dimissioni, licenziamento, scadenza'},
                {'id': 'CCNL', 'nome': 'CCNL Lavoro Domestico', 'usa_periodo': False, 'usa_template': False, 'icona': 'bi-file-earmark-text', 'descrizione': 'Testo integrale del CCNL'},
            ]
        },
        {
            'id': 'RIFERIMENTI_NORMATIVI', 'nome': 'Riferimenti Normativi', 'colore': '#8b5cf6',
            'tipi': [
                {'id': 'INQUADRAMENTO', 'nome': 'Inquadramento', 'usa_periodo': False, 'usa_template': False, 'icona': 'bi-layers', 'descrizione': 'Classificazione del personale CCNL per livelli e mansioni'},
                {'id': 'TABELLE_RETRIBUTIVE', 'nome': 'Tabelle Retributive', 'usa_periodo': False, 'usa_template': False, 'icona': 'bi-table', 'descrizione': 'Minimi tabellari CCNL aggiornati'},
                {'id': 'CONTRIBUTI_CCNL', 'nome': 'Contributi INPS CCNL', 'usa_periodo': False, 'usa_template': False, 'icona': 'bi-percent', 'descrizione': 'Aliquote contributive INPS lavoro domestico 2026'},
            ]
        },
    ]

    oggi = date.today()
    mesi = [(i, ['','Gennaio','Febbraio','Marzo','Aprile','Maggio','Giugno',
                  'Luglio','Agosto','Settembre','Ottobre','Novembre','Dicembre'][i]) for i in range(1, 13)]
    anni = list(range(oggi.year - 5, oggi.year + 2))

    livelli = Livello.objects.all().order_by('codice')
    tipi_progetto = TipoProgettoRegionale.objects.all().order_by('nome')
    comuni = Beneficiario.objects.filter(
        progetti__contrattolavoro__stato='ATTIVO'
    ).exclude(comune='').exclude(comune__isnull=True)\
    .values_list('comune', flat=True).distinct().order_by('comune')

    import json as json_lib
    modelli_email = ModelloDocumentale.objects.filter(tipo='MAIL').order_by('codice')
    composizioni = ModelloComposizione.objects.all().order_by('-is_default', 'nome')
    composizioni_json = json_lib.dumps([{
        'pk': c.pk, 'nome': c.nome, 'elementi': c.elementi,
        'note': c.note, 'is_default': c.is_default,
    } for c in composizioni])
    contratto_pk = request.GET.get('contratto_pk')
    return render(request, 'paghe/stampe_invii.html', {
        'opzioni': opzioni,
        'contratti': contratti,
        'categorie_documenti': categorie_documenti,
        'templates_per_tipo': templates_per_tipo,
        'templates_json': json_lib.dumps({k: [{'pk': t.pk, 'codice': t.codice} for t in v] for k, v in templates_per_tipo.items()}),
        'modelli_email': modelli_email,
        'composizioni_json': composizioni_json,
        'mesi': mesi,
        'anni': anni,
        'livelli': livelli,
        'tipi_progetto': tipi_progetto,
        'comuni': comuni,
        'filtro_datore': datore_q,
        'filtro_lavoratore': lavoratore_q,
        'filtro_beneficiario': beneficiario_q,
        'filtro_livello': livello_q,
        'contratto_pk': contratto_pk,
        'mese_corrente': oggi.month,
        'anno_corrente': oggi.year,
    })


# --- ajax_stampa_unico ---
@login_required
@permesso_richiesto('buste.vedi')
@require_http_methods(['POST'])
def ajax_stampa_unico(request):
    """Stampa il PDF unico generato in Stampe e Invii, dato il token di sessione."""
    import json as json_lib
    data = json_lib.loads(request.body)
    token = data.get('token', '').strip()
    if not token:
        return JsonResponse({'ok': False, 'errore': 'Token mancante'})
    path = request.session.get(f'stampa_token_{token}')
    if not path or not os.path.exists(path):
        return JsonResponse({'ok': False, 'errore': 'File PDF non trovato'})
    ok = _stampa_pdf_windows(path)
    return JsonResponse({'ok': ok, 'errore': None if ok else 'Impossibile stampare. Verifica il lettore PDF predefinito.'})


# --- ajax_stampa_documento ---
@login_required
@permesso_richiesto('documenti.vedi')
@require_http_methods(['POST'])
def ajax_stampa_documento(request, pk):
    """Stampa un DocumentoArchiviato direttamente sulla stampante predefinita."""
    doc = get_object_or_404(DocumentoArchiviato, pk=pk)
    if not doc.file_path or not os.path.exists(doc.file_path):
        return JsonResponse({'ok': False, 'errore': 'File PDF non trovato sul disco.'})
    ok = _stampa_pdf_windows(doc.file_path)
    if ok:
        doc.stampato = True
        doc.data_stampa = timezone.now()
        doc.save(update_fields=['stampato', 'data_stampa'])
    return JsonResponse({'ok': ok, 'errore': None if ok else 'Impossibile stampare. Verifica il lettore PDF predefinito.'})


# --- ajax_stampa_documento_massiva ---
@login_required
@permesso_richiesto('documenti.vedi')
@require_http_methods(['POST'])
def ajax_stampa_documento_massiva(request):
    """Stampa più documenti in sequenza."""
    import json as json_lib
    data = json_lib.loads(request.body)
    pks = data.get('pks', [])
    risultati = []
    doc_map = {d.pk: d for d in DocumentoArchiviato.objects.filter(pk__in=pks)}
    for pk in pks:
        doc = doc_map.get(pk)
        if doc and doc.file_path and os.path.exists(doc.file_path):
            ok = _stampa_pdf_windows(doc.file_path)
            if ok:
                doc.stampato = True
                doc.data_stampa = timezone.now()
                doc.save(update_fields=['stampato', 'data_stampa'])
            risultati.append({'pk': pk, 'ok': ok})
        else:
            risultati.append({'pk': pk, 'ok': False})
    return JsonResponse({'ok': True, 'risultati': risultati, 'totale': len(pks), 'stampati': sum(1 for r in risultati if r['ok'])})


@login_required
@permesso_richiesto('buste.invia')
def ajax_genera_stampe_invii(request):
    """Genera documenti per i contratti selezionati."""
    import json as json_lib
    data = json_lib.loads(request.body)

    contratti_pk = data.get('contratti', [])
    data.get('categoria', '')
    tipo_documento = data.get('tipo_documento', '')
    template_pk = data.get('template_pk')
    periodo_tipo = data.get('periodo_tipo', 'singolo')
    mese_da = data.get('mese_da')
    anno_da = data.get('anno_da')
    mese_a = data.get('mese_a')
    anno_a = data.get('anno_a')
    azione = data.get('azione', 'pdf')
    modello_email_pk = data.get('modello_email_pk')

    # Composizione personalizzata
    composizione = data.get('composizione')
    # Se composizione presente, e' personalizzata (ignora tipo_documento singolo)
    modalita_composizione = bool(composizione)

    if not contratti_pk or (not tipo_documento and not modalita_composizione):
        return JsonResponse({'error': 'Parametri mancanti'}, status=400)

    # Cache per documenti generici (GUIDA_ASSUNZIONE, GUIDA_DECALOGO, GUIDA_CESSAZIONE, CCNL, INQUADRAMENTO, TABELLE_RETRIBUTIVE, CONTRIBUTI_CCNL)
    _documenti_generici_cache = {}

    contratti = ContrattoAttivo.objects.filter(pk__in=contratti_pk).select_related(
        'datore', 'lavoratore', 'parametri_minimi'
    )

    dettaglio = []
    totale_ok = 0
    totale_errori = 0
    pdf_paths = []
    pdf_bytes_list = []

    if modalita_composizione:
        # ---- MODALITA' COMPOSIZIONE: ogni elemento ha tipo + periodo opzionale ----
        try:
            for c in contratti:
                for elem in composizione:
                    elem_tipo = elem.get('tipo', '')
                    elem_label = elem.get('label', elem_tipo)
                    elem_template_pk = elem.get('template_pk') or None
                    elem_periodo = elem.get('periodo') or {}
                    em = elem_periodo.get('mese')
                    ea = elem_periodo.get('anno')

                    if elem_tipo == 'PAGINA_BIANCA':
                        pdf_bytes = _crea_pagina_bianca()
                        entry = {
                            'contratto_pk': c.pk,
                            'datore': str(c.datore),
                            'lavoratore': str(c.lavoratore),
                            'periodo': '',
                            'tipo': elem_tipo,
                            'documento_pk': None,
                            'file_name': '',
                            'email_destinatario': '',
                            'inviato': False,
                            'errore': '',
                        }
                        dettaglio.append(entry)
                        pdf_bytes_list.append(pdf_bytes)
                        totale_ok += 1
                    elif elem_tipo in ('GUIDA_ASSUNZIONE', 'GUIDA_DECALOGO', 'GUIDA_CESSAZIONE', 'CCNL', 'INQUADRAMENTO', 'TABELLE_RETRIBUTIVE', 'CONTRIBUTI_CCNL') and _documenti_generici_cache.get(elem_tipo):
                        # Cache hit: riusa PDF gia' generato per contratto precedente
                        pdf_bytes = _documenti_generici_cache[elem_tipo]
                        nome_file = f"{elem_tipo.lower()}_{c.pk}.pdf"
                        cartella = _get_cartella_documenti(c)
                        full_path = os.path.join(cartella, nome_file)
                        with open(full_path, 'wb') as f:
                            f.write(pdf_bytes)
                        from paghe.models import DocumentoArchiviato
                        doc = DocumentoArchiviato.objects.create(
                            tipo=elem_tipo,
                            titolo=f"{elem_label} \u2013 {c.lavoratore}",
                            file_path=full_path, file_size=len(pdf_bytes), file_name=nome_file,
                            contratto=c, datore=c.datore, lavoratore=c.lavoratore,
                            creato_da=request.user,
                        )
                        entry = {
                            'contratto_pk': c.pk,
                            'datore': str(c.datore),
                            'lavoratore': str(c.lavoratore),
                            'periodo': '',
                            'tipo': elem_tipo,
                            'documento_pk': doc.pk,
                            'file_name': doc.file_name,
                            'email_destinatario': '',
                            'inviato': False,
                            'errore': '',
                        }
                        dettaglio.append(entry)
                        pdf_paths.append(doc.file_path)
                        pdf_bytes_list.append(pdf_bytes)
                        totale_ok += 1
                    else:
                        doc, result = _genera_documento_stampe(
                            c, elem_tipo,
                            mese=int(em) if em else None,
                            anno=int(ea) if ea else None,
                            template_pk=elem_template_pk,
                            user=request.user,
                            request=request,
                        )
                        if doc is None:
                            entry = {
                                'contratto_pk': c.pk,
                                'datore': str(c.datore),
                                'lavoratore': str(c.lavoratore),
                                'periodo': f"{int(em):02d}/{int(ea)}" if em and ea else '',
                                'tipo': elem_tipo,
                                'documento_pk': None,
                                'file_name': '',
                                'email_destinatario': '',
                                'inviato': False,
                                'errore': result or 'Errore generazione',
                            }
                            dettaglio.append(entry)
                            totale_errori += 1
                        else:
                            with open(doc.file_path, 'rb') as f:
                                pdf_bytes = f.read()
                            # Cache per documenti generici: salva bytes per contratti successivi
                            if elem_tipo in ('GUIDA_ASSUNZIONE', 'GUIDA_DECALOGO', 'GUIDA_CESSAZIONE', 'CCNL', 'INQUADRAMENTO', 'TABELLE_RETRIBUTIVE', 'CONTRIBUTI_CCNL'):
                                _documenti_generici_cache.setdefault(elem_tipo, pdf_bytes)
                            entry = {
                                'contratto_pk': c.pk,
                                'datore': str(c.datore),
                                'lavoratore': str(c.lavoratore),
                                'periodo': f"{int(em):02d}/{int(ea)}" if em and ea else '',
                                'tipo': elem_tipo,
                                'documento_pk': doc.pk,
                                'file_name': doc.file_name,
                                'email_destinatario': '',
                                'inviato': False,
                                'errore': '',
                            }
                            dettaglio.append(entry)
                            pdf_paths.append(doc.file_path)
                            pdf_bytes_list.append(pdf_bytes)
                            totale_ok += 1
        except Exception as exc:
            logger.exception("Errore in ajax_genera_stampe_invii")
            import traceback
            return JsonResponse({'error': f'Errore elaborazione composizione: {exc}', 'traceback': traceback.format_exc()}, status=500)
    else:
        # ---- MODALITA' STANDARD: singolo tipo_documento ----
        # Costruisce lista periodi
        try:
            MONTHLY_TYPES = ['STANDARD', 'NON_CONVIVENTE', 'CONVIVENTI_CCNL', 'INVERSO', 'NOTTURNO', 'MALATTIA']
            periodi = []
            if tipo_documento in MONTHLY_TYPES:
                if periodo_tipo == 'singolo' and mese_da and anno_da:
                    periodi.append((int(mese_da), int(anno_da)))
                elif periodo_tipo == 'range' and mese_da and anno_da and mese_a and anno_a:
                    m_curr, a_curr = int(mese_da), int(anno_da)
                    m_end, a_end = int(mese_a), int(anno_a)
                    while (a_curr < a_end) or (a_curr == a_end and m_curr <= m_end):
                        periodi.append((m_curr, a_curr))
                        m_curr += 1
                        if m_curr > 12:
                            m_curr = 1
                            a_curr += 1
                elif periodo_tipo == 'trimestre' and mese_da and anno_da:
                    trim_map = {1: (1, 3), 2: (4, 6), 3: (7, 9), 4: (10, 12)}
                    t = int(mese_da)
                    if t in trim_map:
                        sm, em = trim_map[t]
                        for m in range(sm, em + 1):
                            periodi.append((m, int(anno_da)))
                elif periodo_tipo == 'anno' and anno_da:
                    for m in range(1, 13):
                        periodi.append((m, int(anno_da)))
                else:
                    periodi.append((None, None))
            else:
                # Per documenti non mensili, un solo documento per anno o generico
                periodi.append((None, int(anno_da) if anno_da else None))


            for c in contratti:
                for mese, anno in periodi:
                    doc, result = _genera_documento_stampe(c, tipo_documento, mese=mese, anno=anno, template_pk=template_pk, user=request.user, request=request)
                    if doc is None:
                        entry = {
                            'contratto_pk': c.pk,
                            'datore': str(c.datore),
                            'lavoratore': str(c.lavoratore),
                            'periodo': f"{mese:02d}/{anno}" if mese and anno else '',
                            'tipo': tipo_documento,
                            'documento_pk': None,
                            'file_name': '',
                            'email_destinatario': '',
                            'inviato': False,
                            'errore': result or 'Errore generazione',
                        }
                        dettaglio.append(entry)
                        totale_errori += 1
                    else:
                        with open(doc.file_path, 'rb') as f:
                            pdf_bytes = f.read()
                        entry = {
                            'contratto_pk': c.pk,
                            'datore': str(c.datore),
                            'lavoratore': str(c.lavoratore),
                            'periodo': f"{mese:02d}/{anno}" if mese and anno else '',
                            'tipo': tipo_documento,
                            'documento_pk': doc.pk,
                            'file_name': doc.file_name,
                            'email_destinatario': '',
                            'inviato': False,
                            'errore': '',
                        }
                        dettaglio.append(entry)
                        pdf_paths.append(doc.file_path)
                        pdf_bytes_list.append(pdf_bytes)
                        totale_ok += 1
        except Exception as exc:
            logger.exception("Errore in ajax_genera_stampe_invii")
            import traceback
            return JsonResponse({'error': f'Errore elaborazione documento: {exc}', 'traceback': traceback.format_exc()}, status=500)

    # ---- STAMPA AUTOMATICA (stampa_auto) ----
    if azione == 'stampa_auto':
        stampati = 0
        for path in pdf_paths:
            if _stampa_pdf_windows(path):
                stampati += 1
        return JsonResponse({
            'ok': True,
            'riepilogo_pk': None,
            'totale_contratti': len(contratti_pk),
            'totale_ok': stampati,
            'totale_errori': len(pdf_paths) - stampati,
            'dettaglio': dettaglio,
            'stampati': stampati,
        })

    # ---- AZIONI POST-GENERAZIONE ----

    # ZIP
    zip_path = ''
    if azione in ('zip', 'stampa') and pdf_paths:
        _assicura_cartella_stampe()
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        zip_name = f"stampe_{timestamp}.zip"
        zip_full = os.path.join(CARTELLA_STAMPE_TEMP, zip_name)
        import zipfile
        with zipfile.ZipFile(zip_full, 'w', zipfile.ZIP_DEFLATED) as zf:
            for path in pdf_paths:
                if os.path.exists(path):
                    zf.write(path, os.path.basename(path))
        zip_path = zip_full

    # PDF unico per stampa (usa merge in memoria)
    pdf_unico_path = ''
    if azione == 'stampa' and pdf_bytes_list:
        _assicura_cartella_stampe()
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        pdf_unico_name = f"stampa_unica_{timestamp}.pdf"
        pdf_unico_path = os.path.join(CARTELLA_STAMPE_TEMP, pdf_unico_name)
        try:
            merged = _unisci_pdf_bytes(pdf_bytes_list)
            with open(pdf_unico_path, 'wb') as f:
                f.write(merged)
        except Exception:
            logger.exception("Errore in ajax_genera_stampe_invii")
            pdf_unico_path = ''

    if not pdf_unico_path and azione == 'stampa' and pdf_paths:
        pdf_unico_path = pdf_paths[0] if len(pdf_paths) == 1 else ''

    # RiepilogoInvio
    riepilogo = RiepilogoInvio.objects.create(
        creato_da=request.user,
        mese=int(mese_da) if mese_da else 0,
        anno=int(anno_da) if anno_da else 0,
        totale_contratti=len(contratti_pk),
        totale_ok=totale_ok,
        totale_errori=totale_errori,
        dettaglio=dettaglio,
        archivio_zip_path=zip_path if azione == 'zip' else '',
    )

    # Invio email (via _invia_email.py centralizzato)
    email_ok = 0
    email_errori = 0
    if modello_email_pk and totale_ok > 0:
        dettaglio_aggiornato = list(riepilogo.dettaglio)
        for i, entry in enumerate(dettaglio_aggiornato):
            if not entry.get('documento_pk'):
                continue
            doc_pk = entry['documento_pk']
            contratto = ContrattoLavoro.objects.filter(pk=entry.get('contratto_pk')).first()
            if not contratto:
                continue

            destinatario = ';'.join(filter(None, [
                contratto.lavoratore.email if contratto.lavoratore else '',
                contratto.datore.email if contratto.datore else '',
            ]))
            dettaglio_aggiornato[i]['email_destinatario'] = destinatario

            if not destinatario:
                dettaglio_aggiornato[i]['inviato'] = False
                dettaglio_aggiornato[i]['errore'] = 'Nessun indirizzo email'
                email_errori += 1
                continue

            risultato = invia_documento_email(doc_pk, destinatario, modello_email_pk, request)
            if risultato['ok']:
                dettaglio_aggiornato[i]['inviato'] = True
                dettaglio_aggiornato[i]['errore'] = ''
                email_ok += 1
            else:
                dettaglio_aggiornato[i]['inviato'] = False
                dettaglio_aggiornato[i]['errore'] = risultato.get('errore', 'Errore invio email')
                email_errori += 1

        riepilogo.dettaglio = dettaglio_aggiornato
        riepilogo.totale_ok = email_ok
        riepilogo.totale_errori = email_errori
        riepilogo.modello_email = ModelloDocumentale.objects.get(pk=modello_email_pk)
        riepilogo.save()

    # URL per download ZIP e PDF unico
    zip_url = f'/download-riepilogo-zip/{riepilogo.pk}/' if zip_path and azione == 'zip' else ''
    pdf_unico_url = ''
    if pdf_unico_path and azione == 'stampa':
        import uuid
        token = str(uuid.uuid4())
        request.session[f'stampa_token_{token}'] = pdf_unico_path
        pdf_unico_url = f'/stampe-invii/print/{token}/'

    # URL diretti a ogni PDF singolo
    pdf_urls = [f'/ajax/vedi-documento/{e["documento_pk"]}/' for e in riepilogo.dettaglio if e.get('documento_pk')]

    return JsonResponse({
        'ok': True,
        'riepilogo_pk': riepilogo.pk,
        'totale_contratti': len(contratti_pk),
        'totale_ok': totale_ok,
        'totale_errori': totale_errori,
        'dettaglio': riepilogo.dettaglio,
        'zip_url': zip_url,
        'pdf_unico_url': pdf_unico_url,
        'pdf_urls': pdf_urls,
        'email_inviate': email_ok if modello_email_pk else None,
        'email_errori': email_errori if modello_email_pk else None,
    })

# --- ajax_lista_composizioni ---
@login_required
@permesso_richiesto('buste.vedi')
def ajax_lista_composizioni(request):
    """Restituisce l'elenco delle composizioni salvate."""
    composizioni = ModelloComposizione.objects.all().order_by('-is_default', 'nome')
    data = [{
        'pk': c.pk,
        'nome': c.nome,
        'elementi': c.elementi,
        'note': c.note,
        'is_default': c.is_default,
    } for c in composizioni]
    return JsonResponse({'composizioni': data})


# --- ajax_salva_composizione ---
@login_required
@permesso_richiesto('buste.calcola')
@require_http_methods(['POST'])
def ajax_salva_composizione(request):
    """Salva o aggiorna una composizione."""
    import json as json_lib
    data = json_lib.loads(request.body)
    pk = data.get('pk')
    nome = data.get('nome', '').strip()
    elementi = data.get('elementi', [])
    note = data.get('note', '').strip()

    if not nome:
        return JsonResponse({'error': 'Nome composizione obbligatorio'}, status=400)
    if not elementi:
        return JsonResponse({'error': 'Almeno un elemento richiesto'}, status=400)

    TIPI_CONSENTITI = {
        'PAGINA_BIANCA', 'STANDARD', 'NON_CONVIVENTE', 'CONVIVENTI_CCNL',
        'INVERSO', 'NOTTURNO', 'MALATTIA', 'TFR_LIQUIDAZIONE', 'CONTRATTO',
        'CUD', 'RICHIESTA_CUD', 'LETTERA_ASSUNZIONE', 'LETTERA_LICENZIAMENTO',
        'LETTERA_DIMISSIONI', 'LETTERA_LIBERA', 'DEROGA_TFR', 'CARTELLINA',
        'RICEVUTA', 'RIEPILOGO_RAPPORTO', 'PDF_INIZIO', 'PDF_FINE', 'PDF_RISCONTRO',
        'GUIDA_ASSUNZIONE', 'GUIDA_DECALOGO', 'GUIDA_CESSAZIONE', 'CCNL',
        'INQUADRAMENTO', 'TABELLE_RETRIBUTIVE', 'CONTRIBUTI_CCNL',
    }
    for idx, elem in enumerate(elementi):
        if not isinstance(elem, dict) or not elem.get('tipo'):
            return JsonResponse({'error': f'Elemento {idx+1}: tipo mancante'}, status=400)
        if elem['tipo'] not in TIPI_CONSENTITI:
            return JsonResponse({'error': f'Elemento {idx+1}: tipo "{elem["tipo"]}" non valido'}, status=400)

    if pk:
        composizione = get_object_or_404(ModelloComposizione, pk=pk)
        composizione.nome = nome
        composizione.elementi = elementi
        composizione.note = note
        composizione.save()
    else:
        composizione = ModelloComposizione.objects.create(
            nome=nome, elementi=elementi, note=note,
        )

    return JsonResponse({'ok': True, 'pk': composizione.pk})


# --- ajax_elimina_composizione ---
@login_required
@permesso_richiesto('buste.approva')
@require_http_methods(['POST'])
def ajax_elimina_composizione(request, pk):
    """Elimina una composizione."""
    composizione = get_object_or_404(ModelloComposizione, pk=pk)
    composizione.delete()
    return JsonResponse({'ok': True})


# --- stampe_invii_print ---
@login_required
@permesso_richiesto('buste.vedi')
def stampe_invii_print(request, token):
    """Serve il PDF unico per la stampa."""
    path = request.session.get(f'stampa_token_{token}')
    if not path or not os.path.exists(path):
        return HttpResponse('PDF non trovato o sessione scaduta', status=404)
    with open(path, 'rb') as f:
        pdf_data = f.read()
    response = HttpResponse(pdf_data, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="stampa_unica.pdf"'
    return response


# --- ajax_apri_cartella_stampe ---
@login_required
@permesso_richiesto('buste.vedi')
@require_http_methods(['POST'])
def ajax_apri_cartella_stampe(request, pk):
    """Apre la cartella dei documenti generati in Explorer."""
    riepilogo = get_object_or_404(RiepilogoInvio, pk=pk)
    cartella_aperta = False
    for entry in riepilogo.dettaglio:
        doc_pk = entry.get('documento_pk')
        if doc_pk:
            doc = DocumentoArchiviato.objects.filter(pk=doc_pk).first()
            if doc and doc.file_path:
                cartella = os.path.dirname(doc.file_path)
                if os.path.isdir(cartella):
                    import subprocess
                    subprocess.Popen(['explorer', cartella])
                    cartella_aperta = True
                    break
    if not cartella_aperta and riepilogo.archivio_zip_path:
        cartella = os.path.dirname(riepilogo.archivio_zip_path)
        if os.path.isdir(cartella):
            import subprocess
            subprocess.Popen(['explorer', cartella])
            cartella_aperta = True
    return JsonResponse({'ok': cartella_aperta})
