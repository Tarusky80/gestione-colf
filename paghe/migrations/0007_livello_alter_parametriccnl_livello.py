import django.db.models.deletion
from django.db import migrations, models


def popola_livelli(apps, schema_editor):
    Livello = apps.get_model('paghe', 'Livello')
    ParametriCCNL = apps.get_model('paghe', 'ParametriCCNL')
    codici_esistenti = ParametriCCNL.objects.values_list('livello', flat=True).distinct()
    mapping = {}
    for codice in codici_esistenti:
        if codice:
            obj, _ = Livello.objects.get_or_create(codice=codice, defaults={'colore': '#5E6AD2'})
            mapping[codice] = obj.pk
    for p in ParametriCCNL.objects.all():
        if p.livello in mapping:
            ParametriCCNL.objects.filter(pk=p.pk).update(livello_new_id=mapping[p.livello])


class Migration(migrations.Migration):

    dependencies = [
        ('paghe', '0006_tipoprogettoregionale_colore'),
    ]

    operations = [
        # 1. Create Livello model
        migrations.CreateModel(
            name='Livello',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codice', models.CharField(max_length=5, unique=True, verbose_name='CODICE')),
                ('colore', models.CharField(default='#5E6AD2', max_length=7, verbose_name='COLORE')),
            ],
            options={
                'verbose_name_plural': 'Livelli',
                'ordering': ['codice'],
            },
        ),
        # 2. Add nullable FK column (keep old livello CharField)
        migrations.AddField(
            model_name='parametriccnl',
            name='livello_new',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='paghe.livello', verbose_name='LIVELLO'),
        ),
        # 3. Populate Livello table and set FK values
        migrations.RunPython(popola_livelli),
        # 4. Remove old livello CharField
        migrations.RemoveField(
            model_name='parametriccnl',
            name='livello',
        ),
        # 5. Rename livello_new to livello
        migrations.RenameField(
            model_name='parametriccnl',
            old_name='livello_new',
            new_name='livello',
        ),
        # 6. Make FK non-nullable (no longer conflicts since old data is migrated)
        migrations.AlterField(
            model_name='parametriccnl',
            name='livello',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='paghe.livello', verbose_name='LIVELLO'),
        ),
    ]
