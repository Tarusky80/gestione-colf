"""View lista/pagina per anagrafiche (datori, lavoratori, beneficiari, contratti, impostazioni).
Le view AJAX CRUD sono in _anagrafiche_ajax.py."""

from paghe.views._common_imports import *
from paghe.permessi import filtro_visibilita
from paghe.views._helpers import _decodifica_cf




logger = logging.getLogger(__name__)

_COMUNE_CACHE = {}
def _cerca_comune_con_fallback(nome):
    """Cerca comune con normalizzazione (apostrofi, spazi)."""
    from paghe.views._helpers import _cerca_comune_per_nome as _cerca
    nome = nome.strip()
    risultato = _cerca(nome)
    if risultato:
        return risultato
    # Fallback: normalizza apostrofi in spazio
    normalizzato = nome.replace("'", " ").replace("'", " ").strip()
    if normalizzato != nome:
        risultato = _cerca(normalizzato)
        if risultato:
            return risultato
    # Fallback: rimuovi tutto tranne lettere e spazi
    pulito = re.sub(r"[^a-zA-Z\u00C0-\u024F\s]", " ", nome).strip()
    if pulito != nome and pulito != normalizzato:
        risultato = _cerca(pulito)
        if risultato:
            return risultato
    return None

def _arricchisci_anagrafica(obj):
    """Costruisce dict con indirizzo, comune, provincia, cap, email, tel + dati CF."""
    d = {
        'indirizzo': obj.indirizzo or '',
        'comune': obj.comune or '',
        'email': obj.email or '',
        'telefono': obj.telefono or '',
        'provincia': '',
        'cap': '',
    }
    if obj.comune:
        key = obj.comune.strip().lower()
        if key not in _COMUNE_CACHE:
            _COMUNE_CACHE[key] = _cerca_comune_con_fallback(obj.comune) or {}
        info = _COMUNE_CACHE[key]
        d['provincia'] = info.get('sigla', '')
        d['cap'] = info.get('cap', '')
        pn = info.get('patrono_nome', '') or ''
        pd = info.get('patrono_data', '') or ''
        d['patrono_nome'] = pn
        d['patrono_data'] = pd
        d['patrono'] = (pn + (' (' + pd + ')' if pd else '')) if pn else ''
    else:
        d['patrono_nome'] = ''
        d['patrono_data'] = ''
        d['patrono'] = ''
    cf_data = _decodifica_cf(obj.codice_fiscale)
    d['data_nascita'] = cf_data.get('data_nascita', '')
    d['sesso'] = cf_data.get('sesso', '')
    d['comune_nascita'] = cf_data.get('comune_nascita', '')
    d['provincia_nascita'] = cf_data.get('provincia_nascita', '')
    return d

# --- datori_list ---
@login_required
@permesso_richiesto('anagrafiche.vedi')
@never_cache
def datori_list(request):
    opzioni = get_opzioni()
    datori = filtro_visibilita(DatoreLavoro.objects.all(), request.user).order_by('nome_cognome')
    comuni = DatoreLavoro.objects.exclude(comune='').exclude(comune__isnull=True)\
        .values_list('comune', flat=True).distinct().order_by('comune')
    context = {
        'opzioni': opzioni,
        'datori': datori,
        'count': datori.count(),
        'comuni': comuni,
    }
    return render(request, 'paghe/datori_list.html', context)


# --- lavoratori_list ---
@login_required
@permesso_richiesto('anagrafiche.vedi')
@never_cache
def lavoratori_list(request):
    opzioni = get_opzioni()
    lavoratori = filtro_visibilita(Lavoratore.objects.all(), request.user).order_by('nome_cognome')
    comuni = Lavoratore.objects.exclude(comune='').exclude(comune__isnull=True)\
        .values_list('comune', flat=True).distinct().order_by('comune')
    context = {
        'opzioni': opzioni,
        'lavoratori': lavoratori,
        'count': lavoratori.count(),
        'comuni': comuni,
    }
    return render(request, 'paghe/lavoratori_list.html', context)


# --- beneficiari_list ---
@login_required
@permesso_richiesto('anagrafiche.vedi')
@never_cache
def beneficiari_list(request):
    opzioni = get_opzioni()
    beneficiari = Beneficiario.objects.all().order_by('nome_cognome')
    comuni = Beneficiario.objects.exclude(comune='').exclude(comune__isnull=True)\
        .values_list('comune', flat=True).distinct().order_by('comune')
    view_mappa = request.GET.get('view') == 'mappa'
    context = {
        'opzioni': opzioni,
        'beneficiari': beneficiari,
        'count': beneficiari.count(),
        'comuni': comuni,
        'view_mappa': view_mappa,
    }
    return render(request, 'paghe/beneficiari_list.html', context)


# --- contratti_list ---
@login_required
@permesso_richiesto('contratti.vedi')
@never_cache
def contratti_list(request):
    opzioni = get_opzioni()
    contratti = filtro_visibilita(
        ContrattoAttivo.objects
        .filter(stato='ATTIVO')
        .select_related('datore', 'lavoratore', 'parametri_minimi__livello')
        .prefetch_related('progetto__tipo', 'progetto__beneficiario'),
        request.user
    ).order_by('-data_assunzione')
    livelli = Livello.objects.all()
    tipi_progetto = TipoProgettoRegionale.objects.all()
    # Comuni unici dai beneficiari dei progetti dei contratti attivi
    comuni = Beneficiario.objects.filter(
        progetti__contrattolavoro__stato='ATTIVO'
    ).exclude(comune='').exclude(comune__isnull=True)\
    .values_list('comune', flat=True).distinct().order_by('comune')
    oggi = date.today()
    mese_corr = oggi.month
    anno_corr = oggi.year
    mese_prec = mese_corr - 1 if mese_corr > 1 else 12
    anno_prec = anno_corr if mese_corr > 1 else anno_corr - 1
    mese_succ = mese_corr + 1 if mese_corr < 12 else 1
    anno_succ = anno_corr if mese_corr < 12 else anno_corr + 1
    context = {
        'opzioni': opzioni,
        'contratti': contratti,
        'livelli': livelli,
        'tipi_progetto': tipi_progetto,
        'comuni': comuni,
        'count': contratti.count(),
        'mese_corr': mese_corr,
        'anno_corr': anno_corr,
        'mese_prec': mese_prec,
        'anno_prec': anno_prec,
        'mese_succ': mese_succ,
        'anno_succ': anno_succ,
    }
    return render(request, 'paghe/contratti_list.html', context)


# --- impostazioni_page ---
@login_required
@permesso_richiesto('impostazioni')
@never_cache
def impostazioni_page(request):
    opzioni = get_opzioni()
    if not opzioni:
        opzioni = OpzioniSoftware.objects.create(nome_programma="Nuovo Progetto")

    if request.method == 'POST':
        form = OpzioniSoftwareForm(request.POST, request.FILES, instance=opzioni)
        if form.is_valid():
            form.save()
            cache.delete('opzioni_software')
            return redirect('impostazioni_page')
    else:
        form = OpzioniSoftwareForm(instance=opzioni)

    context = {
        'opzioni': opzioni,
        'form': form,
    }
    return render(request, 'paghe/impostazioni.html', context)
