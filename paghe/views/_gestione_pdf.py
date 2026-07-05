"""Funzioni per generazione, unione e stampa PDF (estratte da _helpers.py)."""

import logging
from paghe.views._common_imports import *
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle,
    HRFlowable, Image, ListFlowable, ListItem, PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor

from paghe.views._constants import _FONT_PROGETTO, CARTELLA_STAMPE_TEMP

logger = logging.getLogger(__name__)


# --- _pulisci_html_tinymce ---

def _pulisci_html_tinymce(testo):
    if not testo:
        return testo or ''
    testo = re.sub(r'\s+data-(?:path-to-node|mce-[a-z0-9]+|sheets-[a-z0-9]+|tmp-[a-z0-9]+)="[^"]*"', '', testo, flags=re.IGNORECASE)
    testo = re.sub(r'\s+(?:contenteditable|spellcheck|translate)="[^"]*"', '', testo, flags=re.IGNORECASE)
    return testo


# --- _formatta_testo_pdf ---

def _formatta_testo_pdf(testo):
    if not testo:
        return testo or ''
    testo = _pulisci_html_tinymce(testo)
    testo = re.sub(r'</?(?:p|div|h[1-6]|blockquote|pre|ul|ol|li|table|thead|tbody|tfoot|tr|th|td|form|fieldset|section|article|header|footer|nav|aside|figure|figcaption|details|summary|dl|dt|dd|span|para)(?:\s[^>]*)?>', '', testo, flags=re.IGNORECASE)
    testo = re.sub(r'<br\s*/?>', '<br/>', testo)
    testo = re.sub(r'(?:<br/>\s*){2,}', '<br/>', testo)
    lines = testo.split('\n')
    result = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('* ') or stripped.startswith('- '):
            if not in_list:
                result.append('<ul>')
                in_list = True
            result.append('<li>' + stripped[2:].strip() + '</li>')
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            result.append(line)
    if in_list:
        result.append('</ul>')
    return '<br/>'.join(result)


# --- _scarica_font_emoji ---

def _scarica_font_emoji():
    import urllib.request
    import zipfile
    os.makedirs(_FONT_PROGETTO, exist_ok=True)
    target_path = os.path.join(_FONT_PROGETTO, 'Symbola.ttf')
    if os.path.exists(target_path):
        return target_path
    url = 'https://www.fontsquirrel.com/fonts/download/symbola'
    try:
        resp = urllib.request.urlopen(url, timeout=30)
        data = resp.read()
        if data[:2] == b'PK':
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                for name in zf.namelist():
                    if name.lower().endswith(('.ttf', '.otf')):
                        with zf.open(name) as f, open(target_path, 'wb') as out:
                            out.write(f.read())
                        return target_path
        else:
            with open(target_path, 'wb') as f:
                f.write(data)
            return target_path
    except Exception:
        logger.exception("Errore in _scarica_font_emoji")
        return None


# --- _scarica_font_roboto ---

def _scarica_font_roboto():
    font_dir = _FONT_PROGETTO
    os.makedirs(font_dir, exist_ok=True)
    targets = ['Roboto-Regular.ttf', 'Roboto-Bold.ttf', 'Roboto-Italic.ttf', 'Roboto-BoldItalic.ttf']
    if all(os.path.exists(os.path.join(font_dir, f)) for f in targets):
        return True
    import urllib.request, zipfile, io
    url = 'https://fonts.google.com/download?family=Roboto'
    try:
        resp = urllib.request.urlopen(url, timeout=60)
        data = resp.read()
        if data[:2] == b'PK':
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                for name in zf.namelist():
                    basename = os.path.basename(name)
                    if basename in targets:
                        with zf.open(name) as f:
                            with open(os.path.join(font_dir, basename), 'wb') as out:
                                out.write(f.read())
        return all(os.path.exists(os.path.join(font_dir, f)) for f in targets)
    except Exception:
        logger.exception("Errore in _scarica_font_roboto")
        return False


# --- _registra_font_pdf ---

_FONT_RL_MAP = {
    'Arial': 'Helvetica',
    'Helvetica': 'Helvetica',
    'Times New Roman': 'Times-Roman',
    'Courier New': 'Courier',
    'Georgia': 'Times-Roman',
    'Verdana': 'Helvetica',
    'Roboto': 'Roboto',
    'Calibri': 'Calibri',
}

def _rl_font_name(ui_name):
    name = ui_name.strip()
    return _FONT_RL_MAP.get(name, 'Helvetica')

def _registra_font_pdf():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    font_dir = _FONT_PROGETTO
    os.makedirs(font_dir, exist_ok=True)
    _scarica_font_roboto()
    roboto_files = {
        'Roboto': 'Roboto-Regular.ttf',
        'Roboto-Bold': 'Roboto-Bold.ttf',
        'Roboto-Italic': 'Roboto-Italic.ttf',
        'Roboto-BoldItalic': 'Roboto-BoldItalic.ttf',
    }
    registered = 0
    for font_name, filename in roboto_files.items():
        path = os.path.join(font_dir, filename)
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(font_name, path))
                registered += 1
            except Exception:
                logger.warning("Impossibile registrare font %s da %s", font_name, path)
    if registered < 4:
        win_fonts = os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts')
        fallback_candidates = [
            {'Roboto': 'calibri.ttf', 'Roboto-Bold': 'calibrib.ttf',
             'Roboto-Italic': 'calibrii.ttf', 'Roboto-BoldItalic': 'calibriz.ttf'},
            {'Roboto': 'segoeui.ttf', 'Roboto-Bold': 'segoeuib.ttf',
             'Roboto-Italic': 'segoeuii.ttf', 'Roboto-BoldItalic': 'segoeuiz.ttf'},
            {'Roboto': 'arial.ttf', 'Roboto-Bold': 'arialbd.ttf',
             'Roboto-Italic': 'ariali.ttf', 'Roboto-BoldItalic': 'arialbi.ttf'},
        ]
        for candidate_set in fallback_candidates:
            for font_name, filename in candidate_set.items():
                if font_name in getattr(pdfmetrics, '_fonts', {}):
                    continue
                path = os.path.join(win_fonts, filename)
                if os.path.exists(path):
                    try:
                        pdfmetrics.registerFont(TTFont(font_name, path))
                        registered += 1
                    except Exception:
                        logger.warning("Impossibile registrare font fallback %s da %s", font_name, path)
            missing = sum(1 for n in roboto_files if n not in getattr(pdfmetrics, '_fonts', {}))
            if missing == 0:
                break
    _scarica_font_emoji()
    font_path = os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts', 'seguisym.ttf')
    if not os.path.exists(font_path):
        font_path = os.path.join(font_dir, 'Symbola.ttf')
        if not os.path.exists(font_path):
            font_path = None
    if font_path and os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('SegoeSymbol', font_path))
        except Exception:
            logger.warning("Impossibile registrare font SegoeSymbol da %s", font_path)
    return registered >= 2


# --- _genera_pdf_da_testo_reportlab ---

def _genera_pdf_da_testo_reportlab(tipo, titolo, corpo, output_path, font_family='Arial', font_size=11):
    _font_ok = _registra_font_pdf()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=10*mm, bottomMargin=10*mm,
    )
    styles = getSampleStyleSheet()
    base_font = _rl_font_name(font_family)
    if not _font_ok:
        base_font = styles['Normal'].fontName

    fs = max(8, min(20, int(font_size)))
    ld = max(fs * 1.4, fs + 4)
    s_body = ParagraphStyle('Body', parent=styles['Normal'],
        fontSize=fs, leading=ld, spaceAfter=2*mm, fontName=base_font)
    s_h = {}
    _hd = [(fs+13,ld+16,5,4),(fs+9,ld+12,4,3),(fs+6,ld+8,3,2.5),(fs+3,ld+5,2.5,2),(fs+1,ld+2,2,1.5),(fs,ld+1,1.5,1)]
    for i, (sz, ld2, sb, sa) in enumerate(_hd, 1):
        s_h[i] = ParagraphStyle(f'H{i}', parent=s_body, fontSize=sz, leading=ld2,
            spaceBefore=sb*mm, spaceAfter=sa*mm)
    s_li = ParagraphStyle('LI', parent=s_body, fontSize=fs, leading=ld, spaceAfter=0.5*mm)
    s_th = ParagraphStyle('TH', parent=s_body, fontSize=max(fs-1,8), leading=max(ld-1,11), fontName='Roboto-Bold')
    s_td = ParagraphStyle('TD', parent=s_body, fontSize=max(fs-1,8), leading=max(ld-1,11))

    grigio_bordo = HexColor('#cccccc')
    grigio_sfondo = HexColor('#f0f0f0')

    from html.parser import HTMLParser
    import base64
    from PIL import Image as PILImage

    class _RLParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.flowables = []
            self._text = []
            self._tag_stack = []
            self._list_buf = None
            self._table_buf = None
            self._tr_buf = None
            self._span_font = []

        def _flush_text(self):
            t = ''.join(self._text).strip()
            self._text.clear()
            if t and t != '<br/>':
                self.flowables.append(Paragraph(t, s_body))

        def _get_text(self):
            t = ''.join(self._text)
            self._text.clear()
            return t

        _FS_RE = re.compile(r'(\d+(?:\.\d+)?)\s*(?:pt|px)?', re.I)
        def _parse_font_size(self, style_str):
            for part in style_str.split(';'):
                part = part.strip()
                if part.lower().startswith('font-size:'):
                    m = self._FS_RE.search(part.split(':', 1)[1].strip())
                    if m:
                        return float(m.group(1))
            return None

        def handle_starttag(self, tag, attrs):
            tag = tag.lower()
            a = dict(attrs)
            if tag in ('p','div','h1','h2','h3','h4','h5','h6'):
                self._flush_text()
                self._tag_stack.append(('block', tag))
            elif tag == 'hr':
                self._flush_text()
                self._tag_stack.append(('hr',))
            elif tag in ('ul','ol'):
                self._flush_text()
                self._tag_stack.append(('list', tag))
                self._list_buf = (tag, [])
            elif tag == 'li':
                self._tag_stack.append(('li',))
            elif tag == 'table':
                self._flush_text()
                self._tag_stack.append(('table',))
                self._table_buf = []
            elif tag == 'tr':
                self._tag_stack.append(('tr',))
                self._tr_buf = []
            elif tag in ('td','th'):
                self._tag_stack.append(('cell', tag))
            elif tag == 'br':
                self._text.append('<br/>')
            elif tag == 'img':
                src = a.get('src','')
                if src.startswith('data:image/'):
                    try:
                        _, b64data = src.split(',', 1)
                        img_data = base64.b64decode(b64data)
                        img_buf = io.BytesIO(img_data)
                        pil = PILImage.open(img_buf)
                        iw, ih = pil.size
                        w = a.get('width')
                        scale = float(w)/iw if w else 1.0
                        img_buf.seek(0)
                        _img = Image(img_buf, width=iw*scale, height=ih*scale)
                        _img.hAlign = 'LEFT'
                        self.flowables.append(_img)
                    except Exception:
                        logger.exception("Errore in handle_starttag")
                        self._text.append('[IMG]')
                else:
                    self._text.append('[IMG]')
            elif tag in ('strong','b'):
                self._text.append('<b>')
            elif tag in ('em','i'):
                self._text.append('<i>')
            elif tag == 'u':
                self._text.append('<u>')
            elif tag == 'span':
                fs = self._parse_font_size(a.get('style', ''))
                if fs and fs >= 11:
                    sz = max(8, min(28, int(fs)))
                    self._text.append(f'<font size="{sz}">')
                    self._span_font.append(sz)
                elif fs is not None:
                    self._text.append(f'<font size="{max(8, int(fs))}">')
                    self._span_font.append(max(8, int(fs)))
                else:
                    self._span_font.append(None)
            elif tag == 'a':
                href = a.get('href', '')
                if href:
                    self._text.append(f'<a href="{href}">')
                else:
                    self._text.append('<a>')
                self._span_font.append(None)

        def handle_endtag(self, tag):
            tag = tag.lower()
            if tag in ('strong','b'):
                self._text.append('</b>'); return
            if tag in ('em','i'):
                self._text.append('</i>'); return
            if tag == 'u':
                self._text.append('</u>'); return
            if tag == 'span':
                if self._span_font:
                    v = self._span_font.pop()
                    if v is not None:
                        self._text.append('</font>')
                return
            if tag == 'a':
                if self._span_font:
                    self._span_font.pop()
                self._text.append('</a>')
                return
            if tag in ('p','div'):
                if self._tag_stack and self._tag_stack[-1] == ('block', tag):
                    self._tag_stack.pop()
                    t = self._get_text()
                    if t.strip():
                        self.flowables.append(Paragraph(t.strip(), s_body))
                return
            if tag in ('h1','h2','h3','h4','h5','h6'):
                if self._tag_stack and self._tag_stack[-1] == ('block', tag):
                    self._tag_stack.pop()
                    t = self._get_text()
                    lvl = int(tag[1])
                    if t.strip():
                        self.flowables.append(Paragraph(t.strip(), s_h[lvl]))
                return
            if tag == 'hr':
                if self._tag_stack and self._tag_stack[-1][0] == 'hr':
                    self._tag_stack.pop()
                    self.flowables.append(HRFlowable(width='100%', thickness=0.5,
                        color=grigio_bordo, spaceAfter=2*mm, spaceBefore=1*mm))
                    self._flush_text()
                return
            if tag in ('ul','ol'):
                if self._tag_stack and self._tag_stack[-1] == ('list', tag) and self._list_buf:
                    self._tag_stack.pop()
                    dtype, items = self._list_buf
                    self._list_buf = None
                    paras = [ListItem(Paragraph(t, s_li)) for t in items if t.strip()]
                    if paras:
                        btype = 'bullet' if dtype == 'ul' else '1'
                        self.flowables.append(ListFlowable(paras, bulletType=btype,
                            start=None, leftIndent=12, bulletFontSize=10))
                    self._flush_text()
                return
            if tag == 'li':
                if self._tag_stack and self._tag_stack[-1] == ('li',):
                    self._tag_stack.pop()
                    t = self._get_text()
                    if self._list_buf:
                        self._list_buf[1].append(t)
                return
            if tag == 'table':
                if self._tag_stack and self._tag_stack[-1][0] == 'table' and self._table_buf is not None:
                    self._tag_stack.pop()
                    tbl = self._table_buf
                    self._table_buf = None
                    if tbl:
                        ts = TableStyle([
                            ('GRID', (0,0), (-1,-1), 0.5, grigio_bordo),
                            ('VALIGN', (0,0), (-1,-1), 'TOP'),
                            ('TOPPADDING', (0,0), (-1,-1), 2),
                            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                            ('LEFTPADDING', (0,0), (-1,-1), 4),
                            ('RIGHTPADDING', (0,0), (-1,-1), 4),
                        ])
                        if tbl and tbl[0] and all(c[1] for c in tbl[0]):
                            ts.add('BACKGROUND', (0,0), (-1,0), grigio_sfondo)
                        data = [[Paragraph(c[0], s_th if c[1] else s_td) for c in row] for row in tbl]
                        self.flowables.append(Table(data, repeatRows=1, style=ts))
                    self._flush_text()
                return
            if tag == 'tr':
                if self._tag_stack and self._tag_stack[-1][0] == 'tr' and self._tr_buf is not None:
                    self._tag_stack.pop()
                    if self._table_buf is not None:
                        self._table_buf.append(list(self._tr_buf))
                    self._tr_buf = None
                return
            if tag in ('td','th'):
                if self._tag_stack and self._tag_stack[-1] == ('cell', tag):
                    self._tag_stack.pop()
                    t = self._get_text()
                    if self._tr_buf is not None:
                        self._tr_buf.append((t, tag == 'th'))
                return

        def handle_data(self, data):
            if not self._tag_stack:
                data = data.replace('\n', '<br/>')
            self._text.append(data)

        def handle_entityref(self, name):
            self._text.append(f'&{name};')

        def handle_charref(self, name):
            self._text.append(f'&#{name};')

        def handle_comment(self, data):
            if data.strip() == 'PAGEBREAK':
                self.flowables.append(PageBreak())

    corpo = _pulisci_html_tinymce(corpo)
    corpo = re.sub(r'<div\s+style="page-break-before:\s*always;"></div>', '<!--PAGEBREAK-->', corpo)
    corpo = re.sub(r'<div\s+id="pdfFooterBlock">', '', corpo)
    corpo = re.sub(r'\{\{LINEA\}\}', '<hr/>', corpo)
    corpo = re.sub(r'\{\{HR\}\}', '<hr/>', corpo)
    corpo = re.sub(r'\{\{.+?\}\}', '', corpo)
    corpo = re.sub(r'<p>\s*(?:<br\s*/?>\s*)*</p>', '', corpo)

    parser = _RLParser()
    parser.feed(corpo)
    tail = ''.join(parser._text).strip()
    parser._text.clear()
    if tail:
        parser.flowables.append(Paragraph(tail, s_body))

    if titolo:
        parser.flowables.insert(0, Paragraph(titolo, s_body))

    doc.build(parser.flowables)
    with open(output_path, 'wb') as f:
        f.write(buffer.getvalue())
    return buffer


# --- _genera_pdf_da_testo_playwright ---

def _genera_pdf_da_testo_playwright(titolo, corpo, output_path, font_family='Roboto', font_size=11):
    from playwright.sync_api import sync_playwright
    rl_font = _rl_font_name(font_family)
    fs = max(8, min(20, int(font_size)))
    titolo_escaped = str(titolo).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
    titolo_html = f'<h1 style="font-size:{fs+13}pt;">{titolo_escaped}</h1>\n' if titolo else ''
    html = f'''<!DOCTYPE html>
<html lang="it"><head><meta charset="utf-8">
<link rel="stylesheet" href="https://cdn.ckeditor.com/ckeditor5/44.3.0/ckeditor5.css">
<style>
@page {{ size: A4; margin: 2mm 5mm 2mm 5mm; }}
body {{ font-family: '{rl_font}', Arial, Helvetica, sans-serif; font-size: {fs}pt; line-height: 1.5; color: #000; }}
.ck-content {{ max-width: 100%; padding: 0; }}
.ck-content p {{ margin: 0 0 1pt 0; line-height: 1.15; }}
table {{ border-collapse: collapse; width: 100%; }}
td, th {{ border: 1pt solid #ccc; padding: 4pt; }}
th {{ background: #f0f0f0; }}
h1 {{ font-size: {fs+13}pt; margin: 0 0 2pt 0; }} h2 {{ font-size: {fs+9}pt; margin: 0 0 2pt 0; }} h3 {{ font-size: {fs+6}pt; margin: 0 0 2pt 0; }}
h4 {{ font-size: {fs+3}pt; margin: 0 0 1pt 0; }} h5 {{ font-size: {fs+1}pt; margin: 0 0 1pt 0; }} h6 {{ font-size: {fs}pt; margin: 0 0 1pt 0; }}
</style></head><body>
{titolo_html}<div class="ck-content">
{corpo}
</div>
</body></html>'''
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={'width': 794, 'height': 1123})
        page = ctx.new_page()
        page.set_content(html, wait_until='networkidle')
        page.pdf(path=output_path, format='A4',
            margin={'top': '2mm', 'bottom': '2mm', 'left': '5mm', 'right': '5mm'})
        browser.close()


# --- _genera_pdf_da_testo ---

def _genera_pdf_da_testo(tipo, titolo, corpo, output_path, font_family='Arial', font_size=11):
    try:
        return _genera_pdf_da_testo_reportlab(tipo, titolo, corpo, output_path, font_family, font_size)
    except Exception:
        logger.warning("ReportLab fallito per %s, passo a xhtml2pdf", tipo)
    _registra_font_pdf()
    from xhtml2pdf import pisa

    corpo = _pulisci_html_tinymce(corpo)
    corpo = corpo.strip()
    corpo = corpo.replace('\n', '<br/>')
    corpo = re.sub(r'<br\s*/?>', '<br/>', corpo)
    corpo = re.sub(r'(?:<br/>\s*){2,}', '<br/>', corpo)
    corpo = re.sub(r'\{\{LINEA\}\}', '_' * 40, corpo)
    corpo = re.sub(r'\{\{\w+\}\}', '___', corpo)

    rl_font = _rl_font_name(font_family)
    fs_pt = max(8, min(20, int(font_size)))
    html = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
@page {{ size: A4; margin: 10mm 15mm 22mm 15mm; @frame footer_frame {{ -pdf-frame-content: pdfFooterBlock; bottom: 8mm; height: 12mm; left: 15mm; right: 15mm; }} }}
body {{ font-family: '{rl_font}', Arial, Helvetica, sans-serif; font-size: {fs_pt}pt; line-height: 1.35; color: #333; max-width: 100%; }}
h1 {{ font-size: {fs_pt+13}pt; }} h2 {{ font-size: {fs_pt+9}pt; }} h3 {{ font-size: {fs_pt+6}pt; }}
h4 {{ font-size: {fs_pt+3}pt; }} h5 {{ font-size: {fs_pt+1}pt; }} h6 {{ font-size: {fs_pt}pt; }}
table {{ border-collapse: collapse; width: 100%; margin: 2px 0; font-size: {fs_pt}pt; }}
td, th {{ border: 1pt solid #ccc; padding: 2pt 5pt; }}
th {{ background: #f0f0f0; font-weight: bold; }}
ul, ol {{ margin: 2px 0; padding-left: 20px; }}
li {{ margin-bottom: 1px; }}
p {{ margin: 0 0 2px 0; }}
#pdfFooterBlock {{ width: 100%; font-size: 8pt; color: #666; }}
</style></head><body>
{corpo}
</body></html>'''

    buf = io.BytesIO()
    pdf = pisa.pisaDocument(io.StringIO(html), dest=buf)
    if pdf.err:
        return None
    with open(output_path, 'wb') as f:
        f.write(buf.getvalue())
    return buf


# --- _format_pdf_cell ---

def _format_pdf_cell(val):
    if val is None:
        return '\u2014'
    if isinstance(val, bool):
        if val:
            return '\u2713 S\u00ec'
        return '\u2717 No'
    if isinstance(val, float):
        if val == 0:
            return '\u20ac 0,00'
        return f'\u20ac {val:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    if isinstance(val, int) and not isinstance(val, bool):
        return str(val)
    return str(val)


# --- _assicura_cartella_stampe ---

def _assicura_cartella_stampe():
    if not os.path.exists(CARTELLA_STAMPE_TEMP):
        os.makedirs(CARTELLA_STAMPE_TEMP)


# --- _unisci_pdf ---

def _unisci_pdf(pdf_paths, output_path):
    from pypdf import PdfWriter
    merger = PdfWriter()
    try:
        for path in pdf_paths:
            if os.path.exists(path):
                merger.append(path)
        merger.write(output_path)
        merger.close()
        return True
    except Exception:
        logger.exception("Unione PDF fallita")
        try:
            merger.close()
        except Exception:
            logger.warning("Impossibile chiudere merger PDF dopo errore")
        return False


# --- _crea_pagina_bianca ---

def _crea_pagina_bianca():
    from io import BytesIO
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(595.28, 841.89)
    buf = BytesIO()
    writer.write(buf)
    buf.seek(0)
    return buf.read()


# --- _unisci_pdf_bytes ---

def _unisci_pdf_bytes(pdf_bytes_list):
    from io import BytesIO
    from pypdf import PdfWriter, PdfReader
    merger = PdfWriter()
    for data in pdf_bytes_list:
        try:
            reader = PdfReader(BytesIO(data))
            merger.append(reader)
        except Exception:
            logger.exception("Errore in _unisci_pdf_bytes")
            merger.add_blank_page(595.28, 841.89)
    out = BytesIO()
    merger.write(out)
    merger.close()
    out.seek(0)
    return out.read()


# --- _stampa_pdf_windows ---

def _stampa_pdf_windows(path):
    if not os.path.exists(path):
        return False
    try:
        opts = get_opzioni()
        if opts and opts.exe_lettore_pdf and os.path.exists(opts.exe_lettore_pdf):
            subprocess.Popen([opts.exe_lettore_pdf, '/p', path])
            return True
    except Exception:
        logger.warning("Lettore PDF configurato non disponibile per stampa: %s", path)
    try:
        os.startfile(path, 'print')
        return True
    except Exception:
        logger.warning("os.startfile print fallito: %s", path)
    foxit_paths = [
        r'C:\Program Files\Foxit Software\Foxit Reader\FoxitReader.exe',
        r'C:\Program Files (x86)\Foxit Software\Foxit Reader\FoxitReader.exe',
    ]
    for exe in foxit_paths:
        if os.path.exists(exe):
            try:
                subprocess.Popen([exe, '/p', path])
                return True
            except Exception:
                logger.warning("Foxit Reader non disponibile per stampa: %s", exe)
    phantom_paths = [
        r'C:\Program Files\Foxit Software\Foxit PhantomPDF\FoxitPhantomPDF.exe',
    ]
    for exe in phantom_paths:
        if os.path.exists(exe):
            try:
                subprocess.Popen([exe, '/p', path])
                return True
            except Exception:
                logger.warning("Foxit PhantomPDF non disponibile per stampa: %s", exe)
    return False
