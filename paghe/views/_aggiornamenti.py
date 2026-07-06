"""View AJAX per gestione aggiornamenti pacchetti Python."""
import sys
import subprocess
import json
from pathlib import Path

from paghe.views._common_imports import *

logger = logging.getLogger('paghe')

# Lista dei pacchetti da tracciare (ordinati come in requirements.txt)
PACCHETTI = [
    'Django', 'django-import-export', 'reportlab', 'xhtml2pdf',
    'openpyxl', 'selenium', 'playwright', 'requests', 'Pillow',
    'pypdf', 'APScheduler', 'chromedriver-autoinstaller', 'bleach',
    'cryptography',
]
NORMALIZZA = {p.lower(): p for p in PACCHETTI}
ESCLUDI_DA_AGG = {'reportlab'}  # mantieni versioni bloccate per compatibilità


def _versioni_installate():
    """Restituisce dict {nome_normalizzato: versione} via importlib.metadata."""
    from importlib.metadata import version as _v
    risultato = {}
    for p in PACCHETTI:
        try:
            risultato[p.lower()] = _v(p)
        except Exception:
            risultato[p.lower()] = '—'
    return risultato


@login_required
@permesso_richiesto('impostazioni')
def ajax_verifica_aggiornamenti(request):
    """Confronta versioni installate con ultime disponibili su PyPI.

    Restituisce JSON:
      {pacchetto: {stato, installata, disponibile}}
    dove stato = 'ok' | 'update' | 'errore'
    """
    corrente = _versioni_installate()

    import requests as req
    disponibili = {}
    for p_norm in NORMALIZZA:
        nome_pip = NORMALIZZA[p_norm]
        try:
            resp = req.get(f'https://pypi.org/pypi/{nome_pip}/json',
                           timeout=5, headers={'Accept': 'application/json'})
            if resp.status_code == 200:
                info = resp.json().get('info', {})
                disponibili[p_norm] = info.get('version', '—')
            else:
                disponibili[p_norm] = '?'
        except Exception:
            disponibili[p_norm] = '?'

    risultato = {}
    for p_norm, nome_bello in NORMALIZZA.items():
        installed = corrente.get(p_norm, '—')
        latest = disponibili.get(p_norm, '?')
        if latest in ('?', '—'):
            stato = 'errore'
        elif installed == latest:
            stato = 'ok'
        else:
            try:
                from packaging.version import Version
                if Version(installed) < Version(latest):
                    stato = 'update'
                else:
                    stato = 'ok'
            except Exception:
                stato = 'update' if installed != latest else 'ok'

        risultato[nome_bello] = {
            'stato': stato,
            'installata': installed,
            'disponibile': latest,
        }

    return JsonResponse({'pacchetti': risultato})


@login_required
@permesso_richiesto('impostazioni')
@require_POST
def ajax_aggiorna_pacchetto(request):
    """Aggiorna un singolo pacchetto via pip install --upgrade."""
    try:
        body = json.loads(request.body)
    except Exception:
        body = request.POST.dict()
    package = body.get('package', '').strip()

    if not package or package.lower() not in NORMALIZZA:
        return JsonResponse({'ok': False, 'errore': 'Pacchetto non valido'})

    try:
        cmd = [sys.executable, '-m', 'pip', 'install', '--upgrade', package]

        # Django causa riavvio autoreloader → processo distaccato
        if package.lower() == 'django':
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            )
            logger.info("Aggiornamento %s: avviato in background", package)
            return JsonResponse({'ok': True, 'in_background': True,
                                 'output': 'Aggiornamento avviato in background...\nIl server si riavvierà automaticamente al termine.'})

        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        output = (r.stdout or '') + (r.stderr or '')
        ok = r.returncode == 0
        logger.info("Aggiornamento %s: %s", package, 'OK' if ok else 'FALLITO')
        return JsonResponse({'ok': ok, 'output': output[:5000]})
    except subprocess.TimeoutExpired:
        return JsonResponse({'ok': False, 'errore': 'Timeout (120s)'})
    except Exception as e:
        logger.exception("Errore aggiornamento %s", package)
        return JsonResponse({'ok': False, 'errore': str(e)[:500]})


@login_required
@permesso_richiesto('impostazioni')
@require_POST
def ajax_aggiorna_requirements(request):
    """Aggiorna requirements.txt con versioni PyPI, senza installare."""
    req_path = Path(__file__).resolve().parent.parent.parent / 'requirements.txt'
    if not req_path.exists():
        return JsonResponse({'ok': False, 'errore': 'requirements.txt non trovato'})

    import requests as req
    import re

    righe = req_path.read_text(encoding='utf-8').splitlines(keepends=True)
    nuove_righe = []
    modificati = []

    for riga in righe:
        riga_strip = riga.strip()
        if not riga_strip or riga_strip.startswith('#'):
            nuove_righe.append(riga)
            continue

        m = re.match(r'^([a-zA-Z0-9_.-]+)\s*==\s*(\S+)', riga_strip)
        if not m:
            nuove_righe.append(riga)
            continue

        nome_pip = m.group(1)
        versione_attuale = m.group(2)

        if nome_pip.lower() not in NORMALIZZA or nome_pip.lower() in ESCLUDI_DA_AGG:
            nuove_righe.append(riga)
            continue

        try:
            resp = req.get(f'https://pypi.org/pypi/{nome_pip}/json',
                           timeout=5, headers={'Accept': 'application/json'})
            if resp.status_code == 200:
                ultima = resp.json().get('info', {}).get('version', '')
                if ultima and ultima != versione_attuale:
                    from packaging.version import Version
                    if Version(versione_attuale) < Version(ultima):
                        nuove_righe.append(f'{nome_pip}=={ultima}\n')
                        modificati.append(f'{nome_pip} {versione_attuale} → {ultima}')
                        continue
        except Exception:
            pass

        nuove_righe.append(riga)

    if modificati:
        req_path.write_text(''.join(nuove_righe), encoding='utf-8')

    return JsonResponse({'ok': True, 'modificati': modificati, 'totale': len(modificati)})

@login_required
@permesso_richiesto('impostazioni')
@require_POST
def ajax_aggiorna_tutti(request):
    """Aggiorna tutti i pacchetti del requirements.txt."""
    req_path = Path(__file__).resolve().parent.parent.parent / 'requirements.txt'
    if not req_path.exists():
        return JsonResponse({'ok': False, 'errore': 'requirements.txt non trovato'})

    try:
        cmd = [sys.executable, '-m', 'pip', 'install', '--upgrade', '-r', str(req_path)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        output = (r.stdout or '') + (r.stderr or '')
        ok = r.returncode == 0
        logger.info("Aggiornamento TUTTI: %s", 'OK' if ok else 'FALLITO')
        return JsonResponse({'ok': ok, 'output': output[:10000]})
    except subprocess.TimeoutExpired:
        return JsonResponse({'ok': False, 'errore': 'Timeout (300s)'})
    except Exception as e:
        logger.exception("Errore aggiornamento tutti")
        return JsonResponse({'ok': False, 'errore': str(e)[:500]})
