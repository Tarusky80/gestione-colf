"""Tabelle retributive lavoro domestico: HTML + PDF + email."""
import io
from pathlib import Path

from paghe.views._common_imports import *
from paghe.models import DatoreLavoro

logger = logging.getLogger('paghe')

COLONNE_ORDINE = ['A', 'B', 'C', 'D', 'E', 'G', 'H', 'I', 'I_ind', 'L', 'L_orario', 'L_ind']
COLONNE_LABEL = {
    'A': 'Tab. A Conv. (€/mese)',
    'B': 'Tab. B Art.15 (€/mese)',
    'C': 'Tab. C Non Conv. (€/ora)',
    'D': 'Tab. D Ass. Nott. (€/mese)',
    'E': 'Tab. E Pres. Nott. (€/mese)',
    'G': 'Tab. G Art.14 (€/ora)',
    'H': 'Tab. H Baby sitter (€/ora)',
    'I': 'Tab. I (€/ora)',
    'I_ind': 'Indennità I (€)',
    'L': 'Tab. L (€/mese)',
    'L_orario': 'Tab. L (€/ora)',
    'L_ind': 'Indennità L (€)',
}

TABELLE_DATA = {
    2026: {
        'indennita': {'pranzo': '2,33', 'cena': '2,33', 'alloggio': '2,00', 'totale': '6,66'},
        'livelli': {
            'A':              {'A': '908,10', 'C': '6,51'},
            'AS':             {'A': '958,55', 'C': '6,76'},
            'B':              {'A': '983,16', 'B': '702,25', 'C': '7,01', 'L_ind': '30,27'},
            'BS':             {'A': '1.053,39', 'B': '737,39', 'C': '7,45', 'D': '1.211,38', 'E': '138,54', 'G': '97,06', 'H': '0,84', 'L_ind': '30,27'},
            'C':              {'A': '1.123,63', 'B': '814,60', 'C': '7,86'},
            'CS':             {'A': '1.193,84', 'C': '8,30', 'D': '1.372,91', 'E': '8,91', 'G': '119,66', 'H': '0,70', 'L_ind': '30,27'},
            'D':              {'A': '1.404,51', 'B': '207,69', 'C': '9,57'},
            'DS':             {'A': '1.474,73', 'B': '207,69', 'C': '9,97', 'D': '1.695,99', 'E': '10,75', 'G': '119,66', 'H': '0,70'},
            'Livello unico':  {'A': '811,09'},
        },
    },
    2025: {
        'indennita': {'pranzo': '2,31', 'cena': '2,31', 'alloggio': '1,98', 'totale': '6,60'},
        'livelli': {
            'A':              {'A': '736,25', 'C': '5,35'},
            'AS':             {'A': '870,13', 'C': '6,30'},
            'B':              {'A': '937,06', 'B': '669,32', 'C': '6,68', 'L_ind': '9,13'},
            'BS':             {'A': '1.003,99', 'B': '702,81', 'C': '7,10', 'D': '1.154,58', 'E': '132,04', 'G': '92,51', 'H': '0,80', 'L_ind': '11,41'},
            'C':              {'A': '1.070,94', 'B': '776,40', 'C': '7,49'},
            'CS':             {'A': '1.137,86', 'C': '7,91', 'D': '1.308,53', 'E': '8,49', 'G': '114,05', 'H': '0,67', 'L_ind': '11,41'},
            'D':              {'A': '1.338,65', 'B': '197,95', 'C': '9,12'},
            'DS':             {'A': '1.405,58', 'B': '197,95', 'C': '9,50', 'D': '1.616,46', 'E': '10,25', 'G': '114,05', 'H': '0,67'},
            'Livello unico':  {'A': '773,06'},
        },
    },
}

ORDINE_LIVELLI = ['A', 'AS', 'B', 'BS', 'C', 'CS', 'D', 'DS', 'Livello unico']

# --- Helper font PDF ---

_TAB_ROBOTO_REG = False

def _registra_tab_roboto():
    global _TAB_ROBOTO_REG
    if _TAB_ROBOTO_REG:
        return
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    d = Path(__file__).resolve().parent.parent.parent / 'static' / 'fonts' / 'Roboto'
    for n, f in [('Roboto', 'Roboto-Regular.ttf'), ('Roboto-Bd', 'Roboto-Bold.ttf')]:
        fp = d / f
        if fp.exists():
            pdfmetrics.registerFont(TTFont(n, str(fp)))
    _TAB_ROBOTO_REG = True


def _font_tab(bold=False):
    if not _TAB_ROBOTO_REG:
        _registra_tab_roboto()
    return 'Roboto-Bd' if bold else 'Roboto'


def _build_tabelle_html():
    html = ''
    for anno in sorted(TABELLE_DATA.keys(), reverse=True):
        data = TABELLE_DATA[anno]
        html += f'<div class="tab-anno" data-anno="{anno}">'
        html += f'<h3 class="tab-anno-titolo">Anno {anno}</h3>'
        ind = data['indennita']
        html += f'<div class="tab-indennita">Indennità giornaliere: Pranzo € {ind["pranzo"]} | Cena € {ind["cena"]} | Alloggio € {ind["alloggio"]} | Totale € {ind["totale"]}</div>'
        html += '<div class="tab-table-wrapper"><table class="tab-table"><thead><tr><th>Livello</th>'
        for col in COLONNE_ORDINE:
            html += f'<th>{COLONNE_LABEL[col]}</th>'
        html += '</tr></thead><tbody>'
        for lv in ORDINE_LIVELLI:
            row = data['livelli'].get(lv, {})
            html += f'<tr><td class="tab-livello">{lv}</td>'
            for col in COLONNE_ORDINE:
                val = row.get(col, '—')
                html += f'<td>{val}</td>'
            html += '</tr>'
        html += '</tbody></table></div></div>'
    return html


def _genera_tabelle_pdf_bytes(request):
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

    _registra_tab_roboto()
    buf = io.BytesIO()
    pw, ph = landscape(A4)
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
        leftMargin=12*mm, rightMargin=12*mm,
        topMargin=14*mm, bottomMargin=14*mm)

    style_titolo = ParagraphStyle('Titolo', fontName=_font_tab(bold=True), fontSize=14, textColor=HexColor('#2c5282'), spaceAfter=4, alignment=TA_CENTER)
    style_sottotitolo = ParagraphStyle('Sottotitolo', fontName=_font_tab(), fontSize=9, textColor=HexColor('#555'), spaceAfter=10, alignment=TA_CENTER)
    style_indennita = ParagraphStyle('Indennita', fontName=_font_tab(), fontSize=8, textColor=HexColor('#444'), spaceAfter=6, alignment=TA_CENTER)
    style_cell = ParagraphStyle('Cell', fontName=_font_tab(), fontSize=7, textColor=HexColor('#222'), alignment=TA_CENTER, leading=9)
    style_cell_bold = ParagraphStyle('CellBold', fontName=_font_tab(bold=True), fontSize=7, textColor=HexColor('#2c5282'), alignment=TA_CENTER, leading=9)
    style_header = ParagraphStyle('Header', fontName=_font_tab(bold=True), fontSize=6.5, textColor=HexColor('#ffffff'), alignment=TA_CENTER, leading=8)

    elements = []
    elements.append(Paragraph('Tabelle Retributive Lavoro Domestico', style_titolo))
    elements.append(Paragraph('Minimi tabellari CCNL — anni 2025 e 2026', style_sottotitolo))
    elements.append(Spacer(1, 4))

    for anno in sorted(TABELLE_DATA.keys(), reverse=True):
        data = TABELLE_DATA[anno]
        ind = data['indennita']

        if anno < max(TABELLE_DATA.keys()):
            elements.append(PageBreak())

        elements.append(Paragraph(f'Anno {anno}', ParagraphStyle('Anno', fontName=_font_tab(bold=True), fontSize=11, textColor=HexColor('#2c5282'), spaceAfter=4, alignment=TA_LEFT)))
        elements.append(Paragraph(f'Indennità giornaliere: Pranzo € {ind["pranzo"]} | Cena € {ind["cena"]} | Alloggio € {ind["alloggio"]} | Totale € {ind["totale"]}', style_indennita))

        headers = ['Livello'] + [COLONNE_LABEL[c] for c in COLONNE_ORDINE]
        table_data = [[Paragraph(h, style_header) for h in headers]]

        for lv in ORDINE_LIVELLI:
            row_data = data['livelli'].get(lv, {})
            row = [Paragraph(lv, style_cell_bold)]
            for col in COLONNE_ORDINE:
                val = row_data.get(col, '—')
                row.append(Paragraph(val, style_cell))
            table_data.append(row)

        col_w = [22*mm] + [18*mm] * len(COLONNE_ORDINE)
        tbl = Table(table_data, colWidths=col_w, repeatRows=1)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.3, HexColor('#999')),
            ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f9f9f9')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#f9f9f9'), HexColor('#ffffff')]),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        elements.append(tbl)

    doc.build(elements)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes


# --- View invio email ---

@login_required
@permesso_richiesto('documenti.vedi')
@require_http_methods(['POST'])
def ajax_tabelle_invia_email(request):
    import json
    data = json.loads(request.body)
    destinatari = data.get('destinatari', [])
    if not destinatari:
        return JsonResponse({'ok': False, 'errore': 'Nessun destinatario selezionato.'})
    pdf_bytes = _genera_tabelle_pdf_bytes(request)
    if not pdf_bytes:
        return JsonResponse({'ok': False, 'errore': 'Errore generazione PDF.'})
    from paghe.views._invia_email import invia_documento_email
    risultati = []
    for cf in destinatari:
        try:
            datore = DatoreLavoro.objects.get(pk=cf)
        except DatoreLavoro.DoesNotExist:
            continue
        ok, msg = invia_documento_email(datore, pdf_bytes, 'Tabelle_Retributive.pdf', 'Tabelle Retributive Lavoro Domestico')
        risultati.append({'ok': ok, 'cf': cf, 'errore': '' if ok else msg})
    return JsonResponse({'ok': True, 'risultati': risultati})


# --- View lista HTML ---

@login_required
@permesso_richiesto('documenti.vedi')
@xframe_options_exempt
@never_cache
def tabelle_retributive_list(request):
    datori = DatoreLavoro.objects.filter(email__isnull=False).exclude(email='')
    return render(request, 'paghe/tabelle_retributive.html', {
        'anni': sorted(TABELLE_DATA.keys(), reverse=True),
        'colonne_ordine': COLONNE_ORDINE,
        'colonne_label': COLONNE_LABEL,
        'ordine_livelli': ORDINE_LIVELLI,
        'tabelle_data': TABELLE_DATA,
        'datori': datori,
    })


# --- View PDF ---

@login_required
@permesso_richiesto('documenti.vedi')
@xframe_options_exempt
@never_cache
def tabelle_retributive_pdf(request):
    pdf_bytes = _genera_tabelle_pdf_bytes(request)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="Tabelle_Retributive.pdf"'
    return response


# === VERIFICA CONFRONTO CCNL <-> DB ===

from decimal import Decimal, InvalidOperation

CONFRONTO_MAPPING = {
    'A':  ('minimo_mensile_ft', 'diretto'),
    'B':  ('minimo_mensile_pt', 'diretto'),
    'C':  ('paga_base', 'approssimativo'),
    'D':  ('ind_notturno_assistenza', 'diretto'),
    'E':  ('ind_notturno_presenza', 'approssimativo'),
    'G':  ('ind_assistenza_piu_persone_non_conv', 'approssimativo'),
    'H':  ('ind_minori_6_anni_non_conv', 'approssimativo'),
}

CONFRONTO_INDENNITA = {
    'pranzo': 'convivenza_pranzo',
    'cena': 'convivenza_cena',
    'alloggio': 'convivenza_alloggio',
}


def _italian_to_decimal(s):
    if not s or s == '—' or s.strip() == '':
        return None
    try:
        return Decimal(s.strip().replace('.', '').replace(',', '.'))
    except InvalidOperation:
        return None


def _confronta_ccnl_db():
    from paghe.models import ParametriCCNL
    risultati = []
    db_records = {
        (p.anno, p.livello.codice): p
        for p in ParametriCCNL.objects.select_related('livello').all()
    }
    set(ORDINE_LIVELLI)
    db_keys_seen = set()
    anni_ccnl = sorted(TABELLE_DATA.keys(), reverse=True)

    for anno in anni_ccnl:
        data = TABELLE_DATA[anno]
        for lv in ORDINE_LIVELLI:
            row_ccnl = data['livelli'].get(lv, {})
            db_key = lv if lv != 'Livello unico' else None
            db_obj = db_records.get((anno, db_key)) if db_key else None
            if db_key and db_obj:
                db_keys_seen.add((anno, db_key))

            colonne = {}
            for col, (campo_db, tipo) in CONFRONTO_MAPPING.items():
                val_ccnl_str = row_ccnl.get(col)
                val_ccnl = _italian_to_decimal(val_ccnl_str)
                if db_obj:
                    val_db = getattr(db_obj, campo_db, None)
                    if val_db is not None:
                        val_db = Decimal(str(val_db))
                else:
                    val_db = None

                if val_ccnl is None and val_db is None:
                    stato = 'nessuno'
                elif val_ccnl is not None and (val_db is None or val_db == 0):
                    stato = 'solo_ccnl'
                elif val_ccnl is None and val_db is not None and val_db != 0:
                    stato = 'solo_db'
                elif val_ccnl is not None and val_db is not None and val_db != 0:
                    if val_ccnl == val_db:
                        stato = 'ok'
                    else:
                        stato = 'diff'
                else:
                    stato = 'nessuno'

                mostra_db = val_db is not None and val_db != 0
                colonne[col] = {
                    'ccnl': val_ccnl_str or '—',
                    'db': str(val_db) if mostra_db else '—',
                    'stato': stato,
                    'tipo': tipo,
                    'campo_db': campo_db,
                }

            indennita = {}
            for nome, campo_db in CONFRONTO_INDENNITA.items():
                val_ccnl_str = data['indennita'].get(nome)
                val_ccnl = _italian_to_decimal(val_ccnl_str)
                val_db = Decimal(str(getattr(db_obj, campo_db, 0))) if db_obj else None

                if val_ccnl == val_db:
                    stato = 'ok'
                elif val_ccnl is not None and val_db is not None:
                    stato = 'diff'
                elif val_ccnl is not None and val_db is None:
                    stato = 'solo_ccnl'
                else:
                    stato = 'solo_db'

                indennita[nome] = {
                    'ccnl': val_ccnl_str or '—',
                    'db': str(val_db) if val_db is not None else '—',
                    'stato': stato,
                }

            risultati.append({
                'anno': anno,
                'livello': lv,
                'db_presente': db_obj is not None,
                'colonne': colonne,
                'indennita': indennita,
            })

    aggiungi_extra_db(risultati, db_records, db_keys_seen)
    return risultati


def aggiungi_extra_db(risultati, db_records, db_keys_seen):
    for (anno, cod), p in db_records.items():
        if (anno, cod) in db_keys_seen:
            continue
        if cod in ('P',):
            continue
        risultati.append({
            'anno': anno,
            'livello': cod,
            'db_presente': True,
            'extra_db': True,
            'colonne': {},
            'indennita': {},
        })


@login_required
@permesso_richiesto('documenti.vedi')
@never_cache
def verifica_ccnl(request):
    risultati = _confronta_ccnl_db()
    totali = {'ok': 0, 'diff': 0, 'solo_ccnl': 0, 'solo_db': 0, 'non_mappato': 0}
    for r in risultati:
        for col, v in r['colonne'].items():
            s = v['stato']
            if s in totali:
                totali[s] += 1
        for nome, v in r['indennita'].items():
            s = v['stato']
            if s in totali:
                totali[s] += 1

    return render(request, 'paghe/verifica_ccnl.html', {
        'risultati': risultati,
        'totali': totali,
        'colonne_ordine': [c for c in COLONNE_ORDINE if c in CONFRONTO_MAPPING],
        'colonne_label': COLONNE_LABEL,
    })
