"""Operazioni massive: rinnovo contratti, aggiornamento parametri CCNL."""

from paghe.views._common_imports import *
from paghe.models import ContrattoAttivo, ContrattoLavoro, ParametriCCNL


logger = logging.getLogger(__name__)


@login_required
@permesso_richiesto('contratti.modifica')
def rinnova_massivo_page(request):
    """Pagina per rinnovo massivo contratti."""
    contratti = ContrattoAttivo.objects.filter(stato='ATTIVO').select_related(
        'datore', 'lavoratore', 'parametri_minimi__livello'
    ).prefetch_related('progetto__tipo', 'progetto__beneficiario').order_by('datore__nome_cognome')

    livelli = list(dict.fromkeys(
        c.parametri_minimi.livello for c in contratti if c.parametri_minimi
    ))
    comuni = list(dict.fromkeys(
        p.beneficiario.comune for c in contratti
        for p in c.progetto.all() if p.beneficiario.comune
    ))
    tipi_progetto = list(dict.fromkeys(
        p.tipo for c in contratti for p in c.progetto.all() if p.tipo
    ))

    oggi = date.today()
    return render(request, 'paghe/rinnova_massivo.html', {
        'contratti': contratti,
        'count': len(contratti),
        'livelli': livelli,
        'comuni': comuni,
        'tipi_progetto': tipi_progetto,
        'oggi': oggi,
        'mese_corr': oggi.month,
        'anno_corr': oggi.year,
        'mese_prec': oggi.month - 1 if oggi.month > 1 else 12,
        'anno_prec': oggi.year if oggi.month > 1 else oggi.year - 1,
        'mese_succ': oggi.month + 1 if oggi.month < 12 else 1,
        'anno_succ': oggi.year if oggi.month < 12 else oggi.year + 1,
    })


@login_required
@permesso_richiesto('contratti.modifica')
@require_http_methods(['POST'])
def ajax_rinnova_massivo(request):
    """Esegue rinnovo massivo contratti."""
    import json
    from datetime import date as dt_date

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON non valido.'})

    pk_list = data.get('contratto_pks', [])
    data_rinnovo_str = data.get('data_rinnovo', '')
    data_fine_str = data.get('data_fine', '')

    if not pk_list:
        return JsonResponse({'success': False, 'error': 'Nessun contratto selezionato.'})
    if not data_rinnovo_str:
        return JsonResponse({'success': False, 'error': 'Data rinnovo obbligatoria.'})

    try:
        data_rinnovo = dt_date.fromisoformat(data_rinnovo_str)
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Data rinnovo non valida.'})

    data_fine = None
    if data_fine_str:
        try:
            data_fine = dt_date.fromisoformat(data_fine_str)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Data fine non valida.'})

    successi = 0
    fallimenti = []

    for pk in pk_list:
        try:
            originale = ContrattoLavoro.objects.get(pk=pk, stato='ATTIVO')
        except ContrattoLavoro.DoesNotExist:
            fallimenti.append({'pk': pk, 'motivo': 'Contratto non trovato o non attivo.'})
            continue

        try:
            nuovo = ContrattoLavoro()
            for f in ContrattoLavoro._meta.get_fields():
                name = f.name
                if f.auto_created or name == 'id':
                    continue
                if f.one_to_many or f.many_to_many:
                    continue
                if name in ('contratto_rinnovato_da',):
                    continue
                setattr(nuovo, name, getattr(originale, name))

            nuovo.data_assunzione = data_rinnovo
            if data_fine:
                nuovo.data_fine = data_fine
                nuovo.tipo_contratto = 'DETERMINATO'
            else:
                nuovo.data_fine = None
            nuovo.stato = 'ATTIVO'
            nuovo.codice_rapporto_inps = ''
            nuovo.contratto_rinnovato_da = originale
            nuovo.contributi_trimestre_versati = False

            ultimo_ccnl = ParametriCCNL.objects.filter(
                livello=originale.parametri_minimi.livello
            ).order_by('-anno').first()
            if ultimo_ccnl:
                nuovo.parametri_minimi = ultimo_ccnl

            nuovo.save()
            nuovo.progetto.set(originale.progetto.all())
            successi += 1
        except Exception as e:
            logger.exception("Errore rinnovo contratto pk=%s", pk)
            fallimenti.append({'pk': pk, 'motivo': str(e)})

    return JsonResponse({
        'success': True,
        'successi': successi,
        'fallimenti': fallimenti,
    })
