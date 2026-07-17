window.getCookie = function(name) {
    var match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? decodeURIComponent(match[2]) : null;
};
window._csrfToken = function() {
    var el = document.querySelector('[name=csrfmiddlewaretoken]');
    if (el) return el.value;
    return window.getCookie('csrftoken') || '';
};
window.getCSRFToken = function() {
    return window.getCookie('csrftoken') || '';
};
