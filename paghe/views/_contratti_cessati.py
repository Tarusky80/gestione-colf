"""Modulo _contratti_cessati - generato automaticamente da views.py"""

from paghe.views._common_imports import *

logger = logging.getLogger(__name__)

from paghe.views._helpers import _get_tabella_conf




# --- contratti_cessati_list ---
@login_required
@permesso_richiesto('contratti.vedi')
@never_cache
def contratti_cessati_list(request):
    opzioni = get_opzioni()
    cessati = filtro_visibilita(ContrattoLavoro.objects.exclude(stato='ATTIVO'), request.user).order_by('-data_assunzione')
    return render(request, 'paghe/contratti_cessati_list.html', {'opzioni': opzioni, 'contratti': cessati, 'count': cessati.count()})


# --- ajax_riattiva_contratto ---
@login_required
@permesso_richiesto('contratti.modifica')
def ajax_riattiva_contratto(request, pk):
    if request.method == 'POST':
        contratto = get_object_or_404(ContrattoLavoro, pk=pk)
        contratto.stato = 'ATTIVO'
        contratto.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'message': 'Richiesta non valida'})


# --- eliminati_list ---
@login_required
@permesso_richiesto('anagrafiche.vedi')
@never_cache
def eliminati_list(request):
    from django.core.paginator import Paginator
    opzioni = get_opzioni()
    records = RecordEliminato.objects.all().order_by('-eliminato_il')
    paginator = Paginator(records, 100)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    return render(request, 'paghe/eliminati_list.html', {
        'opzioni': opzioni,
        'records': page_obj.object_list,
        'page_obj': page_obj,
    })


# --- ajax_vedi_eliminato ---
@login_required
@permesso_richiesto('anagrafiche.vedi')
def ajax_vedi_eliminato(request, pk):
    record = get_object_or_404(RecordEliminato, pk=pk)
    fields = {}
    model_name = None

    # Gestisce entrambi i formati: nuovo [{'model':..., 'fields':{...}}] e vecchio {field: value}
    raw = record.dati
    if isinstance(raw, list) and raw and isinstance(raw[0], dict):
        model_name = raw[0].get('model', '')
        fields = dict(raw[0].get('fields', {}))
    elif isinstance(raw, dict):
        fields = dict(raw)

    # Risolvi FK e M2M ai nomi leggibili
    if model_name and '.' in model_name:
        try:
            app_label, model_cls_name = model_name.split('.')
            from django.contrib.contenttypes.models import ContentType
            ct = ContentType.objects.get(app_label=app_label, model=model_cls_name)
            model_class = ct.model_class()
            if model_class:
                for field in model_class._meta.get_fields():
                    if isinstance(field, models.ForeignKey) and field.name in fields:
                        pk_val = fields[field.name]
                        if pk_val is not None:
                                try:
                                    related_obj = field.related_model.objects.get(pk=pk_val)
                                    fields[field.name] = str(related_obj)
                                except Exception:
                                    logger.warning("FK (ct) %s pk=%s non risolvibile per record %s", field.name, pk_val, record.pk)
                                    fields[field.name] = f'#{pk_val}'
                    elif isinstance(field, models.ManyToManyField) and field.name in fields:
                        pk_list = fields[field.name]
                        if isinstance(pk_list, (list, tuple)) and pk_list:
                            nomi = []
                            for pk_val in pk_list:
                                try:
                                    related_obj = field.related_model.objects.get(pk=pk_val)
                                    nomi.append(str(related_obj))
                                except Exception:
                                    logger.warning("M2M (ct) %s pk=%s non risolvibile per record %s", field.name, pk_val, record.pk)
                                    nomi.append(f'#{pk_val}')
                            fields[field.name] = ', '.join(nomi)
                        elif pk_list:
                            fields[field.name] = str(pk_list)
        except Exception:
            logger.warning("Impossibile deserializzare record %s (ContentType)", record.pk)

    # Per vecchi record (formato flat dict), prova a risolvere i FK via model dai campi
    elif isinstance(raw, dict):
        try:
            from paghe.models import ContrattoLavoro, DatoreLavoro, Lavoratore, Beneficiario, ProgettoRegionale, ParametriCCNL, Livello, TabellaCasse, TabellaContributiINPS, TabellaMalattia, TabellaScattiAnzianita, TipoProgettoRegionale
            MODEL_MAP = {}
            for m in [ContrattoLavoro, DatoreLavoro, Lavoratore, Beneficiario, ProgettoRegionale, ParametriCCNL, Livello, TabellaCasse, TabellaContributiINPS, TabellaMalattia, TabellaScattiAnzianita, TipoProgettoRegionale]:
                MODEL_MAP[m._meta.model_name] = m
            tipo_map = {
                'datore': 'datorelavoro', 'lavoratore': 'lavoratore',
                'beneficiario': 'beneficiario', 'contratto': 'contrattolavoro',
            }
            model_cls_name = tipo_map.get(record.tipo, record.tipo)
            if model_cls_name in MODEL_MAP:
                mc = MODEL_MAP[model_cls_name]
                for field in mc._meta.get_fields():
                    if isinstance(field, models.ForeignKey) and field.name in fields:
                        pk_val = fields[field.name]
                        if pk_val is not None and pk_val != '':
                            try:
                                related_obj = field.related_model.objects.get(pk=pk_val)
                                fields[field.name] = str(related_obj)
                            except Exception:
                                logger.warning("FK (model_map) %s pk=%s non risolvibile per record %s", field.name, pk_val, record.pk)
                                fields[field.name] = f'#{pk_val}'
                    elif isinstance(field, models.ManyToManyField) and field.name in fields:
                        pk_list = fields[field.name]
                        if isinstance(pk_list, (list, tuple)) and pk_list:
                            nomi = []
                            for pk_val in pk_list:
                                try:
                                    related_obj = field.related_model.objects.get(pk=pk_val)
                                    nomi.append(str(related_obj))
                                except Exception:
                                    logger.warning("M2M %s pk=%s non risolvibile (record flat %s)", field.name, pk_val, record.pk)
                                    nomi.append(f'#{pk_val}')
                            fields[field.name] = ', '.join(nomi)
        except Exception:
            logger.warning("Impossibile deserializzare record flat %s", record.pk)

    return JsonResponse({
        'success': True,
        'tipo': record.get_tipo_display(),
        'descrizione': record.descrizione,
        'dati': fields,
        'eliminato_il': record.eliminato_il.strftime('%d/%m/%Y %H:%M'),
    })


# --- ajax_ripristina_eliminato ---
@login_required
@permesso_richiesto('anagrafiche.modifica')
@require_http_methods(["POST"])
def ajax_ripristina_eliminato(request, pk):
    record = get_object_or_404(RecordEliminato, pk=pk)
    # Ricostruisci il record dal JSON salvato
    # Verifica che il tipo sia supportato (la deserialize usa il model dal dato salvato)
    if not (ANAGRAFICA_MAP.get(record.tipo) or _get_tabella_conf(record.tipo) or record.tipo == 'contratto'):
        return JsonResponse({'success': False, 'message': 'Tipo non ripristinabile'})
    # Ricostruisci usando deserialize per gestire date, decimal, FK automaticamente
    data_json = json.dumps(record.dati)
    for deserialized in serializers.deserialize('json', data_json):
        deserialized.object.pk = None  # Forza nuova PK
        deserialized.save()
    record.delete()
    return JsonResponse({'success': True, 'message': f'{record.get_tipo_display()} "{record.descrizione}" ripristinato con successo.'})


# --- ajax_elimina_eliminato ---
@login_required
@permesso_richiesto('anagrafiche.elimina')
@require_http_methods(["POST"])
def ajax_elimina_eliminato(request, pk):
    record = get_object_or_404(RecordEliminato, pk=pk)
    record.delete()
    return JsonResponse({'success': True, 'message': 'Record eliminato definitivamente.'})


# --- ajax_ripristina_tutti_eliminati ---
@login_required
@permesso_richiesto('anagrafiche.modifica')
@require_http_methods(["POST"])
def ajax_ripristina_tutti_eliminati(request):
    records = RecordEliminato.objects.all()
    ripristinati = 0
    for record in records:
        if not (ANAGRAFICA_MAP.get(record.tipo) or _get_tabella_conf(record.tipo) or record.tipo == 'contratto'):
            continue
        data_json = json.dumps(record.dati)
        for deserialized in serializers.deserialize('json', data_json):
            deserialized.object.pk = None
            deserialized.save()
        record.delete()
        ripristinati += 1
    return JsonResponse({'success': True, 'message': f'{ripristinati} record ripristinati con successo.'})


# --- ajax_elimina_tutti_eliminati ---
@login_required
@permesso_richiesto('anagrafiche.elimina')
@require_http_methods(["POST"])
def ajax_elimina_tutti_eliminati(request):
    count = RecordEliminato.objects.count()
    RecordEliminato.objects.all().delete()
    return JsonResponse({'success': True, 'message': f'{count} record eliminati definitivamente.'})
