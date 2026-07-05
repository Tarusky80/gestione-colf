import os
import math
from datetime import date, timedelta
from simple_history import register
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.html import mark_safe, strip_tags
from django.core.management import call_command
from django.contrib.auth.models import User
from io import StringIO

from paghe import fields

try:
    import bleach
except ImportError:
    bleach = None

# --- Whitelist bleach per sanitizzazione HTML ---
BLEACH_ALLOWED_TAGS = [
    'a', 'abbr', 'b', 'blockquote', 'br', 'code', 'dd', 'div', 'dl', 'dt', 'em',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img', 'li', 'ol', 'p', 'pre',
    's', 'span', 'strong', 'sub', 'sup', 'table', 'tbody', 'td', 'th', 'thead',
    'tr', 'u', 'ul',
]
BLEACH_ALLOWED_ATTRIBUTES = {
    'a': ['href', 'target', 'rel', 'title'],
    'img': ['src', 'alt', 'width', 'height'],
    'span': ['style'],
    'div': ['style'],
    'p': ['style'],
    'td': ['style', 'colspan', 'rowspan'],
    'th': ['style', 'colspan', 'rowspan'],
    'table': ['style', 'border', 'cellpadding', 'cellspacing'],
    'hr': ['style'],
    'ol': ['style'],
    'ul': ['style'],
    'li': ['style'],
}
BLEACH_ALLOWED_STYLES = [
    'color', 'background-color', 'font-size', 'font-weight', 'font-style',
    'text-align', 'text-decoration', 'width', 'height', 'border', 'border-collapse',
    'padding', 'margin', 'vertical-align',
]

BLEACH_ALLOWED_TAGS_SIMPLE = ['b', 'i', 'u', 'strong', 'em', 'p', 'br', 'span', 'ul', 'ol', 'li']
BLEACH_ALLOWED_ATTRIBUTES_SIMPLE = {'span': ['style'], 'p': ['style']}
BLEACH_ALLOWED_STYLES_SIMPLE = ['color', 'font-weight', 'font-style']


def _sanitizza_html(testo, tags=None, attributes=None, styles=None):
    """Applica bleach.clean() se disponibile, altrimenti strip_tags()."""
    if not testo:
        return testo or ''
    if bleach:
        css_sanitizer = None
        if styles:
            from bleach.css_sanitizer import CSSSanitizer
            css_sanitizer = CSSSanitizer(allowed_css_properties=styles)
        return bleach.clean(
            testo,
            tags=tags or BLEACH_ALLOWED_TAGS,
            attributes=attributes or BLEACH_ALLOWED_ATTRIBUTES,
            css_sanitizer=css_sanitizer,
            strip=True,
        )
    return strip_tags(testo)


# ==========================================
# 0. IMPOSTAZIONI GENERALI E TESTI
# ==========================================

class OpzioniSoftware(models.Model):
    nome_programma = models.CharField(max_length=100, verbose_name="NOME PROGRAMMA", default="Paghe COLF & Badanti 2026")
    versione_programma = models.CharField(max_length=20, default="1.1", verbose_name="VERSIONE")
    logo = models.ImageField(upload_to='loghi_studio/', blank=True, null=True, verbose_name="LOGO PROGRAMMA")
    logo_buste_paga = models.ImageField(upload_to='loghi_studio/', blank=True, null=True, verbose_name="LOGO BUSTE PAGA")
    exe_posta = models.CharField(max_length=255, blank=True, verbose_name="LINK AL PROGRAMMA DI POSTA")
    exe_lettore_pdf = models.CharField(max_length=512, blank=True, verbose_name="LINK AL LETTORE PDF (per stampa diretta)")
    denominazione_studio = models.CharField(max_length=255, blank=True, verbose_name="DENOMINAZIONE STUDIO")
    cartella_documenti = models.CharField(max_length=255, blank=True, verbose_name="CARTELLA DOCUMENTI")

    email_smtp_server = models.CharField(max_length=255, blank=True, verbose_name="SERVER SMTP")
    email_smtp_port = models.IntegerField(default=587, verbose_name="PORTA SMTP")
    email_smtp_username = models.CharField(max_length=255, blank=True, verbose_name="USERNAME SMTP")
    email_smtp_password = fields.EncryptedCharField(max_length=512, blank=True, verbose_name="PASSWORD SMTP (cifrata)")
    email_mittente = models.EmailField(blank=True, verbose_name="EMAIL MITTENTE")
    email_usa_tls = models.BooleanField(default=True, verbose_name="USA TLS")
    email_usa_programma_posta = models.BooleanField(default=False, verbose_name="USA PROGRAMMA DI POSTA")
    notifiche_scadenze_attive = models.BooleanField(default=False, verbose_name="NOTIFICHE SCADENZE ATTIVE")

    link_inps_mav = models.URLField(max_length=255, verbose_name="LINK AL SITO INPS PER I PAGOPA", blank=True, default="https://serviziweb2.inps.it/PagamentiBollettiniLD/accessoUtente.do")
    link_inps_iscrizione = models.URLField(max_length=255, verbose_name="LINK AL SITO INPS PER IL LAVORO DOMESTICO", blank=True, default="https://www.inps.it/it/it/dettaglio-scheda.it.schede-servizio-strumento.schede-servizi.formalizzare-l-assunzione-di-un-lavoratore-domestico.html")
    disponibile_1 = models.URLField(max_length=255, blank=True, default="https://www.python.org", verbose_name="LINK DISPONIBILE 1")
    disponibile_2 = models.URLField(max_length=255, blank=True, default="https://googlechromelabs.github.io/chrome-for-testing/", verbose_name="LINK DISPONIBILE 2")
    chromedriver_exe = models.CharField(max_length=512, blank=True, default='drivers/chromedriver.exe', verbose_name="PERCORSO CHROMEDRIVER EXE")

    soglia_ore_contributi = models.DecimalField(max_digits=5, decimal_places=2, default=24.90, verbose_name="SOGLIA ORE CONTRIBUTI, PER VERIFICA SUPERAMENTO")
    soglia_paga_1_contributi = models.DecimalField(max_digits=6, decimal_places=2, default=9.61, verbose_name="SOGLIA PAGA 1 CONTRIBUTI (FINO A)")
    soglia_paga_2_contributi = models.DecimalField(max_digits=6, decimal_places=2, default=11.70, verbose_name="SOGLIA PAGA 2 CONTRIBUTI (FINO A)")
    rateo_ferie_mensile = models.DecimalField(max_digits=5, decimal_places=2, default=2.16, verbose_name="RATEO FERIE MENSILI")
    mesi_annuali_std = models.IntegerField(default=12, verbose_name="MESI ANNUALI STANDARD")
    giorni_mensili_std = models.IntegerField(default=26, verbose_name="GIORNI MENSILI STANDARD")
    settimane_annuali_std = models.IntegerField(default=52, verbose_name="SETTIMANE ANNUALI STANDARD")
    anno_gestione = models.IntegerField(default=2026, verbose_name="ANNO DI GESTIONE")

    nome_studio = models.CharField(max_length=255, blank=True, verbose_name="NOME STUDIO", default="CIRCOLO MCL ISILI di GABRIELE CORONGIU")
    dati_studio = models.TextField(blank=True, verbose_name="INDIRIZZO STUDIO")
    comune_studio = models.CharField(max_length=100, blank=True, verbose_name="COMUNE STUDIO")
    cap_studio = models.CharField(max_length=10, blank=True, verbose_name="CAP STUDIO")
    telefono_studio = models.CharField(max_length=100, blank=True, verbose_name="TELEFONO STUDIO")
    email_studio = models.EmailField(blank=True, verbose_name="MAIL STUDIO")
    alert_contributi = models.TextField(blank=True, verbose_name="ALERT CONTRIBUTI")
    tiny_api_key = models.CharField(max_length=100, blank=True, verbose_name="TINY API KEY")
    iban_studio = models.CharField(max_length=50, blank=True, verbose_name="IBAN STUDIO")
    intestatario_iban = models.CharField(max_length=255, blank=True, verbose_name="INTESTATARIO IBAN")
    banca_iban = models.CharField(max_length=255, blank=True, verbose_name="BANCA IBAN")

    testo_alert_contributi = models.ForeignKey('ModelloDocumentale', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', verbose_name="TESTO ALERT CONTRIBUTI", limit_choices_to={'tipo': 'TESTO_PROGRAMMA'})
    testo_note_avvertenze = models.ForeignKey('ModelloDocumentale', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', verbose_name="TESTO NOTE AVVERTENZE BUSTA", limit_choices_to={'tipo': 'TESTO_PROGRAMMA'})
    testo_note_footer_mail = models.ForeignKey('ModelloDocumentale', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', verbose_name="TESTO NOTE FOOTER MAIL", limit_choices_to={'tipo': 'TESTO_PROGRAMMA'})
    testo_firma_email = models.ForeignKey('ModelloDocumentale', null=True, blank=True, on_delete=models.SET_NULL, related_name='+', verbose_name="TESTO FIRMA EMAIL", limit_choices_to={'tipo': 'TESTO_PROGRAMMA'})

    cartella_backup = models.CharField(max_length=255, blank=True, default='', verbose_name="CARTELLA BACKUP")
    giorni_ritenzione_backup = models.IntegerField(default=30, verbose_name="GIORNI RITENZIONE BACKUP")

    class Meta:
        verbose_name = "Opzioni Software"
        verbose_name_plural = "Opzioni Software"

    def get_smtp_password(self):
        from paghe._crypto import decrypt_smtp_password
        return decrypt_smtp_password(self.email_smtp_password)

    def set_smtp_password(self, raw):
        from paghe._crypto import encrypt_smtp_password
        self.email_smtp_password = encrypt_smtp_password(raw)

    def __str__(self):
        return self.nome_programma


class RiepilogoInvio(models.Model):
    MESI = [(i, n) for i, n in enumerate(['','Gennaio','Febbraio','Marzo','Aprile','Maggio','Giugno',
        'Luglio','Agosto','Settembre','Ottobre','Novembre','Dicembre'], 0)]
    creato_il = models.DateTimeField(auto_now_add=True, verbose_name="CREATO IL")
    creato_da = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="CREATO DA", related_name='riepiloghi_invii')
    mese = models.IntegerField(choices=MESI, verbose_name="MESE")
    anno = models.IntegerField(verbose_name="ANNO")
    modello_email = models.ForeignKey('ModelloDocumentale', null=True, blank=True, on_delete=models.SET_NULL,
        limit_choices_to={'tipo': 'MAIL'}, verbose_name="MODELLO EMAIL", related_name='riepiloghi_email')
    totale_contratti = models.IntegerField(default=0, verbose_name="TOTALE CONTRATTI")
    totale_ok = models.IntegerField(default=0, verbose_name="INVIATI CON SUCCESSO")
    totale_errori = models.IntegerField(default=0, verbose_name="ERRORI")
    dettaglio = models.JSONField(default=list, verbose_name="DETTAGLIO",
        help_text="Lista di oggetti: {contratto_pk, datore, lavoratore, documento_pk, email_destinatario, inviato, errore}")
    archivio_zip_path = models.CharField(max_length=512, blank=True, verbose_name="PERCORSO ARCHIVIO ZIP")

    class Meta:
        verbose_name = "Riepilogo Invio"
        verbose_name_plural = "Riepiloghi Invio"
        ordering = ['-creato_il']

    def __str__(self):
        return f"Invio {self.mese:02d}/{self.anno} — {self.totale_ok}/{self.totale_contratti} ok"


class ModelloDocumentale(models.Model):
    TIPO_SCELTE = [
        ('CONTRATTO', 'Contratto'),
        ('CUD', 'CUD'),
        ('CARTELLINA', 'Cartellina'),
        ('RIEPILOGO_RAPPORTO', 'Riepilogo Rapporto di Lavoro'),
        ('LETTERA_ASSUNZIONE', 'Lettera Assunzione'),
        ('LETTERA_LICENZIAMENTO', 'Lettera Licenziamento'),
        ('LETTERA_DIMISSIONI', 'Lettera Dimissioni'),
        ('LETTERA_LIBERA', 'Lettera Libera'),
        ('DEROGA_TFR', 'Deroga Concordata Anticipazione TFR'),
        ('RICEVUTA', 'Ricevuta'),
        ('RICHIESTA_CUD', 'Richiesta CUD'),
        ('PDF_INIZIO', 'Inizio Rapporto'),
        ('PDF_FINE', 'Fine Rapporto'),
        ('PDF_RISCONTRO', 'Riscontro Comune'),
        ('LISTA_STAMPA', 'Lista Stampa'),
        ('BUSTA_PAGA', 'Busta Paga'),
        ('LUL', 'Libro Unico Lavoro'),
        ('MAIL', 'Modello Email'),
        ('TESTO_PROGRAMMA', 'Testi del Programma'),
        ('TOP_DOCUMENTO', 'Top Documento'),
        ('FOOTER_DOCUMENTO', 'Footer Documento'),
    ]
    tipo = models.CharField(max_length=50, choices=TIPO_SCELTE, verbose_name="TIPO DOCUMENTO")
    codice = models.CharField(max_length=50, unique=True, verbose_name="CODICE")
    titolo = models.CharField(max_length=200, blank=True, default='', verbose_name="TITOLO")
    oggetto_titolo = models.CharField(max_length=200, blank=True, default='', verbose_name="OGGETTO")
    corpo_testo = models.TextField(verbose_name="CORPO TESTO")
    note_interne = models.TextField(blank=True, verbose_name="NOTE INTERNE")
    creato_il = models.DateTimeField(auto_now_add=True, verbose_name="CREATO IL")
    modificato_il = models.DateTimeField(auto_now=True, verbose_name="MODIFICATO IL")
    versione = models.IntegerField(default=1, verbose_name="VERSIONE")
    font_family = models.CharField(max_length=100, default='Arial', verbose_name="FONT PDF")
    font_size = models.IntegerField(default=11, verbose_name="DIMENSIONE FONT")

    class Meta:
        verbose_name = "Modello documentale"
        verbose_name_plural = "Modelli documentali"
        ordering = ['tipo', 'codice']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.codice}"

    def save(self, *args, **kwargs):
        self.corpo_testo = _sanitizza_html(self.corpo_testo)
        super().save(*args, **kwargs)


class AnagraficaBase(models.Model):
    codice_fiscale = models.CharField(max_length=16, primary_key=True, verbose_name="CODICE FISCALE")
    nome_cognome = models.CharField(max_length=100, verbose_name="COGNOME E NOME")
    nome = models.CharField(max_length=100, blank=True, default='', verbose_name="NOME")
    cognome = models.CharField(max_length=100, blank=True, default='', verbose_name="COGNOME")
    indirizzo = models.CharField(max_length=200, blank=True, verbose_name="INDIRIZZO")
    comune = models.CharField(max_length=100, blank=True, verbose_name="COMUNE DI RESIDENZA")
    email = models.CharField(max_length=200, blank=True, default='', verbose_name="INDIRIZZO EMAIL", validators=[fields.MultiEmailValidator()])
    telefono = models.CharField(max_length=20, null=True, blank=True, verbose_name="NUMERO TELEFONO O CELLULARE")

    class Meta:
        abstract = True
        ordering = ['cognome', 'nome']

    def save(self, *args, **kwargs):
        self.nome_cognome = f"{self.nome} {self.cognome}".strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome_cognome


class DatoreLavoro(AnagraficaBase):
    provincia = models.CharField(max_length=4, blank=True, verbose_name="PROVINCIA")
    cap = models.CharField(max_length=5, blank=True, verbose_name="CAP")
    pin_inps = models.CharField(max_length=50, blank=True, verbose_name="PIN INPS - PIN TESSERA SANITARIA O CIE")
    invio_digitale_documenti = models.BooleanField(default=True, verbose_name="INVIO DIGITALE DEI DOCUMENTI?")
    note_datore = models.TextField(null=True, blank=True, verbose_name="NOTE DATORE DI LAVORO")
    visibile_a = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, verbose_name="VISIBILE A")

    class Meta:
        verbose_name_plural = "Anagrafica: Datori"


class Lavoratore(AnagraficaBase):
    ferie_pregresse = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="FERIE PREGRESSE")
    scatti_anzianita_maturati = models.IntegerField(default=0, verbose_name="SCATTI ANZIANITA'")
    note_lavoratore = models.TextField(null=True, blank=True, verbose_name="NOTE LAVORATORE")
    visibile_a = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, verbose_name="VISIBILE A")

    class Meta:
        verbose_name_plural = "Anagrafica: Lavoratori"


class Beneficiario(AnagraficaBase):
    provincia = models.CharField(max_length=4, blank=True, verbose_name="PROVINCIA")
    cap = models.CharField(max_length=5, blank=True, verbose_name="CAP")
    note_beneficiario = models.TextField(null=True, blank=True, verbose_name="NOTE BENEFICIARIO")

    class Meta:
        verbose_name_plural = "Anagrafica: Beneficiari"


class TipoProgettoRegionale(models.Model):
    nome = models.CharField(max_length=50, verbose_name="NOME")
    descrizione = models.TextField(null=True, blank=True, verbose_name="DESCRIZIONE")
    colore = models.CharField(max_length=7, default='#10b981', verbose_name="COLORE")

    class Meta:
        verbose_name_plural = "Tipi di Progetto Regionale"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class ProgettoRegionale(models.Model):
    beneficiario = models.ForeignKey(Beneficiario, on_delete=models.CASCADE, verbose_name="BENEFICIARIO", related_name='progetti')
    tipo = models.ForeignKey(TipoProgettoRegionale, null=True, blank=True, on_delete=models.PROTECT, verbose_name="TIPO", related_name='progetti_di_tipo')
    data_inizio = models.DateField(null=True, blank=True, verbose_name="DATA INIZIO")
    data_fine = models.DateField(null=True, blank=True, verbose_name="DATA FINE")
    budget_annuale = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, verbose_name="CIFRA ANNUALE")
    mesi = models.IntegerField(default=12, verbose_name="MESI")
    budget_mensile = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="CIFRA MENSILE DA GESTIRE")

    class Meta:
        verbose_name_plural = "Progetti Regionali"
        ordering = ['beneficiario__nome_cognome']

    def __str__(self):
        return f"{self.beneficiario} - {self.tipo}" if self.tipo else str(self.beneficiario)

    def save(self, *args, **kwargs):
        if self.budget_annuale and self.mesi > 0:
            self.budget_mensile = self.budget_annuale / self.mesi
        super().save(*args, **kwargs)


# ==========================================
# 3. TABELLE PARAMETRICHE
# ==========================================

class Livello(models.Model):
    codice = models.CharField(max_length=5, unique=True, verbose_name="CODICE")
    colore = models.CharField(max_length=7, default='#5E6AD2', verbose_name="COLORE")

    class Meta:
        verbose_name_plural = "Livelli"
        ordering = ['codice']

    def __str__(self):
        return self.codice


class ParametriCCNL(models.Model):
    livello = models.ForeignKey(Livello, on_delete=models.PROTECT, verbose_name="LIVELLO", related_name='parametri_ccnl')
    descrizione_corta = models.CharField(max_length=100, blank=True, verbose_name="DESCRIZIONE")
    descrizione_lunga = models.TextField(blank=True, verbose_name="DESCRIZIONE LUNGA")
    anno = models.IntegerField(default=2026, verbose_name="ANNO")
    paga_base = models.DecimalField(max_digits=10, decimal_places=4, default=0.0, verbose_name="RETRIBUZIONE BASE")
    retribuzione_sostituzione = models.DecimalField(max_digits=10, decimal_places=4, default=0.0, verbose_name="RETRIB. SOSTITUZIONE")
    tfr_orario = models.DecimalField(max_digits=10, decimal_places=4, default=0.0, verbose_name="TFR")
    tredicesima_oraria = models.DecimalField(max_digits=10, decimal_places=4, default=0.0, verbose_name="TREDICESIMA")
    festivi_orari = models.DecimalField(max_digits=10, decimal_places=4, default=0.3333, verbose_name="FESTIVI")
    ferie_orarie = models.DecimalField(max_digits=10, decimal_places=4, default=0.0, verbose_name="FERIE")
    ind_cert_qualita = models.DecimalField(max_digits=10, decimal_places=4, default=0.0, verbose_name="CERTIFICAZIONE DI QUALITÀ")
    ind_assistenza_piu_persone_non_conv = models.DecimalField(max_digits=10, decimal_places=4, default=0.0, verbose_name="IND. PIÙ PERSONE (NON CONV)")
    ind_minori_6_anni_non_conv = models.DecimalField(max_digits=10, decimal_places=4, default=0.0, verbose_name="IND. MINORI < 6 ANNI (NON CONV)")
    ind_piu_persone_qualita = models.DecimalField(max_digits=10, decimal_places=4, default=0.0, verbose_name="IND. PIÙ PERSONE + QUALITÀ")
    ind_minori_qualita = models.DecimalField(max_digits=10, decimal_places=4, default=0.0, verbose_name="IND. MINORI + QUALITÀ")
    ind_assistenza_piu_persone_ft = models.DecimalField(max_digits=10, decimal_places=4, default=0.0, verbose_name="IND. PIÙ PERSONE (CONV FT)")
    ind_assistenza_piu_persone_pt = models.DecimalField(max_digits=10, decimal_places=4, default=0.0, verbose_name="IND. PIÙ PERSONE (CONV PT)")
    ind_minori_6_anni_ft = models.DecimalField(max_digits=10, decimal_places=4, default=0.0, verbose_name="IND. MINORI < 6 ANNI (CONV FT)")
    ind_notturno_assistenza = models.DecimalField(max_digits=10, decimal_places=4, default=811.09, verbose_name="NOTTURNO ASSISTENZA (20-08)")
    ind_notturno_presenza = models.DecimalField(max_digits=10, decimal_places=4, default=0.0, verbose_name="NOTTURNO PRESENZA (21-08)")
    ind_notturno_base = models.DecimalField(max_digits=10, decimal_places=4, default=0.0, verbose_name="NOTTURNO PAGA BASE")
    ind_notturno_20 = models.DecimalField(max_digits=10, decimal_places=4, default=1.2, verbose_name="NOTTURNO PAGA BASE (20%)")
    notturno_tfr = models.DecimalField(max_digits=10, decimal_places=4, default=0.3208, verbose_name="NOTTURNO TFR")
    notturno_13ma = models.DecimalField(max_digits=10, decimal_places=4, default=0.3094, verbose_name="NOTTURNO TREDICESIMA")
    notturno_festivi = models.DecimalField(max_digits=10, decimal_places=4, default=0.3333, verbose_name="NOTTURNO FESTIVI")
    notturno_ferie = models.DecimalField(max_digits=10, decimal_places=4, default=0.3094, verbose_name="NOTTURNO FERIE")
    ind_funzione_conviventi = models.DecimalField(max_digits=10, decimal_places=4, default=0.0, verbose_name="INDENNITÀ FUNZIONE")
    conviventi_ft_54h = models.DecimalField(max_digits=10, decimal_places=4, default=0.0, verbose_name="CONVIVENTI FT (MAX 54H) LORDI")
    conviventi_pt_30h = models.DecimalField(max_digits=10, decimal_places=4, default=0.0, verbose_name="CONVIVENTI PT (MAX 30H)")
    convivenza_pranzo = models.DecimalField(max_digits=10, decimal_places=4, default=2.33, verbose_name="CONVIVENZA PRANZO")
    convivenza_cena = models.DecimalField(max_digits=10, decimal_places=4, default=2.33, verbose_name="CONVIVENZA CENA")
    convivenza_alloggio = models.DecimalField(max_digits=10, decimal_places=4, default=2.0, verbose_name="CONVIVENZA ALLOGGIO")
    # --- Campi mensili CCNL conviventi (Tabella A) ---
    minimo_mensile_ft = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, verbose_name="MINIMO MENSILE FT")
    minimo_mensile_pt = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, verbose_name="MINIMO MENSILE PT")
    ind_funzione_mensile = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, verbose_name="IND. FUNZIONE MENSILE")
    ind_minori_6_mensile_ft = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, verbose_name="IND. BAMBINI <6 FT MENSILE")
    ind_minori_6_mensile_pt = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, verbose_name="IND. BAMBINI <6 PT MENSILE")
    ind_piu_assistiti_mensile = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, verbose_name="IND. PIÙ ASSISTITI MENSILE")
    ind_cert_qualita_mensile = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, verbose_name="IND. CERT. QUALITÀ MENSILE")
    fonte_url = models.URLField(max_length=500, blank=True, verbose_name="FONTE URL")

    class Meta:
        verbose_name_plural = "3. Parametri CCNL"
        ordering = ['livello', 'anno']

    def __str__(self):
        return f"{self.livello} - {self.anno}"

    def save(self, *args, **kwargs):
        self.descrizione_lunga = _sanitizza_html(
            self.descrizione_lunga,
            tags=BLEACH_ALLOWED_TAGS_SIMPLE,
            attributes=BLEACH_ALLOWED_ATTRIBUTES_SIMPLE,
            styles=BLEACH_ALLOWED_STYLES_SIMPLE,
        )
        super().save(*args, **kwargs)


class TabellaCasse(models.Model):
    codice = models.CharField(max_length=2, primary_key=True, verbose_name="CODICE")
    descrizione = models.CharField(max_length=100, verbose_name="DESCRIZIONE")
    quota_datore = models.DecimalField(max_digits=10, decimal_places=4, default=0.04, verbose_name="QUOTA DATORE")
    quota_lavoratore = models.DecimalField(max_digits=10, decimal_places=4, default=0.02, verbose_name="QUOTA LAVORATORE")
    totale = models.DecimalField(max_digits=10, decimal_places=4, default=0.06, verbose_name="TOTALE")

    class Meta:
        verbose_name_plural = "Tabelle Casse (F2/E1)"
        ordering = ['codice']

    def __str__(self):
        return f"{self.codice} - {self.descrizione}"


class TabellaContributiINPS(models.Model):
    descrizione = models.CharField(max_length=100, verbose_name="DESCRIZIONE")
    quota_datore = models.DecimalField(max_digits=10, decimal_places=4, default=0.0, verbose_name="QUOTA DATORE")
    quota_lavoratore = models.DecimalField(max_digits=10, decimal_places=4, default=0.0, verbose_name="QUOTA LAVORATORE")
    totale = models.DecimalField(max_digits=10, decimal_places=4, default=0.0, verbose_name="TOTALE")

    class Meta:
        verbose_name_plural = "Tabelle Contributi INPS"
        ordering = ['descrizione']

    def __str__(self):
        return self.descrizione


class TabellaMalattia(models.Model):
    anzianita = models.CharField(max_length=100, verbose_name="ANZIANITA'")
    giorni_durata = models.IntegerField(verbose_name="GIORNI DURATA")
    conservazione_posto = models.IntegerField(verbose_name="GIORNI CONSERVAZIONE POSTO")
    soglia_mesi = models.IntegerField(default=0, verbose_name="SOGLIA MESI")

    class Meta:
        verbose_name_plural = "Tabelle Malattia"
        ordering = ['anzianita']

    def __str__(self):
        return self.anzianita


class TabellaScattiAnzianita(models.Model):
    LIVELLO_SCELTE = [
        ('A', 'A'), ('AS', 'AS'), ('B', 'B'), ('BS', 'BS'),
        ('C', 'C'), ('CS', 'CS'), ('D', 'D'), ('DS', 'DS'),
    ]
    livello = models.CharField(max_length=2, choices=LIVELLO_SCELTE, verbose_name="LIVELLO")
    valore_scatto = models.DecimalField(max_digits=10, decimal_places=4, verbose_name="VALORE SCATTO")

    class Meta:
        verbose_name_plural = "Tabelle Scatti Anzianità"
        ordering = ['livello']

    def __str__(self):
        return f"{self.livello} - €{self.valore_scatto}"


# ==========================================
# 4. CONTRATTO DI LAVORO
# ==========================================

class ContrattoLavoro(models.Model):
    datore = models.ForeignKey(DatoreLavoro, on_delete=models.CASCADE, related_name='contratti_come_datore')
    lavoratore = models.ForeignKey(Lavoratore, on_delete=models.CASCADE, related_name='contratti_come_lavoratore')
    parametri_minimi = models.ForeignKey(ParametriCCNL, on_delete=models.PROTECT, related_name='contratti_parametrizzati')
    ente_bilaterale = models.ForeignKey(TabellaCasse, on_delete=models.PROTECT, related_name='contratti_ente')
    progetto = models.ManyToManyField(ProgettoRegionale, blank=True, verbose_name="PROGETTI COLLEGATI")

    stato = models.CharField(max_length=10, choices=[('ATTIVO', 'Attivo'), ('CESSATO', 'Cessato')], default='ATTIVO', db_index=True)
    codice_rapporto_inps = models.CharField(max_length=50, blank=True)
    data_fine = models.DateField(null=True, blank=True, verbose_name="DATA FINE RAPPORTO")
    causale_cessazione = models.CharField(max_length=30, blank=True, verbose_name="CAUSALE CESSAZIONE")
    data_assunzione = models.DateField(db_index=True)
    data_inizio_tfr = models.DateField(null=True, blank=True)
    tipo_contratto = models.CharField(max_length=15, choices=[('INDETERMINATO', 'Indeterminato'), ('DETERMINATO', 'Determinato')], default='INDETERMINATO', db_index=True)
    applica_scatti = models.BooleanField(default=True, verbose_name="Applica scatti")
    applica_rivalutazione_tfr = models.BooleanField(default=False, verbose_name="Applica rivalutazione TFR")
    contratto_rinnovato_da = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='rinnovi_successivi', verbose_name="Rinnovato dal contratto")
    paga_tfr = models.BooleanField(default=True, verbose_name="TFR (deprecato)")
    MODALITA_TFR_CHOICES = [
        ('INCLUSO', 'TFR Incluso nel lordo mensile'),
        ('SEPARATO_70', 'TFR Anticipo 70% (30% accantonato)'),
        ('SEPARATO_100', 'TFR 100% Accantonato a fine rapporto'),
    ]
    modalita_tfr = models.CharField(max_length=12, choices=MODALITA_TFR_CHOICES, default='INCLUSO', verbose_name="Modalità TFR")
    paga_13ma = models.BooleanField(default=True, verbose_name="TREDICESIMA")
    paga_festivi = models.BooleanField(default=True, verbose_name="FESTIVI")
    paga_ferie = models.BooleanField(default=True, verbose_name="FERIE")
    ore_mav_custom = models.IntegerField(null=True, blank=True, verbose_name="MODIFICA ORE PAGOPA")
    ore_calcolate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, default=0.0, verbose_name="ORE CALCOLATE")

    ind_certificazione_qualita = models.BooleanField(default=False, verbose_name="CERTIFICAZIONE DI QUALITÀ")
    ind_piu_persone_non_conv = models.BooleanField(default=False, verbose_name="IND. PIÙ PERSONE (NON CONV)")
    ind_minori_non_conv = models.BooleanField(default=False, verbose_name="IND. MINORI < 6 ANNI (NON CONV)")
    ind_piu_persone_qualita = models.BooleanField(default=False, verbose_name="IND. PIÙ PERSONE + QUALITÀ")
    ind_minori_qualita = models.BooleanField(default=False, verbose_name="IND. MINORI + QUALITÀ")
    ind_assistenza_piu_persone_ft = models.BooleanField(default=False, verbose_name="IND. PIÙ PERSONE (CONV FT)")
    ind_assistenza_piu_persone_pt = models.BooleanField(default=False, verbose_name="IND. PIÙ PERSONE (CONV PT)")
    ind_minori_6_anni_ft = models.BooleanField(default=False, verbose_name="IND. MINORI < 6 ANNI (CONV FT)")
    applica_notturno_assistenza = models.BooleanField(default=False, verbose_name="NOTTURNO ASSISTENZA (20-08)")
    applica_notturno_presenza = models.BooleanField(default=False, verbose_name="NOTTURNO PRESENZA (21-08)")
    applica_notturno_base = models.BooleanField(default=False, verbose_name="NOTTURNO PAGA BASE")
    applica_notturno_20 = models.BooleanField(default=False, verbose_name="NOTTURNO PAGA BASE (20%)")
    paga_notturno_tfr = models.BooleanField(default=False, verbose_name="NOTTURNO TFR")
    paga_notturno_13ma = models.BooleanField(default=False, verbose_name="NOTTURNO TREDICESIMA")
    paga_notturno_festivi = models.BooleanField(default=False, verbose_name="NOTTURNO FESTIVI")
    paga_notturno_ferie = models.BooleanField(default=False, verbose_name="NOTTURNO FERIE")
    ind_funzione_conviventi = models.BooleanField(default=False, verbose_name="INDENNITÀ FUNZIONE")
    ind_conviventi_ft_54h = models.BooleanField(default=False, verbose_name="CONVIVENTI FT (54H)")
    ind_conviventi_pt_30h = models.BooleanField(default=False, verbose_name="CONVIVENTI PT (30H)")
    is_convivente = models.BooleanField(default=False, verbose_name="Lavoratore Convivente (Sì/No)", db_index=True)
    usa_ind_funzione_mensile = models.BooleanField(default=False, verbose_name="USA IND. FUNZIONE MENSILE")
    usa_ind_minori_6_mensile_ft = models.BooleanField(default=False, verbose_name="USA IND. MINORI <6 FT MENSILE")
    usa_ind_minori_6_mensile_pt = models.BooleanField(default=False, verbose_name="USA IND. MINORI <6 PT MENSILE")
    usa_ind_piu_assistiti_mensile = models.BooleanField(default=False, verbose_name="USA IND. PIÙ ASSISTITI MENSILE")
    usa_ind_cert_qualita_mensile = models.BooleanField(default=False, verbose_name="USA IND. CERT. QUALITÀ MENSILE")
    usa_retribuzione_sostituzione = models.BooleanField(default=False, verbose_name="USA RETRIBUZIONE SOSTITUZIONE")
    paga_pranzo = models.BooleanField(default=False, verbose_name="CONVIVENZA PRANZO")
    paga_cena = models.BooleanField(default=False, verbose_name="CONVIVENZA CENA")
    paga_alloggio = models.BooleanField(default=False, verbose_name="CONVIVENZA ALLOGGIO")
    note_post_it = models.TextField(null=True, blank=True, verbose_name="NOTE / POST-IT")
    giorni_malattia_usati_anno = models.IntegerField(default=0, verbose_name="GIORNI MALATTIA GIÀ USATI NELL'ANNO")
    contributi_trimestre_versati = models.BooleanField(default=False, verbose_name="CONTRIBUTI TRIMESTRE VERSATI")
    busta_template = models.ForeignKey('ModelloDocumentale', null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Template Busta Paga", limit_choices_to={'tipo': 'BUSTA_PAGA'}, related_name='contratti_template_busta')
    visibile_a = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, verbose_name="VISIBILE A")

    class Meta:
        verbose_name_plural = "6. Anagrafica: Contratti"
        ordering = ['datore__nome_cognome', 'lavoratore__nome_cognome']

    def __str__(self):
        return f"{self.datore} -> {self.lavoratore}"

    # --- Proprietà di calcolo ---

    @property
    def costo_mensile_reale(self):
        ultima = self.buste.filter(stato__in=['APPROVATA','ARCHIVIATA']).order_by('-anno','-mese').first()
        if not ultima:
            return None
        return float(ultima.totale_lordo or 0) + float(ultima.totale_contributi or 0)

    @property
    def budget_di_partenza(self):
        progetti = self.progetto.all()
        if progetti:
            return sum(float(p.budget_mensile or 0) for p in progetti)
        return 0.0

    @property
    def budget_annuale_totale(self):
        return round(self.budget_di_partenza * 12, 2)

    @property
    def ore_mensili_calcolate(self):
        return float(self.ore_calcolate) if self.ore_calcolate else 0.0

    @property
    def ore_settimanali_calcolate(self):
        ore_m = self.ore_mensili_calcolate
        return ore_m / 4.33 if ore_m > 0 else 0.0

    @property
    def paga_oraria_totale(self):
        ore_m = self.ore_mensili_calcolate
        bdp = self.budget_di_partenza
        return bdp / ore_m if ore_m > 0 else 0.0

    @property
    def quota_convivenza_mensile(self):
        p = self.parametri_minimi
        if not p:
            return 0.0
        from paghe.views._common_imports import get_opzioni
        opz = get_opzioni()
        giorni = opz.giorni_mensili_std if opz else 26
        totale = 0.0
        if self.paga_pranzo:
            totale += float(p.convivenza_pranzo) * giorni
        if self.paga_cena:
            totale += float(p.convivenza_cena) * giorni
        if self.paga_alloggio:
            totale += float(p.convivenza_alloggio) * giorni
        return round(totale, 2)

    @property
    def trattenuta_ratei_accantonati(self):
        p = self.parametri_minimi
        if not p:
            return 0.0
        ore_m = self.ore_mensili_calcolate
        if ore_m <= 0:
            return 0.0
        totale = 0.0
        mapping_ratei = [
            ('paga_tfr', p.tfr_orario, 'TFR'),
            ('paga_13ma', p.tredicesima_oraria, '13ª'),
            ('paga_ferie', p.ferie_orarie, 'Ferie'),
            ('paga_festivi', p.festivi_orari, 'Festivi'),
            ('paga_notturno_tfr', p.notturno_tfr, 'TFR Notturno'),
            ('paga_notturno_13ma', p.notturno_13ma, '13ª Notturna'),
            ('paga_notturno_ferie', p.notturno_ferie, 'Ferie Notturne'),
            ('paga_notturno_festivi', p.notturno_festivi, 'Festivi Notturni'),
        ]
        for attr, val_orario, _label in mapping_ratei:
            if attr == 'paga_tfr':
                mt = self.modalita_tfr
                if mt == 'INCLUSO':
                    continue
                coeff = 0.3 if mt == 'SEPARATO_70' else 1.0
                totale += float(val_orario) * ore_m * coeff
            elif getattr(self, attr, False):
                totale += float(val_orario) * ore_m
        return round(totale, 2)

    @property
    def totale_tfr_accantonato_cumulativo(self):
        if not self.data_inizio_tfr or self.modalita_tfr == 'INCLUSO':
            return 0.0
        from datetime import date
        oggi = date.today()
        mesi = (oggi.year - self.data_inizio_tfr.year) * 12 + (oggi.month - self.data_inizio_tfr.month) + 1
        if mesi <= 0:
            return 0.0
        p = self.parametri_minimi
        if not p:
            return 0.0
        ore_m = self.ore_mensili_calcolate
        if ore_m <= 0:
            return 0.0
        coeff = 0.3 if self.modalita_tfr == 'SEPARATO_70' else 1.0
        tfr_mensile = float(p.tfr_orario) * ore_m * coeff
        totale = round(tfr_mensile * mesi, 2)
        anticipi = sum(float(a.importo) for a in self.anticipi_tfr.all()) if self.pk else 0
        return max(totale - anticipi, 0.0)

    @property
    def proiezione_tfr_annuale(self):
        if not self.data_inizio_tfr or self.modalita_tfr == 'INCLUSO':
            return 0.0
        from datetime import date
        oggi = date.today()
        fine_anno = date(oggi.year, 12, 31)
        if self.data_inizio_tfr > fine_anno:
            return 0.0
        inizio = max(self.data_inizio_tfr, date(oggi.year, 1, 1))
        mesi_totali = (fine_anno.year - inizio.year) * 12 + (fine_anno.month - inizio.month) + 1
        if mesi_totali <= 0:
            return 0.0
        p = self.parametri_minimi
        if not p:
            return 0.0
        ore_m = self.ore_mensili_calcolate
        if ore_m <= 0:
            return 0.0
        coeff = 0.3 if self.modalita_tfr == 'SEPARATO_70' else 1.0
        tfr_mensile = float(p.tfr_orario) * ore_m * coeff
        return round(tfr_mensile * mesi_totali, 2)

    # --- Proprietà per Admin readonly_fields ---

    def stima_netto_mensile(self):
        try:
            from .views import _calcola_busta_data
            oggi = date.today()
            data = _calcola_busta_data(self, oggi.month, oggi.year)
            if 'errore' in data:
                return mark_safe(f'<span style="color:#ef4444;">{data["errore"]}</span>')
            netto = data.get('netto', 0)
            return mark_safe(
                f'<div style="font-size:16px;font-weight:700;color:#10b981;">€ {netto:,.2f}</div>'
                f'<div style="font-size:12px;color:#a1a1aa;">Lordo: € {data.get("totale_lordo", 0):,.2f} | '
                f'Contributi: € {data.get("contributi", {}).get("totale", 0):,.2f} | '
                f'Trattenute: € {data.get("trattenute", {}).get("totale", 0):,.2f}</div>'
            )
        except Exception as e:
            return mark_safe(f'<span style="color:#ef4444;">Errore: {e}</span>')
    stima_netto_mensile.short_description = 'Stima Netto Mensile'

    def prospetto_ore_mensili(self):
        ore_m = self.ore_mensili_calcolate
        ore_sett = self.ore_settimanali_calcolate
        ore_inps = math.ceil(ore_m)
        return mark_safe(
            f'<div><b>Mensili:</b> {ore_m:.2f}h</div>'
            f'<div><b>Settimanali:</b> {ore_sett:.2f}h</div>'
            f'<div><b>INPS:</b> {ore_inps}h</div>'
            f'<div><b>Calcolate:</b> {self.ore_calcolate}h</div>'
        )
    prospetto_ore_mensili.short_description = 'Prospetto Ore'

    def costo_mensile_effettivo(self):
        try:
            from .views import _calcola_busta_data
            oggi = date.today()
            data = _calcola_busta_data(self, oggi.month, oggi.year)
            if 'errore' in data:
                return mark_safe(f'<span style="color:#ef4444;">{data["errore"]}</span>')
            lordo = data.get('totale_lordo', 0)
            contrib = data.get('contributi', {}).get('totale', 0)
            return mark_safe(
                f'<div style="font-size:15px;font-weight:700;">€ {(lordo + contrib):,.2f}</div>'
                f'<div style="font-size:11px;color:#a1a1aa;">Lordo €{lordo:,.2f} + Contributi €{contrib:,.2f}</div>'
            )
        except Exception as e:
            return mark_safe(f'<span style="color:#ef4444;">Errore: {e}</span>')
    costo_mensile_effettivo.short_description = 'Costo Mensile Effettivo'

    def differenza_budget(self):
        try:
            from .views import _calcola_busta_data
            oggi = date.today()
            data = _calcola_busta_data(self, oggi.month, oggi.year)
            if 'errore' in data:
                return mark_safe(f'<span style="color:#ef4444;">{data["errore"]}</span>')
            budget = data.get('budget_mensile', 0)
            contrib = data.get('contributi', {}).get('totale', 0)
            trattenute = data.get('trattenute', {}).get('totale', 0)
            differenza = budget - (contrib + trattenute)
            colore = '#10b981' if differenza >= 0 else '#ef4444'
            return mark_safe(
                f'<div style="font-size:15px;font-weight:700;color:{colore};">€ {differenza:,.2f}</div>'
                f'<div style="font-size:11px;color:#a1a1aa;">Budget €{budget:,.2f} - Costi €{(contrib+trattenute):,.2f}</div>'
            )
        except Exception as e:
            return mark_safe(f'<span style="color:#ef4444;">Errore: {e}</span>')
    differenza_budget.short_description = 'Differenza Budget'

    def verifica_soglia_contributi(self):
        ore_sett = self.ore_settimanali_calcolate
        from paghe.views._common_imports import get_opzioni
        opz = get_opzioni()
        soglia = float(opz.soglia_ore_contributi) if opz else 24.90
        sopra = ore_sett > soglia
        icona = '&#10003; S&igrave;' if sopra else '&#10007; No'
        colore = '#10b981' if sopra else '#ef4444'
        return mark_safe(
            f'<div style="font-size:14px;color:{colore};font-weight:600;">{icona}</div>'
            f'<div style="font-size:11px;color:#a1a1aa;">{ore_sett:.2f}h sett > {soglia}h soglia</div>'
        )
    verifica_soglia_contributi.short_description = 'Soglia Contributi'

    def dettaglio_indennita(self):
        p = self.parametri_minimi
        if not p:
            return mark_safe('<span style="color:#ef4444;">Parametri mancanti</span>')
        righe = []
        mapping = [
            ('ind_certificazione_qualita', p.ind_cert_qualita, 'Cert. Qualità'),
            ('ind_piu_persone_non_conv', p.ind_assistenza_piu_persone_non_conv, 'Più Pers. (NC)'),
            ('ind_minori_non_conv', p.ind_minori_6_anni_non_conv, 'Minori <6 (NC)'),
            ('ind_piu_persone_qualita', p.ind_piu_persone_qualita, 'Più Pers. + Qual.'),
            ('ind_minori_qualita', p.ind_minori_qualita, 'Minori + Qual.'),
            ('ind_assistenza_piu_persone_ft', p.ind_assistenza_piu_persone_ft, 'Più Pers. (FT)'),
            ('ind_assistenza_piu_persone_pt', p.ind_assistenza_piu_persone_pt, 'Più Pers. (PT)'),
            ('ind_minori_6_anni_ft', p.ind_minori_6_anni_ft, 'Minori <6 (FT)'),
            ('ind_funzione_conviventi', p.ind_funzione_conviventi, 'Funz. Conv.'),
            ('applica_notturno_base', p.ind_notturno_base, 'Nott. Base'),
            ('applica_notturno_20', p.ind_notturno_20, 'Nott. 20%'),
        ]
        for attr, val, label in mapping:
            if getattr(self, attr, False):
                righe.append(f'<tr><td>{label}</td><td style="text-align:right;">€{float(val):.4f}/h</td></tr>')
        if not righe:
            return mark_safe('<span style="color:#a1a1aa;">Nessuna indennità</span>')
        return mark_safe(
            '<table style="font-size:12px;width:100%;">'
            + ''.join(righe)
            + '</table>'
        )
    dettaglio_indennita.short_description = 'Dettaglio Indennità'

    def alert_fine_prova(self):
        if not self.data_assunzione:
            return mark_safe('<span style="color:#a1a1aa;">N/D</span>')
        fine_prova = self.data_assunzione + timedelta(days=26 * 6)
        oggi = date.today()
        if oggi > fine_prova:
            return mark_safe(f'<span style="color:#10b981;">&#10003; Scaduto il {fine_prova.strftime("%d/%m/%Y")}</span>')
        giorni_mancanti = (fine_prova - oggi).days
        if giorni_mancanti <= 10:
            return mark_safe(f'<span style="color:#ef4444;font-weight:700;">&#9888; Scade tra {giorni_mancanti}gg ({fine_prova.strftime("%d/%m/%Y")})</span>')
        return mark_safe(f'<span style="color:#f59e0b;">Scade tra {giorni_mancanti}gg ({fine_prova.strftime("%d/%m/%Y")})</span>')
    alert_fine_prova.short_description = 'Fine Periodo Prova'

    def alert_scatti_anzianita(self):
        if not self.applica_scatti or not self.data_assunzione:
            return mark_safe('<span style="color:#a1a1aa;">Non applicabile</span>')
        oggi = date.today()
        anni = oggi.year - self.data_assunzione.year
        if (oggi.month, oggi.day) < (self.data_assunzione.month, self.data_assunzione.day):
            anni -= 1
        bienni_maturati = min(anni // 2, 7)
        prossimo_biennio = (anni // 2) + 1
        if prossimo_biennio > 7:
            return mark_safe(f'<span style="color:#10b981;">&#10003; Massimo scatti raggiunti ({bienni_maturati})</span>')
        data_prossimo = date(self.data_assunzione.year + prossimo_biennio * 2, self.data_assunzione.month, self.data_assunzione.day)
        giorni_mancanti = (data_prossimo - oggi).days
        if giorni_mancanti <= 30:
            return mark_safe(f'<span style="color:#ef4444;font-weight:700;">&#9888; Prossimo scatto tra {giorni_mancanti}gg ({data_prossimo.strftime("%d/%m/%Y")})</span>')
        return mark_safe(f'<span style="color:#f59e0b;">Prossimo scatto tra {giorni_mancanti}gg</span>')
    alert_scatti_anzianita.short_description = 'Scatti Anzianità'

    def _calcola_ore(self):
        if not self.pk:
            return
        p = self.parametri_minimi
        if not p:
            return
        budget = self.budget_di_partenza
        if budget <= 0:
            self.ore_calcolate = 0
            return
        paga_oraria = float(p.paga_base)
        if self.paga_13ma:
            paga_oraria += float(p.tredicesima_oraria)
        if self.paga_ferie:
            paga_oraria += float(p.ferie_orarie)
        if self.paga_festivi:
            paga_oraria += float(p.festivi_orari)
        mt = self.modalita_tfr
        if mt == 'INCLUSO':
            paga_oraria += float(p.tfr_orario)
        elif mt == 'SEPARATO_70':
            paga_oraria += float(p.tfr_orario) * 0.7
        ind_mapping = [
            ('ind_certificazione_qualita', p.ind_cert_qualita),
            ('ind_piu_persone_non_conv', p.ind_assistenza_piu_persone_non_conv),
            ('ind_minori_non_conv', p.ind_minori_6_anni_non_conv),
            ('ind_piu_persone_qualita', p.ind_piu_persone_qualita),
            ('ind_minori_qualita', p.ind_minori_qualita),
            ('ind_assistenza_piu_persone_ft', p.ind_assistenza_piu_persone_ft),
            ('ind_assistenza_piu_persone_pt', p.ind_assistenza_piu_persone_pt),
            ('ind_minori_6_anni_ft', p.ind_minori_6_anni_ft),
            ('ind_funzione_conviventi', p.ind_funzione_conviventi),
            ('applica_notturno_base', p.ind_notturno_base),
            ('applica_notturno_20', p.ind_notturno_20),
        ]
        for attr, val in ind_mapping:
            if getattr(self, attr, False):
                paga_oraria += float(val or 0)
        if self.applica_scatti and self.data_assunzione:
            anni = date.today().year - self.data_assunzione.year
            if (date.today().month, date.today().day) < (self.data_assunzione.month, self.data_assunzione.day):
                anni -= 1
            bienni = min(anni // 2, 7)
            scatto_obj = TabellaScattiAnzianita.objects.filter(livello=p.livello.codice).first()
            if scatto_obj:
                paga_oraria += float(scatto_obj.valore_scatto) * bienni
        if paga_oraria > 0:
            self.ore_calcolate = math.ceil(budget / paga_oraria)
        else:
            self.ore_calcolate = 0

    def save(self, *args, **kwargs):
        self._calcola_ore()
        super().save(*args, **kwargs)


register(ContrattoLavoro)


class IndiceISTAT(models.Model):
    anno = models.IntegerField(unique=True, verbose_name="ANNO")
    indice = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="INDICE FOI")

    class Meta:
        verbose_name = "Indice ISTAT FOI"
        verbose_name_plural = "Indici ISTAT FOI"
        ordering = ['-anno']

    def __str__(self):
        return f"ISTAT {self.anno}: {self.indice}"


class AnticipoTFR(models.Model):
    contratto = models.ForeignKey(ContrattoLavoro, on_delete=models.CASCADE, verbose_name="CONTRATTO", related_name='anticipi_tfr')
    importo = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="IMPORTO")
    data = models.DateField(verbose_name="DATA")
    note = models.TextField(blank=True, verbose_name="NOTE")
    creato_il = models.DateTimeField(auto_now_add=True, verbose_name="CREATO IL")

    class Meta:
        verbose_name = "Anticipo TFR"
        verbose_name_plural = "Anticipi TFR"
        ordering = ['-data']

    def __str__(self):
        return f"Anticipo TFR {self.importo} ({self.data}) - {self.contratto}"


class ModificaContratto(models.Model):
    contratto = models.ForeignKey('ContrattoLavoro', on_delete=models.CASCADE, related_name='modifiche')
    campo = models.CharField(max_length=50, verbose_name="CAMPO MODIFICATO")
    valore_precedente = models.TextField(blank=True, verbose_name="VALORE PRECEDENTE")
    valore_nuovo = models.TextField(blank=True, verbose_name="VALORE NUOVO")
    data_modifica = models.DateTimeField(auto_now_add=True, verbose_name="DATA MODIFICA")
    utente = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="UTENTE", related_name='modifiche_contratti')

    class Meta:
        verbose_name = "Modifica Contratto"
        verbose_name_plural = "Modifiche Contratti"
        ordering = ['-data_modifica']

    def __str__(self):
        return f"{self.data_modifica.strftime('%d/%m/%Y %H:%M')} - {self.campo}"


class ContrattoAttivo(ContrattoLavoro):
    class Meta:
        proxy = True
        verbose_name_plural = "Contratti Attivi"


class ContrattoCessato(ContrattoLavoro):
    class Meta:
        proxy = True
        verbose_name_plural = "Contratti Cessati"


# ==========================================
# 5. BUSTE PAGA PERSISTENTI
# ==========================================

class BustaPaga(models.Model):
    STATO_CHOICES = [
        ('BOZZA', 'Bozza'),
        ('APPROVATA', 'Approvata'),
        ('ARCHIVIATA', 'Archiviata'),
    ]
    contratto = models.ForeignKey('ContrattoLavoro', on_delete=models.CASCADE, verbose_name="CONTRATTO", related_name='buste')
    mese = models.IntegerField(verbose_name="MESE")
    anno = models.IntegerField(verbose_name="ANNO")
    tipo_calcolo = models.CharField(max_length=20, verbose_name="TIPO CALCOLO",
        help_text="CONVIVENTE / NON_CONVIVENTE / SOSTITUZIONE")
    stato = models.CharField(max_length=10, choices=STATO_CHOICES, default='BOZZA', verbose_name="STATO")
    data_calcolo = models.DateTimeField(auto_now_add=True, verbose_name="DATA CALCOLO")
    data_modifica = models.DateTimeField(auto_now=True, verbose_name="ULTIMA MODIFICA")

    budget_mensile = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="BUDGET MENSILE")
    ore_mensili = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="ORE MENSILI")
    ore_inps = models.IntegerField(verbose_name="ORE INPS")
    ore_settimanali = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="ORE SETTIMANALI")
    paga_oraria_lorda = models.DecimalField(max_digits=8, decimal_places=4, verbose_name="PAGA ORARIA LORDA")

    paga_base_totale = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="PAGA BASE TOTALE")
    totale_indennita = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="TOTALE INDENNITÀ")
    scatti_totale = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name="SCATTI TOTALI")
    totale_lordo = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="TOTALE LORDO")

    contributi_inps_orario = models.DecimalField(max_digits=8, decimal_places=4, default=0, verbose_name="INPS ORARIO")
    contributi_inps_totale = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="INPS TOTALE")
    contributi_inps_fascia = models.CharField(max_length=10, blank=True, verbose_name="FASCIA INPS")
    contributi_inps_quota_datore = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="INPS QUOTA DATORE TOTALE")
    contributi_inps_quota_lavoratore = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="INPS QUOTA LAVORATORE TOTALE")
    contributi_cassa_orario = models.DecimalField(max_digits=8, decimal_places=4, default=0, verbose_name="CASSA ORARIO")
    contributi_cassa_totale = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="CASSA TOTALE")
    contributi_cassa_nome = models.CharField(max_length=100, blank=True, verbose_name="NOME CASSA")
    totale_contributi = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="TOTALE CONTRIBUTI")

    convivenza_totale = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="CONVIVENZA TOTALE")
    totale_accantonati = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="RATEI ACCANTONATI")
    netto = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="NETTO")

    indennita_json = models.JSONField(default=dict, blank=True, verbose_name="INDENNITÀ (JSON)")
    ratei_pagati_json = models.JSONField(default=list, blank=True, verbose_name="RATEI (JSON)")
    scatti_dettaglio_json = models.JSONField(default=dict, blank=True, verbose_name="SCATTI (JSON)")
    progetti_json = models.JSONField(default=list, blank=True, verbose_name="PROGETTI (JSON)")
    tfr_data = models.JSONField(default=dict, blank=True, verbose_name="DATI LIQUIDAZIONE TFR")

    documento = models.ForeignKey('DocumentoArchiviato', null=True, blank=True, on_delete=models.SET_NULL, verbose_name="DOCUMENTO PDF", related_name='buste_paga')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['contratto', 'mese', 'anno'], name='unique_busta_contratto_mese_anno'),
        ]
        ordering = ['-anno', '-mese', 'contratto__datore__nome_cognome']
        verbose_name = "Busta Paga"
        verbose_name_plural = "Buste Paga"

    def __str__(self):
        return f"{self.contratto} — {self.mese:02d}/{self.anno} ({self.tipo_calcolo})"


# ==========================================
# 6. GESTIONE BACKUP
# ==========================================

class GestoreBackup(models.Model):
    TIPO_BACKUP = [
        ('COMPLETO', '1. Completo'),
        ('ANAGRAFICHE', '2. Solo Anagrafiche'),
        ('CONTRATTI', '3. Solo Contratti e Progetti'),
        ('PARAMETRI', '4. Solo Tabelle Parametriche'),
    ]
    data_creazione = models.DateTimeField(auto_now_add=True)
    tipo_backup = models.CharField(max_length=20, choices=TIPO_BACKUP, default='COMPLETO')
    note_opzionali = models.CharField(max_length=200, blank=True)
    file_json = models.CharField(max_length=500, blank=True, default='')
    file_db = models.CharField(max_length=500, blank=True, default='')

    class Meta:
        verbose_name_plural = "Gestione Backup"
        ordering = ['-data_creazione']

    def __str__(self):
        return f"{self.get_tipo_backup_display()} - {self.data_creazione.strftime('%d/%m/%Y %H:%M')}"

    @staticmethod
    def _get_backup_dir():
        from django.conf import settings
        from paghe.views._common_imports import get_opzioni
        opzioni = get_opzioni()
        if opzioni and opzioni.cartella_backup:
            return opzioni.cartella_backup
        return os.path.join(settings.MEDIA_ROOT, 'backups')

    @staticmethod
    def _pulisci_backup_vecchi(giorni=None):
        if giorni is None:
            from paghe.views._common_imports import get_opzioni
            opzioni = get_opzioni()
            giorni = opzioni.giorni_ritenzione_backup if opzioni else 30
        from datetime import timedelta
        soglia = timezone.now() - timedelta(days=giorni)
        vecchi = GestoreBackup.objects.filter(data_creazione__lt=soglia)
        count = vecchi.count()
        for b in vecchi:
            if b.file_json and os.path.isfile(b.file_json):
                os.remove(b.file_json)
            if b.file_db and os.path.isfile(b.file_db):
                os.remove(b.file_db)
        vecchi.delete()
        return count

    @property
    def file_size_display(self):
        try:
            if self.file_json and os.path.isfile(self.file_json):
                size = os.path.getsize(self.file_json)
                if size < 1024:
                    return f"{size} B"
                elif size < 1024 * 1024:
                    return f"{size / 1024:.1f} KB"
                else:
                    return f"{size / (1024 * 1024):.2f} MB"
            return "N/D"
        except Exception:
            return "N/D"

    @property
    def db_size_display(self):
        try:
            if self.file_db and os.path.isfile(self.file_db):
                size = os.path.getsize(self.file_db)
                if size < 1024:
                    return f"{size} B"
                elif size < 1024 * 1024:
                    return f"{size / 1024:.1f} KB"
                else:
                    return f"{size / (1024 * 1024):.2f} MB"
            return "—"
        except Exception:
            return "—"

    def _crea_backup_db(self):
        import sqlite3, zipfile, tempfile
        src_path = settings.DATABASES['default']['NAME']
        if not os.path.isfile(src_path):
            return
        if not self.file_json:
            return
        oggi = timezone.now().strftime('%Y%m%d_%H%M%S')
        tipo = self.get_tipo_backup_display().split('.')[0].strip() if self.tipo_backup else 'COMPLETO'
        nome_zip = f"backup_db_{tipo}_{oggi}.zip"
        backup_dir = self._get_backup_dir()
        zip_path = os.path.join(backup_dir, nome_zip)
        os.makedirs(backup_dir, exist_ok=True)
        tmp_db = tempfile.mktemp(suffix='.db')
        try:
            src_conn = sqlite3.connect(src_path)
            dest_conn = sqlite3.connect(tmp_db)
            src_conn.backup(dest_conn)
            dest_conn.close()
            src_conn.close()
            json_path = self.file_json
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.write(tmp_db, 'db.sqlite3')
                if os.path.isfile(json_path):
                    zf.write(json_path, os.path.basename(json_path))
            self.file_db = zip_path
        finally:
            if os.path.isfile(tmp_db):
                os.unlink(tmp_db)

    def save(self, *args, **kwargs):
        if not self.pk:
            if not self.file_json:
                oggi = timezone.now().strftime('%Y%m%d_%H%M%S')
                tipo = self.get_tipo_backup_display().split('.')[0].strip() if self.tipo_backup else 'COMPLETO'
                nome_file = f"backup_{tipo}_{oggi}.json"
                backup_dir = self._get_backup_dir()
                filepath = os.path.join(backup_dir, nome_file)
                os.makedirs(backup_dir, exist_ok=True)

                if self.tipo_backup == 'ANAGRAFICHE':
                    app_labels = ['DatoreLavoro', 'Lavoratore', 'Beneficiario']
                elif self.tipo_backup == 'CONTRATTI':
                    app_labels = ['ContrattoLavoro', 'ContrattoAttivo', 'ContrattoCessato', 'ProgettoRegionale', 'TipoProgettoRegionale']
                elif self.tipo_backup == 'PARAMETRI':
                    app_labels = ['ParametriCCNL', 'Livello', 'TabellaCasse', 'TabellaContributiINPS', 'TabellaMalattia', 'TabellaScattiAnzianita', 'OpzioniSoftware']
                else:
                    app_labels = None

                try:
                    output = StringIO()
                    if app_labels:
                        for model_name in app_labels:
                            call_command('dumpdata', f'paghe.{model_name}', stdout=output, format='json', indent=2)
                    else:
                        call_command('dumpdata', 'paghe', stdout=output, format='json', indent=2, exclude=['paghe.auditlog', 'paghe.gestorebackup', 'paghe.recordeliminato', 'paghe.documentoarchiviato'])
                    contenuto = output.getvalue()

                    if not contenuto or contenuto.strip() in ('[]', '[ ]', ''):
                        raise ValueError("Nessun dato da salvare (dumpdata vuoto)")

                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(contenuto)
                    self.file_json = filepath
                    self._crea_backup_db()
                except Exception as e:
                    if os.path.isfile(filepath):
                        os.unlink(filepath)
                    raise e
        super().save(*args, **kwargs)

    def ripristina_comando(self):
        if not self.file_json:
            return False
        if not os.path.isfile(self.file_json):
            return False
        try:
            call_command('loaddata', self.file_json, format='json')
            return True
        except Exception:
            return False


# ==========================================
# 6a. AGENDA APPUNTAMENTI
# ==========================================

class Appuntamento(models.Model):
    TIPO_CHOICES = [
        ('SCADENZA', 'Scadenza'),
        ('APPUNTAMENTO', 'Appuntamento'),
        ('PROMEMORIA', 'Promemoria'),
    ]
    RICORRENZA_CHOICES = [
        ('NESSUNA', 'Nessuna'),
        ('SETTIMANALE', 'Settimanale'),
        ('MENSILE', 'Mensile'),
        ('ANNUALE', 'Annuale'),
    ]
    data = models.DateField(verbose_name="Data")
    ora = models.TimeField(null=True, blank=True, verbose_name="Ora")
    titolo = models.CharField(max_length=200, verbose_name="Titolo")
    descrizione = models.TextField(blank=True, verbose_name="Descrizione")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='PROMEMORIA', verbose_name="Tipo")
    ricorrenza = models.CharField(max_length=20, choices=RICORRENZA_CHOICES, default='NESSUNA', verbose_name="Ricorrenza")
    colore = models.CharField(max_length=7, blank=True, default='', verbose_name="Colore")
    completato = models.BooleanField(default=False, verbose_name="Completato")
    creato_il = models.DateTimeField(auto_now_add=True, verbose_name="Creato il")

    class Meta:
        verbose_name = "Appuntamento"
        verbose_name_plural = "Agenda Appuntamenti"
        ordering = ['data', 'pk']

    def __str__(self):
        label = f" {self.get_ricorrenza_display()}" if self.ricorrenza != 'NESSUNA' else ''
        return f"{self.data.strftime('%d/%m/%Y')} - {self.titolo}{label}"


# ==========================================
# 7. AUDIT, CESTINO, DOCUMENTI
# ==========================================

class AuditLog(models.Model):
    data_ora = models.DateTimeField(auto_now_add=True)
    modello_coinvolto = models.CharField(max_length=50, verbose_name="Modello")
    azione = models.CharField(max_length=255, verbose_name="Azione")
    dettagli = models.TextField(blank=True, verbose_name="Dettagli")
    utente = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Utente")
    pk_oggetto = models.CharField(max_length=50, blank=True, verbose_name="PK Oggetto")
    dati_precedenti = models.JSONField(null=True, blank=True, verbose_name="Dati precedenti")
    dati_successivi = models.JSONField(null=True, blank=True, verbose_name="Dati successivi")
    indirizzo_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="Indirizzo IP")

    class Meta:
        verbose_name_plural = "Registro di Audit (Scatola Nera)"
        ordering = ['-data_ora']

    def __str__(self):
        return f"{self.data_ora.strftime('%d/%m/%Y %H:%M')} - {self.modello_coinvolto} - {self.azione[:50]}"


class RecordEliminato(models.Model):
    TIPO_SCELTE = [
        ('datore', 'Datore'),
        ('lavoratore', 'Lavoratore'),
        ('beneficiario', 'Beneficiario'),
        ('contratto', 'Contratto'),
        ('progetto', 'Progetto Regionale'),
        ('parametro_ccnl', 'Parametro CCNL'),
        ('tabella_casse', 'Tabella Casse'),
        ('contributi_inps', 'Contributi INPS'),
        ('malattia', 'Malattia'),
        ('scatti_anzianita', 'Scatti Anzianità'),
        ('testo_preimpostato', 'Testo Preimpostato'),
        ('tipo_progetto', 'Tipo Progetto'),
        ('livello', 'Livello'),
    ]
    tipo = models.CharField(max_length=50, choices=TIPO_SCELTE, verbose_name="Tipo")
    original_pk = models.CharField(max_length=255, verbose_name="PK originale")
    dati = models.JSONField(verbose_name="Dati del record")
    descrizione = models.CharField(max_length=255, verbose_name="Descrizione")
    eliminato_il = models.DateTimeField(auto_now_add=True, verbose_name="Eliminato il")

    class Meta:
        verbose_name = "Record eliminato"
        verbose_name_plural = "Record eliminati"
        ordering = ['-eliminato_il']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.descrizione}"


class AccessoDatore(models.Model):
    datore = models.OneToOneField(DatoreLavoro, on_delete=models.CASCADE, primary_key=True, verbose_name="DATORE", related_name='accesso')
    password = models.CharField(max_length=128, verbose_name="PASSWORD (hash)")
    accesso_abilitato = models.BooleanField(default=False, verbose_name="ACCESSO ABILITATO")
    ultimo_accesso = models.DateTimeField(null=True, blank=True, verbose_name="ULTIMO ACCESSO")
    creato_il = models.DateTimeField(auto_now_add=True, verbose_name="CREATO IL")
    modificato_il = models.DateTimeField(auto_now=True, verbose_name="MODIFICATO IL")

    class Meta:
        verbose_name = "Accesso datore"
        verbose_name_plural = "Accessi datori"
        ordering = ['datore__nome_cognome']

    def __str__(self):
        return f"Accesso: {self.datore.nome_cognome}"


class RichiestaModificaDatore(models.Model):
    TIPO_SCELTE = [
        ('ANAGRAFICA', 'Modifica Anagrafica'),
        ('CONTRATTO', 'Modifica Contratto'),
        ('PROGETTO', 'Modifica Progetto'),
        ('CESSAZIONE', 'Richiesta Cessazione'),
        ('MALATTIA', 'Richiesta Malattia / Sostituzione'),
        ('CU', 'Richiesta Certificazione Unica'),
        ('TESTO_LIBERO', 'Altro (testo libero)'),
    ]
    STATO_SCELTE = [
        ('INVIATA', 'Inviata'),
        ('VISTA', 'Vista'),
        ('ACCETTATA', 'Accettata'),
        ('RIFIUTATA', 'Rifiutata'),
    ]

    datore = models.ForeignKey(DatoreLavoro, on_delete=models.CASCADE, verbose_name="DATORE", related_name='richieste_modifica')
    contratto = models.ForeignKey('ContrattoLavoro', null=True, blank=True, on_delete=models.SET_NULL, verbose_name="CONTRATTO", related_name='richieste_modifica')
    tipo = models.CharField(max_length=20, choices=TIPO_SCELTE, verbose_name="TIPO RICHIESTA")
    campo = models.CharField(max_length=100, blank=True, verbose_name="CAMPO")
    etichetta_campo = models.CharField(max_length=200, blank=True, verbose_name="ETICHETTA CAMPO")
    valore_attuale = models.TextField(blank=True, verbose_name="VALORE ATTUALE")
    valore_richiesto = models.TextField(blank=True, verbose_name="VALORE RICHIESTO")
    stato = models.CharField(max_length=20, choices=STATO_SCELTE, default='INVIATA', verbose_name="STATO")
    nota_datore = models.TextField(blank=True, verbose_name="NOTA DATORE")
    nota_admin = models.TextField(blank=True, verbose_name="NOTA ADMIN")
    creato_il = models.DateTimeField(auto_now_add=True, verbose_name="CREATO IL")
    gestito_il = models.DateTimeField(null=True, blank=True, verbose_name="GESTITO IL")
    eliminata = models.BooleanField(default=False, verbose_name="ELIMINATA")
    data_eliminazione = models.DateTimeField(null=True, blank=True, verbose_name="DATA ELIMINAZIONE")

    class Meta:
        verbose_name = "Richiesta modifica datore"
        verbose_name_plural = "Richieste modifica datori"
        ordering = ['-creato_il']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.datore.nome_cognome}"


class DocumentoArchiviato(models.Model):
    TIPO_SCELTE = [
        ('CONTRATTO', 'Contratto'),
        ('BUSTA_PAGA', 'Busta Paga'),
        ('LETTERA_ASSUNZIONE', 'Lettera Assunzione'),
        ('LETTERA_LICENZIAMENTO', 'Lettera Licenziamento'),
        ('LETTERA_DIMISSIONI', 'Lettera Dimissioni'),
        ('RICEVUTA', 'Ricevuta'),
        ('CUD', 'CUD'),
        ('RICHIESTA_CUD', 'Richiesta CUD'),
        ('RIEPILOGO_RAPPORTO', 'Riepilogo Rapporto'),
        ('DEROGA_TFR', 'Deroga TFR'),
        ('LETTERA_LIBERA', 'Lettera Libera'),
        ('PDF_INIZIO', 'Inizio Rapporto'),
        ('PDF_FINE', 'Fine Rapporto'),
        ('PDF_RISCONTRO', 'Riscontro Comune'),
        ('CARTELLINA', 'Cartellina'),
        ('LISTA', 'Lista Personalizzata'),
        ('PAGA_STANDARD', 'Busta Paga Standard'),
        ('NON_CONVIVENTE', 'Busta Non Convivente'),
        ('CONVIVENTI_CCNL', 'Busta Conviventi CCNL'),
        ('CALCOLO_INVERSO', 'Busta Calcolo Inverso'),
        ('BUSTA_MASSIVA', 'Busta Massiva'),
        ('MALATTIA', 'Busta Malattia'),
        ('NOTTURNO', 'Busta Notturna'),
        ('SOSTITUZIONE', 'Busta Sostituzione'),
        ('BUSTA_TFR', 'Busta TFR'),
        ('LIQUIDAZIONE_TFR', 'Liquidazione TFR'),
        ('RIEPILOGO_PAGOPA', 'Riepilogo PagoPA'),
        ('PAGOPA', 'PagoPA INPS'),
        ('PAGOPA_MANUALE', 'PagoPA Manuale'),
        ('CU_ANNUALE', 'Certificazione Unica'),
        ('ALTRO', 'Altro'),
    ]
    tipo = models.CharField(max_length=50, choices=TIPO_SCELTE, verbose_name="TIPO DOCUMENTO")
    titolo = models.CharField(max_length=200, verbose_name="TITOLO")
    file_path = models.CharField(max_length=512, verbose_name="PERCORSO FILE")
    file_size = models.IntegerField(default=0, verbose_name="DIMENSIONE (bytes)")
    file_name = models.CharField(max_length=255, blank=True, verbose_name="NOME FILE")
    contratto = models.ForeignKey(ContrattoLavoro, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="CONTRATTO ASSOCIATO", related_name='documenti_archiviati')
    datore = models.ForeignKey(DatoreLavoro, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="DATORE ASSOCIATO", related_name='documenti_archiviati')
    lavoratore = models.ForeignKey(Lavoratore, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="LAVORATORE ASSOCIATO", related_name='documenti_archiviati')
    modello_testo = models.ForeignKey('ModelloDocumentale', null=True, blank=True, on_delete=models.SET_NULL, verbose_name="MODELLO TESTO USATO", related_name='+')
    modello_documentale = models.ForeignKey('ModelloDocumentale', null=True, blank=True, on_delete=models.SET_NULL, verbose_name="MODELLO DOCUMENTALE USATO", related_name='documenti_generati')
    note = models.TextField(blank=True, verbose_name="NOTE")
    creato_il = models.DateTimeField(auto_now_add=True, verbose_name="CREATO IL")
    creato_da = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="CREATO DA", related_name='documenti_creati')
    inviato = models.BooleanField(default=False, verbose_name="INVIATO VIA EMAIL")
    inviato_il = models.DateTimeField(null=True, blank=True, verbose_name="INVIATO IL")
    email_destinatario = models.CharField(max_length=200, blank=True, default='', verbose_name="DESTINATARIO EMAIL", validators=[fields.MultiEmailValidator()])
    stampato = models.BooleanField(default=False, verbose_name="STAMPATO")
    data_stampa = models.DateTimeField(null=True, blank=True, verbose_name="DATA STAMPA")
    visibile_al_datore = models.BooleanField(default=False, verbose_name="VISIBILE AL DATORE")

    class Meta:
        verbose_name = "Documento archiviato"
        verbose_name_plural = "Documenti archiviati"
        ordering = ['-creato_il']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.titolo}"


class LogInvioEmail(models.Model):
    ESITO_SCELTE = [('OK', 'OK'), ('ERRORE', 'Errore')]
    contratto = models.ForeignKey(ContrattoLavoro, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="CONTRATTO", related_name='log_invii_email')
    tipo_documento = models.CharField(max_length=50, verbose_name="TIPO DOCUMENTO")
    data_ora = models.DateTimeField(auto_now_add=True, verbose_name="DATA E ORA")
    destinatario = models.CharField(max_length=200, blank=True, verbose_name="DESTINATARIO")
    esito = models.CharField(max_length=10, choices=ESITO_SCELTE, default='OK', verbose_name="ESITO")
    messaggio_errore = models.TextField(blank=True, verbose_name="MESSAGGIO ERRORE")
    utente = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="UTENTE", related_name='log_invii_email')

    class Meta:
        verbose_name = "Log invio email"
        verbose_name_plural = "Log invii email"
        ordering = ['-data_ora']

    def __str__(self):
        return f"{self.get_esito_display()} {self.tipo_documento} -> {self.destinatario} ({self.data_ora})"


class CUAnnuale(models.Model):
    """Dati annuali per Certificazione Unica (modalità Semi-Automatica e Manuale)."""
    MODALITA_SCELTE = [
        ('AUTOMATICA', 'Automatica (da BustaPaga)'),
        ('SEMI_AUTOMATICA', 'Semi-Automatica (13 mensilità)'),
        ('MANUALE', 'Manuale'),
    ]
    contratto = models.ForeignKey(ContrattoLavoro, on_delete=models.CASCADE, related_name='cu_annuali', verbose_name="CONTRATTO")
    anno = models.IntegerField(verbose_name="ANNO")
    modalita = models.CharField(max_length=20, choices=MODALITA_SCELTE, default='AUTOMATICA', verbose_name="MODALITÀ")
    
    # Dati annuali aggregati (per modalità Manuale e riepilogo Semi-Automatica)
    reddito_lordo = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="REDDITO LORDO")
    contributi_inps_lav = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="CONTRIBUTI INPS LAV.")
    contributi_cassa = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="CONTRIBUTI CASSA")
    contributi_totali = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="CONTRIBUTI TOTALI")
    netto_corrisposto = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="NETTO CORRISPOSTO")
    tfr_accantonato = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="TFR ACCANTONATO")
    indennita_convivenza = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="INDENNITÀ CONVIVENZA")
    imponibile_fiscale = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="IMPONIBILE FISCALE")
    
    # Dettaglio 13 mensilità (JSON) - solo per Semi-Automatica
    dettaglio_mensile = models.JSONField(default=dict, blank=True, verbose_name="DETTAGLIO MENSILE (13 mensilità)")
    
    creato_il = models.DateTimeField(auto_now_add=True, verbose_name="CREATO IL")
    aggiornato_il = models.DateTimeField(auto_now=True, verbose_name="AGGIORNATO IL")
    creato_da = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="CREATO DA", related_name='cu_annuali_create')

    class Meta:
        verbose_name = "CU Annuale"
        verbose_name_plural = "CU Annuali"
        constraints = [
            models.UniqueConstraint(fields=['contratto', 'anno', 'modalita'], name='unique_cu_contratto_anno_modalita'),
        ]
        ordering = ['-anno', '-creato_il']

    def __str__(self):
        return f"CU {self.contratto} {self.anno} ({self.get_modalita_display()})"

    def calcola_imponibile(self):
        """Imponibile fiscale = Reddito lordo - Contributi INPS lavoratore."""
        return self.reddito_lordo - self.contributi_inps_lav

    def calcola_totali_da_mensile(self):
        """Ricalcola i totali annuali dal dettaglio_mensile (13 mensilità)."""
        if not self.dettaglio_mensile:
            return
        tot_lordo = sum(m.get('lordo', 0) for m in self.dettaglio_mensile.values())
        tot_inps = sum(m.get('contributi_inps', 0) for m in self.dettaglio_mensile.values())
        tot_cassa = sum(m.get('contributi_cassa', 0) for m in self.dettaglio_mensile.values())
        tot_contrib = sum(m.get('contributi_totali', 0) for m in self.dettaglio_mensile.values())
        tot_netto = sum(m.get('netto', 0) for m in self.dettaglio_mensile.values())
        tot_tfr = sum(m.get('tfr', 0) for m in self.dettaglio_mensile.values())
        tot_conv = sum(m.get('convivenza', 0) for m in self.dettaglio_mensile.values())
        self.reddito_lordo = round(tot_lordo, 2)
        self.contributi_inps_lav = round(tot_inps, 2)
        self.contributi_cassa = round(tot_cassa, 2)
        self.contributi_totali = round(tot_contrib, 2)
        self.netto_corrisposto = round(tot_netto, 2)
        self.tfr_accantonato = round(tot_tfr, 2)
        self.indennita_convivenza = round(tot_conv, 2)
        self.imponibile_fiscale = round(self.calcola_imponibile(), 2)


class ModelloLista(models.Model):
    TIPO_SORGENTE = [
        ('DATORE', 'Datori di Lavoro'),
        ('LAVORATORE', 'Lavoratori'),
        ('BENEFICIARIO', 'Beneficiari'),
        ('CONTRATTO', 'Contratti'),
        ('PROGETTO_REGIONALE', 'Progetti Regionali'),
        ('PAGOPA_INPS', 'PagoPA INPS'),
    ]
    nome = models.CharField(max_length=100, unique=True, verbose_name="NOME LISTA")
    tipo_sorgente = models.CharField(max_length=30, choices=TIPO_SORGENTE, verbose_name="TIPO SORGENTE")
    configurazione_colonne = models.JSONField(default=list, verbose_name="CONFIGURAZIONE COLONNE",
        help_text="Lista di oggetti: {label, field_path, larghezza, allineamento}")
    note = models.TextField(blank=True, verbose_name="NOTE")
    is_default = models.BooleanField(default=False, verbose_name="MODELLO PREDEFINITO")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="CREATO IL")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="AGGIORNATO IL")

    class Meta:
        verbose_name = "Modello Lista"
        verbose_name_plural = "Modelli Lista"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class ServizioWebConfig(models.Model):
    chrome_user_data_dir = models.CharField(
        max_length=512, blank=True,
        verbose_name="CARTELLA PROFILO CHROME",
        help_text="Percorso alla user-data-dir di Chrome per mantenere la sessione INPS tra le procedure."
    )
    headless = models.BooleanField(default=False, verbose_name="MODALITÀ HEADLESS",
        help_text="Esegue Chrome senza finestra grafica.")
    timeout_elementi = models.IntegerField(default=10, verbose_name="TIMEOUT ATTESA (sec)",
        help_text="Secondi massimi di attesa per la comparsa di elementi nelle pagine INPS.")

    link_inps_cessazione = models.URLField(
        max_length=255, blank=True,
        verbose_name="LINK INPS CESSAZIONE",
        default="https://www.inps.it/it/it/dettaglio-scheda.it.schede-servizio-strumento.schede-servizi.cessazione-lavoratore-domestico-50177.cessazione-lavoratore-domestico.html"
    )

    link_inps_pagopa = models.URLField(
        max_length=255, blank=True,
        verbose_name="LINK INPS PAGOPA",
        default="https://serviziweb2.inps.it/PagamentiBollettiniLD/accessoUtente.do"
    )

    use_playwright = models.BooleanField(
        default=True,
        verbose_name="USA PLAYWRIGHT",
        help_text="Usa Playwright invece di Selenium per l'automazione delle procedure web INPS."
    )

    delay_pausa = models.FloatField(
        default=0.5,
        verbose_name="PAUSA TRA AZIONI (sec)",
        help_text="Pausa in secondi tra le azioni dell'automazione (tra un click e l'altro). Valori tipici: 0.3-1.5."
    )

    class Meta:
        verbose_name = "Configurazione Servizi Web"
        verbose_name_plural = "Configurazioni Servizi Web"
        ordering = ['id']

    def __str__(self):
        return "Configurazione Servizi Web"

    @classmethod
    def get_singleton(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class ModelloComposizione(models.Model):
    nome = models.CharField(max_length=100, unique=True, verbose_name="NOME COMPOSIZIONE")
    elementi = models.JSONField(default=list, verbose_name="ELEMENTI",
        help_text="Lista di oggetti: {tipo, label, template_pk, periodo_tipo, mese, anno}")
    note = models.TextField(blank=True, verbose_name="NOTE")
    is_default = models.BooleanField(default=False, verbose_name="PREDEFINITO")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="CREATO IL")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="AGGIORNATO IL")

    class Meta:
        verbose_name = "Modello Composizione"
        verbose_name_plural = "Modelli Composizione"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class LogOperazioneINPS(models.Model):
    TIPI = [
        ('APERTURA_ASSUNZIONE', 'Apertura Assunzione'),
        ('SALVATAGGIO_CODICE', 'Salvataggio Codice Rapporto'),
        ('APERTURA_CESSAZIONE', 'Apertura Cessazione'),
        ('SALVATAGGIO_DATA_FINE', 'Salvataggio Data Fine'),
        ('APERTURA_PAGOPA_MANUALE', 'Apertura PagoPA Manuale'),
        ('CARICATO_PDF_PAGOPA_MANUALE', 'Caricato PDF PagoPA Manuale'),
        ('APERTURA_PAGOPA_AUTO', 'Apertura PagoPA Automatica'),
        ('COMPLETATO_PAGOPA_AUTO', 'Completato PagoPA Automatico'),
        ('GENERATO_PDF_PAGOPA', 'Generato PDF PagoPA'),
    ]
    contratto = models.ForeignKey(ContrattoLavoro, on_delete=models.CASCADE, verbose_name="CONTRATTO", related_name='log_operazioni_inps')
    tipo_op = models.CharField(max_length=40, choices=TIPI, verbose_name="TIPO OPERAZIONE")
    dettaglio = models.TextField(blank=True, verbose_name="DETTAGLIO")
    data_creazione = models.DateTimeField(auto_now_add=True, verbose_name="DATA")
    utente = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="UTENTE", related_name='log_operazioni_inps')

    class Meta:
        verbose_name = "Log operazione INPS"
        verbose_name_plural = "Log operazioni INPS"
        ordering = ['-data_creazione']

    def __str__(self):
        return f"{self.get_tipo_op_display()} — {self.contratto} ({self.data_creazione:%d/%m/%Y %H:%M})"


class AttivitaMensile(models.Model):
    CATEGORIE = [
        ('BUSTE_PAGA', 'Buste Paga'),
        ('CONTRIBUTI', 'Contributi'),
        ('CU', 'Certificazione Unica'),
        ('DOCUMENTI', 'Documenti'),
        ('VARIE', 'Varie'),
    ]
    label = models.CharField(max_length=200, verbose_name="Attività")
    categoria = models.CharField(max_length=30, choices=CATEGORIE, default='VARIE', verbose_name="Categoria")
    ordine = models.IntegerField(default=0, verbose_name="Ordine")
    obbligatorio = models.BooleanField(default=False, verbose_name="Obbligatoria")

    class Meta:
        verbose_name = "Attività Mensile"
        verbose_name_plural = "Attività Mensili"
        ordering = ['categoria', 'ordine']

    def __str__(self):
        return self.label


class CompletamentoMensile(models.Model):
    attivita = models.ForeignKey(AttivitaMensile, on_delete=models.CASCADE, related_name='completamenti', verbose_name="Attività")
    anno = models.IntegerField(verbose_name="Anno")
    mese = models.IntegerField(verbose_name="Mese")
    completato = models.BooleanField(default=False, verbose_name="Completato")
    completato_il = models.DateTimeField(null=True, blank=True, verbose_name="Completato il")
    completato_da = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Completato da")
    note = models.TextField(blank=True, verbose_name="Note")

    class Meta:
        verbose_name = "Completamento Mensile"
        verbose_name_plural = "Completamenti Mensili"
        ordering = ['-anno', '-mese', 'attivita__categoria', 'attivita__ordine']
        unique_together = ('attivita', 'anno', 'mese')

    def __str__(self):
        stato = '✓' if self.completato else '○'
        return f"{stato} {self.attivita.label} ({self.mese}/{self.anno})"


class ScorciatoiaTastiera(models.Model):
    menu_id = models.CharField(max_length=100, unique=True,
        verbose_name="ID menu",
        help_text="Identificativo univoco, es. 'nav-datore', 'nav-lavoratori'")
    label = models.CharField(max_length=100, verbose_name="Etichetta")
    tasto = models.CharField(max_length=15, unique=True, blank=True, null=True,
        verbose_name="Tasto scorciatoia")
    icona = models.CharField(max_length=50, blank=True, default='',
        verbose_name="Icona Bootstrap")
    ordinamento = models.IntegerField(default=0, verbose_name="Ordine")
    attiva = models.BooleanField(default=True, verbose_name="Attiva")

    class Meta:
        verbose_name = "Scorciatoia da tastiera"
        verbose_name_plural = "Scorciatoie da tastiera"
        ordering = ['ordinamento']

    def __str__(self):
        return f"[{self.tasto}] {self.label}" if self.tasto else self.label


# === CCNL ===
class CcnlArticolo(models.Model):
    """Articolo del CCNL Lavoro Domestico."""
    articolo = models.IntegerField(unique=True, verbose_name="N. articolo")
    titolo = models.CharField(max_length=255, verbose_name="Titolo")
    testo = models.TextField(verbose_name="Testo")

    class Meta:
        ordering = ['articolo']
        verbose_name = "CCNL - Articolo"
        verbose_name_plural = "CCNL"
        indexes = [models.Index(fields=['articolo'])]

    def __str__(self):
        return f"Art. {self.articolo} — {self.titolo}"


# === SEGNALI ===
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

@receiver(m2m_changed, sender=ContrattoLavoro.progetto.through)
def _ricalcola_ore_su_progetto(sender, instance, action, **kwargs):
    if action not in ('post_add', 'post_remove', 'post_clear'):
        return
    if not instance.pk:
        return
    instance._calcola_ore()
    instance.save(update_fields=['ore_calcolate'])


class ProfiloUtente(models.Model):
    RUOLI = [
        ('ADMIN',      'Amministratore'),
        ('OPERATORE',  'Operatore'),
        ('CONSULENTE', 'Consulente'),
        ('DATORE',     'Datore di Lavoro'),
    ]
    utente        = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='profilo')
    ruolo         = models.CharField(max_length=20, choices=RUOLI, default='OPERATORE')
    permessi_json = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Profilo utente"
        verbose_name_plural = "Profili utente"

    def __str__(self):
        return f"{self.utente.username} ({self.get_ruolo_display()})"


@receiver(post_save, sender=User)
def _crea_profilo_utente(sender, instance, created, **kwargs):
    if created and instance.is_staff:
        ProfiloUtente.objects.get_or_create(utente=instance, defaults={'ruolo': 'OPERATORE'})
