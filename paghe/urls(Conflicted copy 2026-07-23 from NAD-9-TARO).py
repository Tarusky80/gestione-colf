from django.urls import path, include, re_path
from django.views.generic.base import RedirectView
from paghe import views

urlpatterns = [

    # === DASHBOARD / ABOUT / SCORCIATOIE ===
    path('dashboard/', views.dashboard, name='dashboard'),
    path('about/', views.about_page, name='about_page'),
    path('ajax/verifica-aggiornamenti/', views.ajax_verifica_aggiornamenti, name='ajax_verifica_aggiornamenti'),
    path('ajax/aggiorna-pacchetto/', views.ajax_aggiorna_pacchetto, name='ajax_aggiorna_pacchetto'),
    path('ajax/aggiorna-tutti/', views.ajax_aggiorna_tutti, name='ajax_aggiorna_tutti'),
    path('ajax/aggiorna-requirements/', views.ajax_aggiorna_requirements, name='ajax_aggiorna_requirements'),
    path('scorciatoie/', views.scorciatoie_view, name='scorciatoie'),
    path('ajax/contributi-trend/', views.ajax_contributi_trend, name='ajax_contributi_trend'),

    # === REPORT PDF ===
    path('report/mensile/', views.report_mensile_pdf, name='report_mensile'),
    path('report/annuale/', views.report_annuale_pdf, name='report_annuale'),
    path('report/annuale/<int:anno>/', views.report_annuale_pdf, name='report_annuale_anno'),
    path('report/annuale/<int:anno>/<int:datore_id>/', views.report_annuale_pdf, name='report_annuale_datore'),

    # === SIDEBAR LISTS ===
    path('datori/', views.datori_list, name='datori_list'),
    path('lavoratori/', views.lavoratori_list, name='lavoratori_list'),
    path('beneficiari/', views.beneficiari_list, name='beneficiari_list'),
    path('contratti/', views.contratti_list, name='contratti_list'),
    path('contratti-cessati/', views.contratti_cessati_list, name='contratti_cessati_list'),
    path('eliminati/', views.eliminati_list, name='eliminati_list'),
    path('backup/', views.backup_page, name='backup_page'),
    path('backup/auto/', views.backup_auto, name='backup_auto'),
    path('backup/esporta-excel/<int:pk>/', views.esporta_backup_excel, name='esporta_backup_excel'),
    path('backup/ripristina-db/<int:pk>/', views.ajax_ripristina_db, name='ajax_ripristina_db'),
    path('backup/scarica-json/<int:pk>/', views.scarica_backup_json, name='scarica_backup_json'),
    path('backup/scarica-db/<int:pk>/', views.scarica_backup_db, name='scarica_backup_db'),
    path('impostazioni/', views.impostazioni_page, name='impostazioni_page'),

    # === AJAX SEARCH / ANAGRAFICHE ===
    path('ajax/search/', views.global_search_view, name='global_search'),
    path('ajax/cerca-anagrafica-json/<str:tipo>/', views.anagrafica_search_json, name='anagrafica_search_json'),
    path('ajax/nuovo-datore/', views.ajax_form_datore, name='ajax_nuovo_datore'),
    path('ajax/nuovo-lavoratore/', views.ajax_form_lavoratore, name='ajax_nuovo_lavoratore'),
    path('ajax/nuovo-beneficiario/', views.ajax_form_beneficiario, name='ajax_nuovo_beneficiario'),
    path('ajax/nuovo-contratto/', views.ajax_form_contratto, name='ajax_nuovo_contratto'),
    path('ajax/modifica-contratto/<int:pk>/', views.ajax_modifica_contratto, name='ajax_modifica_contratto'),
    path('ajax/rigenera-documenti-cessazione/<int:pk>/', views.ajax_rigenera_documenti_cessazione, name='ajax_rigenera_documenti_cessazione'),
    path('ajax/elimina-contratto/<int:pk>/', views.ajax_elimina_contratto, name='ajax_elimina_contratto'),
    path('ajax/modifica-datore/<str:pk>/', views.ajax_modifica_datore, name='ajax_modifica_datore'),
    path('ajax/modifica-lavoratore/<str:pk>/', views.ajax_modifica_lavoratore, name='ajax_modifica_lavoratore'),
    path('ajax/modifica-beneficiario/<str:pk>/', views.ajax_modifica_beneficiario, name='ajax_modifica_beneficiario'),
    path('ajax/duplica-anagrafica/<slug:tipo>/<path:pk>/', views.ajax_duplica_anagrafica, name='ajax_duplica_anagrafica'),
    path('ajax/elimina-anagrafica/<slug:tipo>/<path:pk>/', views.ajax_elimina_anagrafica, name='ajax_elimina_anagrafica'),
    path('ajax/cerca-comune/', views.ajax_cerca_comune, name='ajax_cerca_comune'),

    # === AJAX EXPORT / IMPORT XLSX ===
    path('ajax/esporta-xlsx/<slug:tipo>/', views.ajax_esporta_xlsx, name='ajax_esporta_xlsx'),
    path('ajax/esporta-xlsx-filtrato/<slug:tipo>/', views.ajax_esporta_xlsx_filtrato, name='ajax_esporta_xlsx_filtrato'),
    path('ajax/importa-xlsx/<slug:tipo>/', views.ajax_importa_xlsx, name='ajax_importa_xlsx'),

    # === CONTRATTI CESSATI / ELIMINATI ===
    path('ajax/riattiva-contratto/<int:pk>/', views.ajax_riattiva_contratto, name='ajax_riattiva_contratto'),
    path('ajax/elimina-tutti-cessati/', views.ajax_elimina_tutti_cessati, name='ajax_elimina_tutti_cessati'),
    path('ajax/elimina-tutti-cessati-definitivamente/', views.ajax_elimina_tutti_cessati_definitivamente, name='ajax_elimina_tutti_cessati_definitivamente'),
    path('ajax/vedi-eliminato/<int:pk>/', views.ajax_vedi_eliminato, name='ajax_vedi_eliminato'),
    path('ajax/ripristina-eliminato/<int:pk>/', views.ajax_ripristina_eliminato, name='ajax_ripristina_eliminato'),
    path('ajax/elimina-eliminato/<int:pk>/', views.ajax_elimina_eliminato, name='ajax_elimina_eliminato'),
    path('ajax/ripristina-tutti-eliminati/', views.ajax_ripristina_tutti_eliminati, name='ajax_ripristina_tutti_eliminati'),
    path('ajax/elimina-tutti-eliminati/', views.ajax_elimina_tutti_eliminati, name='ajax_elimina_tutti_eliminati'),

    # === ANTEPRIMA / PDF CONTRATTO ===
    path('contratto/<int:pk>/anteprima/', views.anteprima_contratto, name='anteprima_contratto'),
    path('contratto/<int:pk>/pdf/', views.download_contratto_pdf, name='download_contratto_pdf'),
    path('ajax/genera-contratto-pdf/<int:pk>/', views.ajax_genera_contratto_pdf, name='ajax_genera_contratto_pdf'),

    # === TABELLE GENERICHE ===
    path('tabella/<slug:tipo>/', views.tabella_list, name='tabella_list'),
    path('ajax/nuovo-tabella/<slug:tipo>/', views.ajax_nuovo_tabella, name='ajax_nuovo_tabella'),
    path('ajax/modifica-tabella/<slug:tipo>/<path:pk>/', views.ajax_modifica_tabella, name='ajax_modifica_tabella'),
    path('ajax/duplica-tabella/<slug:tipo>/<path:pk>/', views.ajax_duplica_tabella, name='ajax_duplica_tabella'),
    path('ajax/elimina-tabella/<slug:tipo>/<path:pk>/', views.ajax_elimina_tabella, name='ajax_elimina_tabella'),
    path('ajax/preview-testo/', views.ajax_preview_testo, name='ajax_preview_testo'),
    path('ajax/preview-testo-pdf/', views.ajax_preview_testo_pdf, name='ajax_preview_testo_pdf'),
    path('ajax/testo-preimpostato/<int:pk>/', views.ajax_testo_preimpostato_corpo, name='ajax_testo_preimpostato_corpo'),

    # === CALCOLI BUSTE ===
    path('calcoli/', views.calcoli_list, name='calcoli_list'),
    path('calcoli/non-convivente/', views.calcoli_non_convivente, name='calcoli_non_convivente'),
    path('calcoli/conviventi-ccnl/', views.calcoli_conviventi_ccnl, name='calcoli_conviventi_ccnl'),
    path('calcoli/inverso/', views.calcoli_inverso, name='calcoli_inverso'),
    path('ajax/calcola-busta/<int:pk>/', views.ajax_calcola_busta, name='ajax_calcola_busta'),
    path('ajax/calcola-busta-non-convivente/<int:pk>/', views.ajax_calcola_busta_non_convivente, name='ajax_calcola_busta_non_convivente'),
    path('ajax/calcola-busta-conviventi-ccnl/<int:pk>/', views.ajax_calcola_busta_conviventi_ccnl, name='ajax_calcola_busta_conviventi_ccnl'),
    path('ajax/calcola-busta-inversa/<int:pk>/', views.ajax_calcola_busta_inversa, name='ajax_calcola_busta_inversa'),
    path('calcoli/notturno/', views.calcoli_notturno, name='calcoli_notturno'),
    path('ajax/calcola-busta-notturna/<int:pk>/', views.ajax_calcola_busta_notturna, name='ajax_calcola_busta_notturna'),
    path('calcoli/malattia/', views.calcoli_malattia, name='calcoli_malattia'),
    path('ajax/calcola-busta-malattia/<int:pk>/', views.ajax_calcola_busta_malattia, name='ajax_calcola_busta_malattia'),
    path('calcoli/tfr/', views.calcoli_tfr, name='calcoli_tfr'),
    path('ajax/calcola-busta-tfr/<int:pk>/', views.ajax_calcola_busta_tfr, name='ajax_calcola_busta_tfr'),
    path('calcoli/sostituzione/', views.calcoli_sostituzione, name='calcoli_sostituzione'),
    path('ajax/calcola-costo-malattia-sostituzione/<int:pk>/', views.ajax_calcola_costo_malattia_sostituzione, name='ajax_calcola_costo_malattia_sostituzione'),
    path('ajax/calcola-busta-sostituto/<int:pk>/', views.ajax_calcola_busta_sostituto, name='ajax_calcola_busta_sostituto'),
    path('ajax/crea-contratto-sostituto/', views.ajax_crea_contratto_sostituto, name='ajax_crea_contratto_sostituto'),

    # === PDF BUSTE ===
    path('ajax/busta-sostituto-pdf/<int:pk>/', views.download_busta_sostituto_pdf, name='download_busta_sostituto_pdf'),
    path('ajax/busta-inversa-pdf/<int:pk>/', views.download_busta_inversa_pdf, name='download_busta_inversa_pdf'),
    path('ajax/busta-pdf/<int:pk>/', views.download_busta_pdf, name='download_busta_pdf'),
    path('ajax/busta-non-convivente-pdf/<int:pk>/', views.download_busta_non_convivente_pdf, name='download_busta_non_convivente_pdf'),
    path('ajax/busta-conviventi-ccnl-pdf/<int:pk>/', views.download_busta_conviventi_ccnl_pdf, name='download_busta_conviventi_ccnl_pdf'),
    path('ajax/busta-notturna-pdf/<int:pk>/', views.download_busta_notturna_pdf, name='download_busta_notturna_pdf'),
    path('ajax/busta-malattia-pdf/<int:pk>/', views.download_busta_malattia_pdf, name='download_busta_malattia_pdf'),
    path('ajax/liquidazione-tfr/<int:pk>/', views.liquidazione_tfr, name='liquidazione_tfr'),
    path('ajax/ricevuta-busta-pdf/<int:pk>/', views.download_ricevuta_pdf, name='download_ricevuta_pdf'),
    path('ajax/genera-riepilogo-pdf/', views.ajax_genera_riepilogo_pdf, name='ajax_genera_riepilogo_pdf'),

    # === BUSTE — SALVATAGGIO / TEMPLATE ===
    path('ajax/salva-busta-template/<int:contratto_pk>/', views.ajax_salva_busta_template, name='ajax_salva_busta_template'),
    path('ajax/cerca-contratti-copia/', views.ajax_cerca_contratti_copia, name='ajax_cerca_contratti_copia'),
    path('ajax/dettaglio-contratto-copia/<int:pk>/', views.ajax_dettaglio_contratto_copia, name='ajax_dettaglio_contratto_copia'),

    # === LISTE STAMPA / CCNL OCCHIO ===
    path('liste/', views.liste_view, name='liste_list'),
    path('ajax/genera-lista/<slug:tipo>/', views.ajax_genera_lista, name='ajax_genera_lista'),
    path('ajax/field-browser/<slug:tipo_sorgente>/', views.ajax_field_browser, name='ajax_field_browser'),
    path('ajax/modello-lista-config/<int:pk>/', views.ajax_modello_lista_config, name='ajax_modello_lista_config'),
    path('ajax/salva-config-modello/<int:pk>/', views.ajax_salva_config_modello, name='ajax_salva_config_modello'),
    path('ajax/genera-lista-personalizzata/<int:pk>/', views.ajax_genera_lista_personalizzata, name='ajax_genera_lista_personalizzata'),
    path('ajax/elimina-modello-lista/<int:pk>/', views.ajax_elimina_modello_lista, name='ajax_elimina_modello_lista'),
    path('ajax/ccnl-occhio/', views.ajax_ccnl_occhio, name='ajax_ccnl_occhio'),
    path('ccnl-occhio/popup/', views.ccnl_occhio_popup, name='ccnl_occhio_popup'),
    path('ajax/ccnl-occhio-busta/<int:pk>/', views.ajax_ccnl_occhio_busta, name='ajax_ccnl_occhio_busta'),
    path('ajax/ccnl-occhio-riepilogo-pdf/', views.ajax_ccnl_occhio_riepilogo_pdf, name='ajax_ccnl_occhio_riepilogo_pdf'),

    # === ARCHIVIO BUSTE ===
    path('buste-archivio/', views.buste_archivio, name='buste_archivio'),
    path('ajax/salva-busta/', views.ajax_salva_busta, name='ajax_salva_busta'),
    path('ajax/salva-buste-selezionate/', views.ajax_salva_buste_selezionate, name='ajax_salva_buste_selezionate'),
    path('ajax/liquida-tfr/', views.ajax_liquida_tfr, name='ajax_liquida_tfr'),
    path('ajax/cambia-stato-busta/<int:pk>/', views.ajax_cambia_stato_busta, name='ajax_cambia_stato_busta'),
    path('ajax/elimina-busta/<int:pk>/', views.ajax_elimina_busta, name='ajax_elimina_busta'),
    path('ajax/associa-documento-busta/<int:pk>/', views.ajax_associa_documento_busta, name='ajax_associa_documento_busta'),
    path('ajax/stampa-busta/<int:pk>/', views.ajax_stampa_busta, name='ajax_stampa_busta'),
    path('ajax/genera-pdf-busta/<int:busta_pk>/', views.ajax_genera_pdf_busta, name='ajax_genera_pdf_busta'),
    path('ajax/decodifica-cf/', views.ajax_decodifica_cf, name='ajax_decodifica_cf'),

    # === GESTIONE DOCUMENTALE ===
    path('documenti/', views.documenti_list, name='documenti_list'),
    path('ajax/nuovo-documento/', views.ajax_nuovo_documento, name='ajax_nuovo_documento'),
    path('ajax/anteprima-documento/', views.ajax_anteprima_documento, name='ajax_anteprima_documento'),
    path('ajax/carica-documento/', views.ajax_carica_documento, name='ajax_carica_documento'),
    path('ajax/vedi-documento/<int:pk>/', views.ajax_vedi_documento, name='ajax_vedi_documento'),
    path('ajax/elimina-documento/<int:pk>/', views.ajax_elimina_documento, name='ajax_elimina_documento'),
    path('ajax/invia-documento-email/<int:pk>/', views.ajax_invia_documento_email, name='ajax_invia_documento_email'),
    path('ajax/stampa-documento/<int:pk>/', views.ajax_stampa_documento, name='ajax_stampa_documento'),
    path('ajax/stampa-documento-massiva/', views.ajax_stampa_documento_massiva, name='ajax_stampa_documento_massiva'),
    path('ajax/anteprima-email/<int:pk>/', views.ajax_anteprima_email, name='ajax_anteprima_email'),
    path('ajax/mail-datore/<int:pk>/', views.ajax_mail_datore, name='ajax_mail_datore'),
    path('ajax/ultimo-documento-pk/', views.ajax_ultimo_documento_pk, name='ajax_ultimo_documento_pk'),
    path('ajax/anteprima-email-datore/<int:pk>/', views.ajax_anteprima_email_datore, name='ajax_anteprima_email_datore'),
    path('ajax/invia-massivo-email/', views.ajax_invia_massivo_email, name='ajax_invia_massivo_email'),
    path('ajax/modelli-email/', views.ajax_modelli_email, name='ajax_modelli_email'),
    path('ajax/invia-email-raggruppata/', views.ajax_invia_email_raggruppata, name='ajax_invia_email_raggruppata'),
    path('ajax/cerca-email/', views.ajax_cerca_email, name='ajax_cerca_email'),
    path('ajax/documenti-contratto/<int:pk>/', views.ajax_documenti_contratto, name='ajax_documenti_contratto'),
    path('ajax/sfoglia-file/', views.ajax_sfoglia_file, name='ajax_sfoglia_file'),
    path('ajax/apri-cartella-documento/<int:pk>/', views.ajax_apri_cartella_documento, name='ajax_apri_cartella_documento'),
    path('apri-cartella-documento/<int:pk>/', views.apri_cartella_documento, name='apri_cartella_documento'),
    path('ajax/collega-documento-contratto/<int:pk>/', views.ajax_collega_documento_contratto, name='ajax_collega_documento_contratto'),
    path('ajax/template-selector/<int:contratto_pk>/', views.ajax_template_selector, name='ajax_template_selector'),
    path('genera-pdf-da-template/<int:contratto_pk>/<int:modello_pk>/', views.genera_pdf_da_template, name='genera_pdf_da_template'),

    # === DOCUMENTALE (modelli strutturati) ===
    path('documentale/', views.documentale_root, name='documentale_root'),
    path('documentale/<slug:tipo>/', views.documentale_list, name='documentale_list'),
    path('documentale/<slug:tipo>/nuovo/', views.documentale_edit, name='documentale_nuovo'),
    path('documentale/<slug:tipo>/<int:pk>/', views.documentale_edit, name='documentale_edit'),
    path('ajax/documentale/<slug:tipo>/nuovo/save/', views.documentale_edit, name='ajax_documentale_nuovo_save'),
    path('ajax/documentale/<slug:tipo>/<int:pk>/save/', views.documentale_edit, name='ajax_documentale_modifica_save'),
    path('ajax/documentale-preview/', views.ajax_documentale_preview, name='ajax_documentale_preview'),
    path('ajax/documentale-preview-pdf/', views.ajax_documentale_preview_pdf, name='ajax_documentale_preview_pdf'),
    path('ajax/salva-pdf-anteprima/', views.ajax_salva_pdf_anteprima, name='ajax_salva_pdf_anteprima'),
    path('ajax/documentale-elimina/<int:pk>/', views.ajax_documentale_elimina, name='ajax_documentale_elimina'),
    path('ajax/documentale-duplica/<int:pk>/', views.ajax_documentale_duplica, name='ajax_documentale_duplica'),
    path('genera-pdf-documentale/<int:contratto_pk>/<int:modello_pk>/', views.genera_pdf_documentale, name='genera_pdf_documentale'),

    # === BUSTE PAGA MASSIVE ===
    path('buste-paga-massivo/', views.buste_paga_massivo, name='buste_paga_massivo'),
    path('ajax/genera-buste-massivo/', views.ajax_genera_buste_massivo, name='ajax_genera_buste_massivo'),
    path('ajax/genera-busta-per-email/<int:contratto_pk>/', views.ajax_genera_busta_per_email, name='ajax_genera_busta_per_email'),
    path('ajax/invia-buste-massivo/', views.ajax_invia_buste_massivo, name='ajax_invia_buste_massivo'),

    # === RIEPILOGO INVIO ===
    path('riepilogo-invio/', views.riepilogo_invio_list, name='riepilogo_invio_list'),
    path('riepilogo-invio/<int:pk>/', views.riepilogo_invio_dettaglio, name='riepilogo_invio_dettaglio'),
    path('download-riepilogo-zip/<int:pk>/', views.download_riepilogo_zip, name='download_riepilogo_zip'),
    path('ajax/elimina-riepilogo-invio/<int:pk>/', views.ajax_elimina_riepilogo_invio, name='ajax_elimina_riepilogo_invio'),
    path('ajax/elimina-tutti-riepilogo-invio/', views.ajax_elimina_tutti_riepilogo_invio, name='ajax_elimina_tutti_riepilogo_invio'),

    # === STAMPE E INVII ===
    path('stampe-invii/', views.stampe_invii, name='stampe_invii'),
    path('ajax/genera-stampe-invii/', views.ajax_genera_stampe_invii, name='ajax_genera_stampe_invii'),
    path('ajax/composizioni/', views.ajax_lista_composizioni, name='ajax_lista_composizioni'),
    path('ajax/salva-composizione/', views.ajax_salva_composizione, name='ajax_salva_composizione'),
    path('ajax/elimina-composizione/<int:pk>/', views.ajax_elimina_composizione, name='ajax_elimina_composizione'),
    path('ajax/apri-cartella-stampe/<int:pk>/', views.ajax_apri_cartella_stampe, name='ajax_apri_cartella_stampe'),
    path('stampe-invii/print/<str:token>/', views.stampe_invii_print, name='stampe_invii_print'),
    path('ajax/stampa-unico/', views.ajax_stampa_unico, name='ajax_stampa_unico'),

    # === PROCEDURE WEB INPS ===
    path('procedure/iscrizione-inps/', views.iscrizione_inps, name='iscrizione_inps'),
    path('procedure/iscrizione-inps/popup/<int:pk>/', views.iscrizione_inps_popup, name='iscrizione_inps_popup'),
    path('ajax/salva-codice-rapporto-inps/', views.ajax_salva_codice_rapporto_inps, name='ajax_salva_codice_rapporto_inps'),
    path('procedure/cessazione-inps/', views.cessazione_inps, name='cessazione_inps'),
    path('procedure/cessazione-inps/popup/<int:pk>/', views.cessazione_inps_popup, name='cessazione_inps_popup'),
    path('ajax/salva-data-fine-cessazione/', views.ajax_salva_data_fine_cessazione, name='ajax_salva_data_fine_cessazione'),
    path('ajax/copia-data-fine/', views.ajax_copia_data_fine, name='ajax_copia_data_fine'),
    path('ajax/test-smtp/', views.ajax_test_smtp, name='ajax_test_smtp'),
    path('ajax/ripristina-da-json/', views.ajax_ripristina_da_upload, name='ajax_ripristina_da_upload'),

    # === COMPARATORE ===
    path('comparatore/', views.comparatore_page, name='comparatore_page'),

    # === AGENDA ===
    path('agenda/', views.agenda_page, name='agenda_page'),
    path('agenda/pdf/', views.agenda_pdf, name='agenda_pdf'),
    path('ajax/agenda/nuovo/', views.ajax_agenda_nuovo, name='ajax_agenda_nuovo'),
    path('ajax/agenda/toggle/<int:pk>/', views.ajax_agenda_toggle, name='ajax_agenda_toggle'),
    path('ajax/agenda/elimina/<int:pk>/', views.ajax_agenda_elimina, name='ajax_agenda_elimina'),
    path('ajax/agenda/modifica/<int:pk>/', views.ajax_agenda_modifica, name='ajax_agenda_modifica'),
    path('ajax/agenda/sposta/<int:pk>/', views.ajax_agenda_sposta, name='ajax_agenda_sposta'),

    # === TFR ===
    path('ajax/salva-anticipo-tfr/', views.ajax_salva_anticipo_tfr, name='ajax_salva_anticipo_tfr'),
    path('ajax/elimina-anticipo-tfr/<int:pk>/', views.ajax_elimina_anticipo_tfr, name='ajax_elimina_anticipo_tfr'),
    path('ajax/lista-anticipi-tfr/<int:contratto_pk>/', views.ajax_lista_anticipi_tfr, name='ajax_lista_anticipi_tfr'),
    path('ajax/prospetto-tfr/<int:pk>/', views.ajax_prospetto_tfr, name='ajax_prospetto_tfr'),
    path('ajax/rinnova-contratto/<int:pk>/', views.ajax_rinnova_contratto, name='ajax_rinnova_contratto'),
    path('ajax/log-invii-cu/<int:contratto_pk>/<int:anno>/', views.ajax_log_invii_cu, name='ajax_log_invii_cu'),

    # === PAGOPA ===
    path('procedure/crea-pagopa/', views.crea_pagopa, name='crea_pagopa'),
    path('procedure/crea-pagopa-manuale/', views.crea_pagopa_manuale, name='crea_pagopa_manuale'),
    path('procedure/crea-pagopa-manuale/popup/<int:pk>/', views.crea_pagopa_manuale_popup, name='crea_pagopa_manuale_popup'),
    path('ajax/carica-pdf-pagopa-manuale/', views.ajax_carica_pdf_pagopa_manuale, name='ajax_carica_pdf_pagopa_manuale'),
    path('ajax/lista-pdf-pagopa-manuale/', views.ajax_lista_pdf_pagopa_manuale, name='ajax_lista_pdf_pagopa_manuale'),
    path('procedure/log-inps/', views.log_inps_list, name='log_inps'),
    path('ajax/elimina-log-inps/', views.ajax_elimina_log_inps, name='ajax_elimina_log_inps'),
    path('ajax/carica-dati-pagopa/', views.ajax_carica_dati_pagopa, name='ajax_carica_dati_pagopa'),
    path('ajax/genera-pagopa-pdf/', views.ajax_genera_pagopa_pdf, name='ajax_genera_pagopa_pdf'),
    path('ajax/avvia-pagopa/', views.ajax_avvia_pagopa, name='ajax_avvia_pagopa'),
    path('ajax/pagopa-prosegui/', views.ajax_pagopa_prosegui, name='ajax_pagopa_prosegui'),
    path('ajax/chiudi-pagopa/', views.ajax_chiudi_pagopa, name='ajax_chiudi_pagopa'),
    path('ajax/salva-ore-pagopa/', views.ajax_salva_ore_pagopa, name='ajax_salva_ore_pagopa'),
    path('ajax/apri-pagopa-pdf/', views.ajax_apri_pagopa_pdf, name='ajax_apri_pagopa_pdf'),
    path('ajax/apri-pagopa-manuale-pdf/', views.ajax_apri_pagopa_manuale_pdf, name='ajax_apri_pagopa_manuale_pdf'),
    path('ajax/cerca-pagopa-doc/', views.ajax_cerca_pagopa_doc, name='ajax_cerca_pagopa_doc'),
    path('ajax/storico-pagopa/', views.ajax_storico_pagopa, name='ajax_storico_pagopa'),
    path('ajax/elimina-pagopa-doc/', views.ajax_elimina_pagopa_doc, name='ajax_elimina_pagopa_doc'),
    path('ajax/apri-cartella-documenti/', views.ajax_apri_cartella_documenti, name='ajax_apri_cartella_documenti'),
    path('ajax/apri-cartella-download/', views.ajax_apri_cartella_download, name='ajax_apri_cartella_download'),
    path('configurazioni-servizi/', views.configurazioni_servizi, name='configurazioni_servizi'),

    # === EXPORT UNIEMENS CSV ===
    path('export/uniemens-csv/', views.export_uniemens_csv, name='export_uniemens_csv'),

    # === CCNL ===
    path('ccnl/', views.ccnl_list, name='ccnl_list'),
    path('ccnl/pdf/', views.ccnl_pdf, name='ccnl_pdf'),
    path('ccnl/invia-email/', views.ajax_ccnl_invia_email, name='ajax_ccnl_invia_email'),

    # === INQUADRAMENTO ===
    path('inquadramento/', views.inquadramento_list, name='inquadramento_list'),
    path('inquadramento/pdf/', views.inquadramento_pdf, name='inquadramento_pdf'),
    path('inquadramento/invia-email/', views.ajax_inquadramento_invia_email, name='ajax_inquadramento_invia_email'),

    # === TABELLE RETRIBUTIVE ===
    path('tabelle/', views.tabelle_retributive_list, name='tabelle_retributive_list'),
    path('tabelle/pdf/', views.tabelle_retributive_pdf, name='tabelle_retributive_pdf'),
    path('tabelle/invia-email/', views.ajax_tabelle_invia_email, name='ajax_tabelle_invia_email'),
    path('tabelle/verifica-ccnl/', views.verifica_ccnl, name='verifica_ccnl'),

    # === CONTRIBUTI INPS CCNL ===
    path('contributi-ccnl/', views.contributi_ccnl_list, name='contributi_ccnl_list'),
    path('contributi-ccnl/pdf/', views.contributi_ccnl_pdf, name='contributi_ccnl_pdf'),
    path('contributi-ccnl/invia-email/', views.ajax_contributi_ccnl_invia_email, name='ajax_contributi_ccnl_invia_email'),

    # === GUIDE DOCUMENTALI ===
    path('guide/assunzione/', views.guida_assunzione_list, name='guida_assunzione_list'),
    path('guide/assunzione/pdf/', views.guida_assunzione_pdf, name='guida_assunzione_pdf'),
    path('guide/assunzione/invia-email/', views.ajax_guida_assunzione_invia_email, name='ajax_guida_assunzione_invia_email'),
    path('guide/decalogo-colloquio/', views.decalogo_colloquio_list, name='decalogo_colloquio_list'),
    path('guide/decalogo-colloquio/pdf/', views.decalogo_colloquio_pdf, name='decalogo_colloquio_pdf'),
    path('guide/decalogo-colloquio/invia-email/', views.ajax_decalogo_colloquio_invia_email, name='ajax_decalogo_colloquio_invia_email'),
    path('guide/cessazione/', views.guida_cessazione_list, name='guida_cessazione_list'),
    path('guide/cessazione/pdf/', views.guida_cessazione_pdf, name='guida_cessazione_pdf'),
    path('guide/cessazione/invia-email/', views.ajax_guida_cessazione_invia_email, name='ajax_guida_cessazione_invia_email'),

    # === CERTIFICAZIONE UNICA ===
    path('procedure/redigere-cu/', views.redigere_cu, name='redigere_cu'),
    path('ajax/carica-dati-cu/', views.ajax_carica_dati_cu, name='ajax_carica_dati_cu'),
    path('ajax/genera-cu-pdf/', views.ajax_genera_cu_pdf, name='ajax_genera_cu_pdf'),
    path('ajax/genera-cu-pdf-batch/', views.ajax_genera_cu_pdf_batch, name='ajax_genera_cu_pdf_batch'),
    path('ajax/invia-cu-email/', views.ajax_invia_cu_email, name='ajax_invia_cu_email'),
    path('ajax/invia-cu-massivo/', views.ajax_invia_cu_massivo, name='ajax_invia_cu_massivo'),
    path('ajax/salva-cu-annuale/', views.ajax_salva_cu_annuale, name='ajax_salva_cu_annuale'),
    path('ajax/verifica-cu/', views.ajax_verifica_cu, name='ajax_verifica_cu'),

    # === STORICO / ALERT ===
    path('ajax/storico-modifiche-contratto/<int:contratto_pk>/', views.ajax_storico_modifiche_contratto, name='ajax_storico_modifiche_contratto'),
    path('ajax/alert-contratto/<int:pk>/', views.ajax_alert_contratto, name='ajax_alert_contratto'),

    # === OPERAZIONI MASSIVE ===
    path('contratti/rinnova-massivo/', views.rinnova_massivo_page, name='rinnova_massivo'),
    path('ajax/rinnova-massivo/', views.ajax_rinnova_massivo, name='ajax_rinnova_massivo'),

    # === ACCESSO DATORE — VECCHIO PORTALE (rediretti al nuovo /portal/) ===
    path('datore/login/', RedirectView.as_view(url='/portal/', permanent=False)),
    path('datore/logout/', RedirectView.as_view(url='/portal/', permanent=False)),
    path('datore/', RedirectView.as_view(url='/portal/', permanent=False)),
    path('datore/download/<int:pk>/', RedirectView.as_view(url='/portal/', permanent=False)),

    # === ACCESSO DATORE — AJAX admin (abilitazione, visibilità) ===
    path('ajax/datore-abilita-accesso/', views.ajax_datore_abilita_accesso, name='ajax_datore_abilita_accesso'),
    path('ajax/datore-stato-accesso/<str:cf>/', views.ajax_datore_stato_accesso, name='ajax_datore_stato_accesso'),
    path('ajax/documento-toggle-visibilita-datore/', views.ajax_documento_toggle_visibilita_datore, name='ajax_documento_toggle_visibilita_datore'),

    # === GESTIONE DB ===
    path('gestione-db/', views.gestione_db_page, name='gestione_db_page'),
    path('ajax/attiva-db/', views.ajax_attiva_db, name='ajax_attiva_db'),
    path('attiva-db/<slug:profile>/', views.attiva_db_redirect, name='attiva_db_redirect'),
    path('ajax/crea-db/', views.ajax_crea_db, name='ajax_crea_db'),
    path('ajax/elimina-db/', views.ajax_elimina_db, name='ajax_elimina_db'),

    # === CHECKLIST MENSILE ===
    path('checklist-mensile/', views.checklist_mensile, name='checklist_mensile'),
    path('ajax/checklist/toggle/<int:pk>/', views.ajax_checklist_toggle, name='ajax_checklist_toggle'),
    path('ajax/checklist/note/<int:pk>/', views.ajax_checklist_note, name='ajax_checklist_note'),
    path('ajax/checklist/reset-mese/', views.ajax_checklist_reset_mese, name='ajax_checklist_reset_mese'),

    # === RICHIESTE MODIFICA DATORE ===
    path('richieste-modifica/', views.richieste_modifica_list, name='richieste_modifica_list'),
    # path('ajax/datore-richiedi-modifica/', ...) — sostituito da POST /api/v1/richieste/
    path('ajax/admin-gestisci-richiesta/', views.ajax_admin_gestisci_richiesta, name='ajax_admin_gestisci_richiesta'),
    path('ajax/conta-richieste-pendenti/', views.ajax_conta_richieste_pendenti, name='ajax_conta_richieste_pendenti'),
    path('ajax/admin-elimina-richiesta/', views.ajax_admin_elimina_richiesta, name='ajax_admin_elimina_richiesta'),
    path('ajax/admin-ripristina-richiesta/', views.ajax_admin_ripristina_richiesta, name='ajax_admin_ripristina_richiesta'),

    # === AUDIT LOG ===
    path('audit/', views.audit_log_view, name='audit_log'),
    path('ajax/audit/dettaglio/<int:pk>/', views.ajax_audit_dettaglio, name='ajax_audit_dettaglio'),
    path('ajax/audit/elimina/<int:pk>/', views.ajax_audit_elimina, name='ajax_audit_elimina'),

    # === MAPPA BENEFICIARI ===
    # === LUL — LIBRO UNICO DEL LAVORO ===
    path('lul/', views.lul_list, name='lul_list'),
    path('ajax/lul/genera/', views.ajax_genera_lul, name='ajax_genera_lul'),
    path('ajax/lul/elimina/', views.ajax_elimina_lul, name='ajax_elimina_lul'),

    path('ajax/registra-voce-recente/', views.ajax_registra_voce_recente, name='ajax_registra_voce_recente'),
    path('ajax/beneficiari-mappa/', views.ajax_beneficiari_mappa, name='ajax_beneficiari_mappa'),
    path('mappa-beneficiari/', views.mappa_beneficiari_page, name='mappa_beneficiari'),

    # === MULTI-PROFILO PERMESSI ===
    path('permessi/', views.pannello_permessi, name='pannello_permessi'),
    path('ajax/permessi/modifica-ruolo/', views.ajax_modifica_ruolo, name='ajax_modifica_ruolo'),
    path('ajax/permessi/utenti/', views.ajax_lista_utenti, name='ajax_lista_utenti'),

    # === REST API v1 ===
    path('api/v1/', include('paghe.api.urls')),

    # === Employer Portal SPA (tutti i sotto-path vanno al frontend Vue) ===
    re_path(r'^portal/', views.portal_spa, name='portal_spa'),

    # === Mobile version ===
    path('m/', include('paghe.urls_mobile')),
]
