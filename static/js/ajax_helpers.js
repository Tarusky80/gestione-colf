let currentAjaxUrl = '';
function loadAjaxForm(url, title) {
    currentAjaxUrl = url;
    console.log('loadAjaxForm called with URL:', url, 'Title:', title);
    const offcanvasEl = document.getElementById('panelNuovo');
    const bsOffcanvas = bootstrap.Offcanvas.getInstance(offcanvasEl) || new bootstrap.Offcanvas(offcanvasEl);
    document.getElementById('offcanvas-title').innerText = title;
    const container = document.getElementById('offcanvas-form-container');
    container.innerHTML = `<div class="text-center mt-5"><div class="spinner-border" style="color: var(--accent-color);"></div><p class="text-secondary mt-3 small">Recupero dati...</p></div>`;
    bsOffcanvas.show();
    fetch(url)
        .then(res => {
            console.log('Fetch response status:', res.status);
            if (!res.ok) throw new Error('Errore del server Django (Codice ' + res.status + ')');
            const ct = res.headers.get('content-type') || '';
            console.log('Content-Type:', ct);
            if (ct.includes('application/json')) {
                return res.json();
            }
            return res.text().then(html => ({ html }));
        })
        .then(data => {
            if (data.success || data.html) {
                container.innerHTML = data.html;
                setTimeout(function() { initStepForm(container); }, 50);
            }
        })
        .catch(error => {
            container.innerHTML = `<div class="alert alert-danger mt-4" style="background-color: rgba(220,53,69,0.1); border-color: rgba(220,53,69,0.2); color:#ff6b6b;">
                <i class="bi bi-exclamation-triangle-fill me-2"></i><b>Ops! C'è un intoppo nel backend.</b><br><br><span style="font-size:13px;">${error.message}</span><br><br>
            </div>`;
        });
}

document.addEventListener('keydown', function (event) {
    const isTyping = ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName);
    const searchInput = document.getElementById('globalSearch');
    if (event.key === '/' && searchInput) {
        if (document.activeElement.id !== 'globalSearch') {
            event.preventDefault();
            searchInput.focus();
        }
        return;
    }
    if (isTyping) return;
    const key = event.key.toLowerCase();
    if (key === 'd') loadAjaxForm('/ajax/nuovo-datore/', 'Nuovo Datore');
    else if (key === 'l') loadAjaxForm('/ajax/nuovo-lavoratore/', 'Nuovo Lavoratore');
    else if (key === 'b') loadAjaxForm('/ajax/nuovo-beneficiario/', 'Nuovo Beneficiario');
    else if (key === 'n') loadAjaxForm('/ajax/nuovo-contratto/', 'Nuovo Contratto');
});

function toggleAll(source) {
    const checkboxes = document.querySelectorAll('input[name="contract_ids"]');
    for (const cb of checkboxes) { cb.checked = source.checked; }
}
function bulkActionContracts() {
    const selected = [];
    const checkboxes = document.querySelectorAll('input[name="contract_ids"]:checked');
    checkboxes.forEach(cb => selected.push(cb.value));
    if (selected.length === 0) { alert('Nessun contratto selezionato.'); return false; }
    alert('Azioni di bulk su contratti: ' + selected.join(', '));
    return false;
}

// ===== MULTI-STEP FORM (contratto) =====
function initStepForm(container) {
    const form = container.querySelector('#dynamicForm');
    if (!form) return;
    const stepEls = form.querySelectorAll('[data-step]');
    if (!stepEls.length) return;

    var totalSteps = 4;
    var stepLabels = ['Anagrafiche', 'Dettagli', 'Opzioni', 'Note'];
    var currentStep = 1;

    const scrollArea = form.querySelector('div[style*="overflow-y: auto"]');
    if (!scrollArea) return;

    // --- Step indicator ---
    var indicator = document.createElement('div');
    indicator.style.cssText = 'display:flex;align-items:center;justify-content:center;gap:6px;margin-bottom:18px;padding:12px 0;flex-shrink:0;';
    var dotsHtml = '';
    for (var i = 1; i <= totalSteps; i++) {
        dotsHtml += '<div class="step-circle" data-s="' + i + '" style="width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;color:#fff;background:#27282D;border:2px solid #333;transition:all 0.3s;cursor:default;">' + i + '</div>';
        if (i < totalSteps) {
            dotsHtml += '<div class="step-line" style="flex:1;min-width:40px;max-width:80px;height:2px;background:#27282D;transition:background 0.3s;"></div>';
        }
    }
    indicator.innerHTML = '<div style="display:flex;align-items:center;gap:6px;width:100%;max-width:400px;">' + dotsHtml + '</div>';
    scrollArea.insertBefore(indicator, scrollArea.firstChild);

    // --- Step labels below circles ---
    var labelRow = document.createElement('div');
    labelRow.style.cssText = 'display:flex;justify-content:space-between;margin-bottom:16px;padding:0 10px;flex-shrink:0;font-size:10px;text-transform:uppercase;letter-spacing:0.05em;color:#8A8F98;font-weight:600;';
    labelRow.innerHTML = stepLabels.map(function(l) { return '<span class="step-label" style="text-align:center;flex:1;">' + l + '</span>'; }).join('');
    scrollArea.insertBefore(labelRow, indicator.nextSibling);

    // --- Enhance Progetti section ---
    enhanceProgettiSelection(form);

    // --- Integrate Opzioni Riepilogo into the fixed box ---
    integrateOpzioniRiepilogo(form);

    // --- Replace footer buttons ---
    var footer = form.querySelector('div[style*="border-top"]');
    if (footer) {
        footer.innerHTML =
            '<div class="step-nav" style="display:flex;gap:10px;align-items:center;width:100%;">' +
                '<button type="button" class="btn" id="stepPrevBtn" style="color:#8A8F98;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:10px 18px;font-size:13px;font-weight:500;display:none;"><i class="bi bi-chevron-left"></i> Indietro</button>' +
                '<div style="flex:1;"></div>' +
                '<button type="button" class="btn-linear" id="stepNextBtn" style="background:var(--accent-color,#5E6AD2);color:white;border:none;border-radius:8px;padding:10px 24px;font-size:13px;font-weight:600;box-shadow:0 4px 12px rgba(94,106,210,0.3);">Avanti <i class="bi bi-chevron-right"></i></button>' +
                '<button type="submit" class="btn-linear" id="btnSalvaForm" style="background:var(--accent-color,#5E6AD2);color:white;border:none;border-radius:8px;padding:10px 24px;font-size:13px;font-weight:600;display:none;box-shadow:0 4px 12px rgba(94,106,210,0.3);"><i class="bi bi-check2"></i> Salva Contratto</button>' +
                '<button type="button" class="btn" data-bs-dismiss="offcanvas" style="color:#8A8F98;background:transparent;border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:10px 20px;font-size:13px;font-weight:500;">Annulla</button>' +
            '</div>';
    }

    // --- Nav button listeners ---
    var nextBtn = document.getElementById('stepNextBtn');
    var prevBtn = document.getElementById('stepPrevBtn');
    var salvaBtn = document.getElementById('btnSalvaForm');

    function showStep(n) {
        currentStep = n;
        for (var i = 0; i < stepEls.length; i++) {
            var el = stepEls[i];
            if (parseInt(el.dataset.step) === n) {
                el.style.display = '';
            } else {
                el.style.display = 'none';
            }
        }
        // Update circles
        var circles = indicator.querySelectorAll('.step-circle');
        var lines = indicator.querySelectorAll('.step-line');
        for (var j = 0; j < circles.length; j++) {
            var s = parseInt(circles[j].dataset.s);
            if (s === n) {
                circles[j].style.background = 'var(--accent-color,#5E6AD2)';
                circles[j].style.borderColor = 'var(--accent-color,#5E6AD2)';
            } else if (s < n) {
                circles[j].style.background = '#34d399';
                circles[j].style.borderColor = '#34d399';
            } else {
                circles[j].style.background = '#27282D';
                circles[j].style.borderColor = '#333';
            }
        }
        for (var k = 0; k < lines.length; k++) {
            lines[k].style.background = (k + 1 < n) ? '#34d399' : '#27282D';
        }
        // Update labels
        var labels = labelRow.querySelectorAll('.step-label');
        for (var m = 0; m < labels.length; m++) {
            labels[m].style.color = (m + 1 <= n) ? '#EDEDED' : '#8A8F98';
            labels[m].style.fontWeight = (m + 1 === n) ? '700' : '600';
        }
        // Buttons
        if (prevBtn) prevBtn.style.display = (n === 1) ? 'none' : '';
        if (nextBtn) nextBtn.style.display = (n === totalSteps) ? 'none' : '';
        if (salvaBtn) salvaBtn.style.display = (n === totalSteps) ? '' : 'none';
        // Scroll to top of form
        if (scrollArea) scrollArea.scrollTop = 0;
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', function() {
            if (currentStep < totalSteps) showStep(currentStep + 1);
        });
    }
    if (prevBtn) {
        prevBtn.addEventListener('click', function() {
            if (currentStep > 1) showStep(currentStep - 1);
        });
    }

    // --- Set defaults ---
    setDefaultSelections(form);

    showStep(1);
}

// ===== PROGETTI SEARCH PANEL =====
function enhanceProgettiSelection(form) {
    var progettiSection = form.querySelector('[data-step="1"] .progetto-check-item');
    if (!progettiSection) return;
    var container = form.querySelector('#progettiContainer');
    if (!container) return;
    var filterInput = form.querySelector('#progettiFilter');
    if (filterInput) filterInput.style.display = 'none';

    var bigBtn = document.createElement('button');
    bigBtn.type = 'button';
    bigBtn.id = 'cercaProgettiBtn';
    bigBtn.className = 'btn-linear';
    bigBtn.style.cssText = 'background:var(--accent-color,#5E6AD2);color:white;border:none;border-radius:10px;padding:12px 20px;font-size:14px;font-weight:600;width:100%;display:flex;align-items:center;justify-content:center;gap:10px;margin-bottom:8px;box-shadow:0 4px 16px rgba(94,106,210,0.25);cursor:pointer;';
    bigBtn.innerHTML = '<i class="bi bi-search" style="font-size:18px;"></i> Cerca Progetti';

    var progettiTitle = form.querySelector('.fw-bold:has(.bi-diagram-3)');
    if (progettiTitle) {
        progettiTitle.parentNode.insertBefore(bigBtn, progettiTitle.nextSibling);
    }

    bigBtn.addEventListener('click', function() {
        openProgettiSearch(form, container);
    });
}

function openProgettiSearch(form, container) {
    var checkboxes = container.querySelectorAll('.progetto-checkbox');
    var panelId = 'searchProgettiPanel';
    var panel = document.getElementById(panelId);
    if (!panel) {
        panel = document.createElement('div');
        panel.className = 'offcanvas offcanvas-end';
        panel.id = panelId;
        panel.setAttribute('tabindex', '-1');
        panel.style.width = '440px';
        panel.style.background = 'var(--bg-base)';
        panel.style.borderLeft = '1px solid var(--border-subtle)';
        panel.innerHTML =
            '<div class="offcanvas-header" style="background:var(--bg-surface);border-bottom:1px solid var(--border-subtle);padding:20px 24px;">' +
                '<h5 class="text-white fw-bold mb-0"><i class="bi bi-diagram-3 me-2" style="color:var(--accent-color);"></i>Seleziona Progetti</h5>' +
                '<button type="button" class="btn-close btn-close-white" data-bs-dismiss="offcanvas"></button>' +
            '</div>' +
            '<div class="offcanvas-body" style="padding:20px 24px;display:flex;flex-direction:column;height:100%;">' +
                '<div style="position:relative;margin-bottom:16px;">' +
                    '<i class="bi bi-search" style="position:absolute;left:12px;top:50%;transform:translateY(-50%);color:var(--text-secondary);font-size:13px;z-index:5;"></i>' +
                    '<input type="text" id="progettiSearchInput" placeholder="Filtra progetti per nome..." style="width:100%;padding:10px 12px 10px 36px;border-radius:8px;border:1px solid #27282D;background:#09090B;color:#EDEDED;font-size:13px;">' +
                '</div>' +
                '<div id="progettiSearchList" style="flex:1;overflow-y:auto;min-height:0;"></div>' +
                '<div style="border-top:1px solid var(--border-subtle);padding-top:14px;margin-top:14px;">' +
                    '<button type="button" id="progettiSearchConfirm" class="btn-linear" style="background:var(--accent-color,#5E6AD2);color:white;border:none;border-radius:8px;padding:10px 20px;font-size:13px;font-weight:600;width:100%;box-shadow:0 4px 12px rgba(94,106,210,0.3);">Conferma selezione</button>' +
                '</div>' +
            '</div>';
        document.body.appendChild(panel);
    }

    var list = document.getElementById('progettiSearchList');
    renderProgettiSearchList(list, checkboxes);

    var input = document.getElementById('progettiSearchInput');
    if (input) {
        input.oninput = function() {
            var q = input.value.toLowerCase().trim();
            renderProgettiSearchList(list, checkboxes, q);
        };
    }

    var confirmBtn = document.getElementById('progettiSearchConfirm');
    if (confirmBtn) {
        confirmBtn.onclick = function() {
            syncProgettiSelections(form, container, list);
            var bsOffcanvas = bootstrap.Offcanvas.getInstance(panel);
            if (bsOffcanvas) bsOffcanvas.hide();
        };
    }

    var bsOffcanvas = new bootstrap.Offcanvas(panel);
    bsOffcanvas.show();
}

function renderProgettiSearchList(list, checkboxes, filter) {
    var html = '';
    for (var i = 0; i < checkboxes.length; i++) {
        var cb = checkboxes[i];
        var label = cb.closest('.progetto-check-item');
        if (!label) continue;
        var nameEl = label.querySelector('.progetto-label');
        var name = nameEl ? nameEl.textContent.trim() : 'Progetto #' + cb.value;
        if (filter && !name.toLowerCase().includes(filter)) continue;
        var benef = cb.getAttribute('data-beneficiario') || '';
        var colore = '#10b981';
        var span = nameEl ? nameEl.querySelector('span') : null;
        if (span) {
            var match = nameEl.innerHTML.match(/border-left:\s*3px\s+solid\s+(#[a-f0-9]+)/i);
            if (match) colore = match[1];
        }
        var checked = cb.checked ? 'checked' : '';
        html += '<div class="progetti-search-item" style="padding:10px 12px;border-bottom:1px solid rgba(255,255,255,0.04);cursor:pointer;border-radius:8px;transition:background 0.15s;display:flex;align-items:center;gap:10px;" data-val="' + cb.value + '">' +
                    '<input type="checkbox" ' + checked + ' style="width:16px;height:16px;accent-color:#5E6AD2;cursor:pointer;flex-shrink:0;">' +
                    '<span style="width:4px;height:28px;border-radius:2px;background:' + colore + ';flex-shrink:0;"></span>' +
                    '<div style="flex:1;">' +
                        '<div style="font-size:13px;font-weight:600;color:#EDEDED;">' + name + '</div>' +
                        (benef ? '<div style="font-size:11px;color:#8A8F98;">' + benef + '</div>' : '') +
                    '</div>' +
                '</div>';
    }
    if (!html) {
        html = '<div class="text-center text-secondary small py-5"><i class="bi bi-inbox fs-2 d-block mb-3"></i>Nessun progetto trovato</div>';
    }
    list.innerHTML = html;

    // Click handlers for items
    var items = list.querySelectorAll('.progetti-search-item');
    for (var j = 0; j < items.length; j++) {
        (function(item, cbIdx) {
            item.addEventListener('click', function(e) {
                if (e.target.tagName === 'INPUT') return;
                var chk = item.querySelector('input[type="checkbox"]');
                if (chk) { chk.checked = !chk.checked; }
            });
            var chk = item.querySelector('input[type="checkbox"]');
            if (chk) {
                chk.addEventListener('change', function() {
                    // sync to the original checkbox in the form
                    checkboxes[cbIdx].checked = this.checked;
                    checkboxes[cbIdx].dispatchEvent(new Event('change', { bubbles: true }));
                });
            }
        })(items[j], j);
    }
}

function syncProgettiSelections(form, container, list) {
    var checkboxes = container.querySelectorAll('.progetto-checkbox');
    var searchItems = list.querySelectorAll('.progetti-search-item');
    for (var i = 0; i < searchItems.length; i++) {
        var chk = searchItems[i].querySelector('input[type="checkbox"]');
        if (chk && checkboxes[i]) {
            checkboxes[i].checked = chk.checked;
            checkboxes[i].dispatchEvent(new Event('change', { bubbles: true }));
        }
    }
    updateProgettiBadges(form);
}

function updateProgettiBadges(form) {
    var container = form.querySelector('#progettiContainer');
    var badges = form.querySelector('#progettiSelezionati');
    if (!container || !badges) return;
    var checkboxes = container.querySelectorAll('.progetto-checkbox:checked');
    badges.innerHTML = '';
    for (var i = 0; i < checkboxes.length; i++) {
        var cb = checkboxes[i];
        var label = cb.closest('.progetto-check-item');
        if (!label) continue;
        var nameEl = label.querySelector('.progetto-label');
        var name = nameEl ? nameEl.textContent.trim() : '#' + cb.value;
        var colore = '#10b981';
        if (nameEl) {
            var match = nameEl.innerHTML.match(/border-left:\s*3px\s+solid\s+(#[a-f0-9]+)/i);
            if (match) colore = match[1];
        }
        var badge = document.createElement('span');
        badge.style.cssText = 'display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:6px;font-size:11px;background:rgba(' + hexToRgb(colore) + ',0.12);border:1px solid ' + colore + '33;color:#EDEDED;';
        badge.innerHTML = '<span style="width:6px;height:6px;border-radius:50%;background:' + colore + ';"></span>' + name +
            '<button type="button" class="badge-remove" data-val="' + cb.value + '" style="background:none;border:none;color:#8A8F98;padding:0 2px;font-size:13px;cursor:pointer;line-height:1;margin-left:2px;">&times;</button>';
        badges.appendChild(badge);
    }
    // Remove handlers
    badges.querySelectorAll('.badge-remove').forEach(function(btn) {
        btn.addEventListener('click', function() {
            var val = this.getAttribute('data-val');
            var cbx = container.querySelector('.progetto-checkbox[value="' + val + '"]');
            if (cbx) { cbx.checked = false; cbx.dispatchEvent(new Event('change', { bubbles: true })); }
            this.closest('span').remove();
            if (window.aggiornaValoriOpzioni) window.aggiornaValoriOpzioni();
        });
    });
}

function hexToRgb(hex) {
    if (!hex || hex.length < 7) return '0,0,0';
    var r = parseInt(hex.slice(1,3), 16);
    var g = parseInt(hex.slice(3,5), 16);
    var b = parseInt(hex.slice(5,7), 16);
    return r + ',' + g + ',' + b;
}

// ===== RIEPILOGO OPZIONI INTEGRATION =====
function integrateOpzioniRiepilogo(form) {
    var summaryEl = form.querySelector('#opzioniSummary');
    if (!summaryEl) return;
    var riepilogoDiv = form.querySelector('#riepilogoOpzioni');
    if (!riepilogoDiv) return;
    summaryEl.style.display = 'block';
    summaryEl.style.border = 'none';
    summaryEl.style.background = 'none';
    summaryEl.style.padding = '0';
    summaryEl.style.margin = '0';
    summaryEl.style.marginTop = '4px';
}

// ===== DEFAULT SELECTIONS =====
function setDefaultSelections(form) {
    // Ente bilaterale: cerca [F] FONDOCOLF o F, fallback primo
    var enteSelect = form.querySelector('select[name="ente_bilaterale"]');
    if (enteSelect && !enteSelect.value) {
        var found = false;
        for (var i = 0; i < enteSelect.options.length; i++) {
            var txt = enteSelect.options[i].textContent || enteSelect.options[i].innerText;
            if (txt.indexOf('FONDOCOLF') !== -1 || txt.indexOf('[F]') !== -1 || txt.indexOf('F2') !== -1) {
                enteSelect.value = enteSelect.options[i].value;
                found = true;
                break;
            }
        }
        if (!found && enteSelect.options.length > 0 && enteSelect.options[0].value) {
            enteSelect.value = enteSelect.options[0].value;
        }
        enteSelect.dispatchEvent(new Event('change', { bubbles: true }));
    }

    // Parametri minimi: cerca livello CS, fallback primo
    var paramSelect = form.querySelector('select[name="parametri_minimi"]');
    if (paramSelect && !paramSelect.value) {
        var found = false;
        for (var i = 0; i < paramSelect.options.length; i++) {
            var txt = paramSelect.options[i].textContent || paramSelect.options[i].innerText;
            if (txt.indexOf('CS') !== -1 || txt.indexOf('Cs') !== -1) {
                paramSelect.value = paramSelect.options[i].value;
                found = true;
                break;
            }
        }
        if (!found && paramSelect.options.length > 0 && paramSelect.options[0].value) {
            paramSelect.value = paramSelect.options[0].value;
        }
        paramSelect.dispatchEvent(new Event('change', { bubbles: true }));
    }

    // Trigger riepilogo update
    if (window.aggiornaValoriOpzioni) setTimeout(function() { window.aggiornaValoriOpzioni(); }, 100);
}

// ===== HOOK INTO EXISTING RIE PULLDOWN UPDATES =====
// Patch aggiornaValoriOpzioni to also update progetti badges after it runs
var _origAggiorna = window.aggiornaValoriOpzioni;
if (typeof _origAggiorna === 'function') {
    window.aggiornaValoriOpzioni = function() {
        _origAggiorna.apply(this, arguments);
        var form = document.querySelector('#dynamicForm');
        if (form) updateProgettiBadges(form);
    };
}
