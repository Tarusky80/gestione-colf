"""Modulo _pagopa_manuale - generato automaticamente da views.py"""

from paghe.views._common_imports import *

from paghe.views._helpers import _get_cartella_documenti
from paghe.views._inps import _log_inps
from paghe.views._pagopa_auto import _calcola_dati_pagopa




# --- crea_pagopa_manuale ---
@login_required
@permesso_richiesto('buste.calcola')
@never_cache
def crea_pagopa_manuale(request):
    opzioni = get_opzioni()
    web_config = ServizioWebConfig.objects.first()

    contratti = ContrattoAttivo.objects.select_related(
        'datore', 'lavoratore', 'parametri_minimi', 'ente_bilaterale'
    ).order_by('datore__nome_cognome')

    contratti_data = []
    for c in contratti:
        dati = _calcola_dati_pagopa(c)
        dati['pk'] = c.pk
        dati['datore_pk'] = c.datore.pk if c.datore else None
        dati['lavoratore_pk'] = c.lavoratore.pk if c.lavoratore else None
        contratti_data.append(dati)

    contratto_pk = request.GET.get('contratto_pk')
    if contratto_pk:
        _log_inps('APERTURA_PAGOPA_MANUALE', ContrattoAttivo.objects.get(pk=contratto_pk), request)

    download_folder = os.path.join(os.path.expanduser('~'), 'Downloads')

    return render(request, 'paghe/crea_pagopa_manuale.html', {
        'opzioni': opzioni,
        'web_config': web_config,
        'contratti_data': contratti_data,
        'contratto_pk': contratto_pk,
        'download_folder': download_folder,
    })


# --- crea_pagopa_manuale_popup ---
@login_required
@permesso_richiesto('buste.calcola')
@never_cache
def crea_pagopa_manuale_popup(request, pk):
    ore_auto = request.GET.get('ore_auto', '1') != '0'
    c = get_object_or_404(ContrattoAttivo.objects.select_related(
        'datore', 'lavoratore', 'parametri_minimi', 'ente_bilaterale'), pk=pk)
    d = _calcola_dati_pagopa(c, ore_auto=ore_auto)
    d['pk'] = c.pk
    d['datore_pk'] = c.datore.pk if c.datore else None
    d['lavoratore_pk'] = c.lavoratore.pk if c.lavoratore else None
    opzioni = get_opzioni()
    return render(request, 'paghe/crea_pagopa_manuale_popup.html', {'d': d, 'opzioni': opzioni})


# --- ajax_carica_pdf_pagopa_manuale ---
@login_required
@permesso_richiesto('buste.calcola')
@require_http_methods(['POST'])
@never_cache
def ajax_carica_pdf_pagopa_manuale(request):
    from paghe.models import DocumentoArchiviato

    if 'file' not in request.FILES:
        return JsonResponse({'ok': False, 'errore': 'Nessun file caricato.'})

    file = request.FILES['file']
    if not file.name.lower().endswith('.pdf'):
        return JsonResponse({'ok': False, 'errore': 'Solo file PDF sono accettati.'})

    contratto_pk = request.POST.get('contratto_pk')
    trimestre = request.POST.get('trimestre', 'Q1')
    anno = request.POST.get('anno', str(date.today().year))

    if not contratto_pk:
        return JsonResponse({'ok': False, 'errore': 'Contratto non specificato.'})

    contratto = get_object_or_404(ContrattoAttivo, pk=contratto_pk)

    pdf_bytes = file.read()

    cartella = _get_cartella_documenti(contratto)
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')

    nome_datore = contratto.datore.nome_cognome.replace(' ', '_').upper() if contratto.datore else 'ND'
    nome_lavoratore = contratto.lavoratore.nome_cognome.replace(' ', '_').upper() if contratto.lavoratore else 'ND'

    esistenti = DocumentoArchiviato.objects.filter(
        contratto=contratto, tipo='PAGOPA_MANUALE',
        file_name__contains=f'{trimestre}{anno}'
    ).count()
    v_num = esistenti + 1

    nome_file = f'PAGOPA_MANUALE_{nome_datore}_{nome_lavoratore}_{trimestre}{anno}_v{v_num:02d}_{timestamp}.pdf'
    full_path = os.path.join(cartella, nome_file)

    with open(full_path, 'wb') as f:
        f.write(pdf_bytes)

    doc = DocumentoArchiviato.objects.create(
        tipo='PAGOPA_MANUALE',
        titolo=f"PagoPA Manuale {nome_lavoratore} – {trimestre} {anno} (v{v_num:02d})",
        file_path=full_path,
        file_size=len(pdf_bytes),
        file_name=nome_file,
        contratto=contratto,
        datore=contratto.datore,
        lavoratore=contratto.lavoratore,
        creato_da=request.user if request.user.is_authenticated else None,
    )

    _log_inps('CARICATO_PDF_PAGOPA_MANUALE', contratto, request,
              dettaglio=f"{nome_file} ({trimestre} {anno})")

    return JsonResponse({
        'ok': True,
        'pk': doc.pk,
        'file_name': nome_file,
        'file_size': len(pdf_bytes),
        'titolo': doc.titolo,
    })


# --- ajax_lista_pdf_pagopa_manuale ---
@login_required
@permesso_richiesto('buste.calcola')
@never_cache
def ajax_lista_pdf_pagopa_manuale(request):
    from paghe.models import DocumentoArchiviato

    contratto_pk = request.GET.get('contratto_pk')
    trimestre = request.GET.get('trimestre', 'Q1')
    anno = request.GET.get('anno', str(date.today().year))

    if not contratto_pk:
        return JsonResponse({'ok': False, 'errore': 'Contratto non specificato.'}, status=400)

    docs = DocumentoArchiviato.objects.filter(
        contratto_id=contratto_pk, tipo='PAGOPA_MANUALE',
        file_name__contains=f'{trimestre}{anno}'
    ).order_by('-creato_il').values('pk', 'file_name', 'file_size', 'creato_il', 'titolo')

    return JsonResponse({
        'ok': True,
        'documenti': list(docs),
    })


# --- ajax_apri_pagopa_manuale_pdf ---
@login_required
@permesso_richiesto('buste.calcola')
@xframe_options_exempt
def ajax_apri_pagopa_manuale_pdf(request):
    """Serve il PDF PagoPA manuale piu recente per contratto+trimestre+anno."""
    from paghe.models import DocumentoArchiviato
    contratto_pk = request.GET.get('contratto_pk')
    trimestre = request.GET.get('trimestre', 'Q1')
    anno = request.GET.get('anno', str(date.today().year))
    if not contratto_pk:
        return HttpResponse('Contratto non specificato.', status=400)
    doc = DocumentoArchiviato.objects.filter(
        contratto_id=contratto_pk, tipo='PAGOPA_MANUALE',
        file_name__contains=f'{trimestre}{anno}'
    ).order_by('-creato_il').first()
    if not doc:
        return HttpResponse('Nessun PDF PagoPA manuale trovato per questo trimestre.', status=404)
    if not os.path.exists(doc.file_path):
        return HttpResponse('File PDF non trovato sul disco.', status=404)
    with open(doc.file_path, 'rb') as f:
        pdf_data = f.read()
    response = HttpResponse(pdf_data, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{doc.file_name}"'
    return response
