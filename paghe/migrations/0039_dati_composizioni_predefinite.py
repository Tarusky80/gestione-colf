from django.db import migrations


def crea_composizioni_predefinite(apps, schema_editor):
    ModelloComposizione = apps.get_model('paghe', 'ModelloComposizione')
    predefiniti = [
        {
            'nome': 'Pacchetto Mensile',
            'is_default': True,
            'note': 'Busta paga standard + pagina bianca + CUD annuale. Utile per emissione cedolini mensili con riepilogo annuale.',
            'elementi': [
                {'tipo': 'STANDARD', 'label': 'Busta Paga Standard', 'template_pk': None},
                {'tipo': 'PAGINA_BIANCA', 'label': 'Pagina Bianca'},
                {'tipo': 'CUD', 'label': 'CUD', 'template_pk': None},
            ]
        },
        {
            'nome': 'Pacchetto Assunzione',
            'is_default': False,
            'note': 'Contratto + busta paga standard + lettera assunzione. Per nuove assunzioni.',
            'elementi': [
                {'tipo': 'CONTRATTO', 'label': 'Contratto', 'template_pk': None},
                {'tipo': 'PAGINA_BIANCA', 'label': 'Pagina Bianca'},
                {'tipo': 'STANDARD', 'label': 'Busta Paga Standard', 'template_pk': None},
                {'tipo': 'LETTERA_ASSUNZIONE', 'label': 'Lettera Assunzione', 'template_pk': None},
            ]
        },
        {
            'nome': 'Pacchetto Cessazione',
            'is_default': False,
            'note': 'TFR liquidazione + CUD + lettera licenziamento. Per fine rapporto.',
            'elementi': [
                {'tipo': 'TFR_LIQUIDAZIONE', 'label': 'Liquidazione TFR', 'template_pk': None},
                {'tipo': 'CUD', 'label': 'CUD', 'template_pk': None},
                {'tipo': 'LETTERA_LICENZIAMENTO', 'label': 'Lettera Licenziamento', 'template_pk': None},
            ]
        },
        {
            'nome': 'Documenti Annuali',
            'is_default': False,
            'note': 'CUD + riepilogo rapporto + pagina bianca + lettera libera. Per chiusura anno.',
            'elementi': [
                {'tipo': 'CUD', 'label': 'CUD', 'template_pk': None},
                {'tipo': 'RIEPILOGO_RAPPORTO', 'label': 'Riepilogo Rapporto', 'template_pk': None},
                {'tipo': 'PAGINA_BIANCA', 'label': 'Pagina Bianca'},
                {'tipo': 'LETTERA_LIBERA', 'label': 'Lettera Libera', 'template_pk': None},
            ]
        },
    ]
    for data in predefiniti:
        ModelloComposizione.objects.get_or_create(
            nome=data['nome'],
            defaults={
                'elementi': data['elementi'],
                'note': data['note'],
                'is_default': data['is_default'],
            }
        )


class Migration(migrations.Migration):

    dependencies = [
        ('paghe', '0038_modellocomposizione'),
    ]

    operations = [
        migrations.RunPython(crea_composizioni_predefinite, migrations.RunPython.noop),
    ]
