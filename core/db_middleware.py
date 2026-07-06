"""Middleware per cambiare database SQLite a runtime via cookie firmato."""
import logging
import os

from django.conf import settings
from django.db import connections

logger = logging.getLogger(__name__)


class DatabaseSwitchMiddleware:
    """Legge il cookie db_profile, e se diverso da default, chiude la
    connessione corrente e reimposta DATABASES['default']['NAME'] sul file
    del profilo scelto.

    Deve essere il primo middleware della lista per intercettare la richiesta
    PRIMA che SessionMiddleware/AuthMiddleware tocchino il DB.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            profile = request.get_signed_cookie(
                settings.DB_PROFILE_COOKIE, salt='db_switch', default='default'
            )
        except (ValueError, TypeError):
            profile = 'default'
        if profile not in settings.DB_PROFILES:
            profile = 'default'

        target = settings.DB_PROFILES[profile]['NAME']
        current = settings.DATABASES['default']['NAME']

        # Se siamo in ambiente di test (Django ha cambiato NAME), non
        # interferiamo chiudendo la connessione del test runner.
        test_config = settings.DATABASES['default'].get('TEST', {})
        test_name = test_config.get('NAME')
        in_test_db = (
            (test_name and str(current) == str(test_name))
            or str(current).startswith('file:memorydb')
        )
        if in_test_db:
            request.db_profile = profile
            return self.get_response(request)

        if str(target) != str(current):
            if profile != 'default':
                target_path = str(target)
                if not os.path.exists(target_path) or os.path.getsize(target_path) == 0:
                    logger.warning(
                        'Database "%s" (%s) non trovato o vuoto (%d byte), resto su default',
                        profile, target_path,
                        os.path.getsize(target_path) if os.path.exists(target_path) else -1,
                    )
                    profile = 'default'
                    target = settings.DB_PROFILES['default']['NAME']

            if str(target) != str(current):
                connections['default'].close()
                settings.DATABASES['default']['NAME'] = str(target)

        request.db_profile = profile
        return self.get_response(request)
