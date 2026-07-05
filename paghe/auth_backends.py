from django.contrib.auth.hashers import check_password
from django.shortcuts import redirect
from functools import wraps


class DatoreAuthBackend:
    def authenticate(self, request, codice_fiscale=None, password=None):
        from paghe.models import AccessoDatore
        if not codice_fiscale or not password:
            return None
        cf = codice_fiscale.upper().strip()
        try:
            ad = AccessoDatore.objects.select_related('datore').get(
                datore__codice_fiscale=cf,
                accesso_abilitato=True
            )
            if check_password(password, ad.password):
                return ad.datore
        except AccessoDatore.DoesNotExist:
            pass
        return None

    def get_user(self, datore_cf):
        from paghe.models import DatoreLavoro
        try:
            return DatoreLavoro.objects.get(codice_fiscale=datore_cf)
        except DatoreLavoro.DoesNotExist:
            return None


def datore_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'datore_cf' not in request.session:
            return redirect('datore_login')
        return view_func(request, *args, **kwargs)
    return wrapper
