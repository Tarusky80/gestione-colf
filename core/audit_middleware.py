"""Middleware che cattura l'utente corrente in thread-local per i segnali audit."""

import threading

from django.utils.deprecation import MiddlewareMixin

_audit_thread = threading.local()


def get_audit_user():
    return getattr(_audit_thread, 'user', None)


def get_audit_ip():
    return getattr(_audit_thread, 'ip', None)


class AuditMiddleware(MiddlewareMixin):
    def process_request(self, request):
        _audit_thread.user = getattr(request, 'user', None)
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            _audit_thread.ip = xff.split(',')[0].strip()
        else:
            _audit_thread.ip = request.META.get('REMOTE_ADDR')

    def process_response(self, request, response):
        _audit_thread.user = None
        _audit_thread.ip = None
        return response
