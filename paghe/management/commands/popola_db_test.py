"""Popola database di prova con dati fittizi ma realistici."""
import math
import random
import string
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connections

from paghe.models import (
    DatoreLavoro, Lavoratore, ContrattoLavoro, BustaPaga,
    Livello, ParametriCCNL, TabellaCasse,
    TipoProgettoRegionale, ProgettoRegionale,
    Appuntamento, AttivitaMensile, Beneficiario,
)

# ──────────────────────────── DATI REALISTICI ────────────────────────────

NOMI_M = [
    'Mario', 'Luigi', 'Giuseppe', 'Antonio', 'Francesco', 'Giovanni', 'Paolo',
    'Marco', 'Andrea', 'Alessandro', 'Roberto', 'Stefano', 'Fabio', 'Luca',
    'Simone', 'Claudio', 'Michele', 'Davide', 'Federico', 'Matteo', 'Carlo',
    'Vincenzo', 'Salvatore', 'Daniele', 'Pietro', 'Angelo', 'Riccardo',
    'Alberto', 'Giorgio', 'Massimo', 'Gianni', 'Giulio', 'Renato', 'Valerio',
]
NOMI_F = [
    'Maria', 'Anna', 'Giovanna', 'Francesca', 'Paola', 'Roberta', 'Laura',
    'Stefania', 'Sara', 'Elena', 'Monica', 'Silvia', 'Cristina', 'Marta',
    'Simona', 'Antonella', 'Valentina', 'Daniela', 'Giulia', 'Alessia',
    'Claudia', 'Sabrina', 'Veronica', 'Barbara', 'Patrizia', 'Teresa',
    'Angela', 'Rosa', 'Luisa', 'Rita', 'Carmela', 'Sofia', 'Chiara',
]
COGNOMI = [
    'Rossi', 'Bianchi', 'Ricci', 'Marino', 'Moretti', 'Bruno', 'Conti',
    'Gallo', 'Costa', 'Fontana', 'Santoro', 'Russo', 'Ferrari', 'Esposito',
    'Romano', 'Colombo', 'Greco', 'Barbieri', 'Lombardi', 'De Luca',
    'Mancini', 'Rinaldi', 'Caruso', 'Fabbri', 'Martini', 'Giordano',
    'Guerra', 'Ferri', 'Serra', 'Piras', 'Vitale', 'Sanna', 'Meli',
    'Cattaneo', 'Morelli', 'Testa', 'Leone', 'Barone', 'Poli', 'Orsini',
    'Monti', 'Parisi', 'Grassi', 'Longo', 'Gatti', 'Sartori', 'Vitali',
]
COMUNI = [
    ('Roma', 'RM', 'H501'), ('Milano', 'MI', 'F205'), ('Napoli', 'NA', 'F839'),
    ('Torino', 'TO', 'L219'), ('Palermo', 'PA', 'G273'), ('Genova', 'GE', 'D969'),
    ('Bologna', 'BO', 'A944'), ('Firenze', 'FI', 'D612'), ('Catania', 'CT', 'C351'),
    ('Bari', 'BA', 'A662'), ('Venezia', 'VE', 'L736'), ('Verona', 'VR', 'L781'),
    ('Padova', 'PD', 'G224'), ('Trieste', 'TS', 'L424'), ('Brescia', 'BS', 'B157'),
    ('Parma', 'PR', 'G337'), ('Modena', 'MO', 'F257'), ('Reggio Calabria', 'RC', 'H224'),
    ('Perugia', 'PG', 'G478'), ('Lecce', 'LE', 'E506'), ('Livorno', 'LI', 'E625'),
    ('Cagliari', 'CA', 'B354'), ('Foggia', 'FG', 'D643'), ('Salerno', 'SA', 'H703'),
    ('Ravenna', 'RA', 'H199'), ('Trento', 'TN', 'L378'), ('Ancona', 'AN', 'A271'),
    ('Pescara', 'PE', 'G482'), ('Lucca', 'LU', 'E715'), ('Como', 'CO', 'C933'),
]
VIE = [
    'Via Roma', 'Via Garibaldi', 'Via Mazzini', 'Corso Italia', 'Via Cavour',
    'Via Dante', 'Piazza della Repubblica', 'Via Manzoni', 'Via Verdi',
    'Via Petrarca', 'Viale Rinascimento', 'Via Monte Bianco', 'Largo Europa',
    'Piazza Garibaldi', 'Via del Corso', 'Via Monte Rosa',
    'Viale delle Rimembranze', 'Via Carducci', 'Via Pascoli', 'Via Leopardi',
]
LIVELLI = ['A', 'B', 'C', 'CS', 'DS']
TIPI_PROGETTO = ['Assistenza anziani', 'Assistenza minori', 'Pulizie domestiche', 'Badante', 'Baby-sitter']


def _calc_codice_controllo(cf15):
    """Calcola il carattere di controllo per un CF di 15 caratteri."""
    dispari = {str(i): v for i, v in enumerate('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', 1)}
    pari = {str(i): v for i, v in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 0)}
    somma = 0
    for i, ch in enumerate(cf15.upper()):
        if ch not in dispari:
            ch = '0'
        if i % 2 == 0:
            if ch in dispari and dispari[ch] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                somma += ord(dispari[ch]) - 65
            else:
                somma += ord('A') + int(ch)
        else:
            if ch in string.digits:
                somma += ord(pari[ch]) - 65
            else:
                somma += ord(ch) - 65
    return chr(65 + somma % 26)


def _genera_cf(nome, cognome, sesso, anno_n, mese_n, giorno_n, comune):
    """Genera un CF italiano valido di 16 caratteri."""
    c = cognome.upper().ljust(3, 'X')[:3]
    n = nome.upper().ljust(3, 'X')[:3]
    consonanti = lambda s: ''.join(ch for ch in s if ch not in 'AEIOU')
    vocali = lambda s: ''.join(ch for ch in s if ch in 'AEIOU')
    c = (consonanti(cognome.upper()) + vocali(cognome.upper()) + 'XXX')[:3]
    n = (consonanti(nome.upper()) + vocali(nome.upper()) + 'XXX')[:3]
    a = str(anno_n)[-2:]
    mesi = 'ABCDEHLMPRST'
    m = mesi[mese_n - 1]
    g = giorno_n + (40 if sesso == 'F' else 0)
    cf15 = f'{c}{n}{a}{m}{g:02d}{comune}'
    return cf15 + _calc_codice_controllo(cf15)


def _random_date(start_year=1970, end_year=2004):
    return date(random.randint(start_year, end_year), random.randint(1, 12), random.randint(1, 28))


def _random_comune():
    return random.choice(COMUNI)


def _random_via():
    return random.choice(VIE)


class Command(BaseCommand):
    help = 'Popola un database di prova con dati realistici.'

    def add_arguments(self, parser):
        parser.add_argument('--profile', required=True, choices=list(settings.DB_PROFILES.keys()),
                            help='Profilo database da popolare (es. prova_casistiche)')
        parser.add_argument('--recreate', action='store_true',
                            help='Cancella il file SQLite esistente e ricrea da zero')

    def handle(self, *args, **options):
        profile = options['profile']
        if profile == 'default':
            raise CommandError('Non puoi popolare il database principale con dati di prova.')

        target = settings.DB_PROFILES[profile]
        target_path = target['NAME']
        label = target['label']

        self.stdout.write(f'=== Popolamento database: {label} ===')
        self.stdout.write(f'File: {target_path}')

        # Backup del NAME originale
        original = settings.DATABASES['default']['NAME']

        # Se richiesto, cancella il file esistente
        if options.get('recreate') and target_path.exists():
            target_path.unlink()
            self.stdout.write('File esistente cancellato.')

        # Forza la chiusura e RIMOZIONE della connessione cacheata
        self._invalida_connessione_default()
        settings.DATABASES['default']['NAME'] = str(target_path)

        try:
            self._popola()
            self.stdout.write(self.style.SUCCESS(f'* Database "{label}" popolato con successo!'))
        finally:
            # Ripristina connessione al database originale
            self._invalida_connessione_default()
            settings.DATABASES['default']['NAME'] = original

    def _invalida_connessione_default(self):
        """Chiude e rimuove la connessione cacheata per forzare la ricreazione
        con le nuove impostazioni al prossimo accesso.

        Django 6.0 usa asgiref.local.Local (thread-local) come storage,
        non più un dict semplice. Usiamo hasattr/delattr pubblici."""
        if hasattr(connections._connections, 'default'):
            try:
                connections['default'].close()
            except Exception:
                pass
            try:
                del connections['default']
            except Exception:
                pass

    def _popola(self):
        """Esegue tutte le fasi di popolazione."""
        # Estrai il profilo dal percorso del database
        db_path = settings.DATABASES['default']['NAME']
        profile = 'default'
        if isinstance(db_path, str):
            # Esempio: C:\GESTIONECOLF\db_prova_uno.sqlite3
            # Estrai 'prova_uno' dal nome del file
            import os
            filename = os.path.basename(db_path)
            if filename.startswith('db_') and filename.endswith('.sqlite3'):
                profile = filename[3:-8]  # Rimuovi 'db_' (3) e '.sqlite3' (8)
            elif filename.startswith('db.') and filename.endswith('.sqlite3'):
                profile = filename[3:-8]
        # Esegui migrazioni
        self.stdout.write('Migrazioni in corso...')
        call_command('migrate', verbosity=0, interactive=False)
        self.stdout.write(self.style.SUCCESS('OK'))

        # Crea superuser
        self.stdout.write('Superuser...')
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@gestionecolf.it', 'admin')
        self.stdout.write(self.style.SUCCESS('OK (admin/admin)'))

        # Copia tabelle di configurazione dal database principale
        self._copia_tabelle_config()

        # Determina quanti elementi creare in base al profilo
        counts = self._get_counts(profile)

        # Crea datori e lavoratori
        self._crea_anagrafiche(counts)

        # Crea contratti con progetti e buste
        self._crea_contratti(counts)

        # Crea appuntamenti
        self._crea_appuntamenti()

        # Crea attività checklist
        self._crea_attivita_mensili()

    def _get_counts(self, profile):
        profili = {
            'prova_casistiche': {
                'datori': 5, 'lavoratori': 10, 'contratti': 15,
                'buste_mesi_min': 3, 'buste_mesi_max': 6,
            },
            'prova_molti': {
                'datori': 10, 'lavoratori': 50, 'contratti': 200,
                'buste_mesi_min': 1, 'buste_mesi_max': 6,
            },
            'prova_varie': {
                'datori': 8, 'lavoratori': 25, 'contratti': 50,
                'buste_mesi_min': 3, 'buste_mesi_max': 6,
            },
            'prova_uno': {
                'datori': 1, 'lavoratori': 1, 'contratti': 1,
                'buste_mesi_min': 3, 'buste_mesi_max': 3,
            },
        }
        return profili.get(profile, profili['prova_casistiche'])

    # ────────── COPIA CONFIGURAZIONE DAL DB PRINCIPALE ──────────

    def _copia_tabelle_config(self):
        """Copia le tabelle di configurazione dal database principale
        al database di prova usando ATTACH di SQLite."""
        self.stdout.write('Copia configurazione dal database principale...')

        main_db = settings.DB_PROFILES['default']['NAME']  # Path object
        from django.db import connection

        tabelle_config = [
            'paghe_opzionisoftware',
            'paghe_livello',
            'paghe_parametriccnl',
            'paghe_tabellacasse',
            'paghe_tabellacontributiinps',
            'paghe_tabellamalattia',
            'paghe_tabellascattianzianita',
            'paghe_indiceistat',
            'paghe_tipoprogettoregionale',
        ]

        raw = connection.cursor().connection  # raw sqlite3.Connection (bypassa wrapper Django)
        main_path = str(main_db)
        try:
            raw.execute("ATTACH DATABASE ? AS main_db", [main_path])
            raw.execute("PRAGMA foreign_keys=OFF")
            for table in tabelle_config:
                raw.execute(f"DELETE FROM {table}")
                raw.execute(f"INSERT INTO {table} SELECT * FROM main_db.{table}")
            raw.execute("PRAGMA foreign_keys=ON")
            raw.execute("DETACH DATABASE main_db")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Errore copia configurazione: {e}'))
            self.stdout.write('Uso valori hardcodati di fallback...')
            self._crea_riferimenti_fallback()
            return

        # Aggiunge eventuali dati di test non presenti nel DB principale
        for codice in LIVELLI:
            lv, _ = Livello.objects.get_or_create(codice=codice, defaults={'colore': '#5E6AD2'})
            for anno in (2025, 2026):
                ParametriCCNL.objects.get_or_create(
                    livello=lv, anno=anno,
                    defaults={'paga_base': 7.50, 'tfr_orario': 0.50, 'tredicesima_oraria': 0.60,
                              'ferie_orarie': 0.30, 'festivi_orari': 0.30,
                              'convivenza_pranzo': 2.33, 'convivenza_cena': 2.33, 'convivenza_alloggio': 2.00},
                )
        for tp in TIPI_PROGETTO:
            TipoProgettoRegionale.objects.get_or_create(nome=tp)
        for ente in [
            {'codice': 'F2', 'descrizione': 'EBINCOLF – Fondo 2%', 'quota_datore': 0.04, 'quota_lavoratore': 0.02, 'totale': 0.06},
            {'codice': 'E1', 'descrizione': 'EBINCOLF – Fondo 4%', 'quota_datore': 0.025, 'quota_lavoratore': 0.015, 'totale': 0.04},
        ]:
            TabellaCasse.objects.get_or_create(codice=ente['codice'], defaults=ente)

        # Ricarica i riferimenti in memoria per gli usi successivi
        self._livelli = {lv.codice: lv for lv in Livello.objects.all()}
        self._enti = {e.codice: e for e in TabellaCasse.objects.all()}
        self._tipi_progetto = {tp.nome: tp for tp in TipoProgettoRegionale.objects.all()}

        self.stdout.write(self.style.SUCCESS('OK'))

    def _crea_riferimenti_fallback(self):
        """Crea dati di riferimento hardcodati (fallback se la copia fallisce)."""
        from paghe.models import (
            OpzioniSoftware, ParametriCCNL, TabellaContributiINPS,
            TabellaScattiAnzianita, IndiceISTAT,
        )
        OpzioniSoftware.objects.get_or_create(pk=1, defaults={
            'nome_programma': 'Gestionale COLF', 'versione_programma': '2.0',
        })
        self._livelli = {}
        for codice in LIVELLI:
            lv, _ = Livello.objects.get_or_create(codice=codice, defaults={'colore': '#5E6AD2'})
            self._livelli[codice] = lv
        params = {
            'A': {'paga_base': 6.50}, 'B': {'paga_base': 7.20},
            'C': {'paga_base': 7.80}, 'CS': {'paga_base': 8.50},
            'DS': {'paga_base': 9.20},
        }
        for anno in (2025, 2026):
            for cod, vals in params.items():
                ParametriCCNL.objects.get_or_create(
                    livello=self._livelli[cod], anno=anno,
                    defaults={**vals, 'tfr_orario': 0.50, 'tredicesima_oraria': 0.60,
                              'ferie_orarie': 0.30, 'festivi_orari': 0.30,
                              'convivenza_pranzo': 2.33, 'convivenza_cena': 2.33, 'convivenza_alloggio': 2.00},
                )
        self._enti = {}
        for e in [
            {'codice': 'F2', 'descrizione': 'EBINCOLF – Fondo 2%', 'quota_datore': 0.04, 'quota_lavoratore': 0.02, 'totale': 0.06},
            {'codice': 'E1', 'descrizione': 'EBINCOLF – Fondo 4%', 'quota_datore': 0.025, 'quota_lavoratore': 0.015, 'totale': 0.04},
        ]:
            obj, _ = TabellaCasse.objects.get_or_create(codice=e['codice'], defaults=e)
            self._enti[e['codice']] = obj
        for desc, val in [('MENO 24H', 0.85), ('PIU 24H', 1.15)]:
            TabellaContributiINPS.objects.get_or_create(descrizione=desc, defaults={'quota_datore': val, 'quota_lavoratore': val, 'totale': val})
        for cod, val in {'A': 0.12, 'AS': 0.13, 'B': 0.14, 'BS': 0.15, 'C': 0.16, 'CS': 0.17, 'D': 0.18, 'DS': 0.19}.items():
            TabellaScattiAnzianita.objects.get_or_create(livello=cod, defaults={'valore_scatto': val})
        for anno, val in [
            (2000, 103.7), (2001, 107.1), (2002, 110.0), (2003, 112.8),
            (2004, 115.2), (2005, 117.5), (2006, 119.9), (2007, 122.0),
            (2008, 125.8), (2009, 126.3), (2010, 128.4), (2011, 132.0),
            (2012, 136.3), (2013, 138.6), (2014, 139.8), (2015, 140.2),
            (2016, 140.3), (2017, 141.9), (2018, 143.5), (2019, 144.8),
            (2020, 145.0), (2021, 148.2), (2022, 161.0), (2023, 169.5),
            (2024, 173.2), (2025, 177.8), (2026, 180.5),
        ]:
            IndiceISTAT.objects.get_or_create(anno=anno, defaults={'indice': val})
        self._tipi_progetto = {}
        for tp in TIPI_PROGETTO:
            obj, _ = TipoProgettoRegionale.objects.get_or_create(nome=tp)
            self._tipi_progetto[tp] = obj

    # ────────── ANAGRAFICHE ──────────

    def _crea_anagrafiche(self, counts):
        self.stdout.write(f'Anagrafiche ({counts["datori"]} datori, {counts["lavoratori"]} lavoratori)...')

        self._datori = []
        for i in range(counts['datori']):
            nome = random.choice(NOMI_M if i % 2 == 0 else NOMI_F)
            cognome = random.choice(COGNOMI)
            comune = _random_comune()
            cf = _genera_cf(nome, cognome, 'M' if i % 2 == 0 else 'F',
                            random.randint(1960, 1985), random.randint(1, 12), random.randint(1, 28),
                            comune[2])
            while DatoreLavoro.objects.filter(codice_fiscale=cf).exists():
                cf = _genera_cf(nome, cognome, 'M' if i % 2 == 0 else 'F',
                                random.randint(1960, 1985), random.randint(1, 12), random.randint(1, 28),
                                comune[2])
            datore = DatoreLavoro.objects.create(
                codice_fiscale=cf, nome=nome, cognome=cognome,
                indirizzo=f'{_random_via()}, {random.randint(1, 99)}',
                comune=comune[0], provincia=comune[1], cap=str(random.randint(10000, 99999)),
                email=f'{nome.lower()}.{cognome.lower()}@email.it',
                telefono=f'3{random.randint(10, 99)}{random.randint(1000000, 9999999)}',
            )
            self._datori.append(datore)

        self._lavoratori = []
        for i in range(counts['lavoratori']):
            nome = random.choice(NOMI_F if i % 2 == 0 else NOMI_M)
            cognome = random.choice(COGNOMI)
            sesso = 'F' if i % 2 == 0 else 'M'
            comune = _random_comune()
            cf = _genera_cf(nome, cognome, sesso,
                            random.randint(1970, 2004), random.randint(1, 12), random.randint(1, 28),
                            comune[2])
            while Lavoratore.objects.filter(codice_fiscale=cf).exists():
                cf = _genera_cf(nome, cognome, sesso,
                                random.randint(1970, 2004), random.randint(1, 12), random.randint(1, 28),
                                comune[2])
            lav = Lavoratore.objects.create(
                codice_fiscale=cf, nome=nome, cognome=cognome,
                indirizzo=f'{_random_via()}, {random.randint(1, 99)}',
                comune=comune[0],
                email=f'{nome.lower()}.{cognome.lower()}@email.it',
                telefono=f'3{random.randint(10, 99)}{random.randint(1000000, 9999999)}',
            )
            self._lavoratori.append(lav)

        self.stdout.write(self.style.SUCCESS('OK'))

    # ────────── CONTRATTI ──────────

    def _crea_contratti(self, counts):
        # Pre-create progetti con budget realistico
        progetti_per_tipo = {}
        for tp in TIPI_PROGETTO:
            progetti_per_tipo[tp] = []
            budget_mensili = {
                'Assistenza anziani': 450, 'Assistenza minori': 350,
                'Pulizie domestiche': 250, 'Badante': 500, 'Baby-sitter': 300,
            }
            # Usa il primo beneficiario per i progetti
            beneficiario = Beneficiario.objects.first()
            if not beneficiario:
                # Crea un beneficiario se non esiste
                beneficiario = Beneficiario.objects.create(
                    codice_fiscale='CFTEST12345678901234',
                    nome='Beneficiario', cognome='Test',
                    indirizzo='Via Test, 1', comune='Roma', provincia='RM',
                    cap='00100', email='test@example.com',
                )
            for _ in range(10):
                proj = ProgettoRegionale.objects.create(
                    tipo=self._tipi_progetto[tp],
                    beneficiario=beneficiario,
                    budget_mensile=budget_mensili.get(tp, 300),
                    data_inizio=date(2024, 1, 1),
                    data_fine=None,
                )
                progetti_per_tipo[tp].append(proj)

        self.stdout.write(f'Contratti ({counts["contratti"]})...')

        # Per prova_uno: 1 contratto semplice
        # Per prova_casistiche: mix di casistiche (scadenza, cessato, rinnovato, convivente/non)
        # Per prova_molti e prova_varie: distribuzione random

        scenari_disponibili = ['normale', 'normale', 'normale', 'scadenza_30gg', 'scadenza_60gg',
                               'cessato', 'rinnovato', 'convivente', 'non_convivente_molte_ore',
                               'part_time', 'determinato', 'determinato_breve']

        contratti_creati = []
        for idx in range(counts['contratti']):
            datore = random.choice(self._datori)
            lavoratore = random.choice(self._lavoratori)
            # Evita duplicati datore-lavoratore per semplicità (ma non bloccante)
            livello_cod = random.choice(LIVELLI)
            ente_cod = random.choice(['F2', 'E1'])
            anno_ass = random.choice([2024, 2025, 2026])

            data_assunzione = date(anno_ass, random.randint(1, 12), 1)
            is_convivente = random.choice([True, False])
            tipo_contratto = random.choices(['INDETERMINATO', 'DETERMINATO'], weights=[80, 20])[0]

            scenario = random.choice(scenari_disponibili)
            if counts['contratti'] == 1:
                scenario = 'normale'

            stato = 'ATTIVO'
            data_fine = None
            if scenario in ('scadenza_30gg', 'scadenza_60gg'):
                gg = 30 if scenario == 'scadenza_30gg' else 60
                data_fine = date.today() + timedelta(days=gg)
            elif scenario == 'cessato':
                stato = 'CESSATO'
                data_fine = date.today() - timedelta(days=random.randint(10, 180))
            elif scenario == 'determinato_breve':
                tipo_contratto = 'DETERMINATO'
                data_fine = date.today() + timedelta(days=random.randint(15, 60))

            proj_scelto = random.choice(random.choice(list(progetti_per_tipo.values())))

            contratto_kw = {
                'datore': datore,
                'lavoratore': lavoratore,
                'parametri_minimi': ParametriCCNL.objects.filter(
                    livello=self._livelli[livello_cod], anno=2026).first(),
                'ente_bilaterale': self._enti[ente_cod],
                'data_assunzione': data_assunzione,
                'data_fine': data_fine,
                'stato': stato,
                'tipo_contratto': tipo_contratto,
                'is_convivente': is_convivente,
                'paga_13ma': True,
                'paga_ferie': True,
                'paga_festivi': True,
                'modalita_tfr': 'INCLUSO',
                'applica_scatti': random.choice([True, False]),
                'ind_assistenza_piu_persone_ft': is_convivente and random.choice([True, False]),
                'ind_funzione_conviventi': is_convivente,
                'ind_conviventi_ft_54h': is_convivente and random.choice([True, False]),
            }

            contratto = ContrattoLavoro.objects.create(**contratto_kw)
            contratto.progetto.add(proj_scelto)

            # Forza il ricalcolo delle ore (viene fatto in save ma dopo la M2M)
            contratto.save()

            # Buste paga per i mesi richiesti
            min_mesi = counts.get('buste_mesi_min', 3)
            max_mesi = counts.get('buste_mesi_max', 6)
            if counts['contratti'] == 1:
                num_mesi = 3
            elif counts['contratti'] >= 200:
                num_mesi = random.randint(1, 3)
            else:
                num_mesi = random.randint(min_mesi, max_mesi)

            for mese_offset in range(num_mesi):
                mese = 1 + mese_offset  # Da gennaio in poi
                if mese > 12:
                    break
                self._crea_busta(contratto, mese, 2026, proj_scelto)

            contratti_creati.append(contratto)

            if (idx + 1) % 25 == 0 or idx == counts['contratti'] - 1:
                self.stdout.write(f'  {idx + 1}/{counts["contratti"]} contratti creati', ending='\r')

        self.stdout.write('')

        # Per prova_casistiche, crea anche contratti specifici
        if counts['contratti'] == 15:
            self._crea_casistiche_specifiche(contratti_creati)

        self.stdout.write(self.style.SUCCESS(f'* {counts["contratti"]} contratti creati'))

    def _crea_busta(self, contratto, mese, anno, progetto):
        ore_mensili = random.randint(40, 160)
        budget = float(progetto.budget_mensile)
        paga_oraria = budget / max(ore_mensili, 1) if budget else 7.50

        # Calcoli realistici semplificati
        paga_base_totale = round(ore_mensili * paga_oraria, 2)
        inps_h = 0.85 if contratto.is_convivente else 1.15
        ore_inps = math.ceil(ore_mensili / 4.33)
        contributi_inps = round(ore_inps * 4.33 * inps_h, 2)
        ente_tot = float(contratto.ente_bilaterale.totale)
        contributi_ente = round(paga_base_totale * ente_tot, 2)
        totale_contributi = round(contributi_inps + contributi_ente, 2)
        tfr = round(paga_base_totale * 0.065, 2)
        convivenza = round(3 * 26, 2) if contratto.is_convivente else 0
        netto = round(paga_base_totale - totale_contributi - tfr - convivenza, 2)

        ore_settimanali = round(ore_mensili / 4.33, 2)
        BustaPaga.objects.get_or_create(
            contratto=contratto, mese=mese, anno=anno,
            defaults={
                'budget_mensile': budget,
                'ore_mensili': ore_mensili,
                'ore_inps': ore_inps,
                'ore_settimanali': ore_settimanali,
                'paga_oraria_lorda': round(paga_oraria, 2),
                'paga_base_totale': paga_base_totale,
                'totale_indennita': 0,
                'scatti_totale': 0,
                'totale_lordo': paga_base_totale,
                'contributi_inps_totale': contributi_inps,
                'contributi_cassa_totale': contributi_ente,
                'totale_contributi': totale_contributi,
                'convivenza_totale': convivenza,
                'totale_accantonati': tfr,
                'netto': netto,
                'tipo_calcolo': 'STIMATO',
                'indennita_json': {},
                'ratei_pagati_json': [],
                'scatti_dettaglio_json': {},
                'progetti_json': [],
                'tfr_data': {},
            },
        )

    def _crea_casistiche_specifiche(self, contratti_esistenti):
        """Crea alcuni contratti con casistiche mirate per prova_casistiche."""
        # 1. Contratto in scadenza (30gg)
        d = random.choice(self._datori)
        l = random.choice(self._lavoratori)
        p = ParametriCCNL.objects.filter(livello=self._livelli['B'], anno=2026).first()
        c1 = ContrattoLavoro.objects.create(
            datore=d, lavoratore=l, parametri_minimi=p,
            ente_bilaterale=self._enti['F2'],
            data_assunzione=date(2025, 3, 1),
            data_fine=date.today() + timedelta(days=25),
            is_convivente=False, tipo_contratto='DETERMINATO',
        )
        c1.progetto.add(ProgettoRegionale.objects.first())

        # 2. Contratto convivente con molte indennità
        d2 = random.choice(self._datori)
        l2 = random.choice(self._lavoratori)
        p2 = ParametriCCNL.objects.filter(livello=self._livelli['C'], anno=2026).first()
        c2 = ContrattoLavoro.objects.create(
            datore=d2, lavoratore=l2, parametri_minimi=p2,
            ente_bilaterale=self._enti['F2'],
            data_assunzione=date(2024, 6, 15),
            is_convivente=True, applica_scatti=True,
            ind_funzione_conviventi=True, ind_conviventi_ft_54h=True,
            paga_pranzo=True, paga_cena=True, paga_alloggio=True,
        )
        c2.progetto.add(ProgettoRegionale.objects.first())

        # 3. Contratto cessato da poco
        d3 = random.choice(self._datori)
        l3 = random.choice(self._lavoratori)
        p3 = ParametriCCNL.objects.filter(livello=self._livelli['A'], anno=2026).first()
        c3 = ContrattoLavoro.objects.create(
            datore=d3, lavoratore=l3, parametri_minimi=p3,
            ente_bilaterale=self._enti['E1'],
            data_assunzione=date(2025, 1, 10),
            data_fine=date.today() - timedelta(days=15),
            stato='CESSATO',
            is_convivente=False,
        )
        c3.progetto.add(ProgettoRegionale.objects.first())

        # 4. Contratto senza buste (appena assunto)
        d4 = random.choice(self._datori)
        l4 = random.choice(self._lavoratori)
        p4 = ParametriCCNL.objects.filter(livello=self._livelli['DS'], anno=2026).first()
        c4 = ContrattoLavoro.objects.create(
            datore=d4, lavoratore=l4, parametri_minimi=p4,
            ente_bilaterale=self._enti['F2'],
            data_assunzione=date.today() - timedelta(days=5),
            is_convivente=True,
        )
        c4.progetto.add(ProgettoRegionale.objects.first())

        # 5. Contratto con TFR separato
        d5 = random.choice(self._datori)
        l5 = random.choice(self._lavoratori)
        p5 = ParametriCCNL.objects.filter(livello=self._livelli['CS'], anno=2026).first()
        c5 = ContrattoLavoro.objects.create(
            datore=d5, lavoratore=l5, parametri_minimi=p5,
            ente_bilaterale=self._enti['F2'],
            data_assunzione=date(2023, 9, 1),
            is_convivente=False, modalita_tfr='SEPARATO_100',
        )
        c5.progetto.add(ProgettoRegionale.objects.first())

        # Crea buste per i nuovi contratti
        for c in [c1, c2, c3, c5]:
            proj = c.progetto.first()
            for m in range(1, 7):
                if m <= 12:
                    self._crea_busta(c, m, 2026, proj)

    # ────────── APPUNTAMENTI ──────────

    def _crea_appuntamenti(self):
        self.stdout.write('Appuntamenti...')
        tipi = ['PROMEMORIA', 'SCADENZA', 'VISITA', 'RINNOVO']
        for i in range(min(10, len(self._datori) * 2)):
            Appuntamento.objects.create(
                data=date.today() + timedelta(days=random.randint(-5, 30)),
                ora=f'{random.randint(9, 17):02d}:00',
                titolo=f'{random.choice(tipi)}: {random.choice(COGNOMI)}',
                tipo=random.choice(tipi),
                completato=random.choice([True, False]),
            )
        self.stdout.write(self.style.SUCCESS('OK'))

    # ────────── ATTIVITÀ CHECKLIST ──────────

    def _crea_attivita_mensili(self):
        self.stdout.write('Attività checklist...')
        attivita_default = [
            'Verifica scadenze contratti',
            'Calcolo buste paga mensili',
            'Invio CU annuale',
            'Verifica contributi INPS',
            'Pulizia archivio documenti',
            'Aggiornamento anagrafiche',
            'Verifica scatti anzianità',
            'Verifica TFR maturato',
            'Stampa prospetti riepilogativi',
            'Controllo email datori',
        ]
        for label in attivita_default:
            AttivitaMensile.objects.get_or_create(label=label)
        self.stdout.write(self.style.SUCCESS('OK'))
