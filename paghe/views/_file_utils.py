"""Utility filesystem: sanitizzazione nomi, cartelle documenti (estratte da _helpers.py)."""
from paghe.views._common_imports import *

logger = logging.getLogger(__name__)


def _sanitizza_nome(nome, maxlen=40):
    s = re.sub(r'[^\w\s]', '', nome or '')
    s = s.strip().replace(' ', '')
    return s[:maxlen]


def _nome_cartella_contratto(contratto):
    if not contratto:
        return 'SENZA_CONTRATTO'
    datore = _sanitizza_nome(contratto.datore.nome_cognome) if contratto.datore else 'SENZA_DATORE'
    lavoratore = _sanitizza_nome(contratto.lavoratore.nome_cognome) if contratto.lavoratore else 'SENZA_LAVORATORE'
    primo_progetto = contratto.progetto.first() if hasattr(contratto, 'progetto') else None
    beneficiario = _sanitizza_nome(primo_progetto.beneficiario.nome_cognome) if primo_progetto and primo_progetto.beneficiario else 'SENZA_BENEF'
    tipo_prog = _sanitizza_nome(primo_progetto.tipo.nome) if primo_progetto and primo_progetto.tipo else 'SENZA_PROG'
    nome = f"CONTRATTO_{contratto.pk}_{datore}_{lavoratore}_{beneficiario}_{tipo_prog}"
    return nome[:120]


def _get_cartella_documenti(contratto=None):
    opzioni = get_opzioni()
    if opzioni and opzioni.cartella_documenti:
        base = opzioni.cartella_documenti
    else:
        base = os.path.join(settings.MEDIA_ROOT, 'documenti')
    sottocartella = _nome_cartella_contratto(contratto)
    path = os.path.join(base, sottocartella)
    if not os.path.exists(path):
        os.makedirs(path)
    return path
