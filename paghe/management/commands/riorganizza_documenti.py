from django.core.management.base import BaseCommand
from paghe.models import DocumentoArchiviato
from paghe.views import _get_cartella_documenti, _nome_cartella_contratto
import os
import shutil

class Command(BaseCommand):
    help = 'Sposta i documenti esistenti nelle sottocartelle per contratto'

    def handle(self, *args, **options):
        from django.conf import settings
        opzioni_model = __import__('paghe.models', fromlist=['OpzioniSoftware']).OpzioniSoftware
        opzioni = opzioni_model.objects.first()
        opzioni.cartella_documenti if opzioni and opzioni.cartella_documenti else os.path.join(settings.MEDIA_ROOT, 'documenti')

        spostati = 0
        gia_ok = 0
        non_trovati = 0
        totali = 0

        for doc in DocumentoArchiviato.objects.iterator():
            totali += 1
            vecchio_path = doc.file_path
            if not vecchio_path:
                continue

            nuova_cartella = _get_cartella_documenti(doc.contratto)
            vecchio_nome = os.path.basename(vecchio_path)
            nuovo_path = os.path.join(nuova_cartella, vecchio_nome)

            if os.path.normpath(vecchio_path) == os.path.normpath(nuovo_path):
                gia_ok += 1
                continue

            if os.path.exists(vecchio_path):
                os.makedirs(nuova_cartella, exist_ok=True)
                shutil.move(vecchio_path, nuovo_path)
                doc.file_path = nuovo_path
                doc.save(update_fields=['file_path'])
                spostati += 1
                self.stdout.write(f"  Spostato {vecchio_nome} -> {_nome_cartella_contratto(doc.contratto)}")
            else:
                doc.file_path = nuovo_path
                doc.save(update_fields=['file_path'])
                non_trovati += 1
                self.stdout.write(f"  [{non_trovati}] File non trovato: {vecchio_path}")

        self.stdout.write(self.style.SUCCESS(
            f"\nRiorganizzazione completata: {totali} documenti esaminati, "
            f"{spostati} spostati, {gia_ok} già a posto, {non_trovati} file non trovati (path aggiornato)."
        ))
