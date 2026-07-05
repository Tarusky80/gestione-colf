# PIANO DI SVILUPPO — GESTIONECOLF

> Aggiornato: 01/07/2026

---

## STATO COMPLETAMENTO

| Feature | Stato |
|---------|-------|
| DEFAULT_AUTO_FIELD, Django 6.0.5, pulizia Jazzmin | ✅ |
| LOGGING strutturato su file (RotatingFileHandler) | ✅ |
| `except Exception:` → `logger.exception()` (~144 occorrenze) | ✅ |
| CCNL full-text (56 articoli, fixture, PDF grayscale, Roboto) | ✅ |
| Guide documentali (assunzione, decalogo, cessazione) con PDF/email | ✅ |
| Scadenziario annuale integrato in agenda (19 eventi) | ✅ |
| Composizione multipla stampe-invii (guide + CCNL) | ✅ |
| Requirements updater (auto-fetch PyPI) | ✅ |
| Voci recenti in dashboard (pills sotto orologio) | ✅ |
| RBAC multi-ruolo (4 ruoli, 21 permessi, ~120 view decorate) | ✅ |
| Pannello permessi `/permessi/` | ✅ |
| `filtro_visibilita()` su Datore/Lavoratore/Contratto | ✅ |
| Menu condizionali per permessi in sidebar | ✅ |
| Fix vari (audit signal, email allegati su disco, EPIPE, breadcrumb, ecc.) | ✅ |
| Ctrl+K ricerca globale potenziata | ✅ |
| LUL — Libro Unico del Lavoro | ✅ |
| Modello astratto AnagraficaBase (DRY) — `models.py:223` | ✅ |
| simple-history — sostituito `_thread_local` + migration 0093 | ✅ |
| REST API + Employer Portal 2.0 — 13 endpoint, Portal Vue 3 buildato | ✅ (manca NotificaDatore) |
| Backup su Cloud (Google Drive / SFTP) | ⬜ |
| CSS inline → file statici `.css/.js` | ⬜ |
| Celery + Redis per operazioni asincrone | ⬜ |
| Internazionalizzazione (i18n) | ⬜ |
| Inquadramento (8 livelli, 2 periodi, PDF+HTML+email) | ✅ |
| Tabelle Retributive (2025-2026, A4 Landscape, PDF+HTML+email) | ✅ |
| Verifica CCNL (confronto ParametriCCNL vs Tabelle Retributive) | ✅ |
| Contributi INPS 2026 — 6 fasce con soglie paga oraria | ✅ |
| Pagina Contributi CCNL (HTML+PDF+email+composizione multipla) | ✅ |

---

## ✅ COMPLETATI

### DEFAULT_AUTO_FIELD, Django 6.0.5, Jazzmin
- `DEFAULT_AUTO_FIELD = 'BigAutoField'` in settings.py
- Django 5.2.15 → 6.0.5 (requirements.txt)
- `JAZZMIN_SETTINGS` rimosso (dead code)

### Alert contratto nel modale
- View AJAX + badge per contratti in scadenza
- Backup dashboard (ultimo_backup in Riepilogo Rapido)
- Shortcut Ctrl+ (max_length=15, keydown handler)
- Toast 5s + pulsante ×
- Fix IntegrityError scorciatoie

### LOGGING strutturato
- `core/settings.py`: RotatingFileHandler (10MB, 5 backup), console + file
- `paghe/automation.py`, `paghe/automation_playwright.py`: `logging.basicConfig()` rimosso → `logger = logging.getLogger(__name__)`
- Logger separati per `paghe`, `django.request`, `apscheduler`

### `except Exception:` → `logger.exception()`
- **Batch 1 (critici)**: `signals.py` (audit save/delete), `context_processors.py` (URL)
- **Batch 2 (automation)**: `automation.py` (51 fix), `automation_playwright.py` (63 fix)
- **Batch 3 (view top)**: `_gestione_pdf.py`, `_pagopa_auto.py`, `_stampe_invii.py`, `_testi.py`
- **Batch 4 (resto)**: `_documenti.py`

### CCNL — Contratto Collettivo Nazionale del Lavoro
- Fixture 56 articoli da mondocolf.it, deduplicato, NFC normalizzato
- `python manage.py popola_ccnl` per caricamento
- Parser struttura `analizza_testo_ccnl()` (livello, mansione, elenchi, paragrafi)
- PDF grayscale con Roboto (ReportLab + TTFont, 4 varianti)
- HTML strutturato con highlight JS (TreeWalker + `el.normalize()`)
- Invio email con salvataggio PDF su `CARTELLA_DOCUMENTI/CCNL/`
- Disponibile in composizione multipla `/stampe-invii/`

### Guide documentali
- 3 guide: Assunzione (9 sezioni), Decalogo Colloquio (10 punti), Cessazione (8 sezioni)
- Contenuti strutturati in `GUIDE_DATA` (Python), factory `_guide_view()`
- HTML + PDF grayscale (margini 10mm) + invio email
- PDF salvato su `CARTELLA_DOCUMENTI/GUIDE/` prima dell'invio
- Template: `guida_assunzione.html`, `guida_decalogo_colloquio.html`, `guida_cessazione.html`

### Scadenziario in agenda
- `SCADENZE_FISSE` a livello modulo in `_agenda.py` (19 scadenze annuali)
- Gestione fine mese via `monthrange()` (corretto Feb 28/29)
- Eventi virtuali annuali (nessun record DB)
- Prospetto paga mensile, rilascio CU 31/3, richiesta ferie 31/5, tredicesima 20/12

### Composizione multipla stampe-invii
- Nuova categoria `GUIDE_DOCUMENTI` (4 tipi: GUIDA_ASSUNZIONE, GUIDA_DECALOGO, GUIDA_CESSAZIONE, CCNL)
- Cache `_documenti_generici_cache` per riuso PDF identici tra contratti
- Template aggiornato con classe `.comp-tag-guida`

### Requirements updater
- View `ajax_aggiorna_requirements()` — fetcha ultime versioni PyPI
- Riscrive requirements.txt
- `ESCLUDI_DA_AGG = {'reportlab'}` (vincolo xhtml2pdf <5)
- Pulsante "Aggiorna requirements.txt" (sostituisce aggiornamenti singoli)

### Voci recenti in dashboard
- Pills sotto orologio, max 6, deduplicate, ordine cronologico
- Tracciamento via sessione (nessuna migrazione DB)
- JS silenzioso su navigazione menu laterale

### RBAC — Multi-profilo con permessi
- **4 ruoli**: ADMIN, OPERATORE, CONSULENTE, DATORE
- **21 permessi** granulari (anagrafiche.*, contratti.*, buste.*, documenti.*, backup, impostazioni, report, audit_log, permessi)
- **Modello `ProfiloUtente`**: `OneToOneField` con `User`, campo `ruolo`, `permessi_json` (sovrascritture)
- **Migration 0087**: ProfiloUtente + campo `visibile_a` M2M su DatoreLavoro, Lavoratore, ContrattoLavoro
- **Decoratore `@permesso_richiesto(permesso)`** — ~120+ view in 22 file
- **11 view convertite da `@staff_member_required`** a `@permesso_richiesto`
- **`filtro_visibilita()`**: limita queryset per utenti senza `anagrafiche.vedi_tutti`
- **`ha_permesso()`**: superuser bypass, fallback `ProfiloUtente.DoesNotExist`
- **Menu condizionali**: `{% if permessi_utente.xxx %}` in `base.html` per tutti i nav-group
- **Footer sidebar**: mostra ruolo utente (es. `ADMIN`)
- **Pannello permessi `/permessi/`**: tabella utenti, modale modifica ruolo + sovrascritture individuali, delta JSON
- **Context processor**: `ruolo_utente` + `permessi_utente` in `global_opzioni()`, badge conteggio staff in `shortcut_keys()`
- **Backfill automatico**: utenti staff senza ProfiloUtente vengono creati al login (ADMIN se superuser, OPERATORE altrimenti)
- **Test**: `paghe/tests/test_permessi.py` (9 test, 4 ruoli, visibilità, lettura/riservate)

### Inquadramento (8 livelli, 2 periodi)
- `_inquadramento.py`: `INQUADRAMENTO_DATA` (8 livelli A–DS, 2 periodi di validità)
- HTML TreeWalker search + highlight, PDF grayscale con Roboto
- Invio email con PDF salvato su `CARTELLA_DOCUMENTI/INQUADRAMENTO/`
- Disponibile in composizione multipla (`RIFERIMENTI_NORMATIVI`)

### Tabelle Retributive (2025-2026)
- `_tabelle_retributive.py`: `TABELLE_DATA` (9 livelli + livello unico, 12 colonne)
- PDF A4 Landscape per densità colonne, HTML con filtro anno/livello
- Invio email con PDF salvato su `CARTELLA_DOCUMENTI/TABELLE/`
- Disponibile in composizione multipla (`RIFERIMENTI_NORMATIVI`)

### Verifica CCNL
- View `verifica_ccnl()` + `_confronta_ccnl_db()` in `_tabelle_retributive.py`
- Confronta `TABELLE_DATA` vs `ParametriCCNL` (7 colonne + 3 indennità)
- Mapping approssimativo per 3 colonne (C, G, H) con badge `~`
- Template `verifica_ccnl.html` con badge riepilogativi e tabella colorata

### Pagina Contributi CCNL (HTML+PDF+email+composizione multipla)
- `_contributi_ccnl.py`: dati strutturati (4 fasce), HTML builder, PDF grayscale con Roboto
- Template `contributi_ccnl.html` con tabella, note, riferimenti normativi, help modal
- `_modale_invio_contributi.html` per invio email selettivo
- Disponibile in composizione multipla (`RIFERIMENTI_NORMATIVI`)
- Menu laterale in `base.html` con icona `bi-percent`
- **Fix tema scuro**: allineato a palette #17181C/#EDEDED/C0C4CC come Inquadramento e Tabelle Retributive

### Contributi INPS 2026 — 6 fasce con soglie paga oraria
- 2 nuovi campi in `OpzioniSoftware`: `soglia_paga_1_contributi` (9.61), `soglia_paga_2_contributi` (11.70)
- `_calcola_contributi()` ora usa `paga_eff_inps_oraria` per selezionare fascia
- 3 fasce ≤24,9h (FINO A 9,61 / 9,61-11,70 / OLTRE 11,70) + 1 fascia >24,9h
- Migration 0088, DB aggiornato (rinomina + 2 nuovi record)
- Aggiornati tutti i chiamanti: `_pagopa_auto.py`, `field_resolver.py`, `_datore_accesso.py`, `_liste.py`
- Test: 9/9 modelli + 9/9 permessi OK

### Fix vari
- Audit signal: `str(instance)` rimosso (causava AttributeError su Appuntamento)
- Invio email: PDF salvato su disco prima dell'invio (fix SMTP + Thunderbird)
- `Beneficiario`: rimosso `filtro_visibilita` (manca campo `visibile_a`)
- `event` passato esplicitamente nelle funzioni onclick (compatibilità Firefox)
- Breadcrumb: rimosso `{% url 'documentale_list' %}` con parametro obbligatorio
- Nome template: `decalogo_colloquio.html` → `guida_decalogo_colloquio.html`
- About page: rimosso auto-check aggiornamenti al caricamento
- Struttura if/elif in `_stampe_invii.py`: `PAGINA_BIANCA` non cadeva in `_genera_documento_stampe`
- `buste_paga_massivo`: aggiunto `@login_required` (mancante)
- `DatoreLavoro.save()` sovrascrive `nome_cognome` con `nome + cognome`

---

## 📋 DA FARE

### 1. CSS inline → file statici `.css/.js`
- **File**: ~57 template in `templates/paghe/`, `base.html` (4897 righe)
- **Sforzo**: alto
- **Problema**: ~3.580 occorrenze `style=`, nessun `paghe.css` o `paghe.js`
- **Soluzione**: Estrarre in `static/css/paghe.css` e `static/js/paghe.js`

### 2. Backup su Cloud (Google Drive / SFTP)
- **File**: nuovi: `paghe/models.py` (DestinazioneCloud), `paghe/cloud/` (uploader astratto)
- **Sforzo**: medio (2-3 giorni)
- **Problema**: Nessun upload remoto — solo backup locale su disco
- **Soluzione**: `DestinazioneCloud`, `CloudUploader` → GoogleDriveUploader, SFTPUploader; hook in `GestoreBackup.save()`

---

## FEATURE FUTURE (DETTAGLIO)

### ✅ Ctrl+K Ricerca globale potenziata
- `filtro_visibilita()` applicato in `global_search_view`
- Risultati filtrati per ruolo utente

### ✅ LUL — Libro Unico del Lavoro
- Modulo `_lul.py`, template `lul_list.html`, route, menu sidebar
- Checkbox "Allega LUL" in 8 template calcoli
- PDF generato on-the-fly da BustaPaga, raggruppato per datore
- Variabili template LUL in `_risolvi_variabili_testo()`

---

### REST API + Employer Portal 2.0

**Stato:** ✅ COMPLETATO (manca solo NotificaDatore)

**Realizzato:**
- DRF 3.17.1 + SimpleJWT 5.5.1 + django-cors-headers in `requirements.txt`
- Directory `paghe/api/` con `urls.py`, `views.py` (294 righe), `serializers.py` (186 righe), `permissions.py`, `auth.py`
- **13 endpoint** sotto `/api/v1/`: token, token/refresh, profilo datore, contratti, documenti, richieste (CRUD), download busta PDF, download documento PDF, studio, referenza PDF
- Autenticazione JWT custom (`DatoreJWTAuthentication`) con supporto `?token=` in query string per download
- Permessi custom `IsDatore` / `IsProprioDatore`
- Portal SPA Vue 3 + Vite 6 buildato in `frontend/dist/`
- View `portal_spa` + route `/portal/` in `paghe/urls.py`

**Ancora da fare:**
- `NotificaDatore` model: notifiche automatiche su nuovo documento, richiesta accettata/rifiutata, scadenza contratto
- Password reset flow: token itsdangerous (30 min), email con link
- Download massivo ZIP documenti
- `_notifiche.py`, template reset password
**Effort residuo:** ~1 giorno

---

### Backup su Cloud (Google Drive / SFTP)

**Obiettivo:** Invio automatico backup a destinazione cloud.

**Modello `DestinazioneCloud`:** servizio (Google Drive / SFTP), token OAuth2, credenziali SFTP cifrate.

**Uploader astratto:** `CloudUploader` → `GoogleDriveUploader`, `SFTPUploader`.

**Integrazione:** Hook in `GestoreBackup.save()` → upload a tutte le destinazioni abilitate.

**OAuth2 Google Drive:** flow completo (autorizzazione → callback → selettore cartella).

**Viste:**
- `/impostazioni/cloud/` — configurazione
- `/ajax/cloud/test/<pk>/` — test connessione
- `/ajax/cloud/collega-google/` — OAuth2 init
- `/ajax/cloud/google-callback/` — OAuth2 callback

**Effort:** 2 giorni (Google Drive), +1 giorno (SFTP)
