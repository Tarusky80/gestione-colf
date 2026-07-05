"""Modulo _documenti - generato automaticamente da views.py"""

from paghe.views._common_imports import *

logger = logging.getLogger(__name__)

from paghe.views._helpers import _get_cartella_documenti, _wrap_html_email, _genera_pdf_da_testo_playwright, _risolvi_globali
from paghe.views._testi import _componi_corpo_email, _risolvi_variabili_testo
from paghe.views._invia_email import invia_documento_email, invia_email_senza_documento




# --- documenti_list ---
@login_required
@permesso_richiesto('documenti.vedi')
@never_cache
def documenti_list(request):
    from django.db.models import Prefetch
    from django.core.paginator import Paginator
    qs = DocumentoArchiviato.objects.select_related('contratto', 'datore', 'lavoratore', 'modello_documentale', 'creato_da').prefetch_related(
        Prefetch('contratto__progetto', queryset=ProgettoRegionale.objects.select_related('beneficiario', 'tipo'))
    ).all()
    tipo = request.GET.get('tipo', '')
    if tipo:
        qs = qs.filter(tipo=tipo)
    datore_q = request.GET.get('datore', '')
    if datore_q:
        qs = qs.filter(Q(datore__nome_cognome__icontains=datore_q) | Q(contratto__datore__nome_cognome__icontains=datore_q))
    da = request.GET.get('da', '')
    if da:
        qs = qs.filter(creato_il__date__gte=da)
    a = request.GET.get('a', '')
    if a:
        qs = qs.filter(creato_il__date__lte=a)
    contratto_pk = request.GET.get('contratto_pk', '')
    if contratto_pk:
        qs = qs.filter(contratto__pk=contratto_pk)
    datore_pk = request.GET.get('datore_pk', '')
    if datore_pk:
        qs = qs.filter(Q(datore__pk=datore_pk) | Q(contratto__datore__pk=datore_pk))
    lavoratore_pk = request.GET.get('lavoratore_pk', '')
    if lavoratore_pk:
        qs = qs.filter(contratto__lavoratore__pk=lavoratore_pk)
    beneficiario_pk = request.GET.get('beneficiario_pk', '')
    if beneficiario_pk:
        qs = qs.filter(contratto__progetto__beneficiario__pk=beneficiario_pk).distinct()
    inviato = request.GET.get('inviato', '')
    if inviato == 'si':
        qs = qs.filter(inviato=True)
    elif inviato == 'no':
        qs = qs.filter(inviato=False)
    qs = qs.order_by('-pk')
    paginator = Paginator(qs, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    return render(request, 'paghe/documenti_list.html', {
        'documenti': page_obj.object_list,
        'page_obj': page_obj,
        'tipi_documento': DocumentoArchiviato.TIPO_SCELTE,
        'tipo_colori': {
            'PAGA_STANDARD': '#10b981',
            'NON_CONVIVENTE': '#f59e0b',
            'CONVIVENTI_CCNL': '#8b5cf6',
            'CALCOLO_INVERSO': '#f97316',
            'BUSTA_MASSIVA': '#ec4899',
            'MALATTIA': '#34d399',
            'NOTTURNO': '#6366f1',
            'SOSTITUZIONE': '#14b8a6',
            'BUSTA_TFR': '#fbbf24',
            'LIQUIDAZIONE_TFR': '#ef4444',
            'RIEPILOGO_PAGOPA': '#5E6AD2',
            'PAGOPA': '#2563eb',
        },
        'filtro_tipo': tipo,
        'filtro_datore': datore_q,
        'filtro_da': da,
        'filtro_a': a,
        'filtro_inviato': inviato,
        'filtro_contratto_pk': contratto_pk,
        'filtro_datore_pk': datore_pk,
        'filtro_lavoratore_pk': lavoratore_pk,
        'filtro_beneficiario_pk': beneficiario_pk,
        'opzioni': get_opzioni(),
    })


# --- ajax_nuovo_documento ---
@login_required
@permesso_richiesto('documenti.crea')
@never_cache
def ajax_nuovo_documento(request):
    form = DocumentoArchiviatoForm()
    return render(request, 'frontend/ajax_form_documento.html', {'form': form, 'tipi': DocumentoArchiviato.TIPO_SCELTE})


# --- ajax_anteprima_documento ---
@login_required
@permesso_richiesto('documenti.vedi')
@require_http_methods(['POST'])
def ajax_anteprima_documento(request):
    import json as json_lib
    data = json_lib.loads(request.body)
    contratto_pk = data.get('contratto_pk')
    modello_pk = data.get('modello_pk')
    if not modello_pk:
        return JsonResponse({'error': 'Seleziona un modello testo.'}, status=400)
    modello = get_object_or_404(ModelloDocumentale, pk=modello_pk)
    corpo = modello.corpo_testo
    oggetto = modello.titolo
    if contratto_pk:
        c = get_object_or_404(ContrattoLavoro, pk=contratto_pk)
        corpo = _risolvi_variabili_testo(corpo, c)
        oggetto = _risolvi_variabili_testo(oggetto, c)
    return JsonResponse({'corpo': corpo, 'oggetto': oggetto})


# --- ajax_carica_documento ---
@login_required
@permesso_richiesto('documenti.crea')
@require_http_methods(['POST'])
def ajax_carica_documento(request):
    tipo = request.POST.get('tipo')
    titolo = request.POST.get('titolo', '')
    contratto_pk = request.POST.get('contratto_pk')
    note = request.POST.get('note', '')
    if not tipo:
        return JsonResponse({'error': 'Tipo documento obbligatorio.'}, status=400)
    if not titolo:
        return JsonResponse({'error': 'Titolo obbligatorio.'}, status=400)

    contratto = None
    if contratto_pk:
        contratto = get_object_or_404(ContrattoLavoro, pk=contratto_pk)

    cartella = _get_cartella_documenti(contratto)
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    contratto_suffix = f'_{contratto_pk}' if contratto_pk else ''
    uploaded = request.FILES.get('file')
    if uploaded:
        ext = os.path.splitext(uploaded.name)[1] or '.pdf'
        filename = f'{tipo.lower()}{contratto_suffix}_{timestamp}{ext}'
        full_path = os.path.join(cartella, filename)
        with open(full_path, 'wb+') as f:
            for chunk in uploaded.chunks():
                f.write(chunk)
        file_size = os.path.getsize(full_path)
    else:
        return JsonResponse({'error': 'Nessun file caricato.'}, status=400)

    datore = contratto.datore if contratto else None
    lavoratore = contratto.lavoratore if contratto else None

    doc = DocumentoArchiviato.objects.create(
        tipo=tipo,
        titolo=titolo,
        file_path=full_path,
        file_size=file_size,
        file_name=filename,
        contratto=contratto,
        datore=datore,
        lavoratore=lavoratore,
        note=note,
        creato_da=request.user if request.user.is_authenticated else None,
    )
    return JsonResponse({'ok': True, 'pk': doc.pk, 'filename': filename})


# --- ajax_vedi_documento ---
@login_required
@permesso_richiesto('documenti.vedi')
@never_cache
@xframe_options_exempt
def ajax_vedi_documento(request, pk):
    doc = get_object_or_404(DocumentoArchiviato, pk=pk)
    path = doc.file_path
    if not os.path.exists(path):
        return HttpResponse('File non trovato.', status=404)
    with open(path, 'rb') as f:
        content = f.read()
    mimetype, _ = mimetypes.guess_type(path)
    response = HttpResponse(content, content_type=mimetype or 'application/pdf')
    response['Content-Disposition'] = f'inline; filename="{doc.file_name}"'
    return response


# --- ajax_elimina_documento ---
@login_required
@permesso_richiesto('documenti.elimina')
@require_http_methods(['POST'])
def ajax_elimina_documento(request, pk):
    doc = get_object_or_404(DocumentoArchiviato, pk=pk)
    path = doc.file_path
    if os.path.exists(path):
        os.remove(path)
    doc.delete()
    return JsonResponse({'success': True})


# --- ajax_apri_cartella_documento ---
@login_required
@permesso_richiesto('documenti.vedi')
def ajax_apri_cartella_documento(request, pk):
    doc = get_object_or_404(DocumentoArchiviato, pk=pk)
    path = doc.file_path
    if not path:
        return JsonResponse({'error': 'Percorso file non presente'}, status=400)
    folder = os.path.dirname(os.path.normpath(path))
    if not folder or not os.path.exists(folder):
        return JsonResponse({'error': 'Cartella non trovata: ' + str(folder)}, status=404)
    try:
        os.startfile(folder)
        return JsonResponse({'success': True})
    except Exception as e:
        logger.exception("Errore in ajax_apri_cartella_documento")
        try:
            subprocess.Popen(['explorer', folder], shell=True)
            return JsonResponse({'success': True, 'msg': 'fallback explorer'})
        except Exception as e2:
            logger.exception("Errore in ajax_apri_cartella_documento (fallback explorer)")
            return JsonResponse({'error': f'Errore: {e}, fallback: {e2}'}, status=500)


# --- apri_cartella_documento ---
@login_required
@permesso_richiesto('documenti.vedi')
def apri_cartella_documento(request, pk):
    doc = get_object_or_404(DocumentoArchiviato, pk=pk)
    path = doc.file_path
    html_ok = '<html><body style="background:#1a1a2e;color:#e2e8f0;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;"><div style="text-align:center;"><div style="font-size:48px;margin-bottom:16px;">📂</div><h2>Cartella aperta</h2><p style="color:#94a3b8;">Se non si apre, controlla la cartella documenti.</p><script>setTimeout(function(){window.close()},2000)</' + 'script></div></body></html>'
    html_err = '<html><body style="background:#1a1a2e;color:#e2e8f0;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;"><div style="text-align:center;"><div style="font-size:48px;margin-bottom:16px;">❌</div><h2>Cartella non trovata</h2><p style="color:#94a3b8;">' + str(path) + '</p></div></body></html>'
    if not path:
        return HttpResponse(html_err)
    folder = os.path.dirname(os.path.normpath(path))
    if folder and os.path.exists(folder):
        try:
            os.startfile(folder)
        except Exception:
            logger.warning("os.startfile fallito per: %s", folder)
            try:
                subprocess.Popen(['explorer', folder], shell=True)
            except Exception:
                logger.warning("Anche explorer.exe fallito per: %s", folder)
        return HttpResponse(html_ok)
    return HttpResponse(html_err)


# --- ajax_collega_documento_contratto ---
@login_required
@permesso_richiesto('documenti.crea')
@require_http_methods(['POST'])
def ajax_collega_documento_contratto(request, pk):
    import json as json_lib
    data = json_lib.loads(request.body)
    contratto_pk = data.get('contratto_pk')
    if not contratto_pk:
        return JsonResponse({'error': 'Seleziona un contratto.'}, status=400)
    doc = get_object_or_404(DocumentoArchiviato, pk=pk)
    nuovo_contratto = get_object_or_404(ContrattoLavoro, pk=contratto_pk)
    vecchio_path = doc.file_path
    nuova_cartella = _get_cartella_documenti(nuovo_contratto)
    vecchio_nome = os.path.basename(vecchio_path) if vecchio_path else ''
    nuovo_path = os.path.join(nuova_cartella, vecchio_nome) if vecchio_nome else ''
    if vecchio_path and os.path.exists(vecchio_path) and nuovo_path and os.path.normpath(vecchio_path) != os.path.normpath(nuovo_path):
        os.makedirs(nuova_cartella, exist_ok=True)
        shutil.move(vecchio_path, nuovo_path)
    doc.contratto = nuovo_contratto
    doc.datore = nuovo_contratto.datore
    doc.lavoratore = nuovo_contratto.lavoratore
    if nuovo_path:
        doc.file_path = nuovo_path
    doc.save()
    return JsonResponse({'success': True})


# --- ajax_invia_documento_email ---
@login_required
@permesso_richiesto('documenti.invia')
def ajax_invia_documento_email(request, pk):
    doc = get_object_or_404(DocumentoArchiviato, pk=pk)
    if request.method == 'GET':
        modelli = ModelloDocumentale.objects.filter(tipo='MAIL').values('pk', 'codice', 'oggetto_titolo')
        selected_pk = request.GET.get('selected_template', '')
        opts = ''.join(
            f'<option value="{m["pk"]}"{" selected" if str(m["pk"]) == selected_pk else ""}>'
            f'{m["codice"] or ""}{" - " if m["codice"] else ""}'
            f'{_risolvi_variabili_testo(m["oggetto_titolo"] or "Modello #"+str(m["pk"]), doc.contratto) if doc.contratto else _risolvi_globali(m["oggetto_titolo"] or "Modello #"+str(m["pk"]))}</option>'
            for m in modelli
        )
        dest_val = doc.email_destinatario or (doc.contratto.datore.email if doc.contratto and doc.contratto.datore else '')
        html = f'''<div class="p-4">
  <form id="formInvioEmail" onsubmit="inviaSingolo(event,{pk})" novalidate>
    <div class="mb-3">
      <label class="form-label small fw-bold" style="color:#a1a1aa;">Cerca destinatario</label>
      <input type="text" class="form-control" id="cercaEmailInvio" placeholder="Digita nome o email..." style="background:#09090b;border:1px solid #27272a;color:#fafafa;border-radius:8px;padding:10px 12px;font-size:13px;" oninput="window._cercaInvioHandler(this.value)" autocomplete="off">
      <div id="cercaEmailInvioResults" style="max-height:200px;overflow-y:auto;margin-top:4px;"></div>
    </div>
    <div class="mb-3">
      <label class="form-label small fw-bold" style="color:#a1a1aa;">Destinatario</label>
      <input type="email" class="form-control" id="emailDestinatario" value="{dest_val}" required style="background:#09090b;border:1px solid #27272a;color:#fafafa;border-radius:8px;padding:10px 12px;font-size:13px;">
    </div>
    <div class="mb-3">
      <label class="form-label small fw-bold" style="color:#a1a1aa;">Modello Email</label>
      <select class="form-control" id="modelloMail" required style="background:#09090b;border:1px solid #27272a;color:#fafafa;border-radius:8px;padding:10px 12px;font-size:13px;"><option value="">-- Seleziona --</option>{opts}</select>
    </div>
    <div class="d-flex gap-2 mt-4">
      <button type="button" onclick="anteprimaEmail({pk})" style="flex:1;background:transparent;border:1px solid #3f3f46;color:#a1a1aa;border-radius:8px;padding:10px;font-size:13px;font-weight:600;cursor:pointer;"><i class="bi bi-eye"></i> Anteprima</button>
      <button type="submit" style="flex:1;background:var(--accent-color,#5E6AD2);color:white;border:none;border-radius:8px;padding:10px;font-size:13px;font-weight:600;cursor:pointer;"><i class="bi bi-send"></i> Invia</button>
    </div>
  </form>
 </div>'''
        return HttpResponse(html)

    import json as json_lib
    data = json_lib.loads(request.body)
    destinatario = data.get('destinatario', '').strip()
    modello_mail_pk = data.get('modello_mail_pk')
    if not destinatario:
        return JsonResponse({'error': 'Inserisci un destinatario email.'}, status=400)
    if not modello_mail_pk or str(modello_mail_pk) == 'undefined':
        return JsonResponse({'error': 'Seleziona un modello email.'}, status=400)

    risultato = invia_documento_email(doc.pk, destinatario, modello_mail_pk, request)
    if risultato['ok']:
        return JsonResponse({'ok': True, 'msg': risultato.get('messaggio', 'Email inviata.')})
    return JsonResponse({'error': risultato.get('errore', 'Errore invio email.')}, status=500)


# --- ajax_ultimo_documento_pk ---
@login_required
@permesso_richiesto('documenti.vedi')
def ajax_ultimo_documento_pk(request):
    pk = request.session.get('ultimo_doc_pk')
    return JsonResponse({'doc_pk': pk})


# --- ajax_mail_datore ---
@login_required
@permesso_richiesto('documenti.invia')
def ajax_mail_datore(request, pk):
    contratto = get_object_or_404(ContrattoAttivo, pk=pk)
    datore = contratto.datore
    get_opzioni()
    if request.method == 'GET':
        modelli = ModelloDocumentale.objects.filter(tipo='MAIL').values('pk', 'codice', 'oggetto_titolo')
        opts = ''.join(f'<option value="{m["pk"]}">{m["codice"] or ""}{" - " if m["codice"] else ""}{_risolvi_variabili_testo(m["oggetto_titolo"] or "Modello #"+str(m["pk"]), contratto)}</option>' for m in modelli)
        email_datore = datore.email or ''
        html = f'''<div class="p-4">
  <form id="formMailDatore" onsubmit="inviaMailDatore(event,{pk})" novalidate>
    <div class="mb-3">
      <label class="form-label small fw-bold" style="color:#a1a1aa;">Destinatario</label>
      <input type="email" class="form-control" id="emailDestinatario" value="{email_datore}" required style="background:#09090b;border:1px solid #27272a;color:#fafafa;border-radius:8px;padding:10px 12px;font-size:13px;">
    </div>
    <div class="mb-3">
      <label class="form-label small fw-bold" style="color:#a1a1aa;">Modello Email</label>
      <select class="form-control" id="modelloMail" style="background:#09090b;border:1px solid #27272a;color:#fafafa;border-radius:8px;padding:10px 12px;font-size:13px;"><option value="">-- Seleziona --</option>{opts}</select>
    </div>
    <div class="d-flex gap-2 mt-4">
      <button type="button" onclick="anteprimaEmailDatore({pk})" style="flex:1;background:transparent;border:1px solid #3f3f46;color:#a1a1aa;border-radius:8px;padding:10px;font-size:13px;font-weight:600;cursor:pointer;"><i class="bi bi-eye"></i> Anteprima</button>
      <button type="submit" style="flex:1;background:var(--accent-color,#5E6AD2);color:white;border:none;border-radius:8px;padding:10px;font-size:13px;font-weight:600;cursor:pointer;"><i class="bi bi-send"></i> Invia</button>
    </div>
  </form>
</div>'''
        return HttpResponse(html)

    import json as json_lib
    data = json_lib.loads(request.body)
    destinatario = data.get('destinatario', '').strip()
    modello_mail_pk = data.get('modello_mail_pk')
    if not destinatario:
        return JsonResponse({'error': 'Inserisci un destinatario email.'}, status=400)
    if not modello_mail_pk or str(modello_mail_pk) == 'undefined':
        return JsonResponse({'error': 'Seleziona un modello email.'}, status=400)

    risultato = invia_email_senza_documento(destinatario, modello_mail_pk, contratto=contratto, request=request)
    if risultato['ok']:
        return JsonResponse({'ok': True, 'msg': risultato.get('messaggio', 'Email inviata.')})
    return JsonResponse({'error': risultato.get('errore', 'Errore invio email.')}, status=500)


# --- ajax_anteprima_email_datore ---
@login_required
@permesso_richiesto('documenti.invia')
@require_http_methods(['POST'])
def ajax_anteprima_email_datore(request, pk):
    contratto = get_object_or_404(ContrattoAttivo, pk=pk)
    import json as json_lib
    import re as _re
    data = json_lib.loads(request.body)
    modello_mail_pk = data.get('modello_mail_pk')
    if not modello_mail_pk:
        return JsonResponse({'error': 'Nessun modello selezionato.'}, status=400)
    modello = get_object_or_404(ModelloDocumentale, pk=modello_mail_pk)
    opzioni = get_opzioni()
    try:
        corpo, oggetto = _componi_corpo_email(modello, contratto, opzioni)
    except Exception as e:
        logger.exception("Errore in ajax_anteprima_email_datore")
        return JsonResponse({'error': f'Errore composizione email: {e}'}, status=500)
    corpo_html = _re.sub(r'\n', '<br>', corpo)
    return JsonResponse({'oggetto': oggetto, 'corpo': corpo_html})


# --- ajax_anteprima_email ---
@login_required
@permesso_richiesto('documenti.invia')
def ajax_anteprima_email(request, pk):
    doc = get_object_or_404(DocumentoArchiviato, pk=pk)
    modello_mail_pk = request.GET.get('modello_mail_pk')
    if not modello_mail_pk or str(modello_mail_pk) == 'undefined':
        return JsonResponse({'error': 'Nessun modello selezionato.'}, status=400)
    modello = get_object_or_404(ModelloDocumentale, pk=modello_mail_pk)
    opzioni = get_opzioni()
    try:
        corpo, oggetto = _componi_corpo_email(modello, doc.contratto, opzioni)
    except Exception as e:
        logger.exception("Errore in ajax_anteprima_email")
        return JsonResponse({'error': f'Errore composizione email: {e}'}, status=500)
    return JsonResponse({'oggetto': oggetto, 'corpo': corpo})


# --- ajax_invia_massivo_email ---
@login_required
@permesso_richiesto('documenti.invia')
@require_http_methods(['POST'])
def ajax_invia_massivo_email(request):
    import json as json_lib
    data = json_lib.loads(request.body)
    pks = data.get('pks', [])
    modello_mail_pk = data.get('modello_mail_pk')
    if not pks:
        return JsonResponse({'error': 'Nessun documento selezionato.'}, status=400)
    if not modello_mail_pk:
        return JsonResponse({'error': 'Seleziona un modello email.'}, status=400)

    documenti = DocumentoArchiviato.objects.filter(pk__in=pks).select_related('datore', 'lavoratore', 'contratto__datore')
    risultati = []
    for doc in documenti:
        destinatari = []
        if doc.datore and doc.datore.email:
            for e in doc.datore.email.split(';'):
                e = e.strip()
                if e and e not in destinatari:
                    destinatari.append(e)
        if doc.contratto and doc.contratto.datore and doc.contratto.datore.email:
            for e in doc.contratto.datore.email.split(';'):
                e = e.strip()
                if e and e not in destinatari:
                    destinatari.append(e)
        if doc.lavoratore and doc.lavoratore.email:
            for e in doc.lavoratore.email.split(';'):
                e = e.strip()
                if e and e not in destinatari:
                    destinatari.append(e)

        for dest in destinatari:
            try:
                risultato = invia_documento_email(doc.pk, dest, modello_mail_pk, request)
                risultati.append({'doc_pk': doc.pk, 'destinatario': dest, 'ok': risultato['ok'], 'error': risultato.get('errore')})
            except Exception as e:
                logger.exception("Errore in ajax_invia_massivo_email")
                risultati.append({'doc_pk': doc.pk, 'destinatario': dest, 'ok': False, 'error': str(e)})
    return JsonResponse({'ok': True, 'risultati': risultati, 'totale': len(risultati)})


# --- ajax_modelli_email ---
@login_required
@permesso_richiesto('documenti.vedi')
def ajax_modelli_email(request):
    modelli = ModelloDocumentale.objects.filter(tipo='MAIL').values('pk', 'codice', 'oggetto_titolo')
    for m in modelli:
        m['oggetto_titolo'] = _risolvi_globali(m['oggetto_titolo'] or '')
    return JsonResponse(list(modelli), safe=False)


# --- ajax_invia_email_raggruppata ---
@login_required
@permesso_richiesto('documenti.invia')
@require_http_methods(['POST'])
def ajax_invia_email_raggruppata(request):
    import json as json_lib
    data = json_lib.loads(request.body)
    pks = data.get('pks', [])
    destinatario = data.get('destinatario', '').strip()
    modello_mail_pk = data.get('modello_mail_pk')
    if not pks:
        return JsonResponse({'error': 'Nessun documento selezionato.'}, status=400)
    if not destinatario:
        return JsonResponse({'error': 'Inserisci un destinatario.'}, status=400)
    if not modello_mail_pk:
        return JsonResponse({'error': 'Seleziona un modello email.'}, status=400)
    documenti = DocumentoArchiviato.objects.filter(pk__in=pks).select_related('contratto')
    if not documenti:
        return JsonResponse({'error': 'Nessun documento trovato.'}, status=400)
    opzioni = get_opzioni()
    modello = get_object_or_404(ModelloDocumentale, pk=modello_mail_pk)
    corpo = modello.corpo_testo
    oggetto = modello.oggetto_titolo
    file_names = [doc.file_name for doc in documenti if doc.file_name]
    lista_allegati = '\n'.join(f'• {name}' for name in file_names)
    extra_vars = {'lista_allegati_multipli': lista_allegati}
    contratti = set(doc.contratto for doc in documenti if doc.contratto)
    try:
        if len(contratti) == 1:
            c = contratti.pop()
            corpo, oggetto = _componi_corpo_email(modello, c, opzioni, extra_vars=extra_vars)
        else:
            class _ModelloWrap:
                corpo_testo = modello.corpo_testo.replace('{{lista_allegati_multipli}}', lista_allegati)
                oggetto_titolo = (modello.oggetto_titolo or modello.codice or '').replace('{{lista_allegati_multipli}}', lista_allegati)
                codice = modello.codice
            corpo, oggetto = _componi_corpo_email(_ModelloWrap(), None, opzioni)
    except Exception as e:
        logger.exception("Errore in ajax_invia_email_raggruppata")
        return JsonResponse({'error': f'Errore composizione email: {e}'}, status=500)
    file_paths = [doc.file_path for doc in documenti if doc.file_path]
    if opzioni and opzioni.email_usa_programma_posta and opzioni.exe_posta:
        import subprocess
        def _tbq(s):
            return s.replace("'", "''")
        dest_q = _tbq(destinatario.replace(';', ','))
        subj_q = _tbq(oggetto)
        body_q = _tbq(corpo)
        attach_parts = ','.join(_tbq(p) for p in file_paths)
        params = (f"to='{dest_q}',"
                 f"subject='{subj_q}',"
                 f"body='{body_q}',"
                 f"attachment='{attach_parts}'")
        subprocess.Popen([opzioni.exe_posta, '-compose', params])
    else:
        import smtplib
        msg = MIMEMultipart()
        msg['From'] = opzioni.email_mittente if opzioni else ''
        msg['To'] = destinatario.replace(';', ',')
        msg['Subject'] = oggetto
        msg.attach(MIMEText(_wrap_html_email(corpo), 'html', 'utf-8'))
        for doc in documenti:
            if doc.file_path:
                with open(doc.file_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename="{doc.file_name}"')
                    msg.attach(part)
        smtp = smtplib.SMTP(opzioni.email_smtp_server, opzioni.email_smtp_port)
        if opzioni.email_usa_tls:
            smtp.starttls()
        if opzioni.email_smtp_username and opzioni.get_smtp_password():
            smtp.login(opzioni.email_smtp_username, opzioni.get_smtp_password())
        smtp.send_message(msg)
        smtp.quit()
    for doc in documenti:
        doc.inviato = True
        doc.inviato_il = timezone.now()
        doc.email_destinatario = destinatario
        doc.save()
    return JsonResponse({'ok': True, 'msg': f'Email inviata con {len(file_paths)} allegati.'})


# --- ajax_cerca_email ---
@login_required
@permesso_richiesto('documenti.vedi')
@never_cache
def ajax_cerca_email(request):
    q = request.GET.get('q', '').strip()
    results = []
    if q:
        from paghe.models import DatoreLavoro, Lavoratore
        from django.db.models import Q
        f = Q(email__icontains=q) | Q(nome_cognome__icontains=q)
        datori = DatoreLavoro.objects.filter(f).values('pk', 'nome_cognome', 'email')[:20]
        for d in datori:
            results.append({'type': 'datore', 'pk': d['pk'], 'label': f'{d["nome_cognome"]} ({d["email"]})', 'email': d['email']})
        lavoratori = Lavoratore.objects.filter(f).values('pk', 'nome_cognome', 'email')[:20]
        for l in lavoratori:
            results.append({'type': 'lavoratore', 'pk': l['pk'], 'label': f'{l["nome_cognome"]} ({l["email"]})', 'email': l['email']})
    return JsonResponse({'results': results})


# --- ajax_documenti_contratto ---
@login_required
@permesso_richiesto('documenti.vedi')
@never_cache
def ajax_documenti_contratto(request, pk):
    docs = DocumentoArchiviato.objects.filter(contratto__pk=pk).select_related('datore', 'lavoratore').order_by('-creato_il')
    data = []
    for d in docs:
        data.append({
            'pk': d.pk,
            'tipo': d.get_tipo_display(),
            'titolo': d.titolo,
            'file_name': d.file_name,
            'creato_il': d.creato_il.strftime('%d/%m/%Y %H:%M'),
            'inviato': d.inviato,
            'email_destinatario': d.email_destinatario,
        })
    return JsonResponse({'documenti': data, 'totale': len(data)})


# --- ajax_sfoglia_file ---
@login_required
@permesso_richiesto('documenti.vedi')
@require_http_methods(['POST'])
def ajax_sfoglia_file(request):
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        file_path = filedialog.askopenfilename(
            title='Seleziona il programma di posta',
            filetypes=[('Eseguibili', '*.exe'), ('Tutti i file', '*.*')]
        )
        root.destroy()
        if file_path:
            return JsonResponse({'path': file_path})
        return JsonResponse({'path': ''})
    except Exception as e:
        logger.exception("Errore in ajax_sfoglia_file")
        return JsonResponse({'error': str(e)}, status=500)


# --- ajax_template_selector ---
@login_required
@permesso_richiesto('documenti.vedi')
def ajax_template_selector(request, contratto_pk):
    contratto = get_object_or_404(ContrattoAttivo, pk=contratto_pk)
    templates = ModelloDocumentale.objects.all().order_by('tipo', 'codice')
    grouped = {}
    for t in templates:
        tipo_nome = t.get_tipo_display()
        grouped.setdefault(tipo_nome, []).append(t)
    return render(request, 'paghe/template_selector_embed.html', {
        'contratto': contratto,
        'grouped': grouped,
    })


# --- genera_pdf_da_template ---
@login_required
@permesso_richiesto('documenti.crea')
@never_cache
def genera_pdf_da_template(request, contratto_pk, modello_pk):
    import os

    contratto = get_object_or_404(ContrattoAttivo, pk=contratto_pk)
    modello = get_object_or_404(ModelloDocumentale, pk=modello_pk)

    corpo_risolto = _risolvi_variabili_testo(modello.corpo_testo, contratto)
    oggetto_risolto = _risolvi_variabili_testo(modello.titolo, contratto)

    cartella = _get_cartella_documenti(contratto)
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    safe_name = contratto.lavoratore.nome_cognome.replace(' ', '_').replace('/', '_')
    nome_file = f"{modello.tipo.lower()}_{safe_name}_{timestamp}.pdf"
    full_path = os.path.join(cartella, nome_file)

    _genera_pdf_da_testo_playwright(
        titolo=oggetto_risolto or modello.titolo,
        corpo=corpo_risolto,
        output_path=full_path,
        font_family=modello.font_family or 'Roboto',
        font_size=modello.font_size or 11,
    )
    file_size = os.path.getsize(full_path) if os.path.exists(full_path) else 0

    with open(full_path, 'rb') as f:
        pdf = f.read()

    doc = DocumentoArchiviato.objects.create(
        tipo=modello.tipo,
        titolo=oggetto_risolto or modello.titolo,
        file_path=full_path,
        file_size=file_size,
        file_name=nome_file,
        contratto=contratto,
        datore=contratto.datore,
        lavoratore=contratto.lavoratore,
        modello_documentale=modello,
        creato_da=request.user if request.user.is_authenticated else None,
    )

    # Se richiesta in formato JSON (AJAX), ritorna JSON per finestra flottante
    if request.GET.get('format') == 'json' or request.method == 'POST':
        return JsonResponse({
            'ok': True,
            'pk': doc.pk,
            'url': f'/ajax/vedi-documento/{doc.pk}/',
            'file_name': nome_file,
            'file_size': file_size,
        })

    # Altrimenti ritorna il PDF direttamente (backward compat)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nome_file}"'
    return response
