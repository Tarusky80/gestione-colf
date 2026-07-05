from paghe.views._common_imports import *
from django.contrib.auth.models import User
import json
from paghe.permessi import PERMESSI_DEFAULT, TUTTI_I_PERMESSI, ETICHETTE_PERMESSI
from paghe.models import ProfiloUtente
from paghe.decorators import permesso_richiesto

GRUPPI_PERMESSI = [
    ('Anagrafiche', 'bi-person', [p for p in TUTTI_I_PERMESSI if p.startswith('anagrafiche.')]),
    ('Contratti', 'bi-file-earmark-text', [p for p in TUTTI_I_PERMESSI if p.startswith('contratti.')]),
    ('Buste Paga', 'bi-cash-stack', [p for p in TUTTI_I_PERMESSI if p.startswith('buste.')]),
    ('Documenti', 'bi-folder', [p for p in TUTTI_I_PERMESSI if p.startswith('documenti.')]),
    ('Sistema', 'bi-gear', [p for p in TUTTI_I_PERMESSI if p.startswith(('backup', 'impostazioni', 'report', 'audit_log', 'permessi'))]),
]


@never_cache
@login_required
@permesso_richiesto('permessi')
def pannello_permessi(request):
    utenti = User.objects.filter(is_staff=True).select_related('profilo').order_by('username')
    return render(request, 'paghe/permessi_pannello.html', {
        'utenti': utenti,
        'ruoli': ProfiloUtente.RUOLI,
        'permessi_lista': TUTTI_I_PERMESSI,
        'etichette': ETICHETTE_PERMESSI,
        'permessi_default': PERMESSI_DEFAULT,
        'permessi_default_json': json.dumps(PERMESSI_DEFAULT),
        'permessi_gruppi': [({'label': g[0], 'icona': g[1]}, g[2]) for g in GRUPPI_PERMESSI],
    })


@never_cache
@login_required
@permesso_richiesto('permessi')
@require_POST
def ajax_modifica_ruolo(request):
    import json
    data = json.loads(request.body)
    user_id = data.get('user_id')
    nuovo_ruolo = data.get('ruolo')
    permessi_override = data.get('permessi_override', {})

    utente = get_object_or_404(User, pk=user_id, is_staff=True)
    profilo, _ = ProfiloUtente.objects.get_or_create(utente=utente)

    if nuovo_ruolo in dict(ProfiloUtente.RUOLI):
        profilo.ruolo = nuovo_ruolo
    profilo.permessi_json = permessi_override
    profilo.save()

    return JsonResponse({'ok': True, 'ruolo': profilo.ruolo})


@never_cache
@login_required
@permesso_richiesto('permessi')
def ajax_lista_utenti(request):
    utenti = User.objects.filter(is_staff=True).select_related('profilo').order_by('username')
    data = []
    for u in utenti:
        try:
            ruolo = u.profilo.ruolo
            permessi_json = u.profilo.permessi_json or {}
        except AttributeError:
            ruolo = 'OPERATORE'
            permessi_json = {}
        data.append({
            'id': u.pk,
            'username': u.username,
            'email': u.email,
            'ruolo': ruolo,
            'permessi_json': permessi_json,
            'ultimo_accesso': u.last_login.strftime('%d/%m/%Y %H:%M') if u.last_login else 'Mai',
        })
    return JsonResponse({'utenti': data})
