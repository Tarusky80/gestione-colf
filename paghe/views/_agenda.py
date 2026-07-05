from paghe.views._common_imports import *
from paghe.models import Appuntamento, ContrattoLavoro, ProgettoRegionale

logger = logging.getLogger(__name__)


class _ScadenzaVirtuale:
    def __init__(self, data, titolo, descrizione='', tipo='SCADENZA', completato=False, ricorrenza='NESSUNA', ora=None, colore=''):
        self.data = data
        self.ora = ora
        self.titolo = titolo
        self.descrizione = descrizione
        self.tipo = tipo
        self.completato = completato
        self.pk = None
        self.virtuale = True
        self.ricorrenza = ricorrenza
        self.colore = colore
    def get_tipo_display(self):
        return dict(Appuntamento.TIPO_CHOICES).get(self.tipo, self.tipo)


def _genera_ricorrenze(anno, mese):
    ricorrenti = Appuntamento.objects.exclude(ricorrenza='NESSUNA').exclude(completato=True)
    risultati = []
    ultimo_giorno = monthrange(anno, mese)[1]
    for app in ricorrenti:
        if app.ricorrenza == 'ANNUALE':
            if app.data.month == mese:
                d = date(anno, mese, min(app.data.day, ultimo_giorno))
                risultati.append(_ScadenzaVirtuale(d, app.titolo, app.descrizione, app.tipo, app.completato))
        elif app.ricorrenza == 'MENSILE':
            d = date(anno, mese, min(app.data.day, ultimo_giorno))
            if d >= app.data:
                risultati.append(_ScadenzaVirtuale(d, app.titolo, app.descrizione, app.tipo, app.completato))
        elif app.ricorrenza == 'SETTIMANALE':
            primo_giorno = date(anno, mese, 1)
            inizio = primo_giorno - timedelta(days=primo_giorno.weekday())
            for i in range(42):
                d = inizio + timedelta(days=i)
                if d.month == mese and d.weekday() == app.data.weekday() and d >= app.data:
                    risultati.append(_ScadenzaVirtuale(d, app.titolo, app.descrizione, app.tipo, app.completato))
    return risultati


SCADENZE_FISSE = [
    (1, 10, 'Contributi 4° trimestre anno precedente', 'Versamento INPS + CAS.SA.COLF codice F2 (MAV unico).'),
    (1, 31, 'Prospetto paga e pagamento retribuzione', 'Art. 33 CCNL — duplice copia, consegna contestuale alla retribuzione.'),
    (2, 31, 'Prospetto paga e pagamento retribuzione', 'Art. 33 CCNL — duplice copia, consegna contestuale alla retribuzione.'),
    (3, 31, 'Rilascio Certificazione Unica', 'Consegna al lavoratore: attestazione somme anno precedente.'),
    (4, 10, 'Contributi 1° trimestre', 'Versamento INPS + CAS.SA.COLF codice F2 (MAV unico).'),
    (4, 30, 'Prospetto paga e pagamento retribuzione', 'Art. 33 CCNL — duplice copia, consegna contestuale alla retribuzione.'),
    (5, 31, 'Prospetto paga e pagamento retribuzione', 'Art. 33 CCNL — duplice copia, consegna contestuale alla retribuzione.'),
    (5, 31, 'Richiesta giorni ferie', '26 giorni lavorativi. Periodo ferie da giugno a settembre.'),
    (6, 30, 'Prospetto paga e pagamento retribuzione', 'Art. 33 CCNL — duplice copia, consegna contestuale alla retribuzione.'),
    (7, 10, 'Contributi 2° trimestre', 'Versamento INPS + CAS.SA.COLF codice F2 (MAV unico).'),
    (7, 31, 'Prospetto paga e pagamento retribuzione', 'Art. 33 CCNL — duplice copia, consegna contestuale alla retribuzione.'),
    (8, 31, 'Prospetto paga e pagamento retribuzione', 'Art. 33 CCNL — duplice copia, consegna contestuale alla retribuzione.'),
    (9, 30, 'Prospetto paga e pagamento retribuzione', 'Art. 33 CCNL — duplice copia, consegna contestuale alla retribuzione.'),
    (10, 10, 'Contributi 3° trimestre', 'Versamento INPS + CAS.SA.COLF codice F2 (MAV unico).'),
    (10, 31, 'Prospetto paga e pagamento retribuzione', 'Art. 33 CCNL — duplice copia, consegna contestuale alla retribuzione.'),
    (10, 31, 'Scadenza invio CU', 'Trasmissione telematica CU all\'Agenzia delle Entrate.'),
    (11, 30, 'Prospetto paga e pagamento retribuzione', 'Art. 33 CCNL — duplice copia, consegna contestuale alla retribuzione.'),
    (11, 30, 'F24 — Seconda rata', 'Versamento seconda rata acconto.'),
    (12, 20, 'Tredicesima mensilità', 'Corrispondere al lavoratore entro dicembre.'),
]


def _genera_scadenze_automatiche(anno, mese):
    scadenze = []
    from calendar import monthrange as _mr
    for m, g, titolo, descrizione in SCADENZE_FISSE:
        if m == mese:
            ultimo = _mr(anno, m)[1]
            g_eff = min(g, ultimo)
            scadenze.append(_ScadenzaVirtuale(date(anno, m, g_eff), titolo, descrizione))
    contratti_cessati = ContrattoLavoro.objects.filter(
        data_fine__year=anno, data_fine__month=mese, stato='ATTIVO'
    ).select_related('datore', 'lavoratore')
    for c in contratti_cessati:
        scadenze.append(_ScadenzaVirtuale(
            c.data_fine,
            f'Cessazione: {c.datore.nome_cognome} / {c.lavoratore.nome_cognome}',
        ))
    progetti_termine = ProgettoRegionale.objects.filter(
        data_fine__year=anno, data_fine__month=mese
    ).select_related('beneficiario', 'tipo')
    for p in progetti_termine:
        scadenze.append(_ScadenzaVirtuale(
            p.data_fine,
            f'Fine progetto: {p.beneficiario.nome_cognome} — {p.tipo}',
        ))
    return scadenze


@login_required
@never_cache
def agenda_page(request):
    opzioni = get_opzioni()
    oggi = date.today()
    anno = int(request.GET.get('anno', oggi.year))
    mese = int(request.GET.get('mese', oggi.month))

    if mese < 1:
        mese, anno = 12, anno - 1
    elif mese > 12:
        mese, anno = 1, anno + 1

    appuntamenti = list(Appuntamento.objects.filter(
        data__year=anno, data__month=mese, ricorrenza='NESSUNA'
    ).order_by('data', 'pk'))
    appuntamenti.extend(_genera_ricorrenze(anno, mese))
    appuntamenti.extend(_genera_scadenze_automatiche(anno, mese))
    appuntamenti.sort(key=lambda a: (a.data, a.pk or 0))

    giorni_mese = monthrange(anno, mese)[1]
    MESI_IT = ['', 'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
                'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']
    mese_nome = MESI_IT[mese]

    prev_mese = mese - 1 or 12
    prev_anno = anno - 1 if mese == 1 else anno
    next_mese = mese + 1 if mese < 12 else 1
    next_anno = anno + 1 if mese == 12 else anno

    primo_giorno = date(anno, mese, 1)
    primo_weekday = primo_giorno.weekday()
    inizio = primo_giorno - timedelta(days=primo_weekday)

    FESTIVI = {
        (1, 1): 'Capodanno', (6, 1): 'Epifania',
        (25, 4): 'Liberazione', (1, 5): 'Festa del Lavoro',
        (2, 6): 'Festa Repubblica', (15, 8): 'Ferragosto',
        (1, 11): 'Ognissanti', (8, 12): 'Immacolata',
        (25, 12): 'Natale', (26, 12): 'S. Stefano',
    }

    app_per_giorno = {}
    for app in appuntamenti:
        app_per_giorno.setdefault(app.data.day, []).append(app)

    giorni_della_settimana = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
    settimane = []
    settimana_corrente = []
    for i in range(42):
        d = inizio + timedelta(days=i)
        nome_festivo = FESTIVI.get((d.day, d.month)) if d.month == mese else None
        giorno = {
            'numero': d.day,
            'oggi': d == oggi,
            'fuori_mese': d.month != mese,
            'data': d,
            'festivo': nome_festivo is not None,
            'nome_festivo': nome_festivo or '',
            'appuntamenti': app_per_giorno.get(d.day, []) if d.month == mese else [],
        }
        settimana_corrente.append(giorno)
        if len(settimana_corrente) == 7:
            settimane.append(settimana_corrente)
            settimana_corrente = []

    conteggio_per_tipo = {'SCADENZA': 0, 'APPUNTAMENTO': 0, 'PROMEMORIA': 0}
    for app in appuntamenti:
        conteggio_per_tipo[app.tipo] = conteggio_per_tipo.get(app.tipo, 0) + 1

    prossime_scadenze = _get_prossime_scadenze(oggi)

    context = {
        'opzioni': opzioni,
        'appuntamenti': appuntamenti,
        'mese': mese,
        'anno': anno,
        'mese_nome': mese_nome,
        'giorni_mese': giorni_mese,
        'prev_mese': prev_mese,
        'prev_anno': prev_anno,
        'next_mese': next_mese,
        'next_anno': next_anno,
        'oggi': oggi,
        'settimane': settimane,
        'giorni_della_settimana': giorni_della_settimana,
        'conteggio_per_tipo': conteggio_per_tipo,
        'oggi_eventi': [a for a in appuntamenti if a.data == oggi],
        'prossime_scadenze': prossime_scadenze,
    }
    return render(request, 'paghe/agenda.html', context)


def _get_prossime_scadenze(oggi):
    tra_3 = oggi + timedelta(days=3)
    scadenze_db = list(Appuntamento.objects.filter(
        tipo='SCADENZA', completato=False, data__gte=oggi, data__lte=tra_3
    ).order_by('data'))
    scadenze_fisse = []
    from calendar import monthrange as _mr
    for m, g, titolo, descrizione in SCADENZE_FISSE:
        ultimo = _mr(oggi.year, m)[1]
        g_eff = min(g, ultimo)
        d = date(oggi.year, m, g_eff)
        if oggi <= d <= tra_3:
            scadenze_fisse.append(_ScadenzaVirtuale(d, titolo, descrizione))
    contratti_ces = ContrattoLavoro.objects.filter(
        data_fine__gte=oggi, data_fine__lte=tra_3, stato='ATTIVO'
    ).select_related('datore', 'lavoratore')
    for c in contratti_ces:
        scadenze_fisse.append(_ScadenzaVirtuale(
            c.data_fine,
            f'Cessazione: {c.datore.nome_cognome} / {c.lavoratore.nome_cognome}',
        ))
    progetti_fine = ProgettoRegionale.objects.filter(
        data_fine__gte=oggi, data_fine__lte=tra_3
    ).select_related('beneficiario', 'tipo')
    for p in progetti_fine:
        scadenze_fisse.append(_ScadenzaVirtuale(
            p.data_fine,
            f'Fine progetto: {p.beneficiario.nome_cognome} — {p.tipo}',
        ))
    tutte = list(scadenze_db) + scadenze_fisse
    tutte.sort(key=lambda a: a.data)
    return tutte


@login_required
@require_http_methods(['POST'])
def ajax_agenda_nuovo(request):
    try:
        ora_raw = request.POST.get('ora') or None
        if ora_raw:
            from datetime import datetime as _dt
            ora_raw = _dt.strptime(ora_raw, '%H:%M').time()
        app = Appuntamento.objects.create(
            data=request.POST.get('data'),
            ora=ora_raw,
            titolo=request.POST.get('titolo'),
            descrizione=request.POST.get('descrizione', ''),
            tipo=request.POST.get('tipo', 'PROMEMORIA'),
            ricorrenza=request.POST.get('ricorrenza', 'NESSUNA'),
            colore=request.POST.get('colore', ''),
        )
        return JsonResponse({'success': True, 'pk': app.pk})
    except Exception as e:
        logger.exception("Errore in ajax_agenda_nuovo")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(['POST'])
def ajax_agenda_toggle(request, pk):
    app = get_object_or_404(Appuntamento, pk=pk)
    app.completato = not app.completato
    app.save(update_fields=['completato'])
    return JsonResponse({'success': True, 'completato': app.completato})


@login_required
@require_http_methods(['POST'])
def ajax_agenda_elimina(request, pk):
    app = get_object_or_404(Appuntamento, pk=pk)
    app.delete()
    return JsonResponse({'success': True})


@login_required
@require_http_methods(['POST'])
def ajax_agenda_modifica(request, pk):
    app = get_object_or_404(Appuntamento, pk=pk)
    try:
        if request.POST.get('data'):
            app.data = request.POST['data']
        if request.POST.get('titolo'):
            app.titolo = request.POST['titolo']
        if request.POST.get('descrizione') is not None:
            app.descrizione = request.POST['descrizione']
        if request.POST.get('tipo'):
            app.tipo = request.POST['tipo']
        if request.POST.get('ricorrenza'):
            app.ricorrenza = request.POST['ricorrenza']
        if request.POST.get('ora'):
            from datetime import datetime as _dt
            app.ora = _dt.strptime(request.POST['ora'], '%H:%M').time()
        elif 'ora' in request.POST:
            app.ora = None
        if request.POST.get('colore') is not None:
            app.colore = request.POST['colore']
        app.save()
        return JsonResponse({'success': True})
    except Exception as e:
        logger.exception("Errore in ajax_agenda_modifica")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(['POST'])
def ajax_agenda_sposta(request, pk):
    app = get_object_or_404(Appuntamento, pk=pk)
    try:
        nuova_data = request.POST.get('data')
        if nuova_data:
            app.data = nuova_data
            app.save(update_fields=['data'])
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': 'Data mancante'})
    except Exception as e:
        logger.exception("Errore in ajax_agenda_sposta")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@never_cache
def agenda_pdf(request):
    oggi = date.today()
    anno = int(request.GET.get('anno', oggi.year))
    mese = int(request.GET.get('mese', oggi.month))
    if mese < 1:
        mese, anno = 12, anno - 1
    elif mese > 12:
        mese, anno = 1, anno + 1

    appuntamenti = list(Appuntamento.objects.filter(
        data__year=anno, data__month=mese, ricorrenza='NESSUNA'
    ).order_by('data', 'pk'))
    appuntamenti.extend(_genera_ricorrenze(anno, mese))
    appuntamenti.extend(_genera_scadenze_automatiche(anno, mese))
    appuntamenti.sort(key=lambda a: (a.data, a.pk or 0))

    mesi_it = ['', 'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
               'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']
    mese_nome = mesi_it[mese]
    FESTIVI = {
        (1, 1): 'Capodanno', (6, 1): 'Epifania',
        (25, 4): 'Liberazione', (1, 5): 'Festa del Lavoro',
        (2, 6): 'Festa Repubblica', (15, 8): 'Ferragosto',
        (1, 11): 'Ognissanti', (8, 12): 'Immacolata',
        (25, 12): 'Natale', (26, 12): 'S. Stefano',
    }

    opzioni = get_opzioni()

    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.platypus.flowables import HRFlowable
    from reportlab.platypus import Image as RLImage
    from paghe.views._helpers import _registra_font_pdf, _risolvi_globali
    import os as _os

    _registra_font_pdf()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        leftMargin=10*mm, rightMargin=10*mm,
        topMargin=6*mm, bottomMargin=6*mm,
    )

    grigio_scuro = HexColor('#333333')
    grigio_medio = HexColor('#666666')
    grigio_bordo = HexColor('#cccccc')
    grigio_riga = HexColor('#e0e0e0')

    s_title = ParagraphStyle('title', fontSize=14, leading=18, textColor=grigio_scuro, fontName='Roboto-Bold', spaceAfter=1, alignment=TA_LEFT)
    s_sub = ParagraphStyle('sub', fontSize=7.5, leading=10, textColor=grigio_medio, fontName='Roboto', alignment=TA_LEFT, spaceAfter=2)
    s_header_cell = ParagraphStyle('hcell', fontSize=7.5, leading=11, textColor=HexColor('#111111'), fontName='Roboto-Bold', alignment=TA_LEFT)
    s_cell = ParagraphStyle('cell', fontSize=7.5, leading=11, textColor=HexColor('#333333'), fontName='Roboto', alignment=TA_LEFT)
    s_piccolo = ParagraphStyle('piccolo', fontSize=6.5, leading=9, textColor=grigio_medio, fontName='Roboto', spaceAfter=0)
    s_footer = ParagraphStyle('footer', fontSize=7, leading=9, textColor=grigio_medio, fontName='Roboto', alignment=TA_CENTER, spaceAfter=0)

    story = []

    # === HEADER (come Liste Stampe) ===
    logo_rl = None
    if opzioni and opzioni.logo_buste_paga and opzioni.logo_buste_paga.path and _os.path.exists(opzioni.logo_buste_paga.path):
        try:
            logo_rl = RLImage(opzioni.logo_buste_paga.path, width=110, height=38)
        except Exception:
            logger.exception("Errore in agenda_pdf")
            logo_rl = None

    titolo = f'AGENDA {mese_nome.upper()} {anno}'
    studio_nome = opzioni.denominazione_studio if opzioni and opzioni.denominazione_studio else ''
    if logo_rl:
        avail = landscape(A4)[0] - 20*mm
        gap = 6*mm
        txt_col_w = avail - 110 - gap
        txt_rows = [[Paragraph(titolo, s_title)]]
        if studio_nome:
            txt_rows.append([Paragraph(studio_nome, s_sub)])
        txt_rows.append([Paragraph(f'Generato il {oggi.strftime("%d/%m/%Y")}', s_sub)])
        txt_sub = Table(txt_rows, colWidths=[txt_col_w])
        txt_sub.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0), ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        header_tbl = Table([[logo_rl, txt_sub]], colWidths=[110, txt_col_w])
        header_tbl.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('LINEAFTER', (0, 0), (0, -1), 1.5, HexColor('#000000')),
            ('RIGHTPADDING', (0, 0), (0, 0), 8), ('LEFTPADDING', (1, 0), (1, -1), 8),
        ]))
        story.append(header_tbl)
    else:
        story.append(Paragraph(titolo, s_title))
        if studio_nome:
            story.append(Paragraph(studio_nome, s_sub))
        story.append(Paragraph(f'Generato il {oggi.strftime("%d/%m/%Y")}', s_sub))
    story.append(Spacer(1, 2))
    story.append(HRFlowable(width="100%", thickness=0.5, color=grigio_bordo, spaceAfter=4))

    # === CALENDAR GRID — stile agenda scrivibile ===
    from calendar import monthrange
    primo_giorno = date(anno, mese, 1)
    primo_weekday = primo_giorno.weekday()
    giorni_mese = monthrange(anno, mese)[1]
    giorni_it = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']

    s_numero = ParagraphStyle('num', fontName='Roboto-Bold', fontSize=11, leading=13, textColor=grigio_scuro, spaceAfter=3)
    s_numero_fest = ParagraphStyle('numf', fontName='Roboto-Bold', fontSize=11, leading=13, textColor=grigio_medio, spaceAfter=3)
    s_hdr = ParagraphStyle('hdr', fontSize=7, leading=9, textColor=grigio_scuro, fontName='Roboto-Bold', alignment=TA_LEFT)
    s_ev = ParagraphStyle('ev', fontSize=6, leading=7.5, textColor=grigio_medio, fontName='Roboto', spaceAfter=0)
    s_linea = ParagraphStyle('linea', fontSize=1, leading=11, textColor=HexColor('#ffffff'), fontName='Roboto', spaceAfter=0)

    intestazioni = [Paragraph(g[:3].upper(), s_hdr) for g in giorni_it]
    app_per_giorno = {}
    for app in appuntamenti:
        app_per_giorno.setdefault(app.data.day, []).append(app)

    cella_vuota = Paragraph('', s_ev)
    righe_tabella = [intestazioni]
    riga_corrente = []
    for i in range(primo_weekday):
        riga_corrente.append(cella_vuota)

    for g in range(1, giorni_mese + 1):
        nome_festivo = FESTIVI.get((g, mese))
        cell_content = []
        num_style = s_numero_fest if nome_festivo else s_numero
        cell_content.append(Paragraph(str(g), num_style))
        eventi = app_per_giorno.get(g, [])
        for app in eventi[:3]:
            ora_str = f'{app.ora.strftime("%H:%M")} ' if app.ora else ''
            cell_content.append(Paragraph(f'{ora_str}{app.titolo}', s_ev))
        if len(eventi) > 3:
            cell_content.append(Paragraph(f'+{len(eventi)-3}', ParagraphStyle('piu', fontName='Roboto-Italic', fontSize=5, leading=6, textColor=grigio_medio, spaceAfter=0)))
        for _ in range(4 if not eventi else 3):
            cell_content.append(Paragraph('&nbsp;', s_linea))
        riga_corrente.append(cell_content)
        archi = (g + primo_weekday) % 7
        if archi == 0 or g == giorni_mese:
            while len(riga_corrente) < 7:
                riga_corrente.append(cella_vuota)
            righe_tabella.append(riga_corrente)
            riga_corrente = []

    page_width = landscape(A4)[0] - 20*mm
    col_w = page_width / 7
    stili_tab = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5), ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]
    for i in range(len(righe_tabella)):
        if i == 0:
            stili_tab.append(('LINEBELOW', (0, i), (-1, i), 0.8, grigio_scuro))
        else:
            stili_tab.append(('LINEBELOW', (0, i), (-1, i), 0.3, grigio_riga))
    for i in range(1, len(righe_tabella)):
        stili_tab.append(('LINEAFTER', (5, i), (6, i), 0.2, HexColor('#e8e8e8')))

    tab = Table(righe_tabella, colWidths=[col_w]*7, repeatRows=1)
    tab.setStyle(TableStyle(stili_tab))
    story.append(tab)

    # === PAGINA 2 — DETTAGLIO EVENTI (retro stampa) ===
    story.append(PageBreak())

    mese_label = f'{mese_nome.capitalize()} {anno}'
    story.append(Paragraph(f'Dettaglio eventi — {mese_label}', ParagraphStyle('pg2title', fontName='Roboto-Bold', fontSize=11, leading=15, textColor=grigio_scuro, spaceAfter=3)))
    if appuntamenti:
        _per_giorno = sorted(appuntamenti, key=lambda a: a.data)
        _gruppi = {}
        for app in _per_giorno:
            _gruppi.setdefault(app.data, []).append(app)
        for d, apps in sorted(_gruppi.items()):
            story.append(Paragraph(f'{d.strftime("%A %d %B %Y").capitalize()}', s_header_cell))
            for app in apps:
                tipo_label = app.get_tipo_display()
                ora_str = f'({app.ora.strftime("%H:%M")}) ' if app.ora else ''
                auto_str = ' (Auto)' if app.virtuale else ''
                colore_marker = ''
                if app.colore:
                    colore_marker = f'<font color="{app.colore}">■ </font>'
                story.append(Paragraph(f'  {colore_marker}[{tipo_label}] {ora_str}{app.titolo}{auto_str}', s_cell))
                if app.descrizione:
                    story.append(Paragraph(f'    {app.descrizione}', s_piccolo))
            story.append(Spacer(1, 3))
    else:
        story.append(Paragraph('Nessun evento in agenda per questo mese.', s_piccolo))
    story.append(Spacer(1, 8))

    # === FOOTER (come Liste Stampe) ===
    story.append(HRFlowable(width="100%", thickness=0.3, color=grigio_bordo, spaceAfter=3))
    _footer_txt = _risolvi_globali('{{FOOTER_DOCUMENTO}}')
    if _footer_txt and _footer_txt.strip():
        _footer_plain = _footer_txt.replace('<br/>', '\n').replace('<br>', '\n').replace('&nbsp;', ' ').replace('&euro;', '\u20ac')
        import re as _re
        _footer_plain = _re.sub(r'<[^>]+>', '', _footer_plain)
        story.append(Paragraph(_footer_plain.strip(), s_footer))

    doc.build(story)
    pdf = buf.getvalue()
    buf.close()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Agenda_{mese_nome}_{anno}.pdf"'
    return response

