"""Modulo _dashboard - generato automaticamente da views.py"""

import json
from pathlib import Path

from paghe.views._common_imports import *
from paghe.views._helpers import _cerca_comune_per_nome



# --- about_page ---
@login_required
def about_page(request):
    """Pagina About con crediti e tecnologie."""
    from importlib.metadata import version as _v
    opzioni = get_opzioni()
    vers = {}
    for pip_name, tmpl_key in [
        ('APScheduler', 'APScheduler'),
        ('bleach', 'bleach'),
        ('chromedriver-autoinstaller', 'chromedriver_autoinstaller'),
        ('cryptography', 'cryptography'),
        ('Django', 'Django'),
        ('django-import-export', 'django_import_export'),
        ('openpyxl', 'openpyxl'),
        ('Pillow', 'Pillow'),
        ('playwright', 'playwright'),
        ('pypdf', 'pypdf'),
        ('reportlab', 'reportlab'),
        ('requests', 'requests'),
        ('selenium', 'selenium'),
        ('xhtml2pdf', 'xhtml2pdf'),
    ]:
        try:
            vers[tmpl_key] = _v(pip_name)
        except Exception:
            vers[tmpl_key] = '—'
    return render(request, 'paghe/about.html', {'opzioni': opzioni, 'vers': vers})


# --- _prossime_scadenze ---
def _prossime_scadenze():
    oggi = date.today()
    eventi = []
    trim_fine = [3, 6, 9, 12]
    for mf in trim_fine:
        scad = date(oggi.year, mf, 10) if mf < 12 else date(oggi.year, 12, 10)
        if mf == 3: scad = date(oggi.year, 4, 10)
        elif mf == 6: scad = date(oggi.year, 7, 10)
        elif mf == 9: scad = date(oggi.year, 10, 10)
        elif mf == 12: scad = date(oggi.year + 1, 1, 10)
        if scad >= oggi:
            giorni = (scad - oggi).days
            trim_nome = {3: '1° trimestre', 6: '2° trimestre', 9: '3° trimestre', 12: '4° trimestre'}[mf]
            eventi.append({'data': scad, 'label': f'Contributi {trim_nome}', 'tipo': 'contributi',
                           'giorni_mancanti': giorni, 'urgenza': 'rossa' if giorni <= 7 else 'arancione' if giorni <= 30 else 'gialla'})
    f24 = date(oggi.year, 11, 30)
    if f24 >= oggi:
        giorni = (f24 - oggi).days
        eventi.append({'data': f24, 'label': 'F24 — Seconda rata', 'tipo': 'f24',
                       'giorni_mancanti': giorni, 'urgenza': 'rossa' if giorni <= 7 else 'arancione' if giorni <= 30 else 'gialla'})
    cu_scad = date(oggi.year, 10, 31)
    if cu_scad >= oggi:
        giorni = (cu_scad - oggi).days
        eventi.append({'data': cu_scad, 'label': 'Scadenza invio CU', 'tipo': 'cu',
                       'giorni_mancanti': giorni, 'urgenza': 'rossa' if giorni <= 7 else 'arancione' if giorni <= 30 else 'gialla'})
    eventi.sort(key=lambda e: e['giorni_mancanti'])
    return eventi


# --- _build_dashboard_stats ---
def _build_dashboard_stats(opzioni, contratti_attivi_qs, oggi, totale_attivi):
    stats = {}
    stats['contratti_per_comune'] = list(contratti_attivi_qs
        .values('datore__comune').annotate(count=Count('id')).order_by('-count')[:5])
    tipi = list(contratti_attivi_qs.values('tipo_contratto').annotate(count=Count('id')))
    stats['tipi'] = tipi
    stats['conviventi'] = contratti_attivi_qs.filter(is_convivente=True).count()
    stats['non_conviventi'] = totale_attivi - stats['conviventi']
    progetti_data = []
    for tipo in TipoProgettoRegionale.objects.all():
        cnt = contratti_attivi_qs.filter(progetto__tipo=tipo).distinct().count()
        progetti_data.append({'nome': tipo.nome, 'count': cnt, 'colore': tipo.colore})
    stats['progetti_data'] = progetti_data
    con_progetto = contratti_attivi_qs.annotate(prog=Count('progetto')).filter(prog__gt=0).count()
    stats['con_progetto'] = con_progetto
    stats['senza_progetto'] = totale_attivi - con_progetto
    budget_totale = ProgettoRegionale.objects.aggregate(totale=Sum('budget_mensile'))['totale'] or 0
    stats['budget_totale'] = budget_totale
    stats['budget_medio'] = round(budget_totale / con_progetto, 2) if con_progetto > 0 else 0
    stats['ore_totali'] = contratti_attivi_qs.aggregate(totale=Sum('ore_calcolate'))['totale'] or 0
    ore_tipo_map = {}
    for contratto in contratti_attivi_qs.prefetch_related('progetto__tipo'):
        ore = float(contratto.ore_calcolate or 0)
        if ore <= 0:
            continue
        progetti = list(contratto.progetto.all())
        if not progetti:
            continue
        gruppi = {}
        for p in progetti:
            tn = p.tipo.nome if p.tipo else 'N/D'
            gruppi.setdefault(tn, {'budget': 0.0, 'colore': p.tipo.colore or '#8A8F98'})
            gruppi[tn]['budget'] += float(p.budget_mensile or 0)
        bgtot = sum(g['budget'] for g in gruppi.values())
        for tn, g in gruppi.items():
            quota = g['budget'] / bgtot if bgtot > 0 else 1.0 / max(len(gruppi), 1)
            ore_tipo_map.setdefault(tn, {'ore': 0.0, 'colore': g['colore']})
            ore_tipo_map[tn]['ore'] += ore * quota
    stats['ore_per_tipo'] = sorted(
        [{'nome': k, 'ore': round(v['ore']), 'colore': v['colore']} for k, v in ore_tipo_map.items()],
        key=lambda x: x['ore'], reverse=True)
    stats['budget_per_tipo'] = list(ProgettoRegionale.objects
        .values('tipo__nome', 'tipo__colore').annotate(totale=Sum('budget_mensile')).order_by('-totale'))
    stats['livelli'] = list(contratti_attivi_qs
        .values('parametri_minimi__livello__codice', 'parametri_minimi__livello__colore')
        .annotate(count=Count('id')).order_by('parametri_minimi__livello__codice'))
    tra_30gg = oggi + timedelta(days=30)
    tra_60gg = oggi + timedelta(days=60)
    tra_90gg = oggi + timedelta(days=90)
    stats['contratti_in_scadenza'] = ContrattoAttivo.objects.filter(
        progetto__data_fine__gte=oggi, progetto__data_fine__lte=tra_30gg).distinct().count()
    scad_30gg = ContrattoAttivo.objects.filter(
        data_fine__gte=oggi, data_fine__lte=tra_30gg).select_related('datore', 'lavoratore').order_by('data_fine')
    scad_60gg = ContrattoAttivo.objects.filter(
        data_fine__gte=oggi, data_fine__lte=tra_60gg).select_related('datore', 'lavoratore').order_by('data_fine')
    scad_90gg = ContrattoAttivo.objects.filter(
        data_fine__gte=oggi, data_fine__lte=tra_90gg).select_related('datore', 'lavoratore').order_by('data_fine')
    stats['contratti_scadenza_30gg_count'] = scad_30gg.count()
    stats['contratti_scadenza_60gg_count'] = scad_60gg.count()
    stats['contratti_scadenza_90gg_count'] = scad_90gg.count()
    stats['contratti_scadenza_30gg_items'] = list(scad_30gg[:15])
    stats['contratti_scadenza_90gg_items'] = list(scad_90gg[:15])
    return stats


# --- _build_alert_panel ---
def _build_alert_panel(contratti_attivi_qs, oggi):
    alerts = {}
    scaduti_qs = ContrattoAttivo.objects.filter(progetto__data_fine__lt=oggi).distinct()
    alerts['scaduti_count'] = scaduti_qs.count()
    alerts['scaduti_items'] = list(scaduti_qs.select_related('datore', 'lavoratore').prefetch_related('progetto')[:20])
    alerts['nuovi_mese'] = contratti_attivi_qs.filter(
        data_assunzione__year=oggi.year, data_assunzione__month=oggi.month).count()
    senza_budget_qs = contratti_attivi_qs.annotate(
        prog_count=Count('progetto'), budget_sum=Sum('progetto__budget_mensile')
    ).filter(Q(prog_count=0) | Q(budget_sum=0) | Q(budget_sum__isnull=True))
    alerts['senza_budget_count'] = senza_budget_qs.count()
    alerts['senza_budget_items'] = list(senza_budget_qs.select_related('datore', 'lavoratore')[:20])
    alerts['datori_incompleti'] = DatoreLavoro.objects.filter(
        Q(comune='') | Q(indirizzo='') | Q(email__isnull=True) | Q(telefono__isnull=True)).count()
    alerts['lavoratori_incompleti'] = Lavoratore.objects.filter(
        Q(comune='') | Q(indirizzo='') | Q(email__isnull=True) | Q(telefono__isnull=True)).count()
    totale_anag = DatoreLavoro.objects.count() + Lavoratore.objects.count()
    incomplete = alerts['datori_incompleti'] + alerts['lavoratori_incompleti']
    alerts['anagrafiche_complete_pct'] = round((totale_anag - incomplete) / totale_anag * 100) if totale_anag > 0 else 100
    mese = oggi.month
    if mese <= 3:
        trimestre, scad_mese, inizio_t = 1, 4, date(oggi.year, 1, 1)
    elif mese <= 6:
        trimestre, scad_mese, inizio_t = 2, 7, date(oggi.year, 4, 1)
    elif mese <= 9:
        trimestre, scad_mese, inizio_t = 3, 10, date(oggi.year, 7, 1)
    else:
        trimestre, scad_mese, inizio_t = 4, 1, date(oggi.year, 10, 1)
    prossima_scad = date(oggi.year + 1, 1, 10) if trimestre == 4 else date(oggi.year, scad_mese, 10)
    if oggi > prossima_scad:
        if trimestre == 4:
            prossima_scad = date(oggi.year + 1, 4, 10)
        else:
            mesi_map = {1: 4, 2: 7, 3: 10, 4: 1}
            trimestre += 1
            prossima_scad = date(oggi.year if trimestre != 4 else oggi.year + 1, mesi_map[trimestre], 10)
    alerts['prossima_scadenza'] = prossima_scad
    trim_parz = contratti_attivi_qs.filter(data_assunzione__gt=inizio_t)
    alerts['trimestre_parziale_count'] = trim_parz.count()
    alerts['trimestre_parziale_items'] = list(trim_parz.select_related('datore', 'lavoratore')[:20])
    alerts['trimestre_parziale_mese'] = inizio_t
    MESI_ITA = ['','gennaio','febbraio','marzo','aprile','maggio','giugno',
                'luglio','agosto','settembre','ottobre','novembre','dicembre']
    nome_mese = MESI_ITA[oggi.month]
    contratti_con_patrono = []
    for c in contratti_attivi_qs.select_related('datore', 'lavoratore'):
        comune = c.datore.comune or ''
        if not comune:
            continue
        info = _cerca_comune_per_nome(comune)
        if not info:
            continue
        pd = info.get('patrono_data', '') or ''
        pn = info.get('patrono_nome', '') or ''
        if pn and pd and nome_mese in pd.lower():
            contratti_con_patrono.append({
                'datore': c.datore.nome_cognome,
                'lavoratore': c.lavoratore.nome_cognome,
                'patrono': f"{pn} ({pd})",
            })
    alerts['patrono_count'] = len(contratti_con_patrono)
    alerts['contratti_con_patrono'] = contratti_con_patrono
    return alerts


# --- _build_checklist_grafici ---
def _build_checklist_grafici(contratti_attivi_qs, opzioni, oggi, totale_attivi, tipi):
    charts = {}
    scostamento_items = []
    latest_busta_subq = BustaPaga.objects.filter(
        contratto=OuterRef('pk'),
        stato__in=['APPROVATA', 'ARCHIVIATA']
    ).order_by('-anno', '-mese').annotate(
        _costo=F('totale_lordo') + F('totale_contributi')
    ).values('_costo')[:1]
    qs = contratti_attivi_qs.annotate(
        _costo_reale=Subquery(latest_busta_subq, output_field=FloatField())
    )
    for c in qs:
        costo = c._costo_reale
        if costo is None:
            continue
        budget = float(c.budget_di_partenza)
        if budget > 0:
            scost = abs(costo - budget) / budget * 100
            if scost > 10:
                scostamento_items.append({
                    'contratto': c, 'budget': budget, 'costo': costo,
                    'scostamento_pct': round(scost, 1), 'eccesso': costo > budget,
                })
    charts['scostamento_count'] = len(scostamento_items)
    charts['scostamento_items'] = scostamento_items
    anno_cu = oggi.year
    charts['buste_bozze'] = BustaPaga.objects.filter(contratto__in=contratti_attivi_qs, anno=anno_cu, stato='BOZZA').count()
    charts['buste_approvate'] = BustaPaga.objects.filter(contratto__in=contratti_attivi_qs, anno=anno_cu, stato='APPROVATA').count()
    charts['buste_archiviate'] = BustaPaga.objects.filter(contratto__in=contratti_attivi_qs, anno=anno_cu, stato='ARCHIVIATA').count()
    charts['contratti_con_cu'] = CUAnnuale.objects.filter(contratto__in=contratti_attivi_qs, anno=anno_cu).values('contratto').distinct().count()
    charts['contratti_senza_cu'] = totale_attivi - charts['contratti_con_cu']
    charts['contratti_contributi_versati'] = contratti_attivi_qs.filter(contributi_trimestre_versati=True).count()
    charts['contratti_contributi_da_versare'] = totale_attivi - charts['contratti_contributi_versati']

    from django.db.models.functions import TruncMonth
    ultimi_12 = oggi - timedelta(days=365)
    ass_map = {}
    for entry in (ContrattoLavoro.objects.filter(data_assunzione__gte=ultimi_12)
                  .annotate(mese=TruncMonth('data_assunzione'))
                  .values('mese').annotate(count=Count('id')).order_by('mese')):
        m = entry['mese'].strftime('%b %y') if entry['mese'] else ''
        ass_map[m] = entry['count']
    cess_map = {}
    for entry in (ProgettoRegionale.objects.filter(data_fine__gte=ultimi_12)
                  .annotate(mese=TruncMonth('data_fine'))
                  .values('mese').annotate(count=Count('id', distinct=True)).order_by('mese')):
        m = entry['mese'].strftime('%b %y') if entry['mese'] else ''
        cess_map[m] = entry['count']
    mesi_labels = sorted(set(list(ass_map.keys()) + list(cess_map.keys())), key=lambda x: x)
    charts['mesi_labels'] = mesi_labels
    charts['mesi_counts'] = [ass_map.get(m, 0) for m in mesi_labels]
    charts['cessazioni_counts'] = [cess_map.get(m, 0) for m in mesi_labels]
    charts['contratti_cessati_mese'] = ContrattoLavoro.objects.filter(
        data_fine__year=oggi.year, data_fine__month=oggi.month).count()
    charts['budget_utilizzato'] = round(sum(float(c.budget_di_partenza or 0) for c in contratti_attivi_qs), 0)
    buste_totali_anno = BustaPaga.objects.filter(anno=oggi.year).count()
    buste_arch_anno = BustaPaga.objects.filter(anno=oggi.year, stato='ARCHIVIATA').count()
    charts['buste_archiviate_pct'] = round(buste_arch_anno / max(buste_totali_anno, 1) * 100)
    prossime_list = _prossime_scadenze()
    charts['prossima_scadenza_label'] = prossime_list[0]['label'] if prossime_list else '—'
    charts['prossimi_giorni'] = prossime_list[0]['giorni_mancanti'] if prossime_list else 0
    charts['buste_mese_corrente'] = BustaPaga.objects.filter(anno=oggi.year, mese=oggi.month).count()
    charts['buste_mese_mancanti'] = max(0, totale_attivi - charts['buste_mese_corrente'])
    ore_mesi_labels = []
    ore_mesi_data = []
    ore_lookup = {}
    for b in BustaPaga.objects.filter(stato='ARCHIVIATA').values('anno', 'mese').annotate(totale_ore=Sum('ore_mensili')).order_by('anno', 'mese'):
        ore_lookup[(b['anno'], b['mese'])] = float(b['totale_ore'] or 0)
    for i in range(11, -1, -1):
        d = oggi - timedelta(days=30 * i)
        ore_mesi_labels.append(f'{d.strftime("%b")} {d.year}')
        ore_mesi_data.append(ore_lookup.get((d.year, d.month), 0))
    charts['ore_mesi_labels'] = ore_mesi_labels
    charts['ore_mesi_data'] = ore_mesi_data
    tipo_map = {t['tipo_contratto']: t['count'] for t in tipi}
    charts['tipologia_labels'] = []
    charts['tipologia_data'] = []
    charts['tipologia_colori'] = []
    for label, colore in [('INDETERMINATO', '#5E6AD2'), ('DETERMINATO', '#f59e0b')]:
        cnt = tipo_map.get(label, 0)
        charts['tipologia_labels'].append(label.capitalize())
        charts['tipologia_data'].append(cnt)
        charts['tipologia_colori'].append(colore)
    geo_qs = contratti_attivi_qs.values('datore__comune').annotate(count=Count('id')).order_by('-count')[:10]
    charts['geo_labels'] = [g['datore__comune'] or '(Sconosciuto)' for g in geo_qs]
    charts['geo_data'] = [g['count'] for g in geo_qs]
    return charts


# --- dashboard ---
@login_required
@never_cache
def dashboard(request):
    opzioni = get_opzioni()
    contratti_attivi_qs = ContrattoAttivo.objects.filter(stato='ATTIVO').select_related('parametri_minimi__livello').prefetch_related('progetto')
    totale_attivi = contratti_attivi_qs.count()
    oggi = date.today()

    stats = _build_dashboard_stats(opzioni, contratti_attivi_qs, oggi, totale_attivi)
    alerts = _build_alert_panel(contratti_attivi_qs, oggi)
    charts = _build_checklist_grafici(contratti_attivi_qs, opzioni, oggi, totale_attivi, stats['tipi'])

    totale_alert = (
        alerts['scaduti_count'] + stats['contratti_in_scadenza'] +
        (1 if alerts['nuovi_mese'] > 0 else 0) + stats['senza_progetto'] +
        alerts['senza_budget_count'] +
        (1 if alerts['datori_incompleti'] > 0 or alerts['lavoratori_incompleti'] > 0 else 0) +
        (1 if alerts['trimestre_parziale_count'] > 0 else 0) + alerts['patrono_count']
    )

    context = dict(opzioni=opzioni, totale_attivi=totale_attivi, totale_alert=totale_alert)
    context.update(stats)
    context.update(alerts)
    context.update(charts)
    context['datori_count'] = DatoreLavoro.objects.count()
    context['lavoratori_count'] = Lavoratore.objects.count()
    context['beneficiari_count'] = Beneficiario.objects.count()
    context['contratti'] = (contratti_attivi_qs
        .select_related('datore', 'lavoratore', 'parametri_minimi__livello')
        .prefetch_related('progetto__tipo', 'progetto__beneficiario')
        .order_by('-data_assunzione')[:10])
    context['mese_corr'] = oggi.month
    context['anno_corr'] = oggi.year
    context['mese_prec'] = oggi.month - 1 if oggi.month > 1 else 12
    context['anno_prec'] = oggi.year if oggi.month > 1 else oggi.year - 1
    context['mese_succ'] = oggi.month + 1 if oggi.month < 12 else 1
    context['anno_succ'] = oggi.year if oggi.month < 12 else oggi.year + 1
    context['tfr_annuale_totale'] = sum(
        float(c.proiezione_tfr_annuale) for c in contratti_attivi_qs
    )
    ub = GestoreBackup.objects.order_by('-data_creazione').first()
    context['ultimo_backup'] = ub
    context['backup_fresco'] = ub and (oggi - ub.data_creazione.date()).days < 1
    context['backup_recente'] = ub and (oggi - ub.data_creazione.date()).days < 7
    context['prossime_scadenze'] = _prossime_scadenze()
    context['agenda_prossimi'] = Appuntamento.objects.filter(
        data__gte=oggi, completato=False).order_by('data', 'pk')[:7]
    context['ultimi_documenti'] = DocumentoArchiviato.objects.order_by('-creato_il')[:5]
    context['comuni_beneficiari'] = Beneficiario.objects.exclude(comune='').values_list(
        'comune', flat=True).distinct().order_by('comune')
    context['voci_recenti'] = request.session.get('voci_recenti', [])
    context['documenti_per_tipo'] = list(DocumentoArchiviato.objects.values('tipo').annotate(count=__import__('django').db.models.Count('pk')).order_by('-count')[:8])
    context['contributi_mensili'] = _contributi_mensili_trend()
    return render(request, 'paghe/dashboard.html', context)


def _contributi_mensili_trend():
    from datetime import date, timedelta
    from django.db.models import Sum
    from paghe.models import BustaPaga
    oggi = date.today()
    mesi = []
    for i in range(11, -1, -1):
        m = oggi.month - i
        a = oggi.year
        while m < 1: m += 12; a -= 1
        while m > 12: m -= 12; a += 1
        qs = BustaPaga.objects.filter(mese=m, anno=a)
        totale = qs.aggregate(tot=Sum('contributi_inps_totale'))['tot'] or 0
        mesi.append({'mese': m, 'anno': a, 'totale': float(totale)})
    return mesi

# --- global_search_view ---

def _fv(queryset, request):
    """Helper per applicare filtro_visibilita se il modello ha il campo."""
    from django.core.exceptions import FieldDoesNotExist
    try:
        queryset.model._meta.get_field('visibile_a')
        return filtro_visibilita(queryset, request.user)
    except FieldDoesNotExist:
        return queryset

SEARCH_CONFIG = [
    {
        'categoria': 'Anagrafiche',
        'queryset': lambda q, request: (
            [{'obj': d, 'icona': 'bi-person-badge', 'colore': '#5E6AD2',
              'modale_titolo': 'Modifica Datore',
              'url': lambda o: f'/ajax/modifica-datore/{o.pk}/'}
             for d in _fv(DatoreLavoro.objects.filter(
                 Q(nome_cognome__icontains=q) | Q(codice_fiscale__icontains=q)), request)[:5]] +
            [{'obj': l, 'icona': 'bi-person-workspace', 'colore': '#34d399',
              'modale_titolo': 'Modifica Lavoratore',
              'url': lambda o: f'/ajax/modifica-lavoratore/{o.pk}/'}
             for l in _fv(Lavoratore.objects.filter(
                 Q(nome_cognome__icontains=q) | Q(codice_fiscale__icontains=q)), request)[:5]] +
            [{'obj': b, 'icona': 'bi-person-heart', 'colore': '#f59e0b',
              'modale_titolo': 'Modifica Beneficiario',
              'url': lambda o: f'/ajax/modifica-beneficiario/{o.pk}/'}
             for b in Beneficiario.objects.filter(
                 Q(nome_cognome__icontains=q) | Q(codice_fiscale__icontains=q))[:5]]
        ),
        'titolo': lambda o: o.nome_cognome,
        'sottotitolo': lambda o: o.codice_fiscale,
    },
    {
        'categoria': 'Contratti',
        'queryset': lambda q, request: _fv(ContrattoLavoro.objects.filter(
            Q(datore__nome_cognome__icontains=q) |
            Q(lavoratore__nome_cognome__icontains=q) |
            Q(codice_rapporto_inps__icontains=q)
        ).distinct().select_related('datore', 'lavoratore'), request)[:5],
        'titolo': lambda o: f"{o.datore.nome_cognome} → {o.lavoratore.nome_cognome}",
        'sottotitolo': lambda o: f"{o.get_tipo_contratto_display()} | {o.codice_rapporto_inps or '—'}",
        'icona': 'bi-file-earmark-text', 'colore': '#a78bfa',
        'url': lambda o: f'/ajax/modifica-contratto/{o.pk}/',
        'modale_titolo': 'Modifica Contratto',
    },
    {
        'categoria': 'Documenti',
        'queryset': lambda q, request: DocumentoArchiviato.objects.filter(
            Q(titolo__icontains=q) | Q(note__icontains=q))[:5],
        'titolo': lambda o: o.titolo,
        'sottotitolo': lambda o: f"Documento | {o.creato_il.strftime('%d/%m/%Y')}",
        'icona': 'bi-file-earmark', 'colore': '#06b6d4',
        'url': lambda o: f'/ajax/vedi-documento/{o.pk}/',
        'modale_titolo': 'Dettaglio Documento',
    },
    {
        'categoria': 'Agenda',
        'queryset': lambda q, request: Appuntamento.objects.filter(
            Q(titolo__icontains=q) | Q(descrizione__icontains=q))[:5],
        'titolo': lambda o: o.titolo,
        'sottotitolo': lambda o: f"Agenda | {o.data.strftime('%d/%m/%Y')}",
        'icona': 'bi-calendar-event', 'colore': '#f59e0b',
        'url': lambda o: '/agenda/',
        'tipo_azione': 'link',
    },
    {
        'categoria': 'Richieste Modifica',
        'queryset': lambda q, request: RichiestaModificaDatore.objects.filter(
            eliminata=False
        ).filter(
            Q(datore__nome_cognome__icontains=q) |
            Q(tipo__icontains=q) |
            Q(nota_datore__icontains=q)
        ).select_related('datore')[:5],
        'titolo': lambda o: f"{o.datore.nome_cognome} — {o.get_tipo_display()}",
        'sottotitolo': lambda o: o.campo or o.get_stato_display(),
        'icona': 'bi-chat-dots', 'colore': '#f59e0b',
        'url': lambda o: '/richieste-modifica/',
        'tipo_azione': 'link',
    },
    {
        'categoria': 'Progetti',
        'queryset': lambda q, request: ProgettoRegionale.objects.filter(
            Q(beneficiario__nome_cognome__icontains=q)
        ).select_related('beneficiario', 'tipo')[:5],
        'titolo': lambda o: f"{o.beneficiario.nome_cognome} — {o.tipo}",
        'sottotitolo': lambda o: f"Progetto | Budget: € {o.budget_mensile or 0:.2f}",
        'icona': 'bi-diagram-3', 'colore': '#ec4899',
        'url': lambda o: f'/ajax/modifica-beneficiario/{o.beneficiario.pk}/',
        'modale_titolo': 'Modifica Beneficiario',
    },
    {
        'categoria': 'Anticipi TFR',
        'queryset': lambda q, request: AnticipoTFR.objects.filter(
            Q(contratto__datore__nome_cognome__icontains=q) |
            Q(contratto__lavoratore__nome_cognome__icontains=q) |
            Q(note__icontains=q)
        ).select_related('contratto__datore', 'contratto__lavoratore')[:5],
        'titolo': lambda o: f"€ {o.importo} — {o.contratto.datore.nome_cognome}",
        'sottotitolo': lambda o: f"{o.contratto.lavoratore.nome_cognome} | {o.data}",
        'icona': 'bi-piggy-bank', 'colore': '#ec4899',
        'url': lambda o: f'/ajax/modifica-contratto/{o.contratto.pk}/',
        'modale_titolo': 'Modifica Contratto',
    },
    {
        'categoria': 'CU Annuali',
        'queryset': lambda q, request: CUAnnuale.objects.filter(
            Q(contratto__datore__nome_cognome__icontains=q) |
            Q(contratto__lavoratore__nome_cognome__icontains=q)
        ).select_related('contratto__datore', 'contratto__lavoratore')[:5],
        'titolo': lambda o: f"CU {o.anno} — {o.contratto.datore.nome_cognome}",
        'sottotitolo': lambda o: f"{o.contratto.lavoratore.nome_cognome} | {o.get_modalita_display()}",
        'icona': 'bi-file-earmark-check', 'colore': '#10b981',
        'url': lambda o: f'/ajax/modifica-contratto/{o.contratto.pk}/',
        'modale_titolo': 'Modifica Contratto',
    },
    {
        'categoria': 'Modelli',
        'queryset': lambda q, request: ModelloDocumentale.objects.filter(
            Q(codice__icontains=q) | Q(titolo__icontains=q) | Q(note_interne__icontains=q)
        )[:5],
        'titolo': lambda o: o.titolo or o.codice,
        'sottotitolo': lambda o: f"Modello | {o.get_tipo_display()}",
        'icona': 'bi-file-text', 'colore': '#10b981',
        'url': lambda o: f'/documentale/{o.tipo}/{o.pk}/',
        'tipo_azione': 'link',
    },
    {
        'categoria': 'Modelli Lista',
        'queryset': lambda q, request: ModelloLista.objects.filter(
            Q(nome__icontains=q) | Q(note__icontains=q))[:5],
        'titolo': lambda o: o.nome,
        'sottotitolo': lambda o: f"Lista | {o.get_tipo_sorgente_display()}",
        'icona': 'bi-layout-text-window', 'colore': '#06b6d4',
        'url': lambda o: '/liste/',
        'tipo_azione': 'link',
    },
    {
        'categoria': 'Composizioni',
        'queryset': lambda q, request: ModelloComposizione.objects.filter(
            Q(nome__icontains=q) | Q(note__icontains=q))[:5],
        'titolo': lambda o: o.nome,
        'sottotitolo': lambda o: f"Composizione | {o.note or '—'}",
        'icona': 'bi-layers', 'colore': '#5E6AD2',
        'url': lambda o: '/stampe-invii/',
        'tipo_azione': 'link',
    },
    {
        'categoria': 'Buste Paga',
        'queryset': lambda q, request: BustaPaga.objects.filter(
            Q(contratto__datore__nome_cognome__icontains=q) |
            Q(contratto__lavoratore__nome_cognome__icontains=q)
        ).distinct().select_related('contratto__datore', 'contratto__lavoratore')[:5],
        'titolo': lambda o: f"{o.contratto.datore.nome_cognome} → {o.contratto.lavoratore.nome_cognome}",
        'sottotitolo': lambda o: f"Busta Paga {o.mese}/{o.anno} | {o.get_stato_display()}",
        'icona': 'bi-cash-stack', 'colore': '#f97316',
        'url': lambda o: '/buste-archivio/',
        'tipo_azione': 'link',
    },
]


@login_required
def global_search_view(request):
    query = request.GET.get('q', '').strip()
    results = {}
    if len(query) > 2:
        # --- Prova comandi rapidi ---
        comando, args = _parse_comando_rapido(query)
        if comando:
            items_rapidi = _esegui_comando_rapido(comando, args, request)
            if items_rapidi:
                results['Azioni Rapide'] = items_rapidi
        # --- Ricerca testuale classica (sempre eseguita) ---
        for cfg in SEARCH_CONFIG:
            raw = cfg['queryset'](query, request)
            items = []
            for entry in raw if isinstance(raw, list) else raw:
                if isinstance(entry, dict):
                    obj = entry['obj']
                    url_fn = entry['url'] if 'url' in entry else cfg['url']
                    items.append({
                        'titolo': cfg['titolo'](obj),
                        'sottotitolo': cfg['sottotitolo'](obj),
                        'icona': entry.get('icona', cfg.get('icona', '')),
                        'colore': entry.get('colore', cfg.get('colore', '')),
                        'url': url_fn(obj),
                        'tipo_azione': entry.get('tipo_azione', cfg.get('tipo_azione', 'modale')),
                        'modale_titolo': entry.get('modale_titolo', cfg.get('modale_titolo', '')),
                    })
                else:
                    items.append({
                        'titolo': cfg['titolo'](entry),
                        'sottotitolo': cfg['sottotitolo'](entry),
                        'icona': cfg.get('icona', ''),
                        'colore': cfg.get('colore', ''),
                        'url': cfg['url'](entry),
                        'tipo_azione': cfg.get('tipo_azione', 'modale'),
                        'modale_titolo': cfg.get('modale_titolo', ''),
                    })
            if items:
                results[cfg['categoria']] = items
    totale = sum(len(v) for v in results.values())
    return JsonResponse({'results': results, 'totale': totale})


# === COMANDI RAPIDI ===

_COMANDI_RAPIDI = [
    # (regex, nome_comando, n_argomenti)
    (r'^busta\s+(.+?)\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+(\d{4})$', 'busta', 3),
    (r'^rinnova\s+(.+)$', 'rinnova', 1),
    (r'^contratto\s+(.+)$', 'contratto', 1),
    (r'^scadenza\s+(.+)$', 'scadenza', 1),
    (r'^documento\s+(.+?)\s+(.+)$', 'documento', 2),
    (r'^lul\s+(.+)$', 'lul', 1),
    (r'^(?:apri|vai\s+a|vai\s+)\s+(.+)$', 'apri', 1),
    (r'^report\s+(.+)$', 'report', 1),
]

_MESI_MAP = {
    'gennaio': 1, 'febbraio': 2, 'marzo': 3, 'aprile': 4,
    'maggio': 5, 'giugno': 6, 'luglio': 7, 'agosto': 8,
    'settembre': 9, 'ottobre': 10, 'novembre': 11, 'dicembre': 12,
}


def _parse_comando_rapido(query):
    """Riconosce se la query è un comando rapido. Restituisce (nome, args) o (None, None)."""
    ql = query.strip().lower()
    for pattern, nome, nargs in _COMANDI_RAPIDI:
        m = __import__('re').match(pattern, ql)
        if m:
            return nome, list(m.groups())
    return None, None


def _esegui_comando_rapido(comando, args, request):
    """Esegue il comando e restituisce lista di dict risultato."""
    oggi = __import__('datetime').date.today()
    items = []

    if comando == 'busta':
        # args: [nome_lavoratore, mese_testo, anno]
        nome, mese_testo, anno = args
        mese = _MESI_MAP.get(mese_testo, oggi.month)
        buste = BustaPaga.objects.filter(
            Q(contratto__lavoratore__nome_cognome__icontains=nome) &
            Q(mese=mese, anno=int(anno))
        ).select_related('contratto__datore', 'contratto__lavoratore')[:3]
        for b in buste:
            items.append({
                'titolo': f"Busta {b.mese:02d}/{b.anno} — {b.contratto.lavoratore.nome_cognome}",
                'sottotitolo': f"€ {b.netto:.2f} · {b.get_tipo_calcolo_display()}",
                'icona': 'bi-cash-stack', 'colore': '#f97316',
                'url': '/buste-archivio/',
                'tipo_azione': 'link', 'modale_titolo': '',
            })

    elif comando == 'rinnova':
        query_nome = args[0]
        # Mostra link diretto alla pagina rinnovo
        items.append({
            'titolo': 'Apri Rinnova Contratti',
            'sottotitolo': 'Vai alla pagina di rinnovo massivo',
            'icona': 'bi-arrow-repeat', 'colore': '#a78bfa',
            'url': '/contratti/rinnova-massivo/?q=' + __import__('urllib').parse.quote(query_nome),
            'tipo_azione': 'link', 'modale_titolo': '',
        })

    elif comando == 'contratto':
        query_nome = args[0]
        contratti = _fv(ContrattoLavoro.objects.filter(
            Q(datore__nome_cognome__icontains=query_nome) |
            Q(lavoratore__nome_cognome__icontains=query_nome)
        ).select_related('datore', 'lavoratore'), request)[:3]
        for c in contratti:
            items.append({
                'titolo': f"{c.datore.nome_cognome} → {c.lavoratore.nome_cognome}",
                'sottotitolo': f"{c.get_tipo_contratto_display()} | {c.codice_rapporto_inps or '—'}",
                'icona': 'bi-file-earmark-text', 'colore': '#a78bfa',
                'url': f'/ajax/modifica-contratto/{c.pk}/',
                'tipo_azione': 'modale', 'modale_titolo': 'Modifica Contratto',
            })

    elif comando == 'scadenza':
        query_arg = args[0]
        # Cerca appuntamenti/scadenze
        appuntamenti = Appuntamento.objects.filter(
            Q(titolo__icontains=query_arg) | Q(descrizione__icontains=query_arg)
        ).filter(data__gte=oggi).order_by('data')[:3]
        for a in appuntamenti:
            items.append({
                'titolo': a.titolo,
                'sottotitolo': f"Scadenza: {a.data.strftime('%d/%m/%Y')}",
                'icona': 'bi-calendar-event', 'colore': '#f59e0b',
                'url': '/agenda/',
                'tipo_azione': 'link', 'modale_titolo': '',
            })

    elif comando == 'documento':
        # args: [tipo, nome_lavoratore]
        tipo_doc, nome = args
        docs = DocumentoArchiviato.objects.filter(
            Q(contratto__lavoratore__nome_cognome__icontains=nome) &
            Q(tipo__icontains=tipo_doc)
        ).select_related('contratto__lavoratore')[:3]
        for d in docs:
            items.append({
                'titolo': d.titolo or d.get_tipo_display(),
                'sottotitolo': f"{d.contratto.lavoratore.nome_cognome} | {d.creato_il.strftime('%d/%m/%Y')}",
                'icona': 'bi-file-earmark', 'colore': '#06b6d4',
                'url': f'/ajax/vedi-documento/{d.pk}/',
                'tipo_azione': 'modale', 'modale_titolo': 'Dettaglio Documento',
            })

    elif comando == 'lul':
        query_arg = args[0]
        items.append({
            'titolo': f"Vai a LUL — {query_arg}",
            'sottotitolo': 'Libro Unico del Lavoro',
            'icona': 'bi-journal-text', 'colore': '#10b981',
            'url': '/lul/?q=' + __import__('urllib').parse.quote(query_arg),
            'tipo_azione': 'link', 'modale_titolo': '',
        })

    elif comando == 'apri':
        query_nome = args[0]
        # Cerca in tutte le entità
        models_quick = [
            (DatoreLavoro, '/ajax/modifica-datore/{pk}/', 'Modifica Datore', 'bi-person-badge', '#5E6AD2'),
            (Lavoratore, '/ajax/modifica-lavoratore/{pk}/', 'Modifica Lavoratore', 'bi-person-workspace', '#34d399'),
            (Beneficiario, '/ajax/modifica-beneficiario/{pk}/', 'Modifica Beneficiario', 'bi-person-heart', '#f59e0b'),
        ]
        for model_cls, url_tpl, titolo_modale, icona, colore in models_quick:
            qs = model_cls.objects.filter(nome_cognome__icontains=query_nome)
            objs = _fv(qs, request)[:1]
            for o in objs:
                items.append({
                    'titolo': o.nome_cognome,
                    'sottotitolo': titolo_modale,
                    'icona': icona, 'colore': colore,
                    'url': url_tpl.format(pk=o.pk),
                    'tipo_azione': 'modale', 'modale_titolo': titolo_modale,
                })

    elif comando == 'report':
        query_arg = args[0]
        items.append({
            'titolo': f"Report {query_arg}",
            'sottotitolo': 'Report mensile PDF',
            'icona': 'bi-bar-chart', 'colore': '#5E6AD2',
            'url': f'/report/mensile/?periodo={__import__("urllib").parse.quote(query_arg)}',
            'tipo_azione': 'link', 'modale_titolo': '',
        })

    return items[:5]


# --- mappa_beneficiari_page ---
@login_required
def mappa_beneficiari_page(request):
    comuni = Beneficiario.objects.exclude(comune='').values_list('comune', flat=True).distinct().order_by('comune')
    return render(request, 'paghe/mappa_beneficiari.html', {
        'comuni_beneficiari': comuni,
        'hide_sidebar': True,
    })


# --- ajax_registra_voce_recente ---
@login_required
@require_http_methods(['POST'])
def ajax_registra_voce_recente(request):
    data = json.loads(request.body)
    voci = request.session.get('voci_recenti', [])
    voci = [v for v in voci if v.get('nav_id') != data.get('nav_id')]
    voci.insert(0, data)
    request.session['voci_recenti'] = voci[:6]
    return JsonResponse({'ok': True})


# --- ajax_beneficiari_mappa ---
@login_required
def ajax_beneficiari_mappa(request):
    cache_path = Path(__file__).resolve().parent.parent.parent / 'data' / 'coordinate_beneficiari.json'
    if not cache_path.exists():
        return JsonResponse([], safe=False)

    try:
        cache = json.loads(cache_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return JsonResponse([], safe=False)

    filtro_comune = request.GET.get('comune', '').strip()
    risultati = []
    for cf, data in cache.items():
        if data.get('lat') is None or data.get('lng') is None:
            continue
        if filtro_comune and data.get('comune', '') != filtro_comune:
            continue
        risultati.append({
            'pk': cf,
            'nome': data.get('nome', ''),
            'indirizzo': data.get('indirizzo', ''),
            'comune': data.get('comune', ''),
            'lat': data['lat'],
            'lng': data['lng'],
        })
    return JsonResponse(risultati, safe=False)
