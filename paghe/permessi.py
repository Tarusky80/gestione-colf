PERMESSI_DEFAULT = {
    'ADMIN': {
        'anagrafiche.vedi': True,    'anagrafiche.crea': True,    'anagrafiche.modifica': True,    'anagrafiche.elimina': True,
        'anagrafiche.vedi_tutti': True,
        'contratti.vedi': True,      'contratti.crea': True,      'contratti.modifica': True,      'contratti.elimina': True,
        'buste.vedi': True,          'buste.calcola': True,       'buste.approva': True,           'buste.invia': True,
        'documenti.vedi': True,      'documenti.crea': True,      'documenti.elimina': True,       'documenti.invia': True,
        'backup': True,              'impostazioni': True,        'report': True,                  'audit_log': True,
        'permessi': True,
    },
    'OPERATORE': {
        'anagrafiche.vedi': True,    'anagrafiche.crea': True,    'anagrafiche.modifica': True,    'anagrafiche.elimina': False,
        'anagrafiche.vedi_tutti': False,
        'contratti.vedi': True,      'contratti.crea': True,      'contratti.modifica': True,      'contratti.elimina': False,
        'buste.vedi': True,          'buste.calcola': True,       'buste.approva': False,          'buste.invia': True,
        'documenti.vedi': True,      'documenti.crea': True,      'documenti.elimina': False,      'documenti.invia': True,
        'backup': False,             'impostazioni': False,       'report': True,                  'audit_log': False,
        'permessi': False,
    },
    'CONSULENTE': {
        'anagrafiche.vedi': True,    'anagrafiche.crea': False,   'anagrafiche.modifica': False,   'anagrafiche.elimina': False,
        'anagrafiche.vedi_tutti': False,
        'contratti.vedi': True,      'contratti.crea': False,     'contratti.modifica': False,     'contratti.elimina': False,
        'buste.vedi': True,          'buste.calcola': False,      'buste.approva': False,          'buste.invia': False,
        'documenti.vedi': True,      'documenti.crea': False,     'documenti.elimina': False,      'documenti.invia': False,
        'backup': False,             'impostazioni': False,       'report': True,                  'audit_log': False,
        'permessi': False,
    },
    'DATORE': {
        'anagrafiche.vedi': False,   'anagrafiche.crea': False,   'anagrafiche.modifica': False,   'anagrafiche.elimina': False,
        'anagrafiche.vedi_tutti': False,
        'contratti.vedi': False,     'contratti.crea': False,     'contratti.modifica': False,     'contratti.elimina': False,
        'buste.vedi': False,         'buste.calcola': False,      'buste.approva': False,          'buste.invia': False,
        'documenti.vedi': False,     'documenti.crea': False,     'documenti.elimina': False,      'documenti.invia': False,
        'backup': False,             'impostazioni': False,       'report': False,                 'audit_log': False,
        'permessi': False,
    },
}

TUTTI_I_PERMESSI = sorted(PERMESSI_DEFAULT['ADMIN'].keys())

ETICHETTE_PERMESSI = {
    'anagrafiche.vedi': 'Vedere anagrafiche',
    'anagrafiche.crea': 'Creare anagrafiche',
    'anagrafiche.modifica': 'Modificare anagrafiche',
    'anagrafiche.elimina': 'Eliminare anagrafiche',
    'anagrafiche.vedi_tutti': 'Vedere tutte le anagrafiche',
    'contratti.vedi': 'Vedere contratti',
    'contratti.crea': 'Creare contratti',
    'contratti.modifica': 'Modificare contratti',
    'contratti.elimina': 'Eliminare contratti',
    'buste.vedi': 'Vedere buste paga',
    'buste.calcola': 'Calcolare buste paga',
    'buste.approva': 'Approvare buste paga',
    'buste.invia': 'Inviare buste paga',
    'documenti.vedi': 'Vedere documenti',
    'documenti.crea': 'Creare documenti',
    'documenti.elimina': 'Eliminare documenti',
    'documenti.invia': 'Inviare documenti',
    'backup': 'Gestire backup',
    'impostazioni': 'Impostazioni',
    'report': 'Report',
    'audit_log': 'Registro audit',
    'permessi': 'Gestire permessi',
}


def permessi_per_ruolo(ruolo):
    return dict(PERMESSI_DEFAULT.get(ruolo, {}))


def permessi_effettivi(profilo):
    base = dict(permessi_per_ruolo(profilo.ruolo))
    base.update(profilo.permessi_json or {})
    return base


from paghe.models import ProfiloUtente



def ha_permesso(user, permesso):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        profilo = user.profilo
    except (AttributeError, ProfiloUtente.DoesNotExist):
        return False
    permessi = permessi_effettivi(profilo)
    return bool(permessi.get(permesso, False))


def filtro_visibilita(queryset, user, field_name='visibile_a'):
    """Filtra un queryset in base alla visibilità dell'utente.
    
    Se l'utente ha 'anagrafiche.vedi_tutti' restituisce tutto.
    Altrimenti filtra per visibile_a=user o visibile_a__isnull=True.
    """
    if not user.is_authenticated:
        return queryset.none()
    if user.is_superuser or ha_permesso(user, 'anagrafiche.vedi_tutti'):
        return queryset
    kwargs = {field_name: user}
    return queryset.filter(**kwargs)
