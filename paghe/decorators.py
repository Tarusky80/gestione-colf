from functools import wraps
from django.shortcuts import redirect
from django.http import JsonResponse
from django.conf import settings
from .permessi import ha_permesso


def permesso_richiesto(*permessi):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(settings.LOGIN_URL)
            for p in permessi:
                if not ha_permesso(request.user, p):
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({'errore': 'Permesso negato'}, status=403)
                    return redirect(settings.LOGIN_URL)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
