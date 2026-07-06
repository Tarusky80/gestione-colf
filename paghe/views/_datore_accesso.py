from paghe.views._common_imports import *
from paghe.models import DatoreLavoro, DocumentoArchiviato, AccessoDatore
from paghe.decorators import permesso_richiesto


# --- AJAX admin: abilita/modifica/disabilita accesso datore ---
@login_required
@permesso_richiesto('anagrafiche.modifica')
@require_http_methods(['POST'])
def ajax_datore_abilita_accesso(request):
    import json
    from django.contrib.auth.hashers import make_password
    data = json.loads(request.body)
    cf = data.get('codice_fiscale', '').upper().strip()
    password = data.get('password', '')
    abilita = data.get('abilita', True)
    if not cf:
        return JsonResponse({'success': False, 'error': 'CF richiesto.'})
    try:
        datore = DatoreLavoro.objects.get(codice_fiscale=cf)
    except DatoreLavoro.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Datore non trovato.'})
    if abilita:
        if not password:
            return JsonResponse({'success': False, 'error': 'Password richiesta.'})
        if len(password) < 4:
            return JsonResponse({'success': False, 'error': 'Password troppo corta (min 4 caratteri).'})
        AccessoDatore.objects.update_or_create(
            datore=datore,
            defaults={'password': make_password(password), 'accesso_abilitato': True}
        )
        msg = 'Accesso abilitato con successo.'
    else:
        AccessoDatore.objects.filter(datore=datore).update(accesso_abilitato=False)
        msg = 'Accesso disabilitato.'
    return JsonResponse({'success': True, 'message': msg})


# --- AJAX admin: toggle visibilit� documento per datore ---
@login_required
@require_http_methods(['POST'])
def ajax_documento_toggle_visibilita_datore(request):
    import json
    data = json.loads(request.body)
    pk = data.get('documento_pk')
    visibile = data.get('visibile', False)
    if not pk:
        return JsonResponse({'success': False, 'error': 'Documento non specificato.'})
    doc = get_object_or_404(DocumentoArchiviato, pk=pk)
    doc.visibile_al_datore = bool(visibile)
    doc.save(update_fields=['visibile_al_datore'])
    return JsonResponse({'success': True, 'visibile': doc.visibile_al_datore})


# --- AJAX admin: ottieni stato accesso datore ---
@login_required
def ajax_datore_stato_accesso(request, cf):
    try:
        ad = AccessoDatore.objects.select_related('datore').get(datore__codice_fiscale=cf.upper().strip())
        return JsonResponse({
            'success': True,
            'abilitato': ad.accesso_abilitato,
            'ultimo_accesso': ad.ultimo_accesso.strftime('%d/%m/%Y %H:%M') if ad.ultimo_accesso else None,
            'nome': ad.datore.nome_cognome,
        })
    except AccessoDatore.DoesNotExist:
        return JsonResponse({'success': True, 'abilitato': False, 'ultimo_accesso': None})


def portal_spa(request):
    """Employer Portal SPA (Vue 3 built via Vite)."""
    from django.conf import settings
    dist_index = settings.BASE_DIR / 'frontend' / 'dist' / 'index.html'
    if dist_index.exists():
        with open(dist_index, encoding='utf-8') as f:
            return HttpResponse(f.read())
    opzioni = get_opzioni()
    return render(request, 'paghe/portal_spa.html', {'opzioni': opzioni})
