"""Notifiche email automatiche per scadenze imminenti."""
from datetime import date, timedelta
from django.utils import timezone
from paghe.models import ContrattoLavoro, DatoreLavoro, LogInvioEmail
from paghe.views._invia_email import _invia_via_smtp, _tb_quote
import logging

logger = logging.getLogger(__name__)

SCADENZE_FISSE = [
    (4, 10, 'Contributi 1° trimestre'),
    (7, 10, 'Contributi 2° trimestre'),
    (10, 10, 'Contributi 3° trimestre'),
    (1, 10, 'Contributi 4° trimestre'),
    (11, 30, 'F24 — Seconda rata'),
    (10, 31, 'Scadenza invio CU'),
]


def _etichetta_giorni(gg):
    if gg == 0:
        return 'SCADE OGGI!'
    elif gg == 1:
        return 'domani!'
    elif gg <= 7 or gg <= 14:
        return f'tra {gg} giorni'
    else:
        return f'tra {gg} giorni'


def _prossime_scadenze(oggi=None):
    """Restituisce lista di (data, titolo, giorni_mancanti)."""
    if oggi is None:
        oggi = timezone.localdate()
    scadenze = []
    anno = oggi.year
    for mese, giorno, titolo in SCADENZE_FISSE:
        data_scadenza = date(anno, mese, giorno)
        if data_scadenza < oggi:
            data_scadenza = date(anno + 1, mese, giorno)
        diff = (data_scadenza - oggi).days
        if 0 <= diff <= 30:
            scadenze.append((data_scadenza, titolo, diff))
    cessazioni = ContrattoLavoro.objects.filter(
        stato='ATTIVO', data_fine__gte=oggi, data_fine__lte=oggi + timedelta(days=30)
    ).select_related('datore', 'lavoratore')
    for c in cessazioni:
        diff = (c.data_fine - oggi).days
        scadenze.append((c.data_fine, f'Cessazione: {c.lavoratore.nome_cognome} / {c.datore.nome_cognome}', diff))
    scadenze.sort(key=lambda x: x[2])
    return scadenze


def _componi_corpo_unico(scadenze, totale_datori):
    """Componi corpo email HTML con tabella riepilogativa."""
    righe = []
    for data_scad, titolo, gg in scadenze:
        if gg == 0:
            label = '<span style="color:#dc3545;font-weight:bold;">SCADE OGGI!</span>'
        elif gg <= 7:
            label = f'<span style="color:#dc3545;font-weight:bold;">{_etichetta_giorni(gg)}</span>'
        elif gg <= 14:
            label = f'<span style="color:#f59e0b;">{_etichetta_giorni(gg)}</span>'
        else:
            label = _etichetta_giorni(gg)
        righe.append(
            f'<tr><td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;">'
            f'{data_scad.strftime("%d/%m/%Y")}</td>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;">{titolo}</td>'
            f'<td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;">{label}</td></tr>'
        )
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;background:#f9fafb;padding:20px;">
<div style="max-width:600px;margin:auto;background:white;border-radius:12px;padding:24px;">
<div style="text-align:center;margin-bottom:20px;">
<h2 style="color:#111827;margin:0;">Promemoria Scadenze</h2>
<p style="color:#6b7280;font-size:13px;margin:4px 0 0;">Sono presenti scadenze per <strong>{totale_datori} datori</strong></p>
</div>
<p style="color:#374151;font-size:14px;">Elenco scadenze imminenti per i contratti di lavoro domestico:</p>
<table style="width:100%;border-collapse:collapse;margin:16px 0;font-size:13px;">
<thead><tr style="background:#f3f4f6;">
<th style="padding:8px 12px;text-align:left;font-weight:600;">Data</th>
<th style="padding:8px 12px;text-align:left;font-weight:600;">Scadenza</th>
<th style="padding:8px 12px;text-align:left;font-weight:600;">Mancano</th>
</tr></thead>
<tbody>{''.join(righe)}</tbody>
</table>
<p style="color:#6b7280;font-size:12px;margin-top:20px;">
Per maggiori dettagli accedi al gestionale.<br>
<span style="color:#9ca3af;">Messaggio generato automaticamente, non rispondere.</span></p>
</div></body></html>"""


def invia_notifiche_scadenze(dry_run=False):
    """Funzione principale: controlla flag, raccoglie scadenze e invia.

    - Se usa programma di posta (Thunderbird): apre UNA finestra con BCC a tutti i datori
    - Se SMTP: invia singolarmente a ogni datore
    """
    from paghe.views._common_imports import get_opzioni

    opzioni = get_opzioni()
    if not opzioni:
        logger.warning('[Notifiche] OpzioniSoftware non trovato.')
        return {'inviate': 0, 'fallite': 0, 'totale_datori': 0, 'errore': 'Nessuna opzione configurata'}
    if not opzioni.notifiche_scadenze_attive:
        logger.info('[Notifiche] Flag notifiche_scadenze_attive = False, salto invio.')
        return {'inviate': 0, 'fallite': 0, 'totale_datori': 0, 'skip': True}

    oggi = timezone.localdate()
    scadenze = _prossime_scadenze(oggi)

    if not scadenze:
        logger.info('[Notifiche] Nessuna scadenza nei prossimi 30 giorni.')
        return {'inviate': 0, 'fallite': 0, 'totale_datori': 0}

    datori = DatoreLavoro.objects.filter(
        pk__in=ContrattoLavoro.objects.filter(stato='ATTIVO').values('datore').distinct()
    ).exclude(email='')

    lista_datori = list(datori)
    if not lista_datori:
        logger.info('[Notifiche] Nessun datore con email valida.')
        return {'inviate': 0, 'fallite': 0, 'totale_datori': 0}

    tutte_email = []
    for d in lista_datori:
        for e in d.email.split(';'):
            e = e.strip()
            if e:
                tutte_email.append(e)

    if dry_run:
        logger.info('[Notifiche] [DRY-RUN] %d scadenze, %d datori, %d email in BCC',
                    len(scadenze), len(lista_datori), len(tutte_email))
        return {'inviate': len(lista_datori), 'fallite': 0, 'totale_datori': len(lista_datori)}

    corpo = _componi_corpo_unico(scadenze, len(lista_datori))
    oggetto = f'Promemoria scadenze lavoro domestico - {oggi.strftime("%d/%m/%Y")}'

    inviate = 0
    fallite = 0

    if opzioni.email_usa_programma_posta and opzioni.exe_posta:
        # --- THUNDERBIRD: UNA finestra con BCC ---
        to_addr = opzioni.email_studio or opzioni.email_mittente or 'noreply@localhost'
        try:
            params = (
                f"to='{_tb_quote(to_addr)}',"
                f"bcc='{_tb_quote(';'.join(tutte_email))}',"
                f"subject='{_tb_quote(oggetto)}',"
                f"body='{_tb_quote(corpo)}',"
                f"format=html"
            )
            import subprocess
            subprocess.Popen([opzioni.exe_posta, '-compose', params])
            for dest in tutte_email:
                LogInvioEmail.objects.create(
                    tipo_documento='NOTIFICA_SCADENZA',
                    destinatario=dest,
                    esito='OK',
                )
            inviate = len(tutte_email)
            logger.info('[Notifiche] Thunderbird aperto con %d destinatari in BCC', len(tutte_email))
        except Exception as e:
            for dest in tutte_email:
                LogInvioEmail.objects.create(
                    tipo_documento='NOTIFICA_SCADENZA',
                    destinatario=dest,
                    esito='ERRORE',
                    messaggio_errore=str(e),
                )
            fallite = len(tutte_email)
            logger.error('[Notifiche] ERRORE apertura Thunderbird: %s', e)
    else:
        # --- SMTP: singolarmente ---
        if not opzioni.email_smtp_server:
            logger.warning('[Notifiche] SMTP non configurato.')
            return {'inviate': 0, 'fallite': 0, 'totale_datori': len(lista_datori), 'errore': 'SMTP non configurato'}
        for dest in tutte_email:
            try:
                esito = _invia_via_smtp(dest, oggetto, corpo)
                if esito['ok']:
                    LogInvioEmail.objects.create(tipo_documento='NOTIFICA_SCADENZA', destinatario=dest, esito='OK')
                    inviate += 1
                else:
                    LogInvioEmail.objects.create(tipo_documento='NOTIFICA_SCADENZA', destinatario=dest, esito='ERRORE', messaggio_errore=esito.get('errore', ''))
                    fallite += 1
            except Exception as e:
                LogInvioEmail.objects.create(tipo_documento='NOTIFICA_SCADENZA', destinatario=dest, esito='ERRORE', messaggio_errore=str(e))
                fallite += 1

    logger.info('[Notifiche] Report: %d inviate, %d fallite, %d datori',
                inviate, fallite, len(lista_datori))
    return {'inviate': inviate, 'fallite': fallite, 'totale_datori': len(lista_datori)}
