"""Modulo _buste_download - generato automaticamente da views.py"""

from paghe.views._common_imports import *

logger = logging.getLogger(__name__)

from paghe.views._helpers import _get_cartella_documenti, _genera_pdf_da_testo, _offusca_ctx_anagrafici, _parse_toggles, _parse_convivenza_items
from paghe.views._calcoli_core import _calcola_busta_data, _calcola_busta_inversa_data, _calcola_progetti_data, _calcola_busta_conviventi_ccnl_data
from paghe.views._buste_pdf import _genera_html_busta, _genera_busta_completa_pdf_bytes, _genera_ricevuta_pdf_bytes
from paghe.views._testi import _risolvi_variabili_testo


# --- _crea_busta_paga_da_ctx ---


def _crea_busta_paga_da_ctx(ctx, contratto, mese, anno, tipo_calcolo, documento):
    """Crea o aggiorna il record BustaPaga dal dict ctx di calcolo.
    Necessario per abilitare la generazione LUL anche quando l'utente
    scarica il PDF senza prima salvare la busta dal pannello CRUD.
    """
    d = dict(
        tipo_calcolo=tipo_calcolo,
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
        documento=documento,
    )
    BustaPaga.objects.update_or_create(
        contratto=contratto, mese=mese, anno=anno,
        defaults=d
    )


# --- _build_busta_extra_vars ---


def _build_busta_extra_vars(ctx, html_busta):
    """Costruisce extra_vars per template BUSTA_PAGA.

    Aggiunge TUTTI i campi utili dal dict ctx (calcolo live) come variabili
    singole, più blocchi HTML pre-renderizzati per liste dinamiche.
    """
    _fmt_eur = lambda v: f'\u20ac {v:,.2f}'
    _fmt_eur4 = lambda v: f'\u20ac {v:,.4f}'

    extra_vars = {
        'BUSTA_CONTENUTO': html_busta,
        'BUSTA_MESE_NOME': ctx.get('mese_nome', ''),
        'BUSTA_ANNO': str(ctx.get('anno', '')),
        # --- Informazioni generali ---
        'BUSTA_TIPO_CALCOLO': ctx.get('tipo_calcolo', ''),
        'BUSTA_DATA_ASSUNZIONE': ctx.get('data_assunzione', ''),
        'BUSTA_TIPO_CONTRATTO': ctx.get('tipo_contratto', ''),
        'BUSTA_CODICE_RAPPORTO_INPS': ctx.get('codice_rapporto_inps', ''),
        'BUSTA_LIVELLO_CCNL': str(ctx.get('livello_codice', '')),
        'BUSTA_DESCRIZIONE_CORTA': ctx.get('descrizione_corta', ''),
        # --- Ore ---
        'BUSTA_ORE_MENSILI': str(ctx.get('ore_mensili', '0')),
        'BUSTA_ORE_INPS': str(ctx.get('ore_inps', '0')),
        'BUSTA_ORE_SETTIMANALI': str(ctx.get('ore_settimanali', '0')),
        'BUSTA_SOGLIA_ORE': str(ctx.get('soglia_ore', '0')),
        'BUSTA_SETTIMANE_MENSILI': str(ctx.get('settimane_mensili', '0')),
        'BUSTA_NUM_SABATI': str(ctx.get('num_sabati', '0')),
        # --- Paga base ---
        'BUSTA_PAGA_BASE_ORARIA': _fmt_eur4(ctx['paga_base']['orario']) if ctx.get('paga_base') else '',
        'BUSTA_PAGA_BASE_TOTALE': _fmt_eur(ctx['paga_base']['totale']) if ctx.get('paga_base') else '',
        # --- Paga applicata / effettiva ---
        'BUSTA_PAGA_APPLICATA_ORARIA': _fmt_eur4(ctx.get('paga_applicata_oraria', 0)),
        'BUSTA_PAGA_APPLICATA_MENSILE': _fmt_eur(ctx.get('paga_applicata_mensile', 0)),
        'BUSTA_PAGA_EFF_INPS_ORARIA': _fmt_eur4(ctx.get('paga_effettiva_inps_oraria', 0)),
        'BUSTA_PAGA_EFF_INPS_MENSILE': _fmt_eur(ctx.get('paga_effettiva_inps_mensile', 0)),
        # --- Paga oraria lorda ---
        'BUSTA_PAGA_ORARIA_LORDA': _fmt_eur4(ctx.get('paga_oraria_lorda', 0)),
        # --- Budget ---
        'BUSTA_BUDGET_MENSILE': _fmt_eur(ctx.get('budget_mensile', 0)),
        # --- Scatti ---
        'BUSTA_TOTALE_SCATTI': _fmt_eur(ctx.get('scatti_anzianita', {}).get('valore', 0)),
        'BUSTA_SCATTI_ORARIO': _fmt_eur4(ctx.get('scatti_anzianita', {}).get('orario', 0)),
        'BUSTA_SCATTI_DETTAGLIO': ctx.get('scatti_anzianita', {}).get('dettaglio', ''),
        # --- Indennità ---
        'BUSTA_TOTALE_INDENNITA': _fmt_eur(ctx.get('totale_indennita', 0)),
        # --- Lordo / Accantonati ---
        'BUSTA_TOTALE_LORDO': _fmt_eur(ctx.get('totale_lordo', 0)),
        'BUSTA_TOTALE_RATEI_INCLUSI': _fmt_eur(ctx.get('totale_ratei_inclusi', 0)),
        'BUSTA_TOTALE_ACCANTONATI': _fmt_eur(ctx.get('totale_accantonati', 0)),
        # --- Verifica copertura ---
        'BUSTA_VERIFICA_COPERTURA': _fmt_eur(ctx.get('verifica_copertura', 0)),
        # --- Netto ---
        'BUSTA_NETTO': _fmt_eur(ctx.get('netto', 0)),
        'BUSTA_DIFFERENZA': _fmt_eur(ctx.get('differenza', 0)),
        # --- Contributi INPS ---
        'BUSTA_CONTRIBUTI_INPS_ORARIO': _fmt_eur4(ctx.get('contributi', {}).get('inps', {}).get('orario', 0)),
        'BUSTA_CONTRIBUTI_INPS_TOTALE': _fmt_eur(ctx.get('contributi', {}).get('inps', {}).get('totale', 0)),
        'BUSTA_CONTRIBUTI_INPS_FASCIA': ctx.get('contributi', {}).get('inps', {}).get('fascia', ''),
        # --- Contributi Cassa ---
        'BUSTA_CONTRIBUTI_CASSA_NOME': ctx.get('contributi', {}).get('cassa', {}).get('nome', ''),
        'BUSTA_CONTRIBUTI_CASSA_ORARIO': _fmt_eur4(ctx.get('contributi', {}).get('cassa', {}).get('orario', 0)),
        'BUSTA_CONTRIBUTI_CASSA_TOTALE': _fmt_eur(ctx.get('contributi', {}).get('cassa', {}).get('totale', 0)),
        # --- Contributi totali ---
        'BUSTA_CONTRIBUTI_TOTALE': _fmt_eur(ctx.get('contributi', {}).get('totale', 0)),
        'BUSTA_CONTRIBUTI_TRIMESTRALI': _fmt_eur(ctx.get('contributi', {}).get('trimestrale_stima', 0)),
        # --- Trattenute ---
        'BUSTA_CONVIVENZA_TOTALE': _fmt_eur(ctx.get('trattenute', {}).get('convivenza', {}).get('totale', 0)),
        'BUSTA_TOTALE_TRATTENUTE': _fmt_eur(ctx.get('trattenute', {}).get('totale', 0)),
    }

    # --- Blocchi HTML pre-renderizzati per liste dinamiche ---

    # Indennità
    indennita_rows = []
    for i in ctx.get('indennita', []):
        label = i.get('label', '')
        tot = i.get('totale', 0)
        indennita_rows.append(
            f'<tr><td style="color:#8A8F98;">{label}</td>'
            f'<td class="fw-bold text-end">{_fmt_eur(tot)}</td></tr>'
        )
    extra_vars['BUSTA_INDENNITA_HTML'] = '\n'.join(indennita_rows)

    # Ratei (inclusi e accantonati separati)
    ratei_inclusi_rows = []
    ratei_accantonati_rows = []
    for r in ctx.get('ratei_pagati', []):
        label = r.get('label', '')
        totale = r.get('totale', 0)
        incluso = r.get('incluso', False)
        r.get('nota', '')
        if incluso:
            ratei_inclusi_rows.append(
                f'<tr><td style="color:#8A8F98;">{label}</td>'
                f'<td class="fw-bold text-end"><em>incluso</em></td></tr>'
            )
        else:
            ratei_accantonati_rows.append(
                f'<tr><td style="color:#8A8F98;">{label}</td>'
                f'<td class="fw-bold text-end">{_fmt_eur(totale)}</td></tr>'
            )
    extra_vars['BUSTA_RATEI_INCLUSI_HTML'] = '\n'.join(ratei_inclusi_rows)
    extra_vars['BUSTA_RATEI_ACCANTONATI_HTML'] = '\n'.join(ratei_accantonati_rows)

    # Convivenza dettaglio
    conv_dettaglio = ctx.get('trattenute', {}).get('convivenza', {}).get('dettaglio', [])
    if conv_dettaglio:
        extra_vars['BUSTA_CONVIVENZA_DETTAGLIO_HTML'] = ' · '.join(conv_dettaglio)
    else:
        extra_vars['BUSTA_CONVIVENZA_DETTAGLIO_HTML'] = ''

    # Progetti (prima pagina — solo riga informativa)
    progetti = ctx.get('progetti', [])
    if progetti:
        progetti_rows = []
        for p in progetti:
            progetti_rows.append(
                f'<tr><td>{p.get("beneficiario_nome", "")}</td>'
                f'<td>{p.get("tipo_nome", "")}</td>'
                f'<td>{p.get("data_inizio", "")}</td>'
                f'<td>{p.get("indirizzo", "")}</td></tr>'
            )
        extra_vars['BUSTA_PROGETTI_HTML'] = '\n'.join(progetti_rows)
    else:
        extra_vars['BUSTA_PROGETTI_HTML'] = ''

    return extra_vars


# --- download_busta_sostituto_pdf ---
@login_required
@permesso_richiesto('buste.vedi')
@never_cache
@xframe_options_exempt
def download_busta_sostituto_pdf(request, pk):
    """Genera PDF busta paga per il contratto sostituto con budget_override."""
    contratto = get_object_or_404(ContrattoAttivo, pk=pk)
    try:
        mese = int(request.GET.get('mese', date.today().month))
        anno = int(request.GET.get('anno', date.today().year))
    except (ValueError, TypeError):
        return HttpResponse('Parametri non validi', status=400)
    budget_residuo = request.GET.get('budget_residuo')
    if not budget_residuo:
        return HttpResponse('Parametro budget_residuo mancante', status=400)
    try:
        budget_residuo = float(budget_residuo)
    except (ValueError, TypeError):
        return HttpResponse('budget_residuo non valido', status=400)
    if budget_residuo <= 0:
        return HttpResponse('Budget residuo esaurito', status=400)
    toggles_str = request.GET.get('toggles', '')
    toggles = {}
    for t in toggles_str.split(','):
        if '=' in t:
            k, v = t.split('=', 1)
            toggles[k.strip()] = v.strip() == '1'
    convivenza_items = _parse_convivenza_items(request)
    data = _calcola_busta_data(contratto, mese, anno, is_convivente=contratto.is_convivente, convivenza_items=convivenza_items, toggles=toggles, budget_override=budget_residuo)
    if 'errore' in data:
        return HttpResponse(f'Errore: {data["errore"]}', status=400)
    pdf, _ = _genera_busta_completa_pdf_bytes(contratto, mese, anno, ctx_override=data, tipo_override='SOSTITUZIONE')
    if pdf is None:
        return HttpResponse('Errore generazione PDF', status=400)
    cartella = _get_cartella_documenti(contratto)
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    safe_name = contratto.lavoratore.nome_cognome.replace(' ', '_').replace('/', '_')
    nome_file_disk = f"busta_sostituto_{safe_name}_{mese:02d}_{anno}_{timestamp}.pdf"
    full_path = os.path.join(cartella, nome_file_disk)
    with open(full_path, 'wb') as f:
        f.write(pdf)
    d = DocumentoArchiviato.objects.create(
        tipo='SOSTITUZIONE',
        titolo=f"Busta Sostituto {contratto.lavoratore.nome_cognome} {mese:02d}/{anno}",
        file_path=full_path,
        file_size=len(pdf),
        file_name=nome_file_disk,
        contratto=contratto,
        datore=contratto.datore,
        lavoratore=contratto.lavoratore,
        creato_da=request.user if request.user.is_authenticated else None,
    )
    request.session['ultimo_doc_pk'] = d.pk
    _crea_busta_paga_da_ctx(data, contratto, mese, anno, 'SOSTITUZIONE', d)

    if request.GET.get('allega_lul') == '1':
        from paghe.views._lul import _concatena_lul_a_busta
        pdf = _concatena_lul_a_busta(pdf, contratto, mese, anno)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nome_file}"'
    return response


# --- ajax_genera_riepilogo_pdf ---
@login_required
def ajax_genera_riepilogo_pdf(request):
    import json
    data = json.loads(request.body)
    pk = data.get('pk')
    if not pk:
        return JsonResponse({'errore': 'ID contratto non specificato'}, status=400)

    contratto = get_object_or_404(ContrattoAttivo, pk=pk)
    mese = data.get('mese', date.today().month)
    anno = data.get('anno', date.today().year)

    # Costruisci convivenza_items
    convivenza_items = None
    if data.get('incl_pranzo') is not None or data.get('incl_cena') is not None or data.get('incl_alloggio') is not None or data.get('giorni_conv') is not None:
        conv = {}
        if data.get('incl_pranzo') is not None: conv['pranzo'] = data['incl_pranzo'] == '1'
        if data.get('incl_cena') is not None: conv['cena'] = data['incl_cena'] == '1'
        if data.get('incl_alloggio') is not None: conv['alloggio'] = data['incl_alloggio'] == '1'
        if data.get('giorni_conv') is not None:
            try: conv['giorni'] = int(data['giorni_conv'])
            except: pass
        convivenza_items = conv

    # Costruisci toggles
    toggles = {}
    toggle_keys = ['ind_funzione', 'ind_bambini_6', 'ind_piu_assistiti', 'ind_cert_qualita',
                   'scatti', 'rateo_tfr', 'rateo_tfr_separato', 'rateo_anticipo_70',
                   'rateo_13ma', 'rateo_ferie', 'rateo_festivi']
    for k in toggle_keys:
        v = data.get(k)
        if v is not None:
            toggles[k] = v == '1'
    toggles = toggles or None

    ctx = _calcola_busta_data(contratto, mese, anno, convivenza_items=convivenza_items, toggles=toggles)
    if 'errore' in ctx:
        return JsonResponse({'errore': ctx['errore']}, status=400)

    # Genera PDF riepilogo con ReportLab
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    import io

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        topMargin=20*mm, bottomMargin=15*mm,
        leftMargin=15*mm, rightMargin=15*mm)
    styles = getSampleStyleSheet()
    style_title = ParagraphStyle('Titolo', parent=styles['Normal'], fontSize=16, leading=20, spaceAfter=6, alignment=TA_CENTER, textColor=HexColor('#2c5282'), fontName='Helvetica-Bold')
    style_sub = ParagraphStyle('Sottotitolo', parent=styles['Normal'], fontSize=8, leading=10, spaceAfter=14, alignment=TA_CENTER, textColor=HexColor('#666666'))
    style_h = ParagraphStyle('Header', parent=styles['Normal'], fontSize=9, leading=12, spaceAfter=4, textColor=HexColor('#333333'), fontName='Helvetica-Bold')
    style_val = ParagraphStyle('Value', parent=styles['Normal'], fontSize=9, leading=12, textColor=HexColor('#111111'))
    style_label = ParagraphStyle('Label', parent=styles['Normal'], fontSize=9, leading=12, textColor=HexColor('#666666'))
    style_total = ParagraphStyle('Total', parent=styles['Normal'], fontSize=11, leading=14, textColor=HexColor('#2c5282'), fontName='Helvetica-Bold')
    style_netto = ParagraphStyle('Netto', parent=styles['Normal'], fontSize=14, leading=18, textColor=HexColor('#2c5282'), fontName='Helvetica-Bold')
    style_footer = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=7, leading=9, textColor=HexColor('#999999'), alignment=TA_CENTER)

    elements = []
    elements.append(Paragraph('RIEPILOGO BUSTA PAGA', style_title))
    elements.append(Paragraph(f'{contratto.lavoratore.nome_cognome} — {contratto.datore.nome_cognome} — {mese:02d}/{anno}', style_sub))
    elements.append(HRFlowable(width='100%', thickness=0.5, color=HexColor('#cccccc')))
    elements.append(Spacer(1, 6*mm))

    # Info contratto
    info_data = [
        ['Lavoratore:', contratto.lavoratore.nome_cognome, 'Datore:', contratto.datore.nome_cognome],
    ]
    if contratto.lavoratore.codice_fiscale:
        info_data.append(['CF Lavoratore:', contratto.lavoratore.codice_fiscale, 'CF Datore:', contratto.datore.codice_fiscale])
    if ctx.get('livello_codice'):
        info_data.append(['Livello:', ctx['livello_codice'], 'Ore mensili:', f'{ctx.get("ore_mensili",0):.2f} h'])
    info_data.append(['Tipo calcolo:', 'STANDARD', 'Periodo:', f'{mese:02d}/{anno}'])
    info_table = Table(info_data, colWidths=[45*mm, 55*mm, 45*mm, 55*mm])
    info_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#555555')),
        ('TEXTCOLOR', (1, 0), (1, -1), HexColor('#111111')),
        ('TEXTCOLOR', (3, 0), (3, -1), HexColor('#111111')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6*mm))
    elements.append(HRFlowable(width='100%', thickness=0.5, color=HexColor('#cccccc')))
    elements.append(Spacer(1, 4*mm))

    # Funzione per creare sezioni
    def section(title, rows):
        els = []
        els.append(Paragraph(title, style_h))
        t = Table(rows, colWidths=[100*mm, 55*mm])
        t.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#666666')),
            ('TEXTCOLOR', (1, 0), (1, -1), HexColor('#111111')),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('LINEBELOW', (0, 0), (-1, -2), 0.3, HexColor('#eeeeee')),
        ]))
        if len(rows) > 1:
            t.setStyle(TableStyle([
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (0, -1), (-1, -1), HexColor('#2c5282')),
                ('LINEABOVE', (0, -1), (-1, -1), 0.5, HexColor('#2c5282')),
                ('TOPPADDING', (0, -1), (-1, -1), 4),
            ]))
        els.append(t)
        els.append(Spacer(1, 4*mm))
        return els

    # Retribuzione Lorda
    lordo_rows = [
        [f'Paga base (\u20AC{ctx["paga_base"]["orario"]:.4f} x {ctx["ore_mensili"]}h)', f'\u20AC {ctx["paga_base"]["totale"]:.2f}'],
    ]
    for ind in ctx.get('indennita', []):
        lordo_rows.append([f'{ind["label"]} (\u20AC{ind["orario"]:.4f} x {ctx["ore_mensili"]}h)', f'\u20AC {ind["totale"]:.2f}'])
    lordo_rows.append([f'Scatti anzianit\u00e0 ({ctx["scatti_anzianita"]["dettaglio"]})', f'\u20AC {ctx["scatti_anzianita"]["valore"]:.2f}'])
    for rp in ctx.get('ratei_pagati', []):
        if rp.get('incluso'):
            lordo_rows.append([f'{rp["label"]} (*)', f'\u20AC {rp["totale"]:.2f}'])
    lordo_rows.append(['TOTALE LORDO', f'\u20AC {ctx["totale_lordo"]:.2f}'])
    elements.extend(section('RETRIBUZIONE LORDA', lordo_rows))

    # Contributi
    contr_rows = [
        [f'INPS ({ctx["contributi"]["inps"]["fascia"]})', f'\u20AC {ctx["contributi"]["inps"]["totale"]:.2f}'],
        [f'{ctx["contributi"]["cassa"]["nome"] or "Cassa/Ente"}', f'\u20AC {ctx["contributi"]["cassa"]["totale"]:.2f}'],
        ['TOTALE CONTRIBUTI', f'\u20AC {ctx["contributi"]["totale"]:.2f}'],
    ]
    elements.extend(section('CONTRIBUTI', contr_rows))

    # Trattenute
    trarr_rows = [
        ['Convivenza', f'\u20AC {ctx["trattenute"]["convivenza"]["totale"]:.2f}'],
        ['Ratei accantonati', f'\u20AC {ctx["trattenute"]["ratei_accantonati"]:.2f}'],
    ]
    if ctx['trattenute']['totale'] > 0:
        trarr_rows.append(['TOTALE TRATTENUTE', f'\u20AC {ctx["trattenute"]["totale"]:.2f}'])
    elements.extend(section('TRATTENUTE', trarr_rows))

    # Riepilogo finale
    budget = ctx.get('budget_mensile', 0)
    usato = budget - ctx.get('verifica_copertura', 0)
    perc = min(max((usato / budget) * 100, 0), 100) if budget else 0
    riep_rows = [
        ['Budget mensile', f'\u20AC {budget:.2f}'],
        [f'Copertura budget', f'{perc:.0f}%'],
    ]
    if ctx.get('modalita_tfr') and ctx['modalita_tfr'] != 'INCLUSO':
        riep_rows.append(['TFR accumulato', f'\u20AC {float(ctx.get("tfr_accantonato_cumulativo", 0)):.2f}'])
    riep_rows.append(['NETTO IN BUSTA', f'\u20AC {ctx["netto"]:.2f}'])
    elements.extend(section('RIEPILOGO', riep_rows))

    # Dettaglio progetti
    if ctx.get('progetti') and len(ctx['progetti']) > 0:
        elements.append(Paragraph('PROGETTI COLLEGATI', style_h))
        proj_rows = []
        for pr in ctx['progetti']:
            proj_rows.append([pr.get('nome', '—'), pr.get('budget_mensile', 0)])
        if proj_rows:
            pt = Table(proj_rows, colWidths=[130*mm, 40*mm])
            pt.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#666666')),
                ('TEXTCOLOR', (1, 0), (1, -1), HexColor('#333333')),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ]))
            elements.append(pt)

    elements.append(Spacer(1, 10*mm))
    elements.append(HRFlowable(width='100%', thickness=0.3, color=HexColor('#cccccc')))
    elements.append(Spacer(1, 3*mm))
    elements.append(Paragraph(f'Documento generato il {timezone.now().strftime("%d/%m/%Y %H:%M")} — Gestione Colf', style_footer))

    doc.build(elements)
    pdf = buf.getvalue()

    # Salva su disco e crea DocumentoArchiviato
    nome_file = f"riepilogo_{contratto.lavoratore.nome_cognome.replace(' ','_')}_{mese:02d}_{anno}.pdf"
    cartella = _get_cartella_documenti(contratto)
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    safe_name = contratto.lavoratore.nome_cognome.replace(' ', '_').replace('/', '_')
    nome_file_disk = f"riepilogo_{safe_name}_{mese:02d}_{anno}_{timestamp}.pdf"
    full_path = os.path.join(cartella, nome_file_disk)
    with open(full_path, 'wb') as f:
        f.write(pdf)

    d = DocumentoArchiviato.objects.create(
        tipo='ALTRO',
        titolo=f"Riepilogo Busta Paga {contratto.lavoratore.nome_cognome} {mese:02d}/{anno}",
        file_path=full_path,
        file_size=len(pdf),
        file_name=nome_file_disk,
        contratto=contratto,
        datore=contratto.datore,
        lavoratore=contratto.lavoratore,
        creato_da=request.user if request.user.is_authenticated else None,
    )
    request.session['ultimo_doc_pk'] = d.pk

    return JsonResponse({'success': True, 'url': f'/ajax/vedi-documento/{d.pk}/', 'pk': d.pk})


# --- download_busta_notturna_pdf ---
@login_required
@permesso_richiesto('buste.vedi')
@never_cache
@xframe_options_exempt
def download_busta_notturna_pdf(request, pk):
    contratto = get_object_or_404(ContrattoAttivo, pk=pk)
    try:
        mese = int(request.GET.get('mese', date.today().month))
        anno = int(request.GET.get('anno', date.today().year))
    except (ValueError, TypeError):
        mese = date.today().month
        anno = date.today().year
    p = contratto.parametri_minimi
    if not p:
        return HttpResponse('Parametri CCNL non impostati', status=400)
    ore_mensili = float(contratto.ore_mensili_calcolate)
    tipo_notturno = request.GET.get('tipo_notturno', 'presenza')
    ore_notturne = float(request.GET.get('ore_notturne', 0) or 0)
    rateo_tfr = request.GET.get('rateo_tfr', '1') == '1'
    rateo_13ma = request.GET.get('rateo_13ma', '1') == '1'
    rateo_ferie = request.GET.get('rateo_ferie', '1') == '1'
    rateo_festivi = request.GET.get('rateo_festivi', '1') == '1'
    straord_nott = request.GET.get('straord_nott', '0') == '1'
    ore_straord_nott = float(request.GET.get('ore_straord_nott', 0) or 0)
    festivo_nott = request.GET.get('festivo_nott', '0') == '1'
    ore_festive_nott = float(request.GET.get('ore_festive_nott', 0) or 0)

    if tipo_notturno == 'presenza':
        importo_mensile = float(p.ind_notturno_presenza)
    elif tipo_notturno == 'assistenza':
        importo_mensile = float(p.ind_notturno_assistenza)
    else:
        if ore_notturne <= 0:
            return HttpResponse('Inserire ore notturne', status=400)
        base_nott = float(p.ind_notturno_base) if p.ind_notturno_base and float(p.ind_notturno_base) > 0 else float(p.paga_base)
        coeff_20 = float(p.ind_notturno_20) if p.ind_notturno_20 and float(p.ind_notturno_20) > 0 else 1.20
        paga_oraria = round(base_nott * coeff_20, 4)
        importo_mensile = round(paga_oraria * ore_notturne, 2)

    ratei = []
    totale_ratei = 0.0
    mapping = [
        ('TFR', float(p.notturno_tfr), rateo_tfr),
        ('Tredicesima', float(p.notturno_13ma), rateo_13ma),
        ('Ferie', float(p.notturno_ferie), rateo_ferie),
        ('Festivi', float(p.notturno_festivi), rateo_festivi),
    ]
    for label, val, attivo in mapping:
        if attivo and val != 0:
            totale = round(val * ore_mensili, 2)
            ratei.append({'label': label, 'orario': val, 'totale': totale})
            totale_ratei += totale

    if tipo_notturno == 'a_ore':
        if straord_nott and ore_straord_nott > 0:
            importo_sn = round(paga_oraria * 1.5 * ore_straord_nott, 2)
            ratei.append({'label': 'Straordinario Notturno (50%)', 'orario': round(paga_oraria * 1.5, 4), 'totale': importo_sn})
            totale_ratei += importo_sn
        if festivo_nott and ore_festive_nott > 0:
            importo_fn = round(paga_oraria * 1.6 * ore_festive_nott, 2)
            ratei.append({'label': 'Festivo/Domenicale Notturno (60%)', 'orario': round(paga_oraria * 1.6, 4), 'totale': importo_fn})
            totale_ratei += importo_fn
    tot = round(importo_mensile + totale_ratei, 2)
    # Costruisce ctx compatibile con _genera_busta_completa_pdf_bytes
    base_ctx = _calcola_busta_data(contratto, mese, anno)
    if 'errore' in base_ctx:
        return HttpResponse(f'Errore: {base_ctx["errore"]}', status=400)
    ratei_pagati_nott = [{'label': r['label'], 'orario': r['orario'], 'totale': r['totale'], 'incluso': True} for r in ratei]
    base_ctx.update({
        'tipo_calcolo': 'NOTTURNO',
        'paga_base': {'totale': importo_mensile, 'orario': importo_mensile / ore_mensili if ore_mensili > 0 else 0},
        'indennita': [],
        'scatti_anzianita': {'valore': 0, 'dettaglio': ''},
        'ratei_pagati': ratei_pagati_nott,
        'totale_indennita': 0,
        'totale_ratei_inclusi': sum(r['totale'] for r in ratei_pagati_nott),
        'totale_lordo': tot,
        'contributi': {'totale': 0, 'inps': {'totale': 0, 'orario': 0, 'fascia': ''}, 'cassa': {'nome': '', 'totale': 0, 'orario': 0}, 'trimestrale_stima': 0},
        'trattenute': {'totale': 0, 'convivenza': {'totale': 0, 'dettaglio': []}, 'ratei_accantonati': 0},
        'budget_mensile': tot,
        'netto': tot,
        'verifica_copertura': 0,
        'note_datore': "Indennit\u00e0 aggiuntiva — contributi gi\u00e0 gestiti nella busta ordinaria",
        'paga_applicata_oraria': importo_mensile / ore_mensili if ore_mensili > 0 else 0,
        'paga_applicata_mensile': importo_mensile,
    })
    pdf, _ = _genera_busta_completa_pdf_bytes(contratto, mese, anno, ctx_override=base_ctx, tipo_override='NOTTURNO')
    if pdf is None:
        return HttpResponse('Errore generazione PDF', status=400)
    cartella = _get_cartella_documenti(contratto)
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    safe_name = contratto.lavoratore.nome_cognome.replace(' ', '_').replace('/', '_')
    nome_file_disk = f"busta_notturna_{safe_name}_{mese:02d}_{anno}_{timestamp}.pdf"
    full_path = os.path.join(cartella, nome_file_disk)
    with open(full_path, 'wb') as f:
        f.write(pdf)
    d = DocumentoArchiviato.objects.create(
        tipo='NOTTURNO',
        titolo=f"Busta Notturna {contratto.lavoratore.nome_cognome} {mese:02d}/{anno}",
        file_path=full_path,
        file_size=len(pdf),
        file_name=nome_file_disk,
        contratto=contratto,
        datore=contratto.datore,
        lavoratore=contratto.lavoratore,
        creato_da=request.user if request.user.is_authenticated else None,
    )
    request.session['ultimo_doc_pk'] = d.pk
    _crea_busta_paga_da_ctx(base_ctx, contratto, mese, anno, 'NOTTURNO', d)

    if request.GET.get('allega_lul') == '1':
        from paghe.views._lul import _concatena_lul_a_busta
        pdf = _concatena_lul_a_busta(pdf, contratto, mese, anno)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="notturno_{safe_name}_{mese:02d}_{anno}.pdf"'
    return response


# --- download_busta_malattia_pdf ---
@login_required
@permesso_richiesto('buste.vedi')
@never_cache
@xframe_options_exempt
def download_busta_malattia_pdf(request, pk):
    contratto = get_object_or_404(ContrattoAttivo, pk=pk)
    try:
        mese = int(request.GET.get('mese', date.today().month))
        anno = int(request.GET.get('anno', date.today().year))
        giorni_malattia = int(request.GET.get('giorni_malattia', 0))
    except (ValueError, TypeError):
        return HttpResponse('Parametri non validi', status=400)
    if giorni_malattia <= 0:
        return HttpResponse('Inserire giorni malattia', status=400)
    sostituzione = request.GET.get('sostituzione', '0') == '1'
    ricaduta = request.GET.get('ricaduta', '0') == '1'
    ricoverato = request.GET.get('ricoverato', '0') == '1'
    p = contratto.parametri_minimi
    if not p:
        return HttpResponse('Parametri CCNL non impostati', status=400)
    ore_mensili = float(contratto.ore_mensili_calcolate)
    if ore_mensili <= 0:
        return HttpResponse('Ore mensili pari a zero', status=400)
    anzianita_mesi = (date(anno, mese, 1) - contratto.data_assunzione).days // 30
    if anzianita_mesi < 6:
        max_giorni = 8
    elif anzianita_mesi < 24:
        max_giorni = 12
    else:
        max_giorni = 15
    giorni_pagati = min(giorni_malattia, max_giorni)
    if sostituzione:
        retr_sost = float(p.retribuzione_sostituzione) if p.retribuzione_sostituzione else None
        paga_oraria = retr_sost if retr_sost and retr_sost > 0 else float(p.paga_base)
    else:
        paga_oraria = float(p.paga_base)
    ore_giornaliere = ore_mensili / 26
    retribuzione_giornaliera = round(paga_oraria * ore_giornaliere, 4)
    is_convivente = contratto.is_convivente
    if ricaduta:
        giorni_50 = 0
        giorni_100 = giorni_pagati
        importo_50 = 0
        importo_100 = round(retribuzione_giornaliera * 1.0 * giorni_pagati, 2)
    else:
        giorni_50 = min(giorni_pagati, 3)
        giorni_100 = giorni_pagati - giorni_50
        importo_50 = round(retribuzione_giornaliera * 0.5 * giorni_50, 2)
        importo_100 = round(retribuzione_giornaliera * 1.0 * giorni_100, 2)
    indennita_va = 0
    vitto_alloggio_gg = 0
    if ricoverato and is_convivente:
        vitto_alloggio_gg = round(float(p.convivenza_pranzo or 0) + float(p.convivenza_cena or 0) + float(p.convivenza_alloggio or 0), 2)
        indennita_va = round(vitto_alloggio_gg * giorni_pagati, 2)
    importo_totale = round(importo_50 + importo_100 + indennita_va, 2)
    # Costruisce ctx compatibile con _genera_busta_completa_pdf_bytes
    base_ctx = _calcola_busta_data(contratto, mese, anno)
    if 'errore' in base_ctx:
        return HttpResponse(f'Errore: {base_ctx["errore"]}', status=400)
    indennita_mal = []
    if ricaduta:
        indennita_mal.append({'label': f'Ricaduta stessa malattia — 100% ({giorni_100} gg)', 'orario': 0, 'totale': importo_100})
    else:
        if giorni_50 > 0:
            indennita_mal.append({'label': f'50% — primi {giorni_50} gg', 'orario': 0, 'totale': importo_50})
        if giorni_100 > 0:
            indennita_mal.append({'label': f'100% — dal 4\u00b0 giorno ({giorni_100} gg)', 'orario': 0, 'totale': importo_100})
    if indennita_va > 0:
        indennita_mal.append({'label': f'Indennit\u00e0 sostitutiva vitto/alloggio ({vitto_alloggio_gg}\u20ac/gg \u00d7 {giorni_pagati} gg)', 'orario': 0, 'totale': indennita_va})
    _nota_malattia = (
        "La malattia nel lavoro domestico \u00e8 interamente a carico del datore di lavoro. "
        "Nessun rimborso INPS \u00e8 previsto. "
        "Indennit\u00e0 aggiuntiva — contributi gi\u00e0 gestiti nella busta ordinaria."
    )
    base_ctx.update({
        'tipo_calcolo': 'MALATTIA',
        'paga_base': {'totale': importo_totale, 'orario': retribuzione_giornaliera},
        'indennita': indennita_mal,
        'scatti_anzianita': {'valore': 0, 'dettaglio': ''},
        'ratei_pagati': [],
        'totale_indennita': 0,
        'totale_ratei_inclusi': 0,
        'totale_lordo': importo_totale,
        'contributi': {'totale': 0, 'inps': {'totale': 0, 'orario': 0, 'fascia': ''}, 'cassa': {'nome': '', 'totale': 0, 'orario': 0}, 'trimestrale_stima': 0},
        'trattenute': {'totale': 0, 'convivenza': {'totale': 0, 'dettaglio': []}, 'ratei_accantonati': 0},
        'budget_mensile': importo_totale,
        'netto': importo_totale,
        'verifica_copertura': 0,
        'note_datore': _nota_malattia,
        'paga_applicata_oraria': retribuzione_giornaliera,
        'paga_applicata_mensile': importo_totale,
    })
    pdf, _ = _genera_busta_completa_pdf_bytes(contratto, mese, anno, ctx_override=base_ctx, tipo_override='MALATTIA')
    if pdf is None:
        return HttpResponse('Errore generazione PDF', status=400)
    cartella = _get_cartella_documenti(contratto)
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    safe_name = contratto.lavoratore.nome_cognome.replace(' ', '_').replace('/', '_')
    nome_file_disk = f"busta_malattia_{safe_name}_{mese:02d}_{anno}_{timestamp}.pdf"
    full_path = os.path.join(cartella, nome_file_disk)
    with open(full_path, 'wb') as f:
        f.write(pdf)
    d = DocumentoArchiviato.objects.create(
        tipo='MALATTIA',
        titolo=f"Busta Malattia {contratto.lavoratore.nome_cognome} {mese:02d}/{anno}",
        file_path=full_path,
        file_size=len(pdf),
        file_name=nome_file_disk,
        contratto=contratto,
        datore=contratto.datore,
        lavoratore=contratto.lavoratore,
        creato_da=request.user if request.user.is_authenticated else None,
    )
    request.session['ultimo_doc_pk'] = d.pk
    _crea_busta_paga_da_ctx(base_ctx, contratto, mese, anno, 'MALATTIA', d)

    if request.GET.get('allega_lul') == '1':
        from paghe.views._lul import _concatena_lul_a_busta
        pdf = _concatena_lul_a_busta(pdf, contratto, mese, anno)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="malattia_{safe_name}_{mese:02d}_{anno}.pdf"'
    return response


# --- download_busta_inversa_pdf ---
@login_required
@permesso_richiesto('buste.vedi')
@never_cache
@xframe_options_exempt
def download_busta_inversa_pdf(request, pk):
    contratto = get_object_or_404(ContrattoAttivo, pk=pk)
    try:
        mese = int(request.GET.get('mese', date.today().month))
        anno = int(request.GET.get('anno', date.today().year))
    except (ValueError, TypeError):
        mese = date.today().month
        anno = date.today().year

    ore_mensili = request.GET.get('ore_mensili')
    ore_settimanali = request.GET.get('ore_settimanali')
    lordo = request.GET.get('lordo')
    netto = request.GET.get('netto')

    kwargs = {'contratto': contratto, 'mese': mese, 'anno': anno}
    if ore_mensili is not None:
        try: kwargs['ore_mensili'] = float(ore_mensili)
        except ValueError: logger.warning('ore_mensili non valido: %s', ore_mensili)
    elif ore_settimanali is not None:
        try: kwargs['ore_settimanali'] = float(ore_settimanali)
        except ValueError: logger.warning('ore_settimanali non valido: %s', ore_settimanali)
    elif lordo is not None:
        try: kwargs['lordo_target'] = float(lordo)
        except ValueError: logger.warning('lordo non valido: %s', lordo)
    elif netto is not None:
        try: kwargs['netto_target'] = float(netto)
        except ValueError: logger.warning('netto non valido: %s', netto)

    convivenza_items = _parse_convivenza_items(request)
    ctx = _calcola_busta_inversa_data(convivenza_items=convivenza_items, toggles=_parse_toggles(request), **kwargs)
    if 'errore' in ctx:
        return JsonResponse({'errore': ctx['errore']}, status=400)

    nome_file = f"busta_inversa_{contratto.lavoratore.nome_cognome.replace(' ', '_')}_{mese:02d}_{anno}.pdf"
    cartella = _get_cartella_documenti(contratto)
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    safe_name = contratto.lavoratore.nome_cognome.replace(' ', '_').replace('/', '_')
    nome_file_disk = f"busta_inversa_{safe_name}_{mese:02d}_{anno}_{timestamp}.pdf"
    full_path = os.path.join(cartella, nome_file_disk)

    progetti_data = _calcola_progetti_data(ctx, contratto) if ctx.get('progetti') else None

    if request.GET.get('offusca') == '1':
        _offusca_ctx_anagrafici(ctx)
        if progetti_data and 'righe' in progetti_data:
            for r in progetti_data['righe']:
                r['nome'] = 'Progetto'
            ctx['progetti_data'] = progetti_data

    template_testo = contratto.busta_template if contratto.busta_template and contratto.busta_template.tipo == 'BUSTA_PAGA' else None
    pdf = None
    if template_testo:
        html_busta = _genera_html_busta(ctx, progetti_data)
        extra_vars = _build_busta_extra_vars(ctx, html_busta)
        corpo_risolto = _risolvi_variabili_testo(template_testo.corpo_testo, contratto, extra_vars=extra_vars)
        oggetto_risolto = _risolvi_variabili_testo(template_testo.oggetto_titolo or '', contratto, extra_vars=extra_vars)
        try:
            _pdf_buffer = _genera_pdf_da_testo(
                tipo='CALCOLO_INVERSO',
                titolo=oggetto_risolto,
                corpo=corpo_risolto,
                output_path=full_path
            )
            if _pdf_buffer is not None:
                pdf = _pdf_buffer.getvalue()
        except Exception:
            logger.exception("Errore in download_busta_inversa_pdf")
            pdf = None

    if pdf is None:
        pdf, _ = _genera_busta_completa_pdf_bytes(contratto, mese, anno, ctx_override=ctx, tipo_override='CALCOLO_INVERSO')
        if pdf is None:
            return JsonResponse({'errore': 'Errore generazione PDF'}, status=400)

    with open(full_path, 'wb') as f:
        f.write(pdf)
    d = DocumentoArchiviato.objects.create(
        tipo='CALCOLO_INVERSO',
        titolo=f"Busta Calcolo Inverso {contratto.lavoratore.nome_cognome} {mese:02d}/{anno}",
        file_path=full_path,
        file_size=len(pdf),
        file_name=nome_file_disk,
        contratto=contratto,
        datore=contratto.datore,
        lavoratore=contratto.lavoratore,
        creato_da=request.user if request.user.is_authenticated else None,
    )
    request.session['ultimo_doc_pk'] = d.pk
    _crea_busta_paga_da_ctx(ctx, contratto, mese, anno, 'CALCOLO_INVERSO', d)

    if request.GET.get('allega_lul') == '1':
        from paghe.views._lul import _concatena_lul_a_busta
        pdf = _concatena_lul_a_busta(pdf, contratto, mese, anno)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nome_file}"'
    return response


# --- download_ricevuta_pdf ---
@login_required
@permesso_richiesto('buste.vedi')
def download_ricevuta_pdf(request, pk):
    busta = get_object_or_404(BustaPaga, pk=pk)
    pdf, nome_file = _genera_ricevuta_pdf_bytes(busta)
    if not pdf:
        return JsonResponse({'errore': 'Errore generazione ricevuta'}, status=400)
    cartella = _get_cartella_documenti(busta.contratto)
    timezone.now().strftime('%Y%m%d_%H%M%S')
    full_path = os.path.join(cartella, f"ricevuta_{nome_file}")
    with open(full_path, 'wb') as f:
        f.write(pdf)
    DocumentoArchiviato.objects.create(
        tipo='RICEVUTA',
        titolo=nome_file,
        file_path=full_path,
        file_name=nome_file,
        file_size=len(pdf),
        contratto=busta.contratto,
        datore=busta.contratto.datore,
        lavoratore=busta.contratto.lavoratore,
        creato_da=request.user if request.user.is_authenticated else None,
    )
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nome_file}"'
    return response

# --- download_busta_pdf ---
@login_required
@permesso_richiesto('buste.vedi')
@xframe_options_exempt
def download_busta_pdf(request, pk):
    contratto = get_object_or_404(ContrattoAttivo, pk=pk)
    try:
        mese = int(request.GET.get('mese', date.today().month))
        anno = int(request.GET.get('anno', date.today().year))
    except (ValueError, TypeError):
        mese = date.today().month
        anno = date.today().year

    convivenza_items = _parse_convivenza_items(request)
    ctx = _calcola_busta_data(contratto, mese, anno, convivenza_items=convivenza_items, toggles=_parse_toggles(request))
    if 'errore' in ctx:
        return JsonResponse({'errore': ctx['errore']}, status=400)

    progetti_data = _calcola_progetti_data(ctx, contratto) if ctx.get('progetti') else None

    nome_file = f"busta_{contratto.lavoratore.nome_cognome.replace(' ', '_')}_{mese:02d}_{anno}.pdf"
    cartella = _get_cartella_documenti(contratto)
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    safe_name = contratto.lavoratore.nome_cognome.replace(' ', '_').replace('/', '_')
    nome_file_disk = f"busta_{safe_name}_{mese:02d}_{anno}_{timestamp}.pdf"
    full_path = os.path.join(cartella, nome_file_disk)

    # Template selezionato sul contratto, o None → ReportLab standard
    template_testo = contratto.busta_template if contratto.busta_template and contratto.busta_template.tipo == 'BUSTA_PAGA' else None
    pdf = None
    if template_testo:
        # Genera HTML busta e risolvi template
        html_busta = _genera_html_busta(ctx, progetti_data)
        extra_vars = _build_busta_extra_vars(ctx, html_busta)
        corpo_risolto = _risolvi_variabili_testo(template_testo.corpo_testo, contratto, extra_vars=extra_vars)
        oggetto_risolto = _risolvi_variabili_testo(template_testo.oggetto_titolo or '', contratto, extra_vars=extra_vars)

        # Prova _genera_pdf_da_testo (ReportLab primario, xhtml2pdf fallback)
        try:
            _pdf_buffer = _genera_pdf_da_testo(
                tipo='PAGA_STANDARD',
                titolo=oggetto_risolto,
                corpo=corpo_risolto,
                output_path=full_path
            )
            if _pdf_buffer is not None:
                pdf = _pdf_buffer.getvalue()
        except Exception:
            logger.exception("Errore in download_busta_pdf")
            pdf = None

    if pdf is None:
        # Fallback ReportLab con lo stesso ctx (include convivenza_items)
        pdf, _ = _genera_busta_completa_pdf_bytes(contratto, mese, anno, ctx_override=ctx)
        if pdf is None:
            return JsonResponse({'errore': 'Errore generazione PDF'}, status=400)

    with open(full_path, 'wb') as f:
        f.write(pdf)
    d = DocumentoArchiviato.objects.create(
        tipo='PAGA_STANDARD',
        titolo=f"Busta Paga {contratto.lavoratore.nome_cognome} {mese:02d}/{anno}",
        file_path=full_path,
        file_size=len(pdf),
        file_name=nome_file_disk,
        contratto=contratto,
        datore=contratto.datore,
        lavoratore=contratto.lavoratore,
        creato_da=request.user if request.user.is_authenticated else None,
    )
    request.session['ultimo_doc_pk'] = d.pk
    _crea_busta_paga_da_ctx(ctx, contratto, mese, anno, 'STANDARD', d)

    if request.GET.get('allega_lul') == '1':
        from paghe.views._lul import _concatena_lul_a_busta
        pdf = _concatena_lul_a_busta(pdf, contratto, mese, anno)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nome_file}"'
    return response


# --- download_busta_non_convivente_pdf ---
@login_required
@permesso_richiesto('buste.vedi')
@never_cache
@xframe_options_exempt
def download_busta_non_convivente_pdf(request, pk):
    contratto = get_object_or_404(ContrattoAttivo, pk=pk)
    try:
        mese = int(request.GET.get('mese', date.today().month))
        anno = int(request.GET.get('anno', date.today().year))
    except (ValueError, TypeError):
        mese = date.today().month
        anno = date.today().year
    sostituzione = request.GET.get('sostituzione') == '1'
    convivenza_items = _parse_convivenza_items(request)
    ctx = _calcola_busta_data(contratto, mese, anno, is_convivente=False, sostituzione=sostituzione, convivenza_items=convivenza_items, toggles=_parse_toggles(request))
    if 'errore' in ctx:
        return JsonResponse({'errore': ctx['errore']}, status=400)

    nome_file = f"busta_nonconv_{contratto.lavoratore.nome_cognome.replace(' ', '_')}_{mese:02d}_{anno}.pdf"
    cartella = _get_cartella_documenti(contratto)
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    safe_name = contratto.lavoratore.nome_cognome.replace(' ', '_').replace('/', '_')
    tipo_label = 'sostituzione_' if sostituzione else ''
    nome_file_disk = f"busta_nonconv_{tipo_label}{safe_name}_{mese:02d}_{anno}_{timestamp}.pdf"
    full_path = os.path.join(cartella, nome_file_disk)

    progetti_data = _calcola_progetti_data(ctx, contratto) if ctx.get('progetti') else None

    template_testo = contratto.busta_template if contratto.busta_template and contratto.busta_template.tipo == 'BUSTA_PAGA' else None
    pdf = None
    if template_testo:
        html_busta = _genera_html_busta(ctx, progetti_data)
        extra_vars = _build_busta_extra_vars(ctx, html_busta)
        corpo_risolto = _risolvi_variabili_testo(template_testo.corpo_testo, contratto, extra_vars=extra_vars)
        oggetto_risolto = _risolvi_variabili_testo(template_testo.oggetto_titolo or '', contratto, extra_vars=extra_vars)

        try:
            _pdf_buffer = _genera_pdf_da_testo(
                tipo='NON_CONVIVENTE',
                titolo=oggetto_risolto,
                corpo=corpo_risolto,
                output_path=full_path
            )
            if _pdf_buffer is not None:
                pdf = _pdf_buffer.getvalue()
        except Exception:
            logger.exception("Errore in download_busta_non_convivente_pdf")
            pdf = None

    if pdf is None:
        pdf, _ = _genera_busta_completa_pdf_bytes(contratto, mese, anno, ctx_override=ctx, tipo_override='NON_CONVIVENTE')
        if pdf is None:
            return JsonResponse({'errore': 'Errore generazione PDF'}, status=400)

    with open(full_path, 'wb') as f:
        f.write(pdf)
    d = DocumentoArchiviato.objects.create(
        tipo='NON_CONVIVENTE',
        titolo=f"Busta Non Convivente {contratto.lavoratore.nome_cognome} {mese:02d}/{anno}",
        file_path=full_path,
        file_size=len(pdf),
        file_name=nome_file_disk,
        contratto=contratto,
        datore=contratto.datore,
        lavoratore=contratto.lavoratore,
        creato_da=request.user if request.user.is_authenticated else None,
    )
    request.session['ultimo_doc_pk'] = d.pk
    _crea_busta_paga_da_ctx(ctx, contratto, mese, anno, 'NON_CONVIVENTE', d)

    if request.GET.get('allega_lul') == '1':
        from paghe.views._lul import _concatena_lul_a_busta
        pdf = _concatena_lul_a_busta(pdf, contratto, mese, anno)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nome_file}"'
    return response


# --- download_busta_conviventi_ccnl_pdf ---
@login_required
@permesso_richiesto('buste.vedi')
@never_cache
@xframe_options_exempt
def download_busta_conviventi_ccnl_pdf(request, pk):
    contratto = get_object_or_404(ContrattoAttivo, pk=pk)
    try:
        mese = int(request.GET.get('mese', date.today().month))
        anno = int(request.GET.get('anno', date.today().year))
    except (ValueError, TypeError):
        mese = date.today().month
        anno = date.today().year
    tipo_orario = request.GET.get('tipo_orario', 'FT')
    toggles = {
        'ind_funzione': request.GET.get('ind_funzione') == '1',
        'ind_bambini_6': request.GET.get('ind_bambini_6') == '1',
        'ind_piu_assistiti': request.GET.get('ind_piu_assistiti') == '1',
        'ind_cert_qualita': request.GET.get('ind_cert_qualita') == '1',
        'scatti': request.GET.get('scatti') == '1',
        'rateo_tfr': request.GET.get('rateo_tfr') == '1',
        'rateo_13ma': request.GET.get('rateo_13ma') == '1',
        'rateo_ferie': request.GET.get('rateo_ferie') == '1',
        'rateo_festivi': request.GET.get('rateo_festivi') == '1',
    }
    convivenza_items = _parse_convivenza_items(request)
    ctx = _calcola_busta_conviventi_ccnl_data(contratto, mese, anno, tipo_orario=tipo_orario, toggles=toggles, convivenza_items=convivenza_items)
    if 'errore' in ctx:
        return JsonResponse({'errore': ctx['errore']}, status=400)

    nome_file = f"busta_ccnl_{contratto.lavoratore.nome_cognome.replace(' ', '_')}_{mese:02d}_{anno}.pdf"
    cartella = _get_cartella_documenti(contratto)
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    safe_name = contratto.lavoratore.nome_cognome.replace(' ', '_').replace('/', '_')
    nome_file_disk = f"busta_ccnl_{safe_name}_{mese:02d}_{anno}_{timestamp}.pdf"
    full_path = os.path.join(cartella, nome_file_disk)

    progetti_data = _calcola_progetti_data(ctx, contratto) if ctx.get('progetti') else None

    template_testo = contratto.busta_template if contratto.busta_template and contratto.busta_template.tipo == 'BUSTA_PAGA' else None
    pdf = None
    if template_testo:
        html_busta = _genera_html_busta(ctx, progetti_data)
        extra_vars = _build_busta_extra_vars(ctx, html_busta)
        corpo_risolto = _risolvi_variabili_testo(template_testo.corpo_testo, contratto, extra_vars=extra_vars)
        oggetto_risolto = _risolvi_variabili_testo(template_testo.oggetto_titolo or '', contratto, extra_vars=extra_vars)

        try:
            _pdf_buffer = _genera_pdf_da_testo(
                tipo='CONVIVENTI_CCNL',
                titolo=oggetto_risolto,
                corpo=corpo_risolto,
                output_path=full_path
            )
            if _pdf_buffer is not None:
                pdf = _pdf_buffer.getvalue()
        except Exception:
            logger.exception("Errore in download_busta_conviventi_ccnl_pdf")
            pdf = None

    if pdf is None:
        pdf, _ = _genera_busta_completa_pdf_bytes(contratto, mese, anno, ctx_override=ctx, tipo_override='CONVIVENTI_CCNL')
        if pdf is None:
            return JsonResponse({'errore': 'Errore generazione PDF'}, status=400)

    with open(full_path, 'wb') as f:
        f.write(pdf)

    d = DocumentoArchiviato.objects.create(
        tipo='CONVIVENTI_CCNL',
        titolo=nome_file_disk,
        file_path=full_path,
        file_name=nome_file_disk,
        file_size=len(pdf),
        contratto=contratto,
        datore=contratto.datore,
        lavoratore=contratto.lavoratore,
        creato_da=request.user if request.user.is_authenticated else None,
    )
    request.session['ultimo_doc_pk'] = d.pk
    _crea_busta_paga_da_ctx(ctx, contratto, mese, anno, 'CONVIVENTI_CCNL', d)

    if request.GET.get('allega_lul') == '1':
        from paghe.views._lul import _concatena_lul_a_busta
        pdf = _concatena_lul_a_busta(pdf, contratto, mese, anno)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nome_file}"'
    return response
