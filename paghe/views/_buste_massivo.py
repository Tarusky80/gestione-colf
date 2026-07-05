"""Modulo _buste_massivo - generato automaticamente da views.py"""

from paghe.views._common_imports import *

logger = logging.getLogger(__name__)

from paghe.views._helpers import _get_cartella_documenti, _wrap_html_email
from paghe.views._buste_pdf import _genera_busta_completa_pdf_bytes
from paghe.views._testi import _componi_corpo_email




# --- _genera_busta_massivo_pdf ---


# ═══════════════════════════════════════════════════════════════
#  BUSTE PAGA MASSIVE
# ═══════════════════════════════════════════════════════════════

def _genera_busta_massivo_pdf(contratto, mese, anno, user=None):
    """Genera il PDF busta paga (stessa logica di download_busta_pdf), salva DocumentoArchiviato.
    Restituisce (doc_archiviato, pdf_bytes)."""
    pdf, ctx = _genera_busta_completa_pdf_bytes(contratto, mese, anno)
    if pdf is None:
        return None, ctx.get('errore', '')

    cartella = _get_cartella_documenti(contratto)
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    safe_name = contratto.lavoratore.nome_cognome.replace(' ', '_').replace('/', '_') if contratto.lavoratore else f"contratto_{contratto.pk}"
    nome_file = f"busta_paga_{safe_name}_{mese:02d}_{anno}_{timestamp}.pdf"
    full_path = os.path.join(cartella, nome_file)
    with open(full_path, 'wb') as f:
        f.write(pdf)

    doc_arch = DocumentoArchiviato.objects.create(
        tipo='BUSTA_MASSIVA',
        titolo=f"Busta paga {contratto.lavoratore} - {mese:02d}/{anno}",
        file_path=full_path,
        file_size=os.path.getsize(full_path),
        file_name=nome_file,
        contratto=contratto,
        datore=contratto.datore,
        lavoratore=contratto.lavoratore,
        creato_da=user,
    )
    return doc_arch, pdf


# --- buste_paga_massivo ---


@login_required
@permesso_richiesto('buste.calcola')
def buste_paga_massivo(request):
    """Pagina per generazione massiva buste paga."""
    opzioni = get_opzioni()
    contratti = ContrattoAttivo.objects.filter(stato='ATTIVO').select_related(
        'datore', 'lavoratore', 'parametri_minimi__livello'
    ).order_by('datore__nome_cognome', 'lavoratore__nome_cognome')

    modelli_email = ModelloDocumentale.objects.filter(tipo='MAIL').order_by('codice')

    oggi = date.today()
    mesi = [(i, ['','Gennaio','Febbraio','Marzo','Aprile','Maggio','Giugno',
                  'Luglio','Agosto','Settembre','Ottobre','Novembre','Dicembre'][i]) for i in range(1, 13)]
    anni = list(range(oggi.year - 5, oggi.year + 2))

    return render(request, 'paghe/buste_paga_massivo.html', {
        'opzioni': opzioni,
        'contratti': contratti,
        'modelli_email': modelli_email,
        'mesi': mesi,
        'anni': anni,
        'mese_corrente': oggi.month,
        'anno_corrente': oggi.year,
    })


# --- ajax_genera_buste_massivo ---
@login_required
@permesso_richiesto('buste.calcola')
@require_http_methods(['POST'])
def ajax_genera_buste_massivo(request):
    """Genera buste paga per contratti selezionati."""
    import json as json_lib
    data = json_lib.loads(request.body)
    contratti_pk = data.get('contratti', [])
    mese = int(data.get('mese', date.today().month))
    anno = int(data.get('anno', date.today().year))
    azione = data.get('azione', 'pdf')

    if not contratti_pk:
        return JsonResponse({'error': 'Nessun contratto selezionato'}, status=400)

    contratti = ContrattoAttivo.objects.filter(pk__in=contratti_pk, stato='ATTIVO').select_related(
        'datore', 'lavoratore'
    )

    dettaglio = []
    totale_ok = 0
    totale_errori = 0
    pdf_paths = []

    for c in contratti:
        doc, pdf = _genera_busta_massivo_pdf(c, mese, anno, request.user)
        if doc is None:
            dettaglio.append({
                'contratto_pk': c.pk,
                'datore': str(c.datore),
                'lavoratore': str(c.lavoratore),
                'documento_pk': None,
                'email_destinatario': '',
                'inviato': False,
                'errore': pdf or 'Errore generazione PDF',
            })
            totale_errori += 1
        else:
            dettaglio.append({
                'contratto_pk': c.pk,
                'datore': str(c.datore),
                'lavoratore': str(c.lavoratore),
                'documento_pk': doc.pk,
                'email_destinatario': '',
                'inviato': False,
                'errore': '',
            })
            pdf_paths.append(doc.file_path)
            totale_ok += 1

    zip_path = ''
    if azione == 'zip' and pdf_paths:
        import zipfile
        cartella_zip = os.path.join(settings.MEDIA_ROOT, 'documenti', 'BUSTE_PAGA_ZIP')
        if not os.path.exists(cartella_zip):
            os.makedirs(cartella_zip)
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        zip_name = f"buste_paga_{mese:02d}_{anno}_{timestamp}.zip"
        zip_full = os.path.join(cartella_zip, zip_name)
        with zipfile.ZipFile(zip_full, 'w', zipfile.ZIP_DEFLATED) as zf:
            for path in pdf_paths:
                if os.path.exists(path):
                    zf.write(path, os.path.basename(path))
        zip_path = zip_full

    riepilogo = RiepilogoInvio.objects.create(
        creato_da=request.user,
        mese=mese,
        anno=anno,
        totale_contratti=len(contratti_pk),
        totale_ok=totale_ok,
        totale_errori=totale_errori,
        dettaglio=dettaglio,
        archivio_zip_path=zip_path,
    )

    # Invio email (Thunderbird o mailto)
    modello_email_pk = data.get('modello_email_pk')
    apri_thunderbird = data.get('apri_thunderbird', False)
    mailto_links = []
    thunderbird_aperto = 0
    if modello_email_pk and totale_ok > 0:
        modello = get_object_or_404(ModelloDocumentale, pk=modello_email_pk, tipo='MAIL')
        opzioni = get_opzioni()
        dettaglio_aggiornato = list(riepilogo.dettaglio)

        doc_pks = [e['documento_pk'] for e in dettaglio_aggiornato if e.get('documento_pk')]
        docs_map = {d.pk: d for d in DocumentoArchiviato.objects.filter(pk__in=doc_pks).select_related('contratto__datore', 'contratto__lavoratore')}

        for i, entry in enumerate(dettaglio_aggiornato):
            if not entry.get('documento_pk'):
                continue
            doc = docs_map.get(entry['documento_pk'])
            if not doc or not doc.contratto:
                continue
            contratto = doc.contratto

            try:
                corpo, oggetto = _componi_corpo_email(modello, contratto, opzioni)
            except Exception:
                logger.exception("Errore in ajax_genera_buste_massivo")
                dettaglio_aggiornato[i]['errore'] = 'Errore composizione email'
                continue

            destinatario = ''
            destinatario = ';'.join(filter(None, [
                contratto.lavoratore.email if contratto.lavoratore else '',
                contratto.datore.email if contratto.datore else '',
            ]))
            dettaglio_aggiornato[i]['email_destinatario'] = destinatario

            if destinatario and apri_thunderbird and opzioni and opzioni.email_usa_programma_posta and opzioni.exe_posta:
                import subprocess
                try:
                    def _tb_quote(s):
                        return s.replace("'", "''")
                    body_q = _tb_quote(corpo)
                    subj_q = _tb_quote(oggetto)
                    params = (f"to='{destinatario}',"
                             f"subject='{subj_q}',"
                             f"body='{body_q}',"
                             f"attachment='{doc.file_path}'")
                    subprocess.Popen([opzioni.exe_posta, '-compose', params])
                    doc.inviato = True
                    doc.inviato_il = timezone.now()
                    doc.email_destinatario = destinatario
                    doc.save()
                    dettaglio_aggiornato[i]['inviato'] = True
                    dettaglio_aggiornato[i]['errore'] = ''
                    thunderbird_aperto += 1
                except Exception as ex:
                    logger.exception("Errore in _tb_quote")
                    dettaglio_aggiornato[i]['inviato'] = False
                    dettaglio_aggiornato[i]['errore'] = f'Errore apertura Thunderbird: {ex}'
                    mailto_links.append('')
            elif destinatario:
                _wrap_html_email(corpo).replace('&', '%26').replace('?', '%3F').replace('=', '%3D').replace(' ', '%20')
                mailto_links.append(f"mailto:{destinatario}?subject={oggetto.replace(' ', '%20')}&body=Allega manualmente il PDF dalla cartella documenti.")
                dettaglio_aggiornato[i]['inviato'] = False
                dettaglio_aggiornato[i]['errore'] = ''
            else:
                dettaglio_aggiornato[i]['inviato'] = False
                dettaglio_aggiornato[i]['errore'] = 'Nessun indirizzo email disponibile per lavoratore o datore'
                mailto_links.append('')

        riepilogo.dettaglio = dettaglio_aggiornato
        riepilogo.totale_ok = sum(1 for e in dettaglio_aggiornato if e.get('inviato'))
        riepilogo.totale_errori = sum(1 for e in dettaglio_aggiornato if e.get('errore'))
        riepilogo.modello_email = modello
        riepilogo.save()

    return JsonResponse({
        'ok': True,
        'riepilogo_pk': riepilogo.pk,
        'totale_contratti': len(contratti_pk),
        'totale_ok': riepilogo.totale_ok,
        'totale_errori': riepilogo.totale_errori,
        'zip_path': zip_path,
        'dettaglio': riepilogo.dettaglio,
        'email_inviate': riepilogo.totale_ok if modello_email_pk else None,
        'mailto_links': mailto_links if mailto_links else None,
        'thunderbird_aperto': thunderbird_aperto,
    })


# --- ajax_genera_busta_per_email ---
@login_required
@permesso_richiesto('buste.invia')
@require_http_methods(['POST'])
def ajax_genera_busta_per_email(request, contratto_pk):
    """Genera busta paga per un singolo contratto e restituisce il pk del documento."""
    import json as json_lib
    from datetime import date
    data = json_lib.loads(request.body)
    mese = int(data.get('mese', date.today().month))
    anno = int(data.get('anno', date.today().year))
    contratto = get_object_or_404(ContrattoAttivo, pk=contratto_pk)
    doc, pdf = _genera_busta_massivo_pdf(contratto, mese, anno, request.user)
    if doc is None:
        return JsonResponse({'error': pdf}, status=400)
    return JsonResponse({'ok': True, 'doc_pk': doc.pk})


# --- ajax_invia_buste_massivo ---
@login_required
@permesso_richiesto('buste.invia')
@require_http_methods(['POST'])
def ajax_invia_buste_massivo(request):
    """Invia buste paga di un RiepilogoInvio (Thunderbird o link mailto)."""
    import json as json_lib
    data = json_lib.loads(request.body)
    riepilogo_pk = data.get('riepilogo_pk')
    modello_email_pk = data.get('modello_email_pk')
    apri_thunderbird = data.get('apri_thunderbird', False)

    riepilogo = get_object_or_404(RiepilogoInvio, pk=riepilogo_pk)
    modello = get_object_or_404(ModelloDocumentale, pk=modello_email_pk, tipo='MAIL')
    opzioni = get_opzioni()

    mailto_links = []
    thunderbird_aperto = 0
    dettaglio_aggiornato = []
    for entry in riepilogo.dettaglio:
        if not entry.get('documento_pk'):
            dettaglio_aggiornato.append(entry)
            continue

        doc = DocumentoArchiviato.objects.filter(pk=entry['documento_pk']).first()
        if not doc or not doc.contratto:
            entry['errore'] = 'Documento o contratto non trovato'
            dettaglio_aggiornato.append(entry)
            continue

        contratto = doc.contratto

        try:
            corpo, oggetto = _componi_corpo_email(modello, contratto, opzioni)
        except Exception:
            logger.exception("Errore in ajax_invia_buste_massivo")
            entry['errore'] = 'Errore composizione email'
            dettaglio_aggiornato.append(entry)
            continue

        destinatario = ''
        destinatario = ';'.join(filter(None, [
            contratto.lavoratore.email if contratto.lavoratore else '',
            contratto.datore.email if contratto.datore else '',
        ]))
        entry['email_destinatario'] = destinatario

        if destinatario and apri_thunderbird and opzioni and opzioni.email_usa_programma_posta and opzioni.exe_posta:
            import subprocess
            try:
                def _tb_quote(s):
                    return s.replace("'", "''")
                body_q = _tb_quote(corpo)
                subj_q = _tb_quote(oggetto)
                params = (f"to='{destinatario.replace(';', ',')}',"
                         f"subject='{subj_q}',"
                         f"body='{body_q}',"
                         f"attachment='{doc.file_path}'")
                subprocess.Popen([opzioni.exe_posta, '-compose', params])
                doc.inviato = True
                doc.inviato_il = timezone.now()
                doc.email_destinatario = destinatario
                doc.save()
                entry['inviato'] = True
                entry['errore'] = ''
                thunderbird_aperto += 1
            except Exception as ex:
                logger.exception("Errore in _tb_quote")
                entry['inviato'] = False
                entry['errore'] = f'Errore apertura Thunderbird: {ex}'
                mailto_links.append('')
        elif destinatario:
            _wrap_html_email(corpo).replace('&', '%26').replace('?', '%3F').replace('=', '%3D').replace(' ', '%20')
            mailto_links.append(f"mailto:{destinatario}?subject={oggetto.replace(' ', '%20')}&body=Allega manualmente il PDF dalla cartella documenti.")
            entry['inviato'] = False
            entry['errore'] = ''
        else:
            entry['inviato'] = False
            entry['errore'] = 'Nessun indirizzo email disponibile'
            mailto_links.append('')

        dettaglio_aggiornato.append(entry)

    tot_ok = sum(1 for e in dettaglio_aggiornato if e.get('inviato'))
    tot_err = sum(1 for e in dettaglio_aggiornato if e.get('errore'))
    riepilogo.dettaglio = dettaglio_aggiornato
    riepilogo.totale_ok = tot_ok
    riepilogo.totale_errori = tot_err
    riepilogo.modello_email = modello
    riepilogo.save()

    return JsonResponse({
        'ok': True,
        'riepilogo_pk': riepilogo.pk,
        'totale_ok': tot_ok,
        'totale_errori': tot_err,
        'mailto_links': mailto_links if mailto_links else None,
        'thunderbird_aperto': thunderbird_aperto,
    })


# --- riepilogo_invio_list ---
@login_required
@permesso_richiesto('buste.vedi')
def riepilogo_invio_list(request):
    """Elenco storico dei riepiloghi invio."""
    opzioni = get_opzioni()
    riepiloghi = RiepilogoInvio.objects.select_related('creato_da', 'modello_email').all()
    return render(request, 'paghe/riepilogo_invio_list.html', {'opzioni': opzioni, 'riepiloghi': riepiloghi})


# --- riepilogo_invio_dettaglio ---
@login_required
@permesso_richiesto('buste.vedi')
def riepilogo_invio_dettaglio(request, pk):
    """Dettaglio di un singolo RiepilogoInvio."""
    opzioni = get_opzioni()
    riepilogo = get_object_or_404(RiepilogoInvio, pk=pk)
    modelli_email = ModelloDocumentale.objects.filter(tipo='MAIL').order_by('codice')
    return render(request, 'paghe/riepilogo_invio_dettaglio.html', {
        'opzioni': opzioni,
        'riepilogo': riepilogo,
        'modelli_email': modelli_email,
    })


# --- download_riepilogo_zip ---
@login_required
@permesso_richiesto('buste.vedi')
def download_riepilogo_zip(request, pk):
    """Download ZIP di tutti i PDF di un RiepilogoInvio."""
    riepilogo = get_object_or_404(RiepilogoInvio, pk=pk)
    if riepilogo.archivio_zip_path and os.path.exists(riepilogo.archivio_zip_path):
        with open(riepilogo.archivio_zip_path, 'rb') as f:
            zip_data = f.read()
        nome = os.path.basename(riepilogo.archivio_zip_path)
        response = HttpResponse(zip_data, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{nome}"'
        return response

    import zipfile
    from io import BytesIO
    buf = BytesIO()
    doc_pks = [e.get('documento_pk') for e in riepilogo.dettaglio if e.get('documento_pk')]
    docs_map = {d.pk: d for d in DocumentoArchiviato.objects.filter(pk__in=doc_pks)}
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for entry in riepilogo.dettaglio:
            doc_pk = entry.get('documento_pk')
            if doc_pk:
                doc = docs_map.get(doc_pk)
                if doc and os.path.exists(doc.file_path):
                    zf.write(doc.file_path, doc.file_name)
    zip_data = buf.getvalue()
    buf.close()
    nome = f"buste_paga_{riepilogo.mese:02d}_{riepilogo.anno}_{riepilogo.pk}.zip"
    response = HttpResponse(zip_data, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{nome}"'
    return response


# --- ajax_elimina_riepilogo_invio ---
@login_required
@permesso_richiesto('buste.approva')
@require_http_methods(['POST'])
def ajax_elimina_riepilogo_invio(request, pk):
    """Elimina un RiepilogoInvio e il relativo ZIP su disco."""
    riepilogo = get_object_or_404(RiepilogoInvio, pk=pk)
    if riepilogo.archivio_zip_path and os.path.exists(riepilogo.archivio_zip_path):
        try:
            os.remove(riepilogo.archivio_zip_path)
        except Exception:
            logger.warning("Impossibile eliminare ZIP riepilogo: %s", riepilogo.archivio_zip_path)
    riepilogo.delete()
    return JsonResponse({'ok': True})


# --- ajax_elimina_tutti_riepilogo_invio ---
@login_required
@permesso_richiesto('buste.approva')
@require_http_methods(['POST'])
def ajax_elimina_tutti_riepilogo_invio(request):
    """Elimina tutti i RiepilogoInvio e i relativi ZIP su disco."""
    riepiloghi = RiepilogoInvio.objects.all()
    for r in riepiloghi:
        if r.archivio_zip_path and os.path.exists(r.archivio_zip_path):
            try:
                os.remove(r.archivio_zip_path)
            except Exception:
                logger.warning("Impossibile eliminare ZIP riepilogo (massivo): %s", r.archivio_zip_path)
    count = riepiloghi.count()
    riepiloghi.delete()
    return JsonResponse({'ok': True, 'message': f'{count} riepiloghi eliminati definitivamente.'})
