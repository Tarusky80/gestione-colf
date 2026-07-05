"""Modulo _liste - generato automaticamente da views.py"""

from paghe.views._common_imports import *

logger = logging.getLogger(__name__)

from paghe.views._helpers import _registra_font_pdf, _risolvi_globali, _format_pdf_cell




# --- liste_view ---
@login_required
@permesso_richiesto('report')
def liste_view(request):
    opzioni = get_opzioni()
    datori = DatoreLavoro.objects.all().order_by('nome_cognome')
    livelli = Livello.objects.all()
    tipi_progetto = TipoProgettoRegionale.objects.all()
    return render(request, 'paghe/liste.html', {
        'opzioni': opzioni,
        'datori': datori,
        'livelli': livelli,
        'tipi_progetto': tipi_progetto,
    })


# --- ajax_field_browser ---
@login_required
@permesso_richiesto('report')
def ajax_field_browser(request, tipo_sorgente):
    from paghe.field_browser import FIELD_MAP
    campi = FIELD_MAP.get(tipo_sorgente.upper(), [])
    return JsonResponse({'campi': campi, 'tipo_sorgente': tipo_sorgente.upper()})


# --- ajax_modello_lista_config ---
@login_required
@permesso_richiesto('report')
def ajax_modello_lista_config(request, pk):
    modello = get_object_or_404(ModelloLista, pk=pk)
    return JsonResponse({'colonne': modello.configurazione_colonne, 'nome': modello.nome, 'tipo_sorgente': modello.tipo_sorgente})


# --- ajax_salva_config_modello ---
@login_required
@permesso_richiesto('report')
def ajax_salva_config_modello(request, pk):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Metodo non consentito'}, status=405)
    try:
        data = json.loads(request.body)
        modello = get_object_or_404(ModelloLista, pk=pk)
        modello.configurazione_colonne = data.get('colonne', [])
        modello.save(update_fields=['configurazione_colonne'])
        return JsonResponse({'success': True})
    except Exception as e:
        logger.exception("Errore in ajax_salva_config_modello")
        return JsonResponse({'success': False, 'message': str(e)})


# --- ajax_elimina_modello_lista ---
@login_required
@permesso_richiesto('report')
@require_http_methods(["POST"])
def ajax_elimina_modello_lista(request, pk):
    try:
        modello = get_object_or_404(ModelloLista, pk=pk)
        nome = modello.nome
        modello.delete()
        return JsonResponse({'success': True, 'message': f'Modello "{nome}" eliminato.'})
    except Exception as e:
        logger.exception("Errore in ajax_elimina_modello_lista")
        return JsonResponse({'success': False, 'message': str(e)})


# --- ajax_genera_lista_personalizzata ---
@login_required
@permesso_richiesto('report')
@xframe_options_exempt
def ajax_genera_lista_personalizzata(request, pk):
    from io import BytesIO
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus.flowables import HRFlowable
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm
    from paghe.field_resolver import resolve_column_values

    _registra_font_pdf()
    modello = get_object_or_404(ModelloLista, pk=pk)
    colonne = modello.configurazione_colonne
    if isinstance(colonne, str):
        colonne = json.loads(colonne)
    if not colonne or not isinstance(colonne, list) or len(colonne) == 0:
        return JsonResponse({'error': 'Nessuna colonna configurata per questo modello'}, status=400)
    filters = {k: request.GET.get(k) for k in request.GET if request.GET.get(k)}
    rows, labels = resolve_column_values(modello.tipo_sorgente, colonne, filters)

    if not rows:
        return JsonResponse({'error': 'Nessun dato trovato'}, status=404)

    opzioni = get_opzioni()
    oggi = date.today()
    grigio_scuro = HexColor('#333333')
    grigio_medio = HexColor('#666666')
    grigio_bordo = HexColor('#cccccc')
    HexColor('#ffffff')

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=10*mm, rightMargin=10*mm,
        topMargin=5*mm, bottomMargin=6*mm,
    )
    story = []

    s_title = ParagraphStyle('ltitle', fontSize=14, leading=18, textColor=grigio_scuro, fontName='Roboto-Bold', spaceAfter=1, alignment=TA_LEFT)
    s_sub = ParagraphStyle('lsub', fontSize=7.5, leading=10, textColor=grigio_medio, fontName='Roboto', alignment=TA_LEFT, spaceAfter=2)
    s_header = ParagraphStyle('lheader', fontSize=7.5, leading=11, textColor=HexColor('#111111'), fontName='Roboto-Bold', alignment=TA_LEFT)
    s_cell = ParagraphStyle('lcell', fontSize=7.5, leading=11, textColor=HexColor('#333333'), fontName='Roboto', alignment=TA_LEFT)
    s_footer = ParagraphStyle('lfooter', fontSize=7, leading=9, textColor=grigio_medio, fontName='Roboto', alignment=TA_CENTER)

    # Header con logo
    studio_nome = opzioni.denominazione_studio if opzioni and opzioni.denominazione_studio else ''
    titolo = modello.nome.upper()
    logo_rl = None
    if opzioni and opzioni.logo_buste_paga and opzioni.logo_buste_paga.path and os.path.exists(opzioni.logo_buste_paga.path):
        try:
            logo_rl = RLImage(opzioni.logo_buste_paga.path, width=120, height=40)
        except Exception:
            logger.warning("Impossibile caricare logo lista (header): %s", getattr(opzioni.logo_buste_paga, 'path', ''))

    if logo_rl:
        avail = landscape(A4)[0] - 20*mm
        gap = 6*mm
        txt_col_w = avail - 120 - gap
        txt_rows = [[Paragraph(titolo, s_title)]]
        if studio_nome:
            txt_rows.append([Paragraph(studio_nome, s_sub)])
        txt_rows.append([Paragraph(f'Generato il {oggi.strftime("%d/%m/%Y")}', s_sub)])
        txt_sub = Table(txt_rows, colWidths=[txt_col_w])
        txt_sub.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        header_tbl = Table([[logo_rl, txt_sub]], colWidths=[120, txt_col_w])
        header_tbl.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('LINEAFTER', (0, 0), (0, -1), 1.5, HexColor('#000000')),
            ('RIGHTPADDING', (0, 0), (0, 0), 8),
            ('LEFTPADDING', (1, 0), (1, -1), 8),
        ]))
        story.append(header_tbl)
    else:
        story.append(Paragraph(titolo, s_title))
        if studio_nome:
            story.append(Paragraph(studio_nome, s_sub))
        story.append(Paragraph(f'Generato il {oggi.strftime("%d/%m/%Y")}', s_sub))
    story.append(Spacer(1, 2))
    story.append(HRFlowable(width="100%", thickness=0.5, color=grigio_bordo, spaceAfter=4))

    # Tabella
    ALIGN_MAP = {'left': TA_LEFT, 'center': TA_CENTER, 'right': TA_RIGHT}
    header_cells = [Paragraph(col['label'], s_header) for col in colonne]
    table_data = [header_cells]

    for row in rows:
        cells = []
        for i, col in enumerate(colonne):
            val = row.get(col['field_path'], '\u2014')
            align = ALIGN_MAP.get(col.get('allineamento', 'left'), TA_LEFT)
            s_cell.alignment = align
            formatted = _format_pdf_cell(val)
            cells.append(Paragraph(str(formatted), s_cell))
        table_data.append(cells)

    disp_larghezza = landscape(A4)[0] - 20*mm
    largh_totali = sum(c.get('larghezza', 30) for c in colonne)
    if largh_totali <= 0:
        largh_totali = len(colonne) * 30
    col_widths = [disp_larghezza * (c.get('larghezza', 30) / largh_totali) for c in colonne]

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, HexColor('#e0e0e0')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7.5),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#111111')),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('TOPPADDING', (0, 0), (-1, 0), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('FONTSIZE', (0, 1), (-1, -1), 7.5),
        ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#333333')),
    ]
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), HexColor('#f5f5f7')))
    tbl.setStyle(TableStyle(style_cmds))
    story.append(tbl)

    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=0.3, color=grigio_bordo, spaceAfter=3))
    story.append(Paragraph(f"Totale: {len(rows)} record", s_footer))
    _footer_txt = _risolvi_globali('{{FOOTER_DOCUMENTO}}')
    if _footer_txt and _footer_txt.strip():
        _footer_plain = _footer_txt.replace('<br/>', '\n').replace('<br>', '\n').replace('&nbsp;', ' ').replace('&euro;', '\u20ac')
        _footer_plain = re.sub(r'<[^>]+>', '', _footer_plain)
        story.append(Paragraph(_footer_plain.strip(), s_footer))

    doc.build(story)
    pdf = buf.getvalue()
    buf.close()

    # Salva in DocumentoArchiviato
    cartella_base = opzioni.cartella_documenti if opzioni and opzioni.cartella_documenti else os.path.join(settings.MEDIA_ROOT, 'documenti')
    cartella_liste = os.path.join(cartella_base, 'LISTE_PERSONALIZZATE')
    if not os.path.exists(cartella_liste):
        os.makedirs(cartella_liste)
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    nome_file = f"lista_personalizzata_{pk}_{timestamp}.pdf"
    full_path = os.path.join(cartella_liste, nome_file)
    with open(full_path, 'wb') as f:
        f.write(pdf)

    DocumentoArchiviato.objects.create(
        tipo='LISTA',
        titolo=f"{modello.nome} — {oggi.strftime('%d/%m/%Y')}",
        file_path=full_path,
        file_size=os.path.getsize(full_path),
        file_name=nome_file,
        creato_da=request.user if request.user.is_authenticated else None,
    )

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nome_file}"'
    return response


# --- ajax_genera_lista ---
@login_required
@permesso_richiesto('report')
@xframe_options_exempt
def ajax_genera_lista(request, tipo):
    from io import BytesIO
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    import os

    _registra_font_pdf()
    opzioni = get_opzioni()
    grigio_scuro = HexColor('#333333')
    grigio_medio = HexColor('#666666')
    grigio_bordo = HexColor('#cccccc')
    HexColor('#f0f0f0')
    HexColor('#ffffff')
    oggi = date.today()

    dati = []
    colonne = []
    largh = []
    titolo = ''

    # ─── DATORI ───
    if tipo == 'datori':
        titolo = 'ELENCO DATORI DI LAVORO'
        colonne = ['NOME', 'CF', 'INDIRIZZO', 'COMUNE', 'TEL', 'EMAIL', 'PIN INPS', 'INVIO DIG.', 'NOTE', 'PROGETTI']
        largh = [30, 28, 26, 18, 14, 22, 18, 10, 12, 44]
        qs = DatoreLavoro.objects.prefetch_related('contratti_come_datore__progetto__tipo').all().order_by('nome_cognome')
        for d in qs:
            prog_set = set()
            for c in d.contratti_come_datore.all():
                for p in c.progetto.all():
                    colore = p.tipo.colore if p.tipo and p.tipo.colore else '#10b981'
                    nome = p.tipo.nome if p.tipo else 'N/D'
                    prog_set.add((nome, colore))
            prog_str = '<br/>'.join([f'<font color="{c}">\u25cf</font> {n}' for n, c in sorted(prog_set, key=lambda x: x[0])]) if prog_set else '\u2014'
            invio_digit = '\u2713' if d.invio_digitale_documenti else '\u2717'
            dati.append([d.nome_cognome, d.codice_fiscale, d.indirizzo or '\u2014', d.comune or '\u2014', d.telefono or '\u2014', d.email or '\u2014', d.pin_inps or '\u2014', invio_digit, d.note_datore or '\u2014', prog_str])

    # ─── LAVORATORI ───
    elif tipo == 'lavoratori':
        titolo = 'ELENCO LAVORATORI'
        colonne = ['NOME', 'CF', 'INDIRIZZO', 'COMUNE', 'TEL', 'EMAIL', 'FERIE PREGR.', 'SCATTI ANZ.', 'NOTE', 'PROGETTI']
        largh = [32, 28, 26, 16, 14, 20, 14, 12, 12, 44]
        qs = Lavoratore.objects.prefetch_related('contratti_come_lavoratore__progetto__tipo').all().order_by('nome_cognome')
        for l in qs:
            prog_set = set()
            for c in l.contratti_come_lavoratore.all():
                for p in c.progetto.all():
                    colore = p.tipo.colore if p.tipo and p.tipo.colore else '#10b981'
                    nome = p.tipo.nome if p.tipo else 'N/D'
                    prog_set.add((nome, colore))
            prog_str = '<br/>'.join([f'<font color="{c}">\u25cf</font> {n}' for n, c in sorted(prog_set, key=lambda x: x[0])]) if prog_set else '\u2014'
            ferie = f'{l.ferie_pregresse:.2f}' if l.ferie_pregresse else '\u2014'
            scatti = str(l.scatti_anzianita_maturati) if l.scatti_anzianita_maturati else '\u2014'
            dati.append([l.nome_cognome, l.codice_fiscale, l.indirizzo or '\u2014', l.comune or '\u2014', l.telefono or '\u2014', l.email or '\u2014', ferie, scatti, l.note_lavoratore or '\u2014', prog_str])

    # ─── BENEFICIARI ───
    elif tipo == 'beneficiari':
        titolo = 'ELENCO BENEFICIARI'
        colonne = ['NOME', 'CF', 'INDIRIZZO', 'COMUNE', 'TEL', 'EMAIL', 'NOTE', 'PROGETTI']
        largh = [36, 26, 24, 16, 12, 20, 12, 56]
        qs = Beneficiario.objects.prefetch_related('progetti__tipo').all().order_by('nome_cognome')
        for b in qs:
            progetti_pars = []
            for p in b.progetti.all():
                colore = p.tipo.colore if p.tipo and p.tipo.colore else '#10b981'
                nome = p.tipo.nome if p.tipo else 'N/D'
                progetti_pars.append(f'<font color="{colore}">\u25cf</font> {nome}')
            progetti_str = '<br/>'.join(progetti_pars) if progetti_pars else '\u2014'
            dati.append([b.nome_cognome, b.codice_fiscale, b.indirizzo or '\u2014', b.comune or '\u2014', b.telefono or '\u2014', b.email or '\u2014', b.note_beneficiario or '\u2014', progetti_str])

    # ─── PROGETTI REGIONALI ───
    elif tipo == 'progetti':
        titolo = 'ELENCO PROGETTI REGIONALI'
        colonne = ['BENEFICIARIO', 'DATORE', 'LAVORATORE', 'TIPO', 'INIZIO', 'FINE', 'BUDGET ANN.', 'BUDGET MES.', 'MESI']
        largh = [30, 30, 30, 24, 18, 18, 22, 22, 12]
        from django.db.models import Prefetch
        filtro_tipo = request.GET.get('tipo_progetto')
        qs = ProgettoRegionale.objects.select_related('beneficiario', 'tipo').prefetch_related(
            Prefetch('contrattolavoro_set', queryset=ContrattoLavoro.objects.select_related('datore', 'lavoratore'))
        ).all().order_by('beneficiario__nome_cognome')
        if filtro_tipo:
            qs = qs.filter(tipo_id=filtro_tipo)
        for p in qs:
            colore = p.tipo.colore if p.tipo and p.tipo.colore else '#10b981'
            nome_tipo = p.tipo.nome if p.tipo else '\u2014'
            contratti = p.contrattolavoro_set.all()
            datori_set = set()
            lavoratori_set = set()
            for c in contratti:
                if c.datore:
                    datori_set.add(c.datore.nome_cognome)
                if c.lavoratore:
                    lavoratori_set.add(c.lavoratore.nome_cognome)
            datori_str = '<br/>'.join(sorted(datori_set)) if datori_set else '\u2014'
            lavoratori_str = '<br/>'.join(sorted(lavoratori_set)) if lavoratori_set else '\u2014'
            dati.append([
                p.beneficiario.nome_cognome,
                datori_str,
                lavoratori_str,
                f'<font color="{colore}">\u25cf</font> {nome_tipo}',
                p.data_inizio.strftime('%d/%m/%Y') if p.data_inizio else '\u2014',
                p.data_fine.strftime('%d/%m/%Y') if p.data_fine else '\u2014',
                f"\u20ac {p.budget_annuale:.2f}",
                f"\u20ac {p.budget_mensile:.2f}" if p.budget_mensile else '\u2014',
                str(p.mesi),
            ])

    # ─── CONTRATTI ATTIVI ───
    elif tipo == 'contratti-attivi':
        titolo = 'ELENCO CONTRATTI ATTIVI'
        colonne = ['DATORE', 'LAVORATORE', 'BENEFICIARIO', 'PROGETTO', 'PAESE', 'LIV.', 'DATA ASS.', 'TIPO', 'ENTE', 'MOD. ORE', 'BUDGET ANN.', 'BUDGET MES.', 'ORE', 'OPZIONI', 'NOTE']
        largh = [34, 34, 30, 22, 10, 8, 8, 10, 6, 8, 24, 24, 6, 18, 12]
        qs = ContrattoAttivo.objects.filter(stato='ATTIVO').select_related('datore', 'lavoratore', 'parametri_minimi__livello', 'ente_bilaterale').prefetch_related('progetto__tipo', 'progetto__beneficiario')
        filtro_datore = request.GET.get('datore')
        filtro_livello = request.GET.get('livello')
        if filtro_datore:
            qs = qs.filter(datore_id=filtro_datore)
        if filtro_livello:
            qs = qs.filter(parametri_minimi__livello__codice=filtro_livello)
        for c in qs:
            progetti = list(c.progetto.all())
            beneficiario = progetti[0].beneficiario.nome_cognome if progetti and progetti[0].beneficiario else '\u2014'
            paese = progetti[0].beneficiario.comune if progetti and progetti[0].beneficiario else '\u2014'
            prog_parts = []
            for p in progetti:
                colore = p.tipo.colore if p.tipo and p.tipo.colore else '#10b981'
                nome = p.tipo.nome if p.tipo else 'N/D'
                prog_parts.append(f'<font color="{colore}">\u25cf</font> {nome}')
            prog_str = '<br/>'.join(prog_parts) if prog_parts else '\u2014'
            si = "S\u00ec"; no = "No"
            opzioni_contratto = []
            opzioni_contratto.append(f'<b>13\u00aa</b>: {si if c.paga_13ma else no}')
            opzioni_contratto.append(f'<b>Ferie</b>: {si if c.paga_ferie else no}')
            opzioni_contratto.append(f'<b>Fest.</b>: {si if c.paga_festivi else no}')
            opzioni_contratto.append(f'<b>Scatti</b>: {si if c.applica_scatti else no}')
            opzioni_str = '<br/>'.join(opzioni_contratto)
            tipo_ct = c.tipo_contratto if c.tipo_contratto else '\u2014'
            note_ct = c.note_post_it or '\u2014'
            dati.append([
                c.datore.nome_cognome + '<br/>' + c.datore.codice_fiscale,
                c.lavoratore.nome_cognome + '<br/>' + c.lavoratore.codice_fiscale,
                beneficiario,
                prog_str,
                paese,
                c.parametri_minimi.livello.codice,
                c.data_assunzione.strftime('%d/%m/%Y') if c.data_assunzione else '\u2014',
                tipo_ct,
                c.ente_bilaterale.codice if c.ente_bilaterale else '\u2014',
                str(c.ore_mav_custom) if c.ore_mav_custom and c.ore_mav_custom > 0 else '\u2014',
                f"\u20ac {c.budget_di_partenza * 12:.2f}",
                f"\u20ac {c.budget_di_partenza:.2f}",
                str(c.ore_calcolate),
                opzioni_str,
                note_ct,
            ])

    # ─── PAGOPA INPS ───
    elif tipo == 'pagopa-inps':
        titolo = 'PAGOPA INPS - DATI CONTRIBUTIVI'
        colonne = ['DATORE', 'CF DATORE', 'LAVORATORE', 'COD. RAPP. INPS', 'ORE SETT.', 'ORE MENS.', 'ORE TRIM.', 'PAGA ORARIA INPS', 'IMP. CASSA TRIM.', 'COD. CASSA', 'STIMA CONTRIB. TRIM.', 'CONTRIB. TOTALI', '>24,9H']
        largh = [40, 40, 40, 30, 18, 18, 18, 18, 18, 18, 18, 18, 18]
        qs = ContrattoAttivo.objects.filter(stato='ATTIVO').select_related('datore', 'lavoratore', 'parametri_minimi', 'ente_bilaterale').prefetch_related('progetto__tipo', 'progetto__beneficiario')
        filtro_datore = request.GET.get('datore')
        if filtro_datore:
            qs = qs.filter(datore_id=filtro_datore)

        # Pre-carica aliquota INPS dalla stessa logica della busta paga
        for c in qs:
            ore_mensili_raw = float(c.ore_mensili_calcolate)
            ore_inps = math.ceil(ore_mensili_raw)
            ore_sett = float(c.ore_settimanali_calcolate)

            soglia_ore = float(opzioni.soglia_ore_contributi) if opzioni else 24.90
            soglia_paga_1 = float(opzioni.soglia_paga_1_contributi) if opzioni else 9.61
            soglia_paga_2 = float(opzioni.soglia_paga_2_contributi) if opzioni else 11.70
            is_sopra_soglia = ore_sett > soglia_ore
            paga_base = float(c.parametri_minimi.paga_base)
            tredicesima = float(c.parametri_minimi.tredicesima_oraria)
            paga_inps_2d = math.floor((paga_base + tredicesima) * 100) / 100
            if is_sopra_soglia:
                fascia_inps = TabellaContributiINPS.objects.filter(
                    descrizione__icontains="PIU"
                ).first()
            else:
                if paga_inps_2d <= soglia_paga_1:
                    fascia_inps = TabellaContributiINPS.objects.filter(
                        descrizione="MENO 24H - FINO A 9,61"
                    ).first()
                elif paga_inps_2d <= soglia_paga_2:
                    fascia_inps = TabellaContributiINPS.objects.filter(
                        descrizione="MENO 24H - 9,61-11,70"
                    ).first()
                else:
                    fascia_inps = TabellaContributiINPS.objects.filter(
                        descrizione="MENO 24H - OLTRE 11,70"
                    ).first()
            inps_orario = float(fascia_inps.totale) if fascia_inps else 0.0

            ente = c.ente_bilaterale
            cassa_orario = float(ente.totale) if ente else 0.0
            codice_cassa = ente.codice if ente else '\u2014'

            ore_trim = ore_inps * 3
            imp_cassa_trim = math.floor(cassa_orario * ore_trim * 100) / 100
            stima_contrib_trim = math.floor(inps_orario * ore_trim * 100) / 100
            verifica_soglia = f'<font color="#10b981">\u2713 S\u00ec</font>' if is_sopra_soglia else f'<font color="#ef4444">\u2717 No</font>'

            contrib_totali = math.floor((imp_cassa_trim + stima_contrib_trim) * 100) / 100
            dati.append([
                c.datore.nome_cognome,
                c.datore.codice_fiscale,
                c.lavoratore.nome_cognome,
                c.codice_rapporto_inps or '\u2014',
                str(math.ceil(ore_sett)),
                str(ore_inps),
                str(ore_inps * 3),
                f"\u20ac {paga_inps_2d:.2f}",
                f"\u20ac {imp_cassa_trim:.2f}",
                codice_cassa,
                f"\u20ac {stima_contrib_trim:.2f}",
                f"\u20ac {contrib_totali:.2f}",
                verifica_soglia,
            ])

    else:
        return JsonResponse({'error': 'Tipo lista non valido'}, status=400)

    # ─── GENERAZIONE PDF (LANDSCAPE) via ReportLab ───
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=10*mm, rightMargin=10*mm,
        topMargin=5*mm, bottomMargin=6*mm,
    )
    story = []

    s_title = ParagraphStyle('ltitle', fontSize=14, leading=18, textColor=grigio_scuro, fontName='Roboto-Bold', spaceAfter=1, alignment=TA_LEFT)
    s_sub = ParagraphStyle('lsub', fontSize=7.5, leading=10, textColor=grigio_medio, fontName='Roboto', alignment=TA_LEFT, spaceAfter=2)
    s_header = ParagraphStyle('lheader', fontSize=7.5, leading=11, textColor=HexColor('#111111'), fontName='Roboto-Bold', alignment=TA_CENTER)
    s_cell = ParagraphStyle('lcell', fontSize=7.5, leading=11, textColor=HexColor('#333333'), fontName='Roboto', alignment=TA_CENTER)
    s_footer = ParagraphStyle('lfooter', fontSize=7, leading=9, textColor=grigio_medio, fontName='Roboto', alignment=TA_CENTER)

    # ─── HEADER CON LOGO (se presente) ───
    studio_nome = opzioni.denominazione_studio if opzioni and opzioni.denominazione_studio else ''
    logo_rl = None
    if opzioni and opzioni.logo_buste_paga and opzioni.logo_buste_paga.path and os.path.exists(opzioni.logo_buste_paga.path):
        try:
            logo_rl = Image(opzioni.logo_buste_paga.path, width=120, height=40)
        except Exception:
            logger.warning("Impossibile caricare logo lista (header secondo): %s", getattr(opzioni.logo_buste_paga, 'path', ''))

    if logo_rl:
        avail = landscape(A4)[0] - 20*mm
        gap = 6*mm
        txt_col_w = avail - 120 - gap
        txt_rows = [[Paragraph(titolo, s_title)]]
        if studio_nome:
            txt_rows.append([Paragraph(studio_nome, s_sub)])
        txt_rows.append([Paragraph(f'Generato il {oggi.strftime("%d/%m/%Y")}', s_sub)])
        txt_sub = Table(txt_rows, colWidths=[txt_col_w])
        txt_sub.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        header_tbl = Table([[logo_rl, txt_sub]], colWidths=[120, txt_col_w])
        header_tbl.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('LINEAFTER', (0, 0), (0, -1), 1.5, HexColor('#000000')),
            ('RIGHTPADDING', (0, 0), (0, 0), 8),
            ('LEFTPADDING', (1, 0), (1, -1), 8),
        ]))
        story.append(header_tbl)
    else:
        story.append(Paragraph(titolo, s_title))
        if studio_nome:
            story.append(Paragraph(studio_nome, s_sub))
        story.append(Paragraph(f'Generato il {oggi.strftime("%d/%m/%Y")}', s_sub))
    story.append(Spacer(1, 2))
    story.append(HRFlowable(width="100%", thickness=0.5, color=grigio_bordo, spaceAfter=4))

    # Tabella
    header_cells = [Paragraph(col, s_header) for col in colonne]
    table_data = [header_cells]
    s_cell_progetti = ParagraphStyle('lcell_prog', fontSize=7.5, leading=11, textColor=HexColor('#333333'), fontName='Roboto', alignment=TA_CENTER)
    for row in dati:
        table_data.append([Paragraph(str(cell), s_cell_progetti if i == len(row) - 1 and tipo == 'beneficiari' else s_cell) for i, cell in enumerate(row)])

    disponibile_larghezza = landscape(A4)[0] - 20*mm
    col_widths = [disponibile_larghezza * (w / sum(largh)) for w in largh]

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, HexColor('#e0e0e0')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 7.5),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#111111')),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('TOPPADDING', (0, 0), (-1, 0), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('FONTSIZE', (0, 1), (-1, -1), 7.5),
        ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#333333')),
    ]
    # Righe alternate
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), HexColor('#f5f5f7')))
    tbl.setStyle(TableStyle(style_cmds))
    story.append(tbl)

    # Footer riepilogo
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=0.3, color=grigio_bordo, spaceAfter=3))
    story.append(Paragraph(f"Totale: {len(dati)} record", s_footer))
    _footer_txt = _risolvi_globali('{{FOOTER_DOCUMENTO}}')
    if _footer_txt and _footer_txt.strip():
        _footer_plain = _footer_txt.replace('<br/>', '\n').replace('<br>', '\n').replace('&nbsp;', ' ').replace('&euro;', '\u20ac')
        _footer_plain = re.sub(r'<[^>]+>', '', _footer_plain)
        story.append(Paragraph(_footer_plain.strip(), s_footer))

    doc.build(story)
    pdf = buf.getvalue()
    buf.close()

    # Salva in DocumentoArchiviato
    cartella_base = opzioni.cartella_documenti if opzioni and opzioni.cartella_documenti else os.path.join(settings.MEDIA_ROOT, 'documenti')
    cartella_liste = os.path.join(cartella_base, 'LISTE')
    if not os.path.exists(cartella_liste):
        os.makedirs(cartella_liste)
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    nome_file = f"lista_{tipo}_{timestamp}.pdf"
    full_path = os.path.join(cartella_liste, nome_file)
    with open(full_path, 'wb') as f:
        f.write(pdf)
    DocumentoArchiviato.objects.create(
        tipo='LISTA',
        titolo=f"{titolo} — {oggi.strftime('%d/%m/%Y')}",
        file_path=full_path,
        file_size=os.path.getsize(full_path),
        file_name=nome_file,
        creato_da=request.user if request.user.is_authenticated else None,
    )

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nome_file}"'
    return response
