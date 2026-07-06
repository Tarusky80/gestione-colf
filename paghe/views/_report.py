from paghe.views._common_imports import *
from datetime import date, timedelta
from django.db.models import Count, Sum
import io
import logging

logger = logging.getLogger(__name__)

from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import Image as RLImage
from paghe.views._helpers import _registra_font_pdf

MESI_IT = ['', 'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
           'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']

# === Stili PDF condivisi — minimal B&N ===
_C_DARK = HexColor('#333')
_C_MED  = HexColor('#666')
_C_LIGHT = HexColor('#999')

_S_TITLE = ParagraphStyle('t', fontSize=14, leading=18, textColor=_C_DARK, fontName='Roboto-Bold', spaceAfter=1, alignment=TA_LEFT)
_S_SUB   = ParagraphStyle('sub', fontSize=7.5, leading=10, textColor=_C_MED, fontName='Roboto', alignment=TA_LEFT, spaceAfter=2)
_S_HDR   = ParagraphStyle('h', fontSize=7.5, leading=11, textColor=_C_DARK, fontName='Roboto-Bold', alignment=TA_LEFT)
_S_CELL  = ParagraphStyle('c', fontSize=7.5, leading=11, textColor=_C_DARK, fontName='Roboto', alignment=TA_LEFT)
_S_NUM   = ParagraphStyle('n', fontSize=7.5, leading=11, textColor=_C_DARK, fontName='Roboto', alignment=TA_CENTER)
_S_VAL   = ParagraphStyle('v', fontSize=7.5, leading=11, textColor=_C_DARK, fontName='Roboto', alignment=TA_RIGHT)
_S_KV    = ParagraphStyle('kv', fontSize=16, leading=20, textColor=_C_DARK, fontName='Roboto-Bold', alignment=TA_CENTER)
_S_KL    = ParagraphStyle('kl', fontSize=7, leading=9, textColor=_C_MED, fontName='Roboto', alignment=TA_CENTER)
_S_FOOT  = ParagraphStyle('f', fontSize=7, leading=9, textColor=_C_MED, fontName='Roboto', alignment=TA_CENTER)

_BLACK = HexColor('#000')


def _kpi_table(kpi_pairs):
    """KPI row: 4 coppie (valore, etichetta), nessuna linea decorativa."""
    avail_w = landscape(A4)[0] - 20*mm
    kw = avail_w / 4
    vals = [Paragraph(v, _S_KV) for v, _ in kpi_pairs]
    lbls = [Paragraph(l, _S_KL) for _, l in kpi_pairs]
    t = Table([vals, lbls], colWidths=[kw]*4)
    t.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    return t


@login_required
@permesso_richiesto('report')
def report_mensile_pdf(request):
    oggi = date.today()
    mese = oggi.month
    anno = oggi.year
    mese_label = MESI_IT[mese]

    from paghe.models import ContrattoAttivo, BustaPaga, CUAnnuale, ProgettoRegionale, GestoreBackup
    opzioni = get_opzioni()
    _registra_font_pdf()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        leftMargin=10*mm, rightMargin=10*mm,
        topMargin=6*mm, bottomMargin=6*mm,
    )

    story = []

    # === DATI ===
    contratti_attivi_qs = ContrattoAttivo.objects.filter(stato='ATTIVO')
    totale_attivi = contratti_attivi_qs.count()
    ore_totali = sum(float(c.ore_calcolate or 0) for c in contratti_attivi_qs)
    budget_totale = ProgettoRegionale.objects.aggregate(s=Sum('budget_mensile'))['s'] or 0
    buste_tot_anno = BustaPaga.objects.filter(anno=anno).count()
    buste_arch_anno = BustaPaga.objects.filter(anno=anno, stato='ARCHIVIATA').count()
    buste_arch_pct = round(buste_arch_anno / max(buste_tot_anno, 1) * 100)

    buste_bozze = BustaPaga.objects.filter(contratto__in=contratti_attivi_qs, anno=anno, stato='BOZZA').count()
    buste_approvate = BustaPaga.objects.filter(contratto__in=contratti_attivi_qs, anno=anno, stato='APPROVATA').count()
    buste_archiviate = BustaPaga.objects.filter(contratto__in=contratti_attivi_qs, anno=anno, stato='ARCHIVIATA').count()
    buste_tot = buste_bozze + buste_approvate + buste_archiviate or 1

    contratti_con_cu = CUAnnuale.objects.filter(contratto__in=contratti_attivi_qs, anno=anno).values('contratto').distinct().count()
    contratti_senza_cu = max(0, totale_attivi - contratti_con_cu)
    contratti_contributi_versati = contratti_attivi_qs.filter(contributi_trimestre_versati=True).count()
    contratti_contributi_da_versare = max(0, totale_attivi - contratti_contributi_versati)

    nuovi_mese = contratti_attivi_qs.filter(data_assunzione__year=anno, data_assunzione__month=mese).count()
    contratti_cessati_mese = contratti_attivi_qs.filter(data_fine__year=anno, data_fine__month=mese).count()
    tra_30gg = oggi + timedelta(days=30); tra_60gg = oggi + timedelta(days=60); tra_90gg = oggi + timedelta(days=90)
    scad_30 = contratti_attivi_qs.filter(data_fine__gte=oggi, data_fine__lte=tra_30gg).count()
    scad_60 = contratti_attivi_qs.filter(data_fine__gte=oggi, data_fine__lte=tra_60gg).count()
    scad_90 = contratti_attivi_qs.filter(data_fine__gte=oggi, data_fine__lte=tra_90gg).count()

    con_progetto = contratti_attivi_qs.annotate(pc=Count('progetto')).filter(pc__gt=0).count()
    senza_progetto = max(0, totale_attivi - con_progetto)
    budget_per_tipo = ProgettoRegionale.objects.values('tipo__nome').annotate(totale=Sum('budget_mensile')).order_by('-totale')

    tfr_tot = sum(float(c.proiezione_tfr_annuale) for c in contratti_attivi_qs if c.proiezione_tfr_annuale)
    datori_count = contratti_attivi_qs.values('datore').distinct().count()
    lavoratori_count = contratti_attivi_qs.values('lavoratore').distinct().count()

    ultimo_bk = GestoreBackup.objects.order_by('-data_creazione').first()
    ultimo_backup = ultimo_bk.data_creazione.strftime('%d/%m/%Y %H:%M') if ultimo_bk else '\u2014'
    data_gen = oggi.strftime('%d/%m/%Y %H:%M')

    # === HEADER ===
    story.append(Spacer(1, 3*mm))
    logo_rl = None
    if opzioni and opzioni.logo_buste_paga and opzioni.logo_buste_paga.path:
        import os as _os
        if _os.path.exists(opzioni.logo_buste_paga.path):
            try:
                logo_rl = RLImage(opzioni.logo_buste_paga.path, width=100, height=35)
            except Exception:
                logger.exception("Errore in report_mensile_pdf")
                logo_rl = None

    studio_nome = getattr(opzioni, 'denominazione_studio', None) or getattr(opzioni, 'nome_studio', '') or ''
    titolo = f'REPORT MENSILE \u2014 {mese_label.upper()} {anno}'
    if logo_rl:
        avail_w = landscape(A4)[0] - 20*mm
        txt_col_w = avail_w - 100 - 6*mm
        txt_rows = [[Paragraph(titolo, _S_TITLE)]]
        if studio_nome:
            txt_rows.append([Paragraph(studio_nome, _S_SUB)])
        txt_rows.append([Paragraph(f'Generato il {data_gen}', _S_SUB)])
        txt_sub = Table(txt_rows, colWidths=[txt_col_w])
        txt_sub.setStyle(TableStyle([
            ('LEFTPADDING',(0,0),(-1,-1),0), ('RIGHTPADDING',(0,0),(-1,-1),0),
            ('TOPPADDING',(0,0),(-1,-1),0), ('BOTTOMPADDING',(0,0),(-1,-1),1)
        ]))
        hdr_tbl = Table([[logo_rl, txt_sub]], colWidths=[100, txt_col_w])
        hdr_tbl.setStyle(TableStyle([
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('LEFTPADDING',(0,0),(-1,-1),0), ('RIGHTPADDING',(0,0),(-1,-1),0),
            ('RIGHTPADDING',(0,0),(0,0),8), ('LEFTPADDING',(1,0),(1,-1),8),
        ]))
        story.append(hdr_tbl)
    else:
        story.append(Paragraph(titolo, _S_TITLE))
        if studio_nome:
            story.append(Paragraph(studio_nome, _S_SUB))
        story.append(Paragraph(f'Generato il {data_gen}', _S_SUB))
    story.append(Spacer(1, 2))

    # === KPI ROW ===
    story.append(_kpi_table([
        (str(totale_attivi), 'Contratti attivi'),
        (f'{ore_totali:.0f}', 'Ore / mese'),
        (f'\u20ac {float(budget_totale):,.0f}'.replace(',', '.'), 'Budget mensile'),
        (f'{buste_arch_pct}%', 'Buste archiviate'),
    ]))
    story.append(Spacer(1, 3*mm))

    # === DETTAGLIO ===
    avail_w = landscape(A4)[0] - 20*mm
    left_w = avail_w * 0.48
    right_w = avail_w * 0.48

    def _joined_tables(dati_a, dati_b, n_a, n_b):
        max_r = max(len(dati_a), len(dati_b))
        rows = []
        for i in range(max_r):
            ra = dati_a[i] if i < len(dati_a) else [''] * n_a
            rb = dati_b[i] if i < len(dati_b) else [''] * n_b
            rows.append(ra + rb)
        cw = [left_w / n_a] * n_a + [right_w / n_b] * n_b
        cmds = [
            ('LINEBELOW', (0,0), (-1,0), 0.5, _BLACK),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ]
        return Table(rows, colWidths=cw, repeatRows=1, style=TableStyle(cmds))

    def _rows(tuples):
        return [[Paragraph(t[0], _S_HDR)] + [Paragraph(str(v), _S_CELL) for v in t[1:]] for t in tuples]

    buste_a = [
        ('Buste Paga', 'N.', '%'),
        ('Bozze', buste_bozze, f'{buste_bozze/buste_tot*100:.0f}%'),
        ('Approvate', buste_approvate, f'{buste_approvate/buste_tot*100:.0f}%'),
        ('Archiviate', buste_archiviate, f'{buste_archiviate/buste_tot*100:.0f}%'),
    ]
    uniemens_b = [
        ('UNIEMENS & Contributi', 'N.', '%'),
        ('Con CU', contratti_con_cu, f'{contratti_con_cu/max(totale_attivi,1)*100:.0f}%'),
        ('Senza CU', contratti_senza_cu, f'{contratti_senza_cu/max(totale_attivi,1)*100:.0f}%'),
        ('Versati', contratti_contributi_versati, f'{contratti_contributi_versati/max(totale_attivi,1)*100:.0f}%'),
        ('Da versare', contratti_contributi_da_versare, f'{contratti_contributi_da_versare/max(totale_attivi,1)*100:.0f}%'),
    ]
    story.append(_joined_tables(_rows(buste_a), _rows(uniemens_b), 3, 3))
    story.append(Spacer(1, 3*mm))

    contratti_a = [
        ('Movimenti Contratti', 'N.'),
        (f'Nuovi assunti ({mese_label})', nuovi_mese),
        (f'Cessati ({mese_label})', contratti_cessati_mese),
        ('In scadenza (30gg)', scad_30),
        ('In scadenza (60gg)', scad_60),
        ('In scadenza (90gg)', scad_90),
    ]
    prog_b = [('Progetti e Budget', 'Budget')]
    for b in budget_per_tipo:
        nm = b['tipo__nome'] or 'N/D'
        vl = f'\u20ac {float(b["totale"] or 0):,.0f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        prog_b.append((nm, vl))
    prog_b.append(('Con progetto', str(con_progetto)))
    prog_b.append(('Senza progetto', str(senza_progetto)))
    story.append(_joined_tables(_rows(contratti_a), _rows(prog_b), 2, 2))
    story.append(Spacer(1, 3*mm))

    altri_a = [
        ('Altri Dati', 'Valore'),
        ('Datori coinvolti', datori_count),
        ('Lavoratori coinvolti', lavoratori_count),
        ('TFR proiettato annuale', f'\u20ac {tfr_tot:,.0f}'.replace(',', '.')),
        ('Ultimo backup', ultimo_backup),
    ]
    info_b = [
        ('Info Report', ''),
        ('Generato il', data_gen),
        ('Programma', getattr(opzioni, 'nome_programma', 'GESTIONE CO.LF.')),
    ]
    story.append(_joined_tables(_rows(altri_a), _rows(info_b), 2, 2))

    # === FOOTER ===
    story.append(Spacer(1, 4*mm))
    ver = f' v{opzioni.versione_programma}' if getattr(opzioni, 'versione_programma', None) else ''
    story.append(Paragraph(
        f'{getattr(opzioni, "nome_programma", "GESTIONE CO.LF.") or "GESTIONE CO.LF."}{ver}',
        _S_FOOT
    ))

    doc.build(story)
    pdf = buf.getvalue()
    buf.close()

    filename = f'Report_Mensile_{mese_label}_{anno}.pdf'
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


@login_required
@permesso_richiesto('report')
def report_annuale_pdf(request, anno=None, datore_id=None):
    oggi = date.today()
    if anno is None:
        anno = oggi.year
    from paghe.models import ContrattoLavoro, BustaPaga, CUAnnuale, ProgettoRegionale
    from django.db.models import Sum, Count
    opzioni = get_opzioni()
    _registra_font_pdf()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        leftMargin=10*mm, rightMargin=10*mm,
        topMargin=6*mm, bottomMargin=6*mm,
    )

    story = []
    avail_w = landscape(A4)[0] - 20*mm

    # === DATI ANNUALI ===
    contratti_qs = ContrattoLavoro.objects.all()
    if datore_id:
        contratti_qs = contratti_qs.filter(datore_id=datore_id)

    buste_anno = BustaPaga.objects.filter(anno=anno)
    if datore_id:
        buste_anno = buste_anno.filter(contratto__datore_id=datore_id)

    totali_annuali = buste_anno.aggregate(
        lordo=Sum('totale_lordo'),
        inps=Sum('contributi_inps_totale'),
        cassa=Sum('contributi_cassa_totale'),
        contributi=Sum('totale_contributi'),
        netto=Sum('netto'),
        buste_count=Count('id'),
    )
    lordo_tot = float(totali_annuali['lordo'] or 0)
    float(totali_annuali['inps'] or 0)
    float(totali_annuali['cassa'] or 0)
    contributi_tot = float(totali_annuali['contributi'] or 0)
    netto_tot = float(totali_annuali['netto'] or 0)
    buste_count = totali_annuali['buste_count'] or 0

    tfr_annuale = buste_anno.exclude(tfr_data__isnull=True).count()

    dettaglio_contratti = buste_anno.values(
        'contratto', 'contratto__datore__nome_cognome', 'contratto__lavoratore__nome_cognome'
    ).annotate(
        mesi=Count('id'),
        lordo_c=Sum('totale_lordo'),
        inps_c=Sum('contributi_inps_totale'),
        cassa_c=Sum('contributi_cassa_totale'),
        netto_c=Sum('netto'),
    ).order_by('contratto__datore__nome_cognome')

    contratti_con_cu = CUAnnuale.objects.filter(anno=anno)
    if datore_id:
        contratti_con_cu = contratti_con_cu.filter(contratto__datore_id=datore_id)
    cu_count = contratti_con_cu.count()

    budget_mensile_tot = ProgettoRegionale.objects.aggregate(s=Sum('budget_mensile'))['s'] or 0
    budget_annuale = float(budget_mensile_tot) * 12

    data_gen = oggi.strftime('%d/%m/%Y %H:%M')

    # === HEADER ===
    story.append(Spacer(1, 3*mm))
    logo_rl = None
    if opzioni and opzioni.logo_buste_paga and opzioni.logo_buste_paga.path:
        import os as _os
        if _os.path.exists(opzioni.logo_buste_paga.path):
            try:
                logo_rl = RLImage(opzioni.logo_buste_paga.path, width=100, height=35)
            except Exception:
                logger.exception("Errore in report_annuale_pdf")
                logo_rl = None

    studio_nome = getattr(opzioni, 'denominazione_studio', None) or getattr(opzioni, 'nome_studio', '') or ''
    titolo = f'REPORT ANNUALE \u2014 {anno}'
    if datore_id:
        datore_nome = contratti_qs.values_list('datore__nome_cognome', flat=True).first() or ''
        titolo = f'REPORT ANNUALE \u2014 {anno} \u2014 {datore_nome}'

    if logo_rl:
        txt_col_w = avail_w - 100 - 6*mm
        txt_rows = [[Paragraph(titolo, _S_TITLE)]]
        if studio_nome:
            txt_rows.append([Paragraph(studio_nome, _S_SUB)])
        txt_rows.append([Paragraph(f'Generato il {data_gen}', _S_SUB)])
        txt_sub = Table(txt_rows, colWidths=[txt_col_w])
        txt_sub.setStyle(TableStyle([
            ('LEFTPADDING',(0,0),(-1,-1),0), ('RIGHTPADDING',(0,0),(-1,-1),0),
            ('TOPPADDING',(0,0),(-1,-1),0), ('BOTTOMPADDING',(0,0),(-1,-1),1)
        ]))
        hdr_tbl = Table([[logo_rl, txt_sub]], colWidths=[100, txt_col_w])
        hdr_tbl.setStyle(TableStyle([
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('LEFTPADDING',(0,0),(-1,-1),0), ('RIGHTPADDING',(0,0),(-1,-1),0),
            ('RIGHTPADDING',(0,0),(0,0),8), ('LEFTPADDING',(1,0),(1,-1),8),
        ]))
        story.append(hdr_tbl)
    else:
        story.append(Paragraph(titolo, _S_TITLE))
        if studio_nome:
            story.append(Paragraph(studio_nome, _S_SUB))
        story.append(Paragraph(f'Generato il {data_gen}', _S_SUB))
    story.append(Spacer(1, 2))

    # === KPI ROW ===
    story.append(_kpi_table([
        (f'\u20ac {lordo_tot:,.0f}'.replace(',', '.'), 'Lordo annuo'),
        (f'\u20ac {contributi_tot:,.0f}'.replace(',', '.'), 'Contributi annui'),
        (f'\u20ac {netto_tot:,.0f}'.replace(',', '.'), 'Netto annuo'),
        (str(buste_count), 'Buste emesse'),
    ]))
    story.append(Spacer(1, 3*mm))

    # === TABELLA DETTAGLIO CONTRATTI ===
    if dettaglio_contratti:
        hdr_row = [Paragraph('Datore', _S_HDR), Paragraph('Lavoratore', _S_HDR),
                   Paragraph('Mesi', _S_NUM), Paragraph('Lordo', _S_VAL),
                   Paragraph('INPS', _S_VAL), Paragraph('Cassa', _S_VAL),
                   Paragraph('Netto', _S_VAL)]
        rows = [hdr_row]
        f_val = lambda v: f'\u20ac {float(v or 0):,.0f}'.replace(',', '.')
        for dc in dettaglio_contratti:
            rows.append([
                Paragraph(dc['contratto__datore__nome_cognome'] or '', _S_CELL),
                Paragraph(dc['contratto__lavoratore__nome_cognome'] or '', _S_CELL),
                Paragraph(str(dc['mesi']), _S_NUM),
                Paragraph(f_val(dc['lordo_c']), _S_VAL),
                Paragraph(f_val(dc['inps_c']), _S_VAL),
                Paragraph(f_val(dc['cassa_c']), _S_VAL),
                Paragraph(f_val(dc['netto_c']), _S_VAL),
            ])
        n_cols = 7
        col_w = avail_w / n_cols
        tbl = Table(rows, colWidths=[col_w]*n_cols, repeatRows=1)
        cmds = [
            ('LINEBELOW', (0,0), (-1,0), 0.5, _BLACK),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ]
        tbl.setStyle(TableStyle(cmds))
        story.append(tbl)
    else:
        story.append(Paragraph('Nessuna busta paga trovata per l\'anno selezionato.', _S_CELL))

    # === RIEPILOGO BUDGET / CU ===
    story.append(Spacer(1, 4*mm))
    budget_rows = [
        [Paragraph('Riepilogo', _S_HDR), Paragraph('Valore', _S_VAL)],
        [Paragraph('Budget mensile totale', _S_CELL),
         Paragraph(f'\u20ac {float(budget_mensile_tot):,.0f}'.replace(',', '.'), _S_VAL)],
        [Paragraph('Budget annuale stimato', _S_CELL),
         Paragraph(f'{budget_annuale:,.0f}'.replace(',', '.'), _S_VAL)],
        [Paragraph('Lordo annuo erogato', _S_CELL),
         Paragraph(f'\u20ac {lordo_tot:,.0f}'.replace(',', '.'), _S_VAL)],
        [Paragraph('Buste con TFR', _S_CELL), Paragraph(str(tfr_annuale), _S_NUM)],
        [Paragraph('Certificazioni Uniche (CU)', _S_CELL), Paragraph(str(cu_count), _S_NUM)],
    ]
    bgt_w = avail_w * 0.5
    bgt_tbl = Table(budget_rows, colWidths=[bgt_w*0.7, bgt_w*0.3])
    bgt_tbl.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,0), 0.5, _BLACK),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(bgt_tbl)

    # === FOOTER ===
    story.append(Spacer(1, 4*mm))
    ver = f' v{opzioni.versione_programma}' if getattr(opzioni, 'versione_programma', None) else ''
    story.append(Paragraph(
        f'{getattr(opzioni, "nome_programma", "GESTIONE CO.LF.") or "GESTIONE CO.LF."}{ver}',
        _S_FOOT
    ))

    doc.build(story)
    pdf = buf.getvalue()
    buf.close()

    suffix = f'_{datore_id}' if datore_id else ''
    filename = f'Report_Annuale_{anno}{suffix}.pdf'
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response
