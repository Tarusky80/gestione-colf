from paghe.views._common_imports import *
from paghe.models import ContrattoAttivo
from paghe.views._calcoli_core import _calcola_busta_data


@login_required
@permesso_richiesto('buste.vedi')
@never_cache
def comparatore_page(request):
    opzioni = get_opzioni()
    contratti = ContrattoAttivo.objects.filter(
        parametri_minimi__isnull=False
    ).select_related(
        'datore', 'lavoratore', 'parametri_minimi__livello'
    ).prefetch_related('progetto__tipo', 'progetto__beneficiario').order_by('datore__nome_cognome', 'lavoratore__nome_cognome')

    oggi = date.today()
    mese_default = oggi.month
    anno_default = oggi.year

    mese = int(request.GET.get('mese', mese_default))
    anno = int(request.GET.get('anno', anno_default))

    context = {
        'opzioni': opzioni,
        'contratti': contratti,
        'mese': mese,
        'anno': anno,
    }

    contratto_pk = request.GET.get('contratto') or request.POST.get('contratto')
    if contratto_pk:
        contratto = get_object_or_404(ContrattoAttivo, pk=contratto_pk)
        context['contratto'] = contratto

        current = _calcola_busta_data(contratto, mese, anno, is_convivente=contratto.is_convivente)
        context['current'] = current

        budget_alt = request.GET.get('budget_alt')
        ore_alt = request.GET.get('ore_alt')
        if budget_alt or ore_alt:
            budget_override = float(budget_alt) if budget_alt else None
            ore_override_val = float(ore_alt) if ore_alt else None
            toggles = {}
            for key in ['ind_funzione', 'ind_bambini_6', 'ind_piu_assistiti', 'ind_cert_qualita', 'scatti',
                        'rateo_tfr', 'rateo_13ma', 'rateo_ferie', 'rateo_festivi']:
                val = request.GET.get(key) or request.POST.get(key)
                if val is not None:
                    toggles[key] = val == '1' or val == 'on'
            alt = _calcola_busta_data(contratto, mese, anno, is_convivente=contratto.is_convivente,
                                      budget_override=budget_override, toggles=toggles or None,
                                      ore_override=ore_override_val)
            context['alternative'] = alt
            context['budget_alt'] = budget_alt
            context['ore_alt'] = ore_alt

            # Differenze tra scenario alternativo e corrente
            context['diff_lordo'] = alt['totale_lordo'] - current['totale_lordo']
            context['diff_contributi'] = alt['contributi']['totale'] - current['contributi']['totale']
            context['diff_netto'] = alt['netto'] - current['netto']
            context['diff_trimestrale'] = alt['contributi']['trimestrale_stima'] - current['contributi']['trimestrale_stima']

    return render(request, 'paghe/comparatore.html', context)
