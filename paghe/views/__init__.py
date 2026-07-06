"""Views package - lazy-loading modules via __getattr__"""
import importlib

_modules = [
    '_constants', '_helpers', '_calcoli_core', '_buste_pdf', '_dashboard', '_anagrafiche',
    '_contratti_cessati', '_backup', '_tabelle', '_testi', '_buste_crud',
    '_buste_download', '_buste_massivo', '_calcoli_views', '_contratto_pdf',
    '_tfr_cessazione', '_tfr_rivalutazione', '_documenti', '_liste', '_inps', '_pagopa_manuale',
    '_pagopa_auto', '_stampe_invii', '_cu', '_scorciatoie', '_datore_accesso',
    '_richieste', '_comparatore', '_agenda', '_documentale',     '_checklist', '_audit', '_uniemens', '_report', '_excel_export',
    '_gestione_db', '_gestione_pdf', '_anagrafiche_utils', '_file_utils',
    '_anagrafiche_ajax', '_variabili', '_invia_email',
    '_aggiornamenti',
    '_ccnl',
    '_guide',
    '_inquadramento',
    '_tabelle_retributive',
    '_massive',
    '_permessi',
    '_lul',
    '_contributi_ccnl',
]

_cache = {}

def __getattr__(name):
    for mod_name in _modules:
        if mod_name not in _cache:
            _cache[mod_name] = importlib.import_module(f'.{mod_name}', __package__)
        if hasattr(_cache[mod_name], name):
            return getattr(_cache[mod_name], name)
    raise AttributeError(f"module 'paghe.views' has no attribute '{name}'")
