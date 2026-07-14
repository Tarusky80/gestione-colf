"""Modulo _calcoli_core - generato automaticamente da views.py"""

from paghe.views._common_imports import *

from paghe.views._helpers import _get_testo_fk
from paghe.views._testi import _risolvi_variabili_testo




# --- Helpers calcolo ---

_MAP_IND_MENSILI = [
    ('ind_funzione', 'ind_funzione_mensile', 'Indennità di Funzione'),
    ('ind_bambini_6', 'ind_minori_6_mensile_ft', 'Ind. Bambini <6'),
    ('ind_piu_assistiti', 'ind_piu_assistiti_mensile', 'Ind. Più Assistiti'),
    ('ind_cert_qualita', 'ind_cert_qualita_mensile', 'Cert. Qualità'),
]
_MAP_RATEI = [
    ('paga_tfr', 'tfr_orario', 'TFR'),
    ('paga_13ma', 'tredicesima_oraria', '13ª'),
    ('paga_ferie', 'ferie_orarie', 'Ferie'),
    ('paga_festivi', 'festivi_orari', 'Festivi'),
    ('paga_notturno_tfr', 'notturno_tfr', 'TFR Notturno'),
    ('paga_notturno_13ma', 'notturno_13ma', '13ª Notturna'),
    ('paga_notturno_ferie', 'notturno_ferie', 'Ferie Notturne'),
    ('paga_notturno_festivi', 'notturno_festivi', 'Festivi Notturni'),
]
_SOLO_SE_SELEZIONATO = {'TFR Notturno', '13ª Notturna', 'Ferie Notturne', 'Festivi Notturni'}

_IND_DEFAULTS = {
    'ind_funzione': ('ind_funzione_conviventi', False),
    'ind_bambini_6': ('ind_minori_6_anni_ft', False),
    'ind_piu_assistiti': ('ind_assistenza_piu_persone_ft', False),
    'ind_cert_qualita': ('ind_certificazione_qualita', False),
}


def _calcola_indennita(contratto, p, toggles, attr_overrides=None, default_overrides=None):
    toggles = toggles or {}
    indennita = []
    totale = 0.0
    for key, attr_val, label in _MAP_IND_MENSILI:
        v = float(getattr(p, attr_overrides.get(key, attr_val) if attr_overrides else attr_val, 0))
        campo_default, _ = _IND_DEFAULTS.get(key, (None, False))
        if default_overrides and key in default_overrides:
            campo_default = default_overrides[key]
        if toggles.get(key, getattr(contratto, campo_default, False) if campo_default else False):
            indennita.append({'label': label, 'totale': v})
            totale += v
    return indennita, totale


def _calcola_scatti(contratto, p, toggles, ore_mensili=0):
    toggles = toggles or {}
    scatti_orario = 0.0
    scatti_dettaglio = ''
    if toggles.get('scatti', getattr(contratto, 'applica_scatti', False)) and contratto.data_assunzione:
        anni = date.today().year - contratto.data_assunzione.year
        if (date.today().month, date.today().day) < (contratto.data_assunzione.month, contratto.data_assunzione.day):
            anni -= 1
        bienni = min(anni // 2, 7)
        scatto_obj = TabellaScattiAnzianita.objects.filter(
            livello=contratto.parametri_minimi.livello.codice
        ).first()
        if scatto_obj:
            scatti_orario = float(scatto_obj.valore_scatto) * bienni
            scatti_dettaglio = f"N. {bienni} scatti (€{float(scatto_obj.valore_scatto):.4f} cad.)"
    if not scatti_dettaglio:
        scatti_dettaglio = 'NON INCLUSI'
    scatti_totale = round(scatti_orario * ore_mensili, 4) if ore_mensili else 0.0
    return scatti_orario, scatti_totale, scatti_dettaglio


def _classifica_ratei(contratto, p, toggles, ore_mensili):
    toggles = toggles or {}
    ratei_inclusi = []
    ratei_accantonati = []
    totale_ratei_inclusi_orario = 0.0
    totale_accantonati = 0.0
    for attr, attr_val, label in _MAP_RATEI:
        v = float(getattr(p, attr_val, 0))
        rateo_override_key = 'rateo_' + attr.replace('paga_', '')
        if attr in ('paga_13ma', 'paga_ferie', 'paga_festivi'):
            uso = toggles.get(rateo_override_key, getattr(contratto, attr, False))
            if uso:
                ratei_inclusi.append({'label': label, 'orario': v})
                totale_ratei_inclusi_orario += v
            elif label not in _SOLO_SE_SELEZIONATO:
                ratei_accantonati.append({'label': label, 'orario': v, 'totale': round(v * ore_mensili, 4)})
                totale_accantonati += round(v * ore_mensili, 4)
        elif attr == 'paga_tfr':
            toggle_uso = toggles.get(rateo_override_key)
            tfr_sep = toggles.get('rateo_tfr_separato')
            ant_70 = toggles.get('rateo_anticipo_70')
            if toggle_uso is not None:
                if toggle_uso:
                    ratei_inclusi.append({'label': label, 'orario': v})
                    totale_ratei_inclusi_orario += v
                elif tfr_sep:
                    if ant_70:
                        ratei_inclusi.append({'label': label + ' (70%)', 'orario': round(v * 0.7, 4)})
                        totale_ratei_inclusi_orario += v * 0.7
                        if label not in _SOLO_SE_SELEZIONATO:
                            ratei_accantonati.append({'label': label + ' (30%)', 'orario': round(v * 0.3, 4), 'totale': round(v * 0.3 * ore_mensili, 4)})
                            totale_accantonati += round(v * 0.3 * ore_mensili, 4)
                    else:
                        if label not in _SOLO_SE_SELEZIONATO:
                            ratei_accantonati.append({'label': label, 'orario': v, 'totale': round(v * ore_mensili, 4)})
                            totale_accantonati += round(v * ore_mensili, 4)
                elif label not in _SOLO_SE_SELEZIONATO:
                    ratei_accantonati.append({'label': label, 'orario': v, 'totale': round(v * ore_mensili, 4)})
                    totale_accantonati += round(v * ore_mensili, 4)
            else:
                mt = getattr(contratto, 'modalita_tfr', 'INCLUSO')
                if mt == 'INCLUSO':
                    ratei_inclusi.append({'label': label, 'orario': v})
                    totale_ratei_inclusi_orario += v
                elif mt == 'SEPARATO_70':
                    ratei_inclusi.append({'label': label + ' (70%)', 'orario': round(v * 0.7, 4)})
                    totale_ratei_inclusi_orario += v * 0.7
                    if label not in _SOLO_SE_SELEZIONATO:
                        ratei_accantonati.append({'label': label + ' (30%)', 'orario': round(v * 0.3, 4), 'totale': round(v * 0.3 * ore_mensili, 4)})
                        totale_accantonati += round(v * 0.3 * ore_mensili, 4)
                else:
                    if label not in _SOLO_SE_SELEZIONATO:
                        ratei_accantonati.append({'label': label, 'orario': v, 'totale': round(v * ore_mensili, 4)})
                        totale_accantonati += round(v * ore_mensili, 4)
        else:
            uso = getattr(contratto, attr, False)
            if uso:
                ratei_inclusi.append({'label': label, 'orario': v})
                totale_ratei_inclusi_orario += v
            elif label not in _SOLO_SE_SELEZIONATO:
                ratei_accantonati.append({'label': label, 'orario': v, 'totale': round(v * ore_mensili, 4)})
                totale_accantonati += round(v * ore_mensili, 4)
    return ratei_inclusi, ratei_accantonati, totale_ratei_inclusi_orario, totale_accantonati


def _calcola_contributi(contratto, opzioni, ore_inps, ore_sett, paga_eff_inps_oraria=0):
    soglia_ore = float(opzioni.soglia_ore_contributi) if opzioni else 24.90
    soglia_paga_1 = float(opzioni.soglia_paga_1_contributi) if opzioni else 9.61
    soglia_paga_2 = float(opzioni.soglia_paga_2_contributi) if opzioni else 11.70
    is_sopra_soglia = ore_sett > soglia_ore
    if is_sopra_soglia:
        fascia_inps = TabellaContributiINPS.objects.filter(
            descrizione__icontains="PIU"
        ).first()
    else:
        if paga_eff_inps_oraria <= soglia_paga_1:
            fascia_inps = TabellaContributiINPS.objects.filter(
                descrizione="MENO 24H - FINO A 9,61"
            ).first()
        elif paga_eff_inps_oraria <= soglia_paga_2:
            fascia_inps = TabellaContributiINPS.objects.filter(
                descrizione="MENO 24H - 9,61-11,70"
            ).first()
        else:
            fascia_inps = TabellaContributiINPS.objects.filter(
                descrizione="MENO 24H - OLTRE 11,70"
            ).first()
    inps_orario = float(fascia_inps.totale) if fascia_inps else 0.0
    inps_quota_datore_orario = float(fascia_inps.quota_datore) if fascia_inps else 0.0
    inps_quota_lavoratore_orario = float(fascia_inps.quota_lavoratore) if fascia_inps else 0.0
    inps_totale = round(inps_orario * ore_inps, 4)
    inps_quota_datore_totale = round(inps_quota_datore_orario * ore_inps, 2)
    inps_quota_lavoratore_totale = round(inps_quota_lavoratore_orario * ore_inps, 2)
    ente = getattr(contratto, 'ente_bilaterale', None)
    cassa_orario = float(ente.totale) if ente else 0.0
    cassa_totale = round(cassa_orario * ore_inps, 4)
    fascia_desc = fascia_inps.descrizione if fascia_inps else ('PIU 24H' if is_sopra_soglia else 'MENO 24H')
    return {
        'inps': {'orario': inps_orario, 'totale': inps_totale, 'fascia': fascia_desc,
                 'quota_datore_orario': inps_quota_datore_orario, 'quota_lavoratore_orario': inps_quota_lavoratore_orario,
                 'quota_datore_totale': inps_quota_datore_totale, 'quota_lavoratore_totale': inps_quota_lavoratore_totale},
        'cassa': {'orario': cassa_orario, 'totale': cassa_totale, 'nome': str(ente) if ente else ''},
        'totale': round(inps_totale + cassa_totale, 4),
        'trimestrale_stima': round((inps_totale + cassa_totale) * 3, 2),
        'soglia_ore': soglia_ore,
        'soglia_paga_1': soglia_paga_1,
        'soglia_paga_2': soglia_paga_2,
        'is_sopra_soglia': is_sopra_soglia,
    }


def _calcola_convivenza(contratto, p, is_convivente, convivenza_items):
    if convivenza_items is not None:
        giorni = int(convivenza_items.get('giorni', 26))
        somma_orario = 0.0
        dettaglio = []
        for key, label, attr in [('pranzo', 'Pranzo', 'convivenza_pranzo'), ('cena', 'Cena', 'convivenza_cena'), ('alloggio', 'Alloggio', 'convivenza_alloggio')]:
            if convivenza_items.get(key, False):
                v = float(getattr(p, attr, 0))
                somma_orario += v
                dettaglio.append(f"{label} €{v:.2f}/gg")
        if dettaglio:
            dettaglio.append(f"({giorni}gg)")
            totale = round(somma_orario * giorni, 4)
        else:
            totale = 0.0
            dettaglio = []
    elif is_convivente:
        totale = float(contratto.quota_convivenza_mensile)
        dettaglio = []
        if totale > 0:
            if getattr(contratto, 'paga_pranzo', False):
                dettaglio.append(f"Pranzo €{float(p.convivenza_pranzo):.2f}/gg")
            if getattr(contratto, 'paga_cena', False):
                dettaglio.append(f"Cena €{float(p.convivenza_cena):.2f}/gg")
            if getattr(contratto, 'paga_alloggio', False):
                dettaglio.append(f"Alloggio €{float(p.convivenza_alloggio):.2f}/gg")
    else:
        totale = 0.0
        dettaglio = []
    return totale, dettaglio


def _build_ratei_pagati(ratei_inclusi, ratei_accantonati, ore_mensili, prorata=1.0):
    pagati = []
    for r in ratei_inclusi:
        eff = round(r['orario'] * ore_mensili * prorata, 4)
        pagati.append({'label': r['label'], 'orario': r['orario'], 'totale': 0.0, 'incluso': True, 'nota': 'Incluso nel lordo mensile', 'valore_effettivo': eff})
        r['totale'] = eff
    for r in ratei_accantonati:
        pagati.append({'label': r['label'], 'orario': r['orario'], 'totale': r['totale'], 'incluso': False, 'nota': 'Da corrispondere a fine rapporto', 'valore_effettivo': r['totale']})
    return pagati


def _build_progetti_data(contratto):
    return [
        {
            'nome': 'Progetti ' + str(p.beneficiario) + ' + LUOGO DI LAVORO: "' + (p.beneficiario.indirizzo or '') + (' - ' + p.beneficiario.comune if p.beneficiario.comune else '') + '" — ' + (p.tipo.nome if p.tipo else 'N/D'),
            'colore': p.tipo.colore if p.tipo else '#5E6AD2',
            'data_inizio': p.data_inizio.strftime('%d/%m/%Y') if p.data_inizio else '',
            'indirizzo': getattr(p.beneficiario, 'indirizzo', '') or '',
            'comune': getattr(p.beneficiario, 'comune', '') or '',
            'tipo_nome': p.tipo.nome if p.tipo else 'N/D',
            'beneficiario_nome': str(p.beneficiario),
        }
        for p in contratto.progetto.all().select_related('tipo', 'beneficiario')
    ]


def _build_busta_return_base(contratto, mese, anno, p, opzioni, ore_sett, progetti_data):
    return {
        'contratto_pk': contratto.pk,
        'mese': mese,
        'anno': anno,
        'mese_nome': MESI_IT[mese] if 1 <= mese <= 12 else '',
        'datore': str(contratto.datore),
        'lavoratore': str(contratto.lavoratore),
        'data_assunzione': contratto.data_assunzione.strftime('%d/%m/%Y') if contratto.data_assunzione else '',
        'ore_settimanali': round(ore_sett, 2),
        'soglia_ore': float(opzioni.soglia_ore_contributi) if opzioni else 24.90,
        'codice_rapporto_inps': contratto.codice_rapporto_inps,
        'tipo_contratto': 'Tempo Indeterminato' if contratto.tipo_contratto == 'INDETERMINATO' else ('Tempo Determinato' if contratto.tipo_contratto == 'DETERMINATO' else contratto.get_tipo_contratto_display()),
        'progetti': progetti_data,
        'livello_codice': p.livello.codice,
        'livello_colore': p.livello.colore,
        'descrizione_corta': p.descrizione_corta,
        'settimane_mensili': sum(1 for w in monthcalendar(anno, mese) if w[SATURDAY] != 0),
        'num_sabati': sum(1 for w in monthcalendar(anno, mese) if w[SATURDAY] != 0),
        'convivenza_rates': {'pranzo': float(p.convivenza_pranzo), 'cena': float(p.convivenza_cena), 'alloggio': float(p.convivenza_alloggio)},
        'contratto_paga_pranzo': getattr(contratto, 'paga_pranzo', False),
        'contratto_paga_cena': getattr(contratto, 'paga_cena', False),
        'contratto_paga_alloggio': getattr(contratto, 'paga_alloggio', False),
        'ind_funzione_conviventi': getattr(contratto, 'ind_funzione_conviventi', False),
        'ind_minori_6_anni_ft': getattr(contratto, 'ind_minori_6_anni_ft', False),
        'ind_assistenza_piu_persone_ft': getattr(contratto, 'ind_assistenza_piu_persone_ft', False),
        'ind_certificazione_qualita': getattr(contratto, 'ind_certificazione_qualita', False),
        'contratto_applica_scatti': getattr(contratto, 'applica_scatti', False),
        'contratto_modalita_tfr': getattr(contratto, 'modalita_tfr', 'INCLUSO'),
        'contratto_paga_13ma': getattr(contratto, 'paga_13ma', False),
        'contratto_paga_ferie': getattr(contratto, 'paga_ferie', False),
        'contratto_paga_festivi': getattr(contratto, 'paga_festivi', False),
        'note_datore': getattr(contratto.datore, 'note_datore', '') or '',
        'datore_indirizzo': getattr(contratto.datore, 'indirizzo', '') or '',
        'datore_comune': getattr(contratto.datore, 'comune', '') or '',
        'lavoratore_indirizzo': getattr(contratto.lavoratore, 'indirizzo', '') or '',
        'lavoratore_comune': getattr(contratto.lavoratore, 'comune', '') or '',
        'dati_studio': getattr(opzioni, 'dati_studio', '') or '',
        'telefono_studio': getattr(opzioni, 'telefono_studio', '') or '',
        'email_studio': getattr(opzioni, 'email_studio', '') or '',
        'alert_contributi_studio': _risolvi_variabili_testo(_get_testo_fk(opzioni, 'testo_alert_contributi', 'alert_contributi'), contratto),
        'note_avvertenze': _risolvi_variabili_testo(_get_testo_fk(opzioni, 'testo_note_avvertenze', None) or '', contratto),
        'logo_buste_paga_path': opzioni.logo_buste_paga.path if opzioni and opzioni.logo_buste_paga and hasattr(opzioni.logo_buste_paga, 'path') and opzioni.logo_buste_paga.path else None,
        'logo_buste_paga_url': opzioni.logo_buste_paga.url if opzioni and opzioni.logo_buste_paga and hasattr(opzioni.logo_buste_paga, 'url') and opzioni.logo_buste_paga.url else None,
    }


# --- _calcola_busta_data ---


def _calcola_busta_data(contratto, mese, anno, is_convivente=True, sostituzione=False, convivenza_items=None, toggles=None, budget_override=None, ore_override=None, attr_overrides=None, default_overrides=None, parametri_override=None):
    p = parametri_override or contratto.parametri_minimi
    if not p:
        return {'errore': 'Parametri CCNL non impostati'}
    ore_mensili = float(ore_override) if ore_override is not None else float(contratto.ore_mensili_calcolate)
    budget = float(budget_override) if budget_override is not None else float(contratto.budget_di_partenza)
    if ore_mensili <= 0 or budget <= 0:
        return {'errore': 'Impossibile calcolare: budget o ore pari a zero'}
    ore_inps = math.ceil(ore_mensili)
    ore_sett = round(ore_mensili / 4.345, 2) if ore_override is not None else float(contratto.ore_settimanali_calcolate)
    paga_base_oraria = float(p.retribuzione_sostituzione) if sostituzione and float(p.retribuzione_sostituzione) > 0 else float(p.paga_base)

    indennita, totale_indennita_mensile = _calcola_indennita(contratto, p, toggles, attr_overrides=attr_overrides, default_overrides=default_overrides)
    scatti_orario, scatti_totale, scatti_dettaglio = _calcola_scatti(contratto, p, toggles, ore_mensili)
    ratei_inclusi, ratei_accantonati, totale_ratei_inclusi_orario, totale_accantonati = _classifica_ratei(contratto, p, toggles, ore_mensili)

    totale_indennita_orario = round(totale_indennita_mensile / ore_mensili, 4) if ore_mensili > 0 else 0
    paga_oraria_lorda = paga_base_oraria + totale_ratei_inclusi_orario + totale_indennita_orario + scatti_orario
    lordo_base = (paga_base_oraria + totale_ratei_inclusi_orario) * ore_mensili
    prorata = 1.0 if sostituzione else (budget / lordo_base if lordo_base > 0 else 1.0)
    paga_base_totale = round(paga_base_oraria * ore_mensili * prorata, 4)

    ratei_pagati = _build_ratei_pagati(ratei_inclusi, ratei_accantonati, ore_mensili, prorata)

    opzioni = get_opzioni()
    paga_eff_inps_oraria = paga_base_oraria + float(p.tredicesima_oraria)
    contributi = _calcola_contributi(contratto, opzioni, ore_inps, ore_sett, paga_eff_inps_oraria)
    convivenza_totale, convivenza_dettaglio = _calcola_convivenza(contratto, p, is_convivente, convivenza_items)

    totale_lordo = round(lordo_base * prorata + totale_indennita_mensile + scatti_totale, 2)
    netto = round(totale_lordo - contributi['totale'] - convivenza_totale - totale_accantonati, 4)
    tipo_calcolo = 'SOSTITUZIONE' if sostituzione else ('NON_CONVIVENTE' if not is_convivente else 'CONVIVENTE')

    progetti_data = _build_progetti_data(contratto)
    risultato = _build_busta_return_base(contratto, mese, anno, p, opzioni, ore_sett, progetti_data)
    risultato.update({
        'tipo_calcolo': tipo_calcolo,
        'sopra_soglia': contributi['is_sopra_soglia'],
        'budget_mensile': round(budget, 2),
        'ore_mensili': round(ore_mensili, 2),
        'ore_inps': ore_inps,
        'paga_oraria_totale': round(paga_oraria_lorda, 4),
        'paga_oraria_lorda': round(paga_oraria_lorda, 4),
        'paga_applicata_oraria': round(paga_oraria_lorda, 4),
        'paga_applicata_mensile': round(lordo_base * prorata + totale_indennita_mensile + scatti_totale, 2),
        'paga_base': {'orario': paga_base_oraria, 'totale': paga_base_totale},
        'paga_effettiva_inps_oraria': round(paga_base_oraria + float(p.tredicesima_oraria), 4),
        'paga_effettiva_inps_mensile': round((paga_base_oraria + float(p.tredicesima_oraria)) * ore_mensili, 4),
        'indennita': [{'label': i['label'], 'orario': round(i['totale'] / ore_mensili, 4) if ore_mensili > 0 else 0, 'totale': round(i['totale'], 4)} for i in indennita],
        'totale_indennita': round(sum(i['totale'] for i in indennita), 4),
        'scatti_anzianita': {'valore': round(scatti_totale, 4), 'orario': round(scatti_orario, 4), 'dettaglio': scatti_dettaglio},
        'ratei_pagati': ratei_pagati,
        'totale_ratei_pagati': round(sum(r['totale'] for r in ratei_pagati), 4),
        'totale_ratei_inclusi': round(sum(r['orario'] * ore_mensili for r in ratei_inclusi), 4),
        'ratei_totale_escluso_tfr': round(sum((r['orario'] * ore_mensili) if r.get('incluso') else r['totale'] for r in ratei_pagati if r['label'] not in ('TFR', 'TFR Notturno')), 4),
        'totale_accantonati': round(totale_accantonati, 4),
        'verifica_copertura': round(budget - totale_lordo, 2),
        'totale_lordo': totale_lordo,
        'contributi': contributi,
        'trattenute': {
            'convivenza': {'totale': round(convivenza_totale, 4), 'dettaglio': convivenza_dettaglio},
            'ratei_accantonati': round(totale_accantonati, 4),
            'totale': round(convivenza_totale + totale_accantonati, 4),
        },
        'netto': netto,
        'differenza': round(budget - totale_lordo, 2),
        'tfr_accumulato': round(
            sum(r['valore_effettivo'] for r in ratei_pagati if r['label'] in ('TFR', 'TFR Notturno')),
            4
        ),
    })
    return risultato


# --- _calcola_busta_inversa_data ---


# ============================================================
# CALCOLO INVERSO BUSTA PAGA (da ore/lordo/netto)
# ============================================================

def _calcola_busta_inversa_data(contratto, mese, anno, ore_mensili=None, ore_settimanali=None, lordo_target=None, netto_target=None, convivenza_items=None, toggles=None):
    p = contratto.parametri_minimi
    if not p:
        return {'errore': 'Parametri CCNL non impostati'}
    inputs = [('ore_mensili', ore_mensili), ('ore_settimanali', ore_settimanali), ('lordo', lordo_target), ('netto', netto_target)]
    forniti = [(k, v) for k, v in inputs if v is not None]
    if not forniti:
        return {'errore': 'Specificare almeno uno tra ore_mensili, ore_settimanali, lordo_target, netto_target'}
    if len(forniti) > 1:
        return {'errore': 'Specificare UNO solo tra ore_mensili, ore_settimanali, lordo_target, netto_target'}
    input_usato, input_valore = forniti[0]
    input_valore = float(input_valore)
    paga_base_oraria = float(p.paga_base)
    paga_eff_inps_oraria = paga_base_oraria + float(p.tredicesima_oraria)
    opzioni = get_opzioni()

    indennita, totale_indennita_mensile = _calcola_indennita(contratto, p, toggles)
    scatti_orario, _, scatti_dettaglio = _calcola_scatti(contratto, p, toggles)
    ratei_inclusi, ratei_accantonati, totale_ratei_inclusi_orario, _ = _classifica_ratei(contratto, p, toggles, 1)

    ratei_inclusi_orari = [(r['label'], r['orario']) for r in ratei_inclusi]
    ratei_non_inclusi_orari = [(r['label'], r['orario']) for r in ratei_accantonati]

    def _calcola_con_ore(ore):
        ore = max(ore, 0.01)
        ore_inps = math.ceil(ore)
        ore_sett = ore / 4.33
        paga_base_totale = round(paga_base_oraria * ore, 4)
        scatti_totale = round(scatti_orario * ore, 4)
        ratei_inclusi_out = [{'label': l, 'orario': v, 'totale': round(v * ore, 4)} for l, v in ratei_inclusi_orari]
        totale_accantonati = 0.0
        ratei_accantonati_out = []
        for l, v in ratei_non_inclusi_orari:
            tot = round(v * ore, 4)
            ratei_accantonati_out.append({'label': l, 'orario': v, 'totale': tot})
            totale_accantonati += tot
        for i in indennita:
            i['orario'] = round(i['totale'] / ore, 4) if ore > 0 else 0
            i['totale'] = round(i['totale'], 4)
        ratei_pagati = _build_ratei_pagati(ratei_inclusi_out, ratei_accantonati_out, ore)
        lordo = round(paga_base_totale + totale_indennita_mensile + scatti_totale + sum(r['totale'] for r in ratei_inclusi_out), 2)
        contributi = _calcola_contributi(contratto, opzioni, ore_inps, ore_sett, paga_eff_inps_oraria)
        conv_totale, conv_dettaglio = _calcola_convivenza(contratto, p, True, convivenza_items)
        netto_val = round(lordo - contributi['totale'] - conv_totale - totale_accantonati, 4)
        return {
            'ore': ore, 'ore_inps': ore_inps, 'ore_sett': round(ore_sett, 2),
            'paga_base_totale': paga_base_totale, 'indennita': indennita,
            'totale_indennita': round(totale_indennita_mensile, 4),
            'scatti_totale': scatti_totale, 'scatti_orario': round(scatti_orario, 4),
            'scatti_dettaglio': scatti_dettaglio, 'ratei_inclusi': ratei_inclusi_out,
            'ratei_accantonati': ratei_accantonati_out, 'ratei_pagati': ratei_pagati,
            'totale_ratei_inclusi': round(sum(r['totale'] for r in ratei_inclusi_out), 4),
            'totale_accantonati': round(totale_accantonati, 4), 'lordo': lordo,
            'inps_orario': contributi['inps']['orario'], 'cassa_orario': contributi['cassa']['orario'],
            'inps_totale': contributi['inps']['totale'], 'cassa_totale': contributi['cassa']['totale'],
            'totale_contributi': contributi['totale'],
            'convivenza_totale': conv_totale, 'convivenza_dettaglio': conv_dettaglio,
            'netto': netto_val, 'is_sopra_soglia': contributi['is_sopra_soglia'],
        }

    if input_usato == 'ore_settimanali':
        ore_mensili = round(input_valore * 4.33, 2)
        r = _calcola_con_ore(ore_mensili)
    elif input_usato == 'ore_mensili':
        r = _calcola_con_ore(input_valore)
    elif input_usato == 'lordo':
        coeff = paga_base_oraria + totale_ratei_inclusi_orario + scatti_orario
        if coeff <= 0:
            return {'errore': 'Impossibile calcolare ore: paga oraria lorda pari a zero'}
        ore_derivate = max((input_valore - totale_indennita_mensile) / coeff, 0.01)
        r = _calcola_con_ore(ore_derivate)
        if abs(r['lordo'] - input_valore) > 0.02:
            raffinamento = input_valore / r['lordo'] if r['lordo'] > 0 else 1
            r = _calcola_con_ore(ore_derivate * raffinamento)
    elif input_usato == 'netto':
        lo, hi = 0.01, 2000.0
        for _ in range(50):
            mid = (lo + hi) / 2
            r = _calcola_con_ore(mid)
            if r['netto'] < input_valore:
                lo = mid
            else:
                hi = mid
        r = _calcola_con_ore((lo + hi) / 2)

    ore_finale = r['ore']
    ore_inps = r['ore_inps']
    ore_sett_finale = r['ore_sett']
    paga_oraria_lorda = round(paga_base_oraria + totale_ratei_inclusi_orario + (round(totale_indennita_mensile / ore_finale, 4) if ore_finale > 0 else 0) + scatti_orario, 4)

    progetti_data = _build_progetti_data(contratto)
    risultato = _build_busta_return_base(contratto, mese, anno, p, opzioni, ore_sett_finale, progetti_data)
    risultato.update({
        'tipo_calcolo': f'CALCOLO_INVERSO_{input_usato.upper()}' if input_usato else 'CALCOLO_INVERSO',
        'sopra_soglia': r['is_sopra_soglia'],
        'budget_mensile': 0,
        'ore_mensili': round(ore_finale, 2),
        'ore_inps': ore_inps,
        'paga_oraria_totale': paga_oraria_lorda,
        'paga_oraria_lorda': paga_oraria_lorda,
        'paga_applicata_oraria': round(r['lordo'] / ore_finale, 4) if ore_finale > 0 else 0,
        'paga_applicata_mensile': round(r['lordo'], 2),
        'paga_base': {'orario': paga_base_oraria, 'totale': r['paga_base_totale']},
        'paga_effettiva_inps_oraria': round(paga_base_oraria + float(p.tredicesima_oraria), 4),
        'paga_effettiva_inps_mensile': round((paga_base_oraria + float(p.tredicesima_oraria)) * ore_finale, 4),
        'indennita': r['indennita'],
        'totale_indennita': r['totale_indennita'],
        'scatti_anzianita': {'valore': r['scatti_totale'], 'orario': r['scatti_orario'], 'dettaglio': r['scatti_dettaglio']},
        'ratei_pagati': r['ratei_pagati'],
        'totale_ratei_pagati': round(sum(x['totale'] for x in r['ratei_pagati']), 4),
        'totale_ratei_inclusi': r['totale_ratei_inclusi'],
        'ratei_totale_escluso_tfr': round(sum((x['orario'] * ore_finale) if x.get('incluso') else x['totale'] for x in r['ratei_pagati'] if x['label'] not in ('TFR', 'TFR Notturno')), 4),
        'totale_accantonati': r['totale_accantonati'],
        'verifica_copertura': 0,
        'totale_lordo': r['lordo'],
        'contributi': {
            'inps': {'orario': r['inps_orario'], 'totale': r['inps_totale'], 'fascia': 'SOPRA' if r['is_sopra_soglia'] else 'SOTTO'},
            'cassa': {'orario': r['cassa_orario'], 'totale': r['cassa_totale'], 'nome': str(getattr(contratto, 'ente_bilaterale', None)) if getattr(contratto, 'ente_bilaterale', None) else ''},
            'totale': r['totale_contributi'],
            'trimestrale_stima': round(r['totale_contributi'] * 3, 2),
        },
        'trattenute': {
            'convivenza': {'totale': round(r['convivenza_totale'], 4), 'dettaglio': r['convivenza_dettaglio']},
            'ratei_accantonati': r['totale_accantonati'],
            'totale': round(r['convivenza_totale'] + r['totale_accantonati'], 4),
        },
        'netto': r['netto'],
        'differenza': round(r['lordo'] - r['netto'] - r['totale_contributi'], 2),
        'input_usato': input_usato,
        'input_valore': round(input_valore, 4) if isinstance(input_valore, (int, float)) else input_valore,
        'ore_calcolate': round(ore_finale, 2),
        'ore_settimanali_calcolate': round(ore_sett_finale, 2),
        'lordo_calcolato': r['lordo'],
        'netto_calcolato': r['netto'],
    })
    return risultato


# --- _calcola_progetti_data ---


def _calcola_progetti_data(ctx, contratto):
    """Calcola la ripartizione per progetto basata sul budget mensile."""
    progetti_qs = contratto.progetto.all().select_related('tipo', 'beneficiario')
    if not progetti_qs:
        return None

    # Totali già calcolati in Pagina 1 (escluso TFR)
    ore_totali = ctx['ore_mensili']
    lordo_totale = ctx['totale_lordo']
    contrib_totale = ctx['contributi']['totale']
    ctx['trattenute']['totale']
    ratei_ind_totale = ctx['totale_indennita'] + ctx['totale_ratei_inclusi']
    netto_totale = ctx['netto']

    budget_totale = sum(float(p.budget_mensile or 0) for p in progetti_qs)

    righe = []
    for p in progetti_qs:
        budget_p = float(p.budget_mensile or 0)
        quota = budget_p / budget_totale if budget_totale > 0 else 1.0 / len(progetti_qs)

        ore_p = math.ceil(ore_totali * quota)
        lordo_p = round(lordo_totale * quota, 2)
        contrib_p = round(contrib_totale * quota, 2)
        ratei_ind_p = round(ratei_ind_totale * quota, 2)
        netto_p = round(netto_totale * quota, 2)

        righe.append({
            'nome': str(p.beneficiario) + ' \u2014 ' + (p.tipo.nome if p.tipo else 'N/D'),
            'ore': ore_p,
            'paga_oraria': round(ctx['paga_applicata_oraria'], 4),
            'lordo_progetto': lordo_p,
            'contrib': contrib_p,
            'ratei_ind': ratei_ind_p,
            'netto': netto_p
        })

    return {
        'righe': righe,
        'totali': {
            'ore': math.ceil(ore_totali),
            'lordo_progetto': lordo_totale,
            'contrib': contrib_totale,
            'ratei_ind': ratei_ind_totale,
            'netto': netto_totale,
        },
        'indennita_totale': ctx['totale_indennita'],
        'ratei_totale': ctx['ratei_totale_escluso_tfr'],
    }


# --- _calcola_busta_conviventi_ccnl_data ---


# ============================================================
# BUSTA PAGA CONVIVENTI CCNL (basata su minimi tabellari mensili)
# ============================================================

def _calcola_busta_conviventi_ccnl_data(contratto, mese, anno, tipo_orario='FT', toggles=None, convivenza_items=None):
    p = contratto.parametri_minimi
    if not p:
        return {'errore': 'Parametri CCNL non impostati'}
    opzioni = get_opzioni()
    if tipo_orario == 'PT' and float(p.minimo_mensile_pt) > 0:
        minimo_mensile = float(p.minimo_mensile_pt)
    else:
        minimo_mensile = float(p.minimo_mensile_ft)
    if minimo_mensile <= 0:
        return {'errore': 'Minimo mensile CCNL non impostato per questo livello'}
    paga_base_oraria = float(p.paga_base)

    is_pt = tipo_orario == 'PT'
    attr_overrides = {'ind_bambini_6': 'ind_minori_6_mensile_pt'} if is_pt else None
    default_overrides = {
        'ind_bambini_6': 'ind_minori_6_anni_pt',
        'ind_piu_assistiti': 'ind_assistenza_piu_persone_pt',
    } if is_pt else None
    indennita, totale_indennita_mensile = _calcola_indennita(contratto, p, toggles, attr_overrides, default_overrides)

    lordo_base = minimo_mensile + totale_indennita_mensile
    ore_mensili = math.ceil(lordo_base / paga_base_oraria) if paga_base_oraria > 0 else 0
    if ore_mensili <= 0:
        return {'errore': 'Impossibile calcolare le ore: paga base oraria non valida'}
    ore_inps = ore_mensili
    ore_sett = ore_mensili / 4.33

    scatti_orario, scatti_totale, scatti_dettaglio = _calcola_scatti(contratto, p, toggles, ore_mensili)
    ratei_inclusi, ratei_accantonati, totale_ratei_inclusi_orario, totale_accantonati = _classifica_ratei(contratto, p, toggles, ore_mensili)

    ratei_pagati = _build_ratei_pagati(ratei_inclusi, ratei_accantonati, ore_mensili)

    paga_oraria_lorda = paga_base_oraria + totale_ratei_inclusi_orario + scatti_orario
    paga_eff_inps_oraria = paga_base_oraria + float(p.tredicesima_oraria)
    contributi = _calcola_contributi(contratto, opzioni, ore_inps, ore_sett, paga_eff_inps_oraria)
    convivenza_totale, convivenza_dettaglio = _calcola_convivenza(contratto, p, True, convivenza_items)

    scatti_mensile = round(scatti_orario * ore_mensili, 4)
    totale_lordo = round(lordo_base + scatti_mensile, 2)
    netto = round(totale_lordo - contributi['totale'] - convivenza_totale - totale_accantonati, 4)

    progetti_data = _build_progetti_data(contratto)
    risultato = _build_busta_return_base(contratto, mese, anno, p, opzioni, ore_sett, progetti_data)
    risultato.update({
        'tipo_calcolo': 'CONVIVENTI_CCNL',
        'sopra_soglia': contributi['is_sopra_soglia'],
        'budget_mensile': round(float(contratto.budget_di_partenza), 2),
        'ore_mensili': round(ore_mensili, 2),
        'ore_inps': ore_inps,
        'paga_oraria_totale': round(paga_oraria_lorda, 4),
        'paga_oraria_lorda': round(paga_oraria_lorda, 4),
        'paga_applicata_oraria': round(paga_oraria_lorda, 4),
        'paga_applicata_mensile': round(paga_oraria_lorda * ore_mensili, 4),
        'paga_base': {'orario': paga_base_oraria, 'totale': round(paga_base_oraria * ore_mensili, 4)},
        'paga_effettiva_inps_oraria': round(paga_base_oraria + float(p.tredicesima_oraria), 4),
        'paga_effettiva_inps_mensile': round((paga_base_oraria + float(p.tredicesima_oraria)) * ore_mensili, 4),
        'indennita': [{'label': i['label'], 'orario': round(i['totale'] / ore_mensili, 4) if ore_mensili > 0 else 0, 'totale': round(i['totale'], 4)} for i in indennita],
        'totale_indennita': round(totale_indennita_mensile, 4),
        'scatti_anzianita': {'valore': round(scatti_totale, 4), 'orario': round(scatti_orario, 4), 'dettaglio': scatti_dettaglio},
        'minimo_ccnl': minimo_mensile,
        'indennita_ccnl': indennita,
        'tipo_orario_ccnl': tipo_orario,
        'ratei_pagati': ratei_pagati,
        'totale_ratei_pagati': round(sum(r['totale'] for r in ratei_pagati), 4),
        'totale_ratei_inclusi': round(sum(r['orario'] * ore_mensili for r in ratei_inclusi), 4),
        'ratei_totale_escluso_tfr': round(sum((r['orario'] * ore_mensili) if r.get('incluso') else r['totale'] for r in ratei_pagati if r['label'] not in ('TFR', 'TFR Notturno')), 4),
        'totale_accantonati': round(totale_accantonati, 4),
        'verifica_copertura': round(totale_lordo - round(paga_base_oraria * ore_mensili, 4) - sum(r['totale'] for r in ratei_inclusi) - scatti_mensile, 2),
        'totale_lordo': totale_lordo,
        'contributi': contributi,
        'trattenute': {
            'convivenza': {'totale': round(convivenza_totale, 4), 'dettaglio': convivenza_dettaglio},
            'ratei_accantonati': round(totale_accantonati, 4),
            'totale': round(convivenza_totale + totale_accantonati, 4),
        },
        'netto': netto,
        'differenza': round(totale_lordo - netto - contributi['totale'], 2),
        'has_pt': float(p.minimo_mensile_pt) > 0,
    })
    return risultato


# --- _calcola_malattia_data ---


def _calcola_malattia_data(contratto, mese, anno, giorni_malattia, sostituzione=False, ricaduta=False, ricoverato=False, giorni_usati_override=None):
    """Calcola i dati della busta malattia per un contratto. Ritorna dict con tutti i campi."""
    p = contratto.parametri_minimi
    if not p:
        return {'errore': 'Parametri CCNL non impostati'}
    ore_mensili = float(contratto.ore_mensili_calcolate)
    if ore_mensili <= 0:
        return {'errore': 'Ore mensili pari a zero'}
    if giorni_malattia <= 0:
        return {'errore': 'Inserire il numero di giorni di malattia'}

    anzianita_mesi = (date(anno, mese, 1) - contratto.data_assunzione).days // 30
    rec_malattia = TabellaMalattia.objects.filter(
        soglia_mesi__gte=anzianita_mesi
    ).order_by('soglia_mesi').first()
    max_giorni = rec_malattia.giorni_durata if rec_malattia else 8
    conservazione = rec_malattia.conservazione_posto if rec_malattia else 10

    if sostituzione:
        retr_sost = float(p.retribuzione_sostituzione) if p.retribuzione_sostituzione else None
        paga_oraria = retr_sost if retr_sost and retr_sost > 0 else float(p.paga_base)
        label_paga = 'Retribuzione Sostituzione (Art. 14 c.9)'
    else:
        paga_oraria = float(p.paga_base)
        label_paga = 'Paga Base Oraria'
    ore_giornaliere = ore_mensili / 26
    retribuzione_giornaliera = round(paga_oraria * ore_giornaliere, 4)
    giorni_pagati = min(giorni_malattia, max_giorni)
    giorni_usati_db = int(contratto.giorni_malattia_usati_anno or 0)
    giorni_usati = int(giorni_usati_override) if giorni_usati_override is not None else giorni_usati_db
    if giorni_usati < 0:
        giorni_usati = 0
    giorni_residui = max_giorni - giorni_usati
    plafond_esaurito = giorni_residui <= 0
    if plafond_esaurito:
        giorni_50 = 0; giorni_100 = 0; importo_50 = 0; importo_100 = 0; importo_totale = 0
    else:
        if giorni_malattia > giorni_residui:
            giorni_pagati = giorni_residui

        if ricaduta:
            giorni_50 = 0
            giorni_100 = giorni_pagati
            importo_50 = 0
            importo_100 = round(retribuzione_giornaliera * 1.0 * giorni_pagati, 2)
        else:
            giorni_50 = min(giorni_pagati, 3)
            giorni_100 = giorni_pagati - giorni_50
            importo_50 = round(retribuzione_giornaliera * 0.5 * giorni_50, 2)
            importo_100 = round(retribuzione_giornaliera * 1.0 * giorni_100, 2)



    is_convivente = contratto.is_convivente
    indennita_va = 0
    vitto_alloggio_gg = 0
    if not plafond_esaurito:
        if ricoverato and is_convivente:
            vitto_alloggio_gg = round(float(p.convivenza_pranzo or 0) + float(p.convivenza_cena or 0) + float(p.convivenza_alloggio or 0), 2)
            indennita_va = round(vitto_alloggio_gg * giorni_pagati, 2)
        importo_totale = round(importo_50 + importo_100 + indennita_va, 2)

    mese_nomi = ['', 'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
                 'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']
    if not sostituzione:
        retr_sost_val = float(p.retribuzione_sostituzione) if p.retribuzione_sostituzione else 0
        confronto_sostituzione = round((retr_sost_val if retr_sost_val > 0 else float(p.paga_base)) * ore_giornaliere, 2)
    else:
        confronto_sostituzione = round(float(p.paga_base) * ore_giornaliere, 2)
    ore_pagate = round(giorni_pagati * ore_giornaliere, 2)
    inps_rate = TabellaContributiINPS.objects.first()
    aliquota_inps = float(inps_rate.totale) if inps_rate else 0.0
    contributi_inps = round(ore_pagate * aliquota_inps, 2) if aliquota_inps > 0 else 0
    return {
        'sostituzione': sostituzione,
        'label_paga': label_paga,
        'paga_oraria': round(paga_oraria, 4),
        'paga_base_oraria': round(float(p.paga_base), 4),
        'retribuzione_sostituzione': round(float(p.retribuzione_sostituzione), 4),
        'ore_giornaliere': round(ore_giornaliere, 2),
        'ore_mensili': ore_mensili,
        'retribuzione_giornaliera': round(retribuzione_giornaliera, 2),
        'confronto_sostituzione': round(confronto_sostituzione, 2),
        'giorni_malattia': giorni_malattia,
        'max_giorni': max_giorni,
        'giorni_pagati': giorni_pagati,
        'giorni_50': giorni_50,
        'giorni_100': giorni_100,
        'importo_50': importo_50,
        'importo_100': importo_100,
        'importo_totale': importo_totale,
        'anzianita_mesi': anzianita_mesi,
        'conservazione': conservazione,
        'giorni_usati': giorni_usati,
        'giorni_residui': max(giorni_residui, 0),
        'plafond_esaurito': plafond_esaurito,
        'ricaduta': ricaduta,
        'ricoverato': ricoverato,
        'indennita_va': indennita_va,
        'vitto_alloggio_gg': vitto_alloggio_gg,
        'is_convivente': is_convivente,
        'contributi_inps': contributi_inps,
        'ore_pagate': ore_pagate,
        'livello': p.livello.codice if p.livello else '',
        'livello_colore': p.livello.colore if p.livello and p.livello.colore else '#5E6AD2',
        'datore': contratto.datore.nome_cognome,
        'datore_comune': contratto.datore.comune or '',
        'lavoratore': contratto.lavoratore.nome_cognome,
        'tipo_contratto': contratto.get_tipo_contratto_display(),
        'mese_nome': mese_nomi[mese],
        'anno': anno,
        'mese': mese,
        'budget_mensile': round(float(contratto.budget_di_partenza), 2),
    }
