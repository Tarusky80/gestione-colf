from paghe.views._common_imports import *
from paghe.models import RichiestaModificaDatore


@login_required
def richieste_modifica_list(request):
    stato_f = request.GET.get('stato', '')
    mostra_eliminate = request.GET.get('eliminate', '') == '1'
    qs = RichiestaModificaDatore.objects.select_related(
        'datore', 'contratto', 'contratto__lavoratore'
    ).order_by('-creato_il')
    if not mostra_eliminate:
        qs = qs.filter(eliminata=False)
    if stato_f:
        qs = qs.filter(stato=stato_f)
    return render(request, 'paghe/richieste_modifica_list.html', {
        'richieste': qs,
        'stato_f': stato_f,
        'mostra_eliminate': mostra_eliminate,
        'opzioni': get_opzioni(),
    })


@login_required
def ajax_conta_richieste_pendenti(request):
    cnt = RichiestaModificaDatore.objects.filter(stato='INVIATA', eliminata=False).count()
    return JsonResponse({'count': cnt})


@login_required
@permesso_richiesto('anagrafiche.modifica')
@require_http_methods(['POST'])
def ajax_admin_gestisci_richiesta(request):
    data = json.loads(request.body)
    pk = data.get('pk')
    nuovo_stato = data.get('stato', '').strip()
    nota_admin = data.get('nota_admin', '').strip()

    if nuovo_stato not in ('VISTA', 'ACCETTATA', 'RIFIUTATA'):
        return JsonResponse({'success': False, 'error': 'Stato non valido.'})

    richiesta = get_object_or_404(RichiestaModificaDatore, pk=pk)
    richiesta.stato = nuovo_stato
    if nota_admin:
        richiesta.nota_admin = nota_admin
    if nuovo_stato in ('ACCETTATA', 'RIFIUTATA'):
        richiesta.gestito_il = timezone.now()
    richiesta.save(update_fields=['stato', 'nota_admin', 'gestito_il'])

    return JsonResponse({'success': True, 'stato': richiesta.stato})


@login_required
@permesso_richiesto('anagrafiche.elimina')
@require_http_methods(['POST'])
def ajax_admin_elimina_richiesta(request):
    data = json.loads(request.body)
    pk = data.get('pk')
    richiesta = get_object_or_404(RichiestaModificaDatore, pk=pk)
    richiesta.eliminata = True
    richiesta.data_eliminazione = timezone.now()
    richiesta.save(update_fields=['eliminata', 'data_eliminazione'])
    return JsonResponse({'success': True, 'message': 'Richiesta eliminata.'})


@login_required
@require_http_methods(['POST'])
def ajax_admin_ripristina_richiesta(request):
    data = json.loads(request.body)
    pk = data.get('pk')
    richiesta = get_object_or_404(RichiestaModificaDatore, pk=pk)
    richiesta.eliminata = False
    richiesta.data_eliminazione = None
    richiesta.save(update_fields=['eliminata', 'data_eliminazione'])
    return JsonResponse({'success': True, 'message': 'Richiesta ripristinata.'})
