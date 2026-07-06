"""Modulo _inps - generato automaticamente da views.py"""

from paghe.views._common_imports import *

from paghe.views._helpers import _build_contratto_data, _calcola_preavviso




# --- iscrizione_inps ---
@login_required
@permesso_richiesto('buste.calcola')
@never_cache
def iscrizione_inps(request):
    opzioni = get_opzioni()
    web_config = ServizioWebConfig.objects.first()

    contratti = ContrattoAttivo.objects.select_related(
        'datore', 'lavoratore', 'parametri_minimi'
    ).prefetch_related('progetto__tipo', 'progetto__beneficiario').order_by('datore__nome_cognome')

    contratti_data = [_build_contratto_data(c) for c in contratti]
    contratto_pk = request.GET.get('contratto_pk')
    if contratto_pk:
        _log_inps('APERTURA_ASSUNZIONE', ContrattoAttivo.objects.get(pk=contratto_pk), request)

    return render(request, 'paghe/iscrizione_inps.html', {
        'opzioni': opzioni,
        'web_config': web_config,
        'contratti_data': contratti_data,
        'contratto_pk': contratto_pk,
    })


# --- iscrizione_inps_popup ---
@login_required
@permesso_richiesto('buste.calcola')
@never_cache
def iscrizione_inps_popup(request, pk):
    c = get_object_or_404(ContrattoAttivo.objects.select_related(
        'datore', 'lavoratore', 'parametri_minimi'), pk=pk)
    d = _build_contratto_data(c)
    opzioni = get_opzioni()
    return render(request, 'paghe/iscrizione_inps_popup.html', {'d': d, 'opzioni': opzioni})


# --- ajax_salva_codice_rapporto_inps ---
@login_required
@permesso_richiesto('contratti.modifica')
@require_http_methods(['POST'])
@never_cache
def ajax_salva_codice_rapporto_inps(request):
    import json
    data = json.loads(request.body)
    pk = data.get('pk')
    codice = data.get('codice', '').strip()
    if not pk:
        return JsonResponse({'ok': False, 'errore': 'pk mancante'})
    try:
        c = ContrattoAttivo.objects.get(pk=pk)
    except ContrattoAttivo.DoesNotExist:
        return JsonResponse({'ok': False, 'errore': 'Contratto non trovato'})
    c.codice_rapporto_inps = codice
    c.save(update_fields=['codice_rapporto_inps'])
    _log_inps('SALVATAGGIO_CODICE', c, request, dettaglio=codice)
    return JsonResponse({'ok': True, 'codice': codice})


# --- cessazione_inps ---
@login_required
@permesso_richiesto('buste.calcola')
@never_cache
def cessazione_inps(request):
    opzioni = get_opzioni()
    web_config = ServizioWebConfig.objects.first()

    contratti = ContrattoAttivo.objects.select_related(
        'datore', 'lavoratore', 'parametri_minimi'
    ).prefetch_related('progetto__tipo', 'progetto__beneficiario').order_by('datore__nome_cognome')

    contratti_data = [_build_contratto_data(c) for c in contratti]
    contratto_pk = request.GET.get('contratto_pk')
    if contratto_pk:
        _log_inps('APERTURA_CESSAZIONE', ContrattoAttivo.objects.get(pk=contratto_pk), request)

    return render(request, 'paghe/cessazione_inps.html', {
        'opzioni': opzioni,
        'web_config': web_config,
        'contratti_data': contratti_data,
        'contratto_pk': contratto_pk,
    })


# --- cessazione_inps_popup ---
@login_required
@permesso_richiesto('buste.calcola')
@never_cache
def cessazione_inps_popup(request, pk):
    c = get_object_or_404(ContrattoAttivo.objects.select_related(
        'datore', 'lavoratore', 'parametri_minimi'), pk=pk)
    d = _build_contratto_data(c)
    opzioni = get_opzioni()
    return render(request, 'paghe/cessazione_inps_popup.html', {'d': d, 'opzioni': opzioni})


# --- ajax_salva_data_fine_cessazione ---
@login_required
@permesso_richiesto('contratti.modifica')
@require_http_methods(['POST'])
@never_cache
def ajax_salva_data_fine_cessazione(request):
    import json
    data = json.loads(request.body)
    pk = data.get('pk')
    data_fine_str = data.get('data_fine', '').strip()
    causale = data.get('causale_cessazione', '').strip()
    if not pk:
        return JsonResponse({'ok': False, 'errore': 'pk mancante'})
    try:
        c = ContrattoAttivo.objects.get(pk=pk)
    except ContrattoAttivo.DoesNotExist:
        return JsonResponse({'ok': False, 'errore': 'Contratto non trovato'})

    if data_fine_str:
        try:
            c.data_fine = date.fromisoformat(data_fine_str)
        except ValueError:
            return JsonResponse({'ok': False, 'errore': 'Formato data non valido'})
    else:
        c.data_fine = None

    c.causale_cessazione = causale
    c.save(update_fields=['data_fine', 'causale_cessazione'])

    # Ricalcola preavviso
    preavviso = _calcola_preavviso(c, c.data_fine, causale)
    _log_inps('SALVATAGGIO_DATA_FINE', c, request, dettaglio=f'Data fine: {data_fine_str}, Causale: {causale}')

    return JsonResponse({
        'ok': True,
        'data_fine': data_fine_str,
        'causale_cessazione': causale,
        'preavviso': preavviso,
    })


# --- log_inps_list ---
@login_required
@permesso_richiesto('audit_log')
@never_cache
def log_inps_list(request):
    from paghe.models import LogOperazioneINPS
    from django.core.paginator import Paginator

    opzioni = get_opzioni()
    qs = LogOperazioneINPS.objects.select_related('contratto', 'utente').all()

    contratto_pk = request.GET.get('contratto_pk')
    tipo_op = request.GET.get('tipo_op')
    da_data = request.GET.get('da_data')
    a_data = request.GET.get('a_data')

    if contratto_pk:
        qs = qs.filter(contratto_id=contratto_pk)
    if tipo_op:
        qs = qs.filter(tipo_op=tipo_op)
    if da_data:
        qs = qs.filter(data_creazione__gte=da_data)
    if a_data:
        qs = qs.filter(data_creazione__date__lte=a_data)

    qs = qs.order_by('-pk')
    paginator = Paginator(qs, 100)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    contratti = ContrattoAttivo.objects.select_related('datore', 'lavoratore').prefetch_related('progetto__tipo', 'progetto__beneficiario').order_by('datore__nome_cognome')

    return render(request, 'paghe/log_inps_list.html', {
        'opzioni': opzioni,
        'logs': page_obj.object_list,
        'page_obj': page_obj,
        'contratti': contratti,
        'tipi': LogOperazioneINPS.TIPI,
        'filtro_contratto_pk': contratto_pk,
        'filtro_tipo_op': tipo_op,
        'filtro_da_data': da_data,
        'filtro_a_data': a_data,
    })


# --- _log_inps ---


# =============================================================================
# LOG OPERAZIONI INPS
# =============================================================================

def _log_inps(tipo, contratto, request, dettaglio=''):
    from paghe.models import LogOperazioneINPS
    LogOperazioneINPS.objects.create(
        contratto=contratto,
        tipo_op=tipo,
        dettaglio=dettaglio,
        utente=request.user if request.user.is_authenticated else None,
    )


# --- ajax_elimina_log_inps ---
@login_required
@permesso_richiesto('buste.calcola')
@require_http_methods(['POST'])
def ajax_elimina_log_inps(request):
    import json
    data = json.loads(request.body)
    pk = data.get('pk')
    if not pk:
        return JsonResponse({'success': False, 'error': 'pk mancante'})
    from paghe.models import LogOperazioneINPS
    try:
        log = LogOperazioneINPS.objects.get(pk=pk)
        log.delete()
        return JsonResponse({'success': True})
    except LogOperazioneINPS.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Log non trovato'})
