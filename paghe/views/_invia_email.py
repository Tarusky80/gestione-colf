"""Helper centralizzato per invio email (SMTP / programma posta).
Sostituisce il codice duplicato in _documenti.py, _cu.py, _buste_massivo.py, _stampe_invii.py.
Ogni invio crea automaticamente LogInvioEmail."""

from paghe.views._common_imports import *
from paghe.models import ModelloDocumentale, DocumentoArchiviato, LogInvioEmail
from paghe.views._testi import _componi_corpo_email
from paghe.views._helpers import _wrap_html_email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import subprocess
import os
import logging

logger = logging.getLogger(__name__)


def _tb_quote(s):
    """Escape per parametri Thunderbird."""
    return s.replace("'", "''")


def _invia_via_thunderbird(destinatari, oggetto, corpo, allegato_path=None):
    """Invia email aprendo Thunderbird con parametri -compose."""
    opzioni = get_opzioni()
    if not opzioni or not opzioni.exe_posta:
        return {'ok': False, 'errore': 'Programma di posta non configurato.'}
    try:
        params = f"to='{destinatari.replace(';', ',')}',subject='{_tb_quote(oggetto)}',body='{_tb_quote(corpo)}'"
        if allegato_path and os.path.exists(allegato_path):
            params += f",attachment='{allegato_path}'"
        subprocess.Popen([opzioni.exe_posta, '-compose', params])
        return {'ok': True, 'messaggio': 'Programma di posta aperto.'}
    except Exception as e:
        logger.error('Errore apertura Thunderbird: %s', e)
        return {'ok': False, 'errore': f'Impossibile aprire il programma di posta: {e}'}


def _invia_via_smtp(destinatari, oggetto, corpo, allegato_path=None, allegato_nome=None):
    """Invia email via SMTP con eventuale allegato."""
    opzioni = get_opzioni()
    if not opzioni or not opzioni.email_smtp_server:
        return {'ok': False, 'errore': 'SMTP non configurato. Configuralo in Impostazioni.'}

    try:
        msg = MIMEMultipart()
        msg['From'] = opzioni.email_mittente
        msg['To'] = destinatari.replace(';', ',')
        msg['Subject'] = oggetto
        msg.attach(MIMEText(_wrap_html_email(corpo), 'html', 'utf-8'))

        if allegato_path and os.path.exists(allegato_path):
            with open(allegato_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                nome = allegato_nome or os.path.basename(allegato_path)
                part.add_header('Content-Disposition', f'attachment; filename="{nome}"')
                msg.attach(part)

        smtp = smtplib.SMTP(opzioni.email_smtp_server, opzioni.email_smtp_port)
        if opzioni.email_usa_tls:
            smtp.starttls()
        if opzioni.email_smtp_username and opzioni.get_smtp_password():
            smtp.login(opzioni.email_smtp_username, opzioni.get_smtp_password())
        smtp.send_message(msg)
        smtp.quit()
        return {'ok': True, 'messaggio': 'Email inviata con successo.'}
    except Exception as e:
        logger.error('Errore invio SMTP: %s', e)
        return {'ok': False, 'errore': f'Errore invio email: {e}'}


def _crea_log(esito, destinatario, tipo_documento='', contratto=None, messaggio_errore='', request=None):
    """Crea un record LogInvioEmail."""
    try:
        LogInvioEmail.objects.create(
            contratto=contratto,
            tipo_documento=tipo_documento[:50] or 'DOCUMENTO',
            destinatario=destinatario[:200] if destinatario else '',
            esito=esito,
            messaggio_errore=messaggio_errore or '',
            utente=request.user if request and request.user.is_authenticated else None,
        )
    except Exception as e:
        logger.error('Errore creazione LogInvioEmail: %s', e)


def invia_documento_email(doc_pk, destinatario, modello_mail_pk, request=None):
    """
    Invia un DocumentoArchiviato via email (SMTP o Thunderbird).
    Crea LogInvioEmail per ogni tentativo.

    Parametri:
        doc_pk (int): PK del DocumentoArchiviato da inviare
        destinatario (str): email del destinatario
        modello_mail_pk (int): PK del ModelloDocumentale (tipo='MAIL')
        request (HttpRequest, opzionale): per tracciare l'utente nel log

    Restituisce:
        dict: {'ok': True/False, 'messaggio': '...', 'errore': '...'}
    """
    try:
        doc = DocumentoArchiviato.objects.select_related('contratto__datore', 'contratto__lavoratore').get(pk=doc_pk)
    except DocumentoArchiviato.DoesNotExist:
        return {'ok': False, 'errore': 'Documento non trovato.'}

    try:
        modello = ModelloDocumentale.objects.get(pk=modello_mail_pk)
    except ModelloDocumentale.DoesNotExist:
        return {'ok': False, 'errore': 'Modello email non trovato.'}

    opzioni = get_opzioni()
    try:
        corpo, oggetto = _componi_corpo_email(modello, doc.contratto, opzioni)
    except Exception as e:
        logger.exception("Errore in invia_documento_email")
        _crea_log('ERRORE', destinatario, doc.tipo, doc.contratto, str(e), request)
        return {'ok': False, 'errore': f'Errore composizione email: {e}'}

    if opzioni and opzioni.email_usa_programma_posta and opzioni.exe_posta:
        risultato = _invia_via_thunderbird(destinatario, oggetto, corpo, allegato_path=doc.file_path)
    else:
        risultato = _invia_via_smtp(destinatario, oggetto, corpo, allegato_path=doc.file_path, allegato_nome=doc.file_name)

    if risultato['ok']:
        doc.inviato = True
        doc.inviato_il = timezone.now()
        doc.email_destinatario = destinatario
        doc.save(update_fields=['inviato', 'inviato_il', 'email_destinatario'])
        _crea_log('OK', destinatario, doc.tipo, doc.contratto, request=request)
    else:
        _crea_log('ERRORE', destinatario, doc.tipo, doc.contratto, risultato.get('errore', ''), request)

    return risultato


def invia_email_senza_documento(destinatario, modello_mail_pk, contratto=None, request=None, extra_vars=None):
    """
    Invia una email semplice (senza allegato documento) usando un modello MAIL.
    Crea LogInvioEmail per ogni tentativo.

    Parametri:
        destinatario (str): email del destinatario
        modello_mail_pk (int): PK del ModelloDocumentale (tipo='MAIL')
        contratto (ContrattoLavoro, opzionale): per risolvere variabili per-contratto
        request (HttpRequest, opzionale): per tracciare l'utente
        extra_vars (dict, opzionale): variabili extra da passare a _componi_corpo_email

    Restituisce:
        dict: {'ok': True/False, 'messaggio': '...', 'errore': '...'}
    """
    try:
        modello = ModelloDocumentale.objects.get(pk=modello_mail_pk)
    except ModelloDocumentale.DoesNotExist:
        return {'ok': False, 'errore': 'Modello email non trovato.'}

    opzioni = get_opzioni()
    try:
        corpo, oggetto = _componi_corpo_email(modello, contratto, opzioni, extra_vars=extra_vars)
    except Exception as e:
        logger.exception("Errore in invia_email_senza_documento")
        _crea_log('ERRORE', destinatario, modello.tipo, contratto, str(e), request)
        return {'ok': False, 'errore': f'Errore composizione email: {e}'}

    if opzioni and opzioni.email_usa_programma_posta and opzioni.exe_posta:
        risultato = _invia_via_thunderbird(destinatario, oggetto, corpo)
    else:
        risultato = _invia_via_smtp(destinatario, oggetto, corpo)

    tipo_doc = modello.tipo if hasattr(modello, 'tipo') else 'MAIL'
    if risultato['ok']:
        _crea_log('OK', destinatario, tipo_doc, contratto, request=request)
    else:
        _crea_log('ERRORE', destinatario, tipo_doc, contratto, risultato.get('errore', ''), request)

    return risultato
