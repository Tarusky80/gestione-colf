"""Inquadramento lavoro domestico: HTML + PDF + email."""
import io
from pathlib import Path

from paghe.views._common_imports import *
from paghe.models import DatoreLavoro

logger = logging.getLogger('paghe')

INQUADRAMENTO_DATA = [
    {
        'codice': 'A',
        'nome': 'Livello A',
        'periodi': [
            {
                'validita': 'dal 01/10/2020',
                'descrizione': 'Appartengono a questo livello gli assistenti familiari, non addetti all\'assistenza di persone che svolgono con competenza le proprie mansioni, relative ai profili lavorativi indicati, a livello esecutivo e sotto il diretto controllo del datore di lavoro.',
                'profili': [
                    ('a', 'Addetto alle pulizie. Svolge esclusivamente mansioni relative alla pulizia della casa.'),
                    ('b', 'Addetto alla lavanderia. Svolge esclusivamente mansioni relative alla lavanderia.'),
                    ('c', 'Aiuto di cucina. Svolge esclusivamente mansioni di supporto al cuoco.'),
                    ('d', 'Stalliere. Svolge mansioni di normale pulizia della stalla e di cura generica del/dei cavallo/i.'),
                    ('e', 'Assistente ad animali domestici. Svolge esclusivamente mansioni di assistenza ad animali domestici.'),
                    ('f', 'Addetto alla pulizia ed annaffiatura delle aree verdi.'),
                    ('g', 'Operaio comune. Svolge esclusivamente mansioni manuali, di fatica, sia per le grandi pulizie, sia nell\'ambito di interventi di piccola manutenzione.'),
                ],
            },
            {
                'validita': 'fino al 30/09/2020',
                'descrizione': 'Appartengono a questo livello i collaboratori familiari generici, non addetti all\'assistenza di persone, sprovvisti di esperienza professionale o con esperienza professionale (maturata anche presso datori di lavoro diversi) non superiore a 12 mesi, nonché i lavoratori che, in possesso della necessaria esperienza, svolgono con competenza le proprie mansioni, relative ai profili lavorativi indicati, a livello esecutivo e sotto il diretto controllo del datore di lavoro.',
                'profili': [
                    ('a', 'Collaboratore familiare con meno di 12 mesi di esperienza professionale, non addetto all\'assistenza di persone: Svolge mansioni di pertinenza dei collaboratori familiari, a livello di inserimento al lavoro ed in fase di prima formazione. Al compimento dei dodici mesi di anzianità questo lavoratore sarà inquadrato nel livello B con la qualifica di collaboratore generico polifunzionale.'),
                    ('b', 'Addetto alle pulizie: Svolge esclusivamente mansioni relative alla pulizia della casa.'),
                    ('c', 'Addetto alla lavanderia: Svolge mansioni relative alla lavanderia.'),
                    ('d', 'Aiuto di cucina: Svolge mansioni di supporto al cuoco.'),
                    ('e', 'Stalliere: Svolge mansioni di normale pulizia della stalla e di cura generica del/dei cavallo/i.'),
                    ('f', 'Assistente ad animali domestici: Svolge mansioni di assistenza ad animali domestici.'),
                    ('g', 'Addetto alla pulizia ed annaffiatura delle aree verdi.'),
                    ('h', 'Operaio comune: Svolge mansioni manuali, di fatica, sia per le grandi pulizie, sia nell\'ambito di interventi di piccola manutenzione.'),
                ],
            },
        ],
    },
    {
        'codice': 'AS',
        'nome': 'Livello A Super',
        'periodi': [
            {
                'validita': 'dal 01/10/2020',
                'descrizione': 'Appartengono a questo livello gli assistenti familiari, non addetti all\'assistenza di persone che svolgono con competenza le proprie mansioni, relative ai profili lavorativi indicati, a livello esecutivo e sotto il diretto controllo del datore di lavoro.',
                'profili': [
                    ('a', 'Addetto alla compagnia. Svolge esclusivamente mansioni di mera compagnia a persone adulte autosufficienti, senza effettuare alcuna altra prestazione di lavoro.'),
                ],
            },
            {
                'validita': 'fino al 30/09/2020',
                'descrizione': 'Appartengono a questo livello i collaboratori familiari generici, non addetti all\'assistenza di persone, sprovvisti di esperienza professionale o con esperienza professionale (maturata anche presso datori di lavoro diversi) non superiore a 12 mesi, nonché i lavoratori che, in possesso della necessaria esperienza, svolgono con competenza le proprie mansioni, relative ai profili lavorativi indicati, a livello esecutivo e sotto il diretto controllo del datore di lavoro.',
                'profili': [
                    ('a', 'Addetto alla compagnia: Svolge esclusivamente mansioni di mera compagnia a persone autosufficienti, senza effettuare alcuna prestazione di lavoro.'),
                    ('b', 'Baby sitter: Svolge mansioni occasionali e/o saltuarie di vigilanza di bambini in occasione di assenze dei familiari, con esclusione di qualsiasi prestazione di cura.'),
                ],
            },
        ],
    },
    {
        'codice': 'B',
        'nome': 'Livello B',
        'periodi': [
            {
                'validita': 'dal 01/10/2020',
                'descrizione': 'Appartengono a questo livello gli assistenti familiari che, svolgono con specifica competenza le proprie mansioni, ancorché a livello esecutivo.',
                'profili': [
                    ('a', 'Collaboratore familiare generico polifunzionale. Svolge le plurime incombenze relative al normale andamento della vita familiare, compiendo, promiscuamente, mansioni di pulizia e riassetto della casa, di addetto alla cucina, di addetto alla lavanderia, di assistente ad animali domestici, nonché altri compiti nell\'ambito del livello di appartenenza.'),
                    ('b', 'Custode di abitazione privata. Svolge mansioni di vigilanza dell\'abitazione del datore di lavoro e relative pertinenze, nonché, se fornito di alloggio nella proprietà, di custodia.'),
                    ('c', 'Addetto alla stireria. Svolge mansioni relative alla stiratura.'),
                    ('d', 'Cameriere. Svolge servizio di tavola e di camera.'),
                    ('e', 'Giardiniere. Addetto alla cura delle aree verdi ed ai connessi interventi di manutenzione.'),
                    ('f', 'Operaio qualificato. Svolge mansioni manuali nell\'ambito di interventi, anche complessi, di manutenzione.'),
                    ('g', 'Autista. Svolge mansioni di conduzione di automezzi adibiti al trasporto di persone ed effetti familiari, effettuando anche la relativa ordinaria manutenzione e pulizia.'),
                    ('h', 'Addetto al riassetto camere e servizio di prima colazione anche per persone ospiti del datore di lavoro. Svolge le ordinarie mansioni previste per il collaboratore generico polifunzionale, oltreché occuparsi del rifacimento camere e servizio di tavola della prima colazione per gli ospiti del datore di lavoro.'),
                ],
            },
            {
                'validita': 'fino al 30/09/2020',
                'descrizione': 'Appartengono a questo livello i collaboratori familiari che, in possesso della necessaria esperienza, svolgono con specifica competenza le proprie mansioni, ancorché a livello esecutivo.',
                'profili': [
                    ('a', 'Collaboratore generico polifunzionale: Svolge le incombenze relative al normale andamento della vita familiare, compiendo, anche congiuntamente, mansioni di pulizia e riassetto della casa, di addetto alla cucina, di addetto alla lavanderia, di assistente ad animali domestici, nonché altri compiti nell\'ambito del livello di appartenenza.'),
                    ('b', 'Custode di abitazione privata: Svolge mansioni di vigilanza dell\'abitazione del datore di lavoro e relative pertinenze, nonché, se fornito di alloggio nella proprietà, di custodia.'),
                    ('c', 'Addetto alla stireria: Svolge mansioni relative alla stiratura.'),
                    ('d', 'Cameriere: Svolge servizio di tavola e di camera.'),
                    ('e', 'Giardiniere: Addetto alla cura delle aree verdi ed ai connessi interventi di manutenzione.'),
                    ('f', 'Operaio qualificato: Svolge mansioni manuali nell\'ambito di interventi, anche complessi, di manutenzione.'),
                    ('g', 'Autista: Svolge mansioni di conduzione di automezzi adibiti al trasporto di persone ed effetti familiari, effettuando anche la relativa ordinaria manutenzione e pulizia.'),
                    ('h', 'Addetto al riassetto camere e servizio di prima colazione anche per persone ospiti del datore di lavoro: Svolge le ordinarie mansioni previste per il collaboratore generico polifunzionale, oltreché occuparsi del rifacimento camere e servizio di tavola della prima colazione per gli ospiti del datore di lavoro.'),
                ],
            },
        ],
    },
    {
        'codice': 'BS',
        'nome': 'Livello B Super',
        'periodi': [
            {
                'validita': 'dal 01/10/2020',
                'descrizione': 'Appartengono a questo livello gli assistenti familiari che, svolgono con specifica competenza le proprie mansioni, ancorché a livello esecutivo.',
                'profili': [
                    ('a', 'Assistente familiare che assiste persone autosufficienti, ivi comprese, se richieste, le attività connesse alle esigenze del vitto e della pulizia della casa ove vivono gli assistiti.'),
                    ('b', 'Assistente familiare che assiste bambini (baby sitter), ivi comprese, se richieste, le attività connesse alle esigenze del vitto e della pulizia della casa ove vivono gli assistiti.'),
                ],
            },
            {
                'validita': 'fino al 30/09/2020',
                'descrizione': 'Appartengono a questo livello i collaboratori familiari che, in possesso della necessaria esperienza, svolgono con specifica competenza le proprie mansioni, ancorché a livello esecutivo.',
                'profili': [
                    ('a', 'Assistente a persone autosufficienti: Svolge mansioni di assistenza a persone (anziani o bambini) autosufficienti, ivi comprese, se richieste, le attività connesse alle esigenze del vitto e della pulizia della casa ove vivono gli assistiti.'),
                ],
            },
        ],
    },
    {
        'codice': 'C',
        'nome': 'Livello C',
        'periodi': [
            {
                'validita': 'dal 01/10/2020',
                'descrizione': 'Appartengono a questo livello gli assistenti familiari che, in possesso di specifiche conoscenze di base, sia teoriche che tecniche, relative allo svolgimento dei compiti assegnati, operano con totale autonomia e responsabilità.',
                'profili': [
                    ('a', 'Cuoco. Svolge mansioni di addetto alla preparazione dei pasti ed ai connessi compiti di cucina, nonché di approvvigionamento delle materie prime.'),
                ],
            },
            {
                'validita': 'fino al 30/09/2020',
                'descrizione': 'Appartengono a questo livello i collaboratori familiari che, in possesso di specifiche conoscenze di base, sia teoriche che tecniche, relative allo svolgimento dei compiti assegnati, operano con totale autonomia e responsabilità.',
                'profili': [
                    ('a', 'Cuoco: Svolge mansioni di addetto alla preparazione dei pasti ed ai connessi compiti di cucina, nonché di approvvigionamento delle materie prime.'),
                ],
            },
        ],
    },
    {
        'codice': 'CS',
        'nome': 'Livello C Super',
        'periodi': [
            {
                'validita': 'dal 01/10/2020',
                'descrizione': 'Appartengono a questo livello gli assistenti familiari che, in possesso di specifiche conoscenze di base, sia teoriche che tecniche, relative allo svolgimento dei compiti assegnati, operano con totale autonomia e responsabilità.',
                'profili': [
                    ('a', 'Assistente familiare che assiste persone non autosufficienti (non formato), ivi comprese, se richieste, le attività connesse alle esigenze del vitto e della pulizia della casa ove vivono gli assistiti.'),
                ],
            },
            {
                'validita': 'fino al 30/09/2020',
                'descrizione': 'Appartengono a questo livello i collaboratori familiari che, in possesso di specifiche conoscenze di base, sia teoriche che tecniche, relative allo svolgimento dei compiti assegnati, operano con totale autonomia e responsabilità.',
                'profili': [
                    ('a', 'Assistente a persone non autosufficienti (non formato): Svolge mansioni di assistenza a persone non autosufficienti, ivi comprese, se richieste, le attività connesse alle esigenze del vitto e della pulizia della casa ove vivono gli assistiti.'),
                ],
            },
        ],
    },
    {
        'codice': 'D',
        'nome': 'Livello D',
        'periodi': [
            {
                'validita': 'dal 01/10/2020',
                'descrizione': 'Appartengono a questo livello gli assistenti familiari che, in possesso dei necessari requisiti professionali, ricoprono specifiche posizioni di lavoro caratterizzate da responsabilità, autonomia decisionale e/o coordinamento.',
                'profili': [
                    ('a', 'Amministratore dei beni di famiglia. Svolge mansioni connesse all\'amministrazione del patrimonio familiare.'),
                    ('b', 'Maggiordomo. Svolge mansioni di gestione e di coordinamento relative a tutte le esigenze connesse ai servizi rivolti alla vita familiare.'),
                    ('c', 'Governante. Svolge mansioni di coordinamento relative alle attività di cameriere di camera, di stireria, di lavanderia, di guardaroba e simili.'),
                    ('d', 'Capo cuoco. Svolge mansioni di gestione e di coordinamento relative a tutte le esigenze connesse alla preparazione dei cibi ed, in generale, ai compiti della cucina e della dispensa.'),
                    ('e', 'Capo giardiniere. Svolge mansioni di gestione e di coordinamento relative a tutte le esigenze connesse alla cura delle aree verdi e relativi interventi di manutenzione.'),
                    ('f', 'Istitutore. Svolge mansioni di istruzione e/o educazione dei componenti il nucleo familiare.'),
                ],
            },
            {
                'validita': 'fino al 30/09/2020',
                'descrizione': 'Appartengono a questo livello i collaboratori familiari che, in possesso dei necessari requisiti professionali, ricoprono specifiche posizioni di lavoro caratterizzate da responsabilità, autonomia decisionale e/o coordinamento.',
                'profili': [
                    ('a', 'Amministratore dei beni di famiglia: Svolge mansioni connesse all\'amministrazione del patrimonio familiare.'),
                    ('b', 'Maggiordomo: Svolge mansioni di gestione e di coordinamento relative a tutte le esigenze connesse ai servizi rivolti alla vita familiare.'),
                    ('c', 'Governante: Svolge mansioni di coordinamento relative alle attività di cameriere di camera, di stireria, di lavanderia, di guardaroba e simili.'),
                    ('d', 'Capo cuoco: Svolge mansioni di gestione e di coordinamento relative a tutte le esigenze connesse alla preparazione dei cibi ed, in generale, ai compiti della cucina e della dispensa.'),
                    ('e', 'Capo giardiniere: Svolge mansioni di gestione e di coordinamento relative a tutte le esigenze connesse alla cura delle aree verdi e relativi interventi di manutenzione.'),
                    ('f', 'Istitutore: Svolge mansioni di istruzione e/o educazione dei componenti il nucleo familiare.'),
                ],
            },
        ],
    },
    {
        'codice': 'DS',
        'nome': 'Livello D Super',
        'periodi': [
            {
                'validita': 'dal 01/10/2020',
                'descrizione': 'Appartengono a questo livello gli assistenti familiari che, in possesso dei necessari requisiti professionali, ricoprono specifiche posizioni di lavoro caratterizzate da responsabilità, autonomia decisionale e/o coordinamento.',
                'profili': [
                    ('a', 'Assistente familiare che assiste persone non autosufficienti (formato), ivi comprese, se richieste, le attività connesse alle esigenze del vitto e della pulizia della casa ove vivono gli assistiti.'),
                    ('b', 'Direttore di casa. Svolge mansioni di gestione e di coordinamento relative a tutte le esigenze connesse all\'andamento della casa.'),
                    ('c', 'Assistente familiare educatore formato. Lavoratore che, nell\'ambito di progetti educativi e riabilitativi elaborati da professionisti individuati dal datore di lavoro, attua specifici interventi volti a favorire l\'inserimento o il reinserimento nei rapporti sociali, in autonomia, di persone in condizioni di difficoltà perché affette da disabilità psichica oppure da disturbi dell\'apprendimento o relazionali.'),
                ],
            },
            {
                'validita': 'fino al 30/09/2020',
                'descrizione': 'Appartengono a questo livello i collaboratori familiari che, in possesso dei necessari requisiti professionali, ricoprono specifiche posizioni di lavoro caratterizzate da responsabilità, autonomia decisionale e/o coordinamento.',
                'profili': [
                    ('a', 'Assistente a persone non autosufficienti (formato): Svolge mansioni di assistenza a persone non autosufficienti, ivi comprese, se richieste, le attività connesse alle esigenze del vitto e della pulizia della casa ove vivono gli assistiti.'),
                    ('b', 'Direttore di casa: Svolge mansioni di gestione e di coordinamento relative a tutte le esigenze connesse all\'andamento della casa.'),
                ],
            },
        ],
    },
]

NOTE_INQUADRAMENTO = {
    'dal 01/10/2020': [
        'Il lavoratore addetto allo svolgimento di mansioni promiscue ha diritto all\'inquadramento nel livello corrispondente alle mansioni prevalenti.',
        'Per persona autosufficiente si intende il soggetto in grado di compiere le più importanti attività relative alla cura della propria persona ed alla vita di relazione.',
        'La formazione del personale per l\'assistenza a persona non autosufficiente, laddove prevista per l\'attribuzione della qualifica, si intende conseguita quando il lavoratore sia in possesso di diploma nello specifico campo oggetto della propria mansione, conseguito in Italia o all\'estero, purché equipollente, anche con corsi di formazione aventi la durata minima prevista dalla legislazione regionale e comunque non inferiore a 500 ore.',
        'Ai fini del diritto all\'inquadramento nel livello D Super, è onere del lavoratore comunicare per iscritto al datore di lavoro il conseguimento, anche in corso di rapporto di lavoro, di detto diploma e consegnarne copia.',
        'Le parti firmatarie, in merito al profilo c) "Assistente familiare educatore formato" inquadrato nel livello DS, precisano che per il profilo indicato non si intende la figura professionale dell\'educatore professionale disciplinata dal c.d. "Legge Iori" (art. 1, comma 594 e seguenti, L. n. 205 del 2017).',
    ],
    'fino al 30/09/2020': [
        'Il lavoratore addetto allo svolgimento di mansioni plurime ha diritto all\'inquadramento nel livello corrispondente alle mansioni prevalenti.',
        'Per persona autosufficiente si intende il soggetto in grado di compiere le più importanti attività relative alla cura della propria persona ed alla vita di relazione.',
        'La formazione del personale, laddove prevista per l\'attribuzione della qualifica, si intende conseguita quando il lavoratore sia in possesso di diploma nello specifico campo oggetto della propria mansione, conseguito in Italia o all\'estero, purché equipollente, anche con corsi di formazione aventi la durata minima prevista dalla legislazione regionale e comunque non inferiore a 500 ore.',
    ],
}

# --- Helper font PDF ---

_INQ_ROBOTO_REG = False

def _registra_inq_roboto():
    global _INQ_ROBOTO_REG
    if _INQ_ROBOTO_REG:
        return
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    d = Path(__file__).resolve().parent.parent.parent / 'static' / 'fonts' / 'Roboto'
    for n, f in [('Roboto', 'Roboto-Regular.ttf'), ('Roboto-Bd', 'Roboto-Bold.ttf'), ('Roboto-It', 'Roboto-Italic.ttf'), ('Roboto-BdIt', 'Roboto-BoldItalic.ttf')]:
        fp = d / f
        if fp.exists():
            pdfmetrics.registerFont(TTFont(n, str(fp)))
    _INQ_ROBOTO_REG = True

def _font_inq(bold=False, italic=False):
    if not _INQ_ROBOTO_REG:
        _registra_inq_roboto()
    if bold and italic:
        return 'Roboto-BdIt'
    if bold:
        return 'Roboto-Bd'
    if italic:
        return 'Roboto-It'
    return 'Roboto'


def _build_inquadramento_html():
    html = ''
    for lv in INQUADRAMENTO_DATA:
        html += f'<div class="inq-livello"><h3>{lv["nome"]}</h3>'
        for p in lv['periodi']:
            html += f'<div class="inq-periodo"><span class="inq-validita">Validità {p["validita"]}</span>'
            html += f'<p class="inq-descrizione">{p["descrizione"]}</p>'
            if p['profili']:
                html += '<ol class="inq-profili">'
                for lettera, testo in p['profili']:
                    html += f'<li><strong>{lettera})</strong> {testo}</li>'
                html += '</ol>'
            html += '</div>'
        html += '</div>'
    html += '<div class="inq-note"><h4>Note a verbale</h4>'
    for periodo, note in NOTE_INQUADRAMENTO.items():
        html += f'<p class="inq-validita">Validità {periodo}:</p><ol>'
        for n in note:
            html += f'<li>{n}</li>'
        html += '</ol>'
    html += '</div>'
    return html


def _genera_inquadramento_pdf_bytes(request):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_CENTER
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem

    _registra_inq_roboto()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=18*mm, bottomMargin=18*mm)

    styles = {
        'title': ParagraphStyle('Titolo', fontName=_font_inq(bold=True), fontSize=18, textColor=HexColor('#222'), spaceAfter=6, alignment=TA_CENTER),
        'subtitle': ParagraphStyle('Sottotitolo', fontName=_font_inq(), fontSize=11, textColor=HexColor('#555'), spaceAfter=16, alignment=TA_CENTER),
        'livello': ParagraphStyle('Livello', fontName=_font_inq(bold=True), fontSize=14, textColor=HexColor('#2c5282'), spaceBefore=16, spaceAfter=6),
        'validita': ParagraphStyle('Validita', fontName=_font_inq(italic=True), fontSize=9, textColor=HexColor('#666'), spaceAfter=4),
        'descrizione': ParagraphStyle('Descrizione', fontName=_font_inq(), fontSize=10, textColor=HexColor('#222'), leading=14, spaceAfter=6),
        'profilo': ParagraphStyle('Profilo', fontName=_font_inq(), fontSize=9.5, textColor=HexColor('#333'), leading=13, spaceAfter=2, leftIndent=10),
        'note_title': ParagraphStyle('NoteTitolo', fontName=_font_inq(bold=True), fontSize=13, textColor=HexColor('#2c5282'), spaceBefore=12, spaceAfter=6),
        'note': ParagraphStyle('Nota', fontName=_font_inq(), fontSize=9, textColor=HexColor('#444'), leading=12.5, spaceAfter=3, leftIndent=10),
    }

    elements = []
    elements.append(Paragraph('Inquadramento Lavoro Domestico', styles['title']))
    elements.append(Paragraph('Classificazione del personale secondo il CCNL', styles['subtitle']))
    elements.append(HRFlowColor(HexColor('#2c5282'), thickness=1.5))
    elements.append(Spacer(1, 8))

    for lv in INQUADRAMENTO_DATA:
        elements.append(Paragraph(lv['nome'], styles['livello']))
        for p in lv['periodi']:
            elements.append(Paragraph(f'<i>Validità {p["validita"]}</i>', styles['validita']))
            elements.append(Paragraph(p['descrizione'], styles['descrizione']))
            if p['profili']:
                items = []
                for lettera, testo in p['profili']:
                    items.append(ListItem(Paragraph(f'<b>{lettera})</b> {testo}', styles['profilo']), bulletColor=HexColor('#2c5282')))
                elements.append(ListFlowable(items, bulletType='bullet', start=None, bulletFontSize=6, leftIndent=20))
            elements.append(Spacer(1, 4))

    elements.append(HRFlowColor(HexColor('#2c5282'), thickness=0.8))
    elements.append(Paragraph('Note a verbale', styles['note_title']))
    for periodo, note in NOTE_INQUADRAMENTO.items():
        elements.append(Paragraph(f'<i>Validità {periodo}:</i>', styles['validita']))
        items = []
        for n in note:
            items.append(ListItem(Paragraph(n, styles['note']), bulletColor=HexColor('#2c5282')))
        elements.append(ListFlowable(items, bulletType='bullet', start=None, bulletFontSize=6, leftIndent=20))

    doc.build(elements)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes


def HRFlowColor(color, thickness=0.5):
    from reportlab.platypus.flowables import HRFlowable
    return HRFlowable(width='100%', thickness=thickness, color=color, spaceAfter=6, spaceBefore=2)


# --- View per invio email ---

@login_required
@permesso_richiesto('documenti.vedi')
@require_http_methods(['POST'])
def ajax_inquadramento_invia_email(request):
    import json
    data = json.loads(request.body)
    destinatari = data.get('destinatari', [])
    if not destinatari:
        return JsonResponse({'ok': False, 'errore': 'Nessun destinatario selezionato.'})
    pdf_bytes = _genera_inquadramento_pdf_bytes(request)
    if not pdf_bytes:
        return JsonResponse({'ok': False, 'errore': 'Errore generazione PDF.'})
    from paghe.views._invia_email import invia_documento_email
    risultati = []
    for cf in destinatari:
        try:
            datore = DatoreLavoro.objects.get(pk=cf)
        except DatoreLavoro.DoesNotExist:
            continue
        ok, msg = invia_documento_email(datore, pdf_bytes, 'Inquadramento Lavoro Domestico.pdf', 'Inquadramento Lavoro Domestico')
        risultati.append({'ok': ok, 'cf': cf, 'errore': '' if ok else msg})
    return JsonResponse({'ok': True, 'risultati': risultati})


# --- View lista HTML ---

@login_required
@permesso_richiesto('documenti.vedi')
@xframe_options_exempt
@never_cache
def inquadramento_list(request):
    html_formattato = _build_inquadramento_html()
    datori = DatoreLavoro.objects.filter(email__isnull=False).exclude(email='')
    return render(request, 'paghe/inquadramento.html', {
        'html_formattato': html_formattato,
        'livelli': INQUADRAMENTO_DATA,
        'datori': datori,
    })


# --- View PDF ---

@login_required
@permesso_richiesto('documenti.vedi')
@xframe_options_exempt
@never_cache
def inquadramento_pdf(request):
    pdf_bytes = _genera_inquadramento_pdf_bytes(request)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="Inquadramento_Lavoro_Domestico.pdf"'
    return response
