from django.db import migrations

TIPI_DOCUMENTALI = [
    'CONTRATTO', 'CUD', 'CARTELLINA', 'RIEPILOGO_RAPPORTO',
    'LETTERA_ASSUNZIONE', 'LETTERA_LICENZIAMENTO', 'LETTERA_DIMISSIONI',
    'LETTERA_LIBERA', 'DEROGA_TFR', 'RICEVUTA', 'RICHIESTA_CUD',
    'PDF_INIZIO', 'PDF_FINE', 'PDF_RISCONTRO', 'LISTA_STAMPA',
]


def migra_testi_documentali(apps, schema_editor):
    TestoPreimpostato = apps.get_model('paghe', 'TestoPreimpostato')
    ModelloDocumentale = apps.get_model('paghe', 'ModelloDocumentale')
    DocumentoArchiviato = apps.get_model('paghe', 'DocumentoArchiviato')

    for tp in TestoPreimpostato.objects.filter(tipo__in=TIPI_DOCUMENTALI):
        modello, creato = ModelloDocumentale.objects.get_or_create(
            codice=tp.codice,
            defaults={
                'tipo': tp.tipo,
                'titolo': tp.oggetto_titolo or '',
                'corpo_testo': tp.corpo_testo or '',
                'note_interne': tp.note_interne or '',
            },
        )
        if not creato:
            continue
        DocumentoArchiviato.objects.filter(modello_testo=tp).update(modello_documentale=modello)


def inverti_migrazione(apps, schema_editor):
    ModelloDocumentale = apps.get_model('paghe', 'ModelloDocumentale')
    ModelloDocumentale.objects.filter(tipo__in=TIPI_DOCUMENTALI).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('paghe', '0062_modellodocumentale_and_more'),
    ]

    operations = [
        migrations.RunPython(migra_testi_documentali, inverti_migrazione),
    ]
