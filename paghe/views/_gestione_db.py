"""View per la gestione dei database (Sistema → Database)."""
import traceback
from io import StringIO

from paghe.views._common_imports import *

logger = logging.getLogger(__name__)


@login_required
@permesso_richiesto('backup')
def gestione_db_page(request):
    db_profile = getattr(request, 'db_profile', 'default')
    profili = []
    for key, val in settings.DB_PROFILES.items():
        name = val['NAME']
        exists = os.path.exists(name)
        size = os.path.getsize(name) if exists else 0
        profili.append({
            'key': key,
            'label': val['label'],
            'path': str(name),
            'exists': exists,
            'size': size,
            'active': key == db_profile,
            'is_default': key == 'default',
        })
    return render(request, 'paghe/gestione_db.html', {
        'profili': profili,
        'db_profile': db_profile,
    })


@login_required
@permesso_richiesto('backup')
@require_POST
def ajax_attiva_db(request):
    import json
    data = json.loads(request.body)
    profile = data.get('profile', 'default')
    if profile not in settings.DB_PROFILES:
        return JsonResponse({'success': False, 'error': 'Profilo non valido.'})
    response = JsonResponse({'success': True, 'profile': profile})
    max_age = settings.DB_PROFILE_COOKIE_AGE
    response.set_signed_cookie(
        settings.DB_PROFILE_COOKIE, profile,
        max_age=max_age, httponly=True, samesite='Lax',
        salt='db_switch',
    )
    return response


@login_required
@permesso_richiesto('backup')
def attiva_db_redirect(request, profile):
    """Attiva un database e reindirizza (GET). Il cookie viene settato
    lato server, nessuna race condition client-side."""
    if profile not in settings.DB_PROFILES:
        return redirect('gestione_db_page')
    response = redirect('gestione_db_page')
    max_age = settings.DB_PROFILE_COOKIE_AGE
    response.set_signed_cookie(
        settings.DB_PROFILE_COOKIE, profile,
        max_age=max_age, httponly=True, samesite='Lax',
        salt='db_switch',
    )
    return response


@login_required
@permesso_richiesto('backup')
@require_POST
def ajax_crea_db(request):
    import json
    data = json.loads(request.body)
    profile = data.get('profile', '')
    recreate = data.get('recreate', False)

    if not profile or profile not in settings.DB_PROFILES:
        return JsonResponse({'success': False, 'error': 'Profilo non valido.'})
    if profile == 'default':
        return JsonResponse({'success': False, 'error': 'Impossibile popolare il database principale.'})

    try:
        out = StringIO()
        call_command('popola_db_test', profile=profile, recreate=recreate, stdout=out)
        return JsonResponse({'success': True, 'output': out.getvalue()})
    except Exception as e:
        logger.exception('Errore creazione database %s', profile)
        return JsonResponse({'success': False, 'error': str(e), 'traceback': traceback.format_exc()})


@login_required
@permesso_richiesto('backup')
@require_POST
def ajax_elimina_db(request):
    import json
    data = json.loads(request.body)
    profile = data.get('profile', '')

    if not profile or profile not in settings.DB_PROFILES:
        return JsonResponse({'success': False, 'error': 'Profilo non valido.'})
    if profile == 'default':
        return JsonResponse({'success': False, 'error': 'Impossibile eliminare il database principale.'})

    target = settings.DB_PROFILES[profile]['NAME']
    if os.path.exists(target):
        os.remove(target)

    return JsonResponse({'success': True})
