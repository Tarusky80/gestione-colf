from paghe.views._common_imports import *
from paghe.models import AuditLog
from django.contrib.auth.models import User


@login_required
@permesso_richiesto('audit_log')
@never_cache
def audit_log_view(request):
    MODELLI_CHOICES = [
        ('', 'Tutti'),
        ('DatoreLavoro', 'Datori'),
        ('Lavoratore', 'Lavoratori'),
        ('Beneficiario', 'Beneficiari'),
        ('ProgettoRegionale', 'Progetti Regionali'),
        ('ContrattoLavoro', 'Contratti'),
        ('BustaPaga', 'Buste Paga'),
        ('DocumentoArchiviato', 'Documenti'),
        ('OpzioniSoftware', 'Impostazioni'),
        ('Appuntamento', 'Appuntamenti'),
        ('ModelloDocumentale', 'Modelli Documentali'),
        ('ParametriCCNL', 'Parametri CCNL'),
        ('Livello', 'Livelli'),
        ('TabellaCasse', 'Tabella Casse'),
        ('TabellaContributiINPS', 'Contributi INPS'),
        ('TabellaMalattia', 'Malattia'),
        ('TabellaScattiAnzianita', 'Scatti Anzianità'),
        ('TipoProgettoRegionale', 'Tipi Progetto'),
    ]
    AZIONI_CHOICES = [
        ('', 'Tutte'),
        ('CREAZIONE', 'Creazioni'),
        ('MODIFICA', 'Modifiche'),
        ('ELIMINAZIONE', 'Eliminazioni'),
    ]

    modello = request.GET.get('modello', '')
    azione = request.GET.get('azione', '')
    utente_id = request.GET.get('utente', '')
    da = request.GET.get('da', '')
    a = request.GET.get('a', '')
    q = request.GET.get('q', '').strip()

    qs = AuditLog.objects.select_related('utente').all()

    if modello:
        qs = qs.filter(modello_coinvolto=modello)
    if azione:
        qs = qs.filter(azione=azione)
    if utente_id:
        qs = qs.filter(utente_id=utente_id)
    if da:
        qs = qs.filter(data_ora__gte=da)
    if a:
        qs = qs.filter(data_ora__lte=a + ' 23:59:59')
    if q:
        qs = qs.filter(dettagli__icontains=q)

    from django.core.paginator import Paginator
    paginator = Paginator(qs, 50)
    page_num = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_num)

    utenti = User.objects.filter(
        id__in=AuditLog.objects.values_list('utente_id', flat=True).distinct()
    ).order_by('username')

    context = {
        'page_obj': page_obj,
        'modello': modello,
        'azione': azione,
        'utente_id': utente_id,
        'da': da,
        'a': a,
        'q': q,
        'MODELLI_CHOICES': MODELLI_CHOICES,
        'AZIONI_CHOICES': AZIONI_CHOICES,
        'utenti': utenti,
    }
    return render(request, 'paghe/audit_log.html', context)


@login_required
@permesso_richiesto('audit_log')
@require_http_methods(['GET', 'POST'])
def ajax_audit_dettaglio(request, pk):
    log = get_object_or_404(AuditLog, pk=pk)
    return JsonResponse({
        'data_ora': log.data_ora.strftime('%d/%m/%Y %H:%M:%S'),
        'modello': log.modello_coinvolto,
        'pk_oggetto': log.pk_oggetto,
        'azione': log.azione,
        'dettagli': log.dettagli,
        'utente': log.utente.username if log.utente else '—',
        'ip': log.indirizzo_ip or '—',
        'pk': log.pk,
        'dati_prec': log.dati_precedenti,
        'dati_succ': log.dati_successivi,
    })


@login_required
@permesso_richiesto('audit_log')
@require_http_methods(['POST'])
def ajax_audit_elimina(request, pk):
    log = get_object_or_404(AuditLog, pk=pk)
    log.delete()
    return JsonResponse({'ok': True})
