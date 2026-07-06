"""Import condivisi per tutti i moduli view.

Sostituisce ~40 righe duplicate in 21 file con un singolo import.
Ogni file view fa: from paghe.views._common_imports import *
"""

# --- Standard library ---
import json  # noqa: F401
import logging  # noqa: F401
import math  # noqa: F401
import os  # noqa: F401
import re  # noqa: F401
import io  # noqa: F401
import shutil  # noqa: F401
import subprocess  # noqa: F401
import mimetypes  # noqa: F401
from decimal import Decimal  # noqa: F401
from datetime import date, timedelta  # noqa: F401
from calendar import monthrange, monthcalendar, SATURDAY  # noqa: F401

# --- Django core ---
from django.http import JsonResponse, HttpResponse, FileResponse  # noqa: F401
from django.template.loader import render_to_string  # noqa: F401
from django.shortcuts import render, redirect, get_object_or_404  # noqa: F401
from django.contrib.auth.decorators import login_required  # noqa: F401
from django.contrib.admin.views.decorators import staff_member_required  # noqa: F401
from django.views.decorators.cache import never_cache  # noqa: F401
from django.views.decorators.http import require_http_methods, require_POST  # noqa: F401
from django.views.decorators.clickjacking import xframe_options_exempt  # noqa: F401
from django.db import models  # noqa: F401
from django.db.models import Q, Count, Sum, Value, IntegerField, Subquery, OuterRef, FloatField, F, Min, Prefetch  # noqa: F401
from django.db.models.functions import Coalesce  # noqa: F401
from django.core import serializers  # noqa: F401
from django.core.management import call_command  # noqa: F401
from django.conf import settings  # noqa: F401
from django.utils import timezone  # noqa: F401
from django.contrib import messages  # noqa: F401

# --- Email ---
from email.mime.text import MIMEText  # noqa: F401
from email.mime.multipart import MIMEMultipart  # noqa: F401
from email.mime.base import MIMEBase  # noqa: F401
from email import encoders  # noqa: F401

# --- ReportLab ---
from reportlab.lib.pagesizes import A4, landscape  # noqa: F401
from reportlab.lib.units import mm  # noqa: F401
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image, ListFlowable, ListItem  # noqa: F401
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # noqa: F401
from reportlab.lib.colors import HexColor  # noqa: F401
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT  # noqa: F401

# --- Costanti condivise ---
from paghe.views._constants import MESI_IT  # noqa: F401

# --- Permessi ---
from paghe.decorators import permesso_richiesto  # noqa: F401
from paghe.permessi import ha_permesso, filtro_visibilita, permessi_effettivi  # noqa: F401

# --- Modelli ---
from paghe.models import ( # noqa: F401
    ContrattoLavoro, Beneficiario, DatoreLavoro, Lavoratore,
    ContrattoAttivo, ProgettoRegionale, TipoProgettoRegionale,
    ParametriCCNL, Livello, TabellaCasse, TabellaContributiINPS,
    TabellaMalattia, TabellaScattiAnzianita, RecordEliminato,
    DocumentoArchiviato, ModelloLista, RiepilogoInvio,
    ServizioWebConfig, ModelloComposizione, BustaPaga,
    ModelloDocumentale, AnticipoTFR, ModificaContratto,
    GestoreBackup, CUAnnuale, Appuntamento, RichiestaModificaDatore,
    ProfiloUtente, OpzioniSoftware,
)

# --- Form ---
from paghe.forms import ( # noqa: F401
    DatoreForm, LavoratoreForm, BeneficiarioForm, ContrattoForm,
    OpzioniSoftwareForm, ProgettoRegionaleForm, ParametriCCNLForm,
    TabellaCasseForm, TabellaContributiINPSForm, TabellaMalattiaForm,
    TabellaScattiAnzianitaForm, TipoProgettoRegionaleForm,
    LivelloForm, DocumentoArchiviatoForm, ModelloListaForm,
    ModelloComposizioneForm,
)

# --- Cache ---
from django.core.cache import cache


def get_opzioni():
    """Restituisce OpzioniSoftware (cached 5 minuti)."""
    opz = cache.get('opzioni_software')
    if opz is None:
        opz = OpzioniSoftware.objects.first()
        cache.set('opzioni_software', opz, 300)
    return opz
