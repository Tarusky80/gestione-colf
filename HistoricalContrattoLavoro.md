# HistoricalContrattoLavoro — Sostituzione di `_thread_local`

## Problema originale

Il versioning di `ContrattoLavoro` usava `_thread_local` per trasportare l'utente richiedente dal middleware alla view, combinato con un signal custom `_crea_modifiche_contratto` e il metodo `_tracked_fields` su `save()`. Questo approccio era:

- **Fragile** — dipendeva dallo stato globale del thread
- **Non thread-safe** — sotto carichi concorrenti poteva mischiare utenti
- **Manutenzione onerosa** — ogni nuovo campo da tracciare richiedeva modifiche in 3 punti
- **Solo 11 campi tracciati** — modifiche ad altri campi (es. indennità, notturno, convivenza) non venivano registrate

## Soluzione

### 1. django-simple-history (3.8.0)

Sostituisce `_thread_local` + signal custom con versioning automatico via `register(ContrattoLavoro)`.

**File modificati:**

| File | Modifica |
|------|----------|
| `requirements.txt` | Aggiunto `django-simple-history==3.8.0` |
| `core/settings.py` | `INSTALLED_APPS` += `simple_history`, MIDDLEWARE += `HistoryRequestMiddleware` |
| `paghe/models.py` | Rimossi `_thread_local`, `_tracked_fields`, `_fmt_valore()`, tracking in `save()`, signal `_crea_modifiche_contratto`. Aggiunto `register(ContrattoLavoro)` dopo la classe |
| `paghe/views/_common_imports.py` | Rimosso import `_thread_local` |
| `paghe/views/_anagrafiche_ajax.py` | Rimossi `_thread_local._contratto_user = request.user` (righe 125, 191) |
| `paghe/migrations/0093_historicalcontrattolavoro.py` | Migrazione creata e applicata |

### 2. Proxy model e segnali Django (BUG critico)

**Problema:** `ajax_modifica_contratto` usava `get_object_or_404(ContrattoAttivo, pk=pk)`.  
`ContrattoAttivo` è un **proxy model** di `ContrattoLavoro`. Django invia `post_save` con `sender=ContrattoAttivo`, ma simple-history ascolta su `sender=ContrattoLavoro`.  
Il segnale non arrivava → nessuna registrazione storica.

**Fix:** `_anagrafiche_ajax.py:143` — cambiato `ContrattoAttivo` in `ContrattoLavoro` con filtro `stato='ATTIVO'`:

```python
# PRIMA (non funzionava):
contratto = get_object_or_404(ContrattoAttivo, pk=pk)

# DOPO (funziona):
contratto = get_object_or_404(ContrattoLavoro, pk=pk, stato='ATTIVO')
```

### 3. View `ajax_storico_modifiche_contratto`

Mostra sia i vecchi record `ModificaContratto` (dati pre-migrazione) che i nuovi snapshot simple-history.

**Bug risolti nella view:**

| Bug | Causa | Fix |
|-----|-------|-----|
| Creazione contratto non mostrata | `prev_record is None` → record saltato | Aggiunto item "Contratto creato" quando `prev_record is None` |
| Solo 11 campi tracciati | Confronto manuale su lista fissa di campi | Sostituito con `h.diff_against(prev)` (simple-history) che confronta TUTTI i campi |
| Ordinamento rotto tra anni | Sort su stringa `DD/MM/YYYY` | Passato datetime object, formattato nel template con `|date:'d/m/Y H:i'` |

### 4. Admin Django

Registrato `HistoricalContrattoLavoro` in `paghe/admin.py` per consultazione via `/admin/paghe/historicalcontrattolavoro/`.

### 5. ModificaContratto (vecchio modello)

Il modello `ModificaContratto` e la sua tabella DB sono **mantenuti** (dati storici pre-migrazione consultabili). Non viene più scritto.

## Test

```bash
python manage.py check                                   # 0 issues
python manage.py migrate paghe 0093                       # OK
python manage.py test paghe.tests -v2                     # 18/19 OK (errore auditlog pre-esistente)
```

### Test manuali consigliati

1. Avvia server: `python manage.py runserver`
2. Apri un contratto attivo, modifica un campo qualsiasi (es. Note), salva
3. Verifica nella sezione "Storico variazioni" del contratto che appaia la modifica
4. Verifica in `/admin/paghe/historicalcontrattolavoro/` che lo snapshot sia presente
5. Controlla che i vecchi record `ModificaContratto` (pre-migrazione) siano ancora visibili
