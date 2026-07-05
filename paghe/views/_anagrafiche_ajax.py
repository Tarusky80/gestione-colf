"""View AJAX per anagrafiche: CRUD + utility (estratte da _anagrafiche.py)."""

from paghe.views._common_imports import *
from paghe.views._constants import ANAGRAFICA_MAP
from paghe.views._helpers import _cerca_comune_per_nome, _decodifica_cf, _dati_eliminato
from paghe.views._anagrafiche import _arricchisci_anagrafica
from paghe.views._tfr_cessazione import (
    _genera_ultima_busta_cessazione, _genera_liquidazione_tfr_cessazione,
    _associa_documenti_cessazione,
)
logger = logging.getLogger(__name__)

PARAMETRI_FIELD_MAP = {
    'paga_tfr': 'tfr_orario', 'paga_13ma': 'tredicesima_oraria', 'paga_ferie': 'ferie_orarie', 'paga_festivi': 'festivi_orari',
    'ind_certificazione_qualita': 'ind_cert_qualita', 'ind_piu_persone_non_conv': 'ind_assistenza_piu_persone_non_conv',
    'ind_minori_non_conv': 'ind_minori_6_anni_non_conv', 'ind_piu_persone_qualita': 'ind_piu_persone_qualita',
    'ind_minori_qualita': 'ind_minori_qualita', 'ind_assistenza_piu_persone_ft': 'ind_assistenza_piu_persone_ft',
    'ind_assistenza_piu_persone_pt': 'ind_assistenza_piu_persone_pt', 'ind_minori_6_anni_ft': 'ind_minori_6_anni_ft',
    'ind_funzione_conviventi': 'ind_funzione_conviventi', 'ind_conviventi_ft_54h': 'conviventi_ft_54h',
    'ind_conviventi_pt_30h': 'conviventi_pt_30h', 'applica_notturno_assistenza': 'ind_notturno_assistenza',
    'applica_notturno_presenza': 'ind_notturno_presenza', 'applica_notturno_base': 'ind_notturno_base',
    'applica_notturno_20': 'ind_notturno_20', 'paga_notturno_tfr': 'notturno_tfr', 'paga_notturno_13ma': 'notturno_13ma',
    'paga_notturno_festivi': 'notturno_festivi', 'paga_notturno_ferie': 'notturno_ferie',
    'paga_pranzo': 'convivenza_pranzo', 'paga_cena': 'convivenza_cena', 'paga_alloggio': 'convivenza_alloggio',
    'usa_ind_funzione_mensile': 'ind_funzione_mensile', 'usa_ind_minori_6_mensile_ft': 'ind_minori_6_mensile_ft',
    'usa_ind_minori_6_mensile_pt': 'ind_minori_6_mensile_pt', 'usa_ind_piu_assistiti_mensile': 'ind_piu_assistiti_mensile',
    'usa_ind_cert_qualita_mensile': 'ind_cert_qualita_mensile', 'usa_retribuzione_sostituzione': 'retribuzione_sostituzione',
}


def _build_parametri_data():
    """Costruisce dict parametri_data + PARAMETRI_FIELD_MAP per template AJAX."""
    from paghe.models import ParametriCCNL, TabellaScattiAnzianita
    parametri_all = ParametriCCNL.objects.select_related('livello').all()
    parametri_data = {}
    scatti_cache = {s.livello: float(s.valore_scatto) for s in TabellaScattiAnzianita.objects.all()}
    for p in parametri_all:
        data = {}
        for bool_field, param_field in PARAMETRI_FIELD_MAP.items():
            data[bool_field] = float(getattr(p, param_field, 0) or 0)
        data['paga_base'] = float(p.paga_base)
        data['tfr_orario'] = float(p.tfr_orario)
        data['tredicesima_oraria'] = float(p.tredicesima_oraria)
        data['ferie_orarie'] = float(p.ferie_orarie)
        data['festivi_orari'] = float(p.festivi_orari)
        data['livello'] = p.livello.codice
        data['livello_colore'] = p.livello.colore
        data['descrizione_corta'] = p.descrizione_corta
        data['valore_scatto'] = scatti_cache.get(p.livello.codice, 0.0)
        data['minimo_mensile_ft'] = float(p.minimo_mensile_ft)
        data['minimo_mensile_pt'] = float(p.minimo_mensile_pt)
        parametri_data[str(p.pk)] = data
    return parametri_data


def _build_anagrafe_ctx(request):
    """Costruisce context parametri + datori/lavoratori data per AJAX contratto."""
    import json as json_lib
    opz = get_opzioni()
    parametri_data = _build_parametri_data()
    datori_data = {d.codice_fiscale: _arricchisci_anagrafica(d) for d in DatoreLavoro.objects.all()}
    lavoratori_data = {l.codice_fiscale: _arricchisci_anagrafica(l) for l in Lavoratore.objects.all()}
    return {
        'parametri_map': json_lib.dumps(PARAMETRI_FIELD_MAP),
        'parametri_data': json_lib.dumps(parametri_data),
        'parametri_map_keys': list(PARAMETRI_FIELD_MAP.keys()),
        'soglia_ore_contributi': float(opz.soglia_ore_contributi) if opz else 24,
        'tipi_progetto': TipoProgettoRegionale.objects.all().order_by('nome'),
        'livelli_parametri': Livello.objects.all().order_by('codice'),
        'datori_data': json_lib.dumps(datori_data),
        'lavoratori_data': json_lib.dumps(lavoratori_data),
    }


def handle_ajax_form(request, form_class, template_name):
    model_type = form_class._meta.model.__name__
    ctx = {'form': None, 'entity_type': model_type}
    if request.method == 'POST':
        form = form_class(request.POST, request.FILES)
        ctx['form'] = form
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        html = render_to_string(template_name, ctx, request=request)
        return JsonResponse({'success': False, 'html': html})
    else:
        ctx['form'] = form_class()
        html = render_to_string(template_name, ctx, request=request)
        return JsonResponse({'success': True, 'html': html})


@login_required
@permesso_richiesto('anagrafiche.crea')
def ajax_form_datore(request):
    return handle_ajax_form(request, DatoreForm, 'frontend/ajax_form.html')


@login_required
@permesso_richiesto('anagrafiche.crea')
def ajax_form_lavoratore(request):
    return handle_ajax_form(request, LavoratoreForm, 'frontend/ajax_form.html')


@login_required
@permesso_richiesto('anagrafiche.crea')
def ajax_form_beneficiario(request):
    return handle_ajax_form(request, BeneficiarioForm, 'frontend/ajax_form.html')


@login_required
@permesso_richiesto('contratti.crea')
def ajax_form_contratto(request):
    ctx = {'form': None, 'entity_type': 'ContrattoLavoro'}
    ctx.update(_build_anagrafe_ctx(request))
    tipi_doc = ['LETTERA_ASSUNZIONE','LETTERA_LICENZIAMENTO','LETTERA_DIMISSIONI','DEROGA_TFR','LETTERA_LIBERA','RICEVUTA','RIEPILOGO_RAPPORTO']
    ctx['modelli_precompilati'] = ModelloDocumentale.objects.filter(tipo__in=tipi_doc).order_by('tipo', 'oggetto_titolo')
    ctx['tfr_accantonato_cumulativo'] = 0
    if request.method == 'POST':
        form = ContrattoForm(request.POST, request.FILES)
        ctx['form'] = form
        if form.is_valid():
            instance = form.save()
            if request.GET.get('preview'):
                return JsonResponse({'success': True, 'pk': instance.pk})
            return JsonResponse({'success': True, 'redirect_url': '/contratti/'})
        html = render_to_string('frontend/ajax_form_contratto.html', ctx, request=request)
        return JsonResponse({'success': False, 'html': html})
    else:
        ctx['form'] = ContrattoForm(initial={
            'data_assunzione': date.today(), 'data_inizio_tfr': date.today(),
            'applica_scatti': False, 'modalita_tfr': 'INCLUSO',
        })
        html = render_to_string('frontend/ajax_form_contratto.html', ctx, request=request)
        return JsonResponse({'success': True, 'html': html})


@login_required
@permesso_richiesto('contratti.modifica')
@never_cache
def ajax_modifica_contratto(request, pk):
    contratto = get_object_or_404(ContrattoLavoro, pk=pk, stato='ATTIVO')
    import json as json_lib
    MESI_ITA = ['','gennaio','febbraio','marzo','aprile','maggio','giugno','luglio','agosto','settembre','ottobre','novembre','dicembre']
    oggi = date.today()
    mese_corr = oggi.month; anno_corr = oggi.year
    mese_prec = mese_corr - 1 if mese_corr > 1 else 12
    anno_prec = anno_corr if mese_corr > 1 else anno_corr - 1
    mese_succ = mese_corr + 1 if mese_corr < 12 else 1
    anno_succ = anno_corr if mese_corr < 12 else anno_corr + 1
    ctx = {}
    ctx.update(_build_anagrafe_ctx(request))
    ctx.update({
        'mese_corr': mese_corr, 'mese_corr_nome': MESI_ITA[mese_corr],
        'anno_corr': anno_corr, 'mese_prec': mese_prec,
        'mese_prec_nome': MESI_ITA[mese_prec], 'anno_prec': anno_prec,
        'mese_succ': mese_succ, 'mese_succ_nome': MESI_ITA[mese_succ],
        'anno_succ': anno_succ,
        'modelli_precompilati': ModelloDocumentale.objects.filter(
            tipo__in=['LETTERA_ASSUNZIONE','LETTERA_LICENZIAMENTO','LETTERA_DIMISSIONI',
                      'DEROGA_TFR','LETTERA_LIBERA','RICEVUTA','RIEPILOGO_RAPPORTO']
        ).order_by('tipo', 'oggetto_titolo'),
        'tfr_accantonato_cumulativo': contratto.totale_tfr_accantonato_cumulativo,
    })
    contratti_pks = list(ContrattoAttivo.objects.filter(stato='ATTIVO')
                         .order_by('datore__nome_cognome').values_list('pk', flat=True))
    contratti_qs = ContrattoAttivo.objects.filter(stato='ATTIVO') \
        .select_related('datore', 'lavoratore') \
        .prefetch_related('progetto__beneficiario') \
        .order_by('datore__nome_cognome')
    contratti_nav_data = []
    for c in contratti_qs:
        ben_names = list(c.progetto.values_list('beneficiario__nome_cognome', flat=True).distinct())
        ben_str = ben_names[0] if len(ben_names) == 1 else ', '.join(ben_names) if ben_names else ''
        label = f"{c.datore.nome_cognome} - {c.lavoratore.nome_cognome}"
        if ben_str:
            label += ' per ' + ben_str
        contratti_nav_data.append({'pk': c.pk, 'label': label})
    ctx['contratti_pks'] = json_lib.dumps(contratti_pks)
    ctx['contratto_pk_attuale'] = pk
    ctx['contratti_nav_data'] = json_lib.dumps(contratti_nav_data)
    if request.method == 'POST':
        form = ContrattoForm(request.POST, request.FILES, instance=contratto)
        ctx['form'] = form
        ctx['instance'] = contratto
        if form.is_valid():
            old_stato = contratto.stato
            form.save()
            if old_stato != 'CESSATO' and contratto.stato == 'CESSATO':
                logger.info(f"[Cessazione] Contratto {contratto.pk} passato a CESSATO. Genero documenti...")
                bp_norm, pdf_norm, tipo = _genera_ultima_busta_cessazione(contratto, request.user)
                pdf_tfr, nome_tfr = _genera_liquidazione_tfr_cessazione(contratto, request.user)
                if bp_norm:
                    _associa_documenti_cessazione(bp_norm, pdf_norm, pdf_tfr, nome_tfr, contratto, bp_norm.mese, bp_norm.anno, tipo, request.user)
                logger.info("[Cessazione] Documenti completati.")
            elif contratto.stato == 'CESSATO':
                has_tfr = BustaPaga.objects.filter(contratto=contratto, tipo_calcolo='TFR', tfr_data__tipo='cessazione').exists()
                if not has_tfr:
                    logger.info("[Cessazione] Contratto già CESSATO senza documenti — genero.")
                    bp_norm, pdf_norm, tipo = _genera_ultima_busta_cessazione(contratto, request.user)
                    pdf_tfr, nome_tfr = _genera_liquidazione_tfr_cessazione(contratto, request.user)
                    if bp_norm:
                        _associa_documenti_cessazione(bp_norm, pdf_norm, pdf_tfr, nome_tfr, contratto, bp_norm.mese, bp_norm.anno, tipo, request.user)
                else:
                    logger.info("[Cessazione] Contratto già CESSATO con documenti TFR — skip.")
            if request.GET.get('preview'):
                return JsonResponse({'success': True, 'pk': contratto.pk})
            return JsonResponse({'success': True})
        html = render_to_string('frontend/ajax_form_contratto.html', ctx, request=request)
        return JsonResponse({'success': False, 'html': html})
    else:
        ctx['form'] = ContrattoForm(instance=contratto)
        ctx['instance'] = contratto
        html = render_to_string('frontend/ajax_form_contratto.html', ctx, request=request)
        return JsonResponse({'success': True, 'html': html})


@login_required
@permesso_richiesto('anagrafiche.modifica')
def ajax_modifica_datore(request, pk):
    datore = get_object_or_404(DatoreLavoro, pk=pk)
    contratti = ContrattoLavoro.objects.filter(datore=datore)
    datori_qs = DatoreLavoro.objects.all().order_by('nome_cognome')
    datori_pks = list(datori_qs.values_list('pk', flat=True))
    datori_nav_data = [{'pk': d.pk, 'label': f"{d.nome_cognome} ({d.codice_fiscale})"} for d in datori_qs]
    ctx = {'form': None, 'instance': datore, 'entity_type': 'DatoreLavoro', 'tipo': 'datore',
           'contratti_collegati': contratti, 'datori_pks': datori_pks,
           'datore_pk_attuale': pk, 'datori_nav_data': datori_nav_data}
    if request.method == 'POST':
        form = DatoreForm(request.POST, request.FILES, instance=datore)
        ctx['form'] = form
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        html = render_to_string('frontend/ajax_form.html', ctx, request=request)
        return JsonResponse({'success': False, 'html': html})
    else:
        ctx['form'] = DatoreForm(instance=datore)
        html = render_to_string('frontend/ajax_form.html', ctx, request=request)
        return JsonResponse({'success': True, 'html': html})


@login_required
@permesso_richiesto('anagrafiche.modifica')
def ajax_modifica_lavoratore(request, pk):
    lavoratore = get_object_or_404(Lavoratore, pk=pk)
    contratti = ContrattoLavoro.objects.filter(lavoratore=lavoratore)
    lavoratori_qs = Lavoratore.objects.all().order_by('nome_cognome')
    lavoratori_pks = list(lavoratori_qs.values_list('pk', flat=True))
    lavoratori_nav_data = [{'pk': l.pk, 'label': f"{l.nome_cognome} ({l.codice_fiscale})"} for l in lavoratori_qs]
    ctx = {'form': None, 'instance': lavoratore, 'entity_type': 'Lavoratore', 'tipo': 'lavoratore',
           'contratti_collegati': contratti, 'lavoratori_pks': lavoratori_pks,
           'lavoratore_pk_attuale': pk, 'lavoratori_nav_data': lavoratori_nav_data}
    if request.method == 'POST':
        form = LavoratoreForm(request.POST, request.FILES, instance=lavoratore)
        ctx['form'] = form
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        html = render_to_string('frontend/ajax_form.html', ctx, request=request)
        return JsonResponse({'success': False, 'html': html})
    else:
        ctx['form'] = LavoratoreForm(instance=lavoratore)
        html = render_to_string('frontend/ajax_form.html', ctx, request=request)
        return JsonResponse({'success': True, 'html': html})


@login_required
@permesso_richiesto('anagrafiche.modifica')
def ajax_modifica_beneficiario(request, pk):
    beneficiario = get_object_or_404(Beneficiario, pk=pk)
    contratti = ContrattoLavoro.objects.filter(progetto__beneficiario=beneficiario).distinct()
    beneficiari_qs = Beneficiario.objects.all().order_by('nome_cognome')
    beneficiari_pks = list(beneficiari_qs.values_list('pk', flat=True))
    beneficiari_nav_data = [{'pk': b.pk, 'label': f"{b.nome_cognome} ({b.codice_fiscale})"} for b in beneficiari_qs]
    ctx = {'form': None, 'instance': beneficiario, 'entity_type': 'Beneficiario', 'tipo': 'beneficiario',
           'contratti_collegati': contratti, 'beneficiari_pks': beneficiari_pks,
           'beneficiario_pk_attuale': pk, 'beneficiari_nav_data': beneficiari_nav_data}
    if request.method == 'POST':
        form = BeneficiarioForm(request.POST, request.FILES, instance=beneficiario)
        ctx['form'] = form
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        html = render_to_string('frontend/ajax_form.html', ctx, request=request)
        return JsonResponse({'success': False, 'html': html})
    else:
        ctx['form'] = BeneficiarioForm(instance=beneficiario)
        html = render_to_string('frontend/ajax_form.html', ctx, request=request)
        return JsonResponse({'success': True, 'html': html})


@login_required
@permesso_richiesto('anagrafiche.crea')
def ajax_duplica_anagrafica(request, tipo, pk):
    conf = ANAGRAFICA_MAP.get(tipo)
    if not conf:
        return JsonResponse({'success': False, 'message': 'Tipo non valido'})
    model = conf['model']
    form_class = conf['form']
    obj = get_object_or_404(model, pk=pk)
    ctx = {'form': None, 'entity_type': model.__name__}
    if tipo == 'contratto':
        _arricchisci_ctx_contratto(ctx, request)
    if request.method == 'POST':
        form = form_class(request.POST, request.FILES)
        ctx['form'] = form
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        html = render_to_string(conf['template'], ctx, request=request)
        return JsonResponse({'success': False, 'html': html})
    initial = {}
    for f in model._meta.get_fields():
        if hasattr(f, 'name') and not f.auto_created and f.name not in conf['skip_fields'] and f.name != 'pk':
            if f.many_to_many:
                if hasattr(obj, f.name):
                    initial[f.name] = list(getattr(obj, f.name).values_list('pk', flat=True))
            else:
                initial[f.name] = getattr(obj, f.name)
    ctx['form'] = form_class(initial=initial)
    html = render_to_string(conf['template'], ctx, request=request)
    return JsonResponse({'success': True, 'html': html})


def _arricchisci_ctx_contratto(ctx, request):
    ctx.update(_build_anagrafe_ctx(request))


@login_required
@permesso_richiesto('anagrafiche.elimina')
@require_http_methods(["POST"])
def ajax_elimina_anagrafica(request, tipo, pk):
    conf = ANAGRAFICA_MAP.get(tipo)
    if not conf:
        return JsonResponse({'success': False, 'message': 'Tipo non valido'})
    model = conf['model']
    obj = get_object_or_404(model, pk=pk)
    RecordEliminato.objects.create(
        tipo=tipo, original_pk=str(obj.pk),
        dati=_dati_eliminato(obj), descrizione=str(obj),
    )
    obj.delete()
    return JsonResponse({'success': True})


@login_required
@permesso_richiesto('contratti.elimina')
@never_cache
def ajax_elimina_contratto(request, pk):
    from paghe.models import ContrattoLavoro
    obj = get_object_or_404(ContrattoLavoro, pk=pk)
    if request.method == 'POST':
        RecordEliminato.objects.create(
            tipo='contratto', original_pk=str(obj.pk),
            dati=_dati_eliminato(obj), descrizione=str(obj),
        )
        obj.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'message': 'Metodo non consentito'})


@login_required
@permesso_richiesto('contratti.elimina')
@require_http_methods(["POST"])
def ajax_elimina_tutti_cessati(request):
    cessati = ContrattoLavoro.objects.exclude(stato='ATTIVO')
    count = cessati.count()
    for obj in cessati:
        RecordEliminato.objects.create(
            tipo='contratto', original_pk=str(obj.pk),
            dati=_dati_eliminato(obj), descrizione=str(obj),
        )
    cessati.delete()
    return JsonResponse({'success': True, 'message': f'{count} contratti cessati spostati nel cestino.'})


@login_required
@permesso_richiesto('contratti.elimina')
@require_http_methods(["POST"])
def ajax_elimina_tutti_cessati_definitivamente(request):
    cessati = ContrattoLavoro.objects.exclude(stato='ATTIVO')
    count = cessati.count()
    cessati.delete()
    return JsonResponse({'success': True, 'message': f'{count} contratti cessati eliminati definitivamente.'})


@login_required
def anagrafica_search_json(request, tipo):
    q = request.GET.get('q', '').strip()
    results = []
    model_map = {
        'datore': (DatoreLavoro, 'Datore'),
        'lavoratore': (Lavoratore, 'Lavoratore'),
        'beneficiario': (Beneficiario, 'Beneficiario'),
    }
    if len(q) < 1:
        return JsonResponse({'results': []})
    models_to_search = model_map.values() if tipo == 'tutti' else [model_map.get(tipo)] if model_map.get(tipo) else []
    if not models_to_search:
        return JsonResponse({'results': []})
    for model_class, label in models_to_search:
        items = model_class.objects.filter(
            Q(nome_cognome__icontains=q) | Q(codice_fiscale__icontains=q) | Q(comune__icontains=q)
        )[:8]
        for item in items:
            results.append({
                'pk': item.pk, 'tipo': label.lower(),
                'nome': item.nome_cognome,
                'codice_fiscale': item.codice_fiscale,
                'comune': getattr(item, 'comune', ''),
            })
    return JsonResponse({'results': results})


@login_required
@permesso_richiesto('anagrafiche.vedi')
def ajax_decodifica_cf(request):
    cf = request.GET.get('cf', '')
    return JsonResponse(_decodifica_cf(cf))


@login_required
@permesso_richiesto('anagrafiche.vedi')
def ajax_cerca_comune(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'found': False})
    info = _cerca_comune_per_nome(q)
    if info:
        return JsonResponse({
            'found': True, 'comune': info.get('comune', ''),
            'provincia': info.get('provincia', ''),
            'sigla': info.get('sigla', ''),
            'cap': info.get('cap', ''),
        })
    return JsonResponse({'found': False})


@login_required
@permesso_richiesto('contratti.modifica')
@require_http_methods(['POST'])
def ajax_copia_data_fine(request):
    import json
    data = json.loads(request.body)
    direzione = data.get('direzione')
    contratto_pk = data.get('contratto_pk')
    progetto_pk = data.get('progetto_pk')
    from paghe.models import ProgettoRegionale, ContrattoLavoro
    if direzione == 'progetto_to_contratto':
        progetto = get_object_or_404(ProgettoRegionale, pk=progetto_pk)
        contratto = get_object_or_404(ContrattoLavoro, pk=contratto_pk)
        contratto.data_fine = progetto.data_fine
        contratto.save(update_fields=['data_fine'])
        val = contratto.data_fine.strftime('%Y-%m-%d') if contratto.data_fine else ''
        return JsonResponse({'ok': True, 'data_fine': val,
                             'messaggio': 'Data fine copiata dal progetto regionale.'})
    elif direzione == 'progetto_a_tutti_contratti':
        progetto = get_object_or_404(ProgettoRegionale, pk=progetto_pk)
        contratti = ContrattoLavoro.objects.filter(progetto=progetto)
        count = 0
        for c in contratti:
            c.data_fine = progetto.data_fine
            c.save(update_fields=['data_fine'])
            count += 1
        val = progetto.data_fine.strftime('%Y-%m-%d') if progetto.data_fine else ''
        return JsonResponse({'ok': True, 'data_fine': val,
                             'messaggio': f'Data fine copiata a {count} contratto/i.'})
    return JsonResponse({'ok': False, 'errore': 'Direzione non valida.'})


@login_required
@permesso_richiesto('impostazioni')
@require_http_methods(['POST'])
def ajax_test_smtp(request):
    import smtplib
    from email.mime.text import MIMEText
    opzioni = get_opzioni()
    if not opzioni or not opzioni.email_smtp_server:
        return JsonResponse({'success': False, 'error': 'SMTP non configurato.'})
    try:
        msg = MIMEText('Email di prova da GestioneColf — Configurazione SMTP OK.', 'plain', 'utf-8')
        msg['From'] = opzioni.email_mittente or opzioni.email_smtp_username
        msg['To'] = opzioni.email_mittente or opzioni.email_smtp_username
        msg['Subject'] = 'Test SMTP GestioneColf'
        smtp = smtplib.SMTP(opzioni.email_smtp_server, opzioni.email_smtp_port or 587, timeout=10)
        if opzioni.email_usa_tls:
            smtp.starttls()
        if opzioni.email_smtp_username and opzioni.get_smtp_password():
            smtp.login(opzioni.email_smtp_username, opzioni.get_smtp_password())
        smtp.send_message(msg)
        smtp.quit()
        return JsonResponse({'success': True, 'message': f'Email di prova inviata a {msg["To"]}.'})
    except Exception as e:
        logger.exception("Errore in ajax_test_smtp")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@permesso_richiesto('contratti.modifica')
@require_http_methods(['POST'])
def ajax_salva_anticipo_tfr(request):
    from datetime import datetime
    import json as json_lib
    try:
        body = json_lib.loads(request.body)
        contratto = get_object_or_404(ContrattoAttivo, pk=body.get('contratto_pk'))
        importo = body.get('importo')
        if not importo:
            return JsonResponse({'success': False, 'error': 'Importo richiesto.'})
        data_raw = body.get('data', '')
        data_date = datetime.strptime(data_raw, '%Y-%m-%d').date() if data_raw else date.today()
        anticipo = AnticipoTFR.objects.create(
            contratto=contratto, importo=importo, data=data_date, note=body.get('note', ''),
        )
        return JsonResponse({
            'success': True, 'pk': anticipo.pk, 'importo': str(anticipo.importo),
            'data': anticipo.data.strftime('%d/%m/%Y'), 'note': anticipo.note,
        })
    except Exception as e:
        logger.exception("Errore in ajax_salva_anticipo_tfr")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@permesso_richiesto('contratti.elimina')
@require_http_methods(['POST'])
def ajax_elimina_anticipo_tfr(request, pk):
    anticipo = get_object_or_404(AnticipoTFR, pk=pk)
    anticipo.delete()
    return JsonResponse({'success': True})


@login_required
@permesso_richiesto('contratti.vedi')
def ajax_lista_anticipi_tfr(request, contratto_pk):
    contratto = get_object_or_404(ContrattoAttivo, pk=contratto_pk)
    anticipi = AnticipoTFR.objects.filter(contratto=contratto).order_by('-data')
    items = [{'pk': a.pk, 'importo': str(a.importo), 'data': a.data.strftime('%d/%m/%Y'), 'note': a.note} for a in anticipi]
    return JsonResponse({'success': True, 'items': items, 'totale': str(sum(a.importo for a in anticipi))})


@login_required
@permesso_richiesto('contratti.vedi')
def ajax_storico_modifiche_contratto(request, contratto_pk):
    contratto = get_object_or_404(ContrattoLavoro, pk=contratto_pk)
    items = []
    for m in ModificaContratto.objects.filter(contratto=contratto).select_related('utente')[:100]:
        items.append({
            'data_modifica': m.data_modifica,
            'campo': m.campo, 'valore_precedente': m.valore_precedente,
            'valore_nuovo': m.valore_nuovo,
            'utente': m.utente.get_full_name() or m.utente.username if m.utente else 'Sistema',
        })
    for h in contratto.history.all().order_by('-history_date').select_related('history_user')[:100]:
        prev = h.prev_record
        if prev is None:
            items.append({
                'data_modifica': h.history_date,
                'campo': 'Contratto creato',
                'valore_precedente': '',
                'valore_nuovo': '',
                'utente': h.history_user.get_full_name() or h.history_user.username if h.history_user else 'Sistema',
            })
        else:
            delta = h.diff_against(prev)
            if delta:
                for c in delta.changes:
                    items.append({
                        'data_modifica': h.history_date,
                        'campo': c.field,
                        'valore_precedente': str(c.old) if c.old is not None else '',
                        'valore_nuovo': str(c.new) if c.new is not None else '',
                        'utente': h.history_user.get_full_name() or h.history_user.username if h.history_user else 'Sistema',
                    })
    items.sort(key=lambda x: x['data_modifica'], reverse=True)
    items = items[:100]
    from django.template.loader import render_to_string
    html = render_to_string('frontend/_lista_modifiche_contratto.html', {'modifiche': items})
    return JsonResponse({'success': True, 'html': html, 'count': len(items)})


@login_required
@permesso_richiesto('contratti.modifica')
def ajax_rinnova_contratto(request, pk):
    originale = get_object_or_404(ContrattoLavoro, pk=pk)
    today = date.today()
    ctx = {'form': None, 'entity_type': 'ContrattoLavoro'}
    _arricchisci_ctx_contratto(ctx, request)
    if request.method == 'POST':
        form = ContrattoForm(request.POST, request.FILES)
        ctx['form'] = form
        if form.is_valid():
            nuovo = form.save()
            return JsonResponse({'success': True, 'pk': nuovo.pk})
        html = render_to_string('frontend/ajax_form_contratto.html', ctx, request=request)
        return JsonResponse({'success': False, 'html': html})
    initial = {}
    for f in ContrattoLavoro._meta.get_fields():
        if hasattr(f, 'name') and not f.auto_created and f.name != 'id':
            if f.many_to_many:
                if hasattr(originale, f.name):
                    initial[f.name] = list(getattr(originale, f.name).values_list('pk', flat=True))
            else:
                initial[f.name] = getattr(originale, f.name)
    initial['data_assunzione'] = today
    initial['data_fine'] = None
    initial['stato'] = 'ATTIVO'
    initial['codice_rapporto_inps'] = ''
    initial['ore_calcolate'] = None
    initial['contratto_rinnovato_da'] = originale.pk
    ctx['form'] = ContrattoForm(initial=initial)
    ctx['is_rinnovo'] = True
    ctx['contratto_rinnovato_da'] = originale
    html = render_to_string('frontend/ajax_form_contratto.html', ctx, request=request)
    return JsonResponse({'success': True, 'html': html})


@login_required
@permesso_richiesto('contratti.vedi')
def ajax_alert_contratto(request, pk):
    contratto = get_object_or_404(ContrattoAttivo, pk=pk)
    oggi = date.today()
    alerts = {}

    # 1. Scadenza imminente
    if contratto.data_fine:
        gg = (contratto.data_fine - oggi).days
        if gg < 0:
            alerts['scadenza'] = {'stato': 'rosso', 'msg': f'Scaduto da {abs(gg)} giorni'}
        elif gg <= 30:
            alerts['scadenza'] = {'stato': 'rosso', 'msg': f'Scade tra {gg} giorni'}
        elif gg <= 60:
            alerts['scadenza'] = {'stato': 'giallo', 'msg': f'Scade tra {gg} giorni'}
        else:
            alerts['scadenza'] = {'stato': 'verde', 'msg': f'{gg} giorni rimanenti'}

    # 2. TFR
    if not contratto.data_inizio_tfr:
        alerts['tfr'] = {'stato': 'rosso', 'msg': 'Data inizio TFR non impostata'}
    elif contratto.data_inizio_tfr == contratto.data_assunzione:
        alerts['tfr'] = {'stato': 'giallo', 'msg': 'TFR = data assunzione (possibile retrodatarli)'}
    else:
        alerts['tfr'] = {'stato': 'verde', 'msg': f'TFR dal {contratto.data_inizio_tfr.strftime("%d/%m/%Y")}'}

    # 3. Convivenza — controlla se il campo is_convivente è coerente
    if contratto.is_convivente:
        alerts['convivenza'] = {'stato': 'verde', 'msg': 'Convivente'}
    else:
        alerts['convivenza'] = {'stato': 'giallo', 'msg': 'Non convivente'}

    # 4. Ore PAGOPA insufficienti
    budget = contratto.budget_di_partenza
    paga_oraria = float(contratto.parametri_minimi.paga_oraria_lorda or 0)
    if paga_oraria > 0:
        ore_minime = budget / paga_oraria if budget > 0 else 0
        ore_attuali = contratto.ore_calcolata or 0
        if ore_attuali < ore_minime * 0.8:
            alerts['ore_pagopa'] = {'stato': 'rosso', 'msg': f'Ore ({ore_attuali:.0f}) < 80% del target ({ore_minime:.0f})'}
        elif ore_attuali < ore_minime:
            alerts['ore_pagopa'] = {'stato': 'giallo', 'msg': f'Ore ({ore_attuali:.0f}) sotto target ({ore_minime:.0f})'}
        else:
            alerts['ore_pagopa'] = {'stato': 'verde', 'msg': f'Ore sufficienti ({ore_attuali:.0f})'}
    else:
        alerts['ore_pagopa'] = {'stato': 'giallo', 'msg': 'Paga oraria non disponibile'}

    # 5. Rinnovo prossimo (solo determinato)
    if contratto.tipo_contratto == 'DETERMINATO' and contratto.data_fine:
        gg = (contratto.data_fine - oggi).days
        if gg <= 30:
            alerts['rinnovo'] = {'stato': 'rosso', 'msg': f'Termine tra {gg} giorni — prepara rinnovo'}
        elif gg <= 90:
            alerts['rinnovo'] = {'stato': 'giallo', 'msg': f'Termine tra {gg} giorni'}
        elif gg <= 180:
            alerts['rinnovo'] = {'stato': 'verde', 'msg': f'Termine tra {gg} giorni'}
    elif contratto.tipo_contratto == 'INDETERMINATO':
        alerts['rinnovo'] = {'stato': 'verde', 'msg': 'Indeterminato'}
    else:
        alerts['rinnovo'] = {'stato': 'giallo', 'msg': 'Data fine non impostata'}

    # 6. Anagrafiche incomplete
    incompleti = []
    if not contratto.datore.codice_fiscale:
        incompleti.append('CF Datore')
    if not contratto.datore.comune:
        incompleti.append('Comune Datore')
    if not contratto.lavoratore.codice_fiscale:
        incompleti.append('CF Lavoratore')
    if not contratto.lavoratore.email:
        incompleti.append('Email Lavoratore')
    if incompleti:
        alerts['anagrafiche'] = {'stato': 'rosso', 'msg': 'Mancante: ' + ', '.join(incompleti)}
    else:
        alerts['anagrafiche'] = {'stato': 'verde', 'msg': 'Complete'}

    # 7. Budget esaurito
    if budget > 0:
        bdp = contratto.budget_di_partenza
        if bdp > 0:
            if hasattr(contratto, 'differenza_budget'):
                alerts['budget'] = {'stato': 'giallo', 'msg': f'Budget €{bdp:,.0f}'}
            else:
                alerts['budget'] = {'stato': 'verde', 'msg': f'Budget €{bdp:,.0f}'}
    else:
        alerts['budget'] = {'stato': 'giallo', 'msg': 'Nessun progetto / budget 0'}

    return JsonResponse({'alerts': alerts})
