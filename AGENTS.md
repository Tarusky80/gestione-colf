# GESTIONE COLT — Piano di sviluppo

## Completato
- ✅ Fix `sort-table.js` — toggle A→Z/Z→A non funzionante (controllava `sort-asc` invece di `sort-desc`)
- ✅ Fix pulsante STAMPA abilitato in 6 template calcolo
- ✅ `.btn-new` in utils.css, rimosso inline duplicate
- ✅ Typo `incoda` → `incolla-btn` in 3 popup
- ✅ `btn-outline-*` → `btn-ghost-*` (~28 occorrenze in 7 file)
- ✅ HTML invalido `style="class=..."` corretto (27 bottoni Aiuto)
- ✅ JS duplicati `getCSRFToken()` consolidati in base.html
- ✅ Modali Aiuto sfondo bianco unificati (`modal-content card-alt`)
- ✅ Bug querySelector `.btn-ghost-success` (SALVA vs APRI POPUP) con classe `salva-codice-btn`
- ✅ Pulsante SALVA popup INPS rosso (`btn-ghost-danger`)
- ✅ Console.log/DEBUG rimossi (36 occorrenze in 14 file)
- ✅ `type="button"` aggiunto ai bottoni con onclick/class ghost (62 file)
- ✅ Fix rename `importo` → `totale` in `_calcoli_core.py` + callers + template
- ✅ Fix `ind.orario` undefined in `_calcola_busta_data()`
- ✅ Fix encoding breadcrumb `documentale_edit.html`
- ✅ Toggle switch viola in Modifica Datore/Lavoratore/Contratto (sezione "Visibile agli operatori")
- ✅ Pulsante RIEPILOGO in calcoli_list.html: genera PDF (ReportLab), salva in DocumentoArchiviato, apre nel pannello
- ✅ Frecce navigazione contratto (`< >`) spostate dopo dropdown Contratto, allineate ai bordi interni

## Piano Feature ✅ Completate

### 1. 🎨 Loading Skeletons
- ✅ CSS skeleton animati in `utils.css` (`.skeleton`, `.skeleton-text`, `.skeleton-card`, etc.)
- ✅ `_calcoli_busta_wrapper.html`: spinner sostituito con skeleton card
- ✅ `base.html`: `bustaPreviewLoading` con skeleton
- ✅ `calcoli_inverso.html`, `calcoli_malattia.html`, `calcoli_notturno.html`, `calcoli_tfr.html`: loading rimpiazzati
- ✅ `lul_list.html`: spinner generazione LUL sostituito

### 2. 🔔 Toast Notifications Migliori
- ✅ Container multiplo impilabile (`#toastContainer` + `.toast-item`)
- ✅ Animazioni slide-in/out (keyframe CSS)
- ✅ Icone animate (pulse success, x-circle error)
- ✅ Funzione `mostraToast()` aggiornata per aggiungere toasts multipli
- ✅ `_stampaToast()` delegato a `mostraToast()`

### 3. 📊 Copertura Budget Progress Bar
- ✅ CSS `.budget-progress` in `utils.css`
- ✅ `calcoli_list.html`, `calcoli_non_convivente.html`, `base.html`: testo copertura sostituito con progress bar colorata

### 4. 🏷️ Badge Colorati Uniformi
- ✅ Classi standard in `utils.css`: `.badge-entity-*`, `.badge-calcolo-*`, `.badge-bool-*`, `.badge-status-*`, `.badge-entita[data-tipo]`
- ✅ `buste_archivio.html`: inline if/elif monstrosity sostituito con classi badge-calcolo
- ✅ `eliminati_list.html`: badge inline rimosso, usa `.badge-entita`, badge booleano usa `.badge-bool-*`

### 5. ⌨️ Scorciatoie da Tastiera
- ✅ Ctrl+S → clicca primo pulsante salva visibile
- ✅ Ctrl+P → window.print()
- ✅ Ctrl+Enter → submit del form
- ✅ F1 → clicca pulsante aiuto
- ✅ `?` → mostra toast con elenco scorciatoie

### 6. 🔍 Ricerca Globale Miglioramenti
- ✅ `/` shortcut già esistente
- ✅ Azioni rapide (Dashboard, Nuovo Datore, Nuovo Lavoratore, Nuovo Contratto, Calcola Busta) in cima ai risultati ricerca

### 7. 📄 Riepilogo Stampabile
- ✅ Pulsante "RIEPILOGO" in `calcoli_list.html`
- ✅ Backend ReportLab: `ajax_genera_riepilogo_pdf()` in `_buste_download.py`
- ✅ Salva PDF su disco + `DocumentoArchiviato`, apre nel pannello laterale

### 8. 💾 Backup Automatico Indicatori
- ✅ Dato `ultimo_backup` aggiunto al context processor `global_opzioni`
- ✅ Badge ultimo backup nel sidebar footer con indicatore colore (verde/giallo/rosso)

### 9. 👁️ Anteprima Documento Inline
- ✅ `documentale_list.html`: `window.open` sostituito con modal iframe inline

### 10. 📝 Cronologia Toggles
- ✅ Array globale `_toggleHistory[]`
- ✅ Event delegation su `.toggle-switch input[type="checkbox"]`
- ✅ Funzione `mostraToggleHistory()` con pannello modale
- ✅ Badge conteggio toggles nel sidebar footer
- ✅ Pulsante "Cancella cronologia"

### 11. 📊 Widget Grafici Chart.js
- ✅ `_contributi_mensili_trend()` backend function (12 mesi)
- ✅ `documenti_per_tipo` backend context
- ✅ Doughnut chart "Documenti per tipo" in dashboard
- ✅ Line chart "Trend Contributi (12 mesi)" in dashboard (riusa `creaGraficoLine`)

### 12. 📁 Cartelle Espandibili Documenti
- ✅ Pulsante "ALBERO" in `documenti_list.html`
- ✅ JS raggruppa righe tabella per datore con expand/collapse
- ✅ CSS per `.albero-view`, `.albero-header`, `.albero-body`

## Prossimi miglioramenti proposti (3 rimasti)

### 13. ✅ Pulizia console.log/DEBUG
- ✅ 36 occorrenze rimosse/sostituite in 14 file
- ✅ `ajax_helpers.js`: 3 debug log rimossi
- ✅ `base.html`: 19 console rimossi (DEBUG step, progetti, TinyMCE, RigeneraCessazione)
- ✅ 7 template calcolo: console.error(e) rimossi (ridondanti con mostraToast già presenti)
- ✅ `liste.html`, `popup_ccnl_occhio.html`, `stampe_invii.html`, `crea_pagopa.html`: sostituiti con mostraToast

### 14. 📦 Estrarre JS inline da base.html
- ✅ `sort-table.js` — ordinamento tabelle (57 righe)
- ✅ `nav-layout.js` — sidebar/topbar toggle + nav gruppi collassabili (60 righe)
- ✅ `csrf-utils.js` — getCookie, _csrfToken, getCSRFToken (11 righe)
- ✅ `toast.js` — mostraToast, _stampaToast (23 righe)
- ✅ `table-filters.js` — filterTable, filtraPerComune, aggiornaConteggio (47 righe)
- ⏳ Blocco principale app (~2546 righe) + blocco documenti (~1476 righe) — troppo interconnesso, da pianificare con più calma
- Vantaggi: caching HTTP, manutenibilità, separazione responsabilità

### 15. 🎨 Ridurre style=inline → classi CSS
- ✅ Aggiunte nuove classi utility in `utils.css`: `.ml-auto`, `.fw-8`, `.fs-16/18/20/22`, `.empty-state`, `.error-state`, `.label-info`, `.label-info-12`, `.mt-2/4`
- ✅ `margin-left:auto` → `.ml-auto` (67 occorrenze nav sidebar)
- ✅ `color:#8A8F98;font-size:11px` → `.c-11-m` (1 occorrenza)
- ✅ `color:#8A8F98;font-size:13px` → `.c-muted.fs-13` (1 occorrenza)
- ✅ `font-size:10px;color:#8A8F98;display:block` → `.label-info` (12 occorrenze in renderBusta())
- ⏳ ~4218 style= inline in ~80 file (top 5: base.html 344, ajax_form_contratto.html 325, dashboard.html 160, calcoli_conviventi_ccnl.html 158, calcoli_non_convivente.html 158)
- 📝 Da fare più avanti: convertire per pattern ricorrenti, iniziando dai top 5 file

### 16. 📱 Responsive Design — Versione Mobile Separata
- ✅ Piano definito: prefisso `/m/`, template in `templates/mobile/`, CSS in `static/css/mobile.css`
- ✅ **Step 1**: `base_mobile.html` + `mobile.css` + rilevatore redirect in `<head>` di base.html
- ✅ **Step 2**: Dashboard mobile (`/m/`) — 4 card grid, totale contratti, trend 3 mesi
- ✅ **Step 3**: Datori / Lavoratori / Contratti lista + FAB + link a dettaglio
- ✅ **Step 4**: Calcoli Busta — select contratto + chips mese/anno → calcola → Lordo/Contributi/Netto
- ✅ **Step 5**: Archivio Buste + Documenti — filtri a chips, swipe-to-action PDF
- ✅ **Dettaglio entità**: 3 pagine (`/m/datori/<pk>/`, `/m/lavoratori/<pk>/`, `/m/contratti/<pk>/`)
- ✅ **Grafica**: topbar gradient, bottom nav pill animata, card bordo colorato, tap ripple, skeleton fluido
- ✅ **Filtri a chips**: chips orizzontali scrollabili per mese/anno/tipo
- ✅ **Pull-to-refresh**: trascina giù per ricaricare
- ✅ **Swipe-to-action**: swipe sinistra nelle buste mostra pulsante PDF
- ✅ **Link versione mobile nella sidebar** desktop (base.html)

### 17. ✅ Loading skeletons per pagine lista
- ✅ `datori_list.html` — 5 scheletri su 8 colonne, fade-out 400ms
- ✅ `lavoratori_list.html` — 5 scheletri su 6 colonne, fade-out 400ms
- ✅ `contratti_list.html` — 5 scheletri su 13 colonne, fade-out 400ms
- ✅ `beneficiari_list.html` — 5 scheletri su 6 colonne, fade-out 400ms

### 18. ✅ Accessibilità
- ✅ `aria-label="Chiudi"` su ~85 `btn-close` in 55 file
- ✅ `alt="Codice captcha"` su captcha image
- ✅ `aria-label` su 4 bottoni × in base.html
- ✅ `aria-hidden="true"` su ~200 icone decorative (fix JS globale)
- ⏳ Elementi `<div onclick>` non semantic (~55 da refactoring strutturale)

### 19. 🌐 Internazionalizzazione (i18n)
- Tutte le stringhe hardcoded in italiano
- Aggiungere `{% trans %}` / `{% blocktranslate %}` per futura traduzione

### 20. 📱 Versione Mobile — 6 nuove feature
- ✅ **Feature 1+2**: Form nativi modifica/creazione mobile — view generica `_mobile_entity_form_view()`, template `entity_form.html` con 3 sezioni collassabili via JS, widget `SelectMultiple` compatto per M2M. 5 FAB `+` aggiornati a `/m/nuovo/?tipo=...`.
- ✅ **Feature 3**: Ricerca globale mobile — view `mobile_ricerca()` cerca in 5 entità (Datore, Lavoratore, Contratto, Beneficiario, Progetto), template con debounce 400ms, icona lente in topbar di `base_mobile.html`.
- ✅ **Feature 4**: Chart.js line chart 12 mesi trend contributi su dashboard mobile (`/m/`), `responsive: false` per evitare infinite resize loop.
- ✅ **Feature 5**: Infinite scroll — JS `avviaInfiniteScroll()` con IntersectionObserver in `_swipe_js.html`. Limiti `[:50]` rimossi da viste archivio buste e documenti. **Manca** endpoint JSON backend paginato.
- ✅ **Feature 6**: Pagina "Altri calcoli" — view, template `altri_calcoli.html`, route `/m/altri-calcoli/`.
- ✅ **Fix**: `reverse` import mancante in `_mobile.py` (NameError 500 su modifica).
- ✅ **Fix**: pulsanti "Modifica" su tutti i dettagli mobile ora puntano a `/m/{entity}/{pk}/modifica/` (non più 404 desktop).
- ✅ **Fix**: form contratto mobile — `CheckboxSelectMultiple` → `SelectMultiple` (compatto), `form.save_m2m()` per salvare M2M, sezioni dati/visibilità/altri.
- ✅ **Pulizia**: NAS sync risolta spostando venv fuori dal progetto (`..\.venv_gestione_colf`), `git rm --cached` di 46 file spuri.
- ✅ **CI**: 12 errori ruff risolti (import/variabili inutilizzati, bare except).
- ✅ **setup_venv.bat**: crea/ricrea virtualenv, `GESTIONE.bat` lo chiama automaticamente.
- **Commit**: `7cfa970` — Mobile: 6 nuove feature + fix form contratto

## Comandi utili
```powershell
# Avviare il server
& "..\.venv_gestione_colf\Scripts\python.exe" manage.py runserver

# Verificare errori Django
& "..\.venv_gestione_colf\Scripts\python.exe" manage.py check

# Backup file prima di modificare
Copy-Item "file" "file.bak"

# Commit
git add -A; git commit -m "msg"; git push
```
