from paghe.views._common_imports import *
from ..models import ScorciatoiaTastiera

MENU_ITEMS = [
    ('nav_dashboard', 'Dashboard', 'grid-1x2-fill', '/dashboard/'),
    ('nav_nuovo_datore', 'Nuovo Datore', 'person-plus', 'javascript:loadAjaxForm(\'/ajax/nuovo-datore/\', \'Nuovo Datore\')'),
    ('nav_nuovo_lavoratore', 'Nuovo Lavoratore', 'person-plus', 'javascript:loadAjaxForm(\'/ajax/nuovo-lavoratore/\', \'Nuovo Lavoratore\')'),
    ('nav_nuovo_beneficiario', 'Nuovo Beneficiario', 'person-plus', 'javascript:loadAjaxForm(\'/ajax/nuovo-beneficiario/\', \'Nuovo Beneficiario\')'),
    ('nav_nuovo_contratto', 'Nuovo Contratto', 'file-earmark-plus', 'javascript:loadAjaxForm(\'/ajax/nuovo-contratto/\', \'Nuovo Contratto\')'),
    ('nav_nuovo_progetto', 'Nuovo Progetto Regionale', 'diagram-3', 'javascript:loadAjaxForm(\'/ajax/nuovo-tabella/progetti-regionali/\', \'Nuovo Progetto Regionale\')'),
    ('nav_datori', 'Datori di Lavoro', 'person-vcard', '/datori/'),
    ('nav_lavoratori', 'Lavoratori', 'people', '/lavoratori/'),
    ('nav_beneficiari', 'Beneficiari', 'person-heart', '/beneficiari/'),
    ('nav_mappa_beneficiari', 'Mappa Beneficiari', 'geo-alt', '/beneficiari/?view=mappa'),
    ('nav_contratti', 'Contratti Attivi', 'file-earmark-text', '/contratti/'),
    ('nav_contratti_cessati', 'Contratti Cessati', 'archive', '/contratti-cessati/'),
    ('nav_progetti_regionali', 'Progetti Regionali', 'diagram-3', '/tabella/progetti-regionali/'),
    ('nav_eliminati', 'Eliminati', 'trash3', '/eliminati/'),
    ('nav_stampe_invii', 'Stampe e Invii', 'send', '/stampe-invii/'),
    ('nav_riepilogo_invii', 'Riepilogo Invii', 'clock-history', '/riepilogo-invio/'),
    ('nav_archivio_documenti', 'Archivio Documenti', 'archive', '/documenti/'),
    ('nav_archivio_buste', 'Archivio Buste', 'journal-text', '/buste-archivio/'),
    ('nav_certificazione_unica', 'Certificazione Unica', 'file-earmark-text', '/procedure/redigere-cu/'),
    ('nav_liste_stampe', 'Liste Stampe', 'printer', '/liste/'),
    ('nav_parametri_ccnl', 'Parametri CCNL', 'sliders', '/tabella/parametri-ccnl/'),
    ('nav_tabelle_casse', 'Tabella Casse', 'cash-stack', '/tabella/tabelle-casse/'),
    ('nav_contributi_inps', 'Contributi INPS', 'percent', '/tabella/contributi-inps/'),
    ('nav_tabella_malattia', 'Tabella Malattia', 'heart-pulse', '/tabella/malattia/'),
    ('nav_scatti_anzianita', 'Scatti Anzianità', 'arrow-up-circle', '/tabella/scatti-anzianita/'),
    ('nav_tipo_progetto', 'Tipo Progetto', 'tags', '/tabella/tipi-progetto/'),
    ('nav_livelli', 'Livelli', 'layers', '/tabella/livelli/'),
    ('nav_modelli_lista', 'Modelli Lista', 'file-earmark-spreadsheet', '/tabella/modelli-lista/'),
    ('nav_busta_standard', 'Busta Paga Standard', 'file-earmark-text', '/calcoli/'),
    ('nav_busta_non_convivente', 'Busta Non Convivente', 'person', '/calcoli/non-convivente/'),
    ('nav_busta_conviventi', 'Busta Conviventi CCNL', 'house-heart', '/calcoli/conviventi-ccnl/'),
    ('nav_calcolo_inverso', 'Calcolo Inverso', 'arrow-left-right', '/calcoli/inverso/'),
    ('nav_busta_notturno', 'Busta Notturno', 'moon-stars', '/calcoli/notturno/'),
    ('nav_busta_malattia', 'Busta Malattia', 'heart-pulse', '/calcoli/malattia/'),
    ('nav_sostituzione_malattia', 'Sostituzione Malattia', 'arrow-repeat', '/calcoli/sostituzione/'),
    ('nav_busta_tfr', 'Busta TFR', 'piggy-bank', '/calcoli/tfr/'),
    ('nav_buste_massive', 'Buste Paga Massive', 'files', '/buste-paga-massivo/'),
    ('nav_iscrizione_inps', 'Iscrizione INPS', 'person-plus', '/procedure/iscrizione-inps/'),
    ('nav_cessazione_inps', 'Cessazione INPS', 'person-x', '/procedure/cessazione-inps/'),
    ('nav_crea_pagopa', 'Crea PAGOPA', 'credit-card-2-front', '/procedure/crea-pagopa/'),
    ('nav_crea_pagopa_manuale', 'Crea PAGOPA Manuale', 'credit-card-2-front', '/procedure/crea-pagopa-manuale/'),
    ('nav_configurazioni_web', 'Configurazioni Servizi Web', 'gear-wide-connected', '/configurazioni-servizi/'),
    ('nav_cronologia_inps', 'Cronologia INPS', 'journal-text', '/procedure/log-inps/'),
    ('nav_backup', 'Backup', 'database', '/backup/'),
    ('nav_impostazioni', 'Impostazioni', 'gear-wide-connected', '/impostazioni/'),
    ('nav_admin_django', 'Admin Django', 'shield-lock', '/admin/'),
    ('nav_about', 'About', 'info-circle', '/about/'),
    ('nav_scorciatoie', 'Scorciatoie Tastiera', 'keyboard', '/scorciatoie/'),
    ('nav_checklist', 'Checklist Mensile', 'check2-square', '/checklist-mensile/'),
    ('nav_audit', 'Registro Audit', 'journal-text', '/audit/'),
]


def _sync_menu_items():
    """Ensure all menu items exist in DB, preserving existing shortcuts."""
    valid_ids = {item[0] for item in MENU_ITEMS}
    ScorciatoiaTastiera.objects.exclude(menu_id__in=valid_ids).delete()
    for i, (menu_id, label, icona, _azione) in enumerate(MENU_ITEMS):
        ScorciatoiaTastiera.objects.get_or_create(
            menu_id=menu_id,
            defaults={'label': label, 'icona': icona, 'ordinamento': i}
        )


@login_required
def scorciatoie_view(request):
    _sync_menu_items()

    if request.method == 'POST':
        tasti_usati = set()
        for item in ScorciatoiaTastiera.objects.all():
            tasto = request.POST.get(f'tasto_{item.id}', '').strip().upper() or None
            attiva = request.POST.get(f'attiva_{item.id}') == '1'
            if tasto and tasto in tasti_usati:
                messages.warning(request, f'Il tasto "{tasto}" è duplicato. Saltato.')
                continue
            if tasto:
                conflitto = ScorciatoiaTastiera.objects.filter(
                    tasto=tasto, attiva=True
                ).exclude(pk=item.pk).first()
                if conflitto:
                    messages.warning(request, f'Il tasto "{tasto}" è già assegnato a "{conflitto.label}". Saltato.')
                    continue
            item.tasto = tasto
            item.attiva = attiva
            item.save()
            if tasto:
                tasti_usati.add(tasto)
        messages.success(request, 'Scorciatoie salvate con successo.')
        return redirect('scorciatoie')

    items = ScorciatoiaTastiera.objects.all().order_by('ordinamento')
    return render(request, 'paghe/scorciatoie.html', {'items': items, 'opzioni': get_opzioni()})
