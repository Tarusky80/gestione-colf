"""Utility anagrafiche: comuni, CF, preavviso (estratte da _helpers.py)."""
import logging
import json
from pathlib import Path

from paghe.views._constants import _MESI_CF

logger = logging.getLogger(__name__)


_COMUNI_MAP_CACHE = None
_NOME_MAP_CACHE = None


def _carica_comuni_map():
    global _COMUNI_MAP_CACHE
    if _COMUNI_MAP_CACHE is not None:
        return _COMUNI_MAP_CACHE
    path = Path(__file__).resolve().parent.parent / 'data' / 'comuni_full.json'
    if path.exists():
        with open(str(path), encoding='utf-8') as f:
            _COMUNI_MAP_CACHE = json.load(f)
    else:
        _COMUNI_MAP_CACHE = {}
    return _COMUNI_MAP_CACHE


def _cerca_comune_per_nome(q):
    if not q or not q.strip():
        return None
    q = q.strip().lower()
    mappa = _carica_comuni_map()
    global _NOME_MAP_CACHE
    if _NOME_MAP_CACHE is None:
        _NOME_MAP_CACHE = {}
        for belfiore, info in mappa.items():
            nome = info.get('comune', '').strip().lower()
            if nome:
                _NOME_MAP_CACHE.setdefault(nome, []).append(belfiore)
    if q in _NOME_MAP_CACHE:
        belfiori = _NOME_MAP_CACHE[q]
        if belfiori:
            info = dict(mappa[belfiori[0]])
            info['codice_belfiore'] = belfiori[0]
            return info
    for nome, belfiori in _NOME_MAP_CACHE.items():
        if nome.startswith(q):
            info = dict(mappa[belfiori[0]])
            info['codice_belfiore'] = belfiori[0]
            return info
    for nome, belfiori in _NOME_MAP_CACHE.items():
        if q in nome:
            info = dict(mappa[belfiori[0]])
            info['codice_belfiore'] = belfiori[0]
            return info
    return None


def _decodifica_cf(cf):
    if not cf or len(cf) != 16:
        return {'data_nascita': '', 'sesso': '', 'comune_nascita': '', 'provincia_nascita': '', 'estero': False}
    cf = cf.upper()
    yy = cf[6:8]
    mm = _MESI_CF.get(cf[8], '??')
    dd = int(cf[9:11])
    sesso = 'FEMMINA' if dd > 40 else 'MASCHIO'
    gg = dd - 40 if dd > 40 else dd
    anno = '19' + yy if int(yy) > 25 else '20' + yy
    try:
        from datetime import datetime
        data = datetime.strptime(f'{gg:02d}/{mm}/{anno}', '%d/%m/%Y').strftime('%d/%m/%Y')
    except ValueError:
        data = f'{gg:02d}/{mm}/{anno}'

    codice_catastale = cf[11:15]
    comune_nome = ''
    provincia_sigla = ''
    estero = False
    if codice_catastale:
        mappa = _carica_comuni_map()
        info = mappa.get(codice_catastale)
        if info:
            comune_nome = info.get('comune', '')
            provincia_sigla = info.get('sigla', '')
        elif codice_catastale.startswith('Z'):
            estero = True
            comune_nome = 'Estero'

    return {
        'data_nascita': data,
        'sesso': sesso,
        'comune_nascita': comune_nome,
        'provincia_nascita': provincia_sigla,
        'estero': estero,
    }


def _split_nc(nc):
    if not nc:
        return '', ''
    parts = nc.strip().split(' ', 1)
    return parts[0], parts[1] if len(parts) > 1 else ''


def _calcola_preavviso(contratto, data_cessazione, causale):
    if causale in ('SCADENZA_TERMINE', 'DECESSO_DATORE', 'DECESSO_LAVORATORE'):
        return {'licenziamento': 0, 'dimissioni': 0, 'finale': 0, 'etichetta': 'Nessun preavviso'}

    if not data_cessazione or not contratto.data_assunzione:
        return {'licenziamento': 0, 'dimissioni': 0, 'finale': 0, 'etichetta': '\u2014'}

    delta = data_cessazione - contratto.data_assunzione
    anni = delta.days / 365.25

    ore_sett = float(contratto.ore_settimanali_calcolate)
    is_conv = contratto.is_convivente

    if is_conv:
        if anni <= 1:
            lic = 30
        else:
            lic = 60
    elif ore_sett > 24:
        if anni < 5:
            lic = 15
        else:
            lic = 30
    else:
        if anni <= 2:
            lic = 8
        else:
            lic = 15

    dim = max(round(lic / 2), 1)

    if causale == 'DIMISSIONI':
        finale = dim
        etichetta = f'{finale} giorni (dimissioni)'
    else:
        finale = lic
        etichetta = f'{finale} giorni (licenziamento)'

    return {
        'licenziamento': lic,
        'dimissioni': dim,
        'finale': finale,
        'etichetta': etichetta,
        'ore_settimanali': round(ore_sett, 2),
        'anni_anzianita': round(anni, 1),
        'is_convivente': is_conv,
    }


def _build_contratto_data(c):
    d_nome, d_cogn = _split_nc(c.datore.nome_cognome)
    l_nome, l_cogn = _split_nc(c.lavoratore.nome_cognome)
    l_cf_decoded = _decodifica_cf(c.lavoratore.codice_fiscale)

    paga_base = float(c.parametri_minimi.paga_base) if c.parametri_minimi else 0.0
    tredicesima = float(c.parametri_minimi.tredicesima_oraria) if c.parametri_minimi else 0.0
    paga_inps = paga_base + tredicesima

    ore_sett = round(c.ore_settimanali_calcolate, 2) if hasattr(c, 'ore_settimanali_calcolate') else 0.0

    progetti = list(c.progetto.all())
    data_fine_display = ''
    data_fine_raw = ''
    if c.data_fine:
        data_fine_display = c.data_fine.strftime('%d/%m/%Y')
        data_fine_raw = c.data_fine.isoformat()
    elif c.tipo_contratto == 'DETERMINATO' and progetti:
        date_fini = [p.data_fine for p in progetti if p.data_fine]
        if date_fini:
            df = max(date_fini)
            data_fine_display = df.strftime('%d/%m/%Y')
            data_fine_raw = df.isoformat()

    preavviso = _calcola_preavviso(c, c.data_fine, c.causale_cessazione)

    # Costruisce il testo per il dropdown
    liv_cod = c.parametri_minimi.livello.codice if c.parametri_minimi and c.parametri_minimi.livello else '?'
    contratto_option = c.datore.nome_cognome + ' — ' + c.lavoratore.nome_cognome + ' (' + liv_cod + ')'
    if progetti:
        prog_parts = []
        for i, p in enumerate(progetti):
            tn = p.tipo.nome if p.tipo else '?'
            if i == 0:
                bn = p.beneficiario.nome_cognome if p.beneficiario else '?'
                prog_parts.append(bn + ' [' + tn + ']')
            else:
                prog_parts.append('[' + tn + ']')
        contratto_option += ' — ' + ' | '.join(prog_parts)

    return {
        'pk': c.pk,
        'datore': {
            'nome': d_nome,
            'cognome': d_cogn,
            'indirizzo': c.datore.indirizzo or '',
            'comune': c.datore.comune or '',
        },
        'lavoratore': {
            'cf': c.lavoratore.codice_fiscale.upper() if c.lavoratore.codice_fiscale else '',
            'nome': l_nome,
            'cognome': l_cogn,
            'data_nascita': l_cf_decoded['data_nascita'],
            'sesso': l_cf_decoded['sesso'],
            'comune_nascita': l_cf_decoded['comune_nascita'],
            'provincia_nascita': l_cf_decoded['provincia_nascita'],
            'indirizzo': c.lavoratore.indirizzo or '',
            'comune': c.lavoratore.comune or '',
        },
        'contratto': {
            'tipo': c.get_tipo_contratto_display(),
            'data_assunzione': c.data_assunzione.strftime('%d/%m/%Y'),
            'data_assunzione_raw': c.data_assunzione.isoformat(),
            'data_fine': data_fine_display,
            'data_fine_raw': data_fine_raw,
            'causale_cessazione': c.causale_cessazione or '',
            'ore_settimanali': f'{ore_sett:.2f}'.replace('.', ','),
            'paga_inps': f'{paga_inps:.4f}'.replace('.', ','),
            'codice_rapporto_inps': c.codice_rapporto_inps or '',
            'is_convivente': c.is_convivente,
            'preavviso': preavviso,
        },
        'contratto_option': contratto_option,
    }
