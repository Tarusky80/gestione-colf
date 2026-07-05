"""Contributi INPS Lavoro Domestico: HTML + PDF + email."""
import io
from pathlib import Path

from paghe.views._common_imports import *
from paghe.models import DatoreLavoro

logger = logging.getLogger('paghe')

CONTRIBUTI_DATA = {
    'anno': 2026,
    'soglia_ore': 24.9,
    'soglie_paga': [9.61, 11.70],
    'fasce': [
        {
            'codice': 'A',
            'ore_label': '≤ 24,9 h/sett',
            'paga_label': 'fino a € 9,61/h',
            'totale': 1.70,
            'quota_datore': 1.27,
            'quota_lavoratore': 0.43,
            'note': 'Fascia base — sotto entrambe le soglie di paga',
        },
        {
            'codice': 'B',
            'ore_label': '≤ 24,9 h/sett',
            'paga_label': 'da € 9,61 a € 11,70/h',
            'totale': 1.92,
            'quota_datore': 1.44,
            'quota_lavoratore': 0.48,
            'note': 'Paga oraria effettiva compresa tra prima e seconda soglia',
        },
        {
            'codice': 'C',
            'ore_label': '≤ 24,9 h/sett',
            'paga_label': 'oltre € 11,70/h',
            'totale': 2.34,
            'quota_datore': 1.75,
            'quota_lavoratore': 0.59,
            'note': 'Oltre la seconda soglia di paga',
        },
        {
            'codice': 'D',
            'ore_label': '> 24,9 h/sett',
            'paga_label': 'qualsiasi paga',
            'totale': 1.24,
            'quota_datore': 0.93,
            'quota_lavoratore': 0.31,
            'note': 'Oltre soglia ore — fascia unica indipendentemente dalla paga',
        },
    ],
    'note_generali': [
        'La paga effettiva INPS si calcola come: paga_base_oraria + tredicesima_oraria.',
        'Le soglie di paga (€ 9,61 e € 11,70) sono configurabili in Opzioni Software.',
        'La soglia ore (24,9 h/sett) è configurabile in Opzioni Software.',
        'Con quota assegni familiari — valori validi per il 2026.',
        'Le fasce A, B, C si applicano solo se le ore settimanali sono ≤ 24,9.',
        'La fascia D si applica se le ore settimanali superano 24,9, indipendentemente dalla paga.',
    ],
    'riferimenti': [
        'D.Lgs. 151/2015 — Testo Unico sul lavoro domestico',
        'CCNL Lavoro Domestico — Tabella contributi INPS',
        'Circolare INPS n. 1/2026 — Aliquote contributive lavoro domestico',
    ],
}

# --- Helper font PDF ---

_CONTR_ROBOTO_REG = False

def _registra_contr_roboto():
    global _CONTR_ROBOTO_REG
    if _CONTR_ROBOTO_REG:
        return
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    d = Path(__file__).resolve().parent.parent.parent / 'static' / 'fonts' / 'Roboto'
    for n, f in [('Roboto', 'Roboto-Regular.ttf'), ('Roboto-Bd', 'Roboto-Bold.ttf'), ('Roboto-It', 'Roboto-Italic.ttf'), ('Roboto-BdIt', 'Roboto-BoldItalic.ttf')]:
        fp = d / f
        if fp.exists():
            pdfmetrics.registerFont(TTFont(n, str(fp)))
    _CONTR_ROBOTO_REG = True

def _font_contr(bold=False, italic=False):
    if not _CONTR_ROBOTO_REG:
        _registra_contr_roboto()
    if bold and italic:
        return 'Roboto-BdIt'
    if bold:
        return 'Roboto-Bd'
    if italic:
        return 'Roboto-It'
    return 'Roboto'


def _build_contributi_html():
    note = CONTRIBUTI_DATA
    html = ''

    html += '<div class="contr-intro">'
    html += f'<p class="contr-soglie">Soglia ore settimanali: <strong>{note["soglia_ore"]} h</strong> | '
    html += f'Soglie paga oraria effettiva: <strong>€ {note["soglie_paga"][0]} / € {note["soglie_paga"][1]}</strong></p>'
    html += '</div>'

    html += '<table class="contr-tabella"><thead><tr>'
    html += '<th>Fascia</th><th>Ore sett.</th><th>Paga oraria eff.</th><th>Totale €/h</th><th>Q. Datore €/h</th><th>Q. Lavoratore €/h</th><th>Note</th>'
    html += '</tr></thead><tbody>'
    for f in note['fasce']:
        html += '<tr>'
        html += f'<td><span class="contr-badge">{f["codice"]}</span></td>'
        html += f'<td>{f["ore_label"]}</td>'
        html += f'<td>{f["paga_label"]}</td>'
        html += f'<td class="contr-numero"><strong>€ {f["totale"]:.2f}</strong></td>'
        html += f'<td class="contr-numero">€ {f["quota_datore"]:.2f}</td>'
        html += f'<td class="contr-numero">€ {f["quota_lavoratore"]:.2f}</td>'
        html += f'<td class="contr-note">{f["note"]}</td>'
        html += '</tr>'
    html += '</tbody></table>'

    html += '<div class="contr-approfondimento">'
    html += '<h4>Note</h4><ul>'
    for n in note['note_generali']:
        html += f'<li>{n}</li>'
    html += '</ul>'
    html += '<h4>Riferimenti normativi</h4><ul>'
    for r in note['riferimenti']:
        html += f'<li>{r}</li>'
    html += '</ul></div>'
    return html


def _genera_contributi_pdf_bytes(request):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_CENTER
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    _registra_contr_roboto()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=18*mm, bottomMargin=18*mm)

    ACCIAIO = HexColor('#2c5282')
    GRIGIO_SCURO = HexColor('#222')
    GRIGIO_MEDIO = HexColor('#444')

    styles = {
        'title': ParagraphStyle('Titolo', fontName=_font_contr(bold=True), fontSize=17, textColor=GRIGIO_SCURO, spaceAfter=4, alignment=TA_CENTER),
        'subtitle': ParagraphStyle('Sottotitolo', fontName=_font_contr(), fontSize=10, textColor=GRIGIO_MEDIO, spaceAfter=14, alignment=TA_CENTER),
        'soglie': ParagraphStyle('Soglie', fontName=_font_contr(), fontSize=9.5, textColor=GRIGIO_MEDIO, spaceAfter=12, alignment=TA_CENTER),
        'cell_header': ParagraphStyle('CellH', fontName=_font_contr(bold=True), fontSize=8.5, textColor=HexColor('#ffffff'), alignment=TA_CENTER, leading=11),
        'cell_fascia': ParagraphStyle('CellFascia', fontName=_font_contr(bold=True), fontSize=10, textColor=ACCIAIO, alignment=TA_CENTER),
        'cell': ParagraphStyle('Cell', fontName=_font_contr(), fontSize=8.5, textColor=GRIGIO_SCURO, alignment=TA_CENTER, leading=11),
        'cell_text': ParagraphStyle('CellText', fontName=_font_contr(), fontSize=8, textColor=GRIGIO_MEDIO, leading=10.5),
        'cell_numero': ParagraphStyle('CellNumero', fontName=_font_contr(bold=True), fontSize=9, textColor=GRIGIO_SCURO, alignment=TA_CENTER),
        'note_title': ParagraphStyle('NoteTitolo', fontName=_font_contr(bold=True), fontSize=11, textColor=ACCIAIO, spaceBefore=12, spaceAfter=4),
        'note': ParagraphStyle('Nota', fontName=_font_contr(), fontSize=8.5, textColor=GRIGIO_MEDIO, leading=11.5, spaceAfter=2, leftIndent=10),
        'riferimento': ParagraphStyle('Riferimento', fontName=_font_contr(), fontSize=8.5, textColor=GRIGIO_MEDIO, leading=11, spaceAfter=2, leftIndent=10),
    }

    elements = []
    elements.append(Paragraph('Contributi INPS Lavoro Domestico', styles['title']))
    elements.append(Paragraph('Aliquote contributive 2026 — Con quota assegni familiari', styles['subtitle']))
    elements.append(Paragraph(
        f'Soglia ore settimanali: <b>{CONTRIBUTI_DATA["soglia_ore"]} h</b> &nbsp;&nbsp;|&nbsp;&nbsp; '
        f'Soglie paga: <b>\u20ac {CONTRIBUTI_DATA["soglie_paga"][0]} / \u20ac {CONTRIBUTI_DATA["soglie_paga"][1]}</b>',
        styles['soglie']))
    from reportlab.platypus.flowables import HRFlowable
    elements.append(HRFlowable(width='100%', thickness=1.5, color=ACCIAIO, spaceAfter=8, spaceBefore=2))

    header = [
        Paragraph('Fascia', styles['cell_header']),
        Paragraph('Ore sett.', styles['cell_header']),
        Paragraph('Paga oraria eff.', styles['cell_header']),
        Paragraph('Totale \u20ac/h', styles['cell_header']),
        Paragraph('Q. Datore \u20ac/h', styles['cell_header']),
        Paragraph('Q. Lav. \u20ac/h', styles['cell_header']),
        Paragraph('Note', styles['cell_header']),
    ]
    rows = [header]
    for f in CONTRIBUTI_DATA['fasce']:
        rows.append([
            Paragraph(f['codice'], styles['cell_fascia']),
            Paragraph(f['ore_label'], styles['cell']),
            Paragraph(f['paga_label'], styles['cell']),
            Paragraph(f'\u20ac {f["totale"]:.2f}', styles['cell_numero']),
            Paragraph(f'\u20ac {f["quota_datore"]:.2f}', styles['cell']),
            Paragraph(f'\u20ac {f["quota_lavoratore"]:.2f}', styles['cell']),
            Paragraph(f['note'], styles['cell_text']),
        ])

    col_widths = [28, 58, 85, 58, 62, 62, 165]
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCIAIO),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#f8fafc'), HexColor('#ffffff')]),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 10))

    elements.append(HRFlowable(width='100%', thickness=0.8, color=ACCIAIO, spaceAfter=6, spaceBefore=4))
    elements.append(Paragraph('Note', styles['note_title']))
    for n in CONTRIBUTI_DATA['note_generali']:
        elements.append(Paragraph(f'\u2022 {n}', styles['note']))

    elements.append(Paragraph('Riferimenti normativi', styles['note_title']))
    for r in CONTRIBUTI_DATA['riferimenti']:
        elements.append(Paragraph(f'\u2022 {r}', styles['riferimento']))

    doc.build(elements)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes


# --- View per invio email ---

@login_required
@permesso_richiesto('documenti.vedi')
@require_http_methods(['POST'])
def ajax_contributi_ccnl_invia_email(request):
    import json
    data = json.loads(request.body)
    destinatari = data.get('destinatari', [])
    if not destinatari:
        return JsonResponse({'ok': False, 'errore': 'Nessun destinatario selezionato.'})
    pdf_bytes = _genera_contributi_pdf_bytes(request)
    if not pdf_bytes:
        return JsonResponse({'ok': False, 'errore': 'Errore generazione PDF.'})
    from paghe.views._invia_email import invia_documento_email
    risultati = []
    for cf in destinatari:
        try:
            datore = DatoreLavoro.objects.get(pk=cf)
        except DatoreLavoro.DoesNotExist:
            continue
        ok, msg = invia_documento_email(datore, pdf_bytes, 'Contributi_INPS_CCNL.pdf', 'Contributi INPS CCNL')
        risultati.append({'ok': ok, 'cf': cf, 'errore': '' if ok else msg})
    return JsonResponse({'ok': True, 'risultati': risultati})


# --- View lista HTML ---

@login_required
@permesso_richiesto('documenti.vedi')
@xframe_options_exempt
@never_cache
def contributi_ccnl_list(request):
    html_formattato = _build_contributi_html()
    datori = DatoreLavoro.objects.filter(email__isnull=False).exclude(email='')
    return render(request, 'paghe/contributi_ccnl.html', {
        'html_formattato': html_formattato,
        'dati': CONTRIBUTI_DATA,
        'datori': datori,
    })


# --- View PDF ---

@login_required
@permesso_richiesto('documenti.vedi')
@xframe_options_exempt
@never_cache
def contributi_ccnl_pdf(request):
    pdf_bytes = _genera_contributi_pdf_bytes(request)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="Contributi_INPS_CCNL.pdf"'
    return response
