function sortTable(th, forceDirection) {
    const table = th.closest('table');
    const tbody = table.querySelector('tbody');
    if (!tbody) return;
    const idx = Array.from(th.parentNode.children).indexOf(th);
    const isAsc = forceDirection ? forceDirection === 'asc'
                 : th.classList.contains('sort-desc');
    const dir = isAsc ? 'asc' : 'desc';
    const rows = Array.from(tbody.querySelectorAll('tr:not(.no-sort)'));

    table.querySelectorAll('th').forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
    th.classList.add(dir === 'asc' ? 'sort-asc' : 'sort-desc');

    rows.sort(function(a, b) {
        const ca = a.children[idx];
        const cb = b.children[idx];
        if (!ca || !cb) return 0;
        let va = ca.getAttribute('data-sort') || ca.textContent.trim();
        let vb = cb.getAttribute('data-sort') || cb.textContent.trim();
        const na = parseFloat(va.replace(/[€\s]/g, '').replace(',', '.'));
        const nb = parseFloat(vb.replace(/[€\s]/g, '').replace(',', '.'));
        if (!isNaN(na) && !isNaN(nb)) { va = na; vb = nb; }
        else {
            const da = Date.parse(va);
            const db = Date.parse(vb);
            if (!isNaN(da) && !isNaN(db)) { va = da; vb = db; }
        }
        if (va < vb) return isAsc ? 1 : -1;
        if (va > vb) return isAsc ? -1 : 1;
        return 0;
    });
    rows.forEach(r => tbody.appendChild(r));

    if (table.id) {
        localStorage.setItem('sort_' + table.id + '_col', idx);
        localStorage.setItem('sort_' + table.id + '_dir', dir);
    }
}

document.addEventListener('click', function(e) {
    const th = e.target.closest('.sortable th');
    if (!th) return;
    sortTable(th);
});

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.sortable').forEach(function(table) {
        if (!table.id) return;
        var col = localStorage.getItem('sort_' + table.id + '_col');
        var dir = localStorage.getItem('sort_' + table.id + '_dir');
        if (col !== null && dir !== null) {
            var th = table.querySelectorAll('th')[parseInt(col)];
            if (th) sortTable(th, dir);
        }
    });
});
