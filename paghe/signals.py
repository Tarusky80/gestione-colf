"""Segnali per audit log automatico su tutti i modelli principali."""

import logging
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from core.audit_middleware import get_audit_ip, get_audit_user
from paghe.models import (
    Appuntamento,
    AuditLog,
    Beneficiario,
    BustaPaga,
    ContrattoLavoro,
    DatoreLavoro,
    DocumentoArchiviato,
    Lavoratore,
    Livello,
    ModelloDocumentale,
    OpzioniSoftware,
    ParametriCCNL,
    ProgettoRegionale,
    TabellaCasse,
    TabellaContributiINPS,
    TabellaMalattia,
    TabellaScattiAnzianita,
    TipoProgettoRegionale,
)

logger = logging.getLogger(__name__)

MODELLI_AUDIT = [
    (DatoreLavoro, 'DatoreLavoro'),
    (Lavoratore, 'Lavoratore'),
    (Beneficiario, 'Beneficiario'),
    (ProgettoRegionale, 'ProgettoRegionale'),
    (ContrattoLavoro, 'ContrattoLavoro'),
    (BustaPaga, 'BustaPaga'),
    (DocumentoArchiviato, 'DocumentoArchiviato'),
    (OpzioniSoftware, 'OpzioniSoftware'),
    (Appuntamento, 'Appuntamento'),
    (ModelloDocumentale, 'ModelloDocumentale'),
    (ParametriCCNL, 'ParametriCCNL'),
    (Livello, 'Livello'),
    (TabellaCasse, 'TabellaCasse'),
    (TabellaContributiINPS, 'TabellaContributiINPS'),
    (TabellaMalattia, 'TabellaMalattia'),
    (TabellaScattiAnzianita, 'TabellaScattiAnzianita'),
    (TipoProgettoRegionale, 'TipoProgettoRegionale'),
]


def _serializza(instance):
    data = {}
    for field in instance._meta.fields:
        try:
            val = getattr(instance, field.name)
            if hasattr(val, 'strftime'):
                val = val.isoformat()
            elif hasattr(val, 'pk'):
                val = str(val.pk)
            elif hasattr(val, 'url'):
                val = str(val)
            elif isinstance(val, Decimal):
                val = float(val)
            data[field.name] = val
        except Exception:
            data[field.name] = 'ERR'
    return data


def _log_audit(modello_nome, pk_oggetto, azione, dettagli='',
               dati_prec=None, dati_succ=None):
    utente = get_audit_user()
    ip = get_audit_ip()
    if utente and utente.is_authenticated and not get_user_model().objects.filter(pk=utente.pk).exists():
        utente = None
    AuditLog.objects.create(
        modello_coinvolto=modello_nome,
        pk_oggetto=str(pk_oggetto) if pk_oggetto else '',
        azione=azione,
        dettagli=str(dettagli)[:255],
        utente=utente if utente and utente.is_authenticated else None,
        indirizzo_ip=ip,
        dati_precedenti=dati_prec,
        dati_successivi=dati_succ,
    )


def _crea_segnali(modello, nome):
    """Factory per evitare closure late-binding."""
    @receiver(post_save, sender=modello, weak=False)
    def _on_save(sender, instance, created, **kwargs):
        try:
            azione = 'CREAZIONE' if created else 'MODIFICA'
            pk_name = getattr(sender._meta, 'pk_name', 'pk')
            pk_val = getattr(instance, pk_name, None) or instance.pk
            dettagli = f"{sender._meta.verbose_name or sender.__name__}: {pk_val}"
            _log_audit(
                modello_nome=nome,
                pk_oggetto=str(pk_val) if pk_val else '',
                azione=azione,
                dettagli=dettagli,
                dati_prec=None if created else _serializza(instance),
                dati_succ=_serializza(instance),
            )
        except Exception:
            logger.exception("Audit save fallito per %s pk=%s", nome, instance.pk if instance else '?')

    @receiver(post_delete, sender=modello, weak=False)
    def _on_delete(sender, instance, **kwargs):
        try:
            pk_name = getattr(sender._meta, 'pk_name', 'pk')
            pk_val = getattr(instance, pk_name, None) or instance.pk
            _log_audit(
                modello_nome=nome,
                pk_oggetto=str(pk_val) if pk_val else '',
                azione='ELIMINAZIONE',
                dettagli=f"{sender._meta.verbose_name or sender.__name__}: {pk_val}",
                dati_prec=_serializza(instance),
                dati_succ=None,
            )
        except Exception:
            logger.exception("Audit delete fallito per %s pk=%s", nome, instance.pk if instance else '?')


# Registra segnali per ogni modello
for modello, nome in MODELLI_AUDIT:
    _crea_segnali(modello, nome)
