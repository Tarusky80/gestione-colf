"""Calcolo rivalutazione TFR (75% ISTAT + 1.5% fisso) e prospetto individuale."""
from paghe.views._common_imports import *
from paghe.models import ContrattoLavoro, IndiceISTAT

logger = logging.getLogger(__name__)

PERC_ISTAT = Decimal('0.75')
PERC_FISSO = Decimal('0.015')


def _variazione_istat(anno):
    """Calcola la variazione percentuale ISTAT FOI per l'anno dato rispetto al precedente.
    Restituisce un Decimal (es. 0.016 per 1.6%).
    """
    try:
        idx_corr = IndiceISTAT.objects.get(anno=anno)
        idx_prec = IndiceISTAT.objects.get(anno=anno - 1)
    except IndiceISTAT.DoesNotExist:
        return Decimal('0')
    if idx_prec.indice == 0:
        return Decimal('0')
    return (idx_corr.indice - idx_prec.indice) / idx_prec.indice


def _calcola_rivalutazione_annuale(importo_base, anno):
    """Calcola la rivalutazione annua su un importo base per l'anno dato.
    Formula: importo_base * (75% * variazione_ISTAT + 1.5%)
    """
    var_istat = _variazione_istat(anno)
    coeff = PERC_ISTAT * var_istat + PERC_FISSO
    return round(importo_base * coeff, 2)


def _prospetto_tfr_individuale(contratto, fino_al=None):
    """Genera prospetto annuale TFR con rivalutazione per un contratto.

    Restituisce lista di dict: [
        {'anno': 2020, 'mesi': 12, 'accantonato': ..., 'rivalutazione': ..., 'totale_progressivo': ...},
        ...
    ]
    Se applica_rivalutazione_tfr è False, rivalutazione = 0.
    """
    if contratto.modalita_tfr == 'INCLUSO' or not contratto.data_inizio_tfr:
        return []

    if fino_al is None:
        fino_al = timezone.localdate()

    p = contratto.parametri_minimi
    if not p:
        return []

    ore_m = contratto.ore_mensili_calcolate
    if ore_m <= 0:
        return []

    coeff = Decimal('0.3') if contratto.modalita_tfr == 'SEPARATO_70' else Decimal('1.0')
    tfr_mensile = round(Decimal(str(p.tfr_orario)) * Decimal(str(ore_m)) * coeff, 4)

    inizio = contratto.data_inizio_tfr
    annuali = []
    totale_progressivo = Decimal('0')

    for anno in range(inizio.year, fino_al.year + 1):
        if anno > fino_al.year:
            break
        primo_mese = 1 if anno > inizio.year else inizio.month
        ultimo_mese = 12 if anno < fino_al.year else fino_al.month
        if primo_mese > ultimo_mese:
            continue
        mesi = ultimo_mese - primo_mese + 1
        if mesi <= 0:
            continue
        accantonato = round(tfr_mensile * mesi, 2)
        if contratto.applica_rivalutazione_tfr:
            riv = _calcola_rivalutazione_annuale(totale_progressivo + accantonato, anno)
        else:
            riv = Decimal('0')
        totale_progressivo += accantonato + riv
        annuali.append({
            'anno': anno,
            'mesi': mesi,
            'accantonato': float(accantonato),
            'rivalutazione': float(riv),
            'totale_progressivo': float(totale_progressivo),
        })

    return annuali


def _safe_decimal(v):
    try:
        return Decimal(str(v))
    except Exception:
        logger.exception("Errore in _safe_decimal")
        return Decimal('0')


@login_required
@permesso_richiesto('buste.vedi')
def ajax_prospetto_tfr(request, pk):
    """Vista AJAX: restituisce prospetto TFR per un contratto."""
    try:
        contratto = ContrattoLavoro.objects.select_related('parametri_minimi').get(pk=pk)
    except ContrattoLavoro.DoesNotExist:
        return JsonResponse({'errore': 'Contratto non trovato'}, status=404)

    prospetto = _prospetto_tfr_individuale(contratto)
    if not prospetto:
        return JsonResponse({'prospetto': [], 'totale': 0, 'rivalutazione_totale': 0, 'solo_accantonato': 0})

    totale_riv = sum(p['rivalutazione'] for p in prospetto)
    ultimo = prospetto[-1]
    solo_accantonato = sum(p['accantonato'] for p in prospetto)
    return JsonResponse({
        'prospetto': prospetto,
        'totale': ultimo['totale_progressivo'],
        'rivalutazione_totale': round(totale_riv, 2),
        'solo_accantonato': round(solo_accantonato, 2),
        'applica_rivalutazione': contratto.applica_rivalutazione_tfr,
    })
