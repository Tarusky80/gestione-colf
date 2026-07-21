# GESTIONE COLF

Applicazione Django per la gestione di collaboratori domestici (colf, badanti, baby-sitter).\
Genera buste paga, CU, TFR, contratti, e automatizza le operazioni INPS e PagoPA.

## Funzionalità

- **Contratti di lavoro** — gestione completa con storico revisioni
- **Buste paga** — calcolo automatico di ore, contributi INPS, TFR, indennità, scatti di anzianità
- **Certificazione Unica (CU)** — generazione e invio massivo
- **PagoPA** — integrazione per pagamento contributi con automazione
- **Automazione INPS** — duale Selenium / Playwright con rilevamento automatico
- **Report PDF** — buste, cedolini, contratti, report mensili/annuali
- **Documentale** — modelli personalizzabili con variabili contestuali
- **Agenda** — appuntamenti con ricorrenze e notifiche
- **Audit log** — tracciamento completo di ogni operazione
- **Backup automatico** — schedulato con APScheduler
- **Mappa beneficiari** — geolocalizzazione su mappa (Leaflet.js + MarkerCluster)
- **Multi-ruolo** — admin, consulente, operatore, datore di lavoro
- **Interfaccia** — Bootstrap 5, dark mode, responsive + versione mobile nativa (`/m/`)

## Requisiti

- Python 3.14+
- Windows 10/11 (per automazione INPS con Chromium/Playwright)
- 4 GB RAM (8 GB consigliati per automazione INPS)

## Installazione rapida

```bash
git clone https://github.com/Tarusky80/gestione-colf.git
cd gestione-colf
python -m venv ..\.venv_gestione_colf
..\.venv_gestione_colf\Scripts\pip install -r requirements.txt
..\.venv_gestione_colf\Scripts\python manage.py migrate
..\.venv_gestione_colf\Scripts\python manage.py runserver
```

Oppure esegui `GESTIONE.bat` che automatizza tutto (venv esterno a `..\.venv_gestione_colf`, dipendenze, migrate, avvio).

### Variabili d'ambiente (`.env`)

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `DJANGO_SECRET_KEY` | `change-me` | Chiave segreta Django (obbligatoria in produzione) |
| `DJANGO_DEBUG` | `True` | Modalità debug |
| `DJANGO_ALLOWED_HOSTS` | `*` | Host consentiti |

## Struttura

```
core/                configurazione Django (settings, urls, middleware)
paghe/               app principale (modelli, viste, test, utility)
templates/           template HTML (Bootstrap 5) + mobile/
static/              file statici (CSS, JS, immagini, font)
frontend/            risorse frontend (build, assets)
data/                dati geo (mappa beneficiari)
logs/                log applicativi
media/               upload e documenti generati
drivers/             chromedriver
```

## Versione Mobile

Accessibile automaticamente su schermi <768px o manualmente a `/m/`.

- **Dashboard** — card riepilogo + grafico trend contributi 12 mesi (Chart.js)
- **Anagrafiche** — Datori / Lavoratori / Contratti / Beneficiari / Progetti con liste, dettaglio e modifica nativa
- **Ricerca globale** — cerca in 5 entità con debounce live e icona in topbar
- **Calcolo busta paga rapido** — contratto + mese/anno → Lordo/Contributi/Netto
- **Altri calcoli** — indennità, malattia, notturno, TFR, rateo
- **Archivio buste e documenti** — filtri a chips, infinite scroll, swipe-to-action PDF
- **Form nativi** — creazione/modifica entità con sezioni collassabili, widget SelectMultiplatform compatti
- **Navigazione** — bottom nav con pill animata, topbar con pulsante ricerca
- **Pull-to-refresh** e **skeleton loading** su tutte le liste
- **Tema scuro** — shadcn/ui-inspired design system

## Comandi principali

| Comando | Descrizione |
|---------|-------------|
| `python manage.py check` | Verifica configurazione Django |
| `python manage.py test paghe.tests -v2` | Suite di test (31 test) |
| `ruff check .` | Analisi statica del codice |
| `coverage run --source=paghe manage.py test paghe.tests -v2` | Test con coverage |
| `python manage.py makemigrations` | Crea migrazioni |
| `python manage.py migrate` | Applica migrazioni |
| `python manage.py collectstatic` | Raccoglie file statici |

## Tecnologie

- **Framework**: Django 6.0, Django REST Framework
- **Database**: SQLite
- **PDF**: ReportLab 4.5, xhtml2pdf, pypdf
- **Automazione**: Selenium, Playwright
- **Frontend**: Bootstrap 5, Leaflet.js, TinyMCE
- **Autenticazione**: Simple JWT, django-cors-headers
- **Altro**: Simple History, django-import-export, APScheduler, bleach, cryptography

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`):

1. **lint** — `ruff check .`
2. **check** — `python manage.py check`
3. **test** — `coverage run && coverage report`

## Sviluppo

```bash
# ambiente virtuale (posizionato fuori dal progetto per evitare sync NAS)
python -m venv ..\.venv_gestione_colf
..\.venv_gestione_colf\Scripts\activate

# dipendenze
pip install -r requirements.txt

# lint
ruff check . --fix

# test
python manage.py test paghe.tests -v2

# coverage
coverage run --source=paghe manage.py test paghe.tests -v2
coverage report
coverage html
```

## Licenza

Uso interno / privato. Non distribuito pubblicamente.
