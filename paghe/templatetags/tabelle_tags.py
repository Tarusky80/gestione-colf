from django import template
from datetime import date, datetime
from decimal import Decimal
import math

register = template.Library()

@register.filter
def ceil(value):
    try:
        return int(math.ceil(float(value)))
    except (ValueError, TypeError):
        return value

@register.filter
def field_value(obj, field_name):
    val = getattr(obj, field_name, None)
    if val is None or val == '':
        return {'value': None, 'type': 'none'}
    if isinstance(val, bool):
        return {'value': val, 'type': 'bool'}
    if isinstance(val, (date, datetime)):
        return {'value': val, 'type': 'date'}
    if isinstance(val, (int, float, Decimal)):
        return {'value': float(val), 'type': 'number'}
    return {'value': val, 'type': 'str'}

@register.filter
def hex_to_rgb(value):
    try:
        value = value.lstrip('#')
        if len(value) == 6:
            r = int(value[0:2], 16)
            g = int(value[2:4], 16)
            b = int(value[4:6], 16)
            return f"{r},{g},{b}"
    except (ValueError, TypeError, AttributeError):
        pass
    return "16,185,129"

@register.filter
def get_item(dictionary, key):
    """Accede a un dict per chiave nei template Django."""
    return dictionary.get(key)


@register.filter
def contratto_option(c):
    """Formatta un contratto per option select: Datore — Lavoratore (Livello) — Ben1 [Tipo1] | [Tipo2]"""
    if not c:
        return ''
    datore = getattr(c, 'datore', None)
    lavoratore = getattr(c, 'lavoratore', None)
    parts = []
    if datore:
        parts.append(getattr(datore, 'nome_cognome', str(datore)) or '')
    if lavoratore:
        parts.append(getattr(lavoratore, 'nome_cognome', str(lavoratore)) or '')
    label = ' — '.join(p for p in parts if p)
    pm = getattr(c, 'parametri_minimi', None)
    if pm:
        liv = getattr(pm, 'livello', None)
        if liv:
            label += ' (' + (getattr(liv, 'codice', '?') or '?') + ')'
    progetti = list(c.progetto.all()) if hasattr(c, 'progetto') else []
    if progetti:
        prog_parts = []
        for i, p in enumerate(progetti):
            tipo_nome = p.tipo.nome if p.tipo else '?'
            if i == 0:
                ben_nome = p.beneficiario.nome_cognome if p.beneficiario else '?'
                prog_parts.append(ben_nome + ' [' + tipo_nome + ']')
            else:
                prog_parts.append('[' + tipo_nome + ']')
        label += ' — ' + ' | '.join(prog_parts)
    return label

@register.filter
def tronca_parole(value, n=20):
    if not value:
        return ''
    words = value.split()
    if len(words) <= n:
        return value
    return ' '.join(words[:n]) + '... <span class="text-secondary small fw-bold">CONTINUA</span>'

@register.filter
def tronca_caratteri(value, n=150):
    if not value:
        return ''
    if len(value) <= n:
        return value
    return value[:n].rsplit(' ', 1)[0] + '... <span class="text-secondary small fw-bold">CONTINUA</span>'
