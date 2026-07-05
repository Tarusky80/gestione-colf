"""Modulo _calcoli_views - generato automaticamente da views.py"""

from paghe.views._common_imports import *

logger = logging.getLogger(__name__)

from paghe.views._helpers import _offusca_ctx_anagrafici, _parse_toggles, _parse_convivenza_items
from paghe.views._calcoli_core import _calcola_busta_data, _calcola_busta_inversa_data, _calcola_progetti_data, _calcola_busta_conviventi_ccnl_data, _calcola_malattia_data
from paghe.views._tfr_cessazione import _calcola_tfr_fino_a




def _get_base_calcolo_ctx(request, extra=None):
    opzioni = get_opzioni()
    contratti = ContrattoAttivo.objects.filter(stato='ATTIVO').select_related(
        'datore', 'lavoratore', 'parametri_minimi__livello'
    ).prefetch_related('progetto__tipo', 'progetto__beneficiario').order_by('datore__nome_cognome', 'lavoratore__nome_cognome')
    oggi = date.today()
    mese = int(request.GET.get('mese', oggi.month))
    anno = int(request.GET.get('anno', oggi.year))
    contratto_pk = request.GET.get('contratto')
    if contratto_pk:
        try:
            contratto_pk = int(contratto_pk)
            if not contratti.filter(pk=contratto_pk).exists():
                contratto_pk = None
        except (ValueError, TypeError):
            contratto_pk = None
    ctx = {
        'opzioni': opzioni,
        'contratti': contratti,
        'mese': mese,
        'anno': anno,
        'mesi_range': range(1, 13),
        'anni_range': range(2024, 2029),
        'mese_corrente': oggi.month,
        'anno_corrente': oggi.year,
        'contratto_pk': contratto_pk,
    }
    if extra:
        ctx.update(extra)
    return ctx


def _enrich_busta_response(data, contratto, mese, anno):
    if 'errore' not in data:
        data['busta_esistente'] = BustaPaga.objects.filter(contratto=contratto, mese=mese, anno=anno).exists()
        data['tfr_accantonato_cumulativo'] = float(contratto.totale_tfr_accantonato_cumulativo)
        data['modalita_tfr'] = contratto.modalita_tfr
        if data.get('progetti'):
            p2 = _calcola_progetti_data(data, contratto)
            if p2:
                data['progetti_data'] = p2
    return data


# --- calcoli_list ---
@login_required
@permesso_richiesto('buste.calcola')
@never_cache
def calcoli_list(request):
    extra = {'template_busta_paga': ModelloDocumentale.objects.filter(tipo='BUSTA_PAGA').order_by('codice')}
    return render(request, 'paghe/calcoli_list.html', _get_base_calcolo_ctx(request, extra=extra))


# --- calcoli_non_convivente ---
@login_required
@permesso_richiesto('buste.calcola')
@never_cache
def calcoli_non_convivente(request):
    return render(request, 'paghe/calcoli_non_convivente.html', _get_base_calcolo_ctx(request))


# --- ajax_calcola_busta ---
@login_required
@permesso_richiesto('buste.calcola')
@never_cache
def ajax_calcola_busta(request, pk):
    contratto = get_object_or_404(ContrattoAttivo, pk=pk)
    try:
        mese = int(request.GET.get('mese', date.today().month))
        anno = int(request.GET.get('anno', date.today().year))
    except (ValueError, TypeError):
        mese = date.today().month
        anno = date.today().year
    convivenza_items = _parse_convivenza_items(request)
    data = _calcola_busta_data(contratto, mese, anno, convivenza_items=convivenza_items, toggles=_parse_toggles(request))
    return JsonResponse(_enrich_busta_response(data, contratto, mese, anno))


# --- ajax_calcola_busta_non_convivente ---
@login_required
@permesso_richiesto('buste.calcola')
@never_cache
def ajax_calcola_busta_non_convivente(request, pk):
    contratto = get_object_or_404(ContrattoAttivo, pk=pk)
    try:
        mese = int(request.GET.get('mese', date.today().month))
        anno = int(request.GET.get('anno', date.today().year))
    except (ValueError, TypeError):
        mese = date.today().month
        anno = date.today().year
    sostituzione = request.GET.get('sostituzione') == '1'
    convivenza_items = _parse_convivenza_items(request)
    data = _calcola_busta_data(contratto, mese, anno, is_convivente=False, sostituzione=sostituzione, convivenza_items=convivenza_items, toggles=_parse_toggles(request))
    return JsonResponse(_enrich_busta_response(data, contratto, mese, anno))


# --- calcoli_conviventi_ccnl ---
@login_required
@permesso_richiesto('buste.calcola')
@never_cache
def calcoli_conviventi_ccnl(request):
    return render(request, 'paghe/calcoli_conviventi_ccnl.html', _get_base_calcolo_ctx(request))


# --- calcoli_inverso ---
@login_required
@permesso_richiesto('buste.calcola')
@never_cache
def calcoli_inverso(request):
    return render(request, 'paghe/calcoli_inverso.html', _get_base_calcolo_ctx(request))


# --- calcoli_notturno ---
@login_required
@permesso_richiesto('buste.calcola')
@never_cache
def calcoli_notturno(request):
    return render(request, 'paghe/calcoli_notturno.html', _get_base_calcolo_ctx(request))


# --- ajax_calcola_busta_notturna ---
@login_required
@permesso_richiesto('buste.calcola')
@never_cache
def ajax_calcola_busta_notturna(request, pk):
    contratto = get_object_or_404(ContrattoAttivo, pk=pk)
    try:
        mese = int(request.GET.get('mese', date.today().month))
        anno = int(request.GET.get('anno', date.today().year))
    except (ValueError, TypeError):
        mese = date.today().month
        anno = date.today().year
    p = contratto.parametri_minimi
    if not p:
        return JsonResponse({'errore': 'Parametri CCNL non impostati'})
    ore_mensili = float(contratto.ore_mensili_calcolate)
    if ore_mensili <= 0:
        return JsonResponse({'errore': 'Ore mensili pari a zero'})
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
    convivente_nott = request.GET.get('convivente_nott', '0') == '1'

    if tipo_notturno == 'presenza':
        importo_mensile = float(p.ind_notturno_presenza)
        label_tipo = 'Presenza Notturna (Art. 11)'
    elif tipo_notturno == 'assistenza':
        importo_mensile = float(p.ind_notturno_assistenza)
        label_tipo = 'Assistenza Notturna (Art. 10)'
    else:
        if ore_notturne <= 0:
            return JsonResponse({'errore': 'Inserire il numero di ore notturne'})
        base_nott = float(p.ind_notturno_base) if p.ind_notturno_base and float(p.ind_notturno_base) > 0 else float(p.paga_base)
        coeff_20 = float(p.ind_notturno_20) if p.ind_notturno_20 and float(p.ind_notturno_20) > 0 else 1.20
        paga_oraria = round(base_nott * coeff_20, 4)
        importo_mensile = round(paga_oraria * ore_notturne, 2)
        label_tipo = 'Notturno a Ore'

    ratei_notturni = []
    totale_ratei = 0.0
    mapping = [
        ('notturno_tfr', float(p.notturno_tfr), 'TFR Notturno', rateo_tfr),
        ('notturno_13ma', float(p.notturno_13ma), '13ª Notturna', rateo_13ma),
        ('notturno_ferie', float(p.notturno_ferie), 'Ferie Notturne', rateo_ferie),
        ('notturno_festivi', float(p.notturno_festivi), 'Festivi Notturni', rateo_festivi),
    ]
    for key, val, label, attivo in mapping:
        if not attivo:
            continue
        if val != 0:
            totale = round(val * ore_mensili, 2)
        else:
            totale = 0
        ratei_notturni.append({'label': label, 'orario': val, 'totale': totale})
        totale_ratei += totale

    if tipo_notturno == 'a_ore':
        if straord_nott and ore_straord_nott > 0:
            importo_sn = round(paga_oraria * 1.5 * ore_straord_nott, 2)
            ratei_notturni.append({'label': 'Straordinario Notturno (50%)', 'orario': round(paga_oraria * 1.5, 4), 'totale': importo_sn})
            totale_ratei += importo_sn
        if festivo_nott and ore_festive_nott > 0:
            importo_fn = round(paga_oraria * 1.6 * ore_festive_nott, 2)
            ratei_notturni.append({'label': 'Festivo/Domenicale Notturno (60%)', 'orario': round(paga_oraria * 1.6, 4), 'totale': importo_fn})
            totale_ratei += importo_fn
    totale_ratei = round(totale_ratei, 2)
    mese_nomi = ['', 'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
                 'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']
    ore_sett = float(contratto.ore_settimanali_calcolate) if hasattr(contratto, 'ore_settimanali_calcolate') else 0
    return JsonResponse({
        'tipo_notturno': tipo_notturno,
        'label_tipo': label_tipo,
        'importo_mensile': importo_mensile,
        'ore_mensili': ore_mensili,
        'ore_settimanali': round(ore_sett, 2),
        'ratei_notturni': ratei_notturni,
        'totale_ratei': totale_ratei,
        'totale_complessivo': round(importo_mensile + totale_ratei, 2),
        'livello': p.livello.codice if p.livello else '',
        'livello_colore': p.livello.colore if p.livello and p.livello.colore else '#5E6AD2',
        'datore': contratto.datore.nome_cognome,
        'datore_comune': contratto.datore.comune or '',
        'lavoratore': contratto.lavoratore.nome_cognome,
        'paga_base_oraria': round(float(p.paga_base), 4),
        'tipo_contratto': contratto.get_tipo_contratto_display(),
        'sostituzione': False,
        'convivente': convivente_nott,
        'mese_nome': mese_nomi[mese],
        'anno': anno,
        'mese': mese,
        'straord_nott': straord_nott,
        'ore_straord_nott': ore_straord_nott,
        'festivo_nott': festivo_nott,
        'ore_festive_nott': ore_festive_nott,
        'busta_esistente': BustaPaga.objects.filter(contratto=contratto, mese=mese, anno=anno).exists(),
        'tfr_accantonato_cumulativo': float(contratto.totale_tfr_accantonato_cumulativo),
        'modalita_tfr': contratto.modalita_tfr,
    })


# --- calcoli_malattia ---
@login_required
@permesso_richiesto('buste.calcola')
@never_cache
def calcoli_malattia(request):
    return render(request, 'paghe/calcoli_malattia.html', _get_base_calcolo_ctx(request))


# --- calcoli_tfr ---
@login_required
@permesso_richiesto('buste.calcola')
@never_cache
def calcoli_tfr(request):
    return render(request, 'paghe/calcoli_tfr.html', _get_base_calcolo_ctx(request))


# --- ajax_calcola_busta_malattia ---
@login_required
@permesso_richiesto('buste.calcola')
@never_cache
def ajax_calcola_busta_malattia(request, pk):
    contratto = get_object_or_404(ContrattoAttivo, pk=pk)
    try:
        mese = int(request.GET.get('mese', date.today().month))
        anno = int(request.GET.get('anno', date.today().year))
        giorni_malattia = int(request.GET.get('giorni_malattia', 0))
    except (ValueError, TypeError):
        return JsonResponse({'errore': 'Valori mese/anno/giorni non validi'})
    sostituzione = request.GET.get('sostituzione', '0') == '1'
    ricaduta = request.GET.get('ricaduta', '0') == '1'
    ricoverato = request.GET.get('ricoverato', '0') == '1'
    giorni_usati = request.GET.get('giorni_usati')
    data = _calcola_malattia_data(contratto, mese, anno, giorni_malattia, sostituzione=sostituzione, ricaduta=ricaduta, ricoverato=ricoverato, giorni_usati_override=int(giorni_usati) if giorni_usati else None)
    return JsonResponse(_enrich_busta_response(data, contratto, mese, anno))


# --- ajax_calcola_busta_tfr ---
@login_required
@permesso_richiesto('buste.calcola')
@never_cache
def ajax_calcola_busta_tfr(request, pk):
    import calendar
    contratto = get_object_or_404(ContrattoAttivo, pk=pk)
    if contratto.modalita_tfr == 'INCLUSO':
        return JsonResponse({'errore': 'TFR incluso nel lordo — nessun accantonamento da liquidare.'})
    data_inizio_str = request.GET.get('data_inizio')
    mese_req = request.GET.get('mese')
    anno_req = request.GET.get('anno')
    oggi = date.today()
    if mese_req and anno_req:
        try:
            mese_fine = int(mese_req)
            anno_fine = int(anno_req)
        except (ValueError, TypeError):
            mese_fine, anno_fine = oggi.month, oggi.year
    else:
        mese_fine, anno_fine = oggi.month, oggi.year
    ultimo = calendar.monthrange(anno_fine, mese_fine)[1]
    data_fine = date(anno_fine, mese_fine, ultimo)
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
        return JsonResponse({'errore': 'Nessun importo TFR accantonato da liquidare.'})
    p = contratto.parametri_minimi
    ore_m = contratto.ore_mensili_calcolate
    coeff = 0.3 if contratto.modalita_tfr == 'SEPARATO_70' else 1.0
    tfr_mensile = round(float(p.tfr_orario) * ore_m * coeff, 4) if p else 0
    return JsonResponse({
        'data_inizio': data_inizio_eff.strftime('%d/%m/%Y'),
        'data_fine': data_fine.strftime('%d/%m/%Y'),
        'data_inizio_raw': data_inizio_eff.isoformat(),
        'data_fine_raw': data_fine.isoformat(),
        'mesi': mesi,
        'tfr_mensile': tfr_mensile,
        'tfr_orario': float(p.tfr_orario) if p else 0,
        'ore_mensili': int(ore_m),
        'coeff': coeff,
        'cumulativo': cumulativo,
        'modalita_tfr': contratto.get_modalita_tfr_display(),
        'contratto_pk': contratto.pk,
        'datore': contratto.datore.nome_cognome,
        'lavoratore': contratto.lavoratore.nome_cognome,
        'data_assunzione': contratto.data_assunzione.strftime('%d/%m/%Y') if contratto.data_assunzione else '—',
        'data_assunzione_raw': contratto.data_assunzione.isoformat() if contratto.data_assunzione else '',
        'data_inizio_tfr_eff': (contratto.data_inizio_tfr or contratto.data_assunzione).strftime('%d/%m/%Y') if (contratto.data_inizio_tfr or contratto.data_assunzione) else '—',
        'data_inizio_tfr_raw': (contratto.data_inizio_tfr or contratto.data_assunzione).isoformat() if (contratto.data_inizio_tfr or contratto.data_assunzione) else '',
        'budget_mensile': round(float(contratto.budget_di_partenza), 2) if contratto.budget_di_partenza else 0,
        'paga_base': round(float(p.paga_base), 4) if p and p.paga_base else 0,
        'livello': p.livello.codice if p and p.livello else '?',
        'busta_esistente': BustaPaga.objects.filter(contratto=contratto, mese=mese_fine, anno=anno_fine).exists(),
        'errore': None,
    })


# --- calcoli_sostituzione ---
@login_required
@permesso_richiesto('buste.calcola')
@never_cache
def calcoli_sostituzione(request):
    """Pagina per calcolare sostituzione malattia: seleziona assente, costo malattia, sostituto con budget residuo."""
    extra = {'livelli': Livello.objects.all().order_by('codice')}
    return render(request, 'paghe/calcoli_sostituzione.html', _get_base_calcolo_ctx(request, extra=extra))


# --- ajax_calcola_costo_malattia_sostituzione ---
@login_required
@permesso_richiesto('buste.calcola')
@never_cache
def ajax_calcola_costo_malattia_sostituzione(request, pk):
    """Calcola costo malattia + budget residuo per la sostituzione."""
    contratto = get_object_or_404(ContrattoAttivo, pk=pk)
    try:
        mese = int(request.GET.get('mese', date.today().month))
        anno = int(request.GET.get('anno', date.today().year))
        giorni_malattia = int(request.GET.get('giorni_malattia', 0))
    except (ValueError, TypeError):
        return JsonResponse({'errore': 'Valori mese/anno/giorni non validi'})
    sostituzione = request.GET.get('sostituzione', '0') == '1'
    ricaduta = request.GET.get('ricaduta', '0') == '1'
    ricoverato = request.GET.get('ricoverato', '0') == '1'
    giorni_usati = request.GET.get('giorni_usati')
    data = _calcola_malattia_data(contratto, mese, anno, giorni_malattia, sostituzione=sostituzione, ricaduta=ricaduta, ricoverato=ricoverato, giorni_usati_override=int(giorni_usati) if giorni_usati else None)
    if 'errore' in data:
        return JsonResponse(data)
    budget_assente = float(contratto.budget_di_partenza)
    costo_malattia = float(data.get('importo_totale', 0))
    contributi_malattia = float(data.get('contributi_inps', 0))
    budget_residuo = round(budget_assente - costo_malattia, 2)
    data['budget_assente'] = round(budget_assente, 2)
    data['costo_malattia'] = costo_malattia
    data['contributi_malattia'] = contributi_malattia
    data['budget_residuo'] = budget_residuo
    return JsonResponse(data)


# --- ajax_calcola_busta_sostituto ---
@login_required
@permesso_richiesto('buste.calcola')
@never_cache
def ajax_calcola_busta_sostituto(request, pk):
    """Calcola la busta paga per il contratto sostituto usando il budget residuo."""
    contratto = get_object_or_404(ContrattoAttivo, pk=pk)
    try:
        mese = int(request.GET.get('mese', date.today().month))
        anno = int(request.GET.get('anno', date.today().year))
    except (ValueError, TypeError):
        mese = date.today().month
        anno = date.today().year
    budget_residuo = request.GET.get('budget_residuo')
    if not budget_residuo:
        return JsonResponse({'errore': 'Parametro budget_residuo mancante'})
    try:
        budget_residuo = float(budget_residuo)
    except (ValueError, TypeError):
        return JsonResponse({'errore': 'budget_residuo non valido'})
    if budget_residuo <= 0:
        return JsonResponse({'errore': 'Budget residuo esaurito, impossibile calcolare busta sostituto'})
    toggles = _parse_toggles(request)
    convivenza_items = _parse_convivenza_items(request)
    data = _calcola_busta_data(contratto, mese, anno, is_convivente=contratto.is_convivente, convivenza_items=convivenza_items, toggles=toggles, budget_override=budget_residuo)
    return JsonResponse(_enrich_busta_response(data, contratto, mese, anno))


# --- ajax_crea_contratto_sostituto ---
@login_required
@permesso_richiesto('buste.calcola')
@never_cache
def ajax_crea_contratto_sostituto(request):
    """Crea un nuovo Lavoratore (se non esiste) + ContrattoLavoro determinato per sostituzione."""
    if request.method != 'POST':
        return JsonResponse({'errore': 'Metodo non consentito'})
    try:
        datore_pk = request.POST.get('datore_pk', '').strip()
        nome = request.POST.get('nome', '').strip()
        cognome = request.POST.get('cognome', '').strip()
        cf = request.POST.get('codice_fiscale', '').strip().upper()
        livello_pk = request.POST.get('livello_pk', '').strip()
        ore_mensili = float(request.POST.get('ore_mensili', 0))
        data_inizio_str = request.POST.get('data_inizio', '').strip()
        data_fine_str = request.POST.get('data_fine', '').strip()
        is_convivente = request.POST.get('is_convivente', '0') == '1'
    except (ValueError, TypeError):
        return JsonResponse({'errore': 'Dati non validi'})
    if not all([datore_pk, nome, cognome, cf, livello_pk, ore_mensili, data_inizio_str]):
        return JsonResponse({'errore': 'Compilare tutti i campi obbligatori'})
    datore = get_object_or_404(DatoreLavoro, pk=datore_pk)
    livello = get_object_or_404(Livello, pk=livello_pk)
    try:
        data_inizio = date.fromisoformat(data_inizio_str)
        date.fromisoformat(data_fine_str) if data_fine_str else None
    except ValueError:
        return JsonResponse({'errore': 'Date non valide (formato YYYY-MM-DD)'})
    # Trova o crea Lavoratore
    lavoratore = Lavoratore.objects.filter(codice_fiscale=cf).first()
    if not lavoratore:
        lavoratore = Lavoratore.objects.create(
            nome_cognome=f'{nome} {cognome}',
            codice_fiscale=cf,
            comune=datore.comune or '',
        )
    # Trova ParametriCCNL per livello e anno
    anno_corrente = data_inizio.year
    parametri = ParametriCCNL.objects.filter(livello=livello, anno=anno_corrente).first()
    if not parametri:
        parametri = ParametriCCNL.objects.filter(livello=livello, anno=anno_corrente - 1).first()
    if not parametri:
        return JsonResponse({'errore': f'Parametri CCNL non trovati per livello {livello.codice} anno {anno_corrente}'})
    # Ente bilaterale: richiesto dal modello
    ente = TabellaCasse.objects.first()
    if not ente:
        return JsonResponse({'errore': 'Nessuna cassa/ente bilaterale trovata. Crearne una in Tabelle → Casse.'})
    # Crea ContrattoLavoro
    contratto = ContrattoLavoro.objects.create(
        datore=datore,
        lavoratore=lavoratore,
        parametri_minimi=parametri,
        ente_bilaterale=ente,
        ore_calcolate=ore_mensili,
        tipo_contratto='DETERMINATO',
        stato='ATTIVO',
        data_assunzione=data_inizio,
        data_inizio_tfr=data_inizio,
        is_convivente=is_convivente,
        applica_scatti=False,
        modalita_tfr='INCLUSO',
        paga_13ma=True,
        paga_ferie=True,
        paga_festivi=True,
    )
    return JsonResponse({'success': True, 'pk': contratto.pk, 'lavoratore': f'{nome} {cognome}', 'contratto': f'{contratto.datore.nome_cognome} — {contratto.lavoratore.nome_cognome}'})


# --- ajax_calcola_busta_conviventi_ccnl ---
@login_required
@permesso_richiesto('buste.calcola')
@never_cache
def ajax_calcola_busta_conviventi_ccnl(request, pk):
    contratto = get_object_or_404(ContrattoAttivo, pk=pk)
    try:
        mese = int(request.GET.get('mese', date.today().month))
        anno = int(request.GET.get('anno', date.today().year))
    except (ValueError, TypeError):
        mese = date.today().month
        anno = date.today().year
    tipo_orario = request.GET.get('tipo_orario', 'FT')
    convivenza_items = _parse_convivenza_items(request)
    data = _calcola_busta_conviventi_ccnl_data(contratto, mese, anno, tipo_orario=tipo_orario, toggles=_parse_toggles(request), convivenza_items=convivenza_items)
    return JsonResponse(_enrich_busta_response(data, contratto, mese, anno))


# --- ajax_calcola_busta_inversa ---
@login_required
@permesso_richiesto('buste.calcola')
@never_cache
def ajax_calcola_busta_inversa(request, pk):
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

    # Se nessun input, restituisci solo i flag del contratto
    if ore_mensili is None and ore_settimanali is None and lordo is None and netto is None:
        return JsonResponse({
            'solo_flags': True,
            'contratto_paga_pranzo': bool(getattr(contratto, 'paga_pranzo', False)),
            'contratto_paga_cena': bool(getattr(contratto, 'paga_cena', False)),
            'contratto_paga_alloggio': bool(getattr(contratto, 'paga_alloggio', False)),
            'ind_funzione_conviventi': bool(getattr(contratto, 'ind_funzione_conviventi', False)),
            'ind_minori_6_anni_ft': bool(getattr(contratto, 'ind_minori_6_anni_ft', False)),
            'ind_assistenza_piu_persone_ft': bool(getattr(contratto, 'ind_assistenza_piu_persone_ft', False)),
            'ind_certificazione_qualita': bool(getattr(contratto, 'ind_certificazione_qualita', False)),
            'contratto_applica_scatti': bool(getattr(contratto, 'applica_scatti', False)),
            'contratto_modalita_tfr': getattr(contratto, 'modalita_tfr', 'INCLUSO'),
            'contratto_paga_13ma': bool(getattr(contratto, 'paga_13ma', False)),
            'contratto_paga_ferie': bool(getattr(contratto, 'paga_ferie', False)),
            'contratto_paga_festivi': bool(getattr(contratto, 'paga_festivi', False)),
        })

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

    data = _calcola_busta_inversa_data(convivenza_items=_parse_convivenza_items(request), toggles=_parse_toggles(request), **kwargs)
    data = _enrich_busta_response(data, contratto, mese, anno)
    if request.GET.get('offusca') == '1':
        _offusca_ctx_anagrafici(data)
    return JsonResponse(data)
