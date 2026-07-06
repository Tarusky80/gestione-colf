from paghe.views._common_imports import *
from paghe.models import AttivitaMensile, CompletamentoMensile
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

ATTIVITA_SEED = [
    ('Genera buste paga mese corrente', 'BUSTE_PAGA', 10, True),
    ('Verifica e approva buste paga', 'BUSTE_PAGA', 20, True),
    ('Archivia buste paga approvate', 'BUSTE_PAGA', 30, False),
    ('Verifica contributi trimestrali', 'CONTRIBUTI', 10, True),
    ('Versamento contributi INPS', 'CONTRIBUTI', 20, True),
    ('Compila foglio presenze', 'BUSTE_PAGA', 5, True),
    ('Controllo scostamenti budget', 'VARIE', 30, False),
    ('Verifica scadenze progetti', 'DOCUMENTI', 10, True),
    ('Invio documenti ai datori', 'DOCUMENTI', 20, False),
    ('Check anagrafiche incomplete', 'VARIE', 50, False),
    ('Backup database', 'VARIE', 60, True),
    ('Verifica PagoPA e bollettini', 'CONTRIBUTI', 30, False),
    ('Prepara Certificazione Unica', 'CU', 10, True),
    ('Invio CU ai datori', 'CU', 20, True),
    ('Verifica email e comunicazioni', 'VARIE', 40, False),
    ('Aggiorna parametri CCNL', 'VARIE', 70, False),
]


def _seed_attivita():
    for label, cat, ordine, obblig in ATTIVITA_SEED:
        AttivitaMensile.objects.get_or_create(
            label=label,
            defaults={'categoria': cat, 'ordine': ordine, 'obbligatorio': obblig},
        )


def _get_or_create_mese(anno, mese):
    _seed_attivita()
    attivita = AttivitaMensile.objects.all()
    for a in attivita:
        CompletamentoMensile.objects.get_or_create(
            attivita=a, anno=anno, mese=mese,
            defaults={'completato': False},
        )


@login_required
@never_cache
def checklist_mensile(request):
    oggi = date.today()
    anno = int(request.GET.get('anno', oggi.year))
    mese = int(request.GET.get('mese', oggi.month))
    if mese < 1:
        mese, anno = 12, anno - 1
    elif mese > 12:
        mese, anno = 1, anno + 1

    _get_or_create_mese(anno, mese)

    completamenti = CompletamentoMensile.objects.filter(
        anno=anno, mese=mese
    ).select_related('attivita', 'completato_da').order_by('attivita__categoria', 'attivita__ordine')

    totale = len(completamenti)
    completati = sum(1 for c in completamenti if c.completato)
    progresso_pct = round(completati / max(totale, 1) * 100)

    MESI_IT = ['', 'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
               'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']

    context = {
        'completamenti': completamenti,
        'totale': totale,
        'completati': completati,
        'progresso_pct': progresso_pct,
        'anno': anno,
        'mese': mese,
        'mese_nome': MESI_IT[mese],
        'prev_mese': mese - 1 or 12,
        'prev_anno': anno - 1 if mese == 1 else anno,
        'next_mese': mese + 1 if mese < 12 else 1,
        'next_anno': anno + 1 if mese == 12 else anno,
        'oggi': oggi,
    }
    return render(request, 'paghe/checklist_mensile.html', context)


@login_required
@require_http_methods(['POST'])
def ajax_checklist_toggle(request, pk):
    c = get_object_or_404(CompletamentoMensile, pk=pk)
    try:
        c.completato = not c.completato
        c.completato_il = timezone.now() if c.completato else None
        c.completato_da = request.user if c.completato else None
        c.save(update_fields=['completato', 'completato_il', 'completato_da'])
        return JsonResponse({'success': True, 'completato': c.completato})
    except Exception as e:
        logger.exception("Errore in ajax_checklist_toggle")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(['POST'])
def ajax_checklist_note(request, pk):
    c = get_object_or_404(CompletamentoMensile, pk=pk)
    try:
        c.note = request.POST.get('note', '')
        c.save(update_fields=['note'])
        return JsonResponse({'success': True})
    except Exception as e:
        logger.exception("Errore in ajax_checklist_note")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_http_methods(['POST'])
def ajax_checklist_reset_mese(request):
    anno = int(request.POST.get('anno'))
    mese = int(request.POST.get('mese'))
    try:
        CompletamentoMensile.objects.filter(anno=anno, mese=mese).delete()
        _get_or_create_mese(anno, mese)
        return JsonResponse({'success': True})
    except Exception as e:
        logger.exception("Errore in ajax_checklist_reset_mese")
        return JsonResponse({'success': False, 'error': str(e)})
