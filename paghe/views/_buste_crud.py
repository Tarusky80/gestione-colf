"""Modulo _buste_crud - generato automaticamente da views.py"""

from paghe.views._common_imports import *

from paghe.views._helpers import _get_cartella_documenti, _genera_pdf_da_testo, _stampa_pdf_windows
from paghe.views._calcoli_core import _calcola_busta_data, _calcola_busta_inversa_data, _calcola_progetti_data, _calcola_busta_conviventi_ccnl_data
from paghe.views._buste_pdf import _genera_html_busta, _genera_busta_completa_pdf_bytes
from paghe.views._testi import _risolvi_variabili_testo
from paghe.views._buste_download import _build_busta_extra_vars
from paghe.views._tfr_cessazione import _calcola_tfr_fino_a, _build_liquidazione_tfr_pdf_bytes

logger = logging.getLogger(__name__)



# --- ajax_salva_busta_template ---
@login_required
@permesso_richiesto('buste.calcola')
@require_http_methods(['POST'])
def ajax_salva_busta_template(request, contratto_pk):
    contratto = get_object_or_404(ContrattoAttivo, pk=contratto_pk)
    template_pk = request.POST.get('template_pk')
    if template_pk:
        try:
            template_pk = int(template_pk)
            tpl = ModelloDocumentale.objects.get(pk=template_pk, tipo='BUSTA_PAGA')
            contratto.busta_template = tpl
        except (ValueError, ModelloDocumentale.DoesNotExist):
            return JsonResponse({'errore': 'Template non valido'}, status=400)
    else:
        contratto.busta_template = None
    contratto.save(update_fields=['busta_template'])
    return JsonResponse({'ok': True})


# --- ajax_salva_busta ---
@login_required
@permesso_richiesto('buste.calcola')
@require_http_methods(['POST'])
def ajax_salva_busta(request):
    """Salva o aggiorna una BustaPaga dai dati di calcolo."""
    try:
        contratto_pk = int(request.POST.get('contratto_pk', 0))
        mese = int(request.POST.get('mese', 0))
        anno = int(request.POST.get('anno', 0))
        tipo_calcolo = request.POST.get('tipo_calcolo', 'STANDARD').upper()
        if tipo_calcolo not in ('STANDARD', 'CONVIVENTE', 'NON_CONVIVENTE', 'SOSTITUZIONE', 'NOTTURNO', 'MALATTIA', 'CALCOLO_INVERSO', 'CONVIVENTI_CCNL'):
            return JsonResponse({'errore': 'Tipo calcolo non valido'}, status=400)
    except (ValueError, TypeError):
        return JsonResponse({'errore': 'Parametri non validi'}, status=400)
    contratto = get_object_or_404(ContrattoAttivo, pk=contratto_pk)
    if tipo_calcolo == 'CONVIVENTI_CCNL':
        tipo_orario = request.POST.get('tipo_orario', 'FT')
        data = _calcola_busta_conviventi_ccnl_data(contratto, mese, anno, tipo_orario=tipo_orario)
    elif tipo_calcolo == 'MALATTIA':
        data = _calcola_busta_data(contratto, mese, anno)
    elif tipo_calcolo == 'CALCOLO_INVERSO':
        ore_mensili = request.POST.get('ore_mensili')
        ore_settimanali = request.POST.get('ore_settimanali')
        lordo_target = request.POST.get('lordo_target')
        netto_target = request.POST.get('netto_target')
        data = _calcola_busta_inversa_data(
            contratto, mese, anno,
            ore_mensili=float(ore_mensili) if ore_mensili else None,
            ore_settimanali=float(ore_settimanali) if ore_settimanali else None,
            lordo_target=float(lordo_target) if lordo_target else None,
            netto_target=float(netto_target) if netto_target else None,
        )
    elif tipo_calcolo == 'NOTTURNO':
        data = _calcola_busta_data(contratto, mese, anno)
    else:
        data = _calcola_busta_data(contratto, mese, anno, is_convivente=(tipo_calcolo == 'CONVIVENTE'), sostituzione=(tipo_calcolo == 'SOSTITUZIONE'))
    if 'errore' in data:
        return JsonResponse({'errore': data['errore']}, status=400)
    bp, created = BustaPaga.objects.update_or_create(
        contratto=contratto, mese=mese, anno=anno,
        defaults=dict(
            tipo_calcolo=tipo_calcolo,
            budget_mensile=data['budget_mensile'],
            ore_mensili=data['ore_mensili'],
            ore_inps=data['ore_inps'],
            ore_settimanali=data['ore_settimanali'],
            paga_oraria_lorda=data['paga_oraria_lorda'],
            paga_base_totale=data['paga_base']['totale'],
            totale_indennita=data['totale_indennita'],
            scatti_totale=data['scatti_anzianita']['valore'],
            totale_lordo=data['totale_lordo'],
            contributi_inps_orario=data['contributi']['inps']['orario'],
            contributi_inps_totale=data['contributi']['inps']['totale'],
            contributi_inps_fascia=data['contributi']['inps']['fascia'],
            contributi_inps_quota_datore=data['contributi']['inps']['quota_datore_totale'],
            contributi_inps_quota_lavoratore=data['contributi']['inps']['quota_lavoratore_totale'],
            contributi_cassa_orario=data['contributi']['cassa']['orario'],
            contributi_cassa_totale=data['contributi']['cassa']['totale'],
            contributi_cassa_nome=data['contributi']['cassa']['nome'],
            totale_contributi=data['contributi']['totale'],
            convivenza_totale=data['trattenute']['convivenza']['totale'],
            totale_accantonati=data['trattenute']['ratei_accantonati'],
            netto=data['netto'],
            indennita_json=data.get('indennita', []),
            ratei_pagati_json=data.get('ratei_pagati', []),
            scatti_dettaglio_json=data.get('scatti_anzianita', {}),
            progetti_json=data.get('progetti', []),
        )
    )
    return JsonResponse({
        'ok': True,
        'pk': bp.pk,
        'creato': created,
        'stato': bp.stato,
        'contratto_pk': contratto.pk,
        'mese': mese,
        'anno': anno,
    })


# --- _genera_e_salva_pdf_busta ---


def _genera_e_salva_pdf_busta(contratto_pk, mese, anno, tipo_calcolo, user):
    """Genera PDF per una busta paga e crea DocumentoArchiviato linkato alla BustaPaga."""
    import os

    contratto = get_object_or_404(ContrattoAttivo, pk=contratto_pk)
    bp = BustaPaga.objects.filter(contratto=contratto, mese=mese, anno=anno, tipo_calcolo=tipo_calcolo).first()
    if not bp:
        raise Exception("BustaPaga non trovata")

    # Riutilizza la logica di download_busta_pdf ma senza request HTTP
    # Calcola i dati della busta
    convivenza_items = []  # Default vuoto per salvataggio massivo
    ctx = _calcola_busta_data(contratto, mese, anno, convivenza_items=convivenza_items, toggles={})
    if 'errore' in ctx:
        raise Exception(ctx['errore'])

    progetti_data = _calcola_progetti_data(ctx, contratto) if ctx.get('progetti') else None

    f"busta_{contratto.lavoratore.nome_cognome.replace(' ', '_')}_{mese:02d}_{anno}.pdf"
    cartella = _get_cartella_documenti(contratto)
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    safe_name = contratto.lavoratore.nome_cognome.replace(' ', '_').replace('/', '_')
    nome_file_disk = f"busta_{safe_name}_{mese:02d}_{anno}_{timestamp}.pdf"
    full_path = os.path.join(cartella, nome_file_disk)

    # Template selezionato sul contratto
    template_testo = contratto.busta_template if contratto.busta_template and contratto.busta_template.tipo == 'BUSTA_PAGA' else None
    pdf = None

    try:
        if template_testo:
            html_busta = _genera_html_busta(ctx, progetti_data)
            extra_vars = _build_busta_extra_vars(ctx, html_busta)
            corpo_risolto = _risolvi_variabili_testo(template_testo.corpo_testo, contratto, extra_vars=extra_vars)
            oggetto_risolto = _risolvi_variabili_testo(template_testo.oggetto_titolo or '', contratto, extra_vars=extra_vars)

            _pdf_buffer = _genera_pdf_da_testo(
                tipo='PAGA_STANDARD',
                titolo=oggetto_risolto,
                corpo=corpo_risolto,
                output_path=full_path
            )
            if _pdf_buffer is not None:
                pdf = _pdf_buffer.getvalue()

        if pdf is None:
            pdf, _ = _genera_busta_completa_pdf_bytes(contratto, mese, anno, ctx_override=ctx)
            if pdf is None:
                raise Exception('Errore generazione PDF')
    except Exception:
        logger.exception("PDF ERROR for contratto %s (%s %02d/%s)", contratto_pk, tipo_calcolo, mese, anno)
        raise

    # Salva su disco
    with open(full_path, 'wb') as f:
        f.write(pdf)

    # Crea DocumentoArchiviato
    d = DocumentoArchiviato.objects.create(
        tipo='BUSTA_MASSIVA',
        titolo=f"Busta {tipo_calcolo} {contratto.lavoratore.nome_cognome} {mese:02d}/{anno}",
        file_path=full_path,
        file_size=len(pdf),
        file_name=nome_file_disk,
        contratto=contratto,
        datore=contratto.datore,
        lavoratore=contratto.lavoratore,
        creato_da=user if user.is_authenticated else None,
    )

    # Link al BustaPaga
    bp.documento = d
    bp.save(update_fields=['documento'])

    return d


# --- ajax_salva_buste_selezionate ---
@login_required
@permesso_richiesto('buste.approva')
@require_http_methods(['POST'])
def ajax_salva_buste_selezionate(request):
    """Salva in archivio le buste paga per i contratti selezionati, generando anche il PDF."""
    import json as json_lib
    data = json_lib.loads(request.body)
    contratti_pk = data.get('contratti', [])
    mese = data.get('mese')
    anno = data.get('anno')
    tipo_calcolo = data.get('tipo_calcolo', 'STANDARD').upper()
    if not contratti_pk or not mese or not anno:
        return JsonResponse({'ok': False, 'error': 'Parametri mancanti'}, status=400)
    salvate = 0
    errori = []
    for pk in contratti_pk:
        try:
            from django.http import QueryDict
            post_data = QueryDict(mutable=True)
            post_data['contratto_pk'] = pk
            post_data['mese'] = str(mese)
            post_data['anno'] = str(anno)
            post_data['tipo_calcolo'] = tipo_calcolo
            # Chiama la logica di salvataggio esistente
            from django.test import RequestFactory
            factory = RequestFactory()
            req = factory.post('/ajax/salva-busta/', post_data)
            req.user = request.user
            req.session = request.session
            resp = ajax_salva_busta(req)
            if resp.status_code == 200:
                import json as j
                rdata = j.loads(resp.content)
                if rdata.get('ok'):
                    salvate += 1
                    # Genera PDF e crea DocumentoArchiviato per questa busta
                    try:
                        _genera_e_salva_pdf_busta(pk, mese, anno, tipo_calcolo, request.user)
                    except Exception as e:
                        logger.exception("Errore in ajax_salva_buste_selezionate")
                        errori.append(f"Contratto #{pk} (salvato ma PDF fallito): {str(e)}")
                else:
                    errori.append(f"Contratto #{pk}: {rdata.get('errore', 'Errore')}")
            else:
                errori.append(f"Contratto #{pk}: Errore HTTP {resp.status_code}")
        except Exception as e:
            logger.exception("Errore in ajax_salva_buste_selezionate")
            errori.append(f"Contratto #{pk}: {str(e)}")
    return JsonResponse({'ok': True, 'salvate': salvate, 'errori': errori})


# --- ajax_liquida_tfr ---
@login_required
@permesso_richiesto('buste.calcola')
@require_http_methods(['POST'])
@never_cache
def ajax_liquida_tfr(request):
    """Liquida TFR accantonato e salva record in BustaPaga.
    POST: contratto_pk, mese, anno, data_inizio (opzionale)."""
    try:
        contratto_pk = int(request.POST.get('contratto_pk', 0))
        mese = int(request.POST.get('mese', 0))
        anno = int(request.POST.get('anno', 0))
    except (ValueError, TypeError):
        return JsonResponse({'errore': 'Parametri non validi'}, status=400)
    contratto = get_object_or_404(ContrattoAttivo, pk=contratto_pk)
    if contratto.modalita_tfr == 'INCLUSO':
        return JsonResponse({'errore': 'TFR già incluso nella paga oraria — nessun accantonamento da liquidare.'}, status=400)

    # Determina data_fine dal mese/anno richiesti
    import calendar
    ultimo_giorno = calendar.monthrange(anno, mese)[1]
    data_fine = date(anno, mese, ultimo_giorno)
    data_inizio_str = request.POST.get('data_inizio', '').strip()
    if data_inizio_str:
        try:
            data_inizio_scelta = date.fromisoformat(data_inizio_str)
        except ValueError:
            data_inizio_scelta = None
    else:
        data_inizio_scelta = None

    # Calcola TFR cumulativo fino a data_fine
    mesi, tfr_mensile, cumulativo = _calcola_tfr_fino_a(contratto, data_fine)
    if cumulativo <= 0:
        return JsonResponse({'errore': 'Nessun importo TFR accantonato da liquidare per il periodo richiesto.'}, status=400)

    data_inizio_eff = data_inizio_scelta or contratto.data_inizio_tfr or contratto.data_assunzione
    if not data_inizio_eff:
        return JsonResponse({'errore': 'Data inizio TFR non disponibile.'}, status=400)

    p = contratto.parametri_minimi
    ore_m = contratto.ore_mensili_calcolate
    coeff = 0.3 if contratto.modalita_tfr == 'SEPARATO_70' else 1.0
    tfr_orario = float(p.tfr_orario) if p else 0

    # Se data_inizio è diversa da quella di default, ricalcola mesi/cumulativo
    if data_inizio_scelta and data_inizio_scelta > (contratto.data_inizio_tfr or contratto.data_assunzione):
        if data_fine >= data_inizio_scelta:
            mesi = (data_fine.year - data_inizio_scelta.year) * 12 + (data_fine.month - data_inizio_scelta.month) + 1
        else:
            mesi = 0
        tfr_mensile = round(float(p.tfr_orario) * ore_m * coeff, 4) if p else 0
        cumulativo = round(tfr_mensile * mesi, 2)

    # Genera PDF
    pdf_bytes, nome_file_disk = _build_liquidazione_tfr_pdf_bytes(
        contratto, data_inizio_eff, data_fine, mesi, tfr_mensile, cumulativo, tfr_orario, ore_m, coeff
    )
    cartella = _get_cartella_documenti(contratto)
    full_path = os.path.join(cartella, nome_file_disk)
    os.makedirs(cartella, exist_ok=True)
    with open(full_path, 'wb') as f:
        f.write(pdf_bytes)

    # Crea DocumentoArchiviato
    d = DocumentoArchiviato.objects.create(
        tipo='BUSTA_TFR',
        titolo=f"Liquidazione TFR {contratto.lavoratore.nome_cognome} ({data_inizio_eff.strftime('%d/%m/%Y')} – {data_fine.strftime('%d/%m/%Y')})",
        file_path=full_path, file_size=len(pdf_bytes), file_name=nome_file_disk,
        contratto=contratto, datore=contratto.datore, lavoratore=contratto.lavoratore,
        creato_da=request.user if request.user.is_authenticated else None,
    )

    # Prepara tfr_data
    tfr_data = {
        'modalita_tfr': contratto.modalita_tfr,
        'data_inizio': data_inizio_eff.isoformat(),
        'data_fine': data_fine.isoformat(),
        'mesi': mesi,
        'tfr_orario': tfr_orario,
        'ore_mensili': ore_m,
        'coefficiente': coeff,
        'tfr_mensile': tfr_mensile,
        'cumulativo': cumulativo,
        'tipo': 'liquidazione_mensile',
    }

    # Crea/aggiorna BustaPaga
    bp, created = BustaPaga.objects.update_or_create(
        contratto=contratto, mese=mese, anno=anno,
        defaults=dict(
            tipo_calcolo='TFR',
            budget_mensile=0,
            ore_mensili=ore_m,
            ore_inps=ore_m,
            ore_settimanali=getattr(contratto, 'ore_settimanali_calcolate', 0) or 0,
            paga_oraria_lorda=Decimal(str(tfr_orario)),
            paga_base_totale=0,
            totale_indennita=0,
            scatti_totale=0,
            totale_lordo=cumulativo,
            contributi_inps_orario=0,
            contributi_inps_totale=0,
            contributi_inps_fascia='',
            contributi_inps_quota_datore=0,
            contributi_inps_quota_lavoratore=0,
            contributi_cassa_orario=0,
            contributi_cassa_totale=0,
            contributi_cassa_nome='',
            totale_contributi=0,
            convivenza_totale=0,
            totale_accantonati=0,
            netto=cumulativo,
            indennita_json={},
            ratei_pagati_json=[],
            scatti_dettaglio_json={},
            progetti_json=[],
            tfr_data=tfr_data,
            documento=d,
        )
    )

    return JsonResponse({
        'ok': True,
        'pk': bp.pk,
        'creato': created,
        'stato': bp.stato,
        'contratto_pk': contratto.pk,
        'mese': mese,
        'anno': anno,
        'cumulativo': cumulativo,
    })


# --- buste_archivio ---
@login_required
@permesso_richiesto('buste.vedi')
@never_cache
def buste_archivio(request):
    opzioni = get_opzioni()
    qs = BustaPaga.objects.select_related(
        'contratto__datore', 'contratto__lavoratore', 'contratto__parametri_minimi__livello',
        'documento'
    ).all()
    tipo = request.GET.get('tipo', '')
    if tipo:
        qs = qs.filter(tipo_calcolo=tipo)
    stato = request.GET.get('stato', '')
    if stato:
        qs = qs.filter(stato=stato)
    datore_q = request.GET.get('datore', '')
    if datore_q:
        qs = qs.filter(contratto__datore__nome_cognome__icontains=datore_q)
    lavoratore_q = request.GET.get('lavoratore', '')
    if lavoratore_q:
        qs = qs.filter(contratto__lavoratore__nome_cognome__icontains=lavoratore_q)
    mese_f = request.GET.get('mese')
    if mese_f:
        try:
            qs = qs.filter(mese=int(mese_f))
        except ValueError:
            logger.warning("Valore mese filtro non valido: %s", mese_f)
    anno_f = request.GET.get('anno')
    if anno_f:
        try:
            qs = qs.filter(anno=int(anno_f))
        except ValueError:
            logger.warning("Valore anno filtro non valido: %s", anno_f)
    contratto_pk_f = request.GET.get('contratto_pk', '')
    if contratto_pk_f:
        try:
            qs = qs.filter(contratto__pk=int(contratto_pk_f))
        except ValueError:
            logger.warning("Valore contratto_pk filtro non valido: %s", contratto_pk_f)
    return render(request, 'paghe/buste_archivio.html', {
        'opzioni': opzioni,
        'buste': qs,
        'tipi_calcolo': ['STANDARD', 'CONVIVENTE', 'NON_CONVIVENTE', 'SOSTITUZIONE', 'NOTTURNO', 'MALATTIA', 'CALCOLO_INVERSO', 'TFR', 'CONVIVENTI_CCNL'],
        'stati': ['BOZZA', 'APPROVATA', 'ARCHIVIATA'],
        'mesi_range': range(1, 13),
        'anni_range': range(2024, 2029),
        'filtro_tipo': tipo,
        'filtro_stato': stato,
        'filtro_datore': datore_q,
        'filtro_lavoratore': lavoratore_q,
        'filtro_mese': mese_f,
        'filtro_anno': anno_f,
        'filtro_contratto_pk': contratto_pk_f,
    })


# --- ajax_cambia_stato_busta ---
@login_required
@permesso_richiesto('buste.approva')
@require_http_methods(['POST'])
def ajax_cambia_stato_busta(request, pk):
    bp = get_object_or_404(BustaPaga, pk=pk)
    nuovo_stato = request.POST.get('stato', '')
    if nuovo_stato not in ('BOZZA', 'APPROVATA', 'ARCHIVIATA'):
        return JsonResponse({'errore': 'Stato non valido'}, status=400)
    bp.stato = nuovo_stato
    bp.save(update_fields=['stato'])
    return JsonResponse({'ok': True, 'stato': bp.stato})


# --- ajax_elimina_busta ---
@login_required
@permesso_richiesto('buste.approva')
@require_http_methods(['POST'])
def ajax_elimina_busta(request, pk):
    bp = get_object_or_404(BustaPaga, pk=pk)
    bp.delete()
    return JsonResponse({'ok': True, 'pk': pk})


# --- ajax_associa_documento_busta ---
@login_required
@permesso_richiesto('buste.calcola')
@require_http_methods(['POST'])
def ajax_associa_documento_busta(request, pk):
    bp = get_object_or_404(BustaPaga, pk=pk)
    doc_pk = request.POST.get('documento_pk')
    if not doc_pk:
        return JsonResponse({'errore': 'documento_pk richiesto'}, status=400)
    try:
        doc = DocumentoArchiviato.objects.get(pk=int(doc_pk))
    except (ValueError, DocumentoArchiviato.DoesNotExist):
        return JsonResponse({'errore': 'Documento non trovato'}, status=400)
    bp.documento = doc
    bp.save(update_fields=['documento'])
    return JsonResponse({'ok': True})


# --- ajax_stampa_busta ---
@login_required
@permesso_richiesto('buste.vedi')
@require_http_methods(['POST'])
def ajax_stampa_busta(request, pk):
    """Stampa la busta paga associata a un DocumentoArchiviato, partendo dal pk BustaPaga."""
    busta = get_object_or_404(BustaPaga, pk=pk)
    if not busta.documento:
        return JsonResponse({'ok': False, 'errore': 'Nessun documento associato a questa busta paga.'})
    doc = busta.documento
    if not doc.file_path or not os.path.exists(doc.file_path):
        return JsonResponse({'ok': False, 'errore': 'File PDF non trovato sul disco.'})
    ok = _stampa_pdf_windows(doc.file_path)
    if ok:
        doc.stampato = True
        doc.data_stampa = timezone.now()
        doc.save(update_fields=['stampato', 'data_stampa'])
    return JsonResponse({'ok': ok, 'errore': None if ok else 'Impossibile stampare. Verifica il lettore PDF predefinito.'})


# --- ajax_genera_pdf_busta ---
@login_required
@permesso_richiesto('buste.calcola')
@require_http_methods(['POST'])
def ajax_genera_pdf_busta(request, busta_pk):
    """Genera PDF per busta paga e restituisce JSON con info documento."""
    busta = get_object_or_404(BustaPaga, pk=busta_pk)

    if busta.documento:
        return JsonResponse({
            'ok': True,
            'documento_pk': busta.documento.pk,
            'file_url': f'/ajax/vedi-documento/{busta.documento.pk}/',
            'already_exists': True
        })

    contratto = busta.contratto
    mese, anno = busta.mese, busta.anno

    ctx = _calcola_busta_data(contratto, mese, anno)
    if 'errore' in ctx:
        return JsonResponse({'ok': False, 'errore': ctx['errore']})

    progetti_data = _calcola_progetti_data(ctx, contratto) if ctx.get('progetti') else None

    f"busta_{contratto.lavoratore.nome_cognome.replace(' ', '_')}_{mese:02d}_{anno}.pdf"
    cartella = _get_cartella_documenti(contratto)
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    safe_name = contratto.lavoratore.nome_cognome.replace(' ', '_').replace('/', '_')
    nome_file_disk = f"busta_{safe_name}_{mese:02d}_{anno}_{timestamp}.pdf"
    full_path = os.path.join(cartella, nome_file_disk)

    template_testo = contratto.busta_template if contratto.busta_template and contratto.busta_template.tipo == 'BUSTA_PAGA' else None
    pdf = None

    if template_testo:
        html_busta = _genera_html_busta(ctx, progetti_data)
        extra_vars = {
            'BUSTA_CONTENUTO': html_busta,
            'BUSTA_MESE_NOME': ctx.get('mese_nome', ''),
            'BUSTA_ANNO': str(ctx.get('anno', '')),
        }
        corpo_risolto = _risolvi_variabili_testo(template_testo.corpo_testo, contratto, extra_vars=extra_vars)
        oggetto_risolto = _risolvi_variabili_testo(template_testo.oggetto_titolo or '', contratto, extra_vars=extra_vars)

        try:
            _pdf_buffer = _genera_pdf_da_testo(
                tipo='PAGA_STANDARD',
                titolo=oggetto_risolto,
                corpo=corpo_risolto,
                output_path=full_path
            )
            if _pdf_buffer is not None:
                pdf = _pdf_buffer.getvalue()
        except Exception:
            logger.exception("Errore in ajax_genera_pdf_busta")
            pdf = None

    if pdf is None:
        pdf, _ = _genera_busta_completa_pdf_bytes(contratto, mese, anno, ctx_override=ctx)
        if pdf is None:
            return JsonResponse({'ok': False, 'errore': 'Errore generazione PDF'})

    with open(full_path, 'wb') as f:
        f.write(pdf)

    d = DocumentoArchiviato.objects.create(
        tipo='PAGA_STANDARD',
        titolo=f"Busta Paga {contratto.lavoratore.nome_cognome} {mese:02d}/{anno}",
        file_path=full_path,
        file_size=len(pdf),
        file_name=nome_file_disk,
        contratto=contratto,
        datore=contratto.datore,
        lavoratore=contratto.lavoratore,
        creato_da=request.user if request.user.is_authenticated else None,
    )

    busta.documento = d
    busta.save(update_fields=['documento'])

    return JsonResponse({
        'ok': True,
        'documento_pk': d.pk,
        'file_url': f'/ajax/vedi-documento/{d.pk}/',
        'already_exists': False
    })
