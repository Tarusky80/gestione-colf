# file: paghe/context_processors.py
from django.urls import reverse
from django.contrib.auth.models import User
from .models import ContrattoAttivo, DatoreLavoro, Lavoratore, Beneficiario, ScorciatoiaTastiera, RichiestaModificaDatore, ProfiloUtente
from paghe.views._common_imports import get_opzioni
from paghe.permessi import permessi_effettivi
import logging
logger = logging.getLogger(__name__)

def dashboard_stats(request):
    ctx = {}
    if request.path.startswith('/admin/'):
        ctx.update({
            'total_attivi': ContrattoAttivo.objects.count(),
            'datori_count': DatoreLavoro.objects.count(),
            'lavoratori_count': Lavoratore.objects.count(),
            'beneficiari_count': Beneficiario.objects.count(),
            'ultimi_contratti': ContrattoAttivo.objects.select_related('datore', 'lavoratore').order_by('-data_assunzione')[:8],
        })
    ctx['richieste_pendenti'] = RichiestaModificaDatore.objects.filter(stato='INVIATA', eliminata=False).count()
    return ctx

def global_opzioni(request):
    ctx = {'opzioni': get_opzioni()}
    ctx['db_profile'] = getattr(request, 'db_profile', 'default')
    ctx['ruolo_utente'] = None
    ctx['permessi_utente'] = {}
    profilo = None
    if request.user.is_authenticated:
        try:
            profilo = ProfiloUtente.objects.get(utente=request.user)
        except ProfiloUtente.DoesNotExist:
            if request.user.is_superuser:
                profilo, _ = ProfiloUtente.objects.get_or_create(utente=request.user, defaults={'ruolo': 'ADMIN'})
            elif request.user.is_staff:
                profilo, _ = ProfiloUtente.objects.get_or_create(utente=request.user, defaults={'ruolo': 'OPERATORE'})
        if profilo is not None:
            ctx['ruolo_utente'] = profilo.ruolo
            ctx['permessi_utente'] = {
                k.replace('.', '_'): v for k, v in permessi_effettivi(profilo).items()
            }
    return ctx


def shortcut_keys(request):
    attive = ScorciatoiaTastiera.objects.filter(attiva=True).exclude(tasto__isnull=True).exclude(tasto__exact='')
    shortcut_map = {}
    shortcut_badges = {}
    for s in attive:
        key = s.tasto.upper()
        shortcut_map[key] = s.menu_id
        shortcut_badges[s.menu_id] = key
    shortcut_badges['nav_permessi'] = User.objects.filter(is_staff=True).count()
    return {
        'shortcut_map': shortcut_map,
        'shortcut_badges': shortcut_badges,
        'shortcut_map_json': __import__('json').dumps(shortcut_map),
    }


def js_urls(request):
    """Espone URL nominate come oggetto JSON per JavaScript."""
    urls = {}
    nome_viste = [
        'dashboard', 'calcoli_list', 'buste_archivio', 'datori_list',
        'lavoratori_list', 'beneficiari_list', 'contratti_list',
        'documenti_list', 'stampe_invii', 'liste_list',
        'impostazioni_page', 'backup_page',
    ]
    for nome in nome_viste:
        try:
            urls[nome] = reverse(nome)
        except Exception:
            logger.exception("URL non trovata: %s", nome)
            urls[nome] = None
    return {'js_urls': __import__('json').dumps(urls)}
