var CSRF_TOKEN = window.CU_CONFIG ? window.CU_CONFIG.csrfToken : '';
var _cuContratti = [];
var _cuIdx = -1;
var _cuDati = null;
var MESI_IT = ['','Gennaio','Febbraio','Marzo','Aprile','Maggio','Giugno','Luglio','Agosto','Settembre','Ottobre','Novembre','Dicembre'];

document.addEventListener('DOMContentLoaded', function(){
    var sel = document.getElementById('selContratto');
    for (var i = 0; i < sel.options.length; i++) {
        _cuContratti.push({pk: parseInt(sel.options[i].value), text: sel.options[i].text});
    }
    if (_cuContratti.length > 0) { _cuIdx = 0; aggiornaCounter(); caricaDatiCu(); aggiornaStepper(1); aggiornaBadgeContratto(); }
    sel.addEventListener('change', function(){ _cuIdx = this.selectedIndex; aggiornaCounter(); caricaDatiCu(); aggiornaStepper(1); aggiornaBadgeContratto(); });
    document.getElementById('selAnno').addEventListener('change', caricaDatiCu);
    document.getElementById('selAnno').addEventListener('input', caricaDatiCu);
    // Carica modelli email
    fetch('/ajax/modelli-email/').then(function(r){ return r.json(); }).then(function(lista){
        var selMod = document.getElementById('cuModelloEmail');
        lista.forEach(function(m){
            var opt = document.createElement('option');
            opt.value = m.pk; opt.textContent = m.codice + (m.oggetto_titolo ? ' \u2014 ' + m.oggetto_titolo : '');
            selMod.appendChild(opt);
        });
    }).catch(function(){});
});

function navigaContratto(delta) {
    var nuovo = _cuIdx + delta;
    if (nuovo < 0 || nuovo >= _cuContratti.length) return;
    _cuIdx = nuovo;
    document.getElementById('selContratto').selectedIndex = nuovo;
    aggiornaCounter();
    caricaDatiCu();
}

function aggiornaCounter() {
    var tot = _cuContratti.length;
    document.getElementById('contrattoCounter').textContent = (_cuIdx + 1) + ' / ' + tot;
}

function setMode(m) {
    document.querySelectorAll('.btn-tab[data-mode]').forEach(function(b){ b.classList.remove('active'); });
    var btn = document.querySelector('.btn-tab[data-mode="' + m + '"]');
    if (btn && !btn.disabled) btn.classList.add('active');
    caricaDatiCu();
}

function caricaDatiCu() {
    if (_cuIdx < 0 || _cuIdx >= _cuContratti.length) return;
    var pk = _cuContratti[_cuIdx].pk;
    var anno = document.getElementById('selAnno').value || new Date().getFullYear();
    document.getElementById('riepilogoContainer').style.display = 'none';
    document.getElementById('verificaCuContainer').style.display = 'none';
    aggiornaStepper(2);
    var mode = document.querySelector('.btn-tab.active')?.getAttribute('data-mode') || '1';
    fetch('/ajax/carica-dati-cu/?contratto_pk=' + pk + '&anno=' + anno + '&mode=' + mode)
    .then(function(r){ return r.json(); })
    .then(function(d){
        if (!d.success) { mostraToast(d.error || 'Errore caricamento CU', false); return; }
        _cuDati = d;
        mostraRiepilogo(d);
        document.getElementById('riepilogoContainer').style.display = 'block';
    })
    .catch(function(){ mostraToast('Errore di rete', false); });
}

function mostraRiepilogo(d) {
    var body = document.getElementById('riepilogoBody');
    var html = '<div class="row g-3">';
    html += '<div class="col-md-6"><span style="color:#8A8F98;font-size:11px;">Datore</span><br><b>' + d.nome_datore + '</b></div>';
    html += '<div class="col-md-6"><span style="color:#8A8F98;font-size:11px;">Lavoratore</span><br><b>' + d.nome_lavoratore + '</b></div>';
    html += '<div class="col-md-4"><span style="color:#8A8F98;font-size:11px;">CF Datore</span><br>' + d.cf_datore + '</div>';
    html += '<div class="col-md-4"><span style="color:#8A8F98;font-size:11px;">CF Lavoratore</span><br>' + d.cf_lavoratore + '</div>';
    html += '<div class="col-md-4"><span style="color:#8A8F98;font-size:11px;">Codice Rapporto INPS</span><br>' + (d.codice_rapporto_inps || '-') + '</div>';
    html += '<div class="col-12" style="margin-top:8px;padding-top:8px;border-top:1px solid #27282D;"></div>';
    html += '<div class="col-md-3"><span style="color:#8A8F98;font-size:11px;">Data assunzione</span><br><b>' + (d.data_inizio || '-') + '</b></div>';
    html += '<div class="col-md-3"><span style="color:#8A8F98;font-size:11px;">Data fine</span><br><b id="riepilogoDataFine">' + (d.data_fine || 'In corso') + '</b><span id="riepilogoDataFineLabel" style="font-size:10px;color:#f59e0b;margin-left:4px;">' + (d.data_fine_custom ? '(personalizzata)' : '') + '</span></div>';
    html += '<div class="col-md-3"><span style="color:#8A8F98;font-size:11px;">Giorni</span><br><b id="riepilogoGiorni">' + (d.giorni || '-') + '</b></div>';
    html += '</div>';
    body.innerHTML = html;

    var missing = d.dettaglio_mensile.filter(function(m){ return !m.presente; });
    var avvisoDiv = document.getElementById('avvisoMesiMancanti');
    if (missing.length > 0 && d.mode === 'auto') {
        avvisoDiv.style.display = 'block';
        document.getElementById('avvisoMesiMancantiTesto').textContent = 'Attenzione: ' + missing.length + ' mese/i senza busta paga (' + missing.map(function(m){ return MESI_IT[m.mese]; }).join(', ') + ').';
    } else {
        avvisoDiv.style.display = 'none';
    }

    aggiornaStatBoxes(d);
    var dm = document.getElementById('dettaglioMensileContainer');
    var rs = document.getElementById('riepilogoSomme');

    if (d.mode === 'semiauto') renderSemiAutoView(d, dm, rs);
    else if (d.mode === 'manuale') {
        renderManualeView(d, dm, rs);
        setTimeout(function(){
            anteprimaTestoCu('cuManCaricoFamiliare','cuManCaricoFamiliarePrev');
            anteprimaTestoCu('cuManPresentazioneRedditi','cuManPresentazioneRedditiPrev');
        }, 50);
    }
    else renderAutoView(d, dm, rs);
    aggiornaStepper(3);
    aggiornaBadgeContratto();
}

/* ---- Helper data fine custom (live update) ---- */
function _parseDateIt(str) {
    if (!str) return null;
    var p = str.split('/');
    return new Date(parseInt(p[2]), parseInt(p[1]) - 1, parseInt(p[0]));
}
function _formatDateIt(d) {
    return ('0' + d.getDate()).slice(-2) + '/' + ('0' + (d.getMonth() + 1)).slice(-2) + '/' + d.getFullYear();
}
function aggiornaDataFineCustom(inputId) {
    if (!_cuDati) return;
    var d = _cuDati;
    var customVal = document.getElementById(inputId).value;
    var inizio = _parseDateIt(d.data_inizio);
    var anno = d.anno;
    var inizioAnno = new Date(anno, 0, 1);
    var fineAnno = new Date(anno, 11, 31);
    var dataFine;
    if (customVal) {
        var p = customVal.split('-');
        dataFine = new Date(parseInt(p[0]), parseInt(p[1]) - 1, parseInt(p[2]));
    } else {
        dataFine = _parseDateIt(d.data_fine_contratto) || fineAnno;
    }
    var inizioPeriodo = inizio > inizioAnno ? inizio : inizioAnno;
    var finePeriodo = dataFine < fineAnno ? dataFine : fineAnno;
    var diffMs = finePeriodo - inizioPeriodo;
    var giorni = Math.max(0, Math.min(Math.floor(diffMs / (1000 * 60 * 60 * 24)) + 1, 365));
    document.getElementById('riepilogoDataFine').textContent = dataFine ? _formatDateIt(dataFine) : 'In corso';
    document.getElementById('riepilogoDataFineLabel').textContent = customVal ? '(personalizzata)' : '';
    document.getElementById('riepilogoGiorni').textContent = giorni;
}

function aggiornaStatBoxes(d) {
    var stat = document.getElementById('statBoxes');
    stat.innerHTML = '';
    var boxes = [
        {label:'Mesi lavorati', value:d.num_mesi + ' / 12'},
        {label:'Lordo annuo', value:'\u20ac ' + d.totale_lordo.toFixed(2)},
        {label:'Contributi', value:'\u20ac ' + d.totale_contributi.toFixed(2)},
        {label:'Netto', value:'\u20ac ' + d.totale_netto.toFixed(2)},
        {label:'Imponibile fiscale', value:'\u20ac ' + d.imponibile_fiscale.toFixed(2)},
        {label:'TFR', value:'\u20ac ' + d.totale_tfr.toFixed(2)},
    ];
    boxes.forEach(function(b){
        stat.innerHTML += '<div class="col-md-2 col-6"><div class="cu-stat-box"><div class="value">' + b.value + '</div><div class="label">' + b.label + '</div></div></div>';
    });
}

/* ---- Verifica quadratura ---- */
function verificaQuadratura() {
    if (!_cuDati) { mostraToast('Nessun dato caricato.', false); return; }
    var d = _cuDati;
    var container = document.getElementById('verificaCuContainer');
    var btn = document.getElementById('btnVerificaCu');
    container.style.display = 'block';
    container.innerHTML = '<div style="text-align:center;padding:16px;"><div class="spinner-border spinner-border-sm" style="color:#f59e0b;" role="status"></div> Confronto in corso...</div>';
    fetch('/ajax/verifica-cu/?contratto_pk=' + d.contratto_pk + '&anno=' + d.anno)
    .then(function(r){ return r.json(); })
    .then(function(data){
        if (!data.success) { container.innerHTML = '<div style="color:#f87171;">' + (data.error || 'Errore') + '</div>'; return; }
        var voci = [
            {label:'Reddito lordo', buste:data.buste_lordo, cu:d.totale_lordo},
            {label:'Contributi INPS', buste:data.buste_contributi_inps, cu:d.totale_contributi_inps},
            {label:'Contributi Cassa', buste:data.buste_contributi_cassa, cu:d.totale_contributi_cassa},
            {label:'Totale contributi', buste:data.buste_contributi, cu:d.totale_contributi},
            {label:'Netto corrisposto', buste:data.buste_netto, cu:d.totale_netto},
            {label:'TFR accantonato', buste:data.buste_tfr, cu:d.totale_tfr},
            {label:'Imponibile fiscale', buste:data.buste_imponibile, cu:d.imponibile_fiscale},
        ];
        var html = '<div style="background:rgba(255,255,255,0.02);border:1px solid #27282D;border-radius:10px;overflow:hidden;">';
        html += '<table style="width:100%;border-collapse:collapse;font-size:12px;">';
        html += '<thead><tr style="border-bottom:1px solid #27282D;background:rgba(255,255,255,0.04);">';
        html += '<th style="padding:8px 12px;text-align:left;color:#8A8F98;font-size:10px;text-transform:uppercase;">Voce</th>';
        html += '<th style="padding:8px 12px;text-align:right;color:#8A8F98;font-size:10px;text-transform:uppercase;">Buste paga</th>';
        html += '<th style="padding:8px 12px;text-align:right;color:#8A8F98;font-size:10px;text-transform:uppercase;">CU</th>';
        html += '<th style="padding:8px 12px;text-align:right;color:#8A8F98;font-size:10px;text-transform:uppercase;">Differenza</th>';
        html += '<th style="padding:8px 12px;text-align:center;color:#8A8F98;font-size:10px;text-transform:uppercase;">%</th>';
        html += '<th style="padding:8px 12px;text-align:center;color:#8A8F98;font-size:10px;text-transform:uppercase;"></th>';
        html += '</tr></thead><tbody>';
        var ok = true;
        voci.forEach(function(v){
            var diff = v.cu - v.buste;
            var perc = v.buste !== 0 ? (diff / v.buste * 100) : 0;
            var absPerc = Math.abs(perc);
            var status = absPerc < 1 ? 'ok' : (absPerc < 5 ? 'warn' : 'err');
            var icon = status === 'ok' ? '<i class="bi bi-check-circle-fill" style="color:#34d399;"></i>' : (status === 'warn' ? '<i class="bi bi-exclamation-triangle-fill" style="color:#f59e0b;"></i>' : '<i class="bi bi-x-circle-fill" style="color:#f87171;"></i>');
            if (status !== 'ok') ok = false;
            html += '<tr style="border-bottom:1px solid rgba(39,40,45,0.4);">';
            html += '<td style="padding:6px 12px;color:#EDEDED;">' + v.label + '</td>';
            html += '<td style="padding:6px 12px;text-align:right;color:#ccc;">\u20ac ' + v.buste.toFixed(2) + '</td>';
            html += '<td style="padding:6px 12px;text-align:right;color:#ccc;">\u20ac ' + v.cu.toFixed(2) + '</td>';
            html += '<td style="padding:6px 12px;text-align:right;color:' + (status === 'err' ? '#f87171' : (status === 'warn' ? '#f59e0b' : '#34d399')) + ';">' + (diff >= 0 ? '+' : '') + '\u20ac ' + diff.toFixed(2) + '</td>';
            html += '<td style="padding:6px 12px;text-align:right;color:' + (status === 'err' ? '#f87171' : (status === 'warn' ? '#f59e0b' : '#34d399')) + ';">' + (perc >= 0 ? '+' : '') + perc.toFixed(2) + '%</td>';
            html += '<td style="padding:6px 12px;text-align:center;">' + icon + '</td>';
            html += '</tr>';
        });
        html += '</tbody></table></div>';
        html += '<div style="margin-top:8px;font-size:12px;text-align:center;color:' + (ok ? '#34d399' : '#f59e0b') + ';">';
        html += ok ? '<i class="bi bi-check-circle"></i> Quadratura perfetta (nessuno scostamento superiore all\'1%)' : '<i class="bi bi-exclamation-triangle"></i> Attenzione: alcuni valori si discostano dalle buste paga';
        html += '</div>';
        container.innerHTML = html;
    })
    .catch(function(){ container.innerHTML = '<div style="color:#f87171;">Errore di rete.</div>'; });
}

/* ---- Stepper ---- */
function aggiornaStepper(step) {
    document.querySelectorAll('.stepper-step').forEach(function(el, idx){
        el.classList.remove('active', 'completed');
        if (idx + 1 < step) el.classList.add('completed');
        else if (idx + 1 === step) el.classList.add('active');
    });
}

/* ---- Badge contratto corrente ---- */
function aggiornaBadgeContratto() {
    if (_cuIdx < 0 || _cuIdx >= _cuContratti.length) return;
    var badge = document.getElementById('badgeContrattoCorrente');
    var c = _cuContratti[_cuIdx];
    badge.textContent = (c.pk) + ' \u2014 ' + c.text;
    badge.style.display = 'inline-block';
}

function renderAutoView(d, dm, rs) {
    var dmHtml = '<div class="d-flex flex-wrap gap-2">';
    d.dettaglio_mensile.forEach(function(m){
        var cls = m.presente ? 'mese-presente' : 'mese-assente';
        dmHtml += '<div class="' + cls + '" style="text-align:center;min-width:65px;padding:6px 4px;border:1px solid ' + (m.presente ? 'rgba(52,211,153,0.3)' : '#27282D') + ';border-radius:6px;">';
        dmHtml += '<div style="font-size:10px;color:#8A8F98;">' + MESI_IT[m.mese].substring(0,3) + '</div>';
        dmHtml += '<div style="font-size:12px;font-weight:600;">\u20ac ' + m.lordo.toFixed(0) + '</div></div>';
    });
    dmHtml += '</div>';
    dm.innerHTML = dmHtml;
    rs.innerHTML = '<div class="row g-2">';
    var righe = [
        {label:'Reddito lordo complessivo', value:d.totale_lordo, bold:true},
        {label:'Contributi INPS a carico lavoratore', value:d.totale_contributi_inps, bold:false},
        {label:'Contributi Cassa/Ente bilaterale', value:d.totale_contributi_cassa, bold:false},
        {label:'', value:'', sep:true},
        {label:'Imponibile fiscale', value:d.imponibile_fiscale, bold:true},
        {label:'Contributi totali versati', value:d.totale_contributi, bold:false},
        {label:'', value:'', sep:true},
        {label:'Netto corrisposto', value:d.totale_netto, bold:true},
        {label:'TFR accantonato', value:d.totale_tfr, bold:false},
    ];
    if (d.totale_convivenza > 0) righe.push({label:'Indennit\u00e0 di convivenza', value:d.totale_convivenza, bold:false});
    righe.forEach(function(r){
        if (r.sep) { rs.innerHTML += '<div class="col-12" style="height:4px;"></div>'; return; }
        rs.innerHTML += '<div class="col-6" style="color:#8A8F98;font-size:12px;">' + r.label + '</div>';
        rs.innerHTML += '<div class="col-6" style="text-align:right;font-size:13px;' + (r.bold?'font-weight:700;color:#EDEDED;':'color:#cccccc;') + '">\u20ac ' + r.value.toFixed(2) + '</div>';
    });
    rs.innerHTML += '</div>';
}

/* ---- Semi-Automatica: finestra draggabile ---- */
function renderSemiAutoView(d, dm, rs) {
    dm.innerHTML = '<div style="padding:12px 0;text-align:center;">' +
        '<button class="btn" onclick="apriSemiAuto()" style="background:#5E6AD2;color:white;border:none;border-radius:8px;padding:10px 24px;font-size:13px;font-weight:600;">' +
        '<i class="bi bi-pencil-square me-1"></i> Modifica mensilit\u00e0</button>' +
        '<div style="color:#8A8F98;font-size:11px;margin-top:6px;">Clicca per modificare i lordi mensili nella finestra interattiva</div></div>';
    rs.innerHTML = '<div class="row g-2">';
    var righe = [
        {label:'Reddito lordo complessivo', value:d.totale_lordo, bold:true},
        {label:'Contributi INPS a carico lavoratore', value:d.totale_contributi_inps, bold:false},
        {label:'Contributi Cassa/Ente bilaterale', value:d.totale_contributi_cassa, bold:false},
        {label:'', value:'', sep:true},
        {label:'Imponibile fiscale', value:d.imponibile_fiscale, bold:true},
        {label:'Contributi totali versati', value:d.totale_contributi, bold:false},
        {label:'', value:'', sep:true},
        {label:'Netto corrisposto', value:d.totale_netto, bold:true},
        {label:'TFR accantonato', value:d.totale_tfr, bold:false},
    ];
    if (d.totale_convivenza > 0) righe.push({label:'Indennit\u00e0 di convivenza', value:d.totale_convivenza, bold:false});
    righe.forEach(function(r){
        if (r.sep) { rs.innerHTML += '<div class="col-12" style="height:4px;"></div>'; return; }
        rs.innerHTML += '<div class="col-6" style="color:#8A8F98;font-size:12px;">' + r.label + '</div>';
        rs.innerHTML += '<div class="col-6" style="text-align:right;font-size:13px;' + (r.bold?'font-weight:700;color:#EDEDED;':'color:#cccccc;') + '">\u20ac ' + r.value.toFixed(2) + '</div>';
    });
    rs.innerHTML += '</div>';
    _saDati = d;
}

var _saDati = null;
var _saRifRatios = null;

function apriSemiAuto() {
    var d = _cuDati;
    if (!d) return;
    var nomiMesi = ['','Gennaio','Febbraio','Marzo','Aprile','Maggio','Giugno','Luglio','Agosto','Settembre','Ottobre','Novembre','Dicembre','13\u00aa mens.'];

    // Build grid: 12 mesi + 13°
    var mesi = (d.dettaglio_mensile || []).map(function(m){ return {
        mese: m.mese, presente: m.presente != null ? m.presente : true,
        lordo: m.lordo || 0, contributi_inps: m.contributi_inps || 0,
        contributi_cassa: m.contributi_cassa || 0, netto: m.netto || 0, tfr: m.tfr || 0
    }; });
    // Add 13th if not present
    if (!mesi.some(function(m){ return m.mese === 13; })) {
        mesi.push({mese:13, presente:true, lordo:0, contributi_inps:0, contributi_cassa:0, netto:0, tfr:0});
    }

    // Store reference ratios from existing data
    _saRifRatios = {inps: d.ratio_inps || 0, cassa: d.ratio_cassa || 0, tfr: d.ratio_tfr || 0};

    document.getElementById('semiautoTitle').textContent = d.nome_lavoratore + ' - ' + d.anno;
    var tbody = document.getElementById('semiautoGridBody');
    tbody.innerHTML = '';
    mesi.forEach(function(r, idx){
        var tr = document.createElement('tr');
        tr.setAttribute('data-mese', r.mese);
        var is13 = r.mese === 13;
        tr.style.borderBottom = '1px solid rgba(39,40,45,0.4)';
        tr.style.background = is13 ? 'rgba(94,106,210,0.06)' : (idx % 2 === 0 ? 'rgba(255,255,255,0.01)' : '');
        if (is13) tr.style.borderTop = '2px solid #5E6AD2';

        var tdMese = document.createElement('td');
        tdMese.style.padding = '5px 8px';
        tdMese.style.color = is13 ? '#5E6AD2' : '#EDEDED';
        tdMese.style.fontWeight = is13 ? '700' : '400';
        tdMese.textContent = nomiMesi[r.mese];

        var tdPres = document.createElement('td');
        tdPres.style.padding = '5px 8px';
        tdPres.style.textAlign = 'center';
        var cb = document.createElement('input');
        cb.type = 'checkbox';
        cb.className = 'sa-cb';
        cb.checked = r.presente;
        cb.style.accentColor = '#34d399';
        cb.style.cursor = 'pointer';
        tdPres.appendChild(cb);

        var tdLordo = document.createElement('td');
        tdLordo.style.padding = '3px 6px';
        var inpLordo = document.createElement('input');
        inpLordo.type = 'number';
        inpLordo.step = '0.01';
        inpLordo.className = 'cu-grid-input sa-lordo';
        inpLordo.value = r.lordo.toFixed(2);
        inpLordo.style.width = '88px';
        tdLordo.appendChild(inpLordo);

        // Calcolo automatico contributi dal lordo
        var ratioInps = _saRifRatios.inps || 0;
        var ratioCassa = _saRifRatios.cassa || 0;
        var ratioTfr = _saRifRatios.tfr || 0;
        var ci = r.lordo * ratioInps;
        var cc = r.lordo * ratioCassa;
        var nt = r.lordo - ci - cc - (r.lordo * ratioTfr);
        var tf = r.lordo * ratioTfr;

        var tdInps = document.createElement('td');
        tdInps.style.padding = '3px 6px';
        var inpInps = document.createElement('input');
        inpInps.type = 'number'; inpInps.step = '0.01';
        inpInps.className = 'cu-grid-input sa-inps';
        inpInps.value = (r.contributi_inps || ci).toFixed(2);
        inpInps.style.width = '78px';
        inpInps.dataset.auto = '1';
        tdInps.appendChild(inpInps);

        var tdCassa = document.createElement('td');
        tdCassa.style.padding = '3px 6px';
        var inpCassa = document.createElement('input');
        inpCassa.type = 'number'; inpCassa.step = '0.01';
        inpCassa.className = 'cu-grid-input sa-cassa';
        inpCassa.value = (r.contributi_cassa || cc).toFixed(2);
        inpCassa.style.width = '78px';
        inpCassa.dataset.auto = '1';
        tdCassa.appendChild(inpCassa);

        var tdNetto = document.createElement('td');
        tdNetto.style.padding = '3px 6px';
        var inpNetto = document.createElement('input');
        inpNetto.type = 'number'; inpNetto.step = '0.01';
        inpNetto.className = 'cu-grid-input sa-netto';
        inpNetto.value = (r.netto || nt).toFixed(2);
        inpNetto.style.width = '88px';
        inpNetto.dataset.auto = '1';
        tdNetto.appendChild(inpNetto);

        var tdTfr = document.createElement('td');
        tdTfr.style.padding = '3px 6px';
        var inpTr = document.createElement('input');
        inpTr.type = 'number'; inpTr.step = '0.01';
        inpTr.className = 'cu-grid-input sa-tfr';
        inpTr.value = (r.tfr || tf).toFixed(2);
        inpTr.style.width = '78px';
        inpTr.dataset.auto = '1';
        tdTfr.appendChild(inpTr);

        tr.appendChild(tdMese); tr.appendChild(tdPres);
        tr.appendChild(tdLordo); tr.appendChild(tdInps);
        tr.appendChild(tdCassa); tr.appendChild(tdNetto); tr.appendChild(tdTfr);
        tbody.appendChild(tr);

        // When lordo changes, auto-calc contributi
        inpLordo.addEventListener('input', function(){
            var ld = parseFloat(this.value) || 0;
            var rInps = _saRifRatios.inps || 0;
            var rCassa = _saRifRatios.cassa || 0;
            var rTfr = _saRifRatios.tfr || 0;
            var row = this.closest('tr');
            row.querySelector('.sa-inps').value = (ld * rInps).toFixed(2);
            row.querySelector('.sa-cassa').value = (ld * rCassa).toFixed(2);
            row.querySelector('.sa-tfr').value = (ld * rTfr).toFixed(2);
            row.querySelector('.sa-netto').value = (ld - ld*rInps - ld*rCassa - ld*rTfr).toFixed(2);
            aggiornaTotaliDraggabile();
        });
        cb.addEventListener('change', aggiornaTotaliDraggabile);
    });

    // Pre-popola data_fine_custom
    var dfc = document.getElementById('saDataFineCustom');
    dfc.value = d.data_fine_custom || '';
    dfc.addEventListener('change', function(){ aggiornaDataFineCustom('saDataFineCustom'); });
    document.getElementById('saCaricoFamiliare').value = d.testo_carico_familiare || '';
    document.getElementById('saPresentazioneRedditi').value = d.testo_presentazione_redditi || '';
    anteprimaTestoCu('saCaricoFamiliare','saCaricoFamiliarePrev');
    anteprimaTestoCu('saPresentazioneRedditi','saPresentazioneRedditiPrev');

    var modal = new bootstrap.Modal(document.getElementById('semiautoModal'));
    modal.show();
    aggiornaTotaliDraggabile();
}

function aggiornaTotaliDraggabile() {
    var tot = {lordo:0, inps:0, cassa:0, netto:0, tfr:0};
    var numMesi = 0;
    document.querySelectorAll('#semiautoGridBody tr').forEach(function(tr){
        var cb = tr.querySelector('.sa-cb');
        if (!cb || !cb.checked) return;
        numMesi++;
        tot.lordo += parseFloat(tr.querySelector('.sa-lordo').value) || 0;
        tot.inps += parseFloat(tr.querySelector('.sa-inps').value) || 0;
        tot.cassa += parseFloat(tr.querySelector('.sa-cassa').value) || 0;
        tot.netto += parseFloat(tr.querySelector('.sa-netto').value) || 0;
        tot.tfr += parseFloat(tr.querySelector('.sa-tfr').value) || 0;
    });

    document.getElementById('saTotLordo').textContent = '\u20ac ' + tot.lordo.toFixed(2);
    document.getElementById('saTotInps').textContent = '\u20ac ' + tot.inps.toFixed(2);
    document.getElementById('saTotCassa').textContent = '\u20ac ' + tot.cassa.toFixed(2);
    document.getElementById('saTotNetto').textContent = '\u20ac ' + tot.netto.toFixed(2);
    document.getElementById('saTotTfr').textContent = '\u20ac ' + tot.tfr.toFixed(2);

    // Update _cuDati for save
    var d = _cuDati;
    if (d) {
        d.num_mesi = Math.min(numMesi, 12);
        d.totale_lordo = tot.lordo;
        d.totale_contributi_inps = tot.inps;
        d.totale_contributi_cassa = tot.cassa;
        d.totale_contributi = tot.inps + tot.cassa;
        d.totale_netto = tot.netto;
        d.totale_tfr = tot.tfr;
        d.imponibile_fiscale = tot.lordo - tot.inps;
        aggiornaStatBoxes(d);
    }
}

function anteprimaTestoCu(textareaId, previewId) {
    var ta = document.getElementById(textareaId);
    var prev = document.getElementById(previewId);
    if (!ta || !prev) return;
    var txt = ta.value;
    if (!txt.trim()) { prev.style.display = 'none'; return; }
    var stripped = txt.replace(/<[^>]*>/g, '').replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"');
    prev.textContent = stripped;
    prev.style.display = 'block';
}

function chiudiSemiAuto() {
    var m = bootstrap.Modal.getInstance(document.getElementById('semiautoModal'));
    if (m) m.hide();
}

function salvaSemiAuto() {
    if (!_cuDati) return;
    var d = _cuDati;
    var mesi = [];
    document.querySelectorAll('#semiautoGridBody tr').forEach(function(tr){
        mesi.push({
            mese: parseInt(tr.getAttribute('data-mese')),
            presente: tr.querySelector('.sa-cb').checked,
            lordo: parseFloat(tr.querySelector('.sa-lordo').value) || 0,
            contributi_inps: parseFloat(tr.querySelector('.sa-inps').value) || 0,
            contributi_cassa: parseFloat(tr.querySelector('.sa-cassa').value) || 0,
            netto: parseFloat(tr.querySelector('.sa-netto').value) || 0,
            tfr: parseFloat(tr.querySelector('.sa-tfr').value) || 0,
        });
    });
    d.dettaglio_mensile = mesi;

    var dataFineCustom = document.getElementById('saDataFineCustom').value;
    var valori = {
        totale_lordo: d.totale_lordo,
        totale_contributi_inps: d.totale_contributi_inps,
        totale_contributi_cassa: d.totale_contributi_cassa,
        totale_contributi: d.totale_contributi,
        totale_netto: d.totale_netto,
        totale_tfr: d.totale_tfr,
        totale_convivenza: d.totale_convivenza || 0,
        imponibile_fiscale: d.imponibile_fiscale,
        dettaglio_mensile: mesi,
        data_fine_custom: dataFineCustom,
        testo_carico_familiare: document.getElementById('saCaricoFamiliare').value,
        testo_presentazione_redditi: document.getElementById('saPresentazioneRedditi').value,
    };
    fetch('/ajax/salva-cu-annuale/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN},
        body: JSON.stringify({contratto_pk: d.contratto_pk, anno: d.anno, modalita: 'SEMI_AUTOMATICA', valori: valori})
    })
    .then(function(r){ return r.json(); })
    .then(function(res){
        if (res.success) {
            if (res.warning) { mostraToast(res.warning_msg, false); }
            else { mostraToast('Dati Semi-Automatici salvati.', true); }
            d.data_fine_custom = dataFineCustom;
            chiudiSemiAuto();
            caricaDatiCu();
        } else {
            mostraToast(res.error || 'Errore salvataggio', false);
        }
    })
    .catch(function(){ mostraToast('Errore di rete', false); });
}

/* ---- Manuale ---- */
function renderManualeView(d, dm, rs) {
    dm.innerHTML = '<div style="color:#8A8F98;font-size:11px;font-style:italic;padding:8px 0;">Inserisci il reddito lordo annuale, il sistema calcola automaticamente contributi, netto e TFR.</div>';

    var ri = d.ratio_inps || 0;
    var rc = d.ratio_cassa || 0;
    var rt = d.ratio_tfr || 0;

    rs.innerHTML = '<div class="row g-3">' +
        '<div class="col-md-6"><label style="font-size:11px;color:#8A8F98;font-weight:600;">Reddito lordo annuale</label>' +
        '<input type="number" step="0.01" id="cuManLordo" class="form-control cu-manuale-input" value="' + d.totale_lordo.toFixed(2) + '"></div>' +
        '<div class="col-md-3"><label style="font-size:11px;color:#8A8F98;font-weight:600;">Contributi INPS <span style="color:#5C5F66;font-weight:400;">(' + (ri*100).toFixed(1) + '%)</span></label>' +
        '<div id="cuManInpsDisplay" style="padding:8px 12px;background:#09090B;border:1px solid #27282D;border-radius:6px;color:#f87171;font-size:13px;">\u20ac ' + d.totale_contributi_inps.toFixed(2) + '</div></div>' +
        '<div class="col-md-3"><label style="font-size:11px;color:#8A8F98;font-weight:600;">Contributi Cassa <span style="color:#5C5F66;font-weight:400;">(' + (rc*100).toFixed(1) + '%)</span></label>' +
        '<div id="cuManCassaDisplay" style="padding:8px 12px;background:#09090B;border:1px solid #27282D;border-radius:6px;color:#fbbf24;font-size:13px;">\u20ac ' + d.totale_contributi_cassa.toFixed(2) + '</div></div>' +
        '<div class="col-md-3"><label style="font-size:11px;color:#8A8F98;font-weight:600;">TFR accantonato <span style="color:#5C5F66;font-weight:400;">(' + (rt*100).toFixed(1) + '%)</span></label>' +
        '<div id="cuManTfrDisplay" style="padding:8px 12px;background:#09090B;border:1px solid #27282D;border-radius:6px;color:#60a5fa;font-size:13px;">\u20ac ' + d.totale_tfr.toFixed(2) + '</div></div>' +
        '<div class="col-md-3"><label style="font-size:11px;color:#8A8F98;font-weight:600;">Imponibile fiscale <span style="color:#5C5F66;font-weight:400;">(lordo \u2212 INPS)</span></label>' +
        '<div id="cuManImponibileDisplay" style="padding:8px 12px;background:#09090B;border:1px solid #27282D;border-radius:6px;color:#EDEDED;font-size:13px;">\u20ac ' + d.imponibile_fiscale.toFixed(2) + '</div></div>' +
        '<div class="col-md-3"><label style="font-size:11px;color:#8A8F98;font-weight:600;">Netto corrisposto</label>' +
        '<div id="cuManNettoDisplay" style="padding:8px 12px;background:#09090B;border:1px solid #27282D;border-radius:6px;color:#34d399;font-size:13px;font-weight:600;">\u20ac ' + d.totale_netto.toFixed(2) + '</div></div>' +
        '<div class="col-md-3"><label style="font-size:11px;color:#8A8F98;font-weight:600;">Indennit\u00e0 di convivenza</label>' +
        '<div id="cuManConvivenzaDisplay" style="padding:8px 12px;background:#09090B;border:1px solid #27282D;border-radius:6px;color:#EDEDED;font-size:13px;">\u20ac ' + d.totale_convivenza.toFixed(2) + '</div></div>' +
        '<div class="col-md-3"><label style="font-size:11px;color:#8A8F98;font-weight:600;">Data fine personalizzata <span style="color:#5C5F66;font-weight:400;">(opzionale)</span></label>' +
        '<input type="date" id="cuManDataFineCustom" class="form-control cu-manuale-input" value="' + (d.data_fine_custom || '') + '"></div>' +
        '</div>' +
        '<div class="row g-3 mt-2"><div class="col-md-6"><label style="font-size:11px;color:#8A8F98;font-weight:600;">Carico familiare</label>' +
        '<textarea id="cuManCaricoFamiliare" class="form-control cu-manuale-input" oninput="anteprimaTestoCu(\'cuManCaricoFamiliare\',\'cuManCaricoFamiliarePrev\')" style="min-height:60px;resize:vertical;">' + (d.testo_carico_familiare || '') + '</textarea>' +
        '<div id="cuManCaricoFamiliarePrev" style="margin-top:4px;padding:8px 10px;background:#131316;border:1px solid #27282D;border-radius:6px;font-size:12px;color:#8A8F98;line-height:1.5;white-space:pre-wrap;display:none;"></div></div>' +
        '<div class="col-md-6"><label style="font-size:11px;color:#8A8F98;font-weight:600;">Presentazione dichiarazione dei redditi</label>' +
        '<textarea id="cuManPresentazioneRedditi" class="form-control cu-manuale-input" oninput="anteprimaTestoCu(\'cuManPresentazioneRedditi\',\'cuManPresentazioneRedditiPrev\')" style="min-height:60px;resize:vertical;">' + (d.testo_presentazione_redditi || '') + '</textarea>' +
        '<div id="cuManPresentazioneRedditiPrev" style="margin-top:4px;padding:8px 10px;background:#131316;border:1px solid #27282D;border-radius:6px;font-size:12px;color:#8A8F98;line-height:1.5;white-space:pre-wrap;display:none;"></div></div></div>' +
        '<div class="col-12 mt-3 text-end"><button class="btn" onclick="salvaManuale()" style="background:#10b981;color:white;border:none;border-radius:8px;padding:10px 24px;font-size:13px;font-weight:600;"><i class="bi bi-save me-1"></i> Salva dati Manuali</button></div>';

    document.getElementById('cuManLordo').addEventListener('input', aggiornaAutoManuale);
    document.getElementById('cuManDataFineCustom').addEventListener('change', function(){ aggiornaDataFineCustom('cuManDataFineCustom'); });
    aggiornaAutoManuale();
}

function aggiornaAutoManuale() {
    var lordo = parseFloat(document.getElementById('cuManLordo').value) || 0;
    var ri = (_cuDati && _cuDati.ratio_inps) || 0;
    var rc = (_cuDati && _cuDati.ratio_cassa) || 0;
    var rt = (_cuDati && _cuDati.ratio_tfr) || 0;
    var inps = lordo * ri;
    var cassa = lordo * rc;
    var tfr = lordo * rt;
    var imponibile = lordo - inps;
    var netto = lordo - inps - cassa - tfr;
    document.getElementById('cuManInpsDisplay').textContent = '\u20ac ' + inps.toFixed(2);
    document.getElementById('cuManCassaDisplay').textContent = '\u20ac ' + cassa.toFixed(2);
    document.getElementById('cuManTfrDisplay').textContent = '\u20ac ' + tfr.toFixed(2);
    document.getElementById('cuManImponibileDisplay').textContent = '\u20ac ' + imponibile.toFixed(2);
    document.getElementById('cuManNettoDisplay').textContent = '\u20ac ' + netto.toFixed(2);
}

function salvaManuale() {
    if (!_cuDati) { mostraToast('Nessun dato caricato.', false); return; }
    var d = _cuDati;
    var lordo = parseFloat(document.getElementById('cuManLordo').value) || 0;
    var ri = d.ratio_inps || 0;
    var rc = d.ratio_cassa || 0;
    var rt = d.ratio_tfr || 0;
    var inps = lordo * ri;
    var cassa = lordo * rc;
    var tfr = lordo * rt;
    var valori = {
        totale_lordo: lordo,
        totale_contributi_inps: inps,
        totale_contributi_cassa: cassa,
        totale_contributi: inps + cassa,
        totale_netto: lordo - inps - cassa - tfr,
        totale_tfr: tfr,
        totale_convivenza: d.totale_convivenza || 0,
        imponibile_fiscale: lordo - inps,
        dettaglio_mensile: [],
        data_fine_custom: document.getElementById('cuManDataFineCustom').value || '',
        testo_carico_familiare: document.getElementById('cuManCaricoFamiliare').value,
        testo_presentazione_redditi: document.getElementById('cuManPresentazioneRedditi').value,
    };
    fetch('/ajax/salva-cu-annuale/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN},
        body: JSON.stringify({contratto_pk: d.contratto_pk, anno: d.anno, modalita: 'MANUALE', valori: valori})
    })
    .then(function(r){ return r.json(); })
    .then(function(res){
        if (res.success) {
            if (res.warning) { mostraToast(res.warning_msg, false); }
            else { mostraToast('Dati Manuali salvati.', true); }
            caricaDatiCu();
        }
        else { mostraToast(res.error || 'Errore salvataggio', false); }
    })
    .catch(function(){ mostraToast('Errore di rete', false); });
}

/* ---- Genera PDF ---- */
function generaCuPdf(salva) {
    if (!_cuDati) { mostraToast('Nessun dato caricato.', false); return; }
    var d = _cuDati;
    var mode = document.querySelector('.btn-tab.active')?.getAttribute('data-mode') || '1';
    var url = '/ajax/genera-cu-pdf/?contratto_pk=' + d.contratto_pk + '&anno=' + d.anno + '&mode=' + mode;
    if (mode === '2') {
        var t1 = document.getElementById('saCaricoFamiliare');
        var t2 = document.getElementById('saPresentazioneRedditi');
        if (t1) url += '&testo_carico_familiare=' + encodeURIComponent(t1.value);
        if (t2) url += '&testo_presentazione_redditi=' + encodeURIComponent(t2.value);
    } else if (mode === '3') {
        var t1 = document.getElementById('cuManCaricoFamiliare');
        var t2 = document.getElementById('cuManPresentazioneRedditi');
        if (t1) url += '&testo_carico_familiare=' + encodeURIComponent(t1.value);
        if (t2) url += '&testo_presentazione_redditi=' + encodeURIComponent(t2.value);
    }
    if (salva) {
        fetch(url + '&salva=1')
        .then(function(r){
            if (r.ok) { mostraToast('PDF salvato nella cartella documenti.', true); }
            else { return r.text().then(function(txt){ mostraToast('Errore: ' + (txt || 'generazione PDF fallita'), false); }); }
        })
        .catch(function(){ mostraToast('Errore di rete', false); });
    } else {
        // Embed PDF directly in iframe (no blob URL — Chrome blocks blob: URLs for PDF in iframe)
        document.getElementById('anteprimaCuFrame').src = url;
        var modal = new bootstrap.Modal(document.getElementById('anteprimaCuModal'));
        modal.show();
    }
}

function apriAnteprimaCuPdf() { generaCuPdf(false); }
function salvaDaAnteprima() {
    var m = bootstrap.Modal.getInstance(document.getElementById('anteprimaCuModal'));
    if (m) m.hide();
    generaCuPdf(true);
}
function inviaDaAnteprima() {
    var m = bootstrap.Modal.getInstance(document.getElementById('anteprimaCuModal'));
    if (m) m.hide();
    inviaCuEmail();
}

/* ---- Invia Email ---- */
function inviaCuEmail() {
    if (!_cuDati) { mostraToast('Nessun dato caricato.', false); return; }
    var d = _cuDati;
    var modelloPk = document.getElementById('cuModelloEmail').value;
    document.getElementById('modaleInvioEmailCuBody').innerHTML =
        '<div class="text-center py-4"><div class="spinner-border" style="color:#5E6AD2;" role="status"></div><p style="color:#8A8F98;font-size:13px;margin-top:10px;">Invio in corso...</p></div>';
    var modal = new bootstrap.Modal(document.getElementById('modaleInvioEmailCu'));
    modal.show();
    var mode = document.querySelector('.btn-tab.active')?.getAttribute('data-mode') || '1';
    var body = {contratto_pk: d.contratto_pk, anno: d.anno, modello_pk: modelloPk || null, mode: mode};
    if (mode === '2') {
        var t1 = document.getElementById('saCaricoFamiliare');
        var t2 = document.getElementById('saPresentazioneRedditi');
        if (t1) body.testo_carico_familiare = t1.value;
        if (t2) body.testo_presentazione_redditi = t2.value;
    } else if (mode === '3') {
        var t1 = document.getElementById('cuManCaricoFamiliare');
        var t2 = document.getElementById('cuManPresentazioneRedditi');
        if (t1) body.testo_carico_familiare = t1.value;
        if (t2) body.testo_presentazione_redditi = t2.value;
    }
    fetch('/ajax/invia-cu-email/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN},
        body: JSON.stringify(body)
    })
    .then(function(r){ return r.text(); })
    .then(function(html){
        document.getElementById('modaleInvioEmailCuBody').innerHTML = html;
    })
    .catch(function(){
        document.getElementById('modaleInvioEmailCuBody').innerHTML =
            '<div class="text-center py-4"><div style="font-size:48px;color:#f87171;margin-bottom:12px;"><i class="bi bi-x-circle-fill"></i></div><h6 style="color:#EDEDED;">Errore di rete</h6></div>';
    });
}

/* ---- Storico invii CU ---- */
function toggleStoricoInviiCU() {
    var section = document.getElementById('storicoInviiCuSection');
    if (!section) return;
    var vis = section.style.display !== 'none';
    section.style.display = vis ? 'none' : 'block';
    if (!vis) caricaStoricoInviiCU();
}
function caricaStoricoInviiCU() {
    var list = document.getElementById('storicoInviiCuList');
    if (!list) return;
    var pk = _cuDati ? _cuDati.contratto_pk : '';
    var annoEl = document.getElementById('annoInput') || document.querySelector('[name=anno]');
    var anno = annoEl ? annoEl.value : new Date().getFullYear();
    if (!pk) { list.innerHTML = '<div style="color:#f59e0b;">Carica i dati CU prima di visualizzare lo storico.</div>'; return; }
    list.innerHTML = '<div style="color:#8A8F98;">Caricamento...</div>';
    fetch('/ajax/log-invii-cu/' + pk + '/' + anno + '/')
        .then(function(r) {
            var ct = r.headers.get('content-type') || '';
            if (ct.indexOf('application/json') === -1) {
                throw new Error('Risposta non valida dal server (verifica URL)');
            }
            return r.json();
        })
        .then(function(d) {
            if (!d.success || !d.items || d.items.length === 0) {
                list.innerHTML = '<div style="color:#666;font-size:11px;">Nessun invio registrato.</div>';
                return;
            }
            var html = '';
            for (var i = 0; i < d.items.length; i++) {
                var l = d.items[i];
                html += '<div style="display:flex;align-items:center;gap:8px;padding:5px 8px;border-bottom:1px solid rgba(255,255,255,0.04);font-size:11px;">';
                html += '<span style="font-weight:600;color:' + (l.esito === 'OK' ? '#34d399' : '#f87171') + ';">' + l.esito + '</span>';
                html += '<span style="color:#EDEDED;">' + l.data_ora + '</span>';
                html += '<span style="color:#8A8F98;">' + l.destinatario + '</span>';
                if (l.errore) html += '<span style="color:#f87171;font-size:10px;margin-left:auto;">' + l.errore.substring(0, 60) + '</span>';
                html += '</div>';
            }
            list.innerHTML = html;
        })
        .catch(function(err) { list.innerHTML = '<div style="color:#f87171;">Errore: ' + err.message + '</div>'; });
}

/* ---- Batch: selezione multipla ---- */
function toggleBatchTable() {
    var body = document.getElementById('batchSectionBody');
    if (!body) return;
    body.style.display = body.style.display === 'none' ? 'block' : 'none';
}
function toggleAllBatch(master) {
    var cbs = document.querySelectorAll('.batch-cb');
    for (var i = 0; i < cbs.length; i++) cbs[i].checked = master.checked;
    aggiornaBatchCount();
}
function aggiornaBatchCount() {
    var cbs = document.querySelectorAll('.batch-cb:checked');
    var n = cbs.length;
    var btnPdf = document.getElementById('btnBatchPdf');
    var btnMail = document.getElementById('btnBatchEmail');
    if (btnPdf) { btnPdf.disabled = n === 0; btnPdf.style.opacity = n === 0 ? '0.4' : '1'; btnPdf.innerHTML = '<i class="bi bi-files me-1"></i> Genera PDF selezionati (' + n + ')'; }
    if (btnMail) { btnMail.disabled = n === 0; btnMail.style.opacity = n === 0 ? '0.4' : '1'; btnMail.innerHTML = '<i class="bi bi-envelope-paper me-1"></i> Invia email selezionati (' + n + ')'; }
}
function getSelezionati() {
    var cbs = document.querySelectorAll('.batch-cb:checked');
    var pks = [];
    for (var i = 0; i < cbs.length; i++) pks.push(parseInt(cbs[i].value));
    return pks;
}
var _batchUltimiPks = [];
var _batchUltimoAnno = '';
function generaBatchPdf() {
    var pks = getSelezionati();
    if (pks.length === 0) { mostraToast('Seleziona almeno un contratto.', false); return; }
    _batchUltimiPks = pks;
    var anno = document.getElementById('selAnno').value || new Date().getFullYear();
    _batchUltimoAnno = anno;
    var bodyEl = document.getElementById('modaleBatchPdfBody');
    bodyEl.innerHTML = '<div class="text-center py-4"><div class="spinner-border" style="color:#5E6AD2;" role="status"></div><p style="color:#8A8F98;font-size:13px;margin-top:10px;">Generazione in corso (' + pks.length + ' contratti)...</p></div>';
    var modal = new bootstrap.Modal(document.getElementById('modaleBatchPdf'));
    modal.show();
    var mode = document.querySelector('.btn-tab.active')?.getAttribute('data-mode') || '1';
    var body = { contratti: pks, anno: anno, mode: mode };
    if (mode === '2') {
        var t1 = document.getElementById('saCaricoFamiliare');
        var t2 = document.getElementById('saPresentazioneRedditi');
        if (t1) body.testo_carico_familiare = t1.value;
        if (t2) body.testo_presentazione_redditi = t2.value;
    } else if (mode === '3') {
        var t1 = document.getElementById('cuManCaricoFamiliare');
        var t2 = document.getElementById('cuManPresentazioneRedditi');
        if (t1) body.testo_carico_familiare = t1.value;
        if (t2) body.testo_presentazione_redditi = t2.value;
    }
    fetch('/ajax/genera-cu-pdf-batch/', {
        method: 'POST',
        headers: { 'X-CSRFToken': CSRF_TOKEN, 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    })
    .then(function(r){ return r.json(); })
    .then(function(d){
        if (!d.success) { bodyEl.innerHTML = '<div class="text-center py-4"><div style="font-size:48px;color:#f87171;margin-bottom:12px;"><i class="bi bi-x-circle-fill"></i></div><h6 style="color:#EDEDED;">' + (d.error || 'Errore') + '</h6></div>'; return; }
        var html = '<div style="font-size:14px;font-weight:700;color:#EDEDED;margin-bottom:12px;"><i class="bi bi-check-circle" style="color:#34d399;"></i> Completato: ' + d.ok + ' / ' + d.totale + ' PDF generati</div>';
        html += '<div style="max-height:300px;overflow-y:auto;">';
        for (var i = 0; i < d.esiti.length; i++) {
            var e = d.esiti[i];
            html += '<div style="display:flex;align-items:center;gap:6px;padding:6px 8px;border-bottom:1px solid rgba(39,40,45,0.5);font-size:12px;">';
            if (e.ok) {
                html += '<span style="color:#34d399;"><i class="bi bi-check-circle-fill"></i></span>';
                html += '<span style="color:#EDEDED;">' + e.datore + ' \u2192 ' + e.lavoratore + '</span>';
                html += '<a href="/ajax/genera-cu-pdf/?contratto_pk=' + e.pk + '&anno=' + anno + '" target="_blank" style="margin-left:auto;background:rgba(94,106,210,0.1);border:1px solid rgba(94,106,210,0.2);border-radius:6px;color:#5E6AD2;padding:2px 10px;font-size:11px;font-weight:600;text-decoration:none;white-space:nowrap;"><i class="bi bi-file-pdf"></i> Apri</a>';
            } else {
                html += '<span style="color:#f87171;"><i class="bi bi-x-circle-fill"></i></span>';
                html += '<span style="color:#EDEDED;">Contratto #' + e.pk + '</span>';
                html += '<span style="color:#f87171;margin-left:auto;font-size:11px;">' + (e.errore || '') + '</span>';
            }
            html += '</div>';
        }
        html += '</div>';
        html += '<div style="display:flex;gap:8px;margin-top:12px;padding-top:12px;border-top:1px solid #27282D;">';
        if (d.ok > 0) {
            html += '<button onclick="window.location.href=\'/ajax/genera-cu-pdf/?contratto_pk=' + _batchUltimiPks[0] + '&anno=' + anno + '\'" style="background:rgba(94,106,210,0.1);color:#5E6AD2;border:1px solid rgba(94,106,210,0.2);border-radius:8px;padding:8px 16px;font-size:12px;font-weight:600;cursor:pointer;"><i class="bi bi-folder-open me-1"></i> Apri primo PDF</button>';
            html += '<button onclick="var m=bootstrap.Modal.getInstance(document.getElementById(\'modaleBatchPdf\'));if(m)m.hide();inviaMassivoCuConPks(' + JSON.stringify(_batchUltimiPks) + ',\'' + anno + '\')" style="background:#2563eb;color:white;border:none;border-radius:8px;padding:8px 16px;font-size:12px;font-weight:600;cursor:pointer;"><i class="bi bi-envelope me-1"></i> Invia via email (' + d.ok + ')</button>';
        }
        html += '</div>';
        bodyEl.innerHTML = html;
    })
    .catch(function(){ bodyEl.innerHTML = '<div class="text-center py-4"><div style="font-size:48px;color:#f87171;margin-bottom:12px;"><i class="bi bi-x-circle-fill"></i></div><h6 style="color:#EDEDED;">Errore di rete</h6></div>'; });
}
function inviaMassivoCu() {
    inviaMassivoCuConPks(null, null);
}
function inviaMassivoCuConPks(pks, anno) {
    if (!pks) pks = getSelezionati();
    if (!anno) anno = document.getElementById('selAnno').value || new Date().getFullYear();
    if (pks.length === 0) { mostraToast('Seleziona almeno un contratto.', false); return; }
    var modelloPk = document.getElementById('cuModelloEmail').value || null;
    var bodyEl = document.getElementById('modaleMassivoEmailBody');
    bodyEl.innerHTML = '<div class="text-center py-4"><div class="spinner-border" style="color:#2563eb;" role="status"></div><p style="color:#8A8F98;font-size:13px;margin-top:10px;">Invio in corso (' + pks.length + ' contratti)...</p></div>';
    var modal = new bootstrap.Modal(document.getElementById('modaleMassivoEmail'));
    modal.show();
    var mode = document.querySelector('.btn-tab.active')?.getAttribute('data-mode') || '1';
    var body = { contratti: pks, anno: anno, modello_pk: modelloPk, mode: mode };
    if (mode === '2') {
        var t1 = document.getElementById('saCaricoFamiliare');
        var t2 = document.getElementById('saPresentazioneRedditi');
        if (t1) body.testo_carico_familiare = t1.value;
        if (t2) body.testo_presentazione_redditi = t2.value;
    } else if (mode === '3') {
        var t1 = document.getElementById('cuManCaricoFamiliare');
        var t2 = document.getElementById('cuManPresentazioneRedditi');
        if (t1) body.testo_carico_familiare = t1.value;
        if (t2) body.testo_presentazione_redditi = t2.value;
    }
    fetch('/ajax/invia-cu-massivo/', {
        method: 'POST',
        headers: { 'X-CSRFToken': CSRF_TOKEN, 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    })
    .then(function(r){ return r.json(); })
    .then(function(d){
        if (!d.success) { bodyEl.innerHTML = '<div class="text-center py-4"><div style="font-size:48px;color:#f87171;margin-bottom:12px;"><i class="bi bi-x-circle-fill"></i></div><h6 style="color:#EDEDED;">' + (d.error || 'Errore') + '</h6></div>'; return; }
        var r = d.riepilogo;
        var html = '<div style="font-size:14px;font-weight:700;color:#EDEDED;margin-bottom:12px;"><i class="bi bi-check-circle" style="color:#34d399;"></i> Completato: ' + r.ok + ' inviati, ' + r.errore + ' errori</div>';
        if (r.dettagli && r.dettagli.length > 0) {
            html += '<div style="max-height:300px;overflow-y:auto;">';
            for (var i = 0; i < r.dettagli.length; i++) {
                var e = r.dettagli[i];
                html += '<div style="display:flex;align-items:center;gap:8px;padding:6px 8px;border-bottom:1px solid rgba(39,40,45,0.5);font-size:12px;">';
                if (e.ok) {
                    html += '<span style="color:#34d399;"><i class="bi bi-check-circle-fill"></i></span>';
                    html += '<span style="color:#EDEDED;">' + (e.lavoratore || '#' + e.pk) + '</span><span style="color:#34d399;margin-left:auto;">OK</span>';
                } else {
                    html += '<span style="color:#f87171;"><i class="bi bi-x-circle-fill"></i></span>';
                    html += '<span style="color:#EDEDED;">' + (e.lavoratore || '#' + e.pk) + '</span>';
                    html += '<span style="color:#f87171;margin-left:auto;font-size:11px;">' + (e.errore || '') + '</span>';
                }
                html += '</div>';
            }
            html += '</div>';
        }
        bodyEl.innerHTML = html;
    })
    .catch(function(){ bodyEl.innerHTML = '<div class="text-center py-4"><div style="font-size:48px;color:#f87171;margin-bottom:12px;"><i class="bi bi-x-circle-fill"></i></div><h6 style="color:#EDEDED;">Errore di rete</h6></div>'; });
}
