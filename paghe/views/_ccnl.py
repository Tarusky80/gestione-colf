"""View per CCNL: full page, PDF Roboto, invio email."""
import io
import re
from pathlib import Path

from paghe.views._common_imports import *
from paghe.models import CcnlArticolo, DatoreLavoro

logger = logging.getLogger('paghe')

NERO_TITOLO = HexColor('#222')
GRIGIO_LIVELLO = HexColor('#444')
NERO_MANSIONE = HexColor('#222')
GRIGIO_MEDIO = HexColor('#555')

# --- Registrazione font Roboto ---
ROBOTO_DIR = Path(__file__).resolve().parent.parent.parent / 'static' / 'fonts' / 'Roboto'
ROBOTO_REGULAR = ROBOTO_DIR / 'Roboto-Regular.ttf'
ROBOTO_BOLD = ROBOTO_DIR / 'Roboto-Bold.ttf'
ROBOTO_ITALIC = ROBOTO_DIR / 'Roboto-Italic.ttf'
ROBOTO_BOLDITALIC = ROBOTO_DIR / 'Roboto-BoldItalic.ttf'

_ROBOTO_REGISTRATO = False


def _registra_roboto():
    global _ROBOTO_REGISTRATO
    if _ROBOTO_REGISTRATO:
        return
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    if ROBOTO_REGULAR.exists():
        pdfmetrics.registerFont(TTFont('Roboto', str(ROBOTO_REGULAR)))
        pdfmetrics.registerFont(TTFont('Roboto-Bd', str(ROBOTO_BOLD)))
        if ROBOTO_ITALIC.exists():
            pdfmetrics.registerFont(TTFont('Roboto-It', str(ROBOTO_ITALIC)))
        if ROBOTO_BOLDITALIC.exists():
            pdfmetrics.registerFont(TTFont('Roboto-BdIt', str(ROBOTO_BOLDITALIC)))
        _ROBOTO_REGISTRATO = True
    else:
        logger.warning('Roboto TTF non trovato in %s, uso Helvetica', ROBOTO_DIR)


def _font_name(bold=False, italic=False):
    if _ROBOTO_REGISTRATO:
        if bold and italic:
            return 'Roboto-BdIt'
        if bold:
            return 'Roboto-Bd'
        if italic:
            return 'Roboto-It'
        return 'Roboto'
    return 'Helvetica'


# --- Parser struttura testo CCNL ---
RE_LISTA_NUM = re.compile(r'^(\d+)\)')
RE_LISTA_LETTERA = re.compile(r'^([a-z])\)')
RE_LIVELLO = re.compile(r'^Livello\b', re.IGNORECASE)
RE_MANSIONE = re.compile(r'^[A-ZÀÈÉÌÒÙ][A-Za-zÀÈÉÌÒÙàèéìòù\s\'-]+:\s*$')


def analizza_testo_ccnl(testo):
    linee = testo.split('\n')
    blocchi = []
    i = 0
    n = len(linee)

    while i < n:
        riga = linee[i].strip()
        if not riga:
            i += 1
            continue

        # Livello header
        if RE_LIVELLO.match(riga) and len(riga) < 30:
            blocchi.append({'tipo': 'livello', 'testo': riga})
            i += 1
            continue

        # Mansione (riga corta che finisce con : o match pattern)
        if riga.endswith(':') and len(riga) < 65:
            titolo = riga[:-1].strip()
            i += 1
            descr_righe = []
            while i < n:
                prox = linee[i].strip()
                if not prox:
                    i += 1
                    break
                if RE_LIVELLO.match(prox) and len(prox) < 30:
                    break
                if prox.endswith(':') and len(prox) < 65:
                    break
                if RE_LISTA_NUM.match(prox):
                    break
                descr_righe.append(prox)
                i += 1
            descrizione = ' '.join(descr_righe)
            blocchi.append({'tipo': 'mansione', 'titolo': titolo, 'descrizione': descrizione})
            continue

        # Elenco numerato 1) 2) ...
        match_num = RE_LISTA_NUM.match(riga)
        if match_num:
            items = []
            while i < n:
                r = linee[i].strip()
                if not r:
                    i += 1
                    break
                if RE_LISTA_NUM.match(r):
                    items.append(re.sub(r'^\d+\)\s*', '', r))
                    i += 1
                else:
                    break
            if items:
                blocchi.append({'tipo': 'elenco_numerato', 'items': items})
            continue

        # Elenco letterale a) b) c) ...
        match_let = RE_LISTA_LETTERA.match(riga)
        if match_let:
            items = []
            while i < n:
                r = linee[i].strip()
                if not r:
                    i += 1
                    break
                if RE_LISTA_LETTERA.match(r):
                    items.append(re.sub(r'^[a-z]\)\s*', '', r))
                    i += 1
                else:
                    break
            if items:
                blocchi.append({'tipo': 'elenco_letterale', 'items': items})
            continue

        # Paragrafo normale (raggruppa righe consecutive)
        par_righe = []
        while i < n:
            r = linee[i].strip()
            if not r:
                i += 1
                break
            if RE_LIVELLO.match(r) and len(r) < 30:
                break
            if r.endswith(':') and len(r) < 65:
                break
            if RE_LISTA_NUM.match(r) or RE_LISTA_LETTERA.match(r):
                break
            par_righe.append(r)
            i += 1
        if par_righe:
            blocchi.append({'tipo': 'paragrafo', 'testo': ' '.join(par_righe)})

    return blocchi


def _formatta_per_html(articolo):
    blocchi = analizza_testo_ccnl(articolo.testo)
    parti = []
    for b in blocchi:
        if b['tipo'] == 'livello':
            parti.append(f'<h4 class="ccnl-livello">{b["testo"]}</h4>')
        elif b['tipo'] == 'mansione':
            desc = b['descrizione'].replace('\n', ' ')
            parti.append(f'<p class="ccnl-mansione"><strong>{b["titolo"]}:</strong> {desc}</p>')
        elif b['tipo'] == 'paragrafo':
            parti.append(f'<p class="ccnl-paragrafo">{b["testo"]}</p>')
        elif b['tipo'] == 'elenco_numerato':
            li = ''.join(f'<li>{item}</li>' for item in b['items'])
            parti.append(f'<ol class="ccnl-elenco">{li}</ol>')
        elif b['tipo'] == 'elenco_letterale':
            li = ''.join(f'<li>{item}</li>' for item in b['items'])
            parti.append(f'<ol class="ccnl-elenco ccnl-elenco-letterale" type="a">{li}</ol>')
    return '\n'.join(parti)


# --- Views ---
@login_required
@permesso_richiesto('contratti.vedi')
def ccnl_list(request):
    articoli = CcnlArticolo.objects.all()
    datori = DatoreLavoro.objects.filter(email__isnull=False).exclude(email='')
    # Pre-render HTML strutturato per ogni articolo
    articoli_dati = []
    for a in articoli:
        articoli_dati.append({
            'articolo': a.articolo,
            'titolo': a.titolo,
            'testo_raw': a.testo,  # per ricerca JS
            'html_formattato': _formatta_per_html(a),
        })
    return render(request, 'paghe/ccnl.html', {
        'articoli': articoli_dati,
        'datori': datori,
        'sezione': 'CCNL',
    })


@login_required
@permesso_richiesto('contratti.vedi')
@xframe_options_exempt
def ccnl_pdf(request):
    _registra_roboto()
    font_name = _font_name()
    font_bold = _font_name(bold=True)
    _font_name(italic=True)

    articoli = CcnlArticolo.objects.all()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=14*mm, bottomMargin=14*mm,
        leftMargin=14*mm, rightMargin=14*mm,
    )

    getSampleStyleSheet()

    stile_titolo_sezione = ParagraphStyle(
        'CcnlTitolo', fontName=font_bold, fontSize=14, leading=17,
        spaceAfter=8, textColor=NERO_TITOLO, alignment=TA_CENTER,
    )
    stile_titolo_articolo = ParagraphStyle(
        'CcnlArt', fontName=font_bold, fontSize=11, leading=13,
        spaceBefore=7, spaceAfter=3, textColor=NERO_TITOLO,
    )
    stile_livello = ParagraphStyle(
        'CcnlLivello', fontName=font_bold, fontSize=10, leading=12,
        spaceBefore=5, spaceAfter=2, textColor=GRIGIO_LIVELLO,
        leftIndent=4,
    )
    ParagraphStyle(
        'CcnlMansioneTit', fontName=font_bold, fontSize=9, leading=11.5,
        textColor=NERO_MANSIONE,
    )
    stile_mansione_desc = ParagraphStyle(
        'CcnlMansioneDesc', fontName=font_name, fontSize=9, leading=11.5,
        textColor=GRIGIO_MEDIO,
    )
    stile_corpo = ParagraphStyle(
        'CcnlCorpo', fontName=font_name, fontSize=8.5, leading=10.5,
        spaceBefore=0, spaceAfter=3, textColor=GRIGIO_MEDIO,
    )
    stile_lista = ParagraphStyle(
        'CcnlLista', fontName=font_name, fontSize=8.5, leading=10.5,
        textColor=GRIGIO_MEDIO, leftIndent=8,
    )

    elements = []
    titolo_sezione = Paragraph('CCNL Lavoro Domestico', stile_titolo_sezione)
    elements.append(titolo_sezione)
    elements.append(Spacer(1, 4))

    for a in articoli:
        titolo = f'Art. {a.articolo} \u2014 {a.titolo}'
        elements.append(Paragraph(titolo, stile_titolo_articolo))

        blocchi = analizza_testo_ccnl(a.testo)
        for b in blocchi:
            if b['tipo'] == 'livello':
                elements.append(Paragraph(b['testo'], stile_livello))
            elif b['tipo'] == 'mansione':
                p = Paragraph(
                    f'<font face="{font_bold}">{b["titolo"]}:</font> {b["descrizione"]}',
                    stile_mansione_desc,
                )
                elements.append(Paragraph(
                    f'<b>{b["titolo"]}:</b> {b["descrizione"]}',
                    stile_corpo,
                ))
            elif b['tipo'] == 'paragrafo':
                elements.append(Paragraph(b['testo'], stile_corpo))
            elif b['tipo'] in ('elenco_numerato', 'elenco_letterale'):
                items = []
                for item_text in b['items']:
                    p = Paragraph(item_text, stile_lista)
                    items.append(ListItem(p))
                lista = ListFlowable(
                    items, bulletFontName=font_name, bulletFontSize=8.5,
                    leftIndent=16, bulletOffsetY=-0.5,
                )
                elements.append(lista)

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="CCNL_Lavoro_Domestico.pdf"'
    return response


@login_required
@permesso_richiesto('contratti.vedi')
@require_POST
def ajax_ccnl_invia_email(request):
    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST.dict()

    datore_ids = data.get('datori', [])
    if isinstance(datore_ids, str):
        datore_ids = [datore_ids]

    if not datore_ids:
        return JsonResponse({'ok': False, 'errore': 'Nessun datore selezionato'})

    try:
        pdf_bytes = _genera_pdf_bytes()
    except Exception as e:
        logger.exception('Errore generazione PDF CCNL')
        return JsonResponse({'ok': False, 'errore': f'Errore generazione PDF: {e}'})

    opzioni = get_opzioni()
    base_docs = (opzioni.cartella_documenti if opzioni and opzioni.cartella_documenti
                 else os.path.join(settings.MEDIA_ROOT, 'documenti'))
    cartella_ccnl = os.path.join(base_docs, 'CCNL')
    os.makedirs(cartella_ccnl, exist_ok=True)
    pdf_path = os.path.join(cartella_ccnl, 'CCNL_Lavoro_Domestico.pdf')
    with open(pdf_path, 'wb') as f:
        f.write(pdf_bytes)

    from paghe.views._invia_email import _invia_via_smtp, _crea_log, _invia_via_thunderbird

    inviati = []
    errori = []
    for did in datore_ids:
        try:
            datore = DatoreLavoro.objects.get(pk=did)
        except DatoreLavoro.DoesNotExist:
            errori.append(f'Datore {did} non trovato')
            continue
        email = datore.email
        if not email:
            errori.append(f'{datore} \u2014 email mancante')
            continue
        try:
            corpo = (
                f'Buongiorno {datore.nome},\n\n'
                f'in allegato il testo integrale del CCNL Lavoro Domestico '
                f'aggiornato.\n\n'
                f'Cordiali saluti,\n{dati_software()}'
            )
            if opzioni and opzioni.email_usa_programma_posta:
                esito = _invia_via_thunderbird(email, 'CCNL Lavoro Domestico', corpo, pdf_path)
            else:
                esito = _invia_via_smtp(email, 'CCNL Lavoro Domestico', corpo, pdf_path, 'CCNL_Lavoro_Domestico.pdf')
            _crea_log(esito.get('ok', False), email, 'CCNL', None, esito.get('errore'), request)
            if esito.get('ok'):
                inviati.append(str(datore))
            else:
                errori.append(f'{datore}: {esito.get("errore", "Errore sconosciuto")}')
        except Exception as e:
            logger.exception("Errore invio CCNL a %s", datore)
            errori.append(f'{datore}: {str(e)[:200]}')

    return JsonResponse({'ok': len(errori) == 0, 'inviati': inviati, 'errori': errori})


def _genera_pdf_bytes():
    _registra_roboto()
    font_bold = _font_name(bold=True)
    font_name = _font_name()

    articoli = CcnlArticolo.objects.all()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=14*mm, bottomMargin=14*mm,
        leftMargin=14*mm, rightMargin=14*mm,
    )
    getSampleStyleSheet()

    stile_titolo_sezione = ParagraphStyle(
        'CcnlTitolo', fontName=font_bold, fontSize=14, leading=17,
        spaceAfter=8, textColor=NERO_TITOLO, alignment=TA_CENTER,
    )
    stile_titolo_articolo = ParagraphStyle(
        'CcnlArt', fontName=font_bold, fontSize=11, leading=13,
        spaceBefore=7, spaceAfter=3, textColor=NERO_TITOLO,
    )
    stile_livello = ParagraphStyle(
        'CcnlLivello', fontName=font_bold, fontSize=10, leading=12,
        spaceBefore=5, spaceAfter=2, textColor=GRIGIO_LIVELLO, leftIndent=4,
    )
    stile_corpo = ParagraphStyle(
        'CcnlCorpo', fontName=font_name, fontSize=8.5, leading=10.5,
        spaceBefore=0, spaceAfter=3, textColor=GRIGIO_MEDIO,
    )
    stile_lista = ParagraphStyle(
        'CcnlLista', fontName=font_name, fontSize=8.5, leading=10.5,
        textColor=GRIGIO_MEDIO, leftIndent=8,
    )

    elements = [Paragraph('CCNL Lavoro Domestico', stile_titolo_sezione), Spacer(1, 4)]

    for a in articoli:
        elements.append(Paragraph(f'Art. {a.articolo} \u2014 {a.titolo}', stile_titolo_articolo))
        for b in analizza_testo_ccnl(a.testo):
            if b['tipo'] == 'livello':
                elements.append(Paragraph(b['testo'], stile_livello))
            elif b['tipo'] == 'mansione':
                elements.append(Paragraph(f'<b>{b["titolo"]}:</b> {b["descrizione"]}', stile_corpo))
            elif b['tipo'] == 'paragrafo':
                elements.append(Paragraph(b['testo'], stile_corpo))
            elif b['tipo'] in ('elenco_numerato', 'elenco_letterale'):
                items = [ListItem(Paragraph(it, stile_lista)) for it in b['items']]
                elements.append(ListFlowable(
                    items, bulletFontName=font_name, bulletFontSize=8.5,
                    leftIndent=16, bulletOffsetY=-0.5,
                ))
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def dati_software():
    from paghe.views._dashboard import _get_opzioni_or_default
    opz = _get_opzioni_or_default()
    nome = getattr(opz, 'nome_programma', 'Gestionale COLF') or 'Gestionale COLF'
    return nome
