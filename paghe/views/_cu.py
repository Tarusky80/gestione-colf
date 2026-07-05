"""Modulo _cu - Certificazione Unica"""
from paghe.views._common_imports import *

logger = logging.getLogger(__name__)

from paghe.models import ContrattoAttivo, ContrattoLavoro, BustaPaga, DocumentoArchiviato, LogInvioEmail
from paghe.views._helpers import _get_cartella_documenti, _registra_font_pdf
from paghe.views._testi import _risolvi_variabili_testo, _componi_corpo_email


MESI_IT = ['', 'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
           'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']


def _get_cu_df_custom(contratto, anno, mode):
    """Carica data_fine_custom da CUAnnuale se mode != '1'."""
    from paghe.models import CUAnnuale
    if mode == '1':
        return None
    cu = CUAnnuale.objects.filter(contratto=contratto, anno=anno).exclude(modalita='AUTOMATICA').first()
    if cu and isinstance(cu.dettaglio_mensile, dict):
        dfc = cu.dettaglio_mensile.get('data_fine_custom', '')
        return dfc or None
    return None


def _get_cu_data(contratto, anno, data_fine_custom=None):
    buste = BustaPaga.objects.filter(contratto=contratto, anno=anno).order_by('mese')
    buste_by_mese = {b.mese: b for b in buste}

    dettaglio_mensile = []
    tot_lordo = 0.0
    tot_contrib_inps = 0.0
    tot_contrib_cassa = 0.0
    tot_contrib = 0.0
    tot_netto = 0.0
    tot_tfr = 0.0
    tot_conv = 0.0
    num_mesi = 0
    ratios = []  # ratio per mese con dati

    for mese in range(1, 13):
        busta = buste_by_mese.get(mese)
        presente = busta is not None
        if presente:
            ld = float(busta.totale_lordo)
            ci = float(busta.contributi_inps_totale)
            cc = float(busta.contributi_cassa_totale)
            ct = float(busta.totale_contributi)
            nt = float(busta.netto)
            tf = float(busta.totale_accantonati)
            cv = float(busta.convivenza_totale)
            tot_lordo += ld
            tot_contrib_inps += ci
            tot_contrib_cassa += cc
            tot_contrib += ct
            tot_netto += nt
            tot_tfr += tf
            tot_conv += cv
            num_mesi += 1
            if ld > 0:
                ratios.append({'mese': mese,
                    'inps': ci / ld, 'cassa': cc / ld, 'tfr': tf / ld})
        else:
            ld = ci = cc = ct = nt = tf = cv = 0

        dettaglio_mensile.append({
            'mese': mese, 'presente': presente,
            'lordo': ld, 'contributi_inps': ci, 'contributi_cassa': cc,
            'contributi': ct, 'netto': nt, 'tfr': tf, 'convivenza': cv,
        })

    # Ratio medi da mesi con dati
    if ratios:
        ratio_inps_medio = sum(r['inps'] for r in ratios) / len(ratios)
        ratio_cassa_medio = sum(r['cassa'] for r in ratios) / len(ratios)
        ratio_tfr_medio = sum(r['tfr'] for r in ratios) / len(ratios)
    else:
        ratio_inps_medio = 0.0
        ratio_cassa_medio = 0.0
        ratio_tfr_medio = 0.0

    imponibile = tot_lordo - tot_contrib_inps

    data_inizio = contratto.data_assunzione
    if isinstance(data_fine_custom, str) and data_fine_custom.strip():
        try:
            data_fine_custom = date.fromisoformat(data_fine_custom.strip())
        except ValueError:
            logger.warning("data_fine_custom non valida: %s", data_fine_custom)
    df_contratto = data_fine_custom or contratto.data_fine

    inizio_anno = date(anno, 1, 1)
    fine_anno = date(anno, 12, 31)
    inizio_periodo = max(data_inizio, inizio_anno)
    fine_periodo = min(df_contratto, fine_anno) if df_contratto else fine_anno
    giorni = min(max((fine_periodo - inizio_periodo).days + 1, 0), 365)

    df_out = df_contratto or contratto.data_fine

    from paghe.models import ModelloDocumentale
    _testo_cf = ModelloDocumentale.objects.filter(tipo='TESTO_PROGRAMMA', codice='CARICO FAMILIARE').first()
    _testo_pr = ModelloDocumentale.objects.filter(tipo='TESTO_PROGRAMMA', codice='PRESENTAZIONE DICHIARAZIONE DEI REDDITI').first()
    _testo_cf_default = _testo_cf.corpo_testo if _testo_cf else ''
    _testo_pr_default = _testo_pr.corpo_testo if _testo_pr else ''

    return {
        'success': True,
        'contratto_pk': contratto.pk,
        'anno': anno,
        'data_fine_contratto': contratto.data_fine.strftime('%d/%m/%Y') if contratto.data_fine else '',
        'nome_datore': contratto.datore.nome_cognome or '',
        'cf_datore': contratto.datore.codice_fiscale or '',
        'indirizzo_datore': contratto.datore.indirizzo or '',
        'comune_datore': contratto.datore.comune or '',
        'nome_lavoratore': contratto.lavoratore.nome_cognome or '',
        'cf_lavoratore': contratto.lavoratore.codice_fiscale or '',
        'indirizzo_lavoratore': contratto.lavoratore.indirizzo or '',
        'comune_lavoratore': contratto.lavoratore.comune or '',
        'codice_rapporto_inps': contratto.codice_rapporto_inps or '',
        'email_datore': contratto.datore.email or '',
        'email_lavoratore': contratto.lavoratore.email or '',
        'num_mesi': num_mesi,
        'totale_lordo': float(tot_lordo),
        'totale_contributi_inps': float(tot_contrib_inps),
        'totale_contributi_cassa': float(tot_contrib_cassa),
        'totale_contributi': float(tot_contrib),
        'totale_netto': float(tot_netto),
        'totale_tfr': float(tot_tfr),
        'totale_convivenza': float(tot_conv),
        'imponibile_fiscale': imponibile,
        'dettaglio_mensile': dettaglio_mensile,
        'data_inizio': data_inizio.strftime('%d/%m/%Y'),
        'data_fine': df_out.strftime('%d/%m/%Y') if df_out else '',
        'giorni': giorni,
        'ratio_inps': round(ratio_inps_medio, 6),
        'ratio_cassa': round(ratio_cassa_medio, 6),
        'ratio_tfr': round(ratio_tfr_medio, 6),
        'data_fine_custom': data_fine_custom or '',
        'testo_carico_familiare': _testo_cf_default,
        'testo_presentazione_redditi': _testo_pr_default,
    }


# --- redigere_cu ---
@login_required
@permesso_richiesto('buste.calcola')
@never_cache
def redigere_cu(request):
    opzioni = get_opzioni()
    contratti = ContrattoAttivo.objects.filter(stato='ATTIVO').select_related(
        'datore', 'lavoratore'
    ).prefetch_related('progetto__tipo', 'progetto__beneficiario').order_by('datore__nome_cognome')

    anno_corrente = date.today().year
    anno_min = BustaPaga.objects.aggregate(m=Min('anno'))['m']
    anno_iniziale = anno_min if anno_min else anno_corrente - 5

    return render(request, 'paghe/redigere_cu.html', {
        'opzioni': opzioni,
        'contratti': contratti,
        'anno_corrente': anno_corrente,
        'anno_iniziale': anno_iniziale,
    })


# --- ajax_carica_dati_cu ---
@login_required
@permesso_richiesto('buste.calcola')
def ajax_carica_dati_cu(request):
    contratto_pk = request.GET.get('contratto_pk')
    anno_raw = request.GET.get('anno', '').strip()
    mode = request.GET.get('mode', '1')  # 1=Auto, 2=SemiAuto, 3=Manuale

    if not contratto_pk:
        return JsonResponse({'success': False, 'error': 'Contratto non specificato.'})
    try:
        anno = int(anno_raw) if anno_raw else date.today().year
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Anno non valido.'})

    contratto = get_object_or_404(ContrattoAttivo.objects.select_related(
        'datore', 'lavoratore'), pk=contratto_pk)

    try:
        from paghe.models import CUAnnuale
        dfc_mode = None
        if mode == '2':
            cu = CUAnnuale.objects.filter(contratto=contratto, anno=anno, modalita='SEMI_AUTOMATICA').first()
            if cu and isinstance(cu.dettaglio_mensile, dict):
                dfc_mode = cu.dettaglio_mensile.get('data_fine_custom') or None
        elif mode == '3':
            cu = CUAnnuale.objects.filter(contratto=contratto, anno=anno, modalita='MANUALE').first()
            if cu and isinstance(cu.dettaglio_mensile, dict):
                dfc_mode = cu.dettaglio_mensile.get('data_fine_custom') or None

        dati = _get_cu_data(contratto, anno, data_fine_custom=dfc_mode)
        def _load_testi_cu(dm_dict):
            if dm_dict.get('testo_carico_familiare'):
                dati['testo_carico_familiare'] = dm_dict['testo_carico_familiare']
            if dm_dict.get('testo_presentazione_redditi'):
                dati['testo_presentazione_redditi'] = dm_dict['testo_presentazione_redditi']

        if mode == '2':
            cu = CUAnnuale.objects.filter(contratto=contratto, anno=anno, modalita='SEMI_AUTOMATICA').first()
            if cu:
                dati['totale_lordo'] = float(cu.reddito_lordo)
                dati['totale_contributi_inps'] = float(cu.contributi_inps_lav)
                dati['totale_contributi_cassa'] = float(cu.contributi_cassa)
                dati['totale_contributi'] = float(cu.contributi_totali)
                dati['totale_netto'] = float(cu.netto_corrisposto)
                dati['totale_tfr'] = float(cu.tfr_accantonato)
                dati['totale_convivenza'] = float(cu.indennita_convivenza)
                dati['imponibile_fiscale'] = float(cu.imponibile_fiscale)
                if isinstance(cu.dettaglio_mensile, dict):
                    dm = cu.dettaglio_mensile
                    if 'mesi' in dm:
                        dati['dettaglio_mensile'] = dm['mesi']
                    _load_testi_cu(dm)
                elif isinstance(cu.dettaglio_mensile, list):
                    dati['dettaglio_mensile'] = cu.dettaglio_mensile
                dati['num_mesi'] = sum(1 for m in (dati['dettaglio_mensile'] if isinstance(dati['dettaglio_mensile'], list) else []) if m.get('presente', False))
            dati['mode'] = 'semiauto'
        elif mode == '3':
            cu = CUAnnuale.objects.filter(contratto=contratto, anno=anno, modalita='MANUALE').first()
            if cu:
                dati['totale_lordo'] = float(cu.reddito_lordo)
                dati['totale_contributi_inps'] = float(cu.contributi_inps_lav)
                dati['totale_contributi_cassa'] = float(cu.contributi_cassa)
                dati['totale_contributi'] = float(cu.contributi_totali)
                dati['totale_netto'] = float(cu.netto_corrisposto)
                dati['totale_tfr'] = float(cu.tfr_accantonato)
                dati['totale_convivenza'] = float(cu.indennita_convivenza)
                dati['imponibile_fiscale'] = float(cu.imponibile_fiscale)
                if isinstance(cu.dettaglio_mensile, dict):
                    _load_testi_cu(cu.dettaglio_mensile)
            dati['mode'] = 'manuale'
        else:
            dati['mode'] = 'auto'
        return JsonResponse(dati)
    except Exception as e:
        logger.exception("Errore in _load_testi_cu")
        return JsonResponse({'success': False, 'error': str(e)})


def _build_cu_pdf_bytes(dati, anno):
    """Build full CU PDF, returns (pdf_bytes, nome_file)."""
    import io
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    _registra_font_pdf()
    grigio_scuro = HexColor('#222222')
    grigio_medio = HexColor('#555555')
    grigio_bordo = HexColor('#cccccc')
    acciaio = HexColor('#2c5282')
    acciaio_chiaro = HexColor('#dce6f0')

    s_titolo = ParagraphStyle('titolo', fontSize=16, leading=20, textColor=grigio_scuro,
                              fontName='Roboto-Bold', alignment=TA_CENTER, spaceAfter=2)
    s_sottotitolo = ParagraphStyle('sotto', fontSize=9, leading=12, textColor=grigio_medio,
                                   fontName='Roboto', alignment=TA_CENTER, spaceAfter=0)
    s_corpo = ParagraphStyle('corpo', fontSize=9, leading=13, textColor=grigio_scuro,
                             fontName='Roboto', spaceAfter=4)
    s_corpo_bold = ParagraphStyle('corpob', fontSize=9, leading=13, textColor=grigio_scuro,
                                  fontName='Roboto-Bold', spaceAfter=4)
    s_sezione = ParagraphStyle('sez', fontSize=10, leading=13, textColor=acciaio,
                               fontName='Roboto-Bold', spaceBefore=10, spaceAfter=4,
                               borderPadding=(0, 0, 2, 0))
    s_label = ParagraphStyle('label', fontSize=8, leading=10, textColor=grigio_medio,
                             fontName='Roboto', spaceAfter=0)
    s_val = ParagraphStyle('val', fontSize=9, leading=12, textColor=grigio_scuro,
                           fontName='Roboto-Bold', spaceAfter=0)
    s_firma = ParagraphStyle('firma', fontSize=9, leading=13, textColor=grigio_scuro,
                             fontName='Roboto', spaceAfter=20)
    s_piccolo = ParagraphStyle('picc', fontSize=7, leading=9, textColor=grigio_medio,
                               fontName='Roboto', spaceAfter=1)

    def _fmt_eur(v):
        return "\u20ac %s" % ("{:,.2f}".format(v).replace(',', 'X').replace('.', ',').replace('X', '.'))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            topMargin=12*mm, bottomMargin=10*mm,
                            leftMargin=18*mm, rightMargin=18*mm)
    story = []

    # Intestazione
    story.append(Paragraph('DICHIARAZIONE SOSTITUTIVA', s_titolo))
    story.append(Paragraph('DELLA CERTIFICAZIONE UNICA (EX CUD)', s_titolo))
    story.append(Spacer(1, 2))
    story.append(Paragraph(f'Lavoro Domestico \u2014 Anno {anno}', s_sottotitolo))
    story.append(HRFlowable(width='100%', thickness=1.5, color=acciaio, spaceAfter=8))

    # Testo introduttivo
    story.append(Paragraph(
        'Il datore di lavoro domestico non \u00e8 sostituto d\u2019imposta '
        'ai sensi dell\u2019art. 23 del D.P.R. 29 settembre 1973, n. 600. '
        'La presente dichiarazione, resa ai sensi del D.P.R. 28 dicembre 2000, n. 445, '
        'sostituisce a tutti gli effetti la Certificazione Unica (ex CUD) '
        'per i redditi di lavoro domestico relativi all\u2019anno indicato.',
        s_corpo))
    story.append(Spacer(1, 6))

    # 1. Dati Datore
    story.append(Paragraph('1. DATI DEL DATORE DI LAVORO', s_sezione))
    datore_data = [
        [Paragraph('Nome e Cognome / Ragione Sociale', s_label),
         Paragraph(dati['nome_datore'], s_val)],
        [Paragraph('Codice Fiscale', s_label),
         Paragraph(dati['cf_datore'], s_val)],
        [Paragraph('Indirizzo', s_label),
         Paragraph((dati.get('indirizzo_datore', '') + ', ' + dati.get('comune_datore', '')).strip(', ') or '\u2014', s_val)],
    ]
    datore_tbl = Table(datore_data, colWidths=[doc.width*0.32, doc.width*0.68])
    datore_tbl.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LINEBELOW', (0, 0), (-1, -1), 0.3, grigio_bordo),
    ]))
    story.append(datore_tbl)

    # 2. Dati Lavoratore
    story.append(Paragraph('2. DATI DEL LAVORATORE', s_sezione))
    lav_data = [
        [Paragraph('Nome e Cognome', s_label),
         Paragraph(dati['nome_lavoratore'], s_val)],
        [Paragraph('Codice Fiscale', s_label),
         Paragraph(dati['cf_lavoratore'], s_val)],
        [Paragraph('Indirizzo', s_label),
         Paragraph((dati.get('indirizzo_lavoratore', '') + ', ' + dati.get('comune_lavoratore', '')).strip(', ') or '\u2014', s_val)],
    ]
    lav_tbl = Table(lav_data, colWidths=[doc.width*0.32, doc.width*0.68])
    lav_tbl.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LINEBELOW', (0, 0), (-1, -1), 0.3, grigio_bordo),
    ]))
    story.append(lav_tbl)

    # 3. Periodo
    story.append(Paragraph('3. PERIODO DI LAVORO', s_sezione))
    periodo_label = f"Dal {dati['data_inizio']}"
    if dati['data_fine']:
        periodo_label += f" al {dati['data_fine']}"
    else:
        periodo_label += ' (in corso)'
    periodo_data = [
        [Paragraph('Periodo', s_label), Paragraph(periodo_label, s_val),
         Paragraph('Giorni', s_label), Paragraph(str(dati['giorni']), s_val)],
    ]
    periodo_tbl = Table(periodo_data, colWidths=[doc.width*0.15, doc.width*0.40, doc.width*0.10, doc.width*0.10])
    periodo_tbl.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('BACKGROUND', (0, 0), (-1, -1), acciaio_chiaro),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, grigio_bordo),
    ]))
    story.append(periodo_tbl)

    # 4. Compensi anno XXXX
    story.append(Paragraph(f'4. COMPENSI ANNO {anno}', s_sezione))

    comp_rows = [
        [Paragraph('Retribuzione lorda (comprensiva di 13\u00aa)', s_corpo),
         Paragraph(_fmt_eur(dati['totale_lordo']), s_corpo_bold)],
        [Paragraph('Contributi INPS a carico lavoratore', s_corpo),
         Paragraph(_fmt_eur(dati['totale_contributi_inps']), s_corpo_bold)],
        [Paragraph('Contributi Cassa Colf a carico lavoratore', s_corpo),
         Paragraph(_fmt_eur(dati['totale_contributi_cassa']), s_corpo_bold)],
        ['', ''],
        [Paragraph('<b>Imponibile fiscale</b>', s_corpo),
         Paragraph(f'<b>{_fmt_eur(dati["imponibile_fiscale"])}</b>', s_corpo_bold)],
        [Paragraph('TFR corrisposto nell\'anno', s_corpo),
         Paragraph(_fmt_eur(dati['totale_tfr']), s_corpo_bold)],
    ]
    if dati['totale_convivenza'] > 0:
        comp_rows.append(
            [Paragraph("Indennit\u00e0 di convivenza", s_corpo),
             Paragraph(_fmt_eur(dati['totale_convivenza']), s_corpo_bold)]
        )

    comp_tbl = Table(comp_rows, colWidths=[doc.width*0.55, doc.width*0.25])
    comp_tbl.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 1.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
        ('LINEBELOW', (0, 0), (-1, 0), 0.3, grigio_bordo),
        ('LINEBELOW', (0, 1), (-1, 1), 0.3, grigio_bordo),
        ('LINEBELOW', (0, 2), (-1, 2), 0.3, grigio_bordo),
        ('LINEABOVE', (0, 4), (1, 4), 1.5, acciaio),
        ('LINEBELOW', (0, 4), (-1, 4), 0.3, grigio_bordo),
        ('LINEBELOW', (0, 5), (-1, 5), 0.3, grigio_bordo),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('RIGHTPADDING', (1, 0), (1, -1), 0),
    ]))
    story.append(comp_tbl)
    story.append(Spacer(1, 8))

    # Risolvi variabili nei testi Carico Familiare e Presentazione Redditi
    _testo_cf = dati.get('testo_carico_familiare', '')
    _testo_pr = dati.get('testo_presentazione_redditi', '')
    if _testo_cf or _testo_pr:
        try:
            _ct = ContrattoAttivo.objects.select_related('datore', 'lavoratore').get(pk=dati['contratto_pk'])
            if _testo_cf:
                _testo_cf = _risolvi_variabili_testo(_testo_cf, _ct)
            if _testo_pr:
                _testo_pr = _risolvi_variabili_testo(_testo_pr, _ct)
        except Exception:
            logger.warning("Impossibile risolvere variabili testo CU per contratto pk=%s", dati.get('contratto_pk'))

    # 5. Carico familiare
    if _testo_cf:
        story.append(Paragraph('5. CARICO FAMILIARE', s_sezione))
        story.append(Paragraph(_testo_cf, s_corpo))
        story.append(Spacer(1, 8))

    # 6. Presentazione dichiarazione dei redditi
    if _testo_pr:
        story.append(Paragraph('6. PRESENTAZIONE DICHIARAZIONE DEI REDDITI', s_sezione))
        story.append(Paragraph(_testo_pr, s_corpo))
        story.append(Spacer(1, 8))

    # 7. Dichiarazione
    story.append(Paragraph('7. DICHIARAZIONE SOSTITUTIVA', s_sezione))
    story.append(Paragraph(
        'Il/La sottoscritto/a <b>%s</b>, codice fiscale <b>%s</b>, '
        'nella qualit\u00e0 di datore di lavoro domestico, '
        'consapevole della responsabilit\u00e0 penale prevista '
        'dall\u2019art. 76 del D.P.R. 445/2000 per le dichiarazioni mendaci, '
        'DICHIARA che gli importi sopra indicati rappresentano le somme '
        'effettivamente corrisposte al lavoratore domestico nell\u2019anno %d '
        'e che gli stessi corrispondono a quanto riportato nella documentazione '
        'contabile e retributiva conservata presso il domicilio del dichiarante.' %
        (dati['nome_datore'], dati['cf_datore'], anno),
        s_corpo))
    story.append(Spacer(1, 12))

    # Luogo e data
    luogo = dati.get('comune_datore', '') or '________________'
    story.append(Paragraph(
        f'Luogo e data: {luogo}, l\u00ec {date.today().strftime("%d/%m/%Y")}', s_firma))
    story.append(Spacer(1, 20))

    # Linee firma
    firma_data = [
        [Paragraph('Firma del datore di lavoro', ParagraphStyle('f1', fontSize=9, leading=12,
            textColor=grigio_scuro, fontName='Roboto', alignment=TA_LEFT)),
         Paragraph('Firma del lavoratore (per ricevuta)', ParagraphStyle('f2', fontSize=9, leading=12,
            textColor=grigio_scuro, fontName='Roboto', alignment=TA_LEFT))],
        [Paragraph('____________________________', ParagraphStyle('fl1', fontSize=10, leading=14,
            textColor=grigio_scuro, fontName='Roboto', alignment=TA_LEFT)),
         Paragraph('____________________________', ParagraphStyle('fl2', fontSize=10, leading=14,
            textColor=grigio_scuro, fontName='Roboto', alignment=TA_LEFT))],
    ]
    firma_tbl = Table(firma_data, colWidths=[doc.width*0.45, doc.width*0.45])
    firma_tbl.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(firma_tbl)

    # Footer
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width='100%', thickness=0.3, color=grigio_bordo, spaceAfter=3))
    story.append(Paragraph(
        f'Documento generato automaticamente il {date.today().strftime("%d/%m/%Y")} '
        '\u2014 Dichiarazione sostitutiva ai sensi del D.P.R. 445/2000.',
        s_piccolo))

    doc.build(story)
    pdf_data = buffer.getvalue()
    buffer.close()
    nome_file = f'CU_{dati["nome_lavoratore"].replace(" ", "_").upper()}_{dati["nome_datore"].replace(" ", "_").upper()}_{anno}.pdf'
    return pdf_data, nome_file


# --- ajax_genera_cu_pdf ---
@xframe_options_exempt
@login_required
@permesso_richiesto('buste.calcola')
@never_cache
def ajax_genera_cu_pdf(request):

    contratto_pk = request.GET.get('contratto_pk')
    anno_raw = request.GET.get('anno', '').strip()
    salva = request.GET.get('salva') == '1'

    if not contratto_pk:
        return HttpResponse('Contratto non specificato.', status=400)
    try:
        anno = int(anno_raw) if anno_raw else date.today().year
    except ValueError:
        return HttpResponse('Anno non valido.', status=400)

    contratto = get_object_or_404(ContrattoAttivo.objects.select_related(
        'datore', 'lavoratore', 'parametri_minimi', 'ente_bilaterale'), pk=contratto_pk)
    if not BustaPaga.objects.filter(contratto=contratto, anno=anno).exists():
        return HttpResponse('Nessuna busta paga trovata per questo contratto nell\'anno selezionato. Generare prima le buste paga.', status=400)
    mode = request.GET.get('mode', '1')
    dfc = _get_cu_df_custom(contratto, anno, mode)

    try:
        dati = _get_cu_data(contratto, anno, data_fine_custom=dfc)
    except Exception as e:
        logger.exception("Errore in ajax_genera_cu_pdf")
        return HttpResponse(f'Errore caricamento dati CU: {e}', status=500)

    # Sovrascrivi testi se passati come GET (modifiche non salvate dal textarea)
    tc = request.GET.get('testo_carico_familiare')
    tp = request.GET.get('testo_presentazione_redditi')
    if tc is not None:
        dati['testo_carico_familiare'] = tc
    if tp is not None:
        dati['testo_presentazione_redditi'] = tp

    try:
        pdf_data, nome_file = _build_cu_pdf_bytes(dati, anno)
    except Exception as e:
        logger.exception("Errore in ajax_genera_cu_pdf")
        return HttpResponse(f'Errore generazione PDF: {e}', status=500)

    if salva:
        try:
            cartella = _get_cartella_documenti(contratto)
            os.makedirs(cartella, exist_ok=True)
            full_path = os.path.join(cartella, nome_file)
            with open(full_path, 'wb') as f:
                f.write(pdf_data)
            DocumentoArchiviato.objects.create(
                tipo='CU_ANNUALE',
                titolo=f"Certificazione Unica {dati['nome_lavoratore']} \u2013 {anno}",
                file_path=full_path, file_size=len(pdf_data), file_name=nome_file,
                contratto=contratto, datore=contratto.datore, lavoratore=contratto.lavoratore,
                creato_da=request.user if request.user.is_authenticated else None,
            )
        except Exception as e:
            logger.exception("Errore in ajax_genera_cu_pdf")
            return HttpResponse(f'Errore salvataggio PDF: {e}', status=500)

    response = HttpResponse(pdf_data, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{nome_file}"'
    return response



def _crea_log_cu(contratto, destinatari, esito, msg='', request=None):
    LogInvioEmail.objects.create(
        contratto=contratto, tipo_documento='CU_ANNUALE',
        destinatario=destinatari, esito=esito,
        messaggio_errore=msg,
        utente=request.user if request and request.user.is_authenticated else None,
    )


def _invia_email_cu(doc_arch, destinatari, modello, contratto, opzioni, cu_extra_vars, request):
    """Invia email CU via Thunderbird o SMTP. Crea LogInvioEmail.
    Restituisce {'inviato': bool, 'errore': str|None}."""
    if not destinatari:
        _crea_log_cu(contratto, destinatari, 'ERRORE', 'Nessuna email disponibile.', request)
        return {'inviato': False, 'errore': 'Nessuna email disponibile.'}

    corpo, oggetto = _componi_corpo_email(modello, contratto, opzioni, extra_vars=cu_extra_vars)

    if opzioni and opzioni.email_usa_programma_posta and opzioni.exe_posta:
        try:
            import subprocess
            params = f"to='{destinatari}',subject='{oggetto}',body='{corpo}',attachment='{doc_arch.file_path}'"
            subprocess.Popen([opzioni.exe_posta, '-compose', params])
            doc_arch.inviato = True
            doc_arch.inviato_il = date.today()
            doc_arch.email_destinatario = destinatari
            doc_arch.save()
            _crea_log_cu(contratto, destinatari, 'OK', request=request)
            return {'inviato': True, 'errore': None}
        except Exception as ex:
            logger.exception("Errore invio CU via Thunderbird")
            _crea_log_cu(contratto, destinatari, 'ERRORE', str(ex), request)
            return {'inviato': False, 'errore': f'Errore Thunderbird: {ex}'}

    if opzioni and opzioni.email_smtp_server:
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.base import MIMEBase
            from email import encoders
            msg = MIMEMultipart()
            msg['From'] = opzioni.email_mittente
            msg['To'] = destinatari.replace(';', ',')
            msg['Subject'] = oggetto
            msg.attach(MIMEText(corpo, 'html', 'utf-8'))
            with open(doc_arch.file_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{doc_arch.file_name}"')
                msg.attach(part)
            smtp = smtplib.SMTP(opzioni.email_smtp_server, opzioni.email_smtp_port, timeout=10)
            if opzioni.email_usa_tls:
                smtp.starttls()
            if opzioni.email_smtp_username and opzioni.get_smtp_password():
                smtp.login(opzioni.email_smtp_username, opzioni.get_smtp_password())
            smtp.send_message(msg)
            smtp.quit()
            doc_arch.inviato = True
            doc_arch.inviato_il = date.today()
            doc_arch.email_destinatario = destinatari
            doc_arch.save()
            _crea_log_cu(contratto, destinatari, 'OK', request=request)
            return {'inviato': True, 'errore': None}
        except Exception as ex:
            logger.exception("Errore invio CU via SMTP")
            _crea_log_cu(contratto, destinatari, 'ERRORE', str(ex), request)
            return {'inviato': False, 'errore': f'Errore SMTP: {ex}'}

    _crea_log_cu(contratto, destinatari, 'ERRORE', 'Programma di posta o SMTP non configurato.', request)
    return {'inviato': False, 'errore': 'Configura posta o SMTP nelle opzioni.'}


# --- ajax_invia_cu_email ---
@login_required
@permesso_richiesto('buste.invia')
@require_http_methods(['POST'])
def ajax_invia_cu_email(request):
    from django.template.loader import render_to_string

    data = json.loads(request.body)
    contratto_pk = data.get('contratto_pk')
    anno_raw = data.get('anno', '')

    if not contratto_pk:
        return HttpResponse(render_to_string('paghe/_modale_invio_email_esito.html', {
            'success': False, 'error': 'Contratto non specificato.'
        }))

    try:
        anno = int(anno_raw) if anno_raw else date.today().year
    except ValueError:
        return HttpResponse(render_to_string('paghe/_modale_invio_email_esito.html', {
            'success': False, 'error': 'Anno non valido.'
        }))

    contratto = get_object_or_404(ContrattoAttivo.objects.select_related(
        'datore', 'lavoratore'), pk=contratto_pk)

    modello_pk = data.get('modello_pk')

    # Genera PDF
    mode = data.get('mode', '1')
    dfc = _get_cu_df_custom(contratto, anno, mode)
    dati = _get_cu_data(contratto, anno, data_fine_custom=dfc)

    # Sovrascrivi testi se passati (modifiche non salvate dal textarea)
    tc = data.get('testo_carico_familiare')
    tp = data.get('testo_presentazione_redditi')
    if tc is not None:
        dati['testo_carico_familiare'] = tc
    if tp is not None:
        dati['testo_presentazione_redditi'] = tp

    # Prepara extra_vars per il modello email (tutte le chiavi dati in UPPERCASE)
    cu_extra_vars = {}
    for k, v in dati.items():
        if isinstance(v, float):
            cu_extra_vars[k.upper()] = f'\u20ac {v:,.2f}'
        elif isinstance(v, (int, str)):
            cu_extra_vars[k.upper()] = str(v)
    pdf_data, nome_file = _build_cu_pdf_bytes(dati, anno)

    # Salva PDF
    cartella = _get_cartella_documenti(contratto)
    os.makedirs(cartella, exist_ok=True)
    full_path = os.path.join(cartella, nome_file)
    with open(full_path, 'wb') as f:
        f.write(pdf_data)

    doc_arch = DocumentoArchiviato.objects.create(
        tipo='CU_ANNUALE',
        titolo=f"Certificazione Unica {dati['nome_lavoratore']} – {anno}",
        file_path=full_path, file_size=len(pdf_data), file_name=nome_file,
        contratto=contratto, datore=contratto.datore, lavoratore=contratto.lavoratore,
        creato_da=request.user if request.user.is_authenticated else None,
    )

    # Cerca modello email CU
    from paghe.models import ModelloDocumentale
    modello = None
    if modello_pk:
        modello = ModelloDocumentale.objects.filter(pk=modello_pk, tipo='MAIL').first()
    if not modello:
        modello = ModelloDocumentale.objects.filter(tipo='MAIL', codice__icontains='CUD').first()
    if not modello:
        modello = ModelloDocumentale.objects.filter(tipo='MAIL', codice__icontains='CU').first()
    if not modello:
        modello = ModelloDocumentale.objects.filter(tipo='MAIL').first()

    opzioni = get_opzioni()
    destinatari = data.get('destinatari', '').strip()
    if not destinatari:
        destinatari = ';'.join(filter(None, [
            contratto.lavoratore.email or '',
            contratto.datore.email or '',
        ]))

    def _log_invio(esito, msg_errore=''):
        LogInvioEmail.objects.create(
            contratto=contratto,
            tipo_documento='CU_ANNUALE',
            destinatario=destinatari,
            esito=esito,
            messaggio_errore=msg_errore,
            utente=request.user if request.user.is_authenticated else None,
        )

    risultato = _invia_email_cu(doc_arch, destinatari, modello, contratto, opzioni, cu_extra_vars, request)
    inviato = risultato['inviato']
    errore = risultato['errore']

    from django.template.loader import render_to_string
    html = render_to_string('paghe/_modale_invio_email_esito.html', {
        'success': inviato or not errore,
        'inviato': inviato,
        'errore': errore,
        'destinatari': destinatari,
        'mailto_link': f"mailto:{destinatari}?subject=Certificazione Unica {anno}&body=Allega il PDF dalla cartella documenti." if not inviato and destinatari else '',
        'nome_file': nome_file,
        'full_path': full_path,
    })
    return HttpResponse(html)


# --- ajax_salva_cu_annuale ---
@login_required
@permesso_richiesto('buste.calcola')
@require_http_methods(['POST'])
def ajax_salva_cu_annuale(request):
    """Salva i dati CU per modalità Semi-Automatica e Manuale."""
    import json
    from paghe.models import CUAnnuale
    data = json.loads(request.body)
    contratto_pk = data.get('contratto_pk')
    anno = data.get('anno')
    modalita = data.get('modalita')  # 'SEMI_AUTOMATICA' o 'MANUALE'
    valori = data.get('valori', {})

    if not contratto_pk or not anno:
        return JsonResponse({'success': False, 'error': 'Parametri mancanti.'})

    contratto = get_object_or_404(ContrattoLavoro, pk=contratto_pk)

    try:
        dm = {}
        if modalita == 'SEMI_AUTOMATICA' and 'dettaglio_mensile' in valori:
            dm['mesi'] = valori['dettaglio_mensile']
        data_fine_custom = valori.get('data_fine_custom', '')
        if data_fine_custom:
            dm['data_fine_custom'] = data_fine_custom
        for k in ('testo_carico_familiare', 'testo_presentazione_redditi'):
            v = valori.get(k)
            if v:
                dm[k] = v

        # Pre-save quadratura check
        buste = _get_cu_data(contratto, anno, data_fine_custom=data_fine_custom or None)
        salvati = {
            'lordo': float(valori.get('totale_lordo', 0)),
            'contributi_inps': float(valori.get('totale_contributi_inps', 0)),
            'contributi_cassa': float(valori.get('totale_contributi_cassa', 0)),
            'contributi': float(valori.get('totale_contributi', 0)),
            'netto': float(valori.get('totale_netto', 0)),
            'tfr': float(valori.get('totale_tfr', 0)),
            'imponibile': float(valori.get('imponibile_fiscale', 0)),
        }
        buste_vals = {
            'lordo': buste['totale_lordo'],
            'contributi_inps': buste['totale_contributi_inps'],
            'contributi_cassa': buste['totale_contributi_cassa'],
            'contributi': buste['totale_contributi'],
            'netto': buste['totale_netto'],
            'tfr': buste['totale_tfr'],
            'imponibile': buste['imponibile_fiscale'],
        }
        max_scostamento = 0
        scostamenti = []
        for k in salvati:
            bv = buste_vals[k] or 0.001
            diff = abs(salvati[k] - bv)
            perc = diff / abs(bv) * 100
            if perc > max_scostamento:
                max_scostamento = perc
            if perc > 1:
                scostamenti.append(k)

        cu, created = CUAnnuale.objects.update_or_create(
            contratto=contratto,
            anno=anno,
            modalita=modalita,
            defaults={
                'reddito_lordo': salvati['lordo'],
                'contributi_inps_lav': salvati['contributi_inps'],
                'contributi_cassa': salvati['contributi_cassa'],
                'contributi_totali': salvati['contributi'],
                'netto_corrisposto': salvati['netto'],
                'tfr_accantonato': salvati['tfr'],
                'indennita_convivenza': float(valori.get('totale_convivenza', 0)),
                'imponibile_fiscale': salvati['imponibile'],
                'dettaglio_mensile': dm or {},
                'creato_da': request.user if request.user.is_authenticated else None,
            }
        )
        result = {'success': True, 'created': created, 'pk': cu.pk}
        if scostamenti:
            result['warning'] = True
            result['warning_msg'] = (f'Salvato con scostamenti ({max_scostamento:.1f}%) '
                                     f'rispetto alle buste paga: {", ".join(scostamenti)}.')
        return JsonResponse(result)
    except Exception as e:
        logger.exception("Errore in ajax_salva_cu_annuale")
        return JsonResponse({'success': False, 'error': str(e)})


# --- ajax_log_invii_cu ---
@login_required
@permesso_richiesto('buste.calcola')
def ajax_log_invii_cu(request, contratto_pk, anno):
    contratto = get_object_or_404(ContrattoLavoro, pk=contratto_pk)
    logs = LogInvioEmail.objects.filter(contratto=contratto, tipo_documento='CU_ANNUALE')
    if anno:
        logs = logs.filter(data_ora__year=anno)
    logs = logs.order_by('-data_ora')[:50]
    items = [{
        'pk': l.pk,
        'data_ora': l.data_ora.strftime('%d/%m/%Y %H:%M'),
        'destinatario': l.destinatario,
        'esito': l.get_esito_display(),
        'errore': l.messaggio_errore,
    } for l in logs]
    return JsonResponse({'success': True, 'items': items})


# --- ajax_genera_cu_pdf_batch ---
@login_required
@permesso_richiesto('buste.calcola')
@require_http_methods(['POST'])
def ajax_genera_cu_pdf_batch(request):
    import json as json_lib
    data = json_lib.loads(request.body)
    contratti_pk = data.get('contratti', [])
    anno_raw = data.get('anno', '')
    mode = data.get('mode', '1')
    testo_cf = data.get('testo_carico_familiare')
    testo_pr = data.get('testo_presentazione_redditi')
    try:
        anno = int(anno_raw) if anno_raw else date.today().year
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Anno non valido.'})

    contratti_map = {c.pk: c for c in ContrattoAttivo.objects.filter(pk__in=contratti_pk).select_related(
        'datore', 'lavoratore', 'parametri_minimi', 'ente_bilaterale')}
    esiti = []
    for pk in contratti_pk:
        try:
            contratto = contratti_map.get(pk)
            if not contratto:
                continue
            if not BustaPaga.objects.filter(contratto=contratto, anno=anno).exists():
                esiti.append({'pk': pk, 'ok': False, 'errore': 'Nessuna busta paga per questo contratto nell\'anno selezionato.'})
                continue
            dfc = _get_cu_df_custom(contratto, anno, mode)
            dati = _get_cu_data(contratto, anno, data_fine_custom=dfc)
            if testo_cf is not None:
                dati['testo_carico_familiare'] = testo_cf
            if testo_pr is not None:
                dati['testo_presentazione_redditi'] = testo_pr
            pdf_data, nome_file = _build_cu_pdf_bytes(dati, anno)
            cartella = _get_cartella_documenti(contratto)
            os.makedirs(cartella, exist_ok=True)
            full_path = os.path.join(cartella, nome_file)
            with open(full_path, 'wb') as f:
                f.write(pdf_data)
            doc_arch = DocumentoArchiviato.objects.create(
                tipo='CU_ANNUALE',
                titolo=f"Certificazione Unica {dati['nome_lavoratore']} \u2013 {anno}",
                file_path=full_path, file_size=len(pdf_data), file_name=nome_file,
                contratto=contratto, datore=contratto.datore, lavoratore=contratto.lavoratore,
                creato_da=request.user if request.user.is_authenticated else None,
            )
            esiti.append({'pk': pk, 'ok': True, 'nome_file': nome_file, 'doc_pk': doc_arch.pk,
                          'lavoratore': dati['nome_lavoratore'], 'datore': dati['nome_datore']})
        except Exception as e:
            logger.exception("Errore in ajax_genera_cu_pdf_batch")
            esiti.append({'pk': pk, 'ok': False, 'errore': str(e)})

    ok_count = sum(1 for e in esiti if e['ok'])
    return JsonResponse({'success': True, 'esiti': esiti, 'ok': ok_count, 'totale': len(esiti)})


# --- ajax_invia_cu_massivo ---
@login_required
@permesso_richiesto('buste.invia')
@require_http_methods(['POST'])
def ajax_invia_cu_massivo(request):
    import json as json_lib

    data = json_lib.loads(request.body)
    contratti_pk = data.get('contratti', [])
    anno_raw = data.get('anno', '')
    modello_pk = data.get('modello_pk')
    mode = data.get('mode', '1')
    testo_cf = data.get('testo_carico_familiare')
    testo_pr = data.get('testo_presentazione_redditi')

    try:
        anno = int(anno_raw) if anno_raw else date.today().year
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Anno non valido.'})

    opzioni = get_opzioni()
    from paghe.models import ModelloDocumentale
    modello = None
    if modello_pk:
        modello = ModelloDocumentale.objects.filter(pk=modello_pk, tipo='MAIL').first()
    if not modello:
        modello = ModelloDocumentale.objects.filter(tipo='MAIL', codice__icontains='CUD').first()
    if not modello:
        modello = ModelloDocumentale.objects.filter(tipo='MAIL', codice__icontains='CU').first()
    if not modello:
        modello = ModelloDocumentale.objects.filter(tipo='MAIL').first()

    contratti_map = {c.pk: c for c in ContrattoAttivo.objects.filter(pk__in=contratti_pk).select_related('datore', 'lavoratore')}
    riepilogo = {'ok': 0, 'errore': 0, 'dettagli': []}

    for pk in contratti_pk:
        try:
            contratto = contratti_map.get(pk)
            if not contratto:
                continue
            dfc = _get_cu_df_custom(contratto, anno, mode)
            dati = _get_cu_data(contratto, anno, data_fine_custom=dfc)
            if testo_cf is not None:
                dati['testo_carico_familiare'] = testo_cf
            if testo_pr is not None:
                dati['testo_presentazione_redditi'] = testo_pr
            cu_extra_vars = {}
            for k, v in dati.items():
                if isinstance(v, float):
                    cu_extra_vars[k.upper()] = f'\u20ac {v:,.2f}'
                elif isinstance(v, (int, str)):
                    cu_extra_vars[k.upper()] = str(v)
            pdf_data, nome_file = _build_cu_pdf_bytes(dati, anno)
            cartella = _get_cartella_documenti(contratto)
            os.makedirs(cartella, exist_ok=True)
            full_path = os.path.join(cartella, nome_file)
            with open(full_path, 'wb') as f:
                f.write(pdf_data)
            doc_arch = DocumentoArchiviato.objects.create(
                tipo='CU_ANNUALE',
                titolo=f"Certificazione Unica {dati['nome_lavoratore']} \u2013 {anno}",
                file_path=full_path, file_size=len(pdf_data), file_name=nome_file,
                contratto=contratto, datore=contratto.datore, lavoratore=contratto.lavoratore,
                creato_da=request.user if request.user.is_authenticated else None,
            )
            destinatari = ';'.join(filter(None, [
                contratto.lavoratore.email or '',
                contratto.datore.email or '',
            ]))

            risultato = _invia_email_cu(doc_arch, destinatari, modello, contratto, opzioni, cu_extra_vars, request)
            inviato = risultato['inviato']
            errore = risultato['errore']

            if inviato:
                riepilogo['ok'] += 1
                riepilogo['dettagli'].append({'pk': pk, 'ok': True, 'lavoratore': dati['nome_lavoratore']})
            else:
                riepilogo['errore'] += 1
                riepilogo['dettagli'].append({'pk': pk, 'ok': False, 'lavoratore': dati['nome_lavoratore'], 'errore': errore})
        except Exception as e:
            logger.exception("Errore in _log")
            riepilogo['errore'] += 1
            riepilogo['dettagli'].append({'pk': pk, 'ok': False, 'errore': str(e)})

    return JsonResponse({'success': True, 'riepilogo': riepilogo})


# --- ajax_verifica_cu ---
@login_required
@permesso_richiesto('buste.calcola')
def ajax_verifica_cu(request):
    """Confronta i dati buste paga con i valori CU correnti."""
    contratto_pk = request.GET.get('contratto_pk')
    anno_raw = request.GET.get('anno', '').strip()
    if not contratto_pk:
        return JsonResponse({'success': False, 'error': 'Contratto non specificato.'})
    try:
        anno = int(anno_raw) if anno_raw else date.today().year
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Anno non valido.'})
    contratto = get_object_or_404(ContrattoLavoro, pk=contratto_pk)
    buste = _get_cu_data(contratto, anno)
    return JsonResponse({
        'success': True,
        'buste_lordo': buste['totale_lordo'],
        'buste_contributi_inps': buste['totale_contributi_inps'],
        'buste_contributi_cassa': buste['totale_contributi_cassa'],
        'buste_contributi': buste['totale_contributi'],
        'buste_netto': buste['totale_netto'],
        'buste_tfr': buste['totale_tfr'],
        'buste_convivenza': buste['totale_convivenza'],
        'buste_imponibile': buste['imponibile_fiscale'],
        'num_mesi_buste': buste['num_mesi'],
    })
