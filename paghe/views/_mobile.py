from paghe.views._common_imports import *
from django.urls import reverse

logger = logging.getLogger(__name__)


@login_required
def mobile_dashboard(request):
    from paghe.views._dashboard import _contributi_mensili_trend
    import calendar
    buste = BustaPaga.objects.all()
    buste = filtro_visibilita(buste, request.user)
    ctx = {
        'm_nav': 'dash',
        'totale_datori': DatoreLavoro.objects.filter(visibile_a=request.user).count() if not request.user.is_superuser else DatoreLavoro.objects.count(),
        'totale_lavoratori': Lavoratore.objects.filter(visibile_a=request.user).count() if not request.user.is_superuser else Lavoratore.objects.count(),
        'totale_contratti': ContrattoAttivo.objects.filter(visibile_a=request.user).count() if not request.user.is_superuser else ContrattoAttivo.objects.count(),
        'totale_buste': buste.count(),
        'totale_beneficiari': Beneficiario.objects.count(),
        'totale_progetti': ProgettoRegionale.objects.count(),
    }
    try:
        trend = _contributi_mensili_trend()
        for m in trend:
            m['nome'] = calendar.month_abbr[m['mese']]
        ctx['contrib_trend'] = trend[:12]
    except Exception:
        ctx['contrib_trend'] = []
    return render(request, 'mobile/dashboard.html', ctx)


@login_required
def mobile_datori_list(request):
    datori = DatoreLavoro.objects.all()
    datori = filtro_visibilita(datori, request.user)
    return render(request, 'mobile/datori_list.html', {
        'm_nav': 'datori',
        'datori': datori.order_by('nome_cognome'),
    })


@login_required
def mobile_lavoratori_list(request):
    lav = Lavoratore.objects.all()
    lav = filtro_visibilita(lav, request.user)
    return render(request, 'mobile/lavoratori_list.html', {
        'm_nav': 'lav',
        'lavoratori': lav.order_by('nome_cognome'),
    })


@login_required
def mobile_contratti_list(request):
    contratti = ContrattoAttivo.objects.all()
    contratti = filtro_visibilita(contratti, request.user)
    return render(request, 'mobile/contratti_list.html', {
        'm_nav': 'contr',
        'contratti': contratti.select_related('datore', 'lavoratore').order_by('datore__nome_cognome'),
    })


@login_required
@permesso_richiesto('buste.calcola')
@never_cache
def mobile_calcoli_busta(request):
    """Mobile page for payroll calculation — simple form + key results."""
    oggi = date.today()
    mese = int(request.GET.get('mese', oggi.month))
    anno = int(request.GET.get('anno', oggi.year))
    contratti = ContrattoAttivo.objects.filter(stato='ATTIVO').select_related('datore', 'lavoratore')
    contratti = filtro_visibilita(contratti, request.user)
    return render(request, 'mobile/calcoli_busta.html', {
        'm_nav': 'buste',
        'contratti': contratti.order_by('datore__nome_cognome', 'lavoratore__nome_cognome'),
        'mese': mese,
        'anno': anno,
        'mesi_range': range(1, 13),
        'anni_range': range(2024, 2029),
        'mese_corrente': oggi.month,
        'anno_corrente': oggi.year,
    })


@login_required
@permesso_richiesto('buste.vedi')
@never_cache
def mobile_buste_archivio(request):
    buste = BustaPaga.objects.select_related('contratto__datore', 'contratto__lavoratore', 'documento').all()
    mese = request.GET.get('mese')
    anno = request.GET.get('anno')
    if mese:
        buste = buste.filter(mese=int(mese))
    if anno:
        buste = buste.filter(anno=int(anno))
    oggi = date.today()
    return render(request, 'mobile/buste_archivio.html', {
        'm_nav': 'buste',
        'buste': buste.order_by('-anno', '-mese'),
        'mese': int(mese) if mese else oggi.month,
        'anno': int(anno) if anno else oggi.year,
        'mesi_range': range(1, 13),
        'anni_range': range(2024, 2029),
    })


@login_required
@never_cache
def mobile_documenti(request):
    docs = DocumentoArchiviato.objects.select_related('contratto__datore', 'contratto__lavoratore').all()
    tipo = request.GET.get('tipo')
    if tipo:
        docs = docs.filter(tipo=tipo)
    return render(request, 'mobile/documenti_list.html', {
        'm_nav': 'docs',
        'documenti': docs.order_by('-creato_il'),
        'tipi_documento': DocumentoArchiviato.objects.values_list('tipo', flat=True).distinct().order_by('tipo'),
        'tipo_filtro': tipo or '',
    })


@login_required
def mobile_datore_detail(request, identifier):
    datore = get_object_or_404(DatoreLavoro, pk=identifier)
    contratti = ContrattoAttivo.objects.filter(datore=datore).select_related('lavoratore')[:10]
    return render(request, 'mobile/datore_detail.html', {
        'm_nav': 'datori',
        'd': datore,
        'contratti': contratti,
    })


@login_required
def mobile_lavoratore_detail(request, identifier):
    lav = get_object_or_404(Lavoratore, pk=identifier)
    contratti = ContrattoAttivo.objects.filter(lavoratore=lav).select_related('datore')[:10]
    return render(request, 'mobile/lavoratore_detail.html', {
        'm_nav': 'lav',
        'l': lav,
        'contratti': contratti,
    })


@login_required
def mobile_contratto_detail(request, pk):
    c = get_object_or_404(ContrattoAttivo.objects.select_related('datore', 'lavoratore', 'parametri_minimi__livello'), pk=pk)
    buste = BustaPaga.objects.filter(contratto=c).order_by('-anno', '-mese')[:5]
    return render(request, 'mobile/contratto_detail.html', {
        'm_nav': 'contr',
        'c': c,
        'buste': buste,
    })


@login_required
def mobile_about(request):
    return render(request, 'mobile/about.html', {
        'm_nav': None,
    })


@login_required
def mobile_beneficiari_list(request):
    beneficiari = Beneficiario.objects.all().order_by('nome_cognome')
    return render(request, 'mobile/beneficiari_list.html', {
        'm_nav': 'benef',
        'beneficiari': beneficiari,
    })


@login_required
def mobile_progetti_list(request):
    progetti = ProgettoRegionale.objects.select_related('beneficiario', 'tipo').all().order_by('beneficiario__nome_cognome')
    return render(request, 'mobile/progetti_list.html', {
        'm_nav': 'prog',
        'progetti': progetti,
    })


@login_required
def mobile_beneficiario_detail(request, pk):
    b = get_object_or_404(Beneficiario, pk=pk)
    progetti = ProgettoRegionale.objects.filter(beneficiario=b).select_related('tipo').all()
    return render(request, 'mobile/beneficiario_detail.html', {
        'm_nav': 'benef',
        'b': b,
        'progetti': progetti,
    })


@login_required
def mobile_progetto_detail(request, pk):
    p = get_object_or_404(ProgettoRegionale.objects.select_related('beneficiario', 'tipo'), pk=pk)
    contratti = ContrattoAttivo.objects.filter(progetto=p).select_related('datore', 'lavoratore')[:10]
    return render(request, 'mobile/progetto_detail.html', {
        'm_nav': 'prog',
        'p': p,
        'contratti': contratti,
    })


@login_required
def mobile_ricerca(request):
    q = request.GET.get('q', '').strip()
    ctx = {'m_nav': None, 'q': q}
    if q:
        from django.db.models import Q
        ctx['datori'] = DatoreLavoro.objects.filter(
            Q(nome_cognome__icontains=q) | Q(codice_fiscale__icontains=q) | Q(comune__icontains=q)
        )[:10]
        ctx['lavoratori'] = Lavoratore.objects.filter(
            Q(nome_cognome__icontains=q) | Q(codice_fiscale__icontains=q) | Q(comune__icontains=q)
        )[:10]
        ctx['contratti'] = ContrattoAttivo.objects.filter(
            Q(datore__nome_cognome__icontains=q) | Q(lavoratore__nome_cognome__icontains=q)
        ).select_related('datore', 'lavoratore', 'parametri_minimi')[:10]
        ctx['beneficiari'] = Beneficiario.objects.filter(
            Q(nome_cognome__icontains=q) | Q(codice_fiscale__icontains=q) | Q(comune__icontains=q)
        )[:10]
        ctx['progetti'] = ProgettoRegionale.objects.filter(
            Q(beneficiario__nome_cognome__icontains=q) | Q(tipo__nome__icontains=q)
        ).select_related('beneficiario', 'tipo')[:10]
    return render(request, 'mobile/ricerca.html', ctx)


def _mobile_entity_form_view(request, tipo, pk=None):
    """View generica per creare/modificare entità semplici in mobile."""
    MODEL_MAP = {
        'datore': (DatoreLavoro, DatoreForm, 'mobile_datori_list'),
        'lav': (Lavoratore, LavoratoreForm, 'mobile_lavoratori_list'),
        'benef': (Beneficiario, BeneficiarioForm, 'mobile_beneficiari_list'),
        'progetto': (ProgettoRegionale, ProgettoRegionaleForm, 'mobile_progetti_list'),
        'contratto': (ContrattoAttivo, ContrattoForm, 'mobile_contratti_list'),
    }
    if tipo not in MODEL_MAP:
        return HttpResponseBadRequest('Tipo non valido')
    model_cls, form_cls, list_name = MODEL_MAP[tipo]
    titoli = {'datore': 'Nuovo Datore', 'lav': 'Nuovo Lavoratore',
              'benef': 'Nuovo Beneficiario', 'progetto': 'Nuovo Progetto',
              'contratto': 'Nuovo Contratto'}
    titolo_edit = {'datore': 'Modifica Datore', 'lav': 'Modifica Lavoratore',
                   'benef': 'Modifica Beneficiario', 'progetto': 'Modifica Progetto',
                   'contratto': 'Modifica Contratto'}
    is_create = pk is None
    titolo = titoli[tipo] if is_create else titolo_edit.get(tipo, 'Modifica')
    back_url = reverse(list_name)

    instance = None
    if pk:
        instance = get_object_or_404(model_cls, pk=pk)
        plural = {'datore': 'datori', 'lav': 'lavoratori', 'benef': 'beneficiari',
                  'progetto': 'progetti', 'contratto': 'contratti'}
        back_url = f'/m/{plural[tipo]}/{pk}/'

    # Contratto: sostituisci CheckboxSelectMultiple con SelectMultiple per compattezza
    if tipo == 'contratto':
        from django import forms as djforms
        if instance:
            form_cls.base_fields['progetto'].widget = djforms.SelectMultiple(attrs={'class': 'm-select', 'size': 4})
            form_cls.base_fields['visibile_a'].widget = djforms.SelectMultiple(attrs={'class': 'm-select', 'size': 3})

    if request.method == 'POST':
        form = form_cls(request.POST, instance=instance) if hasattr(form_cls, 'Meta') else form_cls(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            if hasattr(obj, 'visibile_a') and not obj.visibile_a_id:
                obj.visibile_a = request.user
            if tipo == 'contratto':
                # M2M fields not saved with commit=False
                pass  # save_m2m will be called after obj.save()
            obj.save()
            form.save_m2m()
            if pk:
                if tipo == 'progetto':
                    return redirect(f'/m/progetti/{obj.pk}/')
                return redirect(f'/m/{plural[tipo]}/{obj.pk}/')
            return redirect(list_name)
    else:
        form = form_cls(instance=instance) if instance else form_cls()

    # Gruppi di campi per sezioni form
    main_fields = [
        'datore', 'lavoratore', 'parametri_minimi',
        'data_assunzione', 'data_fine', 'data_inizio_tfr',
        'budget_mensile', 'budget_mensile_tfr',
        'ore_calcolate', 'paga_oraria_lorda', 'paga_tfr',
        'nome_cognome', 'codice_fiscale', 'comune', 'provincia', 'indirizzo', 'cap',
        'telefono', 'email', 'data_nascita', 'luogo_nascita', 'sesso', 'cittadinanza',
        'beneficiario', 'tipo', 'data_inizio', 'budget_annuale', 'mesi',
    ]
    visibility_fields = ['visibile_a', 'progetto']
    ctx = {
        'm_nav': list_name.replace('mobile_', '').replace('_list', ''),
        'form': form,
        'titolo': titolo,
        'action_url': request.path + ('?' + request.META.get('QUERY_STRING', '') if request.GET.urlencode() else ''),
        'back_url': back_url,
        'main_fields': main_fields,
        'visibility_fields': visibility_fields,
    }
    return render(request, 'mobile/entity_form.html', ctx)


@login_required
def mobile_entity_create(request):
    tipo = request.GET.get('tipo', 'datore')
    return _mobile_entity_form_view(request, tipo)


@login_required
def mobile_entity_edit(request, tipo, pk):
    return _mobile_entity_form_view(request, tipo, pk)


@login_required
def mobile_altri_calcoli(request):
    return render(request, 'mobile/altri_calcoli.html', {
        'm_nav': 'buste',
    })
