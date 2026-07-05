"""Modulo _buste_pdf - generato automaticamente da views.py"""

from paghe.views._common_imports import *

logger = logging.getLogger(__name__)

from paghe.views._helpers import _registra_font_pdf, _formatta_testo_pdf, _tipo_calcolo_label
from paghe.views._calcoli_core import _calcola_busta_data, _calcola_progetti_data




# --- _genera_html_busta ---


def _genera_html_busta(ctx, progetti_data=None):
    """Genera HTML della busta paga per xhtml2pdf. Usa ctx da _calcola_busta_data()."""
    f = lambda v: f"{v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    lbl = lambda l: f'<span style="font-size:6.5pt;color:#555;letter-spacing:0.04em;text-transform:uppercase;">{l}</span>'
    val = lambda v: f'<span style="font-size:9pt;font-weight:700;color:#222;">{v}</span>'
    row_data = lambda l, v, s='': f'<tr><td style="padding:2pt 4pt;border-bottom:0.5pt solid #ddd;font-size:8pt;color:#333;">{l}<br/><span style="font-size:7pt;color:#666;">{s}</span></td><td style="padding:2pt 4pt;border-bottom:0.5pt solid #ddd;text-align:right;font-size:8.5pt;font-weight:700;color:#333;">€ {v}</td></tr>'
    tot_row = lambda l, v: f'<tr><td style="padding:3pt 4pt;font-size:9pt;font-weight:700;color:#2c5282;border-top:2pt solid #2c5282;border-bottom:0.5pt solid #ddd;">{l}</td><td style="padding:3pt 4pt;text-align:right;font-size:10pt;font-weight:700;color:#222;border-top:2pt solid #2c5282;border-bottom:0.5pt solid #ddd;">€ {v}</td></tr>'
    net_row = lambda l, v: f'<tr><td style="padding:3pt 4pt;font-size:11pt;font-weight:700;color:#2c5282;border-top:1.5pt solid #2c5282;">{l}</td><td style="padding:3pt 4pt;text-align:right;font-size:15pt;font-weight:800;color:#2c5282;border-top:1.5pt solid #2c5282;">€ {v}</td></tr>'

    soglia_label = f"PIU' DI {ctx['soglia_ore']:.2f} ORE SETTIMANALI" if ctx['sopra_soglia'] else f"MENO DI {ctx['soglia_ore']:.2f} ORE SETTIMANALI"
    sabati_str = '\u2713' * ctx['num_sabati']

    progetti_html = ''
    if ctx.get('progetti'):
        progetti_lines = [p['nome'] for p in ctx['progetti']]
        for pl in progetti_lines:
            progetti_html += f'<span style="display:inline-block;padding:1pt 6pt;border-radius:4pt;font-size:7.5pt;border:0.5pt solid #5E6AD2;margin:1pt 2pt;">{pl}</span>'

    info_rows = ''
    def info_row(l, v1, l2='', v2=''):
        c1 = f'<td style="width:20%;padding:2pt 4pt;border-bottom:0.5pt solid #ddd;">{lbl(l)}<br/>{val(v1)}</td>'
        c2 = f'<td style="width:30%;padding:2pt 4pt;border-bottom:0.5pt solid #ddd;">{"<br/>".join(v1.split(chr(10))) if chr(10) in v1 else ""}</td>' if not l2 else ''
        if l2:
            c2 = f'<td style="width:20%;padding:2pt 4pt;border-bottom:0.5pt solid #ddd;">{lbl(l2)}<br/>{val(v2)}</td>'
            c3 = f'<td style="width:30%;padding:2pt 4pt;border-bottom:0.5pt solid #ddd;">{v2}</td>'
            return f'<tr>{c1}<td style="width:30%;padding:2pt 4pt;border-bottom:0.5pt solid #ddd;">{v1}</td>{c2}{c3}</tr>'
        return f'<tr>{c1}<td style="width:30%;padding:2pt 4pt;border-bottom:0.5pt solid #ddd;">{v1}</td>{c2}</tr>'

    info_rows = f'''
    <tr><td style="width:20%;padding:2pt 4pt;border-bottom:0.5pt solid #ddd;">{lbl("DATORE")}<br/>{val(ctx["datore"])}</td>
    <td style="width:30%;padding:2pt 4pt;border-bottom:0.5pt solid #ddd;">{ctx["datore"]} — {ctx["datore_indirizzo"]}{" - "+ctx["datore_comune"] if ctx["datore_comune"] else ""}</td>
    <td style="width:20%;padding:2pt 4pt;border-bottom:0.5pt solid #ddd;">{lbl("LAVORATORE")}<br/>{val(ctx["lavoratore"])}</td>
    <td style="width:30%;padding:2pt 4pt;border-bottom:0.5pt solid #ddd;">{ctx["lavoratore"]} — {ctx["lavoratore_indirizzo"]}{" - "+ctx["lavoratore_comune"] if ctx["lavoratore_comune"] else ""}</td></tr>
    <tr><td style="width:20%;padding:2pt 4pt;border-bottom:0.5pt solid #ddd;">{lbl("DATA INIZIO")}<br/>{val(ctx["data_assunzione"])}</td>
    <td style="width:30%;padding:2pt 4pt;border-bottom:0.5pt solid #ddd;"></td>
    <td style="width:20%;padding:2pt 4pt;border-bottom:0.5pt solid #ddd;">{lbl("TIPO CONTRATTO")}<br/>{val(ctx["tipo_contratto"])}</td>
    <td style="width:30%;padding:2pt 4pt;border-bottom:0.5pt solid #ddd;"></td></tr>
    <tr><td style="width:20%;padding:2pt 4pt;border-bottom:0.5pt solid #ddd;">{lbl("ORE SETTIMANALI")}<br/>{val(f"<span>{ctx['ore_settimanali']:.2f} h</span>")}</td>
    <td style="width:30%;padding:2pt 4pt;border-bottom:0.5pt solid #ddd;">{soglia_label}</td>
    <td style="width:20%;padding:2pt 4pt;border-bottom:0.5pt solid #ddd;">{lbl("SETTIMANE MENSILI")}<br/>{val(str(ctx['settimane_mensili']))}</td>
    <td style="width:30%;padding:2pt 4pt;border-bottom:0.5pt solid #ddd;">{sabati_str}</td></tr>
    <tr><td style="width:20%;padding:2pt 4pt;border-bottom:0.5pt solid #ddd;">{lbl("ORE MESE")}<br/>{val(f"{ctx['ore_mensili']:.2f} h")}</td>
    <td style="width:30%;padding:2pt 4pt;border-bottom:0.5pt solid #ddd;">INPS: {ctx['ore_inps']} h</td>
    <td style="width:20%;padding:2pt 4pt;border-bottom:0.5pt solid #ddd;">{lbl("LIVELLO")}<br/>{val(ctx['livello_codice'])}</td>
    <td style="width:30%;padding:2pt 4pt;border-bottom:0.5pt solid #ddd;">{ctx['descrizione_corta']}</td></tr>
    <tr><td style="width:20%;padding:2pt 4pt;border-bottom:0.5pt solid #ddd;">{lbl("CODICE RAPPORTO")}<br/>{val(ctx['codice_rapporto_inps'])}</td>
    <td style="width:30%;padding:2pt 4pt;border-bottom:0.5pt solid #ddd;"></td>
    <td style="width:20%;padding:2pt 4pt;border-bottom:0.5pt solid #ddd;">{lbl("PAGA EFF. INPS")}<br/>{val(f"€ {ctx['paga_effettiva_inps_oraria']:.4f}/h")}</td>
    <td style="width:30%;padding:2pt 4pt;border-bottom:0.5pt solid #ddd;">€ {ctx['paga_effettiva_inps_mensile']:.2f}/mese</td></tr>
    <tr><td style="width:20%;padding:2pt 4pt;">{lbl("PAGA APPLICATA")}<br/>{val(f"€ {ctx['paga_applicata_oraria']:.4f}/h")}</td>
    <td style="width:30%;padding:2pt 4pt;">€ {ctx['paga_applicata_mensile']:.2f}/mese</td><td style="width:20%;padding:2pt 4pt;">{lbl("TIPO CALCOLO")}<br/>{val(_tipo_calcolo_label(ctx.get('tipo_calcolo', 'CONVIVENTE')))}</td><td style="width:30%;padding:2pt 4pt;"></td></tr>
    '''
    if progetti_html:
        info_rows += f'<tr><td style="padding:2pt 4pt;">{lbl("PROGETTI")}</td><td colspan="3" style="padding:2pt 4pt;">{progetti_html}</td></tr>'

    # Lordo rows
    lordo_rows = ''
    lordo_rows += row_data("Paga base", f(ctx['paga_base']['totale']), f"€ {ctx['paga_base']['orario']:.4f} x {ctx['ore_mensili']:.2f}h")
    for ind in ctx['indennita']:
        lordo_rows += row_data(ind['label'], f(ind['totale']), f"€ {ind['orario']:.4f} x {ctx['ore_mensili']:.2f}h")
    lordo_rows += row_data("Scatti anzianit\u00e0", f(ctx['scatti_anzianita']['valore']), ctx['scatti_anzianita']['dettaglio'])
    for rp in ctx['ratei_pagati']:
        if rp.get('incluso'):
            _calc_val = rp['orario'] * ctx['ore_mensili']
            sub = f"(€{rp['orario']:.4f} x {ctx['ore_mensili']:.2f}h = €{_calc_val:.2f})<br/>Incluso nel lordo mensile"
        else:
            sub = "Da corrispondere a fine rapporto" if rp['totale'] > 0 else ""
        lordo_rows += row_data(rp['label'] + (" (*)" if rp.get('incluso') else ""), f(rp['totale']), sub)
    lordo_rows += row_data("Indennit\u00e0 e Ratei pagati", f(round(ctx['totale_indennita'] + ctx['totale_ratei_inclusi'], 4)), "")
    lordo_rows += tot_row("TOTALE LORDO", f(ctx['totale_lordo']))

    # Contributi rows
    contrib_rows = ''
    contrib_rows += row_data("INPS", f(ctx['contributi']['inps']['totale']), f"€ {ctx['contributi']['inps']['orario']:.4f} x {ctx['ore_inps']}h — {ctx['contributi']['inps']['fascia']} soglia")
    cassa_nome = ctx['contributi']['cassa']['nome'] or 'Cassa/Ente'
    contrib_rows += row_data(cassa_nome, f(ctx['contributi']['cassa']['totale']), f"€ {ctx['contributi']['cassa']['orario']:.4f} x {ctx['ore_inps']}h")
    contrib_rows += tot_row("TOTALE CONTRIBUTI", f(ctx['contributi']['totale']))

    # Trattenute rows
    trat_rows = ''
    dettaglio_conv = ', '.join(ctx['trattenute']['convivenza']['dettaglio']) if ctx['trattenute']['convivenza']['dettaglio'] else ''
    label_conv = "Vitto e alloggio forfettario" if ctx.get('tipo_calcolo') == 'SOSTITUZIONE' else "Convivenza"
    trat_rows += row_data(label_conv, f(ctx['trattenute']['convivenza']['totale']), dettaglio_conv)
    accantonati_nomi_4 = [r['label'] for r in ctx['ratei_pagati'] if not r.get('incluso') and r['totale'] > 0]
    acc_nota_4 = ', '.join(accantonati_nomi_4) + ' non pagati' if accantonati_nomi_4 else ''
    trat_rows += row_data("Ratei accantonati", f(ctx['trattenute']['ratei_accantonati']), acc_nota_4)
    trat_rows += tot_row("TOTALE TRATTENUTE", f(ctx['trattenute']['totale']))

    # Netto
    netto_html = net_row("NETTO IN BUSTA", f(ctx['netto']))

    # Dati studio
    logo_html = ''
    if ctx.get('logo_buste_paga_path') and os.path.exists(ctx['logo_buste_paga_path']):
        try:
            with open(ctx['logo_buste_paga_path'], 'rb') as _f:
                import base64 as _b64
                _data = _b64.b64encode(_f.read()).decode('utf-8')
            _ext = ctx['logo_buste_paga_path'].rsplit('.',1)[-1].lower()
            if _ext == 'jpg': _ext = 'jpeg'
            logo_html = f'<img src="data:image/{_ext};base64,{_data}" width="110" style="margin-bottom:4pt;" alt="Logo studio"/>'
        except Exception:
            logger.exception("Errore in info_row")
            logo_html = ''
    studio_parts = list(filter(None, [
        ctx.get('dati_studio'),
        f"Tel: {ctx['telefono_studio']}" if ctx.get('telefono_studio') else None,
        f"Mail: {ctx['email_studio']}" if ctx.get('email_studio') else None,
    ]))
    studio_line = ' | '.join(studio_parts) if studio_parts else ''

    # Note
    note_html = ''
    if ctx.get('note_datore'):
        note_html += f'<div style="margin-top:8pt;padding:6pt 0;border-top:0.5pt solid #ddd;font-size:7.5pt;color:#444;"><span style="font-size:7pt;font-weight:700;text-transform:uppercase;color:#555;display:block;">NOTE DATORE</span>{ctx["note_datore"]}</div>'

    # Alert contributi
    alert_html = ''
    if ctx.get('alert_contributi_studio'):
        alert_html += f'<div style="margin-top:4pt;padding:4pt 0;border-top:0.5pt solid #ddd;font-size:7pt;color:#444;"><span style="font-size:7pt;font-weight:700;text-transform:uppercase;color:#555;display:block;">SCADENZE</span>{ctx["alert_contributi_studio"]}</div>'

    # Note avvertenze
    avv_html = ''
    if ctx.get('note_avvertenze'):
        avv_html += f'<div style="margin-top:4pt;padding:4pt 0;border-top:0.5pt solid #ddd;font-size:7pt;color:#444;"><span style="font-size:7pt;font-weight:700;text-transform:uppercase;color:#555;display:block;">NOTE AGGIUNTIVE / AVVERTENZE</span>{ctx["note_avvertenze"]}</div>'

    # Avviso patrono
    patrono_html = ''
    if ctx.get('avviso_patrono'):
        patrono_html += f'<div style="margin-top:4pt;padding:4pt 6pt;border:1pt solid #c97a0e;border-radius:3pt;font-size:7pt;color:#c97a0e;font-weight:700;background:#fff8f0;">{ctx["avviso_patrono"]}</div>'

    # Progetti detail page
    dettaglio_html = ''
    if progetti_data and progetti_data.get('righe'):
        def p2_fmt(v):
            return f"€ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        p2_rows = ''
        for r in progetti_data['righe']:
            p2_rows += f'''<tr style="border-bottom:0.5pt solid #eee;">
                <td style="padding:3pt 4pt;font-size:7.5pt;color:#555;">{r['nome']}</td>
                <td style="padding:3pt 4pt;font-size:7.5pt;color:#333;text-align:right;">{p2_fmt(r['lordo_progetto'])}</td>
                <td style="padding:3pt 4pt;font-size:7.5pt;color:#333;text-align:right;">{p2_fmt(r['paga_oraria'])}</td>
                <td style="padding:3pt 4pt;font-size:7.5pt;color:#333;text-align:center;">{r['ore']}</td>
                <td style="padding:3pt 4pt;font-size:7.5pt;color:#333;text-align:right;">{p2_fmt(r['contrib'])}</td>
                <td style="padding:3pt 4pt;font-size:7.5pt;color:#333;text-align:right;">{p2_fmt(r['ratei_ind'])}</td>
                <td style="padding:3pt 4pt;font-size:7.5pt;color:#333;text-align:right;font-weight:700;">{p2_fmt(r['netto'])}</td>
            </tr>'''
        t = progetti_data['totali']
        p2_totali = f'''<tr style="border-top:2pt solid #2c5282;">
            <td style="padding:4pt 4pt;font-size:8pt;font-weight:700;color:#2c5282;">TOTALE</td>
            <td style="padding:4pt 4pt;font-size:8pt;font-weight:700;color:#2c5282;text-align:right;">{p2_fmt(t['lordo_progetto'])}</td>
            <td style="padding:4pt 4pt;"></td>
            <td style="padding:4pt 4pt;font-size:8pt;font-weight:700;color:#2c5282;text-align:center;">{t['ore']}</td>
            <td style="padding:4pt 4pt;font-size:8pt;font-weight:700;color:#2c5282;text-align:right;">{p2_fmt(t['contrib'])}</td>
            <td style="padding:4pt 4pt;font-size:8pt;font-weight:700;color:#2c5282;text-align:right;">{p2_fmt(t['ratei_ind'])}</td>
            <td style="padding:4pt 4pt;"></td>
        </tr>
        <tr><td colspan="6" style="text-align:right;padding:4pt 4pt;font-size:9pt;font-weight:800;color:#2c5282;">NETTO</td>
            <td style="padding:4pt 4pt;font-size:9pt;font-weight:800;color:#2c5282;text-align:right;">{p2_fmt(t['netto'])}</td>
        </tr>'''
        _riep_parts = []
        if ctx.get('indennita'):
            _ind_items = [f"{i['label']} {p2_fmt(i['totale'])}" for i in ctx['indennita']]
            _riep_parts.append(f"Ind.: {' + '.join(_ind_items)} = {p2_fmt(ctx['totale_indennita'])} ({len(ctx['indennita'])})")
        if ctx.get('ratei_pagati'):
            _ri_incl = 0.0; _ri_acc = 0.0; _ci = 0; _ca = 0
            _il = []; _al = []
            for _r in ctx['ratei_pagati']:
                if _r.get('incluso'):
                    _ci += 1; _ri_incl += _r.get('valore_effettivo', 0) or 0; _il.append(_r['label'])
                else:
                    _ca += 1; _ri_acc += _r.get('valore_effettivo', _r.get('totale', 0)) or 0; _al.append(_r['label'])
            _rp = 'Ratei:'
            if _ci > 0: _rp += f" +{p2_fmt(_ri_incl)} ({','.join(_il)} \u2014 {_ci} INCLUSI)"
            if _ca > 0: _rp += f" +{p2_fmt(_ri_acc)} ({','.join(_al)} \u2014 {_ca} {'NON INCLUSO E ACCANTONATO' if _ca == 1 else 'NON INCLUSI E ACCANTONATI'})"
            _riep_parts.append(_rp)
        if ctx.get('trattenute') and ctx['trattenute'].get('convivenza'):
            if ctx['trattenute']['convivenza']['totale'] > 0:
                _riep_parts.append(f"Conv.: INCLUSA {p2_fmt(ctx['trattenute']['convivenza']['totale'])}")
            else:
                _riep_parts.append("Conv.: NON INCLUSA")
        if ctx.get('scatti_anzianita'):
            if ctx['scatti_anzianita'].get('dettaglio') and ctx['scatti_anzianita']['dettaglio'] != 'NON INCLUSI':
                _riep_parts.append(f"Scatti: {ctx['scatti_anzianita']['dettaglio']} = {p2_fmt(ctx['scatti_anzianita']['valore'])}")
            else:
                _riep_parts.append("Scatti: NON INCLUSI")
        _riepilogo_line = ' | '.join(_riep_parts)
        dettaglio_html = f'''<div style="margin-top:18pt;">
            <table style="width:100%;border-collapse:collapse;font-size:9pt;">
            <tr><td colspan="7" style="padding:4pt 0;border-bottom:1.5pt solid #2c5282;"><span style="font-size:14pt;font-weight:700;color:#2c5282;">Dettaglio Progetti</span> <span style="font-size:7.5pt;color:#666;float:right;">{ctx['mese_nome']} {ctx['anno']}</span></td></tr>
            </table>
            <table style="width:100%;border-collapse:collapse;font-size:9pt;margin-top:6pt;">
            <tr style="background:#f5f5f5;"><td style="padding:4pt;font-size:7pt;text-transform:uppercase;color:#555;font-weight:700;">Progetto</td>
            <td style="padding:4pt;font-size:7pt;text-transform:uppercase;color:#555;font-weight:700;text-align:right;">Lordo</td>
            <td style="padding:4pt;font-size:7pt;text-transform:uppercase;color:#555;font-weight:700;text-align:right;">Unit\u00e0</td>
            <td style="padding:4pt;font-size:7pt;text-transform:uppercase;color:#555;font-weight:700;text-align:center;">Ore</td>
            <td style="padding:4pt;font-size:7pt;text-transform:uppercase;color:#555;font-weight:700;text-align:right;">Contrib.</td>
            <td style="padding:4pt;font-size:7pt;text-transform:uppercase;color:#555;font-weight:700;text-align:right;">Ratei/Ind.</td>
            <td style="padding:4pt;font-size:7pt;text-transform:uppercase;color:#555;font-weight:700;text-align:right;">Netto</td></tr>
            {p2_rows}
            {p2_totali}
            </table>
            <div style="margin-top:6pt;padding-top:4pt;border-top:0.5pt solid #ddd;font-size:7pt;color:#666;">
            {_riepilogo_line}
            </div>
        </div>'''

    oggi = date.today().strftime('%d/%m/%Y')

    vc = ctx.get('verifica_copertura', 0)
    copertura_ok = abs(vc) < 0.01
    copertura_color = '#34d399' if copertura_ok else ('#f59e0b' if vc > 0 else '#f87171')
    copertura_icon = '\u2713' if copertura_ok else ('\u2191' if vc > 0 else '\u2193')

    tipo_raw = ctx.get('tipo_calcolo', 'CONVIVENTE')
    if tipo_raw == 'CONVIVENTE':
        inizio = 'STANDARD \u2014 '
    else:
        inizio = _tipo_calcolo_label(tipo_raw) + ' - '
    parti = [inizio + ctx['datore'] + ' - ' + ctx['lavoratore']]
    prog = ctx.get('progetti')
    if prog:
        voci = [f"""{p['tipo_nome']} &quot;per&quot; {p['beneficiario_nome']}""" for p in prog]
        parti.append(', '.join(voci))
    subtitle_text = ' - '.join(parti)

    return f'''
    <hr style="border:none;border-top:1.5pt solid #2c5282;margin:6pt 0 8pt 0;"/>
    <div style="font-size:7.5pt;font-weight:600;color:#2c5282;text-align:left;margin-bottom:8px;">{subtitle_text}</div>
    <hr style="border:none;border-top:1.5pt solid #2c5282;margin:0 0 8pt 0;"/>
    <!-- INFO -->
    <table style="width:100%;border-collapse:collapse;font-size:9pt;color:#333;">
    {info_rows}
    </table>

    <hr style="border:none;border-top:1.5pt solid #2c5282;margin:8pt 0;"/>

    <!-- MAIN TWO-COLUMN -->
    <table style="width:100%;border-collapse:collapse;font-size:9pt;">
    <tr><td style="width:48%;vertical-align:top;padding-right:6pt;">
        <span style="font-size:7.5pt;font-weight:700;text-transform:uppercase;color:#34d399;display:block;margin-bottom:4pt;">Retribuzione Lorda</span>
        <table style="width:100%;border-collapse:collapse;font-size:9pt;">
        {lordo_rows}
        </table>
    </td>
    <td style="width:4%;"></td>
    <td style="width:48%;vertical-align:top;padding-left:6pt;">
        <span style="font-size:7.5pt;font-weight:700;text-transform:uppercase;color:#f59e0b;display:block;margin-bottom:4pt;">Contributi</span>
        <table style="width:100%;border-collapse:collapse;font-size:9pt;">
        {contrib_rows}
        </table>
        <div style="margin-top:2pt;text-align:right;font-size:7pt;color:#666;">Stima contributi trimestrali: € {f(ctx['contributi']['trimestrale_stima'])}</div>

        <div style="margin-top:10pt;"><span style="font-size:7.5pt;font-weight:700;text-transform:uppercase;color:#f87171;display:block;margin-bottom:4pt;">Trattenute</span>
        <table style="width:100%;border-collapse:collapse;font-size:9pt;">
        {trat_rows}
        </table></div>

        <div style="margin-top:12pt;">
        <table style="width:100%;border-collapse:collapse;font-size:9pt;">
        <tr><td style="padding:3pt 4pt;font-size:9pt;color:#333;">Budget mensile</td>
            <td style="padding:3pt 4pt;text-align:right;font-size:9pt;font-weight:700;color:#333;">€ {f(ctx['budget_mensile'])}</td></tr>
        <tr><td style="padding:2pt 4pt;font-size:8pt;color:#666;font-style:italic;">Copertura budget {copertura_icon}</td>
            <td style="padding:2pt 4pt;text-align:right;font-size:8pt;font-weight:700;color:{copertura_color};">€ {abs(ctx['verifica_copertura']):.2f}</td></tr>
        {netto_html}
        </table></div>
    </td></tr>
    </table>

    <hr style="border:none;border-top:0.5pt solid #ddd;margin:8pt 0;"/>

    {note_html}
    {patrono_html}

    <!-- FIRMA -->
    <div style="margin-top:10pt;font-size:7.5pt;color:#555;line-height:1.5;">
    Firma del collaboratore familiare <b>{ctx["lavoratore"]}</b> per ricevuta e conferma delle ore lavorate e retribuite e quietanza dell'importo indicato.
    <div style="margin-top:24pt;font-size:7.5pt;color:#555;">Il collaboratore familiare <b>{ctx["lavoratore"]}</b> <u style="display:inline-block;width:360pt;">&nbsp;</u></div>
    </div>

    <hr style="border:none;border-top:0.5pt solid #ddd;margin:8pt 0;"/>

    <!-- DATI STUDIO -->
    <div style="margin-top:4pt;">
    <span style="font-size:7pt;font-weight:700;text-transform:uppercase;color:#555;display:block;">DATI STUDIO</span>
    {logo_html}
    <div style="font-size:7pt;color:#666;">{studio_line}</div>
    </div>

    {alert_html}
    {avv_html}

    <hr style="border:none;border-top:0.5pt solid #555;margin:6pt 0;"/>
    <div style="font-size:7pt;color:#666;text-align:center;">Tutti i diritti riservati: \u00e8 vietata la riproduzione, anche parziale, dei contenuti. | Stampata il {oggi}</div>

    {dettaglio_html}
    '''


# --- _genera_busta_completa_pdf_bytes ---


def _genera_busta_completa_pdf_bytes(contratto, mese, anno, ctx_override=None, tipo_override=None):
    """Genera il PDF busta paga completo.
    Se ctx_override è fornito, lo usa al posto di _calcola_busta_data.
    tipo_override: 'CONVIVENTE', 'NON_CONVIVENTE', 'SOSTITUZIONE'
    Restituisce (pdf_bytes, ctx)."""
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image, PageBreak

    _registra_font_pdf()
    if ctx_override is not None:
        ctx = ctx_override
    else:
        ctx = _calcola_busta_data(contratto, mese, anno)
    if 'errore' in ctx:
        return None, ctx

    # Avviso patrono datore
    MESI_ITA = ['','gennaio','febbraio','marzo','aprile','maggio','giugno',
                'luglio','agosto','settembre','ottobre','novembre','dicembre']
    nome_mese = MESI_ITA[mese]
    comune = getattr(contratto.datore, 'comune', '') or ''
    if comune:
        from paghe.views._helpers import _cerca_comune_per_nome
        info = _cerca_comune_per_nome(comune)
        if info:
            pn = (info.get('patrono_nome', '') or '').strip()
            pd = (info.get('patrono_data', '') or '').strip()
            if pn and pd and nome_mese in pd.lower():
                ctx['avviso_patrono'] = f"Il giorno {pd} ({pn}) \u00e8 festivo per il comune del datore di lavoro."

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=5*mm, bottomMargin=5*mm,
        leftMargin=20*mm, rightMargin=20*mm,
    )

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
    s_netto_label = ParagraphStyle('netlbl', fontSize=11, leading=14, textColor=acciaio, fontName='Roboto-Bold', spaceAfter=0)
    s_netto_val = ParagraphStyle('netval', fontSize=15, leading=18, textColor=acciaio, fontName='Roboto-Bold', spaceAfter=0)
    ParagraphStyle('subt', fontSize=9, leading=12, textColor=acciaio, fontName='Roboto-Bold', spaceAfter=2)
    s_std_sub = ParagraphStyle('stdsub', fontSize=7, leading=9, textColor=acciaio, fontName='Roboto-Bold', spaceAfter=0, alignment=TA_LEFT)
    s_sezione = ParagraphStyle('sez', fontSize=7.5, leading=10, textColor=acciaio, fontName='Roboto-Bold', spaceAfter=0)
    s_extra = ParagraphStyle('extra', fontSize=7, leading=10, textColor=grigio_medio, fontName='Roboto', spaceAfter=1)
    ParagraphStyle('footer', fontSize=7, leading=9, textColor=grigio_footer, fontName='Roboto', alignment=TA_CENTER)

    def _build_subtitle(ctx):
        tipo_raw = ctx.get('tipo_calcolo', 'CONVIVENTE')
        if tipo_raw == 'CONVIVENTE':
            inizio = 'STANDARD \u2014 '
        elif tipo_raw == 'CONVIVENTI_CCNL':
            tipo_orario = ctx.get('tipo_orario_ccnl', 'FT')
            livello = ctx.get('livello_codice', '')
            inizio = f'CONVIVENTI CCNL \u2014 Livello {livello} ({tipo_orario}) \u2014 '
        else:
            inizio = _tipo_calcolo_label(tipo_raw) + ' - '
        parti = [f"{inizio}{ctx['datore']} - {ctx['lavoratore']}"]
        prog = ctx.get('progetti')
        if prog and isinstance(prog, list):
            voci = [f"""{p['tipo_nome']} "per" {p['beneficiario_nome']}""" for p in prog]
            parti.append(', '.join(voci))
        return ' - '.join(parti)

    _titolo_busta = {
        'SOSTITUZIONE': 'BUSTA PAGA \u2014 SOSTITUZIONE MALATTIA',
        'NOTTURNO': 'INDENNIT\u00c0 NOTTURNA',
        'MALATTIA': 'INDENNIT\u00c0 DI MALATTIA',
    }.get(tipo_override, 'BUSTA PAGA')
    story = []
    header_table = Table([
        [Paragraph(_titolo_busta, s_h1),
         Paragraph(f"{ctx['mese_nome']} {ctx['anno']}", ParagraphStyle('h2right', fontSize=16, leading=20, textColor=grigio_scuro, fontName='Roboto-Bold', alignment=TA_RIGHT))]
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
    sub_table = Table([[Paragraph(_build_subtitle(ctx), s_std_sub)]], colWidths=[doc.width])
    sub_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(sub_table)
    # bottom line, same style as header LINEBELOW
    line_table = Table([['']], colWidths=[doc.width])
    line_table.setStyle(TableStyle([('LINEBELOW', (0, 0), (-1, 0), 1.5, acciaio)]))
    story.append(line_table)
    story.append(Spacer(1, 6))

    soglia_testo = f"PIU' DI {ctx['soglia_ore']:.2f} ORE SETTIMANALI" if ctx['sopra_soglia'] else f"MENO DI {ctx['soglia_ore']:.2f} ORE SETTIMANALI"
    sabati_str = '\u2713' * ctx['num_sabati']
    info_data = [
        [Paragraph("DATORE", s_label),
         Paragraph(f"{ctx['datore']} \u2014 {ctx['datore_indirizzo']}{' - '+ctx['datore_comune'] if ctx['datore_comune'] else ''}", s_val),
         Paragraph("LAVORATORE", s_label),
         Paragraph(f"{ctx['lavoratore']} \u2014 {ctx['lavoratore_indirizzo']}{' - '+ctx['lavoratore_comune'] if ctx['lavoratore_comune'] else ''}", s_val)],
        [Paragraph("DATA INIZIO", s_label), Paragraph(ctx['data_assunzione'], s_val),
         Paragraph("TIPO CONTRATTO", s_label), Paragraph(ctx['tipo_contratto'], s_val)],
        [Paragraph("ORE SETTIMANALI", s_label),
         Paragraph(f"{ctx['ore_settimanali']:.2f} h \u2014 {soglia_testo}", s_val),
         Paragraph("SETTIMANE MENSILI", s_label),
         Paragraph(f"{ctx['settimane_mensili']} ({sabati_str})", s_val)],
        [Paragraph("ORE MESE", s_label),
         Paragraph(f"{ctx['ore_mensili']:.2f} h (INPS: {ctx['ore_inps']} h)", s_val),
         Paragraph("LIVELLO", s_label),
         Paragraph(f"{ctx['livello_codice']} \u2014 {ctx['descrizione_corta']}", s_val)],
        [Paragraph("CODICE RAPPORTO", s_label), Paragraph(ctx['codice_rapporto_inps'], s_val),
         Paragraph("PAGA EFF. INPS", s_label),
         Paragraph(f"\u20AC {ctx['paga_effettiva_inps_oraria']:.4f}/h (\u20AC {ctx['paga_effettiva_inps_mensile']:.2f}/mese)", s_val)],
        [Paragraph("PAGA APPLICATA", s_label),
         Paragraph(f"\u20AC {ctx['paga_applicata_oraria']:.4f}/h (\u20AC {ctx['paga_applicata_mensile']:.2f}/mese)", s_val),
         Paragraph("TIPO CALCOLO", s_label),
         Paragraph(_tipo_calcolo_label(ctx.get('tipo_calcolo', 'CONVIVENTE')), s_val)],
    ]
    info_line_rows = [3, 4, 5]
    if ctx.get('progetti') and isinstance(ctx['progetti'], list):
        progetti_lines = [p['nome'] for p in ctx['progetti']]
        if len(progetti_lines) >= 3:
            mid = (len(progetti_lines) + 1) // 2
            col1 = '<br/>'.join(progetti_lines[:mid])
            col2 = '<br/>'.join(progetti_lines[mid:])
            info_data.append([Paragraph("PROGETTI", s_label), Paragraph(col1, s_val_grigio), Paragraph('', s_label), Paragraph(col2, s_val_grigio)])
        else:
            progetti_text = '<br/>'.join(progetti_lines)
            info_data.append([Paragraph("PROGETTI", s_label), Paragraph(progetti_text, s_val_grigio), '', ''])
        info_line_rows.append(len(info_data) - 1)
    last_two_start = len(info_data) - 2
    for i in range(last_two_start, len(info_data)):
        for j in range(4):
            cell = info_data[i][j]
            if isinstance(cell, Paragraph):
                style = cell.style
                if style.fontSize >= 8:
                    info_data[i][j] = Paragraph(cell.text, s_val_grigio)

    t_info = Table(info_data, colWidths=[doc.width*0.20, doc.width*0.30, doc.width*0.20, doc.width*0.30])
    style_cmds = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, grigio_bordo),
        ('LINEBELOW', (0, 1), (-1, 1), 0.5, grigio_bordo),
        ('LINEBELOW', (0, 2), (-1, 2), 0.5, grigio_bordo),
    ]
    for r in info_line_rows:
        style_cmds.append(('LINEBELOW', (0, r), (-1, r), 0.5, grigio_bordo))
    t_info.setStyle(TableStyle(style_cmds))
    story.append(t_info)
    story.append(Spacer(1, 8))

    items_lordo = []
    def row(label, value, small=''):
        l = f"{label} <font size='7' color='#666666'>{small}</font>" if small else label
        return [Paragraph(l, s_item_label),
                Paragraph(f"€ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), s_item_val)]
    def total_row(label, value):
        return [Paragraph(f"<b>{label}</b>", s_total_label),
                Paragraph(f"<b>€ {value:,.2f}</b>".replace(',', 'X').replace('.', ',').replace('X', '.'), s_total_val)]

    items_lordo.append(row("Paga base", ctx['paga_base']['totale'],
                           f"(€ {ctx['paga_base']['orario']:.4f} x {ctx['ore_mensili']:.2f}h)"))
    for ind in ctx['indennita']:
        items_lordo.append(row(ind['label'], ind['totale'],
                                f"(€ {ind['orario']:.4f} x {ctx['ore_mensili']:.2f}h)"))
    items_lordo.append(row("Scatti anzianità", ctx['scatti_anzianita']['valore'],
                           f"({ctx['scatti_anzianita']['dettaglio']})"))
    for rp in ctx['ratei_pagati']:
        if rp.get('incluso'):
            _calc_val_rl = rp['orario'] * ctx['ore_mensili']
            sub = f"(€{rp['orario']:.4f} x {ctx['ore_mensili']:.2f}h = €{_calc_val_rl:.2f})  Incluso nel lordo mensile"
        else:
            sub = "Da corrispondere a fine rapporto" if rp['totale'] > 0 else ""
        items_lordo.append(row(rp['label'] + (" (*)" if rp.get('incluso') else ""), rp['totale'], sub))
    items_lordo.append(row("Indennità e Ratei pagati", round(ctx['totale_indennita'] + ctx['totale_ratei_inclusi'], 4), ""))
    items_lordo.append(total_row("TOTALE LORDO", ctx['totale_lordo']))

    t_lordo = Table(items_lordo, colWidths=[doc.width*0.35, doc.width*0.15])
    t_lordo.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LINEBELOW', (0, 0), (0, len(items_lordo)-3), 0.5, grigio_bordo),
        ('LINEABOVE', (0, len(items_lordo)-1), (1, len(items_lordo)-1), 2, acciaio),
        ('LINEBELOW', (0, len(items_lordo)-1), (1, len(items_lordo)-1), 0.5, grigio_bordo),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('RIGHTPADDING', (1, 0), (1, -1), 0),
    ]))
    col_sx = [Paragraph("RETRIBUZIONE LORDA", s_sezione), Spacer(1, 2), t_lordo]
    t_lordo.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LINEBELOW', (0, 0), (0, len(items_lordo)-2), 0.5, grigio_bordo),
        ('LINEABOVE', (0, len(items_lordo)-1), (1, len(items_lordo)-1), 2, grigio_scuro),
        ('LINEBELOW', (0, len(items_lordo)-1), (1, len(items_lordo)-1), 0.5, grigio_bordo),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('RIGHTPADDING', (1, 0), (1, -1), 0),
    ]))

    def rows_to_table(rows, total_row_idx=-2):
        cw = [doc.width*0.35, doc.width*0.15]
        t = Table(rows, colWidths=cw)
        style = [
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('RIGHTPADDING', (1, 0), (1, -1), 0),
        ]
        if total_row_idx >= 0 and len(rows) >= abs(total_row_idx):
            style.append(('LINEABOVE', (0, total_row_idx), (-1, total_row_idx), 2, grigio_scuro))
            style.append(('LINEBELOW', (0, -1), (-1, -1), 0.5, grigio_bordo))
        t.setStyle(TableStyle(style))
        return t

    qd = ctx['contributi']['inps'].get('quota_datore_totale', 0)
    ql = ctx['contributi']['inps'].get('quota_lavoratore_totale', 0)
    contrib_rows = [
        row("INPS", ctx['contributi']['inps']['totale'],
            f"(€ {ctx['contributi']['inps']['orario']:.4f} x {ctx['ore_inps']}h — {ctx['contributi']['inps']['fascia']} soglia)"),
    ]
    if qd or ql:
        contrib_rows.append(row("  di cui datore", qd, f"(€ {ctx['contributi']['inps'].get('quota_datore_orario', 0):.4f}/h)"))
        contrib_rows.append(row("  di cui lavoratore", ql, f"(€ {ctx['contributi']['inps'].get('quota_lavoratore_orario', 0):.4f}/h)"))
    contrib_rows.append(row(ctx['contributi']['cassa']['nome'] or 'Cassa/Ente', ctx['contributi']['cassa']['totale'],
            f"(€ {ctx['contributi']['cassa']['orario']:.4f} x {ctx['ore_inps']}h)"),)
    contrib_rows.append(['', ''])
    contrib_rows.append(total_row("TOTALE CONTRIBUTI", ctx['contributi']['totale']))
    stima_trimestrale = Paragraph(f"Stima contributi trimestrali: \u20AC {ctx['contributi']['trimestrale_stima']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), ParagraphStyle('stima', fontSize=7, leading=9, textColor=grigio_medio, fontName='Roboto', alignment=TA_RIGHT))

    trattenute_rows = []
    dettaglio_conv_rl = ', '.join(ctx['trattenute']['convivenza']['dettaglio']) if ctx['trattenute']['convivenza']['dettaglio'] else ''
    label_conv_rl = "Vitto e alloggio forfettario" if ctx.get('tipo_calcolo') == 'SOSTITUZIONE' else "Convivenza"
    trattenute_rows.append(row(label_conv_rl, ctx['trattenute']['convivenza']['totale'], f"({dettaglio_conv_rl})" if dettaglio_conv_rl else ""))
    accantonati_nomi_rl = [r['label'] for r in ctx['ratei_pagati'] if not r.get('incluso') and r['totale'] > 0]
    acc_nota_rl = ', '.join(accantonati_nomi_rl) + ' non pagati' if accantonati_nomi_rl else ''
    trattenute_rows.append(row("Ratei accantonati", ctx['trattenute']['ratei_accantonati'],
                              f"({acc_nota_rl})" if acc_nota_rl else ""))
    if ctx['trattenute']['convivenza']['totale'] != 0 or ctx['trattenute']['ratei_accantonati'] != 0:
        trattenute_rows.append(['', ''])
    trattenute_rows.append(total_row("TOTALE TRATTENUTE", ctx['trattenute']['totale']))

    vc_rep = ctx.get('verifica_copertura', 0)
    cop_ok = abs(vc_rep) < 0.01
    cop_col = '#34d399' if cop_ok else ('#f59e0b' if vc_rep > 0 else '#f87171')
    cop_ico = '\u2713' if cop_ok else ('\u2191' if vc_rep > 0 else '\u2193')
    t_riepilogo = Table([
        [Paragraph("Budget mensile", s_item_label),
         Paragraph(f"€ {ctx['budget_mensile']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), ParagraphStyle('zb', fontSize=9, leading=12, fontName='Roboto-Bold', textColor=grigio_scuro))],
        [Paragraph(f"Copertura budget {cop_ico}", ParagraphStyle('cop', fontSize=7.5, leading=10, fontName='Roboto-Italic', textColor=HexColor(cop_col))),
         Paragraph(f"€ {abs(vc_rep):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), ParagraphStyle('copv', fontSize=8, leading=10, fontName='Roboto-Bold', textColor=HexColor(cop_col)))],
        [Paragraph("<b>NETTO IN BUSTA</b>", s_netto_label),
         Paragraph(f"<b>€ {ctx['netto']:,.2f}</b>".replace(',', 'X').replace('.', ',').replace('X', '.'), s_netto_val)],
    ], colWidths=[doc.width*0.35, doc.width*0.15])
    t_riepilogo.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LINEABOVE', (0, 2), (1, 2), 1.5, acciaio),
        ('LINEBELOW', (0, 2), (1, 2), 0.5, grigio_bordo),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('RIGHTPADDING', (1, 0), (1, -1), 0),
    ]))
    col_dx = []
    col_dx.append(Paragraph("CONTRIBUTI", s_sezione))
    col_dx.append(Spacer(1, 2))
    col_dx.append(rows_to_table(contrib_rows, total_row_idx=-2))
    col_dx.append(Spacer(1, 1))
    col_dx.append(stima_trimestrale)
    col_dx.append(Spacer(1, 4))
    col_dx.append(Paragraph("TRATTENUTE", s_sezione))
    col_dx.append(Spacer(1, 1))
    if trattenute_rows:
        col_dx.append(rows_to_table(trattenute_rows, total_row_idx=-2 if ctx['trattenute']['totale'] > 0 else -1))
    col_dx.append(Spacer(1, 6))
    col_dx.append(t_riepilogo)

    layout = Table([[col_sx, col_dx]], colWidths=[doc.width*0.48, doc.width*0.52])
    layout.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (0, 0), 0),
        ('RIGHTPADDING', (1, 0), (1, 0), 0),
        ('LEFTPADDING', (1, 0), (1, 0), 12),
    ]))
    story.append(layout)

    if ctx.get('note_datore'):
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=0.3, color=grigio_bordo, spaceAfter=3))
        story.append(Paragraph("NOTE DATORE", ParagraphStyle('sezsm', fontSize=7, leading=9, textColor=grigio_scuro, fontName='Roboto-Bold', spaceAfter=0)))
        story.append(Spacer(1, 2))
        story.append(Paragraph(_formatta_testo_pdf(ctx['note_datore']), s_extra))
        story.append(Spacer(1, 4))
        story.append(HRFlowable(width="100%", thickness=0.3, color=grigio_bordo, spaceAfter=3))

    if ctx.get('avviso_patrono'):
        story.append(Spacer(1, 6))
        story.append(HRFlowable(width="100%", thickness=0.3, color=HexColor('#c97a0e'), spaceAfter=3))
        story.append(Paragraph(ctx['avviso_patrono'], ParagraphStyle('avviso', fontSize=8, leading=10, textColor=HexColor('#c97a0e'), fontName='Roboto-Bold', spaceAfter=0)))
        story.append(Spacer(1, 4))
        story.append(HRFlowable(width="100%", thickness=0.3, color=HexColor('#c97a0e'), spaceAfter=3))

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        f"Firma del collaboratore familiare <b>{ctx['lavoratore']}</b> per ricevuta e conferma delle ore lavorate "
        f"e retribuite e quietanza dell'importo indicato.",
        ParagraphStyle('firma', fontSize=7, leading=10, textColor=grigio_medio, fontName='Roboto', spaceAfter=0)))
    story.append(Spacer(1, 24))
    story.append(Paragraph(
        f"Il collaboratore familiare <b>{ctx['lavoratore']}</b> "
        f"<u>{'_' * 55}</u>",
        ParagraphStyle('firmariga', fontSize=7, leading=10, textColor=grigio_medio, fontName='Roboto', spaceAfter=0)))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=0.3, color=grigio_bordo, spaceAfter=4))

    story.append(Paragraph("DATI STUDIO", ParagraphStyle('sezsm', fontSize=7, leading=9, textColor=grigio_scuro, fontName='Roboto-Bold', spaceAfter=0)))
    story.append(Spacer(1, 2))
    logo_path = ctx.get('logo_buste_paga_path')
    if logo_path:
        import os
        if os.path.exists(logo_path):
            try:
                logo_img = Image(logo_path, width=120, height=40, hAlign='LEFT')
                story.append(logo_img)
            except Exception:
                logger.warning("Impossibile caricare logo buste: %s", logo_path)
    studio_parts = []
    if ctx.get('dati_studio'):
        studio_parts.append(ctx['dati_studio'])
    if ctx.get('telefono_studio'):
        studio_parts.append(f"Tel: {ctx['telefono_studio']}")
    if ctx.get('email_studio'):
        studio_parts.append(f"Mail: {ctx['email_studio']}")
    if studio_parts:
        story.append(Paragraph(' | '.join(studio_parts), s_extra))

    if ctx.get('alert_contributi_studio'):
        story.append(Spacer(1, 2))
        story.append(HRFlowable(width="100%", thickness=0.3, color=grigio_bordo, spaceAfter=2))
        story.append(Paragraph("SCADENZE", ParagraphStyle('sezsm', fontSize=7, leading=9, textColor=grigio_scuro, fontName='Roboto-Bold', spaceAfter=0)))
        story.append(Spacer(1, 2))
        story.append(Paragraph(_formatta_testo_pdf(ctx['alert_contributi_studio']), s_extra))

    import datetime
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=0.5, color=grigio_scuro, spaceAfter=3))
    story.append(Paragraph(
        "Tutti i diritti riservati: \u00e8 vietata la riproduzione, anche parziale, dei contenuti. "
        f"| Stampata il {datetime.date.today().strftime('%d/%m/%Y')}",
        s_extra
    ))

    if ctx.get('progetti_data'):
        p2 = ctx['progetti_data']
    elif ctx.get('progetti') and isinstance(ctx['progetti'], list):
        p2 = _calcola_progetti_data(ctx, contratto)
    else:
        p2 = None
    if p2 and p2['righe']:
        story.append(PageBreak())
        p2_title = Paragraph("DETTAGLIO PROGETTI", ParagraphStyle('p2title', fontSize=14, leading=17, textColor=grigio_scuro, fontName='Roboto-Bold', spaceAfter=0))
        p2_subtitle = Paragraph(f"{ctx['mese_nome']} {ctx['anno']}", ParagraphStyle('p2sub', fontSize=8, leading=10, textColor=grigio_medio, fontName='Roboto', alignment=TA_RIGHT))
        story.append(Table([[p2_title, p2_subtitle]], colWidths=[doc.width*0.5, doc.width*0.5],
            style=TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('LINEBELOW', (0,0), (-1,-1), 1.5, acciaio),
                ('LEFTPADDING', (0,0), (0,0), 0),
                ('RIGHTPADDING', (1,0), (1,0), 0),
            ])))
        story.append(Spacer(1, 8))
        col_w = [doc.width*0.26, doc.width*0.13, doc.width*0.13, doc.width*0.08, doc.width*0.13, doc.width*0.13, doc.width*0.14]
        s_p2hdr = ParagraphStyle('p2hdr', fontSize=6.5, leading=8, textColor=grigio_scuro, fontName='Roboto-Bold', alignment=TA_CENTER)
        s_p2cell = ParagraphStyle('p2cell', fontSize=7, leading=9, textColor=grigio_scuro, fontName='Roboto', alignment=TA_CENTER)
        s_p2bold = ParagraphStyle('p2bold', fontSize=7, leading=9, textColor=grigio_scuro, fontName='Roboto-Bold', alignment=TA_CENTER)
        s_p2tot = ParagraphStyle('p2tot', fontSize=8, leading=10, textColor=grigio_scuro, fontName='Roboto-Bold', alignment=TA_CENTER)
        s_p2netlbl = ParagraphStyle('p2netlbl', fontSize=10, leading=13, textColor=acciaio, fontName='Roboto-Bold', alignment=TA_RIGHT)
        s_p2netval = ParagraphStyle('p2netval', fontSize=10, leading=13, textColor=acciaio, fontName='Roboto-Bold', alignment=TA_RIGHT)
        def fmt_p2(v):
            return f"\u20AC {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        def p2cell(text, style=s_p2cell):
            return Paragraph(text, style)
        tbl_data = [
            [p2cell("PROGETTO", s_p2hdr), p2cell("LORDO\nPROGETTO", s_p2hdr), p2cell("UNIT\u00c0\n(PAGA/h)", s_p2hdr),
             p2cell("ORE", s_p2hdr), p2cell("CONTRIB.\nTOTALI", s_p2hdr), p2cell("RATEI ED\nINDENN.", s_p2hdr), p2cell("NETTO", s_p2hdr)]
        ]
        for r in p2['righe']:
            tbl_data.append([
                p2cell(r['nome']), p2cell(fmt_p2(r['lordo_progetto'])), p2cell(fmt_p2(r['paga_oraria'])),
                p2cell(str(r['ore'])), p2cell(fmt_p2(r['contrib'])), p2cell(fmt_p2(r['ratei_ind'])),
                Paragraph(fmt_p2(r['netto']), s_p2bold),
            ])
        t = p2['totali']
        tbl_data.append([
            p2cell("TOTALE", s_p2tot), p2cell(fmt_p2(t['lordo_progetto']), s_p2tot), p2cell('', s_p2tot),
            p2cell(str(t['ore']), s_p2tot), p2cell(fmt_p2(t['contrib']), s_p2tot), p2cell(fmt_p2(t['ratei_ind']), s_p2tot),
            p2cell('', s_p2tot),
        ])
        tbl_data.append([
            p2cell('', s_p2tot), p2cell('', s_p2tot), p2cell('', s_p2tot),
            p2cell('', s_p2tot), p2cell('', s_p2tot),
            Paragraph("NETTO", s_p2netlbl), Paragraph(fmt_p2(t['netto']), s_p2netval),
        ])
        p2_table = Table(tbl_data, colWidths=col_w)
        p2_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 2.5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
            ('LEFTPADDING', (0,0), (-1,-1), 2),
            ('RIGHTPADDING', (0,0), (-1,-1), 2),
            ('LINEBELOW', (0,0), (-1,0), 0.5, grigio_bordo),
            ('LINEBELOW', (0,1), (-1,-3), 0.3, grigio_bordo),
            ('LINEABOVE', (0,-3), (-1,-3), 0.5, grigio_bordo),
            ('LINEABOVE', (0,-1), (-1,-1), 1.5, acciaio),
            ('ALIGN', (1,1), (-1,-2), 'RIGHT'),
            ('ALIGN', (3,1), (3,-2), 'CENTER'),
            ('ALIGN', (1,-2), (-1,-2), 'CENTER'),
        ]))
        story.append(p2_table)
        story.append(Spacer(1, 6))
        _riep_parts_rl = []
        if ctx.get('indennita'):
            _ind_items_rl = [f"{i['label']} {fmt_p2(i['totale'])}" for i in ctx['indennita']]
            _riep_parts_rl.append(f"Ind.: {' + '.join(_ind_items_rl)} = {fmt_p2(ctx['totale_indennita'])} ({len(ctx['indennita'])})")
        if ctx.get('ratei_pagati'):
            _ri_incl_rl = 0.0; _ri_acc_rl = 0.0; _ci_rl = 0; _ca_rl = 0
            _il_rl = []; _al_rl = []
            for _r in ctx['ratei_pagati']:
                if _r.get('incluso'):
                    _ci_rl += 1; _ri_incl_rl += _r.get('valore_effettivo', 0) or 0; _il_rl.append(_r['label'])
                else:
                    _ca_rl += 1; _ri_acc_rl += _r.get('valore_effettivo', _r.get('totale', 0)) or 0; _al_rl.append(_r['label'])
            _rp_rl = 'Ratei:'
            if _ci_rl > 0: _rp_rl += f" +{fmt_p2(_ri_incl_rl)} ({','.join(_il_rl)} \u2014 {_ci_rl} INCLUSI)"
            if _ca_rl > 0: _rp_rl += f" +{fmt_p2(_ri_acc_rl)} ({','.join(_al_rl)} \u2014 {_ca_rl} {'NON INCLUSO E ACCANTONATO' if _ca_rl == 1 else 'NON INCLUSI E ACCANTONATI'})"
            _riep_parts_rl.append(_rp_rl)
        if ctx.get('trattenute') and ctx['trattenute'].get('convivenza'):
            if ctx['trattenute']['convivenza']['totale'] > 0:
                _riep_parts_rl.append(f"Conv.: INCLUSA {fmt_p2(ctx['trattenute']['convivenza']['totale'])}")
            else:
                _riep_parts_rl.append("Conv.: NON INCLUSA")
        if ctx.get('scatti_anzianita'):
            if ctx['scatti_anzianita'].get('dettaglio') and ctx['scatti_anzianita']['dettaglio'] != 'NON INCLUSI':
                _riep_parts_rl.append(f"Scatti: {ctx['scatti_anzianita']['dettaglio']} = {fmt_p2(ctx['scatti_anzianita']['valore'])}")
            else:
                _riep_parts_rl.append("Scatti: NON INCLUSI")
        _riepilogo_line_rl = ' | '.join(_riep_parts_rl)
        story.append(HRFlowable(width="100%", thickness=0.3, color=grigio_bordo, spaceAfter=6))
        story.append(Paragraph(_riepilogo_line_rl, ParagraphStyle('p2riep', fontSize=7.5, leading=10, textColor=grigio_medio, fontName='Roboto', spaceAfter=0)))
        story.append(Spacer(1, 6))
        story.append(HRFlowable(width="100%", thickness=0.3, color=grigio_bordo, spaceAfter=4))
        story.append(Paragraph("DATI STUDIO", ParagraphStyle('sezsm', fontSize=7, leading=9, textColor=grigio_scuro, fontName='Roboto-Bold', spaceAfter=0)))
        story.append(Spacer(1, 2))
        logo_path = ctx.get('logo_buste_paga_path')
        if logo_path:
            import os
            if os.path.exists(logo_path):
                try:
                    logo_img = Image(logo_path, width=120, height=40, hAlign='LEFT')
                    story.append(logo_img)
                except Exception:
                    logger.warning("Impossibile caricare logo buste (secondo): %s", logo_path)
        studio_line = ' | '.join(filter(None, [ctx.get('dati_studio'), f"Tel: {ctx.get('telefono_studio')}", f"Mail: {ctx.get('email_studio')}"]))
        if studio_line:
            story.append(Paragraph(studio_line, s_extra))
        story.append(Spacer(1, 4))
        story.append(HRFlowable(width="100%", thickness=0.3, color=grigio_bordo, spaceAfter=4))
        story.append(Paragraph("NOTE AGGIUNTIVE / AVVERTENZE", ParagraphStyle('sezsm', fontSize=7, leading=9, textColor=grigio_scuro, fontName='Roboto-Bold', spaceAfter=0)))
        story.append(Spacer(1, 2))
        note_avv = _formatta_testo_pdf(ctx.get('note_avvertenze')) or "Si attesta la regolarit\u00e0 delle somme erogate e dei contributi INPS trattenuti e versati per il periodo di riferimento. Il datore di lavoro non \u00e8 sostituto d'imposta; il lavoratore \u00e8 tenuto a dichiarare i redditi percepiti se superiori a \u20ac8.500,00 annui, o a verificare la sussistenza dei requisiti per il mantenimento del diritto a carico familiare (reddito non superiore a \u20ac2.840,51, ovvero \u20ac4.000,00 per figli under 24). Si raccomanda di conservare la presente busta paga per eventuali controlli."
        story.append(Paragraph(note_avv, s_extra))
        story.append(Spacer(1, 6))
        story.append(HRFlowable(width="100%", thickness=0.5, color=grigio_scuro, spaceAfter=3))
        story.append(Paragraph(
            "Tutti i diritti riservati: \u00e8 vietata la riproduzione, anche parziale, dei contenuti. "
            f"| Stampata il {datetime.date.today().strftime('%d/%m/%Y')}",
            s_extra
        ))

    doc.build(story)
    pdf = buf.getvalue()
    buf.close()
    return pdf, ctx


# --- _genera_ricevuta_pdf_bytes ---
def _genera_ricevuta_pdf_bytes(busta):
    """Genera il PDF di ricevuta pagamento per una BustaPaga esistente.
    Restituisce (pdf_bytes, nome_file)."""
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.colors import HexColor, white
    from reportlab.lib.enums import TA_RIGHT, TA_CENTER
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

    _registra_font_pdf()
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=15*mm, bottomMargin=10*mm, leftMargin=20*mm, rightMargin=20*mm)
    grigio_scuro = HexColor('#222222')
    grigio_medio = HexColor('#555555')
    grigio_bordo = HexColor('#cccccc')
    acciaio = HexColor('#2c5282')
    HexColor('#dce6f0')
    HexColor('#34d399')

    s_titolo = ParagraphStyle('titolo', fontSize=18, leading=22, textColor=acciaio, fontName='Roboto-Bold', spaceAfter=2, alignment=TA_CENTER)
    s_sottot = ParagraphStyle('sottot', fontSize=9, leading=12, textColor=grigio_medio, fontName='Roboto', spaceAfter=10, alignment=TA_CENTER)
    s_label = ParagraphStyle('label', fontSize=8, leading=10, textColor=grigio_medio, fontName='Roboto', spaceAfter=0)
    s_valore = ParagraphStyle('valore', fontSize=10, leading=13, textColor=grigio_scuro, fontName='Roboto-Bold', spaceAfter=0)
    s_intest = ParagraphStyle('intest', fontSize=8, leading=10, textColor=grigio_medio, fontName='Roboto-Bold', spaceAfter=0)
    s_netto = ParagraphStyle('netto', fontSize=16, leading=20, textColor=acciaio, fontName='Roboto-Bold', spaceAfter=0, alignment=TA_RIGHT)
    s_firma = ParagraphStyle('firma', fontSize=8.5, leading=12, textColor=grigio_scuro, fontName='Roboto', spaceAfter=0)
    s_nota = ParagraphStyle('nota', fontSize=7.5, leading=10, textColor=grigio_medio, fontName='Roboto', spaceAfter=0)
    s_footer = ParagraphStyle('footer', fontSize=7, leading=9, textColor=grigio_medio, fontName='Roboto', spaceAfter=0, alignment=TA_CENTER)

    story = []

    # Intestazione
    story.append(Paragraph("RICEVUTA DI PAGAMENTO", s_titolo))
    datore = busta.contratto.datore
    lavoratore = busta.contratto.lavoratore
    mese_nomi = ['','Gennaio','Febbraio','Marzo','Aprile','Maggio','Giugno','Luglio','Agosto','Settembre','Ottobre','Novembre','Dicembre']
    periodo = f"{mese_nomi[busta.mese]} {busta.anno}"
    story.append(Paragraph(f"{periodo} — {busta.tipo_calcolo}", s_sottot))
    story.append(HRFlowable(width="100%", thickness=1, color=acciaio, spaceAfter=10))

    # Info datore/lavoratore
    info_data = [
        [Paragraph("Datore", s_intest), Paragraph(datore.nome_cognome, s_valore)],
        [Paragraph("Lavoratore", s_intest), Paragraph(lavoratore.nome_cognome, s_valore)],
        [Paragraph("Periodo", s_intest), Paragraph(periodo, s_valore)],
        [Paragraph("Ore mese", s_intest), Paragraph(f"{busta.ore_mensili:.2f}", s_valore)],
        [Paragraph("Stato", s_intest), Paragraph(busta.get_stato_display(), s_valore)],
    ]
    if busta.data_calcolo:
        data_c = busta.data_calcolo.strftime('%d/%m/%Y %H:%M') if hasattr(busta.data_calcolo, 'strftime') else str(busta.data_calcolo)
        info_data.append([Paragraph("Data calcolo", s_intest), Paragraph(data_c, s_valore)])
    t_info = Table(info_data, colWidths=[100, 300])
    t_info.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LINEBELOW', (0,0), (-1,-1), 0.4, grigio_bordo),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 12))

    # Tabella riepilogativa: 4 colonne (voce, importo, voce, importo)
    f_euro = lambda v: f"\u20ac {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    netto_v = float(busta.netto or 0)
    lordo_v = float(busta.totale_lordo or 0)
    contrib_v = float(busta.totale_contributi or 0)
    budget_v = float(busta.budget_mensile or 0)

    riep_data = [
        [Paragraph("DESCRIZIONE", ParagraphStyle('hdr', fontSize=7.5, leading=10, textColor=white, fontName='Roboto-Bold', spaceAfter=0)),
         Paragraph("IMPORTO", ParagraphStyle('hdr', fontSize=7.5, leading=10, textColor=white, fontName='Roboto-Bold', spaceAfter=0, alignment=TA_RIGHT)),
         Paragraph("DESCRIZIONE", ParagraphStyle('hdr', fontSize=7.5, leading=10, textColor=white, fontName='Roboto-Bold', spaceAfter=0)),
         Paragraph("IMPORTO", ParagraphStyle('hdr', fontSize=7.5, leading=10, textColor=white, fontName='Roboto-Bold', spaceAfter=0, alignment=TA_RIGHT))],
        [Paragraph("Retribuzione lorda", s_label), Paragraph(f_euro(lordo_v), s_valore),
         Paragraph("Contributi INPS/Cassa", s_label), Paragraph(f_euro(contrib_v), s_valore)],
        [Paragraph("Ore mensili", s_label), Paragraph(f"{busta.ore_mensili:.2f}", s_valore),
         Paragraph("Paga oraria lorda", s_label), Paragraph(f_euro(float(busta.paga_oraria_lorda or 0)), s_valore)],
    ]
    budget_str = f_euro(budget_v)
    netto_str = f_euro(netto_v)
    riep_data.append([
        Paragraph("Budget mensile", s_label), Paragraph(budget_str, s_valore),
        Paragraph("", s_label), Paragraph("", s_valore),
    ])
    t_riep = Table(riep_data, colWidths=[140, 80, 140, 80])
    t_riep.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('BACKGROUND', (0,0), (-1,0), acciaio),
        ('LINEBELOW', (0,0), (-1,-2), 0.4, grigio_bordo),
    ]))
    story.append(t_riep)
    story.append(Spacer(1, 4))

    # NETTO
    netto_row = [
        [Paragraph("", s_label), Paragraph("", s_valore),
         Paragraph("NETTO IN BUSTA", ParagraphStyle('netlbl', fontSize=10, leading=13, textColor=acciaio, fontName='Roboto-Bold', spaceAfter=0, alignment=TA_RIGHT)),
         Paragraph(netto_str, s_netto)]
    ]
    t_netto = Table(netto_row, colWidths=[140, 80, 140, 80])
    t_netto.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LINEABOVE', (0,0), (-1,-1), 2, acciaio),
        ('LINEBELOW', (0,0), (-1,-1), 2, acciaio),
    ]))
    story.append(t_netto)
    story.append(Spacer(1, 20))

    # Firma
    story.append(HRFlowable(width="60%", thickness=0.5, color=grigio_bordo, spaceAfter=4))
    story.append(Paragraph("Firma del lavoratore per ricevuta e conferma dell'avvenuto pagamento", s_firma))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Firma: _________________________________________", s_firma))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Data: ____/____/________", s_firma))
    story.append(Spacer(1, 16))

    # Dati studio
    opzioni = get_opzioni()
    story.append(HRFlowable(width="100%", thickness=0.3, color=grigio_bordo, spaceAfter=3))
    story.append(Paragraph("DATI STUDIO", ParagraphStyle('sezsm', fontSize=7, leading=9, textColor=grigio_scuro, fontName='Roboto-Bold', spaceAfter=2)))
    righe_studio = []
    if opzioni:
        if opzioni.denominazione_studio:
            righe_studio.append(opzioni.denominazione_studio)
        if opzioni.telefono_studio:
            righe_studio.append(f"Tel: {opzioni.telefono_studio}")
        if opzioni.email_studio:
            righe_studio.append(opzioni.email_studio)
    righe_studio.append(f"Documento generato il {date.today().strftime('%d/%m/%Y')}")
    story.append(Paragraph(" | ".join(righe_studio), s_nota))

    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.3, color=grigio_bordo, spaceAfter=3))
    story.append(Paragraph(
        "Tutti i diritti riservati. La presente ricevuta attesta l'avvenuto pagamento della retribuzione "
        "per il periodo indicato. Conservare per eventuali controlli.",
        s_footer
    ))

    doc.build(story)
    pdf = buf.getvalue()
    buf.close()
    safe_name = busta.contratto.lavoratore.nome_cognome.replace(' ', '_').replace('/', '_')
    nome_file = f"{safe_name}_Ricevuta_{busta.mese:02d}_{busta.anno}.pdf"
    return pdf, nome_file
