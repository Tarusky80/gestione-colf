"""Modulo _testi - generato automaticamente da views.py"""

import html
from paghe.views._common_imports import *
import logging

logger = logging.getLogger(__name__)

from paghe.views._helpers import _genera_pdf_da_testo, _get_testo_fk, _risolvi_globali




# --- ajax_preview_testo ---
@login_required
def ajax_preview_testo(request):
    if request.method == 'POST':
        oggetto = request.POST.get('oggetto', '')
        corpo = request.POST.get('corpo', '')
        note = request.POST.get('note', '')
    else:
        return JsonResponse({'success': False, 'error': 'POST required'})

    campione = ContrattoLavoro.objects.select_related(
        'datore', 'lavoratore', 'parametri_minimi', 'ente_bilaterale'
    ).first()

    if campione:
        corpo_reso = _risolvi_variabili_testo(corpo, campione)
        oggetto_reso = _risolvi_variabili_testo(oggetto, campione)
        note_rese = _risolvi_variabili_testo(note, campione)
    else:
        corpo_reso = corpo or ''
        oggetto_reso = oggetto or ''
        note_rese = note or ''

    return JsonResponse({
        'success': True,
        'oggetto': oggetto_reso,
        'corpo': corpo_reso,
        'note': note_rese,
    })


# --- ajax_preview_testo_pdf ---
@login_required
def ajax_preview_testo_pdf(request):
    if request.method == 'POST':
        tipo = request.POST.get('tipo', '')
        oggetto = request.POST.get('oggetto', '')
        corpo = request.POST.get('corpo', '')
    else:
        return JsonResponse({'success': False, 'error': 'POST required'})

    campione = ContrattoAttivo.objects.filter(stato='ATTIVO').select_related(
        'datore', 'lavoratore', 'parametri_minimi', 'ente_bilaterale'
    ).first()

    if campione:
        corpo_reso = _risolvi_variabili_testo(corpo, campione)
        oggetto_reso = _risolvi_variabili_testo(oggetto, campione)
    else:
        corpo_reso = corpo or ''
        oggetto_reso = oggetto or ''

    import tempfile, os
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    tmp.close()
    try:
        buf = _genera_pdf_da_testo(tipo, oggetto_reso, corpo_reso, tmp.name)
        if buf is None:
            return JsonResponse({'success': False, 'error': 'Errore generazione PDF'})
        with open(tmp.name, 'rb') as f:
            pdf_data = f.read()
    finally:
        os.unlink(tmp.name)

    response = HttpResponse(pdf_data, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="preview.pdf"'
    return response


# --- _componi_corpo_email ---


def _componi_corpo_email(modello, contratto, opzioni, extra_vars=None):
    """
    Componi corpo e oggetto email unificato.
    - Risolve variabili per-contratto e globali su corpo e oggetto
    - Risolve e appende footer e firma da OpzioniSoftware
    - Se il corpo contiene {{FIRMA_EMAIL}} o {{NOTE_FOOTER_MAIL}},
      li sostituisce; altrimenti append in coda.
    """
    import re as _re
    corpo = modello.corpo_testo or ''
    oggetto = modello.oggetto_titolo or modello.codice or ''

    if contratto:
        corpo = _risolvi_variabili_testo(corpo, contratto, extra_vars=extra_vars)
        oggetto = _risolvi_variabili_testo(oggetto, contratto, extra_vars=extra_vars)

    corpo = _risolvi_globali(corpo)
    oggetto = _risolvi_globali(oggetto)

    footer_txt = _get_testo_fk(opzioni, 'testo_note_footer_mail', contratto=contratto) or ''
    firma_txt = _get_testo_fk(opzioni, 'testo_firma_email', contratto=contratto) or ''

    if footer_txt:
        footer_txt = _risolvi_globali(footer_txt)
    if firma_txt:
        firma_txt = _risolvi_globali(firma_txt)

    if '{{NOTE_FOOTER_MAIL}}' in corpo:
        corpo = corpo.replace('{{NOTE_FOOTER_MAIL}}', footer_txt)
    elif footer_txt:
        corpo += '<br/><br/>' + footer_txt

    if '{{FIRMA_EMAIL}}' in corpo:
        corpo = corpo.replace('{{FIRMA_EMAIL}}', firma_txt)
    elif firma_txt:
        corpo += '<br/><br/>' + firma_txt

    corpo = _re.sub(r'\n{3,}', '\n\n', corpo)
    oggetto = html.unescape(_re.sub(r'<[^>]+>', '', oggetto)).strip()
    return corpo, oggetto


# --- ajax_testo_preimpostato_corpo ---


def ajax_testo_preimpostato_corpo(request, pk):
    from paghe.models import ModelloDocumentale
    if pk == 0:
        templates = list(ModelloDocumentale.objects.values('pk', 'tipo', 'codice', 'oggetto_titolo'))
        return JsonResponse(templates, safe=False)
    try:
        t = ModelloDocumentale.objects.get(pk=pk)
        return JsonResponse({'corpo': _risolvi_globali(t.corpo_testo)})
    except ModelloDocumentale.DoesNotExist:
        return JsonResponse({'corpo': ''}, status=404)


# --- _risolvi_variabili_testo ---


def _risolvi_variabili_testo(corpo_testo, contratto, extra_vars=None, user=None):
    import re
    if not corpo_testo:
        return corpo_testo or ''
    datore = contratto.datore
    lavoratore = contratto.lavoratore
    parametri = contratto.parametri_minimi
    ente = contratto.ente_bilaterale
    progetto = contratto.progetto.first()
    beneficiario = progetto.beneficiario if progetto else None

    vars_map = {}

    if datore:
        vars_map['NOME_DATORE'] = str(datore)
        vars_map['NOME_COGNOME_DATORE'] = datore.nome_cognome
        vars_map['MAIL_DATORE'] = datore.email or '[MAIL_DATORE]'
        vars_map['TELEFONO_DATORE'] = datore.telefono or '[TELEFONO_DATORE]'
        vars_map['CF_DATORE'] = datore.codice_fiscale or '[CF_DATORE]'
        vars_map['INDIRIZZO_DATORE'] = datore.indirizzo or '[INDIRIZZO_DATORE]'
        vars_map['PAESE_DATORE'] = datore.comune or '[PAESE_DATORE]'
        vars_map['PROVINCIA_DATORE'] = datore.provincia or '[PROVINCIA_DATORE]'
        vars_map['CAP_DATORE'] = datore.cap or '[CAP_DATORE]'
        vars_map['NOTE_DATORE'] = datore.note_datore or '[NOTE_DATORE]'
        vars_map['NOME_DATORE_SOLO'] = datore.nome or '[NOME_DATORE_SOLO]'
        vars_map['COGNOME_DATORE_SOLO'] = datore.cognome or '[COGNOME_DATORE_SOLO]'
    else:
        vars_map['NOME_DATORE'] = '[NOME_DATORE]'
        vars_map['NOME_COGNOME_DATORE'] = '[NOME_COGNOME_DATORE]'
        vars_map['MAIL_DATORE'] = '[MAIL_DATORE]'
        vars_map['TELEFONO_DATORE'] = '[TELEFONO_DATORE]'
        vars_map['CF_DATORE'] = '[CF_DATORE]'
        vars_map['INDIRIZZO_DATORE'] = '[INDIRIZZO_DATORE]'
        vars_map['PAESE_DATORE'] = '[PAESE_DATORE]'
        vars_map['PROVINCIA_DATORE'] = '[PROVINCIA_DATORE]'
        vars_map['CAP_DATORE'] = '[CAP_DATORE]'
        vars_map['NOTE_DATORE'] = '[NOTE_DATORE]'
        vars_map['NOME_DATORE_SOLO'] = '[NOME_DATORE_SOLO]'
        vars_map['COGNOME_DATORE_SOLO'] = '[COGNOME_DATORE_SOLO]'

    if lavoratore:
        vars_map['NOME_LAVORATORE'] = str(lavoratore)
        vars_map['NOME_COGNOME_LAVORATORE'] = lavoratore.nome_cognome
        vars_map['CF_LAVORATORE'] = lavoratore.codice_fiscale or '[CF_LAVORATORE]'
        vars_map['INDIRIZZO_LAVORATORE'] = lavoratore.indirizzo or '[INDIRIZZO_LAVORATORE]'
        vars_map['PAESE_LAVORATORE'] = lavoratore.comune or '[PAESE_LAVORATORE]'
        vars_map['EMAIL_LAVORATORE'] = lavoratore.email or '[EMAIL_LAVORATORE]'
        vars_map['TELEFONO_LAVORATORE'] = lavoratore.telefono or '[TELEFONO_LAVORATORE]'
        vars_map['FERIE_PREGRESSE'] = str(lavoratore.ferie_pregresse) if lavoratore.ferie_pregresse else '0'
        vars_map['SCATTI_ANZIANITA_MATURATI'] = str(lavoratore.scatti_anzianita_maturati) if lavoratore.scatti_anzianita_maturati else '0'
        vars_map['NOTE_LAVORATORE'] = lavoratore.note_lavoratore or '[NOTE_LAVORATORE]'
        vars_map['NOME_LAVORATORE_SOLO'] = lavoratore.nome or '[NOME_LAVORATORE_SOLO]'
        vars_map['COGNOME_LAVORATORE_SOLO'] = lavoratore.cognome or '[COGNOME_LAVORATORE_SOLO]'
    else:
        vars_map['NOME_LAVORATORE'] = '[NOME_LAVORATORE]'
        vars_map['NOME_COGNOME_LAVORATORE'] = '[NOME_COGNOME_LAVORATORE]'
        vars_map['CF_LAVORATORE'] = '[CF_LAVORATORE]'
        vars_map['INDIRIZZO_LAVORATORE'] = '[INDIRIZZO_LAVORATORE]'
        vars_map['PAESE_LAVORATORE'] = '[PAESE_LAVORATORE]'
        vars_map['EMAIL_LAVORATORE'] = '[EMAIL_LAVORATORE]'
        vars_map['TELEFONO_LAVORATORE'] = '[TELEFONO_LAVORATORE]'
        vars_map['FERIE_PREGRESSE'] = '0'
        vars_map['SCATTI_ANZIANITA_MATURATI'] = '0'
        vars_map['NOTE_LAVORATORE'] = '[NOTE_LAVORATORE]'
        vars_map['NOME_LAVORATORE_SOLO'] = '[NOME_LAVORATORE_SOLO]'
        vars_map['COGNOME_LAVORATORE_SOLO'] = '[COGNOME_LAVORATORE_SOLO]'

    if beneficiario:
        vars_map['NOME_BENEFICIARIO'] = str(beneficiario)
        vars_map['NOME_COGNOME_BENEFICIARIO'] = beneficiario.nome_cognome
        vars_map['CF_BENEFICIARIO'] = beneficiario.codice_fiscale or '[CF]'
        vars_map['INDIRIZZO_BENEFICIARIO'] = beneficiario.indirizzo or '[INDIRIZZO]'
        vars_map['COMUNE_BENEFICIARIO'] = beneficiario.comune or '[COMUNE]'
        vars_map['EMAIL_BENEFICIARIO'] = beneficiario.email or '[EMAIL_BENEFICIARIO]'
        vars_map['TELEFONO_BENEFICIARIO'] = beneficiario.telefono or '[TELEFONO_BENEFICIARIO]'
        vars_map['NOTE_BENEFICIARIO'] = beneficiario.note_beneficiario or '[NOTE_BENEFICIARIO]'
        vars_map['NOME_BENEFICIARIO_SOLO'] = beneficiario.nome or '[NOME_BENEFICIARIO_SOLO]'
        vars_map['COGNOME_BENEFICIARIO_SOLO'] = beneficiario.cognome or '[COGNOME_BENEFICIARIO_SOLO]'
    else:
        vars_map['NOME_BENEFICIARIO'] = '[NOME_BENEFICIARIO]'
        vars_map['NOME_COGNOME_BENEFICIARIO'] = '[NOME_COGNOME_BENEFICIARIO]'
        vars_map['CF_BENEFICIARIO'] = '[CF_BENEFICIARIO]'
        vars_map['INDIRIZZO_BENEFICIARIO'] = '[INDIRIZZO_BENEFICIARIO]'
        vars_map['COMUNE_BENEFICIARIO'] = '[COMUNE_BENEFICIARIO]'
        vars_map['EMAIL_BENEFICIARIO'] = '[EMAIL_BENEFICIARIO]'
        vars_map['TELEFONO_BENEFICIARIO'] = '[TELEFONO_BENEFICIARIO]'
        vars_map['NOTE_BENEFICIARIO'] = '[NOTE_BENEFICIARIO]'
        vars_map['NOME_BENEFICIARIO_SOLO'] = '[NOME_BENEFICIARIO_SOLO]'
        vars_map['COGNOME_BENEFICIARIO_SOLO'] = '[COGNOME_BENEFICIARIO_SOLO]'

    vars_map['TIPO_CONTRATTO'] = contratto.get_tipo_contratto_display() if hasattr(contratto, 'get_tipo_contratto_display') else str(contratto.tipo_contratto)
    vars_map['DATA_ASSUNZIONE'] = contratto.data_assunzione.strftime('%d/%m/%Y') if contratto.data_assunzione else '[DATA_ASSUNZIONE]'
    vars_map['DATA_FINE'] = progetto.data_fine.strftime('%d/%m/%Y') if progetto and progetto.data_fine else '[DATA_FINE]'
    vars_map['STATO_CONTRATTO'] = contratto.stato if hasattr(contratto, 'stato') else '[STATO_CONTRATTO]'
    vars_map['CAUSALE_CESSAZIONE'] = contratto.causale_cessazione if hasattr(contratto, 'causale_cessazione') and contratto.causale_cessazione else '[CAUSALE_CESSAZIONE]'
    vars_map['DATA_INIZIO_TFR'] = contratto.data_inizio_tfr.strftime('%d/%m/%Y') if hasattr(contratto, 'data_inizio_tfr') and contratto.data_inizio_tfr else '[DATA_INIZIO_TFR]'
    vars_map['GIORNI_MALATTIA_USATI'] = str(contratto.giorni_malattia_usati_anno) if hasattr(contratto, 'giorni_malattia_usati_anno') and contratto.giorni_malattia_usati_anno else '0'
    vars_map['NOTE_CONTRATTO'] = contratto.note_post_it or '[NOTE_CONTRATTO]'
    vars_map['ORE_SETTIMANALI'] = str(contratto.ore_settimanali_calcolate)
    vars_map['ORE_MENSILI'] = str(contratto.ore_mensili_calcolate)
    vars_map['CODICE_RAPPORTO_INPS'] = contratto.codice_rapporto_inps or '[COD_INPS]'

    if progetto:
        vars_map['TIPO_PROGETTO'] = progetto.tipo.nome if progetto.tipo else '[TIPO_PROGETTO]'
        vars_map['DATA_INIZIO_PROGETTO'] = progetto.data_inizio.strftime('%d/%m/%Y') if progetto.data_inizio else '[DATA_INIZIO_PROGETTO]'
        vars_map['MESI_PROGETTO'] = str(progetto.mesi) if hasattr(progetto, 'mesi') and progetto.mesi else '[MESI_PROGETTO]'
        vars_map['BUDGET_ANNUALE'] = f'\u20ac {progetto.budget_annuale:,.2f}' if progetto.budget_annuale else '[BUDGET_ANNUALE]'
        vars_map['BUDGET_MENSILE'] = f'\u20ac {progetto.budget_mensile:,.2f}' if progetto.budget_mensile else '[BUDGET_MENSILE]'
    else:
        vars_map['TIPO_PROGETTO'] = '[TIPO_PROGETTO]'
        vars_map['DATA_INIZIO_PROGETTO'] = '[DATA_INIZIO_PROGETTO]'
        vars_map['MESI_PROGETTO'] = '[MESI_PROGETTO]'
        vars_map['BUDGET_ANNUALE'] = '[BUDGET_ANNUALE]'
        vars_map['BUDGET_MENSILE'] = '[BUDGET_MENSILE]'

    if parametri:
        vars_map['LIVELLO_CCNL'] = parametri.livello.codice if parametri.livello else '[LIVELLO]'
        vars_map['PARAMETRI_MINIMI'] = f"{parametri.livello.codice} - {parametri.descrizione_corta}" if parametri.livello else '[PARAM_CCNL]'
        vars_map['PAGA_BASE'] = f'\u20ac {parametri.paga_base:,.2f}' if parametri.paga_base else '[PAGA_BASE]'
        vars_map['RETRIBUZIONE_SOSTITUZIONE'] = f'\u20ac {parametri.retribuzione_sostituzione:,.2f}' if parametri.retribuzione_sostituzione else '[RETRIBUZIONE_SOSTITUZIONE]'
        vars_map['MINIMO_MENSILE_FT'] = f'\u20ac {parametri.minimo_mensile_ft:,.2f}' if hasattr(parametri, 'minimo_mensile_ft') and parametri.minimo_mensile_ft else '[MINIMO_MENSILE_FT]'
        vars_map['MINIMO_MENSILE_PT'] = f'\u20ac {parametri.minimo_mensile_pt:,.2f}' if hasattr(parametri, 'minimo_mensile_pt') and parametri.minimo_mensile_pt else '[MINIMO_MENSILE_PT]'
        vars_map['ANNO_PARAMETRI_CCNL'] = str(parametri.anno) if hasattr(parametri, 'anno') and parametri.anno else '[ANNO_PARAMETRI_CCNL]'
        vars_map['DESCRIZIONE_LUNGA_CCNL'] = parametri.descrizione_lunga or '[DESCRIZIONE_LUNGA_CCNL]'
    else:
        vars_map['LIVELLO_CCNL'] = '[LIVELLO_CCNL]'
        vars_map['PARAMETRI_MINIMI'] = '[PARAM_CCNL]'
        vars_map['PAGA_BASE'] = '[PAGA_BASE]'
        vars_map['RETRIBUZIONE_SOSTITUZIONE'] = '[RETRIBUZIONE_SOSTITUZIONE]'
        vars_map['MINIMO_MENSILE_FT'] = '[MINIMO_MENSILE_FT]'
        vars_map['MINIMO_MENSILE_PT'] = '[MINIMO_MENSILE_PT]'
        vars_map['ANNO_PARAMETRI_CCNL'] = '[ANNO_PARAMETRI_CCNL]'
        vars_map['DESCRIZIONE_LUNGA_CCNL'] = '[DESCRIZIONE_LUNGA_CCNL]'

    vars_map['ENTE_BILATERALE'] = str(ente) if ente else '[ENTE]'
    vars_map['RETRIBUZIONE_TOTALE'] = f'\u20ac {contratto.budget_di_partenza:,.2f}'

    opzioni_bool = [
        ('APPLICA_SCATTI', 'Applica scatti', contratto.applica_scatti),
        ('PAGA_TFR', 'TFR', contratto.modalita_tfr),
        ('PAGA_13MA', 'Tredicesima', contratto.paga_13ma),
        ('PAGA_FESTIVI', 'Festivi', contratto.paga_festivi),
        ('PAGA_FERIE', 'Ferie', contratto.paga_ferie),
        ('IND_CERTIF_QUALITA', 'Cert. qualit\u00e0', contratto.ind_certificazione_qualita),
        ('IND_PIU_PERSONE_NC', 'Pi\u00f9 persone (NC)', contratto.ind_piu_persone_non_conv),
        ('IND_MINORI_NC', 'Minori <6 (NC)', contratto.ind_minori_non_conv),
        ('IND_PIU_PERSONE_QUAL', 'Pi\u00f9 persone + qualit\u00e0', contratto.ind_piu_persone_qualita),
        ('IND_MINORI_QUAL', 'Minori + qualit\u00e0', contratto.ind_minori_qualita),
        ('IND_PIU_PERSONE_FT', 'Pi\u00f9 persone (FT)', contratto.ind_assistenza_piu_persone_ft),
        ('IND_PIU_PERSONE_PT', 'Pi\u00f9 persone (PT)', contratto.ind_assistenza_piu_persone_pt),
        ('IND_MINORI_FT', 'Minori <6 (FT)', contratto.ind_minori_6_anni_ft),
        ('NOTTURNO_ASSISTENZA', 'Nott. assistenza', contratto.applica_notturno_assistenza),
        ('NOTTURNO_PRESENZA', 'Nott. presenza', contratto.applica_notturno_presenza),
        ('NOTTURNO_BASE', 'Nott. paga base', contratto.applica_notturno_base),
        ('NOTTURNO_20', 'Nott. 20%', contratto.applica_notturno_20),
        ('NOTT_TFR', 'Nott. TFR', contratto.paga_notturno_tfr),
        ('NOTT_13MA', 'Nott. tredicesima', contratto.paga_notturno_13ma),
        ('NOTT_FESTIVI', 'Nott. festivi', contratto.paga_notturno_festivi),
        ('NOTT_FERIE', 'Nott. ferie', contratto.paga_notturno_ferie),
        ('IND_FUNZIONE', 'Ind. funzione', contratto.ind_funzione_conviventi),
        ('CONVIVENTI_FT', 'Conviventi FT', contratto.ind_conviventi_ft_54h),
        ('CONVIVENTI_PT', 'Conviventi PT', contratto.ind_conviventi_pt_30h),
        ('IS_CONVIVENTE', 'Convivente', contratto.is_convivente),
        ('CONVIVENZA', 'Convivente', contratto.is_convivente),
        ('PAGA_PRANZO', 'Pranzo', contratto.paga_pranzo),
        ('PAGA_CENA', 'Cena', contratto.paga_cena),
        ('PAGA_ALLOGGIO', 'Alloggio', contratto.paga_alloggio),
        ('RATEO_TFR', 'Rateo TFR', contratto.modalita_tfr),
        ('RATEO_TREDICESIMA', 'Rateo Tredicesima', contratto.paga_13ma),
        ('RATEO_FESTIVI', 'Rateo Festivi', contratto.paga_festivi),
        ('RATEO_FERIE', 'Rateo Ferie', contratto.paga_ferie),
        ('USA_IND_FUNZIONE_MENSILE', 'Usa ind. funzione mensile', getattr(contratto, 'usa_ind_funzione_mensile', False)),
        ('USA_IND_MINORI_6_MENSILE_FT', 'Usa ind. minori <6 FT mensile', getattr(contratto, 'usa_ind_minori_6_mensile_ft', False)),
        ('USA_IND_MINORI_6_MENSILE_PT', 'Usa ind. minori <6 PT mensile', getattr(contratto, 'usa_ind_minori_6_mensile_pt', False)),
        ('USA_IND_PIU_ASSISTITI_MENSILE', 'Usa ind. pi\u00f9 assistiti mensile', getattr(contratto, 'usa_ind_piu_assistiti_mensile', False)),
        ('USA_IND_CERT_QUALITA_MENSILE', 'Usa ind. cert. qualit\u00e0 mensile', getattr(contratto, 'usa_ind_cert_qualita_mensile', False)),
        ('USA_RETRIBUZIONE_SOSTITUZIONE', 'Usa retrib. sostituzione', getattr(contratto, 'usa_retribuzione_sostituzione', False)),
    ]
    opzioni_attive = []
    for key, label, valore in opzioni_bool:
        if key.startswith('RATEO_'):
            vars_map[key] = 'INCLUSO' if valore else 'NON INCLUSO'
        elif key == 'CONVIVENZA':
            vars_map[key] = "PRESTERA'" if valore else "NON PRESTERA'"
        else:
            vars_map[key] = 'S\u00ec' if valore else 'No'
        if valore:
            opzioni_attive.append(label)
    vars_map['OPZIONI_ATTIVE'] = ', '.join(opzioni_attive) if opzioni_attive else '[NESSUNA]'
    vars_map['RATEO_13MA'] = vars_map.get('RATEO_TREDICESIMA', 'NON INCLUSO')

    oggi = date.today()
    vars_map['DATA_ODIERNA'] = oggi.strftime('%d/%m/%Y')
    vars_map['DATA_ODIERNA_COMPLETA'] = oggi.strftime('%d/%m/%Y %H:%M:%S')
    vars_map['GIORNO_CORRENTE'] = oggi.strftime('%d')
    vars_map['MESE_CORRENTE'] = MESI_IT[oggi.month]
    mese_prec = oggi.month - 1 if oggi.month > 1 else 12
    vars_map['MESE_PRECEDENTE'] = MESI_IT[mese_prec]
    mese_succ = oggi.month + 1 if oggi.month < 12 else 1
    vars_map['MESE_SUCCESSIVO'] = MESI_IT[mese_succ]
    vars_map['ANNO_IN_CORSO'] = str(oggi.year)
    import time as _time
    vars_map['ORA_CORRENTE'] = oggi.strftime('%H:%M:%S')
    vars_map['TIMESTAMP_UNIX'] = str(int(_time.time()))
    _GIORNI = ['Luned\u00ec', 'Marted\u00ec', 'Mercoled\u00ec', 'Gioved\u00ec', 'Venerd\u00ec', 'Sabato', 'Domenica']
    _GIORNI_3 = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
    vars_map['GIORNO_SETTIMANA'] = _GIORNI[oggi.weekday()]
    vars_map['GIORNO_SETTIMANA_3'] = _GIORNI_3[oggi.weekday()]
    vars_map['NUMERO_SETTIMANA_ISO'] = str(oggi.isocalendar()[1])
    vars_map['MESE_CORRENTE_NUMERO'] = f'{oggi.month:02d}'
    vars_map['TRIMESTRE_CORRENTE'] = str((oggi.month - 1) // 3 + 1)
    vars_map['ANNO_CORRENTE_2'] = str(oggi.year)[-2:]
    vars_map['DATA_ODIERNA_DB'] = oggi.strftime('%Y-%m-%d')
    vars_map['DATA_ODIERNA_LONG'] = oggi.strftime(f'%d {MESI_IT[oggi.month]} %Y')
    vars_map['ORA_CORRENTE_COMPLETA'] = oggi.strftime('%H:%M:%S')
    vars_map['INVIO_DIGITALE'] = 'S\u00ec' if getattr(datore, 'invio_digitale_documenti', False) else 'No'

    vars_map['LINEA'] = '<hr style="border:none;border-top:1px solid #5C5F66;margin:4px 0;">'
    vars_map['HR'] = vars_map['LINEA']
    vars_map['RIGA_VUOTA'] = '<br>'
    vars_map['CAMBIA_PAGINA'] = '<div style="page-break-before: always;"></div>'
    vars_map['INIZIO_PAGINA'] = '<div style="page-break-before: always;">'
    vars_map['STOP_INIZIO_PAGINA'] = '</div>'
    vars_map['FINE_PAGINA'] = '<div id="pdfFooterBlock">'
    vars_map['STOP_FINE_PAGINA'] = '</div>'

    opzioni = get_opzioni()
    _logo_data = {}
    if opzioni:
        vars_map['NOME_SOFTWARE'] = opzioni.nome_programma
        vars_map['NOME_STUDIO'] = getattr(opzioni, 'nome_studio', None) or opzioni.nome_programma
        vars_map['DENOMINAZIONE_STUDIO'] = opzioni.denominazione_studio or '[DENOMINAZIONE_STUDIO]'
        vars_map['TELEFONO_STUDIO'] = opzioni.telefono_studio or '[TELEFONO_STUDIO]'
        vars_map['EMAIL_STUDIO'] = opzioni.email_studio or '[EMAIL_STUDIO]'
        vars_map['IBAN_STUDIO'] = getattr(opzioni, 'iban_studio', '') or '[IBAN_STUDIO]'
        vars_map['INTESTATARIO_IBAN'] = getattr(opzioni, 'intestatario_iban', '') or '[INTESTATARIO_IBAN]'
        vars_map['BANCA_IBAN'] = getattr(opzioni, 'banca_iban', '') or '[BANCA_IBAN]'
        _ind = opzioni.dati_studio.strip() if opzioni.dati_studio else ''
        vars_map['DATI_STUDIO'] = _ind
        vars_map['INDIRIZZO_STUDIO'] = _ind
        _comune = opzioni.comune_studio.strip() if opzioni.comune_studio else ''
        _cap = opzioni.cap_studio.strip() if opzioni.cap_studio else ''
        if _comune or _cap:
            vars_map['INDIRIZZO_STUDIO_COMPLETO'] = f"{_ind}, {_comune} ({_cap})" if _comune and _cap else f"{_ind} {_comune}{_cap}".strip()
        else:
            vars_map['INDIRIZZO_STUDIO_COMPLETO'] = _ind
        vars_map['COMUNE_STUDIO'] = _comune or '[COMUNE_STUDIO]'
        vars_map['CAP_STUDIO'] = _cap or '[CAP_STUDIO]'
        vars_map['VERSIONE_SOFTWARE'] = opzioni.versione_programma or ''
        vars_map['SOGLIA_ORE_CONTRIBUTI'] = str(opzioni.soglia_ore_contributi) if opzioni.soglia_ore_contributi else '[SOGLIA_ORE_CONTRIBUTI]'
        vars_map['RATEO_FERIE_MENSILE'] = str(opzioni.rateo_ferie_mensile) if opzioni.rateo_ferie_mensile else '[RATEO_FERIE_MENSILE]'
        vars_map['ANNO_GESTIONE'] = str(opzioni.anno_gestione) if opzioni.anno_gestione else '[ANNO_GESTIONE]'
        vars_map['MESI_ANNUALI_STD'] = str(opzioni.mesi_annuali_std) if opzioni.mesi_annuali_std else '[MESI_ANNUALI_STD]'
        vars_map['GIORNI_MENSILI_STD'] = str(opzioni.giorni_mensili_std) if opzioni.giorni_mensili_std else '[GIORNI_MENSILI_STD]'
        vars_map['SETTIMANE_ANNUALI_STD'] = str(opzioni.settimane_annuali_std) if opzioni.settimane_annuali_std else '[SETTIMANE_ANNUALI_STD]'
        _footer_tpl = opzioni.testo_note_footer_mail
        vars_map['NOTE_FOOTER_MAIL'] = _footer_tpl.corpo_testo if _footer_tpl else ''
        _firma_tpl = opzioni.testo_firma_email
        vars_map['FIRMA_EMAIL'] = _firma_tpl.corpo_testo if _firma_tpl else ''
        vars_map['ALERT_CONTRIBUTI'] = opzioni.testo_alert_contributi.corpo_testo if opzioni.testo_alert_contributi else ''
        vars_map['TESTO_NOTE_AVVERTENZE'] = opzioni.testo_note_avvertenze.corpo_testo if opzioni.testo_note_avvertenze else ''

        for logo_key, logo_field in [('LOGO_PROGRAMMA', 'logo'), ('LOGO_BUSTE_PAGA', 'logo_buste_paga')]:
            try:
                img_field = getattr(opzioni, logo_field, None)
                if img_field and hasattr(img_field, 'path') and img_field.path:
                    from PIL import Image
                    with Image.open(img_field.path) as pil_img:
                        _ow, _oh = pil_img.size
                    with open(img_field.path, 'rb') as f:
                        import base64
                        img_b64 = base64.b64encode(f.read()).decode('utf-8')
                    ext = img_field.path.rsplit('.', 1)[-1].lower() if '.' in img_field.path else 'png'
                    if ext == 'jpg': ext = 'jpeg'
                    _logo_data[logo_key] = {'uri': f'data:image/{ext};base64,{img_b64}', 'w': _ow, 'h': _oh}
                    vars_map[logo_key] = f'<img src="{_logo_data[logo_key]["uri"]}" width="110" style="max-width:110px;height:auto;">'
                else:
                    _logo_data[logo_key] = None
                    vars_map[logo_key] = ''
            except Exception:
                logger.exception("Errore in _risolvi_variabili_testo")
                _logo_data[logo_key] = None
                vars_map[logo_key] = ''

    _logo_keys = {'LOGO_PROGRAMMA', 'LOGO_BUSTE_PAGA'}
    def _replacer_pct(m, lookup):
        _name = m.group(1)
        _pct = m.group(2)
        if _name in _logo_keys and _logo_data.get(_name) and _pct is not None:
            _ratio = int(_pct) / 100.0
            _nw = int(_logo_data[_name]['w'] * _ratio)
            _nh = int(_logo_data[_name]['h'] * _ratio)
            return f'<img src="{_logo_data[_name]["uri"]}" width="{_nw}" height="{_nh}" style="max-width:{_nw}px;height:auto;">'
        return lookup.get(_name, m.group(0))

    # Risoluzione template annidati TOP_DOCUMENTO e FOOTER_DOCUMENTO
    import re as _re2
    from paghe.models import ModelloDocumentale as _ModelloDocumentale
    for _var_key in ('TOP_DOCUMENTO', 'FOOTER_DOCUMENTO'):
        _safe_content = ''
        try:
            _tpl = _ModelloDocumentale.objects.filter(tipo=_var_key).first()
            if _tpl and _tpl.corpo_testo:
                _safe_content = _tpl.corpo_testo.replace('{{' + _var_key + '}}', '')
                _resolved = _re2.sub(r'\{\{(\w+)(?:,\s*(\d+))?\}\}', lambda m: _replacer_pct(m, vars_map), _safe_content)
                vars_map[_var_key] = _resolved
            else:
                vars_map[_var_key] = ''
        except Exception:
            logger.exception("Errore risoluzione template annidato %s", _var_key)
            vars_map[_var_key] = ''

    # Variabili calcolate (contributi, ore INPS, paga oraria)
    try:
        ore_inps = __import__('math').ceil(float(contratto.ore_mensili_calcolate))
    except Exception:
        logger.exception("Errore calcolo ore INPS da contratto")
        ore_inps = 0
    vars_map['ORE_INPS'] = str(ore_inps)
    try:
        _busta_rec = contratto.buste.order_by('-anno', '-mese').first()
        m_contrib = float(_busta_rec.totale_contributi) if _busta_rec and _busta_rec.totale_contributi else 0.0
    except Exception:
        logger.exception("Errore calcolo contributi mensili da contratto")
        m_contrib = 0.0
    vars_map['CONTRIBUTI_MENSILI'] = f'\u20ac {m_contrib:.4f}'
    vars_map['CONTRIBUTI_TRIMESTRALI'] = f'\u20ac {m_contrib * 3:.4f}'
    vars_map['CONTRIBUTI_ANNUALI'] = f'\u20ac {m_contrib * 12:.4f}'
    try:
        ore_m = float(contratto.ore_mensili_calcolate)
        bdp = float(contratto.budget_di_partenza)
        paga_oraria = bdp / ore_m if ore_m > 0 else 0
    except Exception:
        logger.exception("Errore calcolo paga oraria da budget/ore")
        paga_oraria = 0.0
    vars_map['PAGA_ORARIA'] = f'\u20ac {paga_oraria:.4f}/h'

    # --- Variabili Busta Paga (ultima busta del contratto) ---
    try:
        _busta = contratto.buste.order_by('-anno', '-mese').first()
    except Exception:
        logger.exception("Errore recupero ultima busta paga contratto")
        _busta = None
    if _busta:
        vars_map['MESE_BUSTA'] = str(_busta.mese)
        vars_map['ANNO_BUSTA'] = str(_busta.anno)
        vars_map['STATO_BUSTA'] = _busta.stato or '[STATO_BUSTA]'
        vars_map['TIPO_CALCOLO_BUSTA'] = _busta.tipo_calcolo or '[TIPO_CALCOLO_BUSTA]'
        vars_map['DATA_CALCOLO_BUSTA'] = _busta.data_calcolo.strftime('%d/%m/%Y %H:%M') if _busta.data_calcolo else '[DATA_CALCOLO_BUSTA]'
        vars_map['PAGA_BASE_TOTALE'] = f'\u20ac {_busta.paga_base_totale:,.2f}' if _busta.paga_base_totale else '[PAGA_BASE_TOTALE]'
        vars_map['TOTALE_INDENNITA'] = f'\u20ac {_busta.totale_indennita:,.2f}' if _busta.totale_indennita else '[TOTALE_INDENNITA]'
        vars_map['SCATTI_TOTALI'] = f'\u20ac {_busta.scatti_totale:,.2f}' if _busta.scatti_totale else '[SCATTI_TOTALI]'
        vars_map['TOTALE_LORDO'] = f'\u20ac {_busta.totale_lordo:,.2f}' if _busta.totale_lordo else '[TOTALE_LORDO]'
        vars_map['NETTO_BUSTA'] = f'\u20ac {_busta.netto:,.2f}' if _busta.netto else '[NETTO_BUSTA]'
        vars_map['NETTO_MENSILE'] = vars_map['NETTO_BUSTA']
        vars_map['NETTO_MENSILE_NUM'] = str(_busta.netto) if _busta.netto else '0'
        vars_map['ORE_LAVORATE_MENSILI'] = str(_busta.ore_mensili) if _busta.ore_mensili else '[ORE_LAVORATE_MENSILI]'
        vars_map['PAGA_ORARIA_LORDA'] = f'\u20ac {_busta.paga_oraria_lorda:,.4f}' if _busta.paga_oraria_lorda else '[PAGA_ORARIA_LORDA]'
        vars_map['CONTRIBUTI_INPS_TOTALE'] = f'\u20ac {_busta.contributi_inps_totale:,.2f}' if _busta.contributi_inps_totale else '[CONTRIBUTI_INPS_TOTALE]'
        vars_map['CONTRIBUTI_CASSA_TOTALE'] = f'\u20ac {_busta.contributi_cassa_totale:,.2f}' if _busta.contributi_cassa_totale else '[CONTRIBUTI_CASSA_TOTALE]'
        vars_map['CONTRIBUTI_CASSA_NOME'] = _busta.contributi_cassa_nome or '[CONTRIBUTI_CASSA_NOME]'
        vars_map['TOTALE_CONTRIBUTI_BUSTA'] = f'\u20ac {_busta.totale_contributi:,.2f}' if _busta.totale_contributi else '[TOTALE_CONTRIBUTI_BUSTA]'
        vars_map['CONVIVENZA_TOTALE_BUSTA'] = f'\u20ac {_busta.convivenza_totale:,.2f}' if _busta.convivenza_totale else '[CONVIVENZA_TOTALE_BUSTA]'
        vars_map['TOTALE_ACCANTONATI_BUSTA'] = f'\u20ac {_busta.totale_accantonati:,.2f}' if _busta.totale_accantonati else '[TOTALE_ACCANTONATI_BUSTA]'
        vars_map['BUDGET_MENSILE_BUSTA'] = f'\u20ac {_busta.budget_mensile:,.2f}' if _busta.budget_mensile else '[BUDGET_MENSILE_BUSTA]'
    else:
        for _k in ['MESE_BUSTA','ANNO_BUSTA','STATO_BUSTA','TIPO_CALCOLO_BUSTA','DATA_CALCOLO_BUSTA',
                   'PAGA_BASE_TOTALE','TOTALE_INDENNITA','SCATTI_TOTALI','TOTALE_LORDO','NETTO_BUSTA',
                   'NETTO_MENSILE','NETTO_MENSILE_NUM','ORE_LAVORATE_MENSILI','PAGA_ORARIA_LORDA',
                   'CONTRIBUTI_INPS_TOTALE','CONTRIBUTI_CASSA_TOTALE','CONTRIBUTI_CASSA_NOME',
                   'TOTALE_CONTRIBUTI_BUSTA','CONVIVENZA_TOTALE_BUSTA','TOTALE_ACCANTONATI_BUSTA',
                   'BUDGET_MENSILE_BUSTA']:
            vars_map[_k] = f'[{_k}]'

    # --- Variabili CU Annuale (ultima CU del contratto) ---
    try:
        _cu = contratto.cu_annuali.order_by('-anno').first()
    except Exception:
        logger.exception("Errore recupero ultima CU annuale contratto")
        _cu = None
    if _cu:
        vars_map['ANNO_CU'] = str(_cu.anno)
        vars_map['MODALITA_CU'] = _cu.modalita or '[MODALITA_CU]'
        vars_map['REDDITO_LORDO_CU'] = f'\u20ac {_cu.reddito_lordo:,.2f}' if _cu.reddito_lordo else '[REDDITO_LORDO_CU]'
        vars_map['CONTRIBUTI_INPS_CU'] = f'\u20ac {_cu.contributi_inps_lav:,.2f}' if _cu.contributi_inps_lav else '[CONTRIBUTI_INPS_CU]'
        vars_map['CONTRIBUTI_CASSA_CU'] = f'\u20ac {_cu.contributi_cassa:,.2f}' if _cu.contributi_cassa else '[CONTRIBUTI_CASSA_CU]'
        vars_map['CONTRIBUTI_TOTALI_CU'] = f'\u20ac {_cu.contributi_totali:,.2f}' if _cu.contributi_totali else '[CONTRIBUTI_TOTALI_CU]'
        vars_map['NETTO_CORRISPOSTO_CU'] = f'\u20ac {_cu.netto_corrisposto:,.2f}' if _cu.netto_corrisposto else '[NETTO_CORRISPOSTO_CU]'
        vars_map['TFR_ACCANTONATO_CU'] = f'\u20ac {_cu.tfr_accantonato:,.2f}' if _cu.tfr_accantonato else '[TFR_ACCANTONATO_CU]'
        vars_map['INDENNITA_CONVIVENZA_CU'] = f'\u20ac {_cu.indennita_convivenza:,.2f}' if _cu.indennita_convivenza else '[INDENNITA_CONVIVENZA_CU]'
        vars_map['IMPONIBILE_FISCALE_CU'] = f'\u20ac {_cu.imponibile_fiscale:,.2f}' if _cu.imponibile_fiscale else '[IMPONIBILE_FISCALE_CU]'
    else:
        for _k in ['ANNO_CU','MODALITA_CU','REDDITO_LORDO_CU','CONTRIBUTI_INPS_CU','CONTRIBUTI_CASSA_CU',
                   'CONTRIBUTI_TOTALI_CU','NETTO_CORRISPOSTO_CU','TFR_ACCANTONATO_CU',
                   'INDENNITA_CONVIVENZA_CU','IMPONIBILE_FISCALE_CU']:
            vars_map[_k] = f'[{_k}]'

    # --- Variabili formato numerico (senza simbolo valuta) ---
    _strip_cur = lambda v: re.sub(r'[^\d.\-]', '', str(v)) if v else '0'
    for _num_key, _src_key in [
        ('RETRIBUZIONE_TOTALE_NUM', 'RETRIBUZIONE_TOTALE'),
        ('CONTRIBUTI_MENSILI_NUM', 'CONTRIBUTI_MENSILI'),
        ('PAGA_BASE_NUM', 'PAGA_BASE'),
        ('PAGA_ORARIA_NUM', 'PAGA_ORARIA'),
        ('BUDGET_ANNUALE_NUM', 'BUDGET_ANNUALE'),
        ('BUDGET_MENSILE_NUM', 'BUDGET_MENSILE'),
        ('ORE_SETTIMANALI_NUM', 'ORE_SETTIMANALI'),
        ('ORE_MENSILI_NUM', 'ORE_MENSILI'),
        ('ORE_INPS_NUM', 'ORE_INPS'),
    ]:
        vars_map[_num_key] = _strip_cur(vars_map.get(_src_key, ''))

    # --- Variabili CCNL importi mensili ---
    if parametri:
        vars_map['IND_FUNZIONE_MENSILE'] = f'\u20ac {parametri.ind_funzione_mensile:,.2f}' if hasattr(parametri, 'ind_funzione_mensile') and parametri.ind_funzione_mensile else '[IND_FUNZIONE_MENSILE]'
        vars_map['IND_MINORI_6_MENSILE_FT'] = f'\u20ac {parametri.ind_minori_6_mensile_ft:,.2f}' if hasattr(parametri, 'ind_minori_6_mensile_ft') and parametri.ind_minori_6_mensile_ft else '[IND_MINORI_6_MENSILE_FT]'
        vars_map['IND_MINORI_6_MENSILE_PT'] = f'\u20ac {parametri.ind_minori_6_mensile_pt:,.2f}' if hasattr(parametri, 'ind_minori_6_mensile_pt') and parametri.ind_minori_6_mensile_pt else '[IND_MINORI_6_MENSILE_PT]'
        vars_map['IND_PIU_ASSISTITI_MENSILE'] = f'\u20ac {parametri.ind_piu_assistiti_mensile:,.2f}' if hasattr(parametri, 'ind_piu_assistiti_mensile') and parametri.ind_piu_assistiti_mensile else '[IND_PIU_ASSISTITI_MENSILE]'
        vars_map['IND_CERT_QUALITA_MENSILE'] = f'\u20ac {parametri.ind_cert_qualita_mensile:,.2f}' if hasattr(parametri, 'ind_cert_qualita_mensile') and parametri.ind_cert_qualita_mensile else '[IND_CERT_QUALITA_MENSILE]'
    else:
        for _k in ['IND_FUNZIONE_MENSILE','IND_MINORI_6_MENSILE_FT','IND_MINORI_6_MENSILE_PT',
                   'IND_PIU_ASSISTITI_MENSILE','IND_CERT_QUALITA_MENSILE']:
            vars_map[_k] = f'[{_k}]'

    # --- Variabili utente ---
    if user and hasattr(user, 'get_username'):
        vars_map['NOME_UTENTE'] = getattr(user, 'first_name', '') or '[NOME_UTENTE]'
        vars_map['COGNOME_UTENTE'] = getattr(user, 'last_name', '') or '[COGNOME_UTENTE]'
        vars_map['NOME_COGNOME_UTENTE'] = f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip() or user.get_username()
        vars_map['EMAIL_UTENTE'] = getattr(user, 'email', '') or '[EMAIL_UTENTE]'
    else:
        vars_map['NOME_UTENTE'] = '[NOME_UTENTE]'
        vars_map['COGNOME_UTENTE'] = '[COGNOME_UTENTE]'
        vars_map['NOME_COGNOME_UTENTE'] = '[NOME_COGNOME_UTENTE]'
        vars_map['EMAIL_UTENTE'] = '[EMAIL_UTENTE]'

    if extra_vars and isinstance(extra_vars, dict):
        vars_map.update(extra_vars)

    vars_map['datore_nome'] = vars_map.get('NOME_DATORE', '')
    vars_map['lavoratore_nome'] = vars_map.get('NOME_LAVORATORE', '')
    vars_map['datore_cognome'] = vars_map.get('NOME_COGNOME_DATORE', '')
    vars_map['lavoratore_cognome'] = vars_map.get('NOME_COGNOME_LAVORATORE', '')
    vars_map['beneficiario_nome'] = vars_map.get('NOME_BENEFICIARIO', '')

    import operator as _op
    _SAFE_OPS = {'+': _op.add, '-': _op.sub, '*': _op.mul, '/': _op.truediv, '//': _op.floordiv, '%': _op.mod}
    def _resolve_arith(m):
        vn, op, num = m.group(1), m.group(2), m.group(3)
        if vn not in vars_map:
            return m.group(0)
        v = vars_map[vn]
        try:
            vc = re.sub(r'[^\d.\-]', '', str(v))
            if not vc:
                return m.group(0)
            r = _SAFE_OPS[op](float(vc), float(num))
            has_cur = '\u20ac' in str(v)
            if has_cur:
                return f'\u20ac {r:,.2f}' if r != int(r) else f'\u20ac {int(r):,}'
            return f'{r:.2f}' if r != int(r) else str(int(r))
        except (ValueError, TypeError, KeyError, ZeroDivisionError):
            return m.group(0)

    def sostituisci(testo):
        if not testo:
            return ''
        risultato = re.sub(r'\{\{(\w+)\s*([+\-*/%]|//)\s*(\d+(?:\.\d+)?)\}\}', _resolve_arith, testo)
        risultato = re.sub(r'\{\{(\w+)(?:,\s*(\d+))?\}\}', lambda m: _replacer_pct(m, vars_map), risultato)
        risultato = re.sub(r'\{(\w+)\}', lambda m: str(vars_map.get(m.group(1), m.group(0))), risultato)
        return risultato

    return sostituisci(corpo_testo)
