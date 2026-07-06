from django.core.management.base import BaseCommand
from paghe.models import ModelloDocumentale

CODICE_PREFIX = 'TEMPLATE AUTOMATICO'

TEMPLATES = [
    # 1. PDF_INIZIO — Inizio Rapporto
    {
        'tipo': 'PDF_INIZIO',
        'codice': f'{CODICE_PREFIX}_PDF_INIZIO',
        'oggetto_titolo': 'Inizio Rapporto di Lavoro - {{NOME_DATORE}} / {{NOME_LAVORATORE}}',
        'corpo_testo': '''{{NOME_DATORE}}
{{INDIRIZZO_DATORE}}
{{PAESE_DATORE}}

Oggetto: Comunicazione di Inizio Rapporto di Lavoro

Il/La Sig./Sig.ra {{NOME_LAVORATORE}}
{{INDIRIZZO_LAVORATORE}}
{{PAESE_LAVORATORE}}
Codice Fiscale: {{CF_LAVORATORE}}

con decorrenza {{DATA_ASSUNZIONE}}
Tipologia: {{TIPO_CONTRATTO}}
Orario: {{ORE_SETTIMANALI}} ore settimanali ({{ORE_MENSILI}} ore mensili)
Codice Rapporto INPS: {{CODICE_RAPPORTO_INPS}}
Parametri Minimi: {{PARAMETRI_MINIMI}}
Ente Bilaterale: {{ENTE_BILATERALE}}

{{LINEA}}

Progetto: {{TIPO_PROGETTO}}
Budget Annuale: {{BUDGET_ANNUALE}}
Budget Mensile: {{BUDGET_MENSILE}}
Beneficiario: {{NOME_BENEFICIARIO}}

{{LINEA}}

CCNL: Livello {{LIVELLO_CCNL}} - Paga Base: {{PAGA_BASE}}

{{LINEA}}

Data: {{DATA_ODIERNA}}''',
    },

    # 2. PDF_FINE — Fine Rapporto
    {
        'tipo': 'PDF_FINE',
        'codice': f'{CODICE_PREFIX}_PDF_FINE',
        'oggetto_titolo': 'Fine Rapporto di Lavoro - {{NOME_DATORE}} / {{NOME_LAVORATORE}}',
        'corpo_testo': '''{{NOME_DATORE}}
{{INDIRIZZO_DATORE}}
{{PAESE_DATORE}}

Oggetto: Comunicazione di Fine Rapporto di Lavoro

Il/La Sig./Sig.ra {{NOME_LAVORATORE}}
{{INDIRIZZO_LAVORATORE}}
{{PAESE_LAVORATORE}}
Codice Fiscale: {{CF_LAVORATORE}}

Data fine rapporto: {{DATA_FINE}}
Tipo contratto: {{TIPO_CONTRATTO}}
Codice Rapporto INPS: {{CODICE_RAPPORTO_INPS}}

{{LINEA}}

Si attesta che il rapporto di lavoro è cessato in data {{DATA_FINE}}.
Il lavoratore ha diritto al trattamento di fine rapporto (TFR) e agli altri
emolumenti previsti dalla normativa vigente.

{{LINEA}}

Data: {{DATA_ODIERNA}}''',
    },

    # 3. PDF_RISCONTRO — Riscontro Comune
    {
        'tipo': 'PDF_RISCONTRO',
        'codice': f'{CODICE_PREFIX}_PDF_RISCONTRO',
        'oggetto_titolo': 'Riscontro Comune - {{NOME_BENEFICIARIO}}',
        'corpo_testo': '''{{NOME_DATORE}}
{{INDIRIZZO_DATORE}}
{{PAESE_DATORE}}

Oggetto: Riscontro Comune per il Beneficiario {{NOME_BENEFICIARIO}}

Il/La Sig./Sig.ra {{NOME_BENEFICIARIO}}
Codice Fiscale: {{CF_BENEFICIARIO}}
Indirizzo: {{INDIRIZZO_BENEFICIARIO}}
Comune: {{COMUNE_BENEFICIARIO}}

Progetto: {{TIPO_PROGETTO}}
Budget Annuale: {{BUDGET_ANNUALE}}

{{LINEA}}

Lavoratore incaricato: {{NOME_LAVORATORE}}

{{LINEA}}

Data: {{DATA_ODIERNA}}''',
    },

    # 4. RICEVUTA
    {
        'tipo': 'RICEVUTA',
        'codice': f'{CODICE_PREFIX}_RICEVUTA',
        'oggetto_titolo': 'Ricevuta - {{NOME_DATORE}} / {{NOME_LAVORATORE}}',
        'corpo_testo': '''RICEVUTA

Il/La sottoscritto/a {{NOME_DATORE}}
{{INDIRIZZO_DATORE}}
{{PAESE_DATORE}}

dichiara di aver ricevuto dal/la Sig./Sig.ra {{NOME_LAVORATORE}}
{{INDIRIZZO_LAVORATORE}}
{{PAESE_LAVORATORE}}

la documentazione relativa al rapporto di lavoro decorrente dal {{DATA_ASSUNZIONE}}
per il progetto {{TIPO_PROGETTO}} a favore del beneficiario {{NOME_BENEFICIARIO}}.

{{LINEA}}

Data: {{DATA_ODIERNA}}

Firma del Datore
________________________

Firma del Lavoratore
________________________''',
    },

    # 5. RIEPILOGO_RAPPORTO
    {
        'tipo': 'RIEPILOGO_RAPPORTO',
        'codice': f'{CODICE_PREFIX}_RIEPILOGO_RAPPORTO',
        'oggetto_titolo': 'Riepilogo Rapporto di Lavoro - {{NOME_DATORE}} / {{NOME_LAVORATORE}}',
        'corpo_testo': '''RIEPILOGO RAPPORTO DI LAVORO

Datore di Lavoro: {{NOME_DATORE}}
Codice Fiscale: {{CF_DATORE}}
Indirizzo: {{INDIRIZZO_DATORE}}
Comune: {{PAESE_DATORE}}
Email: {{MAIL_DATORE}}
Telefono: {{TELEFONO_DATORE}}

{{LINEA}}

Lavoratore: {{NOME_LAVORATORE}}
Codice Fiscale: {{CF_LAVORATORE}}
Indirizzo: {{INDIRIZZO_LAVORATORE}}
Comune: {{PAESE_LAVORATORE}}

{{LINEA}}

Dati Contratto:
Tipo: {{TIPO_CONTRATTO}}
Data Assunzione: {{DATA_ASSUNZIONE}}
Data Fine: {{DATA_FINE}}
Ore Settimanali: {{ORE_SETTIMANALI}}
Ore Mensili: {{ORE_MENSILI}}
Codice Rapporto INPS: {{CODICE_RAPPORTO_INPS}}
Parametri Minimi: {{PARAMETRI_MINIMI}}
Ente Bilaterale: {{ENTE_BILATERALE}}

{{LINEA}}

CCNL: Livello {{LIVELLO_CCNL}}
Paga Base: {{PAGA_BASE}}

{{LINEA}}

Progetto: {{TIPO_PROGETTO}}
Budget Annuale: {{BUDGET_ANNUALE}}
Budget Mensile: {{BUDGET_MENSILE}}
Beneficiario: {{NOME_BENEFICIARIO}}

{{LINEA}}

Data: {{DATA_ODIERNA}}''',
    },

    # 6. CARTELLINA
    {
        'tipo': 'CARTELLINA',
        'codice': f'{CODICE_PREFIX}_CARTELLINA',
        'oggetto_titolo': '',
        'corpo_testo': '''<p>{{TOP_DOCUMENTO}}</p>
<p><strong>Documentazione allegata:</strong></p>
<ul>
<li>Copia contratto di lavoro</li>
<li>Buste paga</li>
<li>CUD / Certificazione Unica</li>
</ul>
<p>&nbsp;</p>
<p>{{LINEA}}</p>
<p>Data: {{DATA_ODIERNA}}</p>
<p>{{FOOTER_DOCUMENTO}}</p>''',
    },

    # 7. CUD
    {
        'tipo': 'CUD',
        'codice': f'{CODICE_PREFIX}_CUD',
        'oggetto_titolo': 'Certificazione Unica - {{NOME_LAVORATORE}}',
        'corpo_testo': '''CERTIFICAZIONE UNICA (CUD)

Anno {{ANNO_IN_CORSO}}

Datore di Lavoro: {{NOME_DATORE}}
Codice Fiscale: {{CF_DATORE}}
Indirizzo: {{INDIRIZZO_DATORE}}
Comune: {{PAESE_DATORE}}

{{LINEA}}

Lavoratore: {{NOME_LAVORATORE}}
Codice Fiscale: {{CF_LAVORATORE}}
Indirizzo: {{INDIRIZZO_LAVORATORE}}
Comune: {{PAESE_LAVORATORE}}

{{LINEA}}

Il sottoscritto datore di lavoro comunica i dati retributivi e
contributivi per l'anno precedente relativi al rapporto di lavoro
del/la Sig./Sig.ra {{NOME_LAVORATORE}}.

{{LINEA}}

La presente certificazione viene rilasciata per gli adempimenti
fiscali previsti dalla normativa vigente.

{{LINEA}}

Data: {{DATA_ODIERNA}}

Firma del Datore
________________________''',
    },

    # 8. RICHIESTA_CUD
    {
        'tipo': 'RICHIESTA_CUD',
        'codice': f'{CODICE_PREFIX}_RICHIESTA_CUD',
        'oggetto_titolo': 'Richiesta Certificazione Unica - {{NOME_LAVORATORE}}',
        'corpo_testo': '''RICHIESTA CERTIFICAZIONE UNICA (CUD)

Il/La sottoscritto/a {{NOME_LAVORATORE}}
Codice Fiscale: {{CF_LAVORATORE}}
Indirizzo: {{INDIRIZZO_LAVORATORE}}
Comune: {{PAESE_LAVORATORE}}

CHIEDE

al/la Sig./Sig.ra {{NOME_DATORE}}
{{INDIRIZZO_DATORE}}
{{PAESE_DATORE}}
Email: {{MAIL_DATORE}}

il rilascio della Certificazione Unica (CUD) relativa al rapporto
di lavoro per il periodo {{DATA_ASSUNZIONE}} - {{DATA_FINE}}.

{{LINEA}}

Data: {{DATA_ODIERNA}}

Firma del Richiedente
________________________''',
    },

    # 9. LETTERA_ASSUNZIONE
    {
        'tipo': 'LETTERA_ASSUNZIONE',
        'codice': f'{CODICE_PREFIX}_LETTERA_ASSUNZIONE',
        'oggetto_titolo': 'Lettera di Assunzione - {{NOME_LAVORATORE}}',
        'corpo_testo': '''Lettera di Assunzione

Spett.le {{NOME_LAVORATORE}}
{{INDIRIZZO_LAVORATORE}}
{{PAESE_LAVORATORE}}

{{LINEA}}

Oggetto: Comunicazione di Assunzione

Con la presente, il/la Sig./Sig.ra {{NOME_DATORE}}
{{INDIRIZZO_DATORE}} - {{PAESE_DATORE}}
Codice Fiscale: {{CF_DATORE}}

comunica l'assunzione del/la Sig./Sig.ra {{NOME_LAVORATORE}}
(Codice Fiscale: {{CF_LAVORATORE}})
con decorrenza {{DATA_ASSUNZIONE}}.

{{LINEA}}

Tipologia contrattuale: {{TIPO_CONTRATTO}}
Orario di lavoro: {{ORE_SETTIMANALI}} ore settimanali ({{ORE_MENSILI}} ore mensili)
Livello CCNL: {{LIVELLO_CCNL}}
Paga Base: {{PAGA_BASE}}
Codice Rapporto INPS: {{CODICE_RAPPORTO_INPS}}

{{LINEA}}

Progetto: {{TIPO_PROGETTO}}
Beneficiario: {{NOME_BENEFICIARIO}}

Il presente rapporto di lavoro è regolato dal CCNL di categoria
e dalle disposizioni legislative e contrattuali vigenti.

{{LINEA}}

Data: {{DATA_ODIERNA}}

Firma del Datore
________________________

Firma del Lavoratore per accettazione
________________________''',
    },

    # 10. LETTERA_LICENZIAMENTO
    {
        'tipo': 'LETTERA_LICENZIAMENTO',
        'codice': f'{CODICE_PREFIX}_LETTERA_LICENZIAMENTO',
        'oggetto_titolo': 'Lettera di Licenziamento - {{NOME_LAVORATORE}}',
        'corpo_testo': '''Lettera di Licenziamento

Spett.le {{NOME_LAVORATORE}}
{{INDIRIZZO_LAVORATORE}}
{{PAESE_LAVORATORE}}

{{LINEA}}

Oggetto: Comunicazione di Licenziamento

Il/La sottoscritto/a {{NOME_DATORE}}
{{INDIRIZZO_DATORE}} - {{PAESE_DATORE}}
Codice Fiscale: {{CF_DATORE}}

con la presente comunica il licenziamento del/la Sig./Sig.ra
{{NOME_LAVORATORE}} (Codice Fiscale: {{CF_LAVORATORE}}).

{{LINEA}}

Il rapporto di lavoro, iniziato in data {{DATA_ASSUNZIONE}},
cesserà in data {{DATA_FINE}}.

Tipologia contratto: {{TIPO_CONTRATTO}}

Il lavoratore avrà diritto al trattamento di fine rapporto (TFR)
e agli altri compensi maturati e non ancora corrisposti.

{{LINEA}}

Data: {{DATA_ODIERNA}}

Firma del Datore
________________________

Ricevuta dal Lavoratore
________________________''',
    },

    # 11. LETTERA_DIMISSIONI
    {
        'tipo': 'LETTERA_DIMISSIONI',
        'codice': f'{CODICE_PREFIX}_LETTERA_DIMISSIONI',
        'oggetto_titolo': 'Lettera di Dimissioni - {{NOME_LAVORATORE}}',
        'corpo_testo': '''Lettera di Dimissioni

Spett.le {{NOME_DATORE}}
{{INDIRIZZO_DATORE}}
{{PAESE_DATORE}}

{{LINEA}}

Oggetto: Comunicazione di Dimissioni

Il/La sottoscritto/a {{NOME_LAVORATORE}}
{{INDIRIZZO_LAVORATORE}} - {{PAESE_LAVORATORE}}
Codice Fiscale: {{CF_LAVORATORE}}

con la presente rassegna le proprie dimissioni dal rapporto di lavoro
in essere con decorrenza {{DATA_FINE}}.

{{LINEA}}

Il rapporto di lavoro era iniziato in data {{DATA_ASSUNZIONE}}
con la qualifica di {{TIPO_CONTRATTO}}.

Si richiede il saldo di quanto maturato (TFR, ferie non godute,
rateo 13ma mensilità, ecc.).

{{LINEA}}

Data: {{DATA_ODIERNA}}

Firma del Lavoratore
________________________''',
    },

    # 12. DEROGA_TFR
    {
        'tipo': 'DEROGA_TFR',
        'codice': f'{CODICE_PREFIX}_DEROGA_TFR',
        'oggetto_titolo': 'Deroga Anticipazione TFR - {{NOME_DATORE}} / {{NOME_LAVORATORE}}',
        'corpo_testo': '''DEROGA CONCORDATA ANTICIPAZIONE TFR

Il/La sottoscritto/a {{NOME_DATORE}}
{{INDIRIZZO_DATORE}} - {{PAESE_DATORE}}
Codice Fiscale: {{CF_DATORE}}

e

Il/La sottoscritto/a {{NOME_LAVORATORE}}
{{INDIRIZZO_LAVORATORE}} - {{PAESE_LAVORATORE}}
Codice Fiscale: {{CF_LAVORATORE}}

CONVENGONO E STIPULANO

la presente deroga per l'anticipazione del Trattamento di Fine
Rapporto (TFR) relativo al rapporto di lavoro in essere.

{{LINEA}}

Tipo contratto: {{TIPO_CONTRATTO}}
Data assunzione: {{DATA_ASSUNZIONE}}
Progetto: {{TIPO_PROGETTO}}
Beneficiario: {{NOME_BENEFICIARIO}}

{{LINEA}}

Il datore di lavoro {{NOME_DATORE}} autorizza l'anticipazione del
TFR maturato dal lavoratore {{NOME_LAVORATORE}}.

{{LINEA}}

Data: {{DATA_ODIERNA}}

Firma del Datore
________________________

Firma del Lavoratore
________________________''',
    },

    # 13. LETTERA_LIBERA
    {
        'tipo': 'LETTERA_LIBERA',
        'codice': f'{CODICE_PREFIX}_LETTERA_LIBERA',
        'oggetto_titolo': 'Lettera - {{NOME_DATORE}} / {{NOME_LAVORATORE}}',
        'corpo_testo': '''Lettera

Mittente: {{NOME_DATORE}}
{{INDIRIZZO_DATORE}}
{{PAESE_DATORE}}
Email: {{MAIL_DATORE}}
Tel: {{TELEFONO_DATORE}}

{{LINEA}}

Destinatario: {{NOME_LAVORATORE}}
{{INDIRIZZO_LAVORATORE}}
{{PAESE_LAVORATORE}}

{{LINEA}}

Data: {{DATA_ODIERNA}}
Luogo: {{PAESE_DATORE}}

{{LINEA}}

Oggetto: Comunicazione relativa al contratto {{TIPO_CONTRATTO}}
del {{DATA_ASSUNZIONE}} - Progetto {{TIPO_PROGETTO}}
a favore di {{NOME_BENEFICIARIO}}

{{LINEA}}

Il sottoscritto {{NOME_DATORE}}, in relazione al rapporto di lavoro
con il/la Sig./Sig.ra {{NOME_LAVORATORE}} per il progetto
{{TIPO_PROGETTO}} a favore del beneficiario {{NOME_BENEFICIARIO}},

COMUNICA

quanto segue:

[INSERIRE TESTO DELLA COMUNICAZIONE]

{{LINEA}}

Cordiali saluti.

{{NOME_DATORE}}''',
    },

    # 14. NOTE FOOTER MAIL
    {
        'tipo': 'TESTO_PROGRAMMA',
        'codice': f'{CODICE_PREFIX}_NOTE_FOOTER_MAIL',
        'oggetto_titolo': 'Note Footer Mail (automatico)',
        'corpo_testo': '''Si ringrazia per la cortese attenzione e si porgono cordiali saluti.

{{NOME_STUDIO}}
{{TELEFONO_STUDIO}} | {{EMAIL_STUDIO}}''',
    },

    # 15. FIRMA EMAIL
    {
        'tipo': 'TESTO_PROGRAMMA',
        'codice': f'{CODICE_PREFIX}_FIRMA_EMAIL',
        'oggetto_titolo': 'Firma Email (automatico)',
        'corpo_testo': '''{{NOME_STUDIO}}
{{INDIRIZZO_DATORE}} - {{PAESE_DATORE}}
Tel: {{TELEFONO_STUDIO}} | Email: {{EMAIL_STUDIO}} | IBAN: {{IBAN_STUDIO}}''',
    },

    # 16. TOP_DOCUMENTO — Intestazione documento
    {
        'tipo': 'TOP_DOCUMENTO',
        'codice': f'{CODICE_PREFIX}_TOP_DOCUMENTO',
        'oggetto_titolo': 'Top Documento predefinito',
        'corpo_testo': '''<table style="width:100%; border-collapse:collapse; margin-bottom:12px; font-size:9pt;">
<tr><td style="padding:4px 8px; background:#f5f5f5; font-weight:bold; width:25%;">Datore</td><td style="padding:4px 8px; width:75%;">{{NOME_DATORE}} - CF {{CF_DATORE}}</td></tr>
<tr><td style="padding:4px 8px; background:#f5f5f5; font-weight:bold;">Lavoratore</td><td style="padding:4px 8px;">{{NOME_LAVORATORE}} - CF {{CF_LAVORATORE}}</td></tr>
<tr><td style="padding:4px 8px; background:#f5f5f5; font-weight:bold;">Contratto</td><td style="padding:4px 8px;">{{TIPO_CONTRATTO}} \u2014 {{ORE_SETTIMANALI}} h/sett</td></tr>
<tr><td style="padding:4px 8px; background:#f5f5f5; font-weight:bold;">Periodo</td><td style="padding:4px 8px;">{{DATA_ASSUNZIONE}} - {{DATA_FINE}}</td></tr>
</table>''',
    },

    # 17. FOOTER_DOCUMENTO — Footer documento (fondo ultima pagina)
    {
        'tipo': 'FOOTER_DOCUMENTO',
        'codice': f'{CODICE_PREFIX}_FOOTER_DOCUMENTO',
        'oggetto_titolo': 'Footer Documento predefinito',
        'corpo_testo': '''<div style="border-top:1px solid #ccc; padding-top:8px; font-size:8pt; color:#666; margin-top:20px;">
<table style="width:100%; border-collapse:collapse; font-size:8pt;">
<tr><td style="padding:2px 4px;"><strong>{{NOME_STUDIO}}</strong></td><td style="padding:2px 4px; text-align:right;">Tel: {{TELEFONO_STUDIO}} \u2014 Mail: {{EMAIL_STUDIO}}</td></tr>
<tr><td style="padding:2px 4px;" colspan="2">IBAN: {{IBAN_STUDIO}}</td></tr>
</table>
</div>''',
    },

    # 18. BUSTA PAGA DEFAULT
    {
        'tipo': 'BUSTA_PAGA',
        'codice': f'{CODICE_PREFIX}_BUSTA_PAGA_DEFAULT',
        'oggetto_titolo': 'Busta Paga Default',
        'corpo_testo': '''<h2 style="text-align:center;">BUSTA PAGA</h2>
<p style="text-align:center;">{{BUSTA_MESE_NOME}} {{BUSTA_ANNO}}</p>

<h3>Datore: {{NOME_DATORE}}</h3>
<h3>Lavoratore: {{NOME_LAVORATORE}}</h3>

{{BUSTA_CONTENUTO}}''',
    },

    # 19-24. LISTE STAMPE
    {
        'tipo': 'LISTA_STAMPA',
        'codice': 'DATORI',
        'oggetto_titolo': '',
        'corpo_testo': '''<h2 style="text-align:center; margin-bottom:4px;">{{INTESTAZIONE}}</h2>
<p style="text-align:center; font-size:8pt; color:#666; margin-bottom:8px;">Generato il {{DATA_ODIERNA}}</p>
{{LISTA_TABELLA}}
<p style="text-align:right; font-size:7pt; color:#999; margin-top:4px;">{{NOME_STUDIO}}</p>''',
    },
    {
        'tipo': 'LISTA_STAMPA',
        'codice': 'LAVORATORI',
        'oggetto_titolo': '',
        'corpo_testo': '''<h2 style="text-align:center; margin-bottom:4px;">{{INTESTAZIONE}}</h2>
<p style="text-align:center; font-size:8pt; color:#666; margin-bottom:8px;">Generato il {{DATA_ODIERNA}}</p>
{{LISTA_TABELLA}}
<p style="text-align:right; font-size:7pt; color:#999; margin-top:4px;">{{NOME_STUDIO}}</p>''',
    },
    {
        'tipo': 'LISTA_STAMPA',
        'codice': 'BENEFICIARI',
        'oggetto_titolo': '',
        'corpo_testo': '''<h2 style="text-align:center; margin-bottom:4px;">{{INTESTAZIONE}}</h2>
<p style="text-align:center; font-size:8pt; color:#666; margin-bottom:8px;">Generato il {{DATA_ODIERNA}}</p>
{{LISTA_TABELLA}}
<p style="text-align:right; font-size:7pt; color:#999; margin-top:4px;">{{NOME_STUDIO}}</p>''',
    },
    {
        'tipo': 'LISTA_STAMPA',
        'codice': 'PROGETTI',
        'oggetto_titolo': '',
        'corpo_testo': '''<h2 style="text-align:center; margin-bottom:4px;">{{INTESTAZIONE}}</h2>
<p style="text-align:center; font-size:8pt; color:#666; margin-bottom:8px;">Generato il {{DATA_ODIERNA}}</p>
{{LISTA_TABELLA}}
<p style="text-align:right; font-size:7pt; color:#999; margin-top:4px;">{{NOME_STUDIO}}</p>''',
    },
    {
        'tipo': 'LISTA_STAMPA',
        'codice': 'CONTRATTI_ATTIVI',
        'oggetto_titolo': '',
        'corpo_testo': '''<h2 style="text-align:center; margin-bottom:4px;">{{INTESTAZIONE}}</h2>
<p style="text-align:center; font-size:8pt; color:#666; margin-bottom:8px;">Generato il {{DATA_ODIERNA}}</p>
{{LISTA_TABELLA}}
<p style="text-align:right; font-size:7pt; color:#999; margin-top:4px;">{{NOME_STUDIO}}</p>''',
    },
    {
        'tipo': 'LISTA_STAMPA',
        'codice': 'PAGOPA_INPS',
        'oggetto_titolo': '',
        'corpo_testo': '''<h2 style="text-align:center; margin-bottom:4px;">{{INTESTAZIONE}}</h2>
<p style="text-align:center; font-size:8pt; color:#666; margin-bottom:8px;">Generato il {{DATA_ODIERNA}}</p>
{{LISTA_TABELLA}}
<p style="text-align:right; font-size:7pt; color:#999; margin-top:4px;">{{NOME_STUDIO}}</p>''',
    },
]


class Command(BaseCommand):
    help = 'Crea template automatici per i tipi di ModelloDocumentale ancora vuoti'

    def handle(self, *args, **options):
        created = 0
        skipped = 0
        for tpl in TEMPLATES:
            if ModelloDocumentale.objects.filter(codice=tpl['codice']).exists():
                self.stdout.write(self.style.WARNING(
                    f"SKIP {tpl['tipo']}: '{tpl['codice']}' già esistente"
                ))
                skipped += 1
                continue
            ModelloDocumentale.objects.create(
                tipo=tpl['tipo'],
                codice=tpl['codice'],
                oggetto_titolo=tpl['oggetto_titolo'],
                corpo_testo=tpl['corpo_testo'],
            )
            self.stdout.write(self.style.SUCCESS(
                f"CREATO {tpl['tipo']}: {tpl['codice']}"
            ))
            created += 1

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\nFatto: {created} creati, {skipped} saltati"
        ))
