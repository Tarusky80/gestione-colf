"""
Field resolver — risolve field_path contro un modello Django,
inclusi FK annidati, property, campi calcolati speciali.
"""
import math
from decimal import Decimal
from datetime import date
from .models import (
    DatoreLavoro, Lavoratore, Beneficiario, ContrattoAttivo,
    ProgettoRegionale, TabellaContributiINPS
)
from paghe.views._common_imports import get_opzioni


def _trova_fascia_inps(obj, opzioni, ore_sett):
    """Seleziona la fascia contributiva INPS in base a ore settimanali e paga effettiva."""
    soglia_ore = float(opzioni.soglia_ore_contributi) if opzioni and opzioni.soglia_ore_contributi else 24.90
    is_sopra = ore_sett > soglia_ore
    if is_sopra:
        return TabellaContributiINPS.objects.filter(descrizione__icontains="PIU").first()
    soglia_paga_1 = float(opzioni.soglia_paga_1_contributi) if opzioni else 9.61
    soglia_paga_2 = float(opzioni.soglia_paga_2_contributi) if opzioni else 11.70
    paga_base = float(obj.parametri_minimi.paga_base) if obj.parametri_minimi else 0
    tredicesima = float(obj.parametri_minimi.tredicesima_oraria) if obj.parametri_minimi else 0
    paga_eff = math.floor((paga_base + tredicesima) * 100) / 100
    if paga_eff <= soglia_paga_1:
        return TabellaContributiINPS.objects.filter(descrizione="MENO 24H - FINO A 9,61").first()
    elif paga_eff <= soglia_paga_2:
        return TabellaContributiINPS.objects.filter(descrizione="MENO 24H - 9,61-11,70").first()
    else:
        return TabellaContributiINPS.objects.filter(descrizione="MENO 24H - OLTRE 11,70").first()


def resolve_column_values(tipo_sorgente, colonne, filters=None):
    """
    Dato un tipo_sorgente e una lista di colonne (con field_path),
    restituisce una lista di dict con i valori risolti per ogni riga.
    """
    qs = _build_queryset(tipo_sorgente, filters)
    if qs is None:
        return [], []

    opzioni = get_opzioni()
    rows = []
    for obj in qs:
        row = {}
        for col in colonne:
            row[col['field_path']] = _resolve_field(obj, col['field_path'], tipo_sorgente, opzioni)
        rows.append(row)

    labels = [c['label'] for c in colonne]
    return rows, labels


def _build_queryset(tipo_sorgente, filters=None):
    filters = filters or {}

    if tipo_sorgente == 'DATORE':
        qs = DatoreLavoro.objects.prefetch_related(
            'contratti_come_datore__progetto__tipo'
        ).all().order_by('nome_cognome')

    elif tipo_sorgente == 'LAVORATORE':
        qs = Lavoratore.objects.prefetch_related(
            'contratti_come_lavoratore__progetto__tipo'
        ).all().order_by('nome_cognome')

    elif tipo_sorgente == 'BENEFICIARIO':
        qs = Beneficiario.objects.prefetch_related(
            'progetti__tipo'
        ).all().order_by('nome_cognome')

    elif tipo_sorgente in ('CONTRATTO', 'PAGOPA_INPS'):
        qs = ContrattoAttivo.objects.filter(stato='ATTIVO').select_related(
            'datore', 'lavoratore',
            'parametri_minimi__livello',
            'ente_bilaterale'
        ).prefetch_related(
            'progetto__tipo', 'progetto__beneficiario'
        ).order_by('datore__nome_cognome', 'lavoratore__nome_cognome')

        filtro_datore = filters.get('datore')
        filtro_livello = filters.get('livello')
        if filtro_datore:
            qs = qs.filter(datore_id=filtro_datore)
        if filtro_livello:
            qs = qs.filter(parametri_minimi__livello__codice=filtro_livello)

    elif tipo_sorgente == 'PROGETTO_REGIONALE':
        qs = ProgettoRegionale.objects.select_related(
            'beneficiario', 'tipo'
        ).all().order_by('beneficiario__nome_cognome')

        filtro_tipo = filters.get('tipo_progetto')
        if filtro_tipo:
            qs = qs.filter(tipo_id=filtro_tipo)

    else:
        return None

    return qs


def _resolve_field(obj, field_path, tipo_sorgente, opzioni):
    """Risolve un singolo field_path su un oggetto."""

    # --- Campi calcolati speciali (non sono attributi reali) ---

    if field_path == 'n_progetti':
        if tipo_sorgente == 'DATORE':
            progetti = set()
            for c in obj.contratti_come_datore.all():
                for p in c.progetto.all():
                    progetti.add(p.pk)
            return len(progetti)
        elif tipo_sorgente == 'LAVORATORE':
            progetti = set()
            for c in obj.contratti_come_lavoratore.all():
                for p in c.progetto.all():
                    progetti.add(p.pk)
            return len(progetti)
        elif tipo_sorgente == 'BENEFICIARIO':
            return obj.progetti.count()
        return 0

    if field_path == 'n_contratti_attivi':
        if tipo_sorgente == 'DATORE':
            return obj.contratti_come_datore.filter(stato='ATTIVO').count()
        elif tipo_sorgente == 'LAVORATORE':
            return obj.contratti_come_lavoratore.filter(stato='ATTIVO').count()
        return 0

    if field_path == 'budget_annuale':
        if tipo_sorgente in ('CONTRATTO', 'PAGOPA_INPS'):
            bdp = float(obj.budget_di_partenza) if hasattr(obj, 'budget_di_partenza') else 0.0
            return math.floor(bdp * 12 * 100) / 100
        return 0.0

    if field_path == 'progetti_lista':
        if tipo_sorgente in ('CONTRATTO', 'PAGOPA_INPS'):
            progetti = list(obj.progetto.all())
            nomi = []
            for p in progetti:
                nome = p.tipo.nome if p.tipo else 'N/D'
                nomi.append(nome)
            return ', '.join(nomi) if nomi else '\u2014'
        return '\u2014'

    if field_path == 'ore_inps':
        ore_m = float(obj.ore_mensili_calcolate)
        return math.ceil(ore_m)

    if field_path == 'ore_trim':
        ore_m = float(obj.ore_mensili_calcolate)
        ore_inps = math.ceil(ore_m)
        return ore_inps * 3

    if field_path == 'paga_oraria_inps':
        paga_base = float(obj.parametri_minimi.paga_base) if obj.parametri_minimi else 0
        tredicesima = float(obj.parametri_minimi.tredicesima_oraria) if obj.parametri_minimi else 0
        return math.floor((paga_base + tredicesima) * 100) / 100

    if field_path == 'cassa_orario':
        return float(obj.ente_bilaterale.totale) if obj.ente_bilaterale else 0.0

    if field_path == 'aliquota_inps_orario':
        ore_sett = float(obj.ore_settimanali_calcolate)
        fascia = _trova_fascia_inps(obj, opzioni, ore_sett)
        return float(fascia.totale) if fascia else 0.0

    if field_path == 'soglia_contributi_superata':
        ore_sett = float(obj.ore_settimanali_calcolate)
        soglia = float(opzioni.soglia_ore_contributi) if opzioni and opzioni.soglia_ore_contributi else 24.90
        return ore_sett > soglia

    if field_path == 'imp_cassa_trim':
        ore_m = float(obj.ore_mensili_calcolate)
        ore_inps = math.ceil(ore_m)
        ore_trim = ore_inps * 3
        cassa_orario = float(obj.ente_bilaterale.totale) if obj.ente_bilaterale else 0.0
        return math.floor(cassa_orario * ore_trim * 100) / 100

    if field_path == 'stima_contrib_trim':
        ore_m = float(obj.ore_mensili_calcolate)
        ore_inps = math.ceil(ore_m)
        ore_trim = ore_inps * 3
        ore_sett = float(obj.ore_settimanali_calcolate)
        fascia = _trova_fascia_inps(obj, opzioni, ore_sett)
        inps_orario = float(fascia.totale) if fascia else 0.0
        return math.floor(inps_orario * ore_trim * 100) / 100

    if field_path == 'contrib_totali':
        ore_m = float(obj.ore_mensili_calcolate)
        ore_inps = math.ceil(ore_m)
        ore_trim = ore_inps * 3
        cassa_orario = float(obj.ente_bilaterale.totale) if obj.ente_bilaterale else 0.0
        ore_sett = float(obj.ore_settimanali_calcolate)
        fascia = _trova_fascia_inps(obj, opzioni, ore_sett)
        inps_orario = float(fascia.totale) if fascia else 0.0
        imp_cassa = math.floor(cassa_orario * ore_trim * 100) / 100
        stima = math.floor(inps_orario * ore_trim * 100) / 100
        return math.floor((imp_cassa + stima) * 100) / 100

    # --- Attributi diretti, FK annidati, e property ---
    return _resolve_attribute(obj, field_path)


def _resolve_attribute(obj, field_path):
    """Risolve un field_path come attributo (sale FK con dot notation)."""
    parts = field_path.split('.')
    current = obj
    for part in parts:
        if current is None:
            return None
        try:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                current = getattr(current, part)
        except Exception:
            return None

    if callable(current):
        try:
            current = current()
        except Exception:
            return None

    return _format_value(current)


def _format_value(val):
    """Formatta il valore per il display."""
    if val is None:
        return '\u2014'

    if isinstance(val, bool):
        return val

    if isinstance(val, date):
        return val.strftime('%d/%m/%Y')

    if isinstance(val, (Decimal, float, int)):
        if isinstance(val, bool):
            return val
        if isinstance(val, int) and not isinstance(val, bool):
            return val
        return val

    if isinstance(val, str):
        return val.strip() if val.strip() else '\u2014'

    return str(val)
