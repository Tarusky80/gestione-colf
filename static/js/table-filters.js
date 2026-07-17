function filterTable(inputId, tableId) {
    var input = document.getElementById(inputId);
    var filter = input.value.toUpperCase();
    var table = document.getElementById(tableId);
    var rows = table.getElementsByTagName('tr');
    var cols = Array.from(arguments).slice(2);
    for (var i = 1; i < rows.length; i++) {
        var show = false;
        for (var ci = 0; ci < cols.length; ci++) {
            var cell = rows[i].getElementsByTagName('td')[cols[ci]];
            if (cell && cell.textContent.toUpperCase().indexOf(filter) > -1) { show = true; break; }
        }
        rows[i].style.display = show ? '' : 'none';
    }
}
window.filtraPerComune = function(selectId, tableId) {
    var valore = document.getElementById(selectId).value.toUpperCase();
    var table = document.getElementById(tableId);
    var rows = table.getElementsByTagName('tr');
    for (var i = 1; i < rows.length; i++) {
        var comune = (rows[i].getAttribute('data-comune') || '').toUpperCase();
        var show = !valore || comune === valore;
        rows[i].style.display = show ? '' : 'none';
    }
    var countId = tableId === 'datoriTable' ? 'fCount' :
                  tableId === 'lavTable' ? 'fCount' : 'fCount';
    window.aggiornaConteggio(tableId, countId);
};
window.aggiornaConteggio = function(tableId, countId) {
    var tbl = document.getElementById(tableId);
    var cnt = document.getElementById(countId);
    if (!tbl || !cnt) return;
    var rows = tbl.querySelectorAll('tbody tr');
    var tot = 0, vis = 0;
    rows.forEach(function(r) {
        if (r.querySelector('td[colspan]')) return;
        tot++;
        if (r.style.display !== 'none') vis++;
    });
    var val = cnt.querySelector('#fCountVal');
    if (val) { val.textContent = vis + ' di ' + tot; }
    else { cnt.textContent = vis + ' di ' + tot; }
};
