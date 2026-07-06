"""Comando management per creare backup e pulire copie vecchie."""
import os
from django.core.management.base import BaseCommand
from django.utils import timezone
from paghe.models import GestoreBackup


class Command(BaseCommand):
    help = 'Crea un backup del database con pulizia automatica dei vecchi backup.'

    def add_arguments(self, parser):
        parser.add_argument('--tipo', type=str, default='COMPLETO', choices=['COMPLETO', 'ANAGRAFICHE', 'CONTRATTI', 'PARAMETRI'], help='Tipo di backup')
        parser.add_argument('--note', type=str, default='Backup da comando management', help='Note opzionali')
        parser.add_argument('--retenzione', type=int, default=None, help='Giorni ritenzione (default: da OpzioniSoftware o 30)')

    def handle(self, *args, **options):
        tipo = options['tipo']
        note = options['note']
        giorni = options['retenzione']

        backup = GestoreBackup.objects.create(tipo_backup=tipo, note_opzionali=note)

        if not backup.file_json:
            self.stdout.write(self.style.ERROR('Errore: file backup non generato.'))
            return

        dimensione_json = os.path.getsize(backup.file_json) if os.path.isfile(backup.file_json) else 0
        dimensione_db = os.path.getsize(backup.file_db) if backup.file_db and os.path.isfile(backup.file_db) else 0

        self.stdout.write(self.style.SUCCESS('Backup creato con successo:'))
        self.stdout.write(f'  JSON: {backup.file_json} ({_fmt_size(dimensione_json)})')
        if backup.file_db:
            self.stdout.write(f'  ZIP:  {backup.file_db} ({_fmt_size(dimensione_db)})')
        self.stdout.write(f'  Tipo: {tipo}')
        self.stdout.write(f'  Data: {timezone.now().strftime("%d/%m/%Y %H:%M")}')

        puliti = GestoreBackup._pulisci_backup_vecchi(giorni)
        if puliti > 0:
            self.stdout.write(self.style.WARNING(f'Puliti {puliti} backup precedenti.'))
        else:
            self.stdout.write('Nessun backup vecchio da pulire.')

        self.stdout.write(self.style.SUCCESS('Operazione completata.'))


def _fmt_size(size):
    if size < 1024:
        return f'{size} B'
    elif size < 1024 * 1024:
        return f'{size / 1024:.1f} KB'
    else:
        return f'{size / (1024 * 1024):.2f} MB'
