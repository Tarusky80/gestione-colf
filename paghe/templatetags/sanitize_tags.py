import bleach as _bleach
from django import template
from django.utils.html import mark_safe

register = template.Library()

_ALLOWED_TAGS = {
    'p', 'br', 'b', 'i', 'u', 'em', 'strong', 'a', 'ul', 'ol', 'li',
    'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'table', 'thead', 'tbody', 'tr', 'td', 'th',
    'img', 'hr', 'pre', 'code', 'blockquote', 'sub', 'sup',
}

_ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'span': ['style'],
    'div': ['style'],
    'p': ['style'],
    'td': ['style', 'colspan', 'rowspan'],
    'th': ['style', 'colspan', 'rowspan'],
    'table': ['style', 'class'],
}

_ALLOWED_STYLES = [
    'color', 'background-color', 'font-size', 'font-family',
    'font-weight', 'text-align', 'text-decoration',
    'margin', 'margin-left', 'margin-right', 'padding',
    'border', 'border-collapse', 'width', 'height',
]


@register.filter(is_safe=True)
def sanitize(value):
    """Sanitizza HTML: rimuove tag/attributi pericolosi, mantiene safe."""
    if not value:
        return ''
    cleaned = _bleach.clean(
        value,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        styles=_ALLOWED_STYLES,
        strip=True,
    )
    return mark_safe(cleaned)
