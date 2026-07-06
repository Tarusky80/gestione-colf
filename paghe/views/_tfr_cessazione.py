"""Modulo _tfr_cessazione - generato automaticamente da views.py"""

from paghe.views._common_imports import *

logger = logging.getLogger(__name__)

from paghe.views._helpers import _get_cartella_documenti, _registra_font_pdf
from paghe.views._calcoli_core import _calcola_busta_data
from paghe.views._buste_pdf import _genera_busta_completa_pdf_bytes




# --- _calcola_tfr_fino_a ---

def _calcola_tfr_fino_a(contratto, data_fine):
    """Calcola TFR cumulativo fino a data_fine (ultimo giorno del mese).
    Restituisce (mesi, tfr_mensile, totale)."""
    if contratto.modalita_tfr == 'INCLUSO':
        return (0, 0, 0)
    p = contratto.parametri_minimi
    if not p:
        return (0, 0, 0)
    ore_m = contratto.ore_mensili_calcolate
    if ore_m <= 0:
        return (0, 0, 0)
    coeff = 0.3 if contratto.modalita_tfr == 'SEPARATO_70' else 1.0
    tfr_mensile = round(float(p.tfr_orario) * ore_m * coeff, 4)
    data_inizio = contratto.data_inizio_tfr or contratto.data_assunzione
    if not data_inizio or data_fine < data_inizio:
        return (0, tfr_mensile, 0)
    mesi = (data_fine.year - data_inizio.year) * 12 + (data_fine.month - data_inizio.month) + 1
    if mesi <= 0:
        mesi = 0
    totale = round(tfr_mensile * mesi, 2)
    return (mesi, tfr_mensile, totale)


# --- _build_liquidazione_tfr_pdf_bytes ---


def _build_liquidazione_tfr_pdf_bytes(contratto, data_inizio_eff, data_fine, mesi, tfr_mensile, cumulativo, tfr_orario, ore_m, coeff):
    """Costruisce PDF Liquidazione TFR in stile busta paga.
       Restituisce (pdf_bytes, nome_file_disk)."""
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle, Image
    import os

    _registra_font_pdf()
    grigio_scuro = HexColor('#222222')
    grigio_medio = HexColor('#555555')
    grigio_label = HexColor('#555555')
    grigio_footer = HexColor('#777777')
    grigio_bordo = HexColor('#cccccc')
    HexColor('#f5f5f5')
    acciaio = HexColor('#2c5282')
    HexColor('#dce6f0')

    s_h1 = ParagraphStyle('H1', fontSize=18, leading=22, textColor=grigio_scuro, fontName='Roboto-Bold', spaceAfter=0)
    ParagraphStyle('H2', fontSize=8, leading=10, textColor=grigio_medio, fontName='Roboto', spaceAfter=6)
    s_label = ParagraphStyle('label', fontSize=6.5, leading=8, textColor=grigio_label, fontName='Roboto', spaceAfter=0)
    s_val = ParagraphStyle('val', fontSize=9, leading=12, textColor=grigio_scuro, fontName='Roboto-Bold', spaceAfter=0)
    s_val_grigio = ParagraphStyle('valg', fontSize=7.5, leading=10, textColor=grigio_medio, fontName='Roboto', spaceAfter=0)
    s_item_label = ParagraphStyle('iteml', fontSize=8, leading=11, textColor=grigio_scuro, fontName='Roboto', spaceAfter=0)
    s_item_val = ParagraphStyle('itemv', fontSize=8.5, leading=11, textColor=grigio_scuro, fontName='Roboto-Bold', spaceAfter=0)
    s_total_label = ParagraphStyle('totlbl', fontSize=9, leading=12, textColor=acciaio, fontName='Roboto-Bold', spaceAfter=0)
    s_total_val = ParagraphStyle('totval', fontSize=10, leading=12, textColor=grigio_scuro, fontName='Roboto-Bold', spaceAfter=0)
    ParagraphStyle('netlbl', fontSize=11, leading=14, textColor=acciaio, fontName='Roboto-Bold', spaceAfter=0)
    ParagraphStyle('netval', fontSize=15, leading=18, textColor=acciaio, fontName='Roboto-Bold', spaceAfter=0)
    s_sezione = ParagraphStyle('sez', fontSize=7.5, leading=10, textColor=acciaio, fontName='Roboto-Bold', spaceAfter=0)
    s_std_sub = ParagraphStyle('stdsub', fontSize=7, leading=9, textColor=acciaio, fontName='Roboto-Bold', spaceAfter=0, alignment=TA_LEFT)
    s_extra = ParagraphStyle('extra', fontSize=7, leading=10, textColor=grigio_medio, fontName='Roboto', spaceAfter=1)
    ParagraphStyle('footer', fontSize=7, leading=9, textColor=grigio_footer, fontName='Roboto', alignment=TA_CENTER)

    def _fmt_eur(v):
        return ("€ %s" % ("{:,.2f}".format(v).replace(',', 'X').replace('.', ',').replace('X', '.')))

    def _row(label, value, small=''):
        l = f"{label} <font size='7' color='#666666'>{small}</font>" if small else label
        return [Paragraph(l, s_item_label), Paragraph(_fmt_eur(value), s_item_val)]

    def _total_row(label, value):
        return [Paragraph(f"<b>{label}</b>", s_total_label), Paragraph(f"<b>{_fmt_eur(value)}</b>", s_total_val)]

    def _val_row(label, value, unit=''):
        suffix = f" <font size='7' color='#666666'>({unit})</font>" if unit else ''
        return [Paragraph(f"{label}{suffix}", s_item_label), Paragraph(f"{value}", s_item_val)]

    buf = BytesIO()
    opzioni = get_opzioni()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=5*mm, bottomMargin=5*mm, leftMargin=20*mm, rightMargin=20*mm)
    story = []

    header_table = Table([
        [Paragraph('LIQUIDAZIONE TFR', s_h1),
         Paragraph('Fondo trattamento di fine rapporto', ParagraphStyle('h2right', fontSize=16, leading=20, textColor=grigio_scuro, fontName='Roboto-Bold', alignment=TA_RIGHT))]
    ], colWidths=[doc.width*0.5, doc.width*0.5])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, 0), (-1, -1), 1.5, acciaio),
        ('LEFTPADDING', (0, 0), (0, 0), 0),
        ('RIGHTPADDING', (1, 0), (1, 0), 0),
    ]))
    story.append(header_table)
    sub_table = Table([[Paragraph(f"{contratto.datore.nome_cognome} - {contratto.lavoratore.nome_cognome}", s_std_sub)]], colWidths=[doc.width])
    sub_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(sub_table)
    line_table = Table([['']], colWidths=[doc.width])
    line_table.setStyle(TableStyle([('LINEBELOW', (0, 0), (-1, 0), 1.5, acciaio)]))
    story.append(line_table)
    story.append(Spacer(1, 6))

    info_data = [
        [Paragraph('DATORE', s_label), Paragraph(f"{contratto.datore.nome_cognome}", s_val),
         Paragraph('LAVORATORE', s_label), Paragraph(f"{contratto.lavoratore.nome_cognome}", s_val)],
        [Paragraph('CF DATORE', s_label), Paragraph(contratto.datore.codice_fiscale or '—', s_val_grigio),
         Paragraph('CF LAVORATORE', s_label), Paragraph(contratto.lavoratore.codice_fiscale or '—', s_val_grigio)],
        [Paragraph('PERIODO MATURAZIONE', s_label),
         Paragraph(f'{data_inizio_eff.strftime("%d/%m/%Y")} – {data_fine.strftime("%d/%m/%Y")}', s_val),
         Paragraph('MESI TRASCORSI', s_label), Paragraph(str(mesi), s_val)],
        [Paragraph('ORE MENSILI', s_label), Paragraph(str(int(ore_m)), s_val),
         Paragraph('TFR ORARIO', s_label),
         Paragraph(f'€ {tfr_orario:.4f}  ({coeff*100:.0f}% accantonato)', s_val)],
        [Paragraph('MODALITÀ TFR', s_label), Paragraph(contratto.get_modalita_tfr_display(), s_val),
         Paragraph('RATEO MENSILE', s_label), Paragraph(f'€ {tfr_mensile:.4f}', s_val)],
    ]
    info_tbl = Table(info_data, colWidths=[doc.width*0.17, doc.width*0.33, doc.width*0.17, doc.width*0.33])
    info_tbl.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, grigio_bordo),
        ('LINEBELOW', (0, 1), (-1, 1), 0.5, grigio_bordo),
        ('LINEBELOW', (0, 2), (-1, 2), 0.5, grigio_bordo),
        ('LINEBELOW', (0, 3), (-1, 3), 0.5, grigio_bordo),
        ('LINEBELOW', (0, 4), (-1, 4), 0.5, grigio_bordo),
    ]))
    story.append(info_tbl)
    story.append(Spacer(1, 8))

    calc_rows = []
    calc_rows.append(_row("TFR orario", tfr_orario, f"{coeff*100:.0f}% accantonato"))
    calc_rows.append(_val_row("Ore mensili", f"{int(ore_m)} h"))
    calc_rows.append(_row("Rateo mensile", tfr_mensile))
    calc_rows.append(_val_row("Mesi di maturazione", str(mesi)))
    calc_rows.append(['', ''])
    calc_rows.append(_total_row("TOTALE TFR ACCANTONATO", cumulativo))
    t_calcolo = Table(calc_rows, colWidths=[doc.width*0.35, doc.width*0.15])
    t_calcolo.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LINEBELOW', (0, 0), (0, len(calc_rows)-3), 0.5, grigio_bordo),
        ('LINEABOVE', (0, len(calc_rows)-1), (1, len(calc_rows)-1), 2, acciaio),
        ('LINEBELOW', (0, len(calc_rows)-1), (1, len(calc_rows)-1), 0.5, grigio_bordo),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('RIGHTPADDING', (1, 0), (1, -1), 0),
    ]))
    col_sx = [Paragraph("DETTAGLIO LIQUIDAZIONE TFR", s_sezione), Spacer(1, 2), t_calcolo]

    riep_rows = []
    riep_rows.append(_val_row("Mesi trascorsi", str(mesi)))
    riep_rows.append(_val_row("Ore mensili", f"{int(ore_m)} h"))
    riep_rows.append(_row("Rateo mensile", tfr_mensile))
    riep_rows.append(['', ''])
    note_style = ParagraphStyle('nota', fontSize=6.5, leading=9, textColor=grigio_footer, fontName='Roboto-Italic')
    if contratto.modalita_tfr == 'SEPARATO_70':
        riep_rows.append([Paragraph("<i>70% già corrisposto in busta paga.</i>", note_style), Paragraph('', s_item_val)])
    else:
        riep_rows.append([Paragraph("<i>100% interamente accantonato.</i>", note_style), Paragraph('', s_item_val)])
    t_riep = Table(riep_rows, colWidths=[doc.width*0.35, doc.width*0.15])
    t_riep.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LINEBELOW', (0, 0), (0, len(riep_rows)-1), 0.5, grigio_bordo),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('RIGHTPADDING', (1, 0), (1, -1), 0),
    ]))
    col_dx = [Paragraph("RIEPILOGO", s_sezione), Spacer(1, 2), t_riep]

    layout = Table([[col_sx, col_dx]], colWidths=[doc.width*0.48, doc.width*0.52])
    layout.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (0, 0), 0),
        ('RIGHTPADDING', (1, 0), (1, 0), 0),
        ('LEFTPADDING', (1, 0), (1, 0), 12),
    ]))
    story.append(layout)
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        f"Firma del lavoratore <b>{contratto.lavoratore.nome_cognome}</b> per ricevuta e conferma delle "
        f"ore lavorate e retribuite e quietanza dell'importo indicato.",
        ParagraphStyle('firma', fontSize=7, leading=10, textColor=grigio_medio, fontName='Roboto', spaceAfter=0)))
    story.append(Spacer(1, 24))
    story.append(Paragraph(
        f"Il collaboratore familiare <b>{contratto.lavoratore.nome_cognome}</b> "
        f"<u>{'_' * 55}</u>",
        ParagraphStyle('firmariga', fontSize=7, leading=10, textColor=grigio_medio, fontName='Roboto', spaceAfter=0)))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width='100%', thickness=0.3, color=grigio_bordo, spaceAfter=4))

    story.append(Paragraph("DATI STUDIO", ParagraphStyle('sezsm', fontSize=7, leading=9, textColor=grigio_scuro, fontName='Roboto-Bold', spaceAfter=0)))
    story.append(Spacer(1, 2))
    if opzioni:
        if opzioni.logo_buste_paga and opzioni.logo_buste_paga.path and os.path.exists(opzioni.logo_buste_paga.path):
            try:
                logo_img = Image(opzioni.logo_buste_paga.path, width=120, height=40, hAlign='LEFT')
                story.append(logo_img)
            except Exception:
                logger.warning("Impossibile caricare logo TFR cessazione: %s", getattr(opzioni.logo_buste_paga, 'path', ''))
        studio_parts = []
        if opzioni.dati_studio:
            studio_parts.append(opzioni.dati_studio)
        if opzioni.telefono_studio:
            studio_parts.append(f"Tel: {opzioni.telefono_studio}")
        if opzioni.email_studio:
            studio_parts.append(f"Mail: {opzioni.email_studio}")
        if studio_parts:
            story.append(Paragraph(' | '.join(studio_parts), s_extra))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width='100%', thickness=0.5, color=grigio_scuro, spaceAfter=3))
    story.append(Paragraph(
        f"Tutti i diritti riservati: \u00e8 vietata la riproduzione, anche parziale, dei contenuti. "
        f"| Stampata il {date.today().strftime('%d/%m/%Y')}",
        s_extra))

    doc.build(story)
    pdf = buf.getvalue()
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    safe_name = contratto.lavoratore.nome_cognome.replace(' ', '_').replace('/', '_')
    nome_file_disk = f"liquidazione_tfr_{safe_name}_{timestamp}.pdf"
    return pdf, nome_file_disk


# --- liquidazione_tfr ---
@login_required
@permesso_richiesto('buste.calcola')
@xframe_options_exempt
def liquidazione_tfr(request, pk):
    import os, calendar

    contratto = get_object_or_404(ContrattoAttivo, pk=pk)
    if contratto.modalita_tfr == 'INCLUSO':
        return HttpResponse('TFR incluso nel lordo — nessun accantonamento da liquidare.', status=400)

    data_inizio_str = request.GET.get('data_inizio')
    mese_req = request.GET.get('mese')
    anno_req = request.GET.get('anno')
    oggi = date.today()

    if mese_req and anno_req:
        try:
            mese_fine = int(mese_req); anno_fine = int(anno_req)
        except (ValueError, TypeError):
            mese_fine, anno_fine = oggi.month, oggi.year
    else:
        mese_fine, anno_fine = oggi.month, oggi.year
    ultimo_giorno = calendar.monthrange(anno_fine, mese_fine)[1]
    data_fine = date(anno_fine, mese_fine, ultimo_giorno)

    if data_inizio_str:
        try:
            data_inizio_scelta = date.fromisoformat(data_inizio_str)
        except (ValueError, TypeError):
            data_inizio_scelta = max(date(oggi.year, 1, 1), contratto.data_assunzione or date(oggi.year, 1, 1))
    else:
        data_inizio_scelta = max(date(oggi.year, 1, 1), contratto.data_assunzione or date(oggi.year, 1, 1))

    data_inizio_eff = max(data_inizio_scelta, contratto.data_inizio_tfr or contratto.data_assunzione or data_inizio_scelta)

    mesi, tfr_mensile, cumulativo = _calcola_tfr_fino_a(contratto, data_fine)
    if data_inizio_eff > (contratto.data_inizio_tfr or contratto.data_assunzione):
        _dummy, _dummy2, cumulativo = _calcola_tfr_fino_a(contratto, data_fine)
        p = contratto.parametri_minimi
        ore_m = contratto.ore_mensili_calcolate
        coeff = 0.3 if contratto.modalita_tfr == 'SEPARATO_70' else 1.0
        tfr_mensile = round(float(p.tfr_orario) * ore_m * coeff, 4) if p else 0
        if data_fine >= data_inizio_eff:
            mesi = (data_fine.year - data_inizio_eff.year) * 12 + (data_fine.month - data_inizio_eff.month) + 1
        else:
            mesi = 0
        cumulativo = round(tfr_mensile * mesi, 2)

    if cumulativo <= 0:
        return HttpResponse('Nessun importo TFR accantonato da liquidare.', status=400)

    p = contratto.parametri_minimi
    ore_m = contratto.ore_mensili_calcolate
    coeff = 0.3 if contratto.modalita_tfr == 'SEPARATO_70' else 1.0
    tfr_mensile = round(float(p.tfr_orario) * ore_m * coeff, 4) if p else 0
    tfr_orario = float(p.tfr_orario) if p else 0

    pdf, nome_file_disk = _build_liquidazione_tfr_pdf_bytes(contratto, data_inizio_eff, data_fine, mesi, tfr_mensile, cumulativo, tfr_orario, ore_m, coeff)

    cartella = _get_cartella_documenti(contratto)
    full_path = os.path.join(cartella, nome_file_disk)
    with open(full_path, 'wb') as f:
        f.write(pdf)

    d = DocumentoArchiviato.objects.create(
        tipo='BUSTA_TFR',
        titolo=f"Liquidazione TFR {contratto.lavoratore.nome_cognome} ({data_inizio_eff.strftime('%d/%m/%Y')} – {data_fine.strftime('%d/%m/%Y')})",
        file_path=full_path, file_size=len(pdf), file_name=nome_file_disk,
        contratto=contratto, datore=contratto.datore, lavoratore=contratto.lavoratore,
        creato_da=request.user if request.user.is_authenticated else None,
    )
    request.session['ultimo_doc_pk'] = d.pk
    if mese_req and anno_req:
        BustaPaga.objects.filter(contratto=contratto, mese=int(mese_req), anno=int(anno_req), tipo_calcolo='TFR').update(documento=d)

    if request.GET.get('allega_lul') == '1':
        from paghe.views._lul import _concatena_lul_a_busta
        pdf = _concatena_lul_a_busta(pdf, contratto, mese=int(mese_req), anno=int(anno_req)) if mese_req and anno_req else pdf

    response = HttpResponse(pdf, content_type='application/pdf')
    safe_filename = f"{contratto.lavoratore.nome_cognome.replace(' ', '_').replace('/', '_')}_Liquidazione_TFR.pdf"
    response['Content-Disposition'] = f'inline; filename="{safe_filename}"'
    return response


# --- ajax_rigenera_documenti_cessazione ---
@login_required
@permesso_richiesto('buste.calcola')
def ajax_rigenera_documenti_cessazione(request, pk):
    """Rigenera i documenti di cessazione (ultima busta + TFR) per un contratto."""
    try:
        contratto = get_object_or_404(ContrattoAttivo, pk=pk)
        if contratto.stato != 'CESSATO':
            return JsonResponse({'ok': False, 'errore': 'Il contratto non è in stato CESSATO.'})
        logger.info(f"[ajax_rigenera_documenti_cessazione] Contratto {pk} ({contratto.lavoratore.nome_cognome})")
        bp_norm, pdf_norm, tipo = _genera_ultima_busta_cessazione(contratto, request.user)
        pdf_tfr, nome_tfr = _genera_liquidazione_tfr_cessazione(contratto, request.user)
        if bp_norm:
            _associa_documenti_cessazione(bp_norm, pdf_norm, pdf_tfr, nome_tfr, contratto, bp_norm.mese, bp_norm.anno, tipo, request.user)
        logger.info(f"[ajax_rigenera_documenti_cessazione] Completato.")
        return JsonResponse({'ok': True})
    except Exception as e:
        logger.exception("[ajax_rigenera_documenti_cessazione] ECCEZIONE: %s", e)
        return JsonResponse({'ok': False, 'errore': str(e)})


# --- _genera_ultima_busta_cessazione ---


def _genera_ultima_busta_cessazione(contratto, user):
    """Genera l'ultima busta paga normale alla cessazione del contratto.
    Restituisce (BustaPaga, pdf_bytes, tipo_calcolo) oppure (None, None, None)."""
    try:
        if contratto.data_fine:
            data_cess = contratto.data_fine
        else:
            data_cess = date.today()
        mese = data_cess.month
        anno = data_cess.year
        ore_sett = float(getattr(contratto, 'ore_settimanali_calcolate', 0) or 0)
        if contratto.is_convivente:
            tipo = 'CONVIVENTE'
        elif ore_sett > 0:
            tipo = 'NON_CONVIVENTE'
        else:
            tipo = 'STANDARD'
        is_conv = (tipo == 'CONVIVENTE')
        logger.info(f"[_genera_ultima_busta_cessazione] Contratto {contratto.pk}, mese={mese}, anno={anno}, tipo={tipo}, is_conv={is_conv}, ore_sett={ore_sett}, data_cess={data_cess}")
        data = _calcola_busta_data(contratto, mese, anno, is_convivente=is_conv)
        if 'errore' in data:
            logger.error("[_genera_ultima_busta_cessazione] ERRORE da _calcola_busta_data: %s", data.get('errore'))
            return None, None, None
        logger.info(f"[_genera_ultima_busta_cessazione] _calcola_busta_data OK, lordo={data.get('totale_lordo')}, netto={data.get('netto')}")
        bp, created = BustaPaga.objects.update_or_create(
            contratto=contratto, mese=mese, anno=anno,
            defaults=dict(
                tipo_calcolo=tipo,
                budget_mensile=data['budget_mensile'],
                ore_mensili=data['ore_mensili'],
                ore_inps=data['ore_inps'],
                ore_settimanali=data['ore_settimanali'],
                paga_oraria_lorda=data['paga_oraria_lorda'],
                paga_base_totale=data['paga_base']['totale'],
                totale_indennita=data['totale_indennita'],
                scatti_totale=data['scatti_anzianita']['valore'],
                totale_lordo=data['totale_lordo'],
                contributi_inps_orario=data['contributi']['inps']['orario'],
                contributi_inps_totale=data['contributi']['inps']['totale'],
                contributi_inps_fascia=data['contributi']['inps']['fascia'],
                contributi_inps_quota_datore=data['contributi']['inps']['quota_datore_totale'],
                contributi_inps_quota_lavoratore=data['contributi']['inps']['quota_lavoratore_totale'],
                contributi_cassa_orario=data['contributi']['cassa']['orario'],
                contributi_cassa_totale=data['contributi']['cassa']['totale'],
                contributi_cassa_nome=data['contributi']['cassa']['nome'],
                totale_contributi=data['contributi']['totale'],
                convivenza_totale=data['trattenute']['convivenza']['totale'],
                totale_accantonati=data['trattenute']['ratei_accantonati'],
                netto=data['netto'],
                indennita_json=data.get('indennita', []),
                ratei_pagati_json=data.get('ratei_pagati', []),
                scatti_dettaglio_json=data.get('scatti_anzianita', {}),
                progetti_json=data.get('progetti', []),
                tfr_data={'tipo': 'cessazione', 'data_cessazione': data_cess.isoformat()},
            )
        )
        logger.info(f"[_genera_ultima_busta_cessazione] BustaPaga {'creata' if created else 'aggiornata'} pk={bp.pk}. Genero PDF completo...")
        pdf_bytes, _ = _genera_busta_completa_pdf_bytes(contratto, mese, anno, ctx_override=data, tipo_override=tipo)
        logger.info(f"[_genera_ultima_busta_cessazione] PDF generato ({len(pdf_bytes)} byte).")
        return bp, pdf_bytes, tipo
    except Exception as e:
        logger.exception("[_genera_ultima_busta_cessazione] ECCEZIONE: %s", e)
        return None, None, None


# --- _genera_liquidazione_tfr_cessazione ---


def _genera_liquidazione_tfr_cessazione(contratto, user):
    """Genera il PDF di liquidazione TFR alla cessazione del contratto.
    Restituisce (pdf_bytes, nome_file_disk) oppure (None, None) se TFR non dovuto."""
    import calendar
    try:
        logger.info(f"[_genera_liquidazione_tfr_cessazione] Contratto {contratto.pk} ({contratto.lavoratore.nome_cognome}) — modalita_tfr={contratto.modalita_tfr}, data_fine={contratto.data_fine}")
        if contratto.modalita_tfr == 'INCLUSO':
            logger.info(f"[_genera_liquidazione_tfr_cessazione] TFR INCLUSO — skip.")
            return None, None
        p = contratto.parametri_minimi
        if not p:
            logger.info(f"[_genera_liquidazione_tfr_cessazione] parametri_minimi assente — skip.")
            return None, None
        ore_m = contratto.ore_mensili_calcolate
        if ore_m <= 0:
            logger.info(f"[_genera_liquidazione_tfr_cessazione] ore_mensili_calcolate={ore_m} <= 0 — skip.")
            return None, None

        if contratto.data_fine:
            data_cess = contratto.data_fine
        else:
            data_cess = date.today()
        mese = data_cess.month
        anno = data_cess.year
        ultimo = calendar.monthrange(anno, mese)[1]
        data_fine = date(anno, mese, ultimo)
        data_inizio_eff = contratto.data_inizio_tfr or contratto.data_assunzione
        if not data_inizio_eff:
            logger.info(f"[_genera_liquidazione_tfr_cessazione] data_inizio_tfr e data_assunzione entrambe None — skip.")
            return None, None

        mesi, tfr_mensile, cumulativo = _calcola_tfr_fino_a(contratto, data_fine)
        logger.info(f"[_genera_liquidazione_tfr_cessazione] _calcola_tfr_fino_a: mesi={mesi}, tfr_mensile={tfr_mensile}, cumulativo={cumulativo}")
        if cumulativo <= 0:
            logger.info(f"[_genera_liquidazione_tfr_cessazione] cumulativo={cumulativo} <= 0 — skip.")
            return None, None

        coeff = 0.3 if contratto.modalita_tfr == 'SEPARATO_70' else 1.0
        tfr_orario = float(p.tfr_orario) if p else 0

        logger.info(f"[_genera_liquidazione_tfr_cessazione] Genero PDF liquidazione... coeff={coeff}, tfr_orario={tfr_orario}")
        pdf, nome_file_disk = _build_liquidazione_tfr_pdf_bytes(contratto, data_inizio_eff, data_fine, mesi, tfr_mensile, cumulativo, tfr_orario, ore_m, coeff)
        logger.info(f"[_genera_liquidazione_tfr_cessazione] PDF generato ({len(pdf)} byte, nome={nome_file_disk})")
        return pdf, nome_file_disk
    except Exception as e:
        logger.exception("[_genera_liquidazione_tfr_cessazione] ECCEZIONE: %s", e)
        return None, None


# --- _associa_documenti_cessazione ---


def _associa_documenti_cessazione(bp_normale, pdf_normale, pdf_tfr, nome_file_tfr, contratto, mese, anno, tipo_normale, user):
    """Crea i DocumentiArchiviato per la cessazione:
    - BUSTA_PAGA: PDF combinato (normale + TFR)
    - LIQUIDAZIONE_TFR: solo PDF TFR (se presente)
    Associa BUSTA_PAGA a bp_normale, elimina vecchi doc.
    """
    import os
    from io import BytesIO
    from pypdf import PdfWriter
    try:
        # 1. PDF combinato
        writer = PdfWriter()
        writer.append(BytesIO(pdf_normale))
        if pdf_tfr:
            writer.append(BytesIO(pdf_tfr))
        combined_buf = BytesIO()
        writer.write(combined_buf)
        combined_bytes = combined_buf.getvalue()
        combined_buf.close()

        safe_name = f"{contratto.lavoratore.nome_cognome.replace(' ', '_')}_{mese:02d}{anno}_{tipo_normale}.pdf"
        cartella = _get_cartella_documenti(contratto)
        os.makedirs(cartella, exist_ok=True)
        full_path = os.path.join(cartella, safe_name)

        with open(full_path, 'wb') as f:
            f.write(combined_bytes)

        # 2. Elimina vecchio documento della busta normale
        old_doc = bp_normale.documento
        if old_doc:
            logger.info(f"[_associa_documenti_cessazione] Elimino vecchio DocumentoArchiviato busta pk={old_doc.pk}")
            old_doc.delete()

        # 3. Crea DocumentoArchiviato BUSTA_PAGA (combinato)
        d_busta = DocumentoArchiviato.objects.create(
            tipo='BUSTA_PAGA',
            titolo=f"Busta paga {contratto.lavoratore.nome_cognome} {mese:02d}/{anno} ({tipo_normale})",
            file_path=full_path, file_size=len(combined_bytes), file_name=safe_name,
            contratto=contratto, datore=contratto.datore, lavoratore=contratto.lavoratore,
            creato_da=user if user and user.is_authenticated else None,
        )
        BustaPaga.objects.filter(pk=bp_normale.pk).update(documento=d_busta)
        logger.info(f"[_associa_documenti_cessazione] Documento BUSTA_PAGA creato pk={d_busta.pk} (combinato, {len(combined_bytes)} byte)")

        # 4. Crea DocumentoArchiviato LIQUIDAZIONE_TFR (se TFR presente)
        if pdf_tfr and nome_file_tfr:
            tfr_path = os.path.join(cartella, nome_file_tfr)
            with open(tfr_path, 'wb') as f:
                f.write(pdf_tfr)
            # Elimina eventuale vecchio doc TFR (cerca per tipo+contratto)
            vecchi_tfr = DocumentoArchiviato.objects.filter(
                tipo='LIQUIDAZIONE_TFR', contratto=contratto
            )
            for v in vecchi_tfr:
                logger.info(f"[_associa_documenti_cessazione] Elimino vecchio DocumentoArchiviato TFR pk={v.pk}")
                v.delete()
            d_tfr = DocumentoArchiviato.objects.create(
                tipo='LIQUIDAZIONE_TFR',
                titolo=f"Liquidazione TFR Cessazione {contratto.lavoratore.nome_cognome}",
                file_path=tfr_path, file_size=len(pdf_tfr), file_name=nome_file_tfr,
                contratto=contratto, datore=contratto.datore, lavoratore=contratto.lavoratore,
                creato_da=user if user and user.is_authenticated else None,
            )
            logger.info(f"[_associa_documenti_cessazione] Documento LIQUIDAZIONE_TFR creato pk={d_tfr.pk}")

        logger.info(f"[_associa_documenti_cessazione] Completato.")
    except Exception as e:
        logger.exception("[_associa_documenti_cessazione] ECCEZIONE: %s", e)


# --- ajax_cerca_contratti_copia ---
@login_required
@permesso_richiesto('documenti.crea')
def ajax_cerca_contratti_copia(request):
    q = request.GET.get('q', '').strip()
    contratti = ContrattoLavoro.objects.filter(stato='ATTIVO').order_by('-data_assunzione')
    if len(q) >= 2:
        from django.db.models import Q
        contratti = contratti.filter(
            Q(datore__nome_cognome__icontains=q) |
            Q(lavoratore__nome_cognome__icontains=q) |
            Q(codice_rapporto_inps__icontains=q)
        )
    results = []
    for c in contratti[:30]:
        primo_progetto = c.progetto.first()
        results.append({
            'pk': c.pk,
            'datore': c.datore.nome_cognome,
            'lavoratore': c.lavoratore.nome_cognome,
            'beneficiario': primo_progetto.beneficiario.nome_cognome if primo_progetto and primo_progetto.beneficiario else '',
            'tipo_contratto': c.get_tipo_contratto_display(),
            'data_assunzione': c.data_assunzione.isoformat() if c.data_assunzione else '',
            'codice_inps': c.codice_rapporto_inps or '',
        })
    return JsonResponse({'results': results})


# --- ajax_dettaglio_contratto_copia ---
@login_required
@permesso_richiesto('documenti.crea')
def ajax_dettaglio_contratto_copia(request, pk):
    c = get_object_or_404(ContrattoLavoro, pk=pk)
    progetti_ids = list(c.progetto.values_list('pk', flat=True))
    data = {
        'datore': c.datore_id,
        'lavoratore': c.lavoratore_id,
        'progetto': progetti_ids,
        'parametri_minimi': c.parametri_minimi_id,
        'ente_bilaterale': c.ente_bilaterale_id if hasattr(c, 'ente_bilaterale_id') else None,
        'stato': c.stato,
        'tipo_contratto': c.tipo_contratto,
        'data_assunzione': c.data_assunzione.isoformat() if c.data_assunzione else '',
        'data_inizio_tfr': c.data_inizio_tfr.isoformat() if c.data_inizio_tfr else '',
        'codice_rapporto_inps': c.codice_rapporto_inps or '',
        'ore_mav_custom': str(c.ore_mav_custom) if c.ore_mav_custom else '',
        'note_post_it': c.note_post_it or '',
        'modalita_tfr': c.modalita_tfr,
        'paga_13ma': c.paga_13ma,
        'paga_ferie': c.paga_ferie,
        'paga_festivi': c.paga_festivi,
        'paga_notturno_tfr': c.paga_notturno_tfr,
        'paga_notturno_13ma': c.paga_notturno_13ma,
        'paga_notturno_festivi': c.paga_notturno_festivi,
        'paga_notturno_ferie': c.paga_notturno_ferie,
        'paga_pranzo': c.paga_pranzo,
        'paga_cena': c.paga_cena,
        'paga_alloggio': c.paga_alloggio,
        'applica_scatti': c.applica_scatti,
        'applica_notturno_assistenza': c.applica_notturno_assistenza,
        'applica_notturno_presenza': c.applica_notturno_presenza,
        'applica_notturno_base': c.applica_notturno_base,
        'applica_notturno_20': c.applica_notturno_20,
        'ind_certificazione_qualita': c.ind_certificazione_qualita,
        'ind_piu_persone_non_conv': c.ind_piu_persone_non_conv,
        'ind_minori_non_conv': c.ind_minori_non_conv,
        'ind_piu_persone_qualita': c.ind_piu_persone_qualita,
        'ind_minori_qualita': c.ind_minori_qualita,
        'ind_assistenza_piu_persone_ft': c.ind_assistenza_piu_persone_ft,
        'ind_assistenza_piu_persone_pt': c.ind_assistenza_piu_persone_pt,
        'ind_minori_6_anni_ft': c.ind_minori_6_anni_ft,
        'ind_funzione_conviventi': c.ind_funzione_conviventi,
        'ind_conviventi_ft_54h': c.ind_conviventi_ft_54h,
        'ind_conviventi_pt_30h': c.ind_conviventi_pt_30h,
    }
    return JsonResponse(data)
