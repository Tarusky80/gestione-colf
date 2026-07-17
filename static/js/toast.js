window.mostraToast = function(msg, ok) {
    var container = document.getElementById('toastContainer');
    if (!container) return;
    var toast = document.createElement('div');
    toast.className = 'toast-item';
    var iconClass = ok ? 'bi-check-circle-fill success' : 'bi-x-circle-fill error';
    toast.innerHTML = '<i class="bi ' + iconClass + ' toast-icon"></i><span class="toast-text" style="font-size:13px;">' + msg + '</span><button type="button" class="toast-close" onclick="this.parentElement.classList.add(\'removing\');setTimeout(function(){var p=this.parentElement;if(p&&p.parentElement)p.remove();}.bind(this),300);">&times;</button>';
    container.appendChild(toast);
    setTimeout(function() {
        if (toast) { toast.classList.add('removing'); setTimeout(function() { if (toast.parentElement) toast.remove(); }, 300); }
    }, 5000);
};
window._stampaToast = function(msg, ok) {
    window.mostraToast(msg, ok);
};
