import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models

logger = logging.getLogger(__name__)


def _fernet_key():
    raw = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(raw)


class EncryptedCharField(models.CharField):
    """CharField che cifra/decifra in trasparenza con Fernet.

    I dati esistenti in chiaro vengono letti senza errori (fallback).
    Ogni scrittura cifra automaticamente il valore.
    """

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is None or value == '':
            return value
        return Fernet(_fernet_key()).encrypt(value.encode()).decode()

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            return Fernet(_fernet_key()).decrypt(value.encode()).decode()
        except InvalidToken:
            logger.warning("email_smtp_password in chiaro nel DB — verra' cifrato al prossimo salvataggio")
            return value
        except Exception as exc:
            logger.exception("Errore decrypt email_smtp_password: %s", exc)
            return value


class MultiEmailValidator:
    """Valida una stringa contenente una o piu email separate da ;"""

    def __init__(self, message=None):
        from django.core.validators import EmailValidator
        self.validator = EmailValidator()
        self.message = message or 'Inserire uno o piu indirizzi email validi separati da ;'

    def __call__(self, value):
        if not value or not isinstance(value, str):
            return
        parti = [p.strip() for p in value.split(';') if p.strip()]
        for parte in parti:
            try:
                self.validator(parte)
            except Exception as exc:
                from django.core.exceptions import ValidationError
                raise ValidationError(self.message) from exc

    def deconstruct(self):
        return 'paghe.fields.MultiEmailValidator', [], {'message': self.message}
