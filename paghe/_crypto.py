import logging
from django.core import signing

logger = logging.getLogger(__name__)

_SALT = 'smtp_password'

def encrypt_smtp_password(raw: str) -> str:
    if not raw:
        return ''
    try:
        return signing.dumps(raw, salt=_SALT)
    except Exception as e:
        logger.error('Errore crittografia password SMTP: %s', e)
        return raw

def decrypt_smtp_password(encrypted: str) -> str:
    if not encrypted:
        return ''
    if encrypted.startswith('{') or encrypted.startswith('['):
        return encrypted
    try:
        return signing.loads(encrypted, salt=_SALT)
    except (signing.BadSignature, signing.SignatureExpired):
        return encrypted
    except Exception as e:
        logger.error('Errore decrittografia password SMTP: %s', e)
        return encrypted
