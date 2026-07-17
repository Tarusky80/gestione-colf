document.querySelectorAll('.nav-group .nav-group-label').forEach(function(label) {
    label.addEventListener('click', function(e) {
        var group = this.closest('.nav-group');
        group.classList.toggle('collapsed');
        if (group.id) {
            localStorage.setItem('sidebar_' + group.id, group.classList.contains('collapsed') ? '1' : '0');
        }
    });
});
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.nav-group[id]').forEach(function(group) {
        var saved = localStorage.getItem('sidebar_' + group.id);
        if (saved === '0') {
            group.classList.remove('collapsed');
        } else {
            group.classList.add('collapsed');
        }
    });
});

document.getElementById('nav_dashboard').addEventListener('click', function() {
    document.querySelectorAll('.nav-group[id]').forEach(function(g) {
        g.classList.add('collapsed');
        localStorage.setItem('sidebar_' + g.id, '1');
    });
});

function toggleNavLayout() {
    var b = document.body;
    b.classList.toggle('topbar-mode');
    var isTopbar = b.classList.contains('topbar-mode');
    localStorage.setItem('nav_layout', isTopbar ? 'topbar' : 'sidebar');
    var nav = document.querySelector('.sidebar nav');
    if (nav) nav.classList.toggle('overflow-auto', !isTopbar);
    var edge = document.querySelector('.sidebar-toggle-edge');
    if (edge) edge.title = isTopbar ? 'Passa a sidebar' : 'Passa a topbar';
    if (isTopbar) {
        document.querySelectorAll('.nav-group').forEach(function(g) { g.classList.remove('collapsed'); });
    } else {
        document.querySelectorAll('.nav-group[id]').forEach(function(g) {
            var s = localStorage.getItem('sidebar_' + g.id);
            g.classList.toggle('collapsed', s !== '0');
        });
    }
}
document.addEventListener('DOMContentLoaded', function() {
    if (localStorage.getItem('nav_layout') === 'topbar') {
        document.body.classList.add('topbar-mode');
        document.querySelectorAll('.nav-group').forEach(function(g) { g.classList.remove('collapsed'); });
        var nav = document.querySelector('.sidebar nav');
        if (nav) nav.classList.remove('overflow-auto');
    }
});
