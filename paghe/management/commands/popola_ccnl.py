"""Popola il database con gli articoli del CCNL dal fixture JSON."""
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Carica gli articoli del CCNL dal fixture ccnl_articoli.json"

    def handle(self, *args, **options):
        fixture_path = Path(__file__).resolve().parent.parent.parent / 'fixtures' / 'ccnl_articoli.json'
        if not fixture_path.exists():
            self.stderr.write(f"Fixture non trovato: {fixture_path}")
            return
        call_command('loaddata', str(fixture_path))
        self.stdout.write(self.style.SUCCESS(f"CCNL caricato con successo da {fixture_path}"))
