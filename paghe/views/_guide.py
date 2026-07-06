"""Guide documentali: Assunzione, Decalogo Colloquio, Cessazione. HTML + PDF + email."""
import io
from pathlib import Path
from datetime import date

from paghe.views._common_imports import *
from paghe.models import DatoreLavoro

logger = logging.getLogger('paghe')

# --- Contenuti strutturati delle guide ---

GUIDE_DATA = {
    'assunzione': {
        'title': 'Guida all\'Assunzione',
        'subtitle': 'Check-list completa per assumere un collaboratore domestico in regola',
        'sections': [
            {
                'title': '1. Documenti necessari',
                'items': [
                    'Del lavoratore: documento d\'identità valido, codice fiscale, permesso di soggiorno in corso di validità (per extra-UE), tesserino sanitario.',
                    'Del datore di lavoro: codice fiscale, documento d\'identità, credenziali SPID/CIE/CNS per accesso INPS.',
                    'Dell\'assistito (se diverso dal datore): codice fiscale, certificazione di non autosufficienza o verbale invalidità (per livelli CS/DS).',
                    'Conserva copia di tutta la documentazione per tutto il periodo del rapporto.',
                ],
            },
            {
                'title': '2. Scegli il livello di inquadramento',
                'content': 'Il livello dipende dalle mansioni prevalenti, non dall\'anzianità del lavoratore:',
                'items': [
                    'Livello A: collaboratore generico (pulizie, riassetto casa).',
                    'Livello B: collaboratore con esperienza o specializzazione base.',
                    'Livello BS: baby-sitter (cura bambini).',
                    'Livello CS: assistente a persone non autosufficienti (badante).',
                    'Livello DS: assistente a persone non autosufficienti con formazione specifica.',
                    'Se non sei sicuro, il livello superiore è la scelta più prudente.',
                ],
            },
            {
                'title': '3. Definisci retribuzione, orario e mansioni',
                'content': 'La retribuzione non può essere inferiore ai minimi tabellari del CCNL. Definisci:',
                'items': [
                    'Retribuzione oraria lorda (almeno il minimo CCNL per il livello scelto).',
                    'Orario settimanale: fino a 40 ore per non conviventi, fino a 54 ore per conviventi.',
                    'Distribuzione dell\'orario sui giorni della settimana.',
                    'Mansioni specifiche (es. pulizie, preparazione pasti, assistenza notturna).',
                    'Indennità di vitto e alloggio (per conviventi).',
                    'Eventuale patto di conglobamento (retribuzione tutto-compreso).',
                ],
            },
            {
                'title': '4. Redigi la lettera di assunzione',
                'content': 'L\'art. 6 del CCNL elenca gli elementi obbligatori. La lettera va firmata da entrambe le parti in duplice copia:',
                'items': [
                    'Data di inizio del rapporto.',
                    'Livello di inquadramento.',
                    'Retribuzione concordata.',
                    'Orario di lavoro.',
                    'Mansioni.',
                    'Periodo di prova (se previsto).',
                    'Indennità vitto e alloggio (per conviventi).',
                    'Indirizzo per le comunicazioni.',
                ],
            },
            {
                'title': '5. Comunica l\'assunzione all\'INPS',
                'warning': 'La comunicazione va fatta almeno 24 ore prima dell\'inizio del rapporto, pena sanzioni da €1.500 a €12.000.',
                'items': [
                    'Accedi al Portale dei Pagamenti INPS con SPID/CIE/CNS.',
                    'Seleziona "Lavoro Domestico" → "Comunicazione di assunzione".',
                    'Inserisci i dati del datore e del lavoratore (codice fiscale, dati anagrafici).',
                    'Indica data inizio, orario settimanale, retribuzione, livello.',
                    'Conferma e conserva la ricevuta.',
                    'In alternativa, rivolgiti a un CAF o patronato.',
                ],
            },
            {
                'title': '6. Iscrizione CAS.SA.COLF',
                'content': 'L\'iscrizione alla Cassa Assistenza Sanitaria Colf e Badanti avviene contestualmente all\'assunzione INPS. Il contributo è pari a circa €1,50/ora (fino a 24h) o €1,30/ora (oltre 24h). Il datore paga 2/3, il lavoratore 1/3.',
            },
            {
                'title': '7. Periodo di prova',
                'items': [
                    'Se previsto nella lettera di assunzione, il periodo di prova dura:',
                    '8 giorni lavorativi per livelli A-B.',
                    '30 giorni lavorativi per livelli BS-DS.',
                    'Durante il periodo di prova entrambe le parti possono recedere senza preavviso.',
                    'Se non inserito in lettera, il rapporto si considera confermato da subito.',
                ],
            },
            {
                'title': '8. Adempimenti mensili',
                'items': [
                    'Predisporre e consegnare il prospetto paga (busta paga) ogni mese, entro la fine del mese successivo.',
                    'Il prospetto paga va in duplice copia: una firmata dal datore al lavoratore, una firmata dal lavoratore al datore.',
                    'Pagare la retribuzione entro l\'ultimo giorno del mese (o come concordato).',
                    'Versare i contributi INPS trimestralmente (codice F2) tramite MAV/PagoPA.',
                    'Le scadenze contributive sono: 10 gennaio (IV trim.), 10 aprile (I trim.), 10 luglio (II trim.), 10 ottobre (III trim.).',
                ],
            },
            {
                'title': '9. Conservazione documenti',
                'items': [
                    'Lettera di assunzione firmata da entrambe le parti.',
                    'Ricevuta della comunicazione INPS.',
                    'Cedolini mensili firmati per ricevuta.',
                    'Ricevute PagoPA dei contributi trimestrali.',
                    'Riepilogo annuale delle somme erogate (Certificazione Unica).',
                    'Conserva tutto per almeno 5 anni dalla cessazione del rapporto.',
                ],
            },
        ],
    },
    'decalogo_colloquio': {
        'title': 'Decalogo del Colloquio',
        'subtitle': '10 consigli per scegliere la persona giusta',
        'sections': [
            {
                'title': '1. Prepara la lista delle domande',
                'content': 'Prima del colloquio, prepara un elenco di domande mirate: esperienze pregresse, disponibilità oraria, mansioni specifiche, conoscenze linguistiche. Un colloquio strutturato aiuta a valutare obiettivamente ogni candidato.',
            },
            {
                'title': '2. Verifica i documenti',
                'content': 'Chiedi documento d\'identità valido, codice fiscale e, per cittadini extra-UE, permesso di soggiorno in corso di validità. Verifica che il permesso consenta attività lavorativa subordinata. Non puoi assumere senza regolare permesso.',
                'warning': 'Assumere un lavoratore senza permesso di soggiorno comporta sanzioni penali: arresto da 3 mesi a 1 anno e ammenda fino a 5.000 euro.',
            },
            {
                'title': '3. Valuta formazione ed esperienza',
                'content': 'Chiedi se ha frequentato corsi di formazione (OSS, assistenza anziani, primo soccorso). Le badanti professionali hanno spesso attestati che certificano le competenze. Verifica le esperienze lavorative precedenti e la durata.',
            },
            {
                'title': '4. Richiedi le referenze',
                'content': 'Chiedi i contatti di precedenti datori di lavoro. Una candidata che porta referenze scritte o contatti telefonici ispira più fiducia. Telefona per avere un riscontro diretto su puntualità, affidabilità e qualità del lavoro.',
            },
            {
                'title': '5. Valuta l\'affidabilità',
                'content': 'Osserva puntualità, chiarezza espositiva e coerenza nelle risposte. Chiedi perché ha lasciato il precedente impiego e cosa cerca in una nuova occupazione. L\'affidabilità si valuta anche dal modo in cui si presenta al colloquio.',
            },
            {
                'title': '6. Discuti le mansioni specifiche',
                'content': 'Spiega chiaramente cosa dovrà fare: pulizie, preparazione pasti, igiene della persona, somministrazione farmaci, accompagnamento visite mediche. Verifica che abbia esperienza specifica per le mansioni richieste.',
            },
            {
                'title': '7. Verifica la conoscenza linguistica',
                'content': 'Per assistenza a persone anziane, la comprensione dell\'italiano è fondamentale. Valuta la capacità di comprendere istruzioni mediche, comunicare con i familiari e gestire situazioni di emergenza. Un test pratico può essere utile.',
            },
            {
                'title': '8. Chiarisci orario e condizioni economiche',
                'content': 'Discuti apertamente di orario di lavoro, giorni di riposo, retribuzione, ferie e permessi. Spiega se è prevista convivenza o meno, e in caso di convivenza come sono organizzati vitto e alloggio. La trasparenza evita futuri malintesi.',
            },
            {
                'title': '9. Spiega diritti e doveri',
                'content': 'Illustra i diritti del lavoratore: busta paga, contributi INPS, TFR, ferie, malattia, permessi. Una persona informata sarà più serena e motivata. Ricorda che il lavoro in regola tutela entrambe le parti.',
                'note': 'Puoi stampare questa guida e consegnarla al candidato come sintesi dei principali diritti e doveri.',
            },
            {
                'title': '10. Valuta la compatibilità umana',
                'content': 'Affidare la cura di un familiare a un estraneo è una scelta delicata. Cerca una persona empatica, paziente, con buona comunicazione. Un colloquio informale, simile a una conversazione, aiuta a scoprire il lato umano del candidato.',
            },
        ],
    },
    'cessazione': {
        'title': 'Guida alla Cessazione del Rapporto',
        'subtitle': 'Dimissioni, licenziamento, scadenza, morte del datore — procedure e tempistiche',
        'sections': [
            {
                'title': '1. Tipologie di cessazione',
                'items': [
                    'Dimissioni: decisione del lavoratore di interrompere il rapporto.',
                    'Licenziamento: decisione del datore di lavoro.',
                    'Scadenza del termine: per contratti a tempo determinato.',
                    'Recesso durante il periodo di prova: senza preavviso.',
                    'Risoluzione consensuale: accordo tra le parti.',
                    'Morte del datore di lavoro o del lavoratore: causa di forza maggiore.',
                    'Licenziamento per giusta causa: comportamenti gravi che ledono la fiducia (art. 2119 c.c.).',
                ],
            },
            {
                'title': '2. Preavviso: termini e modalità',
                'content': 'Il preavviso decorre dal giorno successivo alla firma della lettera di cessazione. Ecco i termini previsti dall\'art. 40 del CCNL:',
                'items': [
                    'Rapporti ≥ 25 ore settimanali, fino a 5 anni di anzianità: 15 giorni.',
                    'Rapporti ≥ 25 ore settimanali, oltre 5 anni: 30 giorni.',
                    'Rapporti < 25 ore settimanali, fino a 2 anni di anzianità: 8 giorni.',
                    'Rapporti < 25 ore settimanali, oltre 2 anni: 15 giorni.',
                    'In caso di dimissioni del lavoratore, i termini sono ridotti del 50%.',
                    'Il preavviso può essere lavorato oppure pagato (indennità sostitutiva).',
                    'In caso di licenziamento per giusta causa non è dovuto preavviso.',
                ],
            },
            {
                'title': '3. Comunicazione all\'INPS',
                'warning': 'La comunicazione di cessazione all\'INPS deve essere effettuata tempestivamente, entro 5 giorni dall\'evento.',
                'items': [
                    'Accedi al Portale INPS con SPID/CIE/CNS.',
                    'Seleziona "Cessazione del rapporto di lavoro domestico".',
                    'Indica la data di cessazione e la motivazione (dimissioni, licenziamento, ecc.).',
                    'Stampa e conserva la ricevuta della comunicazione.',
                    'La data di cessazione INPS coincide con il termine della contribuzione.',
                ],
            },
            {
                'title': '4. Spettanze di fine rapporto',
                'content': 'Alla cessazione il lavoratore ha diritto a:',
                'items': [
                    'Trattamento di Fine Rapporto (TFR): calcolato sull\'intero periodo lavorato.',
                    'Ferie non godute: pagamento dei giorni di ferie maturati e non fruiti.',
                    'Tredicesima maturata: rateo dalla data di inizio anno alla cessazione.',
                    'Eventuale indennità sostitutiva del preavviso (se non lavorato).',
                    'Tutte le spettanze vanno liquidate con l\'ultima busta paga.',
                    'Per importi elevati si può concordare una rateizzazione (2-3 rate).',
                ],
            },
            {
                'title': '5. Documenti da consegnare al lavoratore',
                'items': [
                    'Cessazione INPS (ricevuta della comunicazione).',
                    'Ultima busta paga con le spettanze di fine rapporto.',
                    'Ultimo bollettino INPS con data di cessazione.',
                    'Certificazione Unica sostitutiva (dichiarazione somme erogate).',
                    'Tutti i documenti vanno firmati da entrambe le parti per presa visione.',
                ],
            },
            {
                'title': '6. Caso particolare: morte del datore di lavoro',
                'warning': 'Il decesso del datore è una delle situazioni più delicate. Il rapporto di lavoro si estingue automaticamente, ma vanno gestiti diversi adempimenti.',
                'items': [
                    'Il rapporto si estingue per morte del datore (causa di forza maggiore).',
                    'Gli eredi devono comunicare la cessazione all\'INPS entro 5 giorni.',
                    'È dovuta l\'indennità sostitutiva del preavviso al lavoratore.',
                    'Il TFR e le altre spettanze vanno liquidate dagli eredi.',
                    'Se il lavoratore è convivente, va gestita la ricollocazione abitativa.',
                    'Gli eredi devono presentare la denuncia di successione entro 12 mesi.',
                    'Se l\'assistito (non il datore) è deceduto, si valuta la prosecuzione con gli eredi.',
                ],
            },
            {
                'title': '7. Caso particolare: morte del lavoratore',
                'items': [
                    'Il rapporto si estingue automaticamente per morte del lavoratore.',
                    'Il datore deve comunicare la cessazione all\'INPS.',
                    'Il TFR maturato spetta agli eredi del lavoratore.',
                    'Ferie e tredicesima non godute vanno liquidate agli aventi diritto.',
                    'La procedura è più snella rispetto al decesso del datore.',
                ],
            },
            {
                'title': '8. Dimissioni e disoccupazione',
                'content': 'Il lavoratore che si dimette NON ha diritto alla disoccupazione (NASpI). Per accedere alla NASpI serve il licenziamento (anche per scadenza termine o giusta causa). Attenzione: molti lavoratori chiedono di essere licenziati invece di dimettersi proprio per non perdere il diritto alla disoccupazione.',
                'note': 'Le dimissioni della lavoratrice in gravidanza o maternità devono essere convalidate dall\'Ispettorato del Lavoro.',
            },
        ],
    },
}


# --- Helper per font PDF ---

_ROBOTO_GUIDE_REGISTRATO = False

def _registra_roboto_guide():
    global _ROBOTO_GUIDE_REGISTRATO
    if _ROBOTO_GUIDE_REGISTRATO:
        return
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    ROBOTO_DIR = Path(__file__).resolve().parent.parent.parent / 'static' / 'fonts' / 'Roboto'
    for name, fname in [('Roboto', 'Roboto-Regular.ttf'), ('Roboto-Bd', 'Roboto-Bold.ttf'), ('Roboto-It', 'Roboto-Italic.ttf'), ('Roboto-BdIt', 'Roboto-BoldItalic.ttf')]:
        fp = ROBOTO_DIR / fname
        if fp.exists():
            pdfmetrics.registerFont(TTFont(name, str(fp)))
    _ROBOTO_GUIDE_REGISTRATO = True


def _font_guide(bold=False, italic=False):
    global _ROBOTO_GUIDE_REGISTRATO
    if not _ROBOTO_GUIDE_REGISTRATO:
        _registra_roboto_guide()
    if bold and italic:
        return 'Roboto-BdIt'
    if bold:
        return 'Roboto-Bd'
    return 'Roboto'


def _build_guide_html(guide_id):
    guide = GUIDE_DATA[guide_id]
    html = f'<h3>{guide["title"]}</h3>'
    if guide.get('subtitle'):
        html += f'<p style="color:#8A8F98;font-size:14px;margin-bottom:20px;">{guide["subtitle"]}</p>'
    for sec in guide['sections']:
        html += f'<h4>{sec["title"]}</h4>'
        if sec.get('content'):
            html += f'<p>{sec["content"]}</p>'
        if sec.get('items'):
            html += '<ul>'
            for item in sec['items']:
                html += f'<li>{item}</li>'
            html += '</ul>'
        if sec.get('note'):
            html += f'<div class="guide-note"><strong>Nota:</strong> {sec["note"]}</div>'
        if sec.get('warning'):
            html += f'<div class="guide-warning"><strong>Attenzione:</strong> {sec["warning"]}</div>'
    return html


# --- PDF generation ---

def _genera_guida_pdf(guide_id, request):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.lib.enums import TA_CENTER
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
    from reportlab.platypus.flowables import HRFlowable, KeepTogether
    from paghe.views._helpers import _risolvi_globali

    _registra_roboto_guide()
    grigio_scuro = HexColor('#333')
    grigio_medio = HexColor('#666')
    grigio_bordo = HexColor('#ccc')
    HexColor('#fef9e7')
    HexColor('#fdedec')

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=10*mm, bottomMargin=10*mm,
    )

    s_title = ParagraphStyle('title', fontSize=16, leading=20, textColor=grigio_scuro, fontName=_font_guide(bold=True), spaceAfter=2, alignment=TA_CENTER)
    s_sub = ParagraphStyle('sub', fontSize=10, leading=13, textColor=grigio_medio, fontName=_font_guide(), alignment=TA_CENTER, spaceAfter=14)
    s_section = ParagraphStyle('sec', fontSize=12, leading=15, textColor=grigio_scuro, fontName=_font_guide(bold=True), spaceAfter=4, spaceBefore=12)
    s_body = ParagraphStyle('body', fontSize=9.5, leading=13, textColor=grigio_scuro, fontName=_font_guide(), spaceAfter=4)
    s_item = ParagraphStyle('item', fontSize=9.5, leading=13, textColor=grigio_scuro, fontName=_font_guide(), leftIndent=14, spaceAfter=2)
    s_note = ParagraphStyle('note', fontSize=9, leading=12, textColor=HexColor('#7f6000'), fontName=_font_guide(), leftIndent=8, spaceAfter=6)
    s_warning = ParagraphStyle('warn', fontSize=9, leading=12, textColor=HexColor('#b71c1c'), fontName=_font_guide(), leftIndent=8, spaceAfter=6)
    s_footer = ParagraphStyle('footer', fontSize=7, leading=9, textColor=grigio_medio, fontName=_font_guide(), alignment=TA_CENTER)
    s_data = ParagraphStyle('data', fontSize=7.5, leading=10, textColor=grigio_medio, fontName=_font_guide(), alignment=TA_CENTER, spaceAfter=10)

    story = []
    guide = GUIDE_DATA[guide_id]

    story.append(Paragraph(guide['title'], s_title))
    if guide.get('subtitle'):
        story.append(Paragraph(guide['subtitle'], s_sub))
    story.append(Paragraph(f'Documento generato il {date.today().strftime("%d/%m/%Y")}', s_data))
    story.append(HRFlowable(width="100%", thickness=0.5, color=grigio_bordo, spaceBefore=2, spaceAfter=8))

    for sec in guide['sections']:
        elements = []
        elements.append(Paragraph(sec['title'], s_section))
        if sec.get('content'):
            elements.append(Paragraph(sec['content'], s_body))
        if sec.get('items'):
            items_flow = []
            for item in sec['items']:
                items_flow.append(ListItem(Paragraph(item, s_item), bulletColor=grigio_scuro))
            elements.append(ListFlowable(items_flow, bulletType='bullet', bulletFontSize=6, leftIndent=10, bulletOffsetY=-1, start=None))
        if sec.get('note'):
            elements.append(Paragraph(f'<strong>Nota:</strong> {sec["note"]}', s_note))
        if sec.get('warning'):
            elements.append(Paragraph(f'<strong>Attenzione:</strong> {sec["warning"]}', s_warning))
        story.append(KeepTogether(elements) if len(elements) <= 3 else elements)

    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.3, color=grigio_bordo, spaceAfter=4))
    footer_txt = _risolvi_globali('{{FOOTER_DOCUMENTO}}')
    if footer_txt and footer_txt.strip():
        import re as _re
        footer_plain = footer_txt.replace('<br/>', '\n').replace('<br>', '\n').replace('&nbsp;', ' ').replace('&euro;', '\u20ac')
        footer_plain = _re.sub(r'<[^>]+>', '', footer_plain)
        story.append(Paragraph(footer_plain.strip(), s_footer))

    doc.build(story)
    pdf = buf.getvalue()
    buf.close()
    return pdf


# --- Views ---

def _guide_view(guide_id):
    """Factory per le 3 view di una guida."""
    guide = GUIDE_DATA[guide_id]
    slug = guide_id

    @login_required
    @permesso_richiesto('documenti.vedi')
    @never_cache
    def lista(request):
        html_content = _build_guide_html(slug)
        context = {
            'guide': guide,
            'guide_id': slug,
            'html_content': html_content,
            'datori': DatoreLavoro.objects.filter(email__isnull=False).exclude(email='').order_by('nome_cognome'),
        }
        return render(request, f'paghe/guida_{slug}.html', context)

    @login_required
    @permesso_richiesto('documenti.vedi')
    @xframe_options_exempt
    @never_cache
    def pdf(request):
        pdf_bytes = _genera_guida_pdf(slug, request)
        get_opzioni()
        nome_file = f'Guida_{slug.capitalize()}.pdf'
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{nome_file}"'
        return response

    @login_required
    @permesso_richiesto('documenti.vedi')
    @require_http_methods(['POST'])
    def invia_email(request):
        try:
            import json
            data = json.loads(request.body)
            destinatari = data.get('destinatari', [])
            if not destinatari:
                return JsonResponse({'success': False, 'error': 'Nessun destinatario selezionato.'})

            pdf_bytes = _genera_guida_pdf(slug, request)

            opzioni = get_opzioni()
            base_docs = (opzioni.cartella_documenti if opzioni and opzioni.cartella_documenti
                         else os.path.join(settings.MEDIA_ROOT, 'documenti'))
            cartella_guide = os.path.join(base_docs, 'GUIDE')
            os.makedirs(cartella_guide, exist_ok=True)
            nome_file = f'Guida_{slug.capitalize()}.pdf'
            pdf_path = os.path.join(cartella_guide, nome_file)
            with open(pdf_path, 'wb') as f:
                f.write(pdf_bytes)

            from paghe.views._invia_email import _invia_via_smtp, _crea_log, _invia_via_thunderbird
            risultati = []
            for dest in destinatari:
                dest = dest.strip()
                if not dest:
                    continue
                try:
                    if opzioni and opzioni.email_usa_programma_posta:
                        esito = _invia_via_thunderbird(dest, f'{guide["title"]}', f'In allegato la guida: {guide["title"]}', pdf_path)
                    else:
                        esito = _invia_via_smtp(dest, f'{guide["title"]}', f'In allegato la guida: {guide["title"]}', pdf_path, nome_file)
                    _crea_log(esito.get('ok', False), dest, f'GUIDA_{slug.upper()}', None, esito.get('errore'), request)
                    risultati.append({'destinatario': dest, 'ok': esito.get('ok', False), 'errore': esito.get('errore')})
                except Exception as e:
                    logger.exception(f'Errore invio a {dest}')
                    risultati.append({'destinatario': dest, 'ok': False, 'errore': str(e)})
            ok_count = sum(1 for r in risultati if r['ok'])
            return JsonResponse({'success': ok_count > 0, 'ok_count': ok_count, 'totale': len(risultati), 'dettaglio': risultati})
        except Exception as e:
            logger.exception('Errore in invia_email guida')
            return JsonResponse({'success': False, 'error': str(e)})

    return lista, pdf, invia_email


guida_assunzione_list, guida_assunzione_pdf, ajax_guida_assunzione_invia_email = _guide_view('assunzione')
decalogo_colloquio_list, decalogo_colloquio_pdf, ajax_decalogo_colloquio_invia_email = _guide_view('decalogo_colloquio')
guida_cessazione_list, guida_cessazione_pdf, ajax_guida_cessazione_invia_email = _guide_view('cessazione')
