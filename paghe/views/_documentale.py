from paghe.views._common_imports import *
from paghe.models import ModelloDocumentale, ContrattoLavoro, DocumentoArchiviato
from paghe.views._helpers import _get_cartella_documenti, _genera_pdf_da_testo_playwright
from paghe.views._testi import _risolvi_variabili_testo, _risolvi_globali
from paghe.views._variabili import VARIABILI_DISPONIBILI


TIPO_LABEL = dict(ModelloDocumentale.TIPO_SCELTE)
TIPO_ICON = {
    'CONTRATTO': 'file-earmark-text',
    'CUD': 'file-earmark-check',
    'CARTELLINA': 'folder',
    'RIEPILOGO_RAPPORTO': 'journal-text',
    'LETTERA_ASSUNZIONE': 'envelope',
    'LETTERA_LICENZIAMENTO': 'envelope',
    'LETTERA_DIMISSIONI': 'envelope',
    'LETTERA_LIBERA': 'envelope',
    'DEROGA_TFR': 'file-earmark',
    'RICEVUTA': 'receipt',
    'RICHIESTA_CUD': 'file-earmark',
    'PDF_INIZIO': 'file-earmark',
    'PDF_FINE': 'file-earmark',
    'PDF_RISCONTRO': 'file-earmark',
    'LISTA_STAMPA': 'list-ul',
    'BUSTA_PAGA': 'cash-stack',
    'MAIL': 'envelope-at',
    'TESTO_PROGRAMMA': 'gear',
    'TOP_DOCUMENTO': 'file-earmark-richtext',
    'FOOTER_DOCUMENTO': 'file-earmark-richtext',
}
TIPO_COLORE = {
    'CONTRATTO': '#10b981',
    'CUD': '#f59e0b',
    'CARTELLINA': '#f59e0b',
    'RIEPILOGO_RAPPORTO': '#f59e0b',
    'LETTERA_ASSUNZIONE': '#8b5cf6',
    'LETTERA_LICENZIAMENTO': '#8b5cf6',
    'LETTERA_DIMISSIONI': '#8b5cf6',
    'LETTERA_LIBERA': '#8b5cf6',
    'DEROGA_TFR': '#8b5cf6',
    'RICEVUTA': '#f59e0b',
    'RICHIESTA_CUD': '#f59e0b',
    'PDF_INIZIO': '#f59e0b',
    'PDF_FINE': '#f59e0b',
    'PDF_RISCONTRO': '#f59e0b',
    'LISTA_STAMPA': '#06b6d4',
    'BUSTA_PAGA': '#5E6AD2',
    'MAIL': '#5E6AD2',
    'TESTO_PROGRAMMA': '#8A8F98',
    'TOP_DOCUMENTO': '#8A8F98',
    'FOOTER_DOCUMENTO': '#8A8F98',
}


@login_required
@permesso_richiesto('documenti.vedi')
@never_cache
def documentale_root(request):
    """Dashboard root /documentale/ — stat cards per tipo + pill navigation."""
    tipi_stats = []
    for k, v in ModelloDocumentale.TIPO_SCELTE:
        qs = ModelloDocumentale.objects.filter(tipo=k)
        last = qs.order_by('-modificato_il').first()
        first = qs.order_by('creato_il').first()
        tipi_stats.append({
            'tipo': k,
            'label': v,
            'icon': TIPO_ICON.get(k, 'file-earmark'),
            'count': qs.count(),
            'last_mod': last.modificato_il if last else None,
            'first_cre': first.creato_il if first else None,
            'colore': TIPO_COLORE.get(k, '#5E6AD2'),
        })

    tipi_docs = []
    for k, v in ModelloDocumentale.TIPO_SCELTE:
        tipi_docs.append({'tipo': k, 'label': v, 'icon': TIPO_ICON.get(k, 'file-earmark'), 'count': ModelloDocumentale.objects.filter(tipo=k).count(), 'colore': TIPO_COLORE.get(k, '#5E6AD2')})

    opzioni = get_opzioni()
    return render(request, 'paghe/documentale_list.html', {
        'opzioni': opzioni,
        'tipi_stats': tipi_stats,
        'tipo_corrente': None,
        'tipo_label': '',
        'tipo_icon': 'file-earmark-code',
        'tipi_docs': tipi_docs,
        'modelli': [],
    })


@login_required
@permesso_richiesto('documenti.vedi')
@never_cache
def documentale_list(request, tipo):
    tipo_upper = tipo.upper()
    tipi_docs = []
    for k, v in ModelloDocumentale.TIPO_SCELTE:
        tipi_docs.append({'tipo': k, 'label': v, 'icon': TIPO_ICON.get(k, 'file-earmark'), 'count': ModelloDocumentale.objects.filter(tipo=k).count()})

    modelli = ModelloDocumentale.objects.filter(tipo=tipo_upper).order_by('codice')
    opzioni = get_opzioni()
    return render(request, 'paghe/documentale_list.html', {
        'opzioni': opzioni,
        'modelli': modelli,
        'tipo_corrente': tipo_upper,
        'tipo_label': TIPO_LABEL.get(tipo_upper, tipo),
        'tipo_icon': TIPO_ICON.get(tipo_upper, 'file-earmark'),
        'tipo_colore': TIPO_COLORE.get(tipo_upper, '#5E6AD2'),
        'tipi_docs': tipi_docs,
    })


@login_required
@permesso_richiesto('documenti.crea')
@never_cache
def documentale_edit(request, tipo, pk=None):
    tipo_upper = tipo.upper()
    opzioni = get_opzioni()
    modello = None
    if pk:
        modello = get_object_or_404(ModelloDocumentale, pk=pk)

    if request.method == 'POST':
        data = json.loads(request.body)
        if modello:
            modello.titolo = data.get('titolo', '')
            modello.corpo_testo = data.get('corpo_testo', '')
            modello.note_interne = data.get('note_interne', '')
            modello.font_family = data.get('font_family', 'Roboto')
            modello.font_size = int(data.get('font_size', 11))
            modello.versione += 1
            modello.save()
            return JsonResponse({'ok': True, 'pk': modello.pk})
        else:
            codice = data.get('codice', '').strip().upper().replace(' ', '_') or f"{tipo_upper}_{ModelloDocumentale.objects.filter(tipo=tipo_upper).count() + 1}"
            modello = ModelloDocumentale.objects.create(
                tipo=tipo_upper,
                codice=codice,
                titolo=data.get('titolo', ''),
                corpo_testo=data.get('corpo_testo', ''),
                note_interne=data.get('note_interne', ''),
                font_family=data.get('font_family', 'Roboto'),
                font_size=int(data.get('font_size', 11)),
            )
            return JsonResponse({'ok': True, 'pk': modello.pk})

    contratti = ContrattoLavoro.objects.select_related('datore', 'lavoratore').prefetch_related('progetto__tipo', 'progetto__beneficiario').order_by('datore__cognome', 'lavoratore__cognome')[:20]
    return render(request, 'paghe/documentale_edit.html', {
        'opzioni': opzioni,
        'modello': modello,
        'tipo_corrente': tipo_upper,
        'tipo_label': TIPO_LABEL.get(tipo_upper, tipo),
        'tipo_colore': TIPO_COLORE.get(tipo_upper, '#5E6AD2'),
        'is_new': pk is None,
        'contratti_preview': contratti,
        'variabili': VARIABILI_DISPONIBILI,
    })


@login_required
@permesso_richiesto('documenti.vedi')
@require_http_methods(['POST'])
def ajax_documentale_preview(request):
    data = json.loads(request.body)
    corpo = data.get('corpo_testo', '')
    contratto_pk = data.get('contratto_pk')
    contratto = None
    if contratto_pk:
        contratto = get_object_or_404(ContrattoLavoro, pk=contratto_pk)
    risolto = corpo
    if contratto:
        risolto = _risolvi_variabili_testo(risolto, contratto, user=request.user)
    else:
        risolto = _risolvi_globali(risolto)
    return JsonResponse({'corpo': risolto})


@login_required
@permesso_richiesto('documenti.vedi')
@require_http_methods(['POST'])
def ajax_documentale_preview_pdf(request):
    data = json.loads(request.body)
    data.get('tipo', 'ALTRO')
    titolo = data.get('titolo', '')
    corpo = data.get('corpo_testo', '')
    font_family = data.get('font_family', 'Roboto')
    font_size = int(data.get('font_size', 11))
    contratto_pk = data.get('contratto_pk')
    contratto = None
    if contratto_pk:
        contratto = get_object_or_404(ContrattoLavoro, pk=contratto_pk)
    risolto = corpo
    if contratto:
        risolto = _risolvi_variabili_testo(risolto, contratto, user=request.user)
    else:
        risolto = _risolvi_globali(risolto)
    import tempfile
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    tmp.close()
    try:
        _genera_pdf_da_testo_playwright(titolo, risolto, tmp.name, font_family, font_size)
        with open(tmp.name, 'rb') as f:
            pdf_bytes = f.read()
    finally:
        os.unlink(tmp.name)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="anteprima.pdf"'
    return response


@login_required
@permesso_richiesto('documenti.crea')
@require_http_methods(['POST'])
def ajax_salva_pdf_anteprima(request):
    """Salva il PDF dell'anteprima corrente in DocumentoArchiviato.
    Riceve gli stessi parametri di ajax_documentale_preview_pdf + mode='save'.
    """
    data = json.loads(request.body)
    tipo = data.get('tipo', 'ALTRO')
    titolo = data.get('titolo', '')
    corpo = data.get('corpo_testo', '')
    font_family = data.get('font_family', 'Roboto')
    font_size = int(data.get('font_size', 11))
    contratto_pk = data.get('contratto_pk')
    contratto = None
    if contratto_pk:
        contratto = get_object_or_404(ContrattoLavoro, pk=contratto_pk)
    risolto = corpo
    if contratto:
        risolto = _risolvi_variabili_testo(risolto, contratto)
    else:
        risolto = _risolvi_globali(risolto)

    cartella = _get_cartella_documenti(contratto)
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{tipo.lower()}_{timestamp}.pdf'
    full_path = os.path.join(cartella, filename)

    _genera_pdf_da_testo_playwright(titolo, risolto, full_path, font_family, font_size)

    file_size = os.path.getsize(full_path) if os.path.exists(full_path) else 0
    doc = DocumentoArchiviato.objects.create(
        tipo=tipo[:50],
        titolo=titolo or f'Documento {timestamp}',
        file_path=full_path,
        file_size=file_size,
        file_name=filename,
        contratto=contratto,
        datore=contratto.datore if contratto else None,
        lavoratore=contratto.lavoratore if contratto else None,
        creato_da=request.user if request.user.is_authenticated else None,
    )
    return JsonResponse({
        'ok': True,
        'pk': doc.pk,
        'url': f'/ajax/vedi-documento/{doc.pk}/',
        'file_name': filename,
        'file_size': file_size,
    })


@login_required
@permesso_richiesto('documenti.elimina')
@require_http_methods(['POST'])
def ajax_documentale_elimina(request, pk):
    modello = get_object_or_404(ModelloDocumentale, pk=pk)
    modello.delete()
    return JsonResponse({'ok': True})


@login_required
@permesso_richiesto('documenti.crea')
@require_http_methods(['POST'])
def ajax_documentale_duplica(request, pk):
    originale = get_object_or_404(ModelloDocumentale, pk=pk)
    copia = ModelloDocumentale.objects.create(
        tipo=originale.tipo,
        codice=originale.codice + '_COPIA',
        titolo=originale.titolo + ' (copia)',
        corpo_testo=originale.corpo_testo,
        note_interne=originale.note_interne,
        font_family=originale.font_family,
        font_size=originale.font_size,
    )
    return JsonResponse({'ok': True, 'pk': copia.pk})


@login_required
@permesso_richiesto('documenti.crea')
@never_cache
def genera_pdf_documentale(request, contratto_pk, modello_pk):
    contratto = get_object_or_404(ContrattoLavoro, pk=contratto_pk)
    modello = get_object_or_404(ModelloDocumentale, pk=modello_pk)
    cartella = _get_cartella_documenti(contratto)
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{modello.tipo.lower()}_{contratto_pk}_{timestamp}.pdf'
    full_path = os.path.join(cartella, filename)
    corpo_risolto = _risolvi_variabili_testo(modello.corpo_testo, contratto, user=request.user)
    _genera_pdf_da_testo_playwright(modello.titolo or modello.codice, corpo_risolto, full_path, modello.font_family or 'Arial', modello.font_size or 11)
    file_size = os.path.getsize(full_path) if os.path.exists(full_path) else 0
    DocumentoArchiviato.objects.create(
        tipo=modello.tipo,
        titolo=modello.titolo or modello.codice,
        file_path=full_path,
        file_size=file_size,
        file_name=filename,
        contratto=contratto,
        datore=contratto.datore,
        lavoratore=contratto.lavoratore,
        modello_documentale=modello,
        creato_da=request.user if request.user.is_authenticated else None,
    )
    with open(full_path, 'rb') as f:
        pdf_bytes = f.read()
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response
