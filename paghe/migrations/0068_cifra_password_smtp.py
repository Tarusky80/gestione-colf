from django.db import migrations
from django.core import signing

_SALT = 'smtp_password'


def cifra_password(apps, schema_editor):
    OpzioniSoftware = apps.get_model('paghe', 'OpzioniSoftware')
    for row in OpzioniSoftware.objects.all():
        raw = row.email_smtp_password
        if raw and not raw.startswith('gAAAAA'):
            try:
                row.email_smtp_password = signing.dumps(raw, salt=_SALT)
                row.save(update_fields=['email_smtp_password'])
            except Exception:
                pass


def decifra_password(apps, schema_editor):
    OpzioniSoftware = apps.get_model('paghe', 'OpzioniSoftware')
    for row in OpzioniSoftware.objects.all():
        encrypted = row.email_smtp_password
        if encrypted and encrypted.startswith('gAAAAA'):
            try:
                row.email_smtp_password = signing.loads(encrypted, salt=_SALT)
                row.save(update_fields=['email_smtp_password'])
            except Exception:
                pass


class Migration(migrations.Migration):

    dependencies = [
        ('paghe', '0067_remove_testopreimpostato'),
    ]

    operations = [
        migrations.RunPython(cifra_password, decifra_password),
    ]
