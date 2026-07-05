from django.conf import settings

# Build CSP policy once at import time
_CSP = {
    'default-src': ["'self'"],
    'script-src': [
        "'self'",
        "'unsafe-inline'",
        "'unsafe-eval'",
        'https://cdn.ckeditor.com',
        'https://code.jquery.com',
        'https://cdn.jsdelivr.net',
        'https://cdnjs.cloudflare.com',
    ],
    'style-src': [
        "'self'",
        "'unsafe-inline'",
        'https://cdn.ckeditor.com',
        'https://cdn.jsdelivr.net',
        'https://cdnjs.cloudflare.com',
        'https://fonts.googleapis.com',
        'https://stackpath.bootstrapcdn.com',
    ],
    'img-src': [
        "'self'",
        'data:',
        'blob:',
        'https://cdn.ckeditor.com',
    ],
    'font-src': [
        "'self'",
        'https://cdnjs.cloudflare.com',
        'https://fonts.gstatic.com',
    ],
    'connect-src': ["'self'"],
    'frame-src': ["'self'"],
    'object-src': ["'none'"],
    'base-uri': ["'self'"],
}

_CSP_STRING = '; '.join(
    f"{key} {' '.join(vals)}" for key, vals in _CSP.items()
)


class ContentSecurityPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not getattr(settings, 'DEBUG', False):
            response['Content-Security-Policy'] = _CSP_STRING
        return response
