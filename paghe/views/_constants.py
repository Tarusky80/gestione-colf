"""Costanti globali condivise tra i moduli delle views"""

import os
from django.conf import settings

# Modelli e form necessari per le mappe
from paghe.models import (
    ProgettoRegionale, TipoProgettoRegionale, ParametriCCNL, Livello,
    TabellaCasse, TabellaContributiINPS, TabellaMalattia, TabellaScattiAnzianita,
    ModelloLista, DatoreLavoro, Lavoratore,
    ContrattoLavoro, Beneficiario, ContrattoAttivo,
)
from paghe.forms import (
    DatoreForm, LavoratoreForm, BeneficiarioForm, ContrattoForm,
    ProgettoRegionaleForm, ParametriCCNLForm, TabellaCasseForm,
    TabellaContributiINPSForm, TabellaMalattiaForm, TabellaScattiAnzianitaForm,
    TipoProgettoRegionaleForm, LivelloForm,
    ModelloListaForm,
)

TABELLE_MAP = {
    'progetti-regionali': {'model': ProgettoRegionale, 'form': ProgettoRegionaleForm, 'titolo': 'Progetti Regionali', 'icona': 'diagram-3'},
    'parametri-ccnl': {'model': ParametriCCNL, 'form': ParametriCCNLForm, 'titolo': 'Parametri CCNL', 'icona': 'sliders'},
    'tabelle-casse': {'model': TabellaCasse, 'form': TabellaCasseForm, 'titolo': 'Tabella Casse', 'icona': 'cash-stack'},
    'contributi-inps': {'model': TabellaContributiINPS, 'form': TabellaContributiINPSForm, 'titolo': 'Contributi INPS', 'icona': 'percent'},
    'malattia': {'model': TabellaMalattia, 'form': TabellaMalattiaForm, 'titolo': 'Tabella Malattia', 'icona': 'heart-pulse'},
    'scatti-anzianita': {'model': TabellaScattiAnzianita, 'form': TabellaScattiAnzianitaForm, 'titolo': 'Scatti Anzianità', 'icona': 'arrow-up-circle'},
    'tipi-progetto': {'model': TipoProgettoRegionale, 'form': TipoProgettoRegionaleForm, 'titolo': 'Tipo Progetto', 'icona': 'tags'},
    'livelli': {'model': Livello, 'form': LivelloForm, 'titolo': 'Livelli', 'icona': 'layers'},
    'modelli-lista': {'model': ModelloLista, 'form': ModelloListaForm, 'titolo': 'Modelli Lista', 'icona': 'file-earmark-spreadsheet'},
}

XLSX_EXPORT_MAP = {
    'datori': {
        'model': DatoreLavoro,
        'sheet': 'Datori',
        'fields': [
            ('Codice Fiscale', 'codice_fiscale'),
            ('Nome e Cognome', 'nome_cognome'),
            ('Indirizzo', 'indirizzo'),
            ('Comune', 'comune'),
            ('Email', 'email'),
            ('Telefono', 'telefono'),
            ('PIN INPS', 'pin_inps'),
            ('Invio Digitale Documenti', 'invio_digitale_documenti'),
            ('Note', 'note_datore'),
        ],
        'lookup': 'codice_fiscale',
    },
    'lavoratori': {
        'model': Lavoratore,
        'sheet': 'Lavoratori',
        'fields': [
            ('Codice Fiscale', 'codice_fiscale'),
            ('Nome e Cognome', 'nome_cognome'),
            ('Indirizzo', 'indirizzo'),
            ('Comune', 'comune'),
            ('Email', 'email'),
            ('Telefono', 'telefono'),
            ('Ferie Pregresse', 'ferie_pregresse'),
            ('Scatti Anzianità Maturati', 'scatti_anzianita_maturati'),
            ('Note', 'note_lavoratore'),
        ],
        'lookup': 'codice_fiscale',
    },
    'contratti': {
        'model': ContrattoLavoro,
        'sheet': 'Contratti',
        'fields': [
            ('Datore CF', 'datore__codice_fiscale'),
            ('Datore Nome', 'datore__nome_cognome'),
            ('Lavoratore CF', 'lavoratore__codice_fiscale'),
            ('Lavoratore Nome', 'lavoratore__nome_cognome'),
            ('Data Assunzione', 'data_assunzione'),
            ('Stato', 'stato'),
            ('Tipo Contratto', 'tipo_contratto'),
            ('Modalità TFR', 'modalita_tfr'),
            ('Tredicesima', 'paga_13ma'),
            ('Festivi', 'paga_festivi'),
            ('Ferie', 'paga_ferie'),
            ('Ind. Certificazione Qualità', 'ind_certificazione_qualita'),
            ('Più Persone Non Conv.', 'ind_piu_persone_non_conv'),
            ('Minori Non Conv.', 'ind_minori_non_conv'),
            ('Ind. Funzione Conviventi', 'ind_funzione_conviventi'),
            ('Notturno Assistenza', 'applica_notturno_assistenza'),
            ('Notturno Presenza', 'applica_notturno_presenza'),
            ('Notturno Base', 'applica_notturno_base'),
            ('Notturno 20%', 'applica_notturno_20'),
            ('Is Convivente', 'is_convivente'),
            ('Ore Calcolate', 'ore_calcolate'),
        ],
        'lookup': None,
    },
    'buste-paga': {
        'model': 'BustaPaga',
        'sheet': 'Buste Paga',
        'fields': [
            ('Mese', 'mese'),
            ('Anno', 'anno'),
            ('Datore', 'contratto__datore__nome_cognome'),
            ('Lavoratore', 'contratto__lavoratore__nome_cognome'),
            ('Tipo Calcolo', 'tipo_calcolo'),
            ('Stato', 'stato'),
            ('Budget Mensile', 'budget_mensile'),
            ('Ore Mensili', 'ore_mensili'),
            ('Paga Base', 'paga_base_totale'),
            ('Indennità', 'totale_indennita'),
            ('Scatti', 'scatti_totale'),
            ('Lordo', 'totale_lordo'),
            ('INPS', 'contributi_inps_totale'),
            ('Cassa', 'contributi_cassa_totale'),
            ('Totale Contributi', 'totale_contributi'),
            ('Convivenza', 'convivenza_totale'),
            ('Accantonati', 'totale_accantonati'),
            ('Netto', 'netto'),
        ],
        'lookup': None,
    },
    'beneficiari': {
        'model': Beneficiario,
        'sheet': 'Beneficiari',
        'fields': [
            ('Codice Fiscale', 'codice_fiscale'),
            ('Nome e Cognome', 'nome_cognome'),
            ('Indirizzo', 'indirizzo'),
            ('Comune', 'comune'),
            ('Email', 'email'),
            ('Telefono', 'telefono'),
            ('Note', 'note_beneficiario'),
        ],
        'lookup': 'codice_fiscale',
    },
    'progetti-regionali': {
        'model': ProgettoRegionale,
        'sheet': 'Progetti Regionali',
        'fields': [
            ('Beneficiario CF', 'beneficiario__codice_fiscale'),
            ('Beneficiario Nome', 'beneficiario__nome_cognome'),
            ('Tipo Progetto', 'tipo__nome'),
            ('Data Inizio', 'data_inizio'),
            ('Data Fine', 'data_fine'),
            ('Budget Annuale', 'budget_annuale'),
            ('Mesi', 'mesi'),
            ('Budget Mensile', 'budget_mensile'),
        ],
        'lookup': None,
    },
}

XLSX_IMPORT_MAP = {
    'datori': XLSX_EXPORT_MAP['datori'],
    'lavoratori': XLSX_EXPORT_MAP['lavoratori'],
    'contratti': XLSX_EXPORT_MAP['contratti'],
    'beneficiari': XLSX_EXPORT_MAP['beneficiari'],
    'progetti-regionali': XLSX_EXPORT_MAP['progetti-regionali'],
}

ANAGRAFICA_MAP = {
    'datore': {'model': DatoreLavoro, 'form': DatoreForm, 'template': 'frontend/ajax_form.html', 'skip_fields': ['codice_fiscale']},
    'lavoratore': {'model': Lavoratore, 'form': LavoratoreForm, 'template': 'frontend/ajax_form.html', 'skip_fields': ['codice_fiscale']},
    'beneficiario': {'model': Beneficiario, 'form': BeneficiarioForm, 'template': 'frontend/ajax_form.html', 'skip_fields': ['codice_fiscale']},
    'contratto': {'model': ContrattoAttivo, 'form': ContrattoForm, 'template': 'frontend/ajax_form_contratto.html', 'skip_fields': ['id']},
}

MESI_IT = ['', 'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
           'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']

TOGGLE_KEYS = ['ind_funzione', 'ind_bambini_6', 'ind_piu_assistiti', 'ind_cert_qualita',
               'scatti', 'rateo_tfr', 'rateo_tfr_separato', 'rateo_anticipo_70',
               'rateo_13ma', 'rateo_ferie', 'rateo_festivi']

_FONT_PROGETTO = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', 'fonts')

_MESI_CF = {'A':'01','B':'02','C':'03','D':'04','E':'05','H':'06',
            'L':'07','M':'08','P':'09','R':'10','S':'11','T':'12'}

_pagopa_drivers = {}
_pagopa_screenshots = {}

CARTELLA_STAMPE_TEMP = os.path.join(settings.MEDIA_ROOT, 'stampe_temp')
