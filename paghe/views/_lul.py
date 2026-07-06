"""Modulo _lul — Libro Unico del Lavoro"""
from paghe.views._common_imports import *
from paghe.views._file_utils import _get_cartella_documenti
from paghe.views._gestione_pdf import _registra_font_pdf
from paghe.views._calcoli_core import _calcola_busta_data

logger = logging.getLogger(__name__)


# --- helpers PDF ---


def _genera_lul_pdf_bytes(datore, mese, anno, buste):
    """Genera il PDF del LUL per un datore in un dato mese/anno, stile busta paga.

    Args:
        datore: DatoreLavoro
        mese: int (1-12)
        anno: int
        buste: QuerySet di BustaPaga con select_related + prefetch_related

    Returns:
        bytes del PDF
    """
    _registra_font_pdf()
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable, Image)
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.colors import HexColor
    from io import BytesIO
    import os

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=5*mm, bottomMargin=5*mm,
        leftMargin=20*mm, rightMargin=20*mm,
    )

    # Colori (palette busta paga)
    grigio_scuro = HexColor('#222222')
    grigio_medio = HexColor('#555555')
    grigio_bordo = HexColor('#cccccc')
    grigio_sfondo = HexColor('#f5f5f5')
    grigio_footer = HexColor('#777777')
    acciaio = HexColor('#2c5282')

    # Stili
    s_titolo = ParagraphStyle('Titolo', fontName='Roboto-Bold', fontSize=18,
                              leading=22, textColor=grigio_scuro, spaceAfter=0)
    s_data = ParagraphStyle('Data', fontName='Roboto-Bold', fontSize=16,
                            leading=20, textColor=grigio_scuro, spaceAfter=0, alignment=TA_RIGHT)
    s_subtitle = ParagraphStyle('Sub', fontName='Roboto', fontSize=9,
                                leading=11, textColor=acciaio, spaceAfter=0)
    s_label = ParagraphStyle('Label', fontName='Roboto', fontSize=6.5,
                             leading=8, textColor=grigio_medio, spaceAfter=0)
    s_val = ParagraphStyle('Val', fontName='Roboto-Bold', fontSize=9,
                           leading=11, textColor=grigio_scuro, spaceAfter=0)
    s_secondario = ParagraphStyle('Sec', fontName='Roboto', fontSize=7.5,
                                  leading=9, textColor=grigio_medio, spaceAfter=0)
    s_sezione = ParagraphStyle('Sez', fontName='Roboto-Bold', fontSize=11,
                               leading=13, textColor=acciaio, spaceAfter=4, spaceBefore=2)
    s_th = ParagraphStyle('TH', fontName='Roboto-Bold', fontSize=7.5,
                          leading=9, textColor=grigio_scuro, spaceAfter=0, alignment=TA_CENTER)
    s_th_left = ParagraphStyle('THL', fontName='Roboto-Bold', fontSize=7.5,
                               leading=9, textColor=grigio_scuro, spaceAfter=0, alignment=TA_LEFT)
    ParagraphStyle('TD', fontName='Roboto', fontSize=7.5,
                          leading=9, textColor=grigio_scuro, spaceAfter=0, alignment=TA_CENTER)
    ParagraphStyle('TDL', fontName='Roboto', fontSize=7.5,
                               leading=9, textColor=grigio_scuro, spaceAfter=0, alignment=TA_LEFT)
    s_td_right = ParagraphStyle('TDR', fontName='Roboto', fontSize=7.5,
                                leading=9, textColor=grigio_scuro, spaceAfter=0, alignment=TA_RIGHT)
    s_td_nome = ParagraphStyle('TDN', fontName='Roboto-Bold', fontSize=7.5,
                               leading=9, textColor=grigio_scuro, spaceAfter=0, alignment=TA_LEFT)
    ParagraphStyle('TDCF', fontName='Roboto', fontSize=6.5,
                             leading=8, textColor=grigio_medio, spaceAfter=0, alignment=TA_LEFT)
    s_tot_label = ParagraphStyle('TotL', fontName='Roboto-Bold', fontSize=8.5,
                                 leading=11, textColor=grigio_scuro, spaceAfter=0, alignment=TA_LEFT)
    s_tot_val = ParagraphStyle('TotV', fontName='Roboto-Bold', fontSize=8.5,
                               leading=11, textColor=grigio_scuro, spaceAfter=0, alignment=TA_RIGHT)
    s_prog_label = ParagraphStyle('ProgL', fontName='Roboto-Bold', fontSize=8,
                                  leading=10, textColor=grigio_medio, spaceAfter=2, spaceBefore=4)
    s_prog_val = ParagraphStyle('ProgV', fontName='Roboto', fontSize=7.5,
                                leading=9, textColor=grigio_medio, spaceAfter=0)
    s_nota = ParagraphStyle('Nota', fontName='Roboto', fontSize=7, leading=9,
                            textColor=grigio_medio, spaceAfter=0)
    s_footer = ParagraphStyle('Footer', fontName='Roboto', fontSize=7, leading=9,
                              textColor=grigio_footer, spaceAfter=0, alignment=TA_CENTER)
    s_firma = ParagraphStyle('Firma', fontName='Roboto', fontSize=7, leading=10,
                             textColor=grigio_medio, spaceAfter=0)
    s_firmariga = ParagraphStyle('FirmaR', fontName='Roboto', fontSize=7, leading=10,
                                 textColor=grigio_medio, spaceAfter=0)
    s_sezsm = ParagraphStyle('SezSm', fontName='Roboto-Bold', fontSize=7, leading=9,
                             textColor=grigio_scuro, spaceAfter=2)

    story = []

    # === HEADER ===
    header_data = [[
        Paragraph('LIBRO UNICO DEL LAVORO', s_titolo),
        Paragraph(f'{MESI_IT[mese]} {anno}', s_data),
    ]]
    h_cols = [doc.width * 0.55, doc.width * 0.45]
    t_header = Table(header_data, colWidths=h_cols)
    t_header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_header)
    story.append(HRFlowable(width='100%', thickness=1.5, color=acciaio, spaceAfter=2, spaceBefore=2))
    story.append(Paragraph(
        f'Lavoro Domestico \u2014 {datore.nome_cognome}', s_subtitle
    ))
    story.append(HRFlowable(width='100%', thickness=1.5, color=acciaio, spaceAfter=6, spaceBefore=2))

    # === DATORE INFO ===
    info_rows = []
    info_rows.append([
        Paragraph('DATORE', s_label),
        Paragraph(datore.nome_cognome, s_val),
    ])
    info_rows.append([
        Paragraph('CF', s_label),
        Paragraph(datore.codice_fiscale or '\u2014', s_val),
    ])
    indirizzo_parts = list(filter(None, [
        datore.indirizzo,
        f'{datore.comune} ({datore.provincia})' if datore.comune and datore.provincia else datore.comune or '',
        f'{datore.cap}' if datore.cap else '',
    ]))
    indirizzo = ' \u2014 '.join(indirizzo_parts) if indirizzo_parts else ''
    if indirizzo:
        info_rows.append([
            Paragraph('Indirizzo', s_label),
            Paragraph(indirizzo, s_secondario),
        ])

    col_w = [doc.width * 0.15, doc.width * 0.85]
    t_info = Table(info_rows, colWidths=col_w)
    t_info.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LINEBELOW', (0, 0), (-1, -1), 0.3, HexColor('#dddddd')),
        ('LINEBELOW', (0, -1), (1, -1), 0, HexColor('#dddddd')),
    ]))
    story.append(t_info)

    # === SEPARATORE ===
    story.append(HRFlowable(width='100%', thickness=1.5, color=acciaio, spaceAfter=6, spaceBefore=4))

    # === TABELLA LAVORATORI ===
    story.append(Paragraph('LAVORATORI', s_sezione))

    if not buste:
        story.append(Paragraph('Nessuna busta paga trovata per il periodo indicato.', s_nota))
        doc.build(story)
        pdf = buf.getvalue()
        buf.close()
        return pdf

    # Pre-scan: cassa presente?
    cassa_presente = any(
        float(b.contributi_cassa_totale or 0) != 0 for b in buste
    )

    # Intestazioni colonna
    headers = ['Lavoratore']
    col_aligns = ['LEFT']
    col_pcts = [28]
    if cassa_presente:
        headers += ['Ore', 'Lordo', 'INPS', 'Q.DAT', 'Q.LAV', 'Cassa', 'TFR', 'Netto']
        col_aligns += ['RIGHT'] * 8
        col_pcts += [9, 12, 8, 7, 10, 8, 8, 10]
    else:
        headers += ['Ore', 'Lordo', 'INPS', 'Q.DAT', 'Q.LAV', 'TFR', 'Netto']
        col_aligns += ['RIGHT'] * 7
        col_pcts += [11, 15, 10, 7, 10, 11, 11]

    n_cols = len(headers)
    col_widths = [doc.width * pct / 100 for pct in col_pcts]

    table_data = []
    # Header row
    header_cells = []
    for i, h in enumerate(headers):
        s = s_th_left if i == 0 else s_th
        header_cells.append(Paragraph(h, s))
    table_data.append(header_cells)

    # Data rows
    tot_ore = 0.0
    tot_lordo = 0.0
    tot_inps = 0.0
    tot_qdat = 0.0
    tot_qlav = 0.0
    tot_cassa = 0.0
    tot_tfr = 0.0
    tot_netto = 0.0

    for b in buste:
        lav = b.contratto.lavoratore
        ore = float(b.ore_mensili or 0)
        lordo = float(b.totale_lordo or 0)
        inps = float(b.contributi_inps_totale or 0)
        qdat = float(b.contributi_inps_quota_datore or 0)
        qlav = float(b.contributi_inps_quota_lavoratore or 0)
        cassa = float(b.contributi_cassa_totale or 0)
        tfr = float(b.totale_accantonati or 0)
        netto = float(b.netto or 0)

        tot_ore += ore
        tot_lordo += lordo
        tot_inps += inps
        tot_qdat += qdat
        tot_qlav += qlav
        tot_cassa += cassa
        tot_tfr += tfr
        tot_netto += netto

        cf_label = f'CF: {lav.codice_fiscale or "\u2014"}'
        row = [
            Paragraph(f'{lav.nome_cognome}<br/><font size="6.5" color="#555555">{cf_label}</font>', s_td_nome),
            Paragraph(f'{ore:.2f}', s_td_right),
            Paragraph(f'\u20ac {lordo:.2f}', s_td_right),
            Paragraph(f'\u20ac {inps:.2f}', s_td_right),
            Paragraph(f'\u20ac {qdat:.2f}', s_td_right),
            Paragraph(f'\u20ac {qlav:.2f}', s_td_right),
        ]
        if cassa_presente:
            row.append(Paragraph(f'\u20ac {cassa:.2f}', s_td_right))
        row.append(Paragraph(f'\u20ac {tfr:.2f}', s_td_right))
        row.append(Paragraph(f'\u20ac {netto:.2f}', s_td_right))
        table_data.append(row)

    # Total row
    tot_cells = [
        Paragraph('TOTALE', s_tot_label),
        Paragraph(f'{tot_ore:.2f}', s_tot_val),
        Paragraph(f'\u20ac {tot_lordo:.2f}', s_tot_val),
        Paragraph(f'\u20ac {tot_inps:.2f}', s_tot_val),
        Paragraph(f'\u20ac {tot_qdat:.2f}', s_tot_val),
        Paragraph(f'\u20ac {tot_qlav:.2f}', s_tot_val),
    ]
    if cassa_presente:
        tot_cells.append(Paragraph(f'\u20ac {tot_cassa:.2f}', s_tot_val))
    tot_cells.append(Paragraph(f'\u20ac {tot_tfr:.2f}', s_tot_val))
    tot_cells.append(Paragraph(f'\u20ac {tot_netto:.2f}', s_tot_val))
    table_data.append(tot_cells)

    # Build table style
    base_style = [
        ('FONTNAME', (0, 0), (-1, 0), 'Roboto-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
        ('BACKGROUND', (0, 0), (-1, 0), grigio_sfondo),
        ('BACKGROUND', (0, -1), (-1, -1), grigio_sfondo),
        ('FONTNAME', (0, -1), (-1, -1), 'Roboto-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.3, grigio_bordo),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]
    # First column left-aligned, rest right-aligned
    for i in range(1, n_cols):
        base_style.append(('ALIGN', (i, 0), (i, -1), 'RIGHT'))
    base_style.append(('ALIGN', (0, 0), (0, -1), 'LEFT'))

    t_workers = Table(table_data, colWidths=col_widths, repeatRows=1)
    t_workers.setStyle(TableStyle(base_style))
    story.append(t_workers)

    # === PROGETTI / BENEFICIARI ===
    progetti_rows = []
    for b in buste:
        for p in b.contratto.progetto.all():
            ben = p.beneficiario
            ben_label = f'{ben.nome_cognome}' if ben else '\u2014'
            tipo_label = p.tipo.nome if p.tipo and p.tipo.nome else 'Progetto'
            date_label = ''
            if p.data_inizio:
                date_label += p.data_inizio.strftime('%d/%m/%Y')
            if p.data_fine:
                date_label += f' \u2013 {p.data_fine.strftime("%d/%m/%Y")}'
            progetti_rows.append(
                f'{b.contratto.lavoratore.nome_cognome} \u2192 {tipo_label} '
                f'(ben.: {ben_label}) {date_label}'
            )

    if progetti_rows:
        story.append(Spacer(1, 4))
        story.append(Paragraph('Progetti collegati:', s_prog_label))
        for linea in progetti_rows:
            story.append(Paragraph(f'  {linea}', s_prog_val))

    # === FOOTER ===
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width='100%', thickness=1.5, color=acciaio, spaceAfter=4, spaceBefore=4))
    story.append(Paragraph('DATI STUDIO', s_sezsm))

    opzioni = get_opzioni()
    logo_path = None
    if opzioni and opzioni.logo_buste_paga and hasattr(opzioni.logo_buste_paga, 'path'):
        try:
            lp = opzioni.logo_buste_paga.path
            if lp and os.path.exists(lp):
                logo_path = lp
        except Exception:
            pass

    if logo_path:
        try:
            logo_img = Image(logo_path, width=120, height=40, hAlign='LEFT')
            story.append(logo_img)
        except Exception:
            logo_path = None

    righe_studio = []
    if opzioni:
        if opzioni.denominazione_studio:
            righe_studio.append(opzioni.denominazione_studio)
        if opzioni.telefono_studio:
            righe_studio.append(f'Tel: {opzioni.telefono_studio}')
        if opzioni.email_studio:
            righe_studio.append(opzioni.email_studio)
    righe_studio.append(f'Documento generato il {date.today().strftime("%d/%m/%Y")}')
    story.append(Paragraph(' | '.join(righe_studio), s_nota))

    story.append(Spacer(1, 4))
    story.append(HRFlowable(width='100%', thickness=0.3, color=grigio_bordo, spaceAfter=3))
    story.append(Paragraph(
        'Tutti i diritti riservati. Il presente documento costituisce il Libro Unico del Lavoro '
        'ai sensi del D.Lgs. 151/2015.',
        s_footer
    ))
    story.append(Spacer(1, 6))

    # === FIRMA ===
    story.append(HRFlowable(width='40%', thickness=0.3, color=grigio_bordo, spaceAfter=2))
    story.append(Paragraph('Firma del datore di lavoro', s_firma))
    story.append(Spacer(1, 12))
    story.append(Paragraph('_________________________________________', s_firmariga))

    doc.build(story)
    pdf = buf.getvalue()
    buf.close()
    return pdf


def _crea_buste_mancanti_per_lul(datore, mese, anno):
    """Crea i record BustaPaga mancanti per tutti i contratti attivi del datore.
    Necessario per generare il LUL anche quando nessuna busta e' mai stata salvata.
    """
    contratti = ContrattoAttivo.objects.filter(datore=datore)
    create_count = 0
    for contratto in contratti:
        bp_qs = BustaPaga.objects.filter(contratto=contratto, mese=mese, anno=anno)
        if bp_qs.exists():
            continue
        try:
            ctx = _calcola_busta_data(contratto, mese, anno)
        except Exception as e:
            logger.warning("LUL: impossibile calcolare busta per contratto %s: %s", contratto.pk, e)
            continue
        if 'errore' in ctx:
            continue
        tipo = 'CONVIVENTE' if contratto.is_convivente else 'NON_CONVIVENTE'
        defaults = dict(
            tipo_calcolo=tipo,
            budget_mensile=ctx.get('budget_mensile', 0),
            ore_mensili=ctx.get('ore_mensili', 0),
            ore_inps=ctx.get('ore_inps', 0),
            ore_settimanali=ctx.get('ore_settimanali', 0),
            paga_oraria_lorda=ctx.get('paga_oraria_lorda', 0),
            paga_base_totale=(ctx.get('paga_base') or {}).get('totale', 0),
            totale_indennita=ctx.get('totale_indennita', 0),
            scatti_totale=(ctx.get('scatti_anzianita') or {}).get('valore', 0),
            totale_lordo=ctx.get('totale_lordo', 0),
            contributi_inps_orario=(ctx.get('contributi') or {}).get('inps', {}).get('orario', 0),
            contributi_inps_totale=(ctx.get('contributi') or {}).get('inps', {}).get('totale', 0),
            contributi_inps_fascia=(ctx.get('contributi') or {}).get('inps', {}).get('fascia', ''),
            contributi_inps_quota_datore=(ctx.get('contributi') or {}).get('inps', {}).get('quota_datore_totale', 0),
            contributi_inps_quota_lavoratore=(ctx.get('contributi') or {}).get('inps', {}).get('quota_lavoratore_totale', 0),
            contributi_cassa_orario=(ctx.get('contributi') or {}).get('cassa', {}).get('orario', 0),
            contributi_cassa_totale=(ctx.get('contributi') or {}).get('cassa', {}).get('totale', 0),
            contributi_cassa_nome=(ctx.get('contributi') or {}).get('cassa', {}).get('nome', ''),
            totale_contributi=(ctx.get('contributi') or {}).get('totale', 0),
            convivenza_totale=(ctx.get('trattenute') or {}).get('convivenza', {}).get('totale', 0),
            totale_accantonati=(ctx.get('trattenute') or {}).get('ratei_accantonati', 0),
            netto=ctx.get('netto', 0),
            indennita_json=ctx.get('indennita', []),
            ratei_pagati_json=ctx.get('ratei_pagati', []),
            scatti_dettaglio_json=ctx.get('scatti_anzianita', {}),
            progetti_json=ctx.get('progetti', []),
        )
        BustaPaga.objects.update_or_create(
            contratto=contratto, mese=mese, anno=anno,
            defaults=defaults
        )
        create_count += 1
    if create_count > 0:
        logger.info("LUL: create %d BustaPaga mancanti per datore %s (mese=%02d/%d)", create_count, datore, mese, anno)
    return create_count


def _trova_o_genera_lul(datore, mese, anno, request=None):
    """Trova un LUL esistente o lo genera per datore/mese/anno.

    Returns:
        (bytes, DocumentoArchiviato or None)
    """
    # Cerca documento esistente
    lul_doc = DocumentoArchiviato.objects.filter(
        tipo='LUL', datore=datore,
        titolo__icontains=f"{mese:02d}/{anno}"
    ).first()
    if lul_doc and lul_doc.file_path and os.path.exists(lul_doc.file_path):
        with open(lul_doc.file_path, 'rb') as f:
            return f.read(), lul_doc

    # Genera nuovo LUL
    buste = BustaPaga.objects.filter(
        contratto__datore=datore, mese=mese, anno=anno
    ).select_related(
        'contratto__lavoratore',
    ).prefetch_related(
        'contratto__progetto__beneficiario',
        'contratto__progetto__tipo',
    ).order_by('contratto__lavoratore__nome_cognome')
    if not buste.exists():
        _crea_buste_mancanti_per_lul(datore, mese, anno)
        buste = BustaPaga.objects.filter(
            contratto__datore=datore, mese=mese, anno=anno
        ).select_related(
            'contratto__lavoratore',
        ).prefetch_related(
            'contratto__progetto__beneficiario',
            'contratto__progetto__tipo',
        ).order_by('contratto__lavoratore__nome_cognome')
        if not buste.exists():
            return None, None

    pdf_lul = _genera_lul_pdf_bytes(datore, mese, anno, buste)

    # Salva su disco
    cartella = os.path.join(_get_cartella_documenti(), 'LUL')
    os.makedirs(cartella, exist_ok=True)
    safe_name = datore.nome_cognome.replace(' ', '_').replace('/', '_')
    nome_file = f"LUL_{safe_name}_{mese:02d}_{anno}.pdf"
    full_path = os.path.join(cartella, nome_file)
    with open(full_path, 'wb') as f:
        f.write(pdf_lul)

    lul_doc = DocumentoArchiviato.objects.create(
        tipo='LUL',
        titolo=f"LUL {datore.nome_cognome} {mese:02d}/{anno}",
        file_path=full_path,
        file_size=len(pdf_lul),
        file_name=nome_file,
        datore=datore,
    )
    return pdf_lul, lul_doc


def _concatena_lul_a_busta(pdf_busta, contratto, mese, anno):
    """Concatena il PDF del LUL (datore del contratto) dopo la busta paga.

    Args:
        pdf_busta: bytes del PDF busta paga
        contratto: ContrattoLavoro (per risalire al datore)
        mese, anno: int

    Returns:
        bytes del PDF concatenato (solo busta se LUL non disponibile)
    """
    datore = contratto.datore
    pdf_lul, _ = _trova_o_genera_lul(datore, mese, anno)
    if not pdf_lul:
        return pdf_busta

    from pypdf import PdfWriter, PdfReader
    from io import BytesIO
    merger = PdfWriter()
    merger.append(PdfReader(BytesIO(pdf_busta)))
    merger.append(PdfReader(BytesIO(pdf_lul)))
    output = BytesIO()
    merger.write(output)
    return output.getvalue()


# === VIEWS ===

@login_required
@permesso_richiesto('buste.vedi')
@never_cache
def lul_list(request):
    """Elenco LUL generati, con filtri anno/datore."""
    anno = request.GET.get('anno', str(date.today().year))
    try:
        anno = int(anno)
    except (ValueError, TypeError):
        anno = date.today().year

    # Filtri
    datori = filtro_visibilita(DatoreLavoro.objects.all(), request.user).order_by('nome_cognome')
    lul_docs = DocumentoArchiviato.objects.filter(tipo='LUL').select_related('datore').order_by('-creato_il')

    datore_id = request.GET.get('datore', '')
    if datore_id:
        lul_docs = lul_docs.filter(datore_id=datore_id)

    # Filtra per anno dal titolo (es. "LUL Mario Rossi 06/2026")
    lul_docs = [d for d in lul_docs if f"/{anno}" in d.titolo]

    anni_disponibili = range(date.today().year, date.today().year - 5, -1)

    return render(request, 'paghe/lul_list.html', {
        'datori': datori,
        'lul_docs': lul_docs,
        'anno': anno,
        'datore_id': datore_id,
        'anni_disponibili': anni_disponibili,
        'MESI_IT': MESI_IT,
        'mese_default': date.today().month,
        'opzioni': get_opzioni(),
    })


@login_required
@permesso_richiesto('buste.calcola')
@require_POST
def ajax_genera_lul(request):
    """Genera LUL per datore/mese/anno. RESTituisce JSON con esito."""
    try:
        datore_id = request.POST.get('datore_id', '')  # PK stringa (codice_fiscale)
        mese = int(request.POST.get('mese', 0))
        anno = int(request.POST.get('anno', 0))
    except (ValueError, TypeError):
        return JsonResponse({'errore': 'Parametri non validi'}, status=400)

    if not datore_id:
        return JsonResponse({'errore': 'Seleziona un datore di lavoro.'}, status=400)

    datore = get_object_or_404(DatoreLavoro, pk=datore_id)
    if not ha_permesso(request.user, 'anagrafiche.vedi_tutti') and request.user not in datore.visibile_a.all():
        return JsonResponse({'errore': 'Permesso negato'}, status=403)

    if not (1 <= mese <= 12):
        return JsonResponse({'errore': 'Mese non valido'}, status=400)

    pdf_lul, doc = _trova_o_genera_lul(datore, mese, anno, request)
    if not pdf_lul:
        return JsonResponse({'errore': 'Nessuna busta paga trovata per il periodo indicato.'}, status=404)

    return JsonResponse({
        'ok': True,
        'documento_pk': doc.pk,
        'titolo': doc.titolo,
        'url': f'/ajax/vedi-documento/{doc.pk}/',
    })


@login_required
@permesso_richiesto('documenti.elimina')
@require_POST
def ajax_elimina_lul(request):
    """Elimina un LUL (DocumentoArchiviato) con verifica visibilità datore."""
    try:
        doc_pk = int(request.POST.get('documento_pk', 0))
    except (ValueError, TypeError):
        return JsonResponse({'errore': 'Parametro non valido'}, status=400)

    doc = get_object_or_404(DocumentoArchiviato, pk=doc_pk, tipo='LUL')

    if not ha_permesso(request.user, 'anagrafiche.vedi_tutti'):
        if doc.datore and request.user not in doc.datore.visibile_a.all():
            return JsonResponse({'errore': 'Permesso negato'}, status=403)

    # Elimina file fisico su disco
    if doc.file_path:
        try:
            import os
            if os.path.isfile(doc.file_path):
                os.remove(doc.file_path)
        except Exception:
            pass

    doc.delete()
    return JsonResponse({'ok': True})
