"""Modulo _helpers - funzioni miscellanea (ridotto: PDF→_gestione_pdf,
anagrafica→_anagrafiche_utils, filesystem→_file_utils)."""

import logging

logger = logging.getLogger(__name__)

from paghe.views._common_imports import *
from paghe.views._constants import TABELLE_MAP, TOGGLE_KEYS

# Re-export da moduli specializzati per retrocompatibilità
from paghe.views._gestione_pdf import (
    _genera_pdf_da_testo,
    _genera_pdf_da_testo_playwright,
    _genera_pdf_da_testo_reportlab,
    _stampa_pdf_windows,
    _assicura_cartella_stampe,
    _crea_pagina_bianca,
    _unisci_pdf,
    _unisci_pdf_bytes,
    _formatta_testo_pdf,
    _pulisci_html_tinymce,
    _rl_font_name,
    _registra_font_pdf,
    _format_pdf_cell,
    _scarica_font_emoji,
    _scarica_font_roboto,
    _FONT_RL_MAP,
)
from paghe.views._anagrafiche_utils import (
    _cerca_comune_per_nome,
    _decodifica_cf,
    _split_nc,
    _calcola_preavviso,
    _build_contratto_data,
    _carica_comuni_map,
)
from paghe.views._file_utils import (
    _sanitizza_nome,
    _nome_cartella_contratto,
    _get_cartella_documenti,
)


# --- _dati_eliminato ---

def _dati_eliminato(obj):
    """Serializza un oggetto inclusi i campi ManyToMany (esclusi di default)."""
    dati = json.loads(serializers.serialize('json', [obj]))
    for m2m in obj._meta.many_to_many:
        pks = list(getattr(obj, m2m.name).values_list('pk', flat=True))
        if pks:
            dati[0]['fields'][m2m.name] = pks
    return dati


# --- _get_tabella_conf ---

def _get_tabella_conf(tipo):
    conf = TABELLE_MAP.get(tipo)
    if not conf:
        return None
    return {
        'model': conf['model'],
        'form_class': conf['form'],
        'titolo': conf['titolo'],
        'icona': conf['icona'],
        'tipo_url': tipo,
    }


# --- _resolve_valore ---

def _resolve_valore(obj, field_path):
    parts = field_path.split('__')
    for p in parts:
        if obj is None:
            return ''
        val = getattr(obj, p, None)
        if callable(val) and not isinstance(val, type):
            val = val()
        obj = val
    return obj if obj is not None else ''


# --- _xlsx_field_to_python ---

def _xlsx_field_to_python(val, field_name):
    if val is None or val == '':
        return None
    from datetime import datetime
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, str):
        lower = val.strip().lower()
        if lower in ('si', 'sì', 'vero', 'true', 'yes', 'x', '1'):
            return True
        if lower in ('no', 'falso', 'false', '', '-', '0'):
            return False
    return val


# --- _risolvi_globali ---

def _risolvi_globali(testo):
    """Resolve only global/OpzioniSoftware variables (no contratto needed)."""
    import re as _re
    from datetime import date as _date
    opzioni = get_opzioni()
    _v = {}
    if opzioni:
        _v['NOME_SOFTWARE'] = opzioni.nome_programma
        _v['NOME_STUDIO'] = getattr(opzioni, 'nome_studio', 'CIRCOLO MCL ISILI di GABRIELE CORONGIU') or 'CIRCOLO MCL ISILI di GABRIELE CORONGIU'
        _v['DENOMINAZIONE_STUDIO'] = opzioni.denominazione_studio or ''
        _v['TELEFONO_STUDIO'] = opzioni.telefono_studio or ''
        _v['EMAIL_STUDIO'] = opzioni.email_studio or ''
        _v['IBAN_STUDIO'] = opzioni.iban_studio or ''
        _v['INTESTATARIO_IBAN'] = opzioni.intestatario_iban or ''
        _v['BANCA_IBAN'] = opzioni.banca_iban or ''
        _val = opzioni.dati_studio.strip() if opzioni.dati_studio else ''
        _v['INDIRIZZO_STUDIO'] = _val
        _v['DATI_STUDIO'] = _val
        _footer_tpl = opzioni.testo_note_footer_mail
        _v['NOTE_FOOTER_MAIL'] = _footer_tpl.corpo_testo if _footer_tpl else ''
        _firma_tpl = opzioni.testo_firma_email
        _v['FIRMA_EMAIL'] = _firma_tpl.corpo_testo if _firma_tpl else ''
        _v['ALERT_CONTRIBUTI'] = opzioni.testo_alert_contributi.corpo_testo if opzioni.testo_alert_contributi else ''
        _v['TESTO_NOTE_AVVERTENZE'] = opzioni.testo_note_avvertenze.corpo_testo if opzioni.testo_note_avvertenze else ''
        _comune = opzioni.comune_studio.strip() if opzioni.comune_studio else ''
        _cap = opzioni.cap_studio.strip() if opzioni.cap_studio else ''
        if _comune or _cap:
            _v['INDIRIZZO_STUDIO_COMPLETO'] = f"{_val}, {_comune} ({_cap})" if _comune and _cap else f"{_val} {_comune}{_cap}".strip()
        else:
            _v['INDIRIZZO_STUDIO_COMPLETO'] = _val
        _v['VERSIONE_SOFTWARE'] = opzioni.versione_programma or ''
        _v['COMUNE_STUDIO'] = _comune or '[COMUNE_STUDIO]'
        _v['CAP_STUDIO'] = _cap or '[CAP_STUDIO]'
    oggi = _date.today()
    from datetime import datetime as _datetime
    import time as _time
    _v['DATA_ODIERNA'] = oggi.strftime('%d/%m/%Y')
    _v['ANNO_IN_CORSO'] = str(oggi.year)
    _v['ANNO_CORRENTE'] = str(oggi.year)
    _v['MESE_CORRENTE'] = MESI_IT[oggi.month]
    _v['MESE_CORRENTE_NOME'] = MESI_IT[oggi.month]
    _v['GIORNO_CORRENTE'] = str(oggi.day)
    _v['ORA_CORRENTE'] = _datetime.now().strftime('%H:%M')
    _v['DATA_ODIERNA_COMPLETA'] = _datetime.now().strftime('%d/%m/%Y %H:%M')
    _v['TIMESTAMP_UNIX'] = str(int(_time.time()))
    _v['LINEA'] = '<hr style="border:none;border-top:1px solid #5C5F66;margin:4px 0;">'
    _v['HR'] = _v['LINEA']
    _v['RIGA_VUOTA'] = '<br>'
    _v['RATEO_13MA'] = 'NON INCLUSO'
    _v['CAMBIA_PAGINA'] = '<div style="page-break-before: always;"></div>'
    _v['INIZIO_PAGINA'] = '<div style="page-break-before: always;">'
    _v['STOP_INIZIO_PAGINA'] = '</div>'
    _v['FINE_PAGINA'] = '<div id="pdfFooterBlock">'
    _v['STOP_FINE_PAGINA'] = '</div>'

    _logo_data = {}
    if opzioni:
        for _logo_key, _logo_field in [('LOGO_PROGRAMMA', 'logo'), ('LOGO_BUSTE_PAGA', 'logo_buste_paga')]:
            try:
                _img_field = getattr(opzioni, _logo_field, None)
                if _img_field and hasattr(_img_field, 'path') and _img_field.path:
                    from PIL import Image
                    with Image.open(_img_field.path) as _pil:
                        _ow, _oh = _pil.size
                    with open(_img_field.path, 'rb') as _f:
                        import base64
                        _b64 = base64.b64encode(_f.read()).decode('utf-8')
                    _ext = _img_field.path.rsplit('.', 1)[-1].lower() if '.' in _img_field.path else 'png'
                    if _ext == 'jpg': _ext = 'jpeg'
                    _logo_data[_logo_key] = {'uri': f'data:image/{_ext};base64,{_b64}', 'w': _ow, 'h': _oh}
                    _v[_logo_key] = f'<img src="{_logo_data[_logo_key]["uri"]}" width="110" style="max-width:110px;height:auto;">'
                else:
                    _logo_data[_logo_key] = None
                    _v[_logo_key] = ''
            except Exception:
                logger.exception("Errore in _risolvi_globali")
                _logo_data[_logo_key] = None
                _v[_logo_key] = ''

    _logo_keys = {'LOGO_PROGRAMMA', 'LOGO_BUSTE_PAGA'}
    def _replacer_glob(m, lookup):
        _name = m.group(1)
        _pct = m.group(2)
        if _name in _logo_keys and _logo_data.get(_name) and _pct is not None:
            _ratio = int(_pct) / 100.0
            _nw = int(_logo_data[_name]['w'] * _ratio)
            _nh = int(_logo_data[_name]['h'] * _ratio)
            return f'<img src="{_logo_data[_name]["uri"]}" width="{_nw}" height="{_nh}" style="max-width:{_nw}px;height:auto;">'
        return lookup.get(_name, m.group(0))

    from paghe.models import ModelloDocumentale as _TP
    for _k in ('TOP_DOCUMENTO', 'FOOTER_DOCUMENTO'):
        _c = ''
        try:
            _t = _TP.objects.filter(tipo=_k).first()
            if _t and _t.corpo_testo:
                _c = _t.corpo_testo.replace('{{' + _k + '}}', '')
                _c = _re.sub(r'\{\{(\w+)(?:,\s*(\d+))?\}\}', lambda m: _replacer_glob(m, _v), _c)
        except Exception:
            logger.exception("Errore in _replacer_glob")
            _c = ''
        _v[_k] = _c

    import operator as _op
    _SAFE_OPS = {'+': _op.add, '-': _op.sub, '*': _op.mul, '/': _op.truediv, '//': _op.floordiv, '%': _op.mod}
    def _resolve_arith_glob(m):
        vn, op, num = m.group(1), m.group(2), m.group(3)
        if vn not in _v:
            return m.group(0)
        v = _v[vn]
        try:
            vc = _re.sub(r'[^\d.\-]', '', str(v))
            if not vc:
                return m.group(0)
            r = _SAFE_OPS[op](float(vc), float(num))
            has_cur = '\u20ac' in str(v)
            if has_cur:
                return f'\u20ac {r:,.2f}' if r != int(r) else f'\u20ac {int(r):,}'
            return f'{r:.2f}' if r != int(r) else str(int(r))
        except (ValueError, TypeError, KeyError, ZeroDivisionError):
            return m.group(0)
    testo = _re.sub(r'\{\{(\w+)\s*([+\-*/%]|//)\s*(\d+(?:\.\d+)?)\}\}', _resolve_arith_glob, testo)

    return _re.sub(r'\{\{(\w+)(?:,\s*(\d+))?\}\}', lambda m: _replacer_glob(m, _v), testo)


# --- _get_testo_fk ---

def _get_testo_fk(opzioni, fk_field, fallback_field=None, contratto=None):
    val = getattr(opzioni, fk_field, None)
    if val is not None:
        testo = val.corpo_testo or ''
        if contratto:
            from paghe.views._testi import _risolvi_variabili_testo
            testo = _risolvi_variabili_testo(testo, contratto)
        return testo
    if fallback_field:
        return getattr(opzioni, fallback_field, '') or ''
    return ''


# --- _parse_toggles ---

def _parse_toggles(request):
    toggles = {}
    for k in TOGGLE_KEYS:
        v = request.GET.get(k)
        if v is not None:
            toggles[k] = v == '1'
    return toggles or None


# --- _parse_convivenza_items ---

def _parse_convivenza_items(request):
    incl_pranzo = request.GET.get('incl_pranzo')
    incl_cena = request.GET.get('incl_cena')
    incl_alloggio = request.GET.get('incl_alloggio')
    giorni = request.GET.get('giorni_conv')
    if incl_pranzo is None and incl_cena is None and incl_alloggio is None and giorni is None:
        return None
    conv = {}
    if incl_pranzo is not None:
        conv['pranzo'] = incl_pranzo == '1'
    if incl_cena is not None:
        conv['cena'] = incl_cena == '1'
    if incl_alloggio is not None:
        conv['alloggio'] = incl_alloggio == '1'
    if giorni is not None:
        try:
            conv['giorni'] = int(giorni)
        except (ValueError, TypeError):
            pass
    return conv


# --- _tipo_calcolo_label ---

def _tipo_calcolo_label(tipo):
    if tipo == 'SOSTITUZIONE':
        return 'Sostituzione (Art. 14 c.9)'
    if tipo == 'NON_CONVIVENTE':
        return 'Non Convivente'
    if tipo == 'CONVIVENTI_CCNL':
        return 'Conviventi CCNL'
    if tipo == 'NOTTURNO':
        return 'Notturno'
    if tipo == 'MALATTIA':
        return 'Malattia'
    if tipo and tipo.startswith('CALCOLO_INVERSO'):
        mappa = {
            '_ORE_MENSILI': 'IN BASE ALLE ORE MENSILI',
            '_ORE_SETTIMANALI': 'IN BASE ALLE ORE SETTIMANALI',
            '_LORDO': 'IN BASE ALLO STIPENDIO LORDO',
            '_NETTO': 'IN BASE ALLO STIPENDIO NETTO',
        }
        suffix = tipo.replace('CALCOLO_INVERSO', '')
        label = mappa.get(suffix)
        if label:
            return f'Calcolo Inverso \u2014 {label}'
        return 'Calcolo Inverso'
    return 'CONVIVENTE'


# --- _offusca_ctx_anagrafici ---

def _offusca_ctx_anagrafici(ctx):
    ctx['datore'] = 'Datore di Lavoro'
    ctx['lavoratore'] = 'Collaboratore'
    ctx['datore_indirizzo'] = '***'
    ctx['lavoratore_indirizzo'] = '***'
    ctx['datore_comune'] = ''
    ctx['lavoratore_comune'] = ''
    ctx['data_assunzione'] = '***'
    ctx['codice_rapporto_inps'] = '***'
    ctx['note_datore'] = ''
    ctx['note_avvertenze'] = ''
    ctx['alert_contributi_studio'] = ''
    if ctx.get('progetti'):
        for i, p in enumerate(ctx['progetti']):
            p['nome'] = f'Progetto {i + 1}'
            p['indirizzo'] = '***'
            p['comune'] = ''
            p['beneficiario_nome'] = f'Beneficiario {i + 1}'
    if ctx.get('progetti_data') and ctx['progetti_data'].get('righe'):
        for r in ctx['progetti_data']['righe']:
            r['nome'] = 'Progetto'


# --- _wrap_html_email ---

def _wrap_html_email(corpo):
    return f'''<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
body {{ font-family: Arial, Helvetica, sans-serif; font-size: 11pt; color: #333; line-height: 1.6; }}
p {{ margin: 0 0 10px 0; }}
table {{ border-collapse: collapse; width: 100%; }}
td, th {{ border: 1px solid #ccc; padding: 4px 8px; }}
</style></head><body>
{corpo}
</body></html>'''
