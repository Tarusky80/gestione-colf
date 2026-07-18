from paghe.views._common_imports import *
from django.views.decorators.http import require_GET

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
        ctx['contrib_trend'] = trend[:3]
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
        'buste': buste.order_by('-anno', '-mese')[:50],
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
    oggi = date.today()
    return render(request, 'mobile/documenti_list.html', {
        'm_nav': 'docs',
        'documenti': docs.order_by('-creato_il')[:50],
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
