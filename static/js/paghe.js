// PAGHE.JS — Action Panel, utility funzioni
// ============================================

window.closeActionPanel = function() {
    document.getElementById('actionPanelOverlay').style.display = 'none';
    document.getElementById('actionPanel').style.display = 'none';
};

window._renderActionBtn = function(a, defaultStyle) {
    var style = a.style || defaultStyle || '';
    var icon = a.icon ? '<i class="bi ' + a.icon + '"></i> ' : '';
    var extraStyle = style ? ' style="' + style + '"' : '';
    var btnClass = 'btn-action';
    if (a.cat === 'primary') btnClass += ' btn-action-primary';
    else if (a.cat === 'danger') btnClass += ' btn-action-danger';
    if (a.type === 'duplica' && !a.style) btnClass += ' btn-action-duplica';
    if (a.type === 'link') {
        return '<a href="' + a.url + '" class="' + btnClass + '"' + extraStyle + '>' + icon + a.label + '</a>';
    } else if (a.type === 'link_blank') {
        return '<a href="' + a.url + '" target="_blank" class="' + btnClass + '"' + extraStyle + '>' + icon + a.label + '</a>';
    } else if (a.type === 'js') {
        return '<a href="#" onclick="event.preventDefault();closeActionPanel();' + a.code + '" class="' + btnClass + '"' + extraStyle + '>' + icon + a.label + '</a>';
    } else if (a.type === 'delete') {
        var _url = (a.url || '').replace(/'/g, '&#39;');
        var _tp = (a.deleteTipo || '').replace(/'/g, '&#39;');
        var _nm = (a.deleteNome || '').replace(/'/g, '&#39;');
        var _im = (a.deleteImpatto || '').replace(/'/g, '&#39;');
        return '<a href="#" data-delete-btn="1" data-delete-url="' + _url + '" data-delete-tipo="' + _tp + '" data-delete-nome="' + _nm + '" data-delete-impatto="' + _im + '" class="' + btnClass + '"' + extraStyle + '>' + icon + a.label + '</a>';
    } else if (a.type === 'duplica') {
        return '<a href="#" onclick="event.preventDefault();closeActionPanel();loadAjaxForm(\'' + a.url + '\', \'Duplica ' + (a.titolo || '') + '\');" class="' + btnClass + '"' + extraStyle + '>' + icon + a.label + '</a>';
    } else if (a.type === 'custom') {
        return a.html;
    }
    return '';
};

window.openActionPanel = function(title, subtitle, actions, meta) {
    document.getElementById('actionPanelTitle').textContent = (title || '').replace(/\s*\|\s*/g, '\n');
    document.getElementById('actionPanelSubtitle').textContent = subtitle || '';
    var body = document.getElementById('actionPanelBody');
    var html = '';

    if (meta) {
        html += '<div class="meta-box">';
        if (meta.stato) {
            var sc = '#8A8F98';
            if (meta.stato === 'Attivo' || meta.stato === 'attivo' || meta.stato === 'ATTIVO') sc = '#34d399';
            else if (meta.stato === 'Cessato' || meta.stato === 'cessato' || meta.stato === 'CESSATO') sc = '#f87171';
            else if (meta.stato === 'Indeterminato') sc = '#60a5fa';
            else if (meta.stato === 'Determinato') sc = '#fbbf24';
            html += '<div style="margin-bottom:6px;"><span class="badge-stato" style="background:' + sc + '20;color:' + sc + ';border:1px solid ' + sc + '40;"><span class="dot" style="background:' + sc + ';"></span> ' + meta.stato + '</span></div>';
        }
        if (meta.info && meta.info.length > 0) {
            html += '<div class="grid-info">';
            for (var i = 0; i < meta.info.length; i++) {
                var inf = meta.info[i];
                if (inf.v && inf.v !== '-' && inf.v !== '') {
                    html += '<div><span class="c-gray">' + inf.l + ':</span> <span style="color:#ccc;">' + inf.v + '</span></div>';
                }
            }
            html += '</div>';
        }
        if (meta.creatoIl || meta.modificatoIl) {
            html += '<div class="meta-date">';
            if (meta.creatoIl) html += '<span><i class="bi bi-plus-circle me-1"></i>' + meta.creatoIl + '</span>';
            if (meta.modificatoIl) html += '<span><i class="bi bi-pencil me-1"></i>' + meta.modificatoIl + '</span>';
            html += '</div>';
        }
        html += '</div>';
    }

    var hasRow = false;
    for (var _i = 0; _i < actions.length; _i++) {
        if (actions[_i] && actions[_i].row !== undefined) { hasRow = true; break; }
    }

    if (hasRow) {
        var rows = {};
        for (var _i = 0; _i < actions.length; _i++) {
            var a = actions[_i];
            if (!a) continue;
            var r = a.row || 0;
            if (!rows[r]) rows[r] = [];
            rows[r].push(a);
        }
        var rowKeys = Object.keys(rows).sort(function(x,y) { return parseInt(x)-parseInt(y); });
        for (var _ri = 0; _ri < rowKeys.length; _ri++) {
            var items = rows[rowKeys[_ri]];
            var cols = items.length;
            var hasDanger = false;
            for (var _j = 0; _j < items.length; _j++) {
                if (items[_j].cat === 'danger') { hasDanger = true; break; }
            }
            html += '<div style="display:grid;grid-template-columns:repeat(' + cols + ',1fr);gap:6px;margin-bottom:6px;' + (hasDanger ? 'border-top:1px solid rgba(248,113,113,0.15);padding-top:6px;' : '') + '">';
            for (var _j = 0; _j < items.length; _j++) {
                var it = items[_j];
                var ds;
                if (it.cat === 'primary') ds = 'background:rgba(96,165,250,0.1);border:1px solid rgba(96,165,250,0.25);';
                else if (it.cat === 'danger') ds = 'background:rgba(248,113,113,0.08);border:1px solid rgba(248,113,113,0.15);color:#f87171;';
                else ds = 'background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);';
                html += _renderActionBtn(it, ds);
            }
            html += '</div>';
        }
    } else {
        var primary = [], secondary = [], danger = [];
        for (var i = 0; i < actions.length; i++) {
            var a = actions[i];
            if (a.cat === 'primary') primary.push(a);
            else if (a.cat === 'danger') danger.push(a);
            else secondary.push(a);
        }
        if (primary.length > 0) {
            html += '<div style="display:grid;grid-template-columns:repeat(' + Math.min(primary.length, 2) + ',1fr);gap:6px;margin-bottom:6px;">';
            for (var i = 0; i < primary.length; i++) {
                html += _renderActionBtn(primary[i], 'background:rgba(96,165,250,0.1);border:1px solid rgba(96,165,250,0.25);');
            }
            html += '</div>';
        }
        if (secondary.length > 0) {
            html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:6px;">';
            for (var i = 0; i < secondary.length; i++) {
                html += _renderActionBtn(secondary[i], 'background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);');
            }
            html += '</div>';
        }
        if (danger.length > 0) {
            html += '<div style="border-top:1px solid rgba(248,113,113,0.15);margin-top:6px;padding-top:6px;display:grid;grid-template-columns:1fr 1fr;gap:6px;">';
            for (var i = 0; i < danger.length; i++) {
                html += _renderActionBtn(danger[i], 'background:rgba(248,113,113,0.08);border:1px solid rgba(248,113,113,0.15);color:#f87171;');
            }
            html += '</div>';
        }
    }

    body.innerHTML = html;
    document.getElementById('actionPanelOverlay').style.display = 'block';
    document.getElementById('actionPanel').style.display = 'block';
};

window._buildInfoMeta = function(tr, extra) {
    var info = [];
    var email = tr.getAttribute('data-email');
    var tel = tr.getAttribute('data-telefono');
    var comune = tr.getAttribute('data-comune');
    if (email) info.push({l:'Email', v:email});
    if (tel) info.push({l:'Tel', v:tel});
    if (comune) info.push({l:'Comune', v:comune});
    if (extra) { for (var _i = 0; _i < extra.length; _i++) info.push(extra[_i]); }
    var meta = {};
    if (info.length > 0) meta.info = info;
    return meta;
};

window.getActionsForRow = function(tr) {
    var type = tr.getAttribute('data-type');
    var pk = tr.getAttribute('data-pk');
    var title = tr.getAttribute('data-title') || '';
    var sub = tr.getAttribute('data-sub') || '';
    if (!type || !pk) return null;

    if (type === 'datore' || type === 'lavoratore' || type === 'beneficiario') {
        var entity = type;
        var entityLabel = type.charAt(0).toUpperCase() + type.slice(1);
        var modUrl = '/ajax/modifica-' + entity + '/' + pk + '/';
        var docUrl = '/documenti/?' + entity + '_pk=' + pk;
        var dupUrl = '/ajax/duplica-anagrafica/' + entity + '/' + pk + '/';
        var delUrl = '/ajax/elimina-anagrafica/' + entity + '/' + pk + '/';
        return {
            title: title, subtitle: sub,
            meta: _buildInfoMeta(tr),
            actions: [
                {icon:'bi-pencil-fill', label:'Modifica', type:'js', cat:'primary', code:"loadAjaxForm('" + modUrl + "','Modifica " + entityLabel + "')"},
                {icon:'bi-files', label:'Duplica', type:'duplica', url:dupUrl, titolo:entityLabel},
                {icon:'bi-file-earmark', label:'Documenti', type:'link', url:docUrl, style:'background:rgba(250,204,21,0.12);border:1px solid rgba(250,204,21,0.3);'},
                {icon:'bi-trash3', label:'Elimina', type:'delete', cat:'danger', url:delUrl, deleteTipo:entityLabel, deleteNome:title, deleteImpatto:'Il record viene spostato nella pagina Eliminati (ripristinabile).'},
            ]
        };
    }

    if (type === 'contratto_cessato') {
        var docUrl2 = '/documenti/?contratto_pk=' + pk;
        var modUrl2 = '/ajax/modifica-contratto/' + pk + '/';
        var dupUrlCess = '/ajax/duplica-anagrafica/contratto/' + pk + '/';
        var delUrl2 = '/ajax/elimina-contratto/' + pk + '/';
        var metaCess = _buildInfoMeta(tr, [{l:'Stato', v:'Cessato'}]);
        return {
            title: title, subtitle: sub,
            meta: metaCess,
            actions: [
                {icon:'bi-pencil-fill', label:'Modifica', type:'js', cat:'primary', code:"loadAjaxForm('" + modUrl2 + "','Modifica Contratto')"},
                {icon:'bi-files', label:'Duplica', type:'duplica', url:dupUrlCess, titolo:'Contratto'},
                {icon:'bi-file-earmark', label:'Documenti', type:'link', url:docUrl2},
                {icon:'bi-arrow-repeat', label:'Riattiva', type:'js', code:"riattivaContratto(" + pk + ", null)", style:'background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.2);color:#34d399;'},
                {icon:'bi-trash3', label:'Elimina', type:'delete', cat:'danger', url:delUrl2, deleteTipo:'Contratto cessato', deleteNome:title, deleteImpatto:'Eliminazione definitiva del contratto.'},
            ]
        };
    }

    if (type === 'contratto') {
        var table = tr.closest('table');
        var mp = table ? table.getAttribute('data-mp') : '';
        var mc = table ? table.getAttribute('data-mc') : '';
        var ms = table ? table.getAttribute('data-ms') : '';
        var ap = table ? table.getAttribute('data-ap') : '';
        var ac = table ? table.getAttribute('data-ac') : '';
        var as_ = table ? table.getAttribute('data-as') : '';
        var modUrl3 = '/ajax/modifica-contratto/' + pk + '/';
        var docUrl3 = '/documenti/?contratto_pk=' + pk;
        var dupUrl3 = '/ajax/duplica-anagrafica/contratto/' + pk + '/';
        var delUrl3 = '/ajax/elimina-anagrafica/contratto/' + pk + '/';
        var metaCont = _buildInfoMeta(tr, [
            {l:'Tipo', v:tr.getAttribute('data-tipo-contratto')||'-'},
            {l:'Livello', v:tr.getAttribute('data-livello')||'-'},
            {l:'Assunzione', v:tr.getAttribute('data-data-assunzione')||'-'},
            {l:'Fine', v:tr.getAttribute('data-data-fine')||'-'},
        ]);
        metaCont.stato = tr.getAttribute('data-stato') || 'Attivo';
        return {
            title: title, subtitle: sub,
            meta: metaCont,
            actions: [
                {icon:'bi-pencil-fill', label:'Modifica', type:'js', cat:'primary', row:1, code:"loadAjaxForm('" + modUrl3 + "','Modifica Contratto')"},
                mp ? {icon:'bi-calculator', label:'Busta < ' + mp, type:'link', row:2, url:'/calcoli/?contratto=' + pk + '&mese=' + mp + '&anno=' + ap} : null,
                mc ? {icon:'bi-calculator', label:'Busta ' + mc, type:'link', row:2, url:'/calcoli/?contratto=' + pk + '&mese=' + mc + '&anno=' + ac, style:'background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.2);'} : null,
                ms ? {icon:'bi-calculator', label:'Busta > ' + ms, type:'link', row:2, url:'/calcoli/?contratto=' + pk + '&mese=' + ms + '&anno=' + as_} : null,
                {icon:'bi-files', label:'Duplica', type:'duplica', row:3, url:dupUrl3, titolo:'Contratto'},
                {icon:'bi-trash3', label:'Elimina', type:'delete', cat:'danger', row:3, url:delUrl3, deleteTipo:'Contratto', deleteNome:title, deleteImpatto:'Il contratto viene spostato in Contratti Cessati.'},
                {icon:'bi-folder2-open', label:'Documenti arch.', type:'link', row:4, url:docUrl3},
                {icon:'bi-file-pdf', label:'Genera documento', type:'js', row:4, code:"apriGeneraDocumento(" + pk + ")", style:'background:rgba(250,204,21,0.12);border:1px solid rgba(250,204,21,0.3);'},
            ].filter(function(x) { return x !== null; })
        };
    }

    if (type === 'documento') {
        var seeUrl = '/ajax/vedi-documento/' + pk + '/';
        var cartellaUrl = '/apri-cartella-documento/' + pk + '/';
        var delUrl4 = '/ajax/elimina-documento/' + pk + '/';
        var hasContratto = tr.getAttribute('data-has-contratto') === '1';
        var actions = [
            {icon:'bi-eye', label:'Vedi', type:'js', cat:'primary', code:"apriNelPannello('" + seeUrl + "', " + pk + ")"},
            {icon:'bi-download', label:'Scarica', type:'link', url:seeUrl},
            {icon:'bi-printer', label:'Stampa', type:'js', code:"stampaDocumento(" + pk + ", null)"},
            {icon:'bi-folder2-open', label:'Apri cartella', type:'link', url:cartellaUrl}
        ];
        if (!hasContratto) {
            actions.push({icon:'bi-link-45deg', label:'Collega contratto', type:'js', code:"apriCollegaContratto(" + pk + ")"});
        }
        actions.push({icon:'bi-envelope', label:'Invia Email', type:'js', code:"apriInvioDocumento(" + pk + ")"});
        actions.push({icon:'bi-trash3', label:'Elimina', type:'delete', cat:'danger', url:delUrl4, deleteTipo:'Documento', deleteNome:title, deleteImpatto:'Il documento viene eliminato definitivamente.'});
        var metaDoc = {};
        var creato = tr.getAttribute('data-creato');
        var fileSize = tr.getAttribute('data-file-size');
        if (creato || fileSize) {
            metaDoc.info = [];
            if (creato) metaDoc.info.push({l:'Creato', v:creato});
            if (fileSize) metaDoc.info.push({l:'Dimensione', v:fileSize});
        }
        return {title: title, subtitle: sub, meta: metaDoc, actions: actions};
    }

    if (type === 'tabella') {
        var table = tr.closest('table');
        var tipo = table ? table.getAttribute('data-tipo') : '';
        if (!tipo) return null;
        var modUrl = '/ajax/modifica-tabella/' + tipo + '/' + pk + '/';
        var dupUrl = '/ajax/duplica-tabella/' + tipo + '/' + pk + '/';
        var delUrl = '/ajax/elimina-tabella/' + tipo + '/' + pk + '/';
        return {
            title: title, subtitle: sub,
            actions: [
                {icon:'bi-pencil-fill', label:'Modifica', type:'js', cat:'primary', code:"loadAjaxForm('" + modUrl + "','Modifica')"},
                {icon:'bi-files', label:'Duplica', type:'duplica', url:dupUrl, titolo:''},
                {icon:'bi-trash3', label:'Elimina', type:'delete', cat:'danger', url:delUrl, deleteTipo:'Record', deleteNome:title, deleteImpatto:'Eliminazione definitiva.'},
            ]
        };
    }

    if (type === 'backup') {
        return {
            title: title, subtitle: sub,
            actions: [
                {icon:'bi-arrow-counterclockwise', label:'Ripristina', type:'js', cat:'primary', code:"ripristinaBackup(" + pk + ", null)"},
                {icon:'bi-trash3', label:'Elimina', type:'js', cat:'danger', code:"eliminaBackup(" + pk + ")"}
            ]
        };
    }

    if (type === 'eliminato') {
        return {
            title: title, subtitle: sub,
            actions: [
                {icon:'bi-eye', label:'Vedi', type:'js', cat:'primary', code:"apriVediEliminato(" + pk + ")"},
                {icon:'bi-arrow-repeat', label:'Ripristina', type:'js', code:"confermaRipristino(" + pk + ", null)", style:'background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.2);color:#34d399;'},
                {icon:'bi-trash3-fill', label:'Elimina definitivamente', type:'js', cat:'danger', code:"eliminaDefinitivamente(" + pk + ", null)"}
            ]
        };
    }
    return null;
};
