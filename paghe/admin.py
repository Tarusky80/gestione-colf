from django.contrib import admin
from django.utils.html import mark_safe
from django.contrib import messages
from django.db.models import Case, When, Value, IntegerField

from .forms import OpzioniSoftwareForm

from .models import (
    DatoreLavoro, Lavoratore, Beneficiario, ProgettoRegionale,
    ContrattoLavoro, ContrattoAttivo, ContrattoCessato,
    ParametriCCNL, Livello, TabellaContributiINPS, AuditLog,
    OpzioniSoftware, TabellaCasse,
    TabellaScattiAnzianita, TipoProgettoRegionale,
    TabellaMalattia, GestoreBackup, RecordEliminato,
    DocumentoArchiviato, ModelloLista, RiepilogoInvio,
    ServizioWebConfig, ModelloComposizione, BustaPaga, ModificaContratto,
    Appuntamento, ModelloDocumentale,
    AnticipoTFR, IndiceISTAT, AccessoDatore, RichiestaModificaDatore,
    LogInvioEmail, CUAnnuale, LogOperazioneINPS, ScorciatoiaTastiera,
    AttivitaMensile, CompletamentoMensile, CcnlArticolo,
    HistoricalContrattoLavoro,
)

admin.site.site_header = "Gestione COLF & Badanti"
admin.site.site_title = "GESTIONECOLF"
admin.site.index_title = "Pannello di Amministrazione"

# ====================================================
# 1. ANAGRAFICHE
# ====================================================

@admin.register(DatoreLavoro)
class DatoreAdmin(admin.ModelAdmin):
    list_display = ('nome_cognome', 'codice_fiscale', 'comune', 'email', 'telefono')
    search_fields = ('nome_cognome', 'codice_fiscale', 'comune', 'email')
    list_per_page = 25


@admin.register(Lavoratore)
class LavoratoreAdmin(admin.ModelAdmin):
    list_display = ('nome_cognome', 'codice_fiscale', 'comune', 'email', 'telefono')
    search_fields = ('nome_cognome', 'codice_fiscale', 'comune', 'email')
    list_per_page = 25


@admin.register(Beneficiario)
class BeneficiarioAdmin(admin.ModelAdmin):
    list_display = ('nome_cognome', 'codice_fiscale', 'comune', 'email', 'telefono')
    search_fields = ('nome_cognome', 'codice_fiscale', 'comune')
    list_per_page = 25


# ====================================================
# 2. PROGETTI
# ====================================================

@admin.register(ProgettoRegionale)
class ProgettoRegionaleAdmin(admin.ModelAdmin):
    list_display = ('beneficiario', 'tipo', 'budget_mensile', 'budget_annuale', 'data_inizio', 'data_fine')
    list_filter = ('tipo',)
    search_fields = ('beneficiario__nome_cognome',)
    list_per_page = 25


@admin.register(TipoProgettoRegionale)
class TipoProgettoRegionaleAdmin(admin.ModelAdmin):
    list_display = ('nome', 'colore', 'descrizione')
    search_fields = ('nome',)
    list_per_page = 25


# ====================================================
# 3. TABELLE PARAMETRICHE
# ====================================================

@admin.register(ParametriCCNL)
class ParametriAdmin(admin.ModelAdmin):
    search_fields = ('livello__codice', 'descrizione_corta')
    list_display = ('livello', 'paga_base', 'minimo_mensile_ft', 'minimo_mensile_pt', 'anno', 'descrizione_corta')
    list_per_page = 25

    fieldsets = (
        (None, {
            'fields': ('livello', 'anno', 'descrizione_corta', 'descrizione_lunga'),
        }),
        ('RETRIBUZIONE ORARIA', {
            'fields': (
                ('paga_base', 'retribuzione_sostituzione'),
                ('tfr_orario', 'tredicesima_oraria'),
                ('ferie_orarie', 'festivi_orari'),
            ),
        }),
        ('MINIMI MENSILI CCNL (Busta Conviventi)', {
            'fields': (
                ('minimo_mensile_ft', 'minimo_mensile_pt'),
                ('ind_funzione_mensile', 'ind_cert_qualita_mensile'),
                ('ind_minori_6_mensile_ft', 'ind_minori_6_mensile_pt'),
                ('ind_piu_assistiti_mensile',),
            ),
        }),
        ('INDENNITÀ ORARIE', {
            'fields': (
                ('ind_cert_qualita', 'ind_assistenza_piu_persone_non_conv'),
                ('ind_minori_6_anni_non_conv', 'ind_piu_persone_qualita'),
                ('ind_minori_qualita', 'ind_assistenza_piu_persone_ft'),
                ('ind_assistenza_piu_persone_pt', 'ind_minori_6_anni_ft'),
                ('ind_funzione_conviventi', 'conviventi_ft_54h'),
                ('conviventi_pt_30h',),
            ),
        }),
        ('NOTTURNO', {
            'fields': (
                ('ind_notturno_assistenza', 'ind_notturno_presenza'),
                ('ind_notturno_base', 'ind_notturno_20'),
                ('notturno_tfr', 'notturno_13ma'),
                ('notturno_festivi', 'notturno_ferie'),
            ),
        }),
        ('CONVIVENZA (valori giornalieri)', {
            'fields': (
                ('convivenza_pranzo', 'convivenza_cena', 'convivenza_alloggio'),
            ),
        }),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            custom_order=Case(
                When(livello__codice='A', then=Value(1)),
                When(livello__codice='AS', then=Value(2)),
                When(livello__codice='B', then=Value(3)),
                When(livello__codice='BS', then=Value(4)),
                When(livello__codice='C', then=Value(5)),
                When(livello__codice='CS', then=Value(6)),
                When(livello__codice='D', then=Value(7)),
                When(livello__codice='DS', then=Value(8)),
                default=Value(99),
                output_field=IntegerField(),
            )
        ).order_by('custom_order', 'livello__codice')


@admin.register(Livello)
class LivelloAdmin(admin.ModelAdmin):
    list_display = ('codice', 'colore')
    search_fields = ('codice',)
    list_per_page = 25


@admin.register(TabellaContributiINPS)
class TabellaContributiINPSAdmin(admin.ModelAdmin):
    list_display = ('descrizione', 'quota_datore', 'quota_lavoratore', 'totale')
    ordering = ('descrizione',)
    list_per_page = 25


@admin.register(TabellaCasse)
class TabellaCasseAdmin(admin.ModelAdmin):
    list_display = ('codice', 'descrizione', 'quota_datore', 'quota_lavoratore', 'totale')
    list_per_page = 25


@admin.register(TabellaScattiAnzianita)
class TabellaScattiAnzianitaAdmin(admin.ModelAdmin):
    list_display = ('livello', 'valore_scatto')
    list_filter = ('livello',)
    list_per_page = 25


@admin.register(TabellaMalattia)
class TabellaMalattiaAdmin(admin.ModelAdmin):
    list_display = ('anzianita', 'soglia_mesi', 'giorni_durata', 'conservazione_posto')
    list_per_page = 25


# ====================================================
# 4. CONTRATTI
# ====================================================

class ContrattoBaseAdmin(admin.ModelAdmin):
    readonly_fields = (
        'stima_netto_mensile', 'prospetto_ore_mensili', 'costo_mensile_effettivo', 
        'differenza_budget', 'verifica_soglia_contributi', 'dettaglio_indennita',
        'alert_fine_prova', 'alert_scatti_anzianita'
    )
    list_display = ('datore', 'lavoratore', 'data_assunzione', 'tipo_contratto', 'stato')
    search_fields = ('datore__nome_cognome', 'lavoratore__nome_cognome', 'codice_rapporto_inps')
    list_filter = ('stato', 'tipo_contratto', 'is_convivente')
    autocomplete_fields = ['datore', 'lavoratore', 'parametri_minimi']
    list_select_related = ('datore', 'lavoratore', 'parametri_minimi')
    list_per_page = 25

    fieldsets = (
        ('1. ANAGRAFICA E STATO', {
            'fields': (
                ('datore', 'lavoratore'),
                ('stato', 'tipo_contratto'),
                ('data_assunzione', 'data_inizio_tfr'),
                ('codice_rapporto_inps'),
                ('contratto_rinnovato_da'),
            ),
        }),
        ('2. INQUADRAMENTO E WELFARE', {
            'fields': (
                ('parametri_minimi', 'ente_bilaterale'),
                'progetto',
                'ore_mav_custom',
            ),
        }),
        ('3. IMPOSTAZIONI RATEI (Standard)', {
            'classes': ('colonne-2',),
            'fields': (
                ('applica_scatti', 'is_convivente'),
                ('modalita_tfr', 'paga_13ma'),
                ('paga_festivi', 'paga_ferie'),
            ),
        }),
        ('4. INDENNITÀ SPECIALI', {
            'classes': ('colonne-2',),
            'fields': (
                ('ind_certificazione_qualita', 'ind_piu_persone_non_conv'),
                ('ind_minori_non_conv', 'ind_piu_persone_qualita'),
                ('ind_minori_qualita', 'ind_assistenza_piu_persone_ft'),
                ('ind_assistenza_piu_persone_pt', 'ind_minori_6_anni_ft'),
            ),
        }),
        ('5. NOTTURNO E CONVIVENZA', {
            'classes': ('colonne-2',),
            'fields': (
                ('applica_notturno_assistenza', 'applica_notturno_presenza'),
                ('applica_notturno_base', 'applica_notturno_20'),
                ('paga_notturno_tfr', 'paga_notturno_13ma'),
                ('paga_notturno_festivi', 'paga_notturno_ferie'),
                ('ind_funzione_conviventi', 'ind_conviventi_ft_54h'),
                ('ind_conviventi_pt_30h', 'paga_pranzo'),
                ('paga_cena', 'paga_alloggio'),
            ),
        }),
        ('6. CALCOLI E PROSPETTI (Sola Lettura)', {
            'fields': (
                'stima_netto_mensile',
                ('prospetto_ore_mensili', 'costo_mensile_effettivo'),
                ('differenza_budget', 'verifica_soglia_contributi'),
                ('alert_fine_prova', 'alert_scatti_anzianita'),
            ),
        }),
        ('7. NOTE', {
            'fields': ('note_post_it',),
        }),
    )


@admin.register(ContrattoLavoro)
class ContrattoLavoroAdmin(ContrattoBaseAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request)


@admin.register(ContrattoAttivo)
class ContrattoAttivoAdmin(ContrattoBaseAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(stato='ATTIVO')


@admin.register(ContrattoCessato)
class ContrattoCessatoAdmin(ContrattoBaseAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).exclude(stato='ATTIVO')


# ====================================================
# 5. DOCUMENTI E BACKUP
# ====================================================

@admin.register(DocumentoArchiviato)
class DocumentoArchiviatoAdmin(admin.ModelAdmin):
    list_display = ('get_tipo_display', 'titolo', 'file_size_formattato', 'creato_il', 'inviato', 'email_destinatario')
    list_filter = ('tipo', 'inviato')
    search_fields = ('titolo', 'note')
    readonly_fields = ('tipo', 'titolo', 'file_path', 'file_size', 'file_name', 'contratto', 'datore', 'lavoratore', 'modello_testo', 'modello_documentale', 'note', 'creato_il', 'creato_da', 'inviato', 'inviato_il', 'email_destinatario')
    date_hierarchy = 'creato_il'
    list_per_page = 25

    @admin.display(description='DIMENSIONE')
    def file_size_formattato(self, obj):
        if obj.file_size < 1024:
            return f"{obj.file_size} B"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.1f} KB"
        else:
            return f"{obj.file_size / (1024 * 1024):.2f} MB"


@admin.register(GestoreBackup)
class BackupAdmin(admin.ModelAdmin):
    list_display = ('data_creazione', 'tipo_backup', 'note_opzionali', 'link_download')
    readonly_fields = ('data_creazione', 'file_json', 'link_download')
    actions = ['ripristina_selezionato']
    list_per_page = 25

    @admin.action(description="⚠️ RIPRISTINA il database da questo backup")
    def ripristina_selezionato(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Per favore, seleziona un solo backup per volta.", messages.ERROR)
            return
        backup = queryset.first()
        try:
            successo = backup.ripristina_comando()
            if successo:
                self.message_user(request, f"Database ripristinato con successo!", messages.SUCCESS)
            else:
                self.message_user(request, "Errore: file non trovato.", messages.ERROR)
        except Exception as e:
            self.message_user(request, f"Errore durante il ripristino: {e}", messages.ERROR)

    def link_download(self, obj):
        if obj.file_json:
            from django.urls import reverse
            url = reverse('scarica_backup_json', args=[obj.pk])
            return mark_safe(f'<a href="{url}" class="button" style="background-color: #27272a; color: white; padding: 5px 10px; border-radius: 5px; text-decoration: none;">📥 Scarica JSON</a>')
        return "File non ancora generato"
    
    link_download.short_description = "DOWNLOAD"

    def has_view_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Appuntamento)
class AppuntamentoAdmin(admin.ModelAdmin):
    list_display = ('data', 'titolo', 'tipo', 'completato')
    list_filter = ('tipo', 'completato')
    date_hierarchy = 'data'


# ====================================================
# 5b. BUSTE PAGA PERSISTENTI
# ====================================================

@admin.register(BustaPaga)
class BustaPagaAdmin(admin.ModelAdmin):
    list_display = ('contratto', 'mese', 'anno', 'tipo_calcolo', 'stato', 'totale_lordo', 'netto')
    list_filter = ('stato', 'tipo_calcolo', 'anno', 'mese')
    search_fields = ('contratto__datore__nome_cognome', 'contratto__lavoratore__nome_cognome')
    readonly_fields = ('data_calcolo', 'data_modifica', 'indennita_json', 'ratei_pagati_json', 'scatti_dettaglio_json', 'progetti_json')
    list_per_page = 25
    date_hierarchy = 'data_calcolo'


# ====================================================
# 6. REGISTRO E CESTINO
# ====================================================

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('data_ora', 'modello_coinvolto', 'azione', 'utente', 'pk_oggetto', 'indirizzo_ip')
    list_filter = ('modello_coinvolto', 'azione', 'utente')
    search_fields = ('azione', 'dettagli', 'modello_coinvolto')
    date_hierarchy = 'data_ora'
    readonly_fields = [f.name for f in AuditLog._meta.fields]
    list_per_page = 25

    def has_view_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RecordEliminato)
class RecordEliminatoAdmin(admin.ModelAdmin):
    list_display = ('get_tipo_display', 'descrizione', 'original_pk', 'eliminato_il')
    list_filter = ('tipo',)
    search_fields = ('descrizione',)
    readonly_fields = ('tipo', 'original_pk', 'dati', 'descrizione', 'eliminato_il')
    date_hierarchy = 'eliminato_il'
    list_per_page = 25

    def has_view_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ====================================================
# 7. OPZIONI E CONFIGURAZIONE
# ====================================================

@admin.register(OpzioniSoftware)
class OpzioniSoftwareAdmin(admin.ModelAdmin):
    form = OpzioniSoftwareForm
    list_display = ('nome_programma', 'versione_programma', 'denominazione_studio', 'anno_gestione')
    list_per_page = 25
    fieldsets = (
        ('Programma', {
            'classes': ('colonne-2',),
            'fields': (
                ('nome_programma', 'versione_programma'),
                ('logo', 'logo_buste_paga'),
                'cartella_documenti',
                'exe_posta',
            ),
        }),
        ('Email SMTP', {
            'classes': ('colonne-2',),
            'fields': (
                ('email_smtp_server', 'email_smtp_port'),
                ('email_smtp_username', 'email_smtp_password'),
                ('email_mittente', 'email_usa_tls'),
                'email_usa_programma_posta',
            ),
        }),
        ('Collegamenti e Link', {
            'classes': ('colonne-2',),
            'fields': (
                ('link_inps_mav', 'link_inps_iscrizione'),
                ('disponibile_1', 'disponibile_2'),
                'chromedriver_exe',
            ),
        }),
        ('Parametri di Calcolo', {
            'classes': ('colonne-2',),
            'fields': (
                ('soglia_ore_contributi', 'rateo_ferie_mensile'),
                ('soglia_paga_1_contributi', 'soglia_paga_2_contributi'),
                ('mesi_annuali_std', 'giorni_mensili_std'),
                ('settimane_annuali_std', 'anno_gestione'),
            ),
        }),
        ('Dati Studio', {
            'classes': ('colonne-2',),
            'fields': (
                ('nome_studio', 'denominazione_studio'),
                'dati_studio',
                ('comune_studio', 'cap_studio'),
            ),
        }),
        ('Recapiti Studio', {
            'classes': ('colonne-2',),
            'fields': (
                ('telefono_studio', 'email_studio'),
                'alert_contributi',
                ('tiny_api_key', 'iban_studio'),
                ('intestatario_iban', 'banca_iban'),
            ),
        }),
        ('Testi Preimpostati', {
            'classes': ('colonne-2',),
            'fields': (
                ('testo_alert_contributi', 'testo_note_avvertenze'),
                ('testo_note_footer_mail', 'testo_firma_email'),
            ),
        }),
        ('Backup', {
            'classes': ('colonne-2',),
            'fields': (
                'cartella_backup',
                ('giorni_ritenzione_backup',),
            ),
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ServizioWebConfig)
class ServizioWebConfigAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Browser / Playwright', {
            'fields': ('use_playwright', 'chrome_user_data_dir', 'headless', 'timeout_elementi', 'delay_pausa')
        }),
        ('Collegamenti INPS', {
            'fields': ('link_inps_cessazione', 'link_inps_pagopa')
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_view_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser


# ====================================================
# 8. TESTI E MODELLI
# ====================================================


@admin.register(ModelloDocumentale)
class ModelloDocumentaleAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'codice', 'titolo', 'versione', 'modificato_il')
    list_filter = ('tipo',)
    search_fields = ('codice', 'titolo', 'corpo_testo')
    list_per_page = 25


@admin.register(ModelloLista)
class ModelloListaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo_sorgente', 'is_default', 'created_at')
    list_filter = ('tipo_sorgente', 'is_default')
    search_fields = ('nome',)
    list_per_page = 25


@admin.register(ModelloComposizione)
class ModelloComposizioneAdmin(admin.ModelAdmin):
    list_display = ('nome', 'is_default', 'created_at')
    list_filter = ('is_default',)
    search_fields = ('nome',)
    list_per_page = 25


@admin.register(RiepilogoInvio)
class RiepilogoInvioAdmin(admin.ModelAdmin):
    list_display = ('creato_il', 'creato_da', 'mese', 'anno', 'totale_contratti', 'totale_ok', 'totale_errori')
    list_filter = ('creato_il', 'mese', 'anno')
    readonly_fields = ('dettaglio',)
    date_hierarchy = 'creato_il'
    list_per_page = 25


@admin.register(ModificaContratto)
class ModificaContrattoAdmin(admin.ModelAdmin):
    list_display = ('data_modifica', 'contratto', 'campo', 'valore_precedente', 'valore_nuovo', 'utente')
    list_filter = ('campo', 'data_modifica')
    search_fields = ('campo', 'contratto__datore__nome_cognome', 'contratto__lavoratore__nome_cognome')
    date_hierarchy = 'data_modifica'
    readonly_fields = ('contratto', 'campo', 'valore_precedente', 'valore_nuovo', 'data_modifica', 'utente')
    list_per_page = 25

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(HistoricalContrattoLavoro)
class HistoricalContrattoLavoroAdmin(admin.ModelAdmin):
    list_display = ('id', 'history_date', 'history_user', 'history_type', 'stato')
    list_filter = ('history_type', 'stato', 'history_date')
    search_fields = ('id', 'history_user__username')
    date_hierarchy = 'history_date'
    readonly_fields = [f.name for f in HistoricalContrattoLavoro._meta.fields]
    list_per_page = 25

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ====================================================
# 8. TABELLE DI SERVIZIO / LOG
# ====================================================


@admin.register(IndiceISTAT)
class IndiceISTATAdmin(admin.ModelAdmin):
    list_display = ('anno', 'indice')
    search_fields = ('anno',)


@admin.register(AnticipoTFR)
class AnticipoTFRAdmin(admin.ModelAdmin):
    list_display = ('contratto', 'importo', 'data', 'creato_il')
    search_fields = ('contratto__datore__nome_cognome', 'contratto__lavoratore__nome_cognome')
    list_filter = ('data',)
    date_hierarchy = 'data'


@admin.register(AccessoDatore)
class AccessoDatoreAdmin(admin.ModelAdmin):
    list_display = ('datore', 'accesso_abilitato', 'ultimo_accesso')
    search_fields = ('datore__nome_cognome',)
    list_filter = ('accesso_abilitato',)
    readonly_fields = ('password',)


@admin.register(RichiestaModificaDatore)
class RichiestaModificaDatoreAdmin(admin.ModelAdmin):
    list_display = ('datore', 'tipo', 'stato', 'creato_il', 'eliminata')
    list_filter = ('tipo', 'stato', 'eliminata')
    search_fields = ('datore__nome_cognome',)
    date_hierarchy = 'creato_il'


@admin.register(LogInvioEmail)
class LogInvioEmailAdmin(admin.ModelAdmin):
    list_display = ('destinatario', 'tipo_documento', 'data_ora', 'esito')
    list_filter = ('esito', 'tipo_documento')
    search_fields = ('destinatario',)
    date_hierarchy = 'data_ora'
    readonly_fields = ('data_ora',)

    def has_add_permission(self, request):
        return False


@admin.register(CUAnnuale)
class CUAnnualeAdmin(admin.ModelAdmin):
    list_display = ('contratto', 'anno', 'modalita', 'creato_il')
    list_filter = ('anno', 'modalita')
    search_fields = ('contratto__datore__nome_cognome', 'contratto__lavoratore__nome_cognome')
    date_hierarchy = 'creato_il'


@admin.register(LogOperazioneINPS)
class LogOperazioneINPSAdmin(admin.ModelAdmin):
    list_display = ('contratto', 'tipo_op', 'data_creazione', 'utente')
    list_filter = ('tipo_op',)
    search_fields = ('contratto__datore__nome_cognome',)
    date_hierarchy = 'data_creazione'
    readonly_fields = ('data_creazione',)

    def has_add_permission(self, request):
        return False


@admin.register(ScorciatoiaTastiera)
class ScorciatoiaTastieraAdmin(admin.ModelAdmin):
    list_display = ('label', 'tasto', 'menu_id', 'attiva', 'ordinamento')
    list_filter = ('attiva',)
    search_fields = ('label', 'menu_id', 'tasto')
    list_editable = ('tasto', 'attiva', 'ordinamento')


@admin.register(AttivitaMensile)
class AttivitaMensileAdmin(admin.ModelAdmin):
    list_display = ('label', 'categoria', 'ordine', 'obbligatorio')
    list_filter = ('categoria', 'obbligatorio')
    list_editable = ('ordine', 'obbligatorio')
    search_fields = ('label',)


@admin.register(CompletamentoMensile)
class CompletamentoMensileAdmin(admin.ModelAdmin):
    list_display = ('attivita', 'anno', 'mese', 'completato', 'completato_il', 'completato_da')
    list_filter = ('completato', 'anno', 'mese')
    search_fields = ('attivita__label', 'note')
    date_hierarchy = 'completato_il'


@admin.register(CcnlArticolo)
class CcnlArticoloAdmin(admin.ModelAdmin):
    list_display = ('articolo', 'titolo', 'anteprima')
    search_fields = ('titolo', 'testo')
    ordering = ['articolo']

    def anteprima(self, obj):
        from django.utils.html import strip_tags
        return strip_tags(obj.testo)[:80] + '…'
    anteprima.short_description = 'Anteprima'
