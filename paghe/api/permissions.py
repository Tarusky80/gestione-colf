from rest_framework.permissions import BasePermission


class IsDatore(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, 'codice_fiscale')


class IsProprioDatore(BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(request.user, 'codice_fiscale'):
            if hasattr(obj, 'datore'):
                return obj.datore.codice_fiscale == request.user.codice_fiscale
            if hasattr(obj, 'codice_fiscale'):
                return obj.codice_fiscale == request.user.codice_fiscale
        return False
