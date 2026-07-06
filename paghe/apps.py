import sys
import os
import warnings
import logging
import subprocess
import threading
import atexit
from pathlib import Path
from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)

_scheduler_started = False


class PagheConfig(AppConfig):
    name = 'paghe'

    def ready(self):
        """Avvia verifiche in thread separato per non bloccare l'avvio del server."""
        global _scheduler_started
        # Verifica dipendenze in background (non blocca l'avvio)
        t = threading.Thread(target=self._verifica_tutto_async, daemon=True)
        t.start()
        if not _scheduler_started:
            self._avvia_scheduler()
            _scheduler_started = True

    def _verifica_tutto_async(self):
        """Esegue tutte le verifiche in ordine."""
        logger.info('=' * 60)
        logger.info('  VERIFICA DIPENDENZE E SETUP')
        logger.info('=' * 60)
        self._verifica_requirements()
        self._verifica_migrazioni()
        self._verifica_playwright()
        self._verifica_chromedriver()
        logger.info('=' * 60)
        logger.info('  VERIFICA COMPLETATA — Sistema pronto')
        logger.info('=' * 60)

    def _avvia_scheduler(self):
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            self._sched = BackgroundScheduler()
            self._sched.add_job(
                self._backup_automatico,
                'cron',
                hour=3,
                minute=0,
                id='backup_giornaliero',
                name='Backup automatico giornaliero',
                replace_existing=True,
            )
            self._sched.add_job(
                self._notifica_scadenze_settimanale,
                'cron',
                day_of_week='mon',
                hour=8,
                minute=0,
                id='notifica_scadenze_settimanale',
                name='Notifica scadenze settimanale',
                replace_existing=True,
            )
            self._sched.start()
            logger.info('[Scheduler] Backup automatico attivato (ogni giorno alle 03:00)')
            logger.info('[Scheduler] Notifica scadenze attivata (ogni lunedì alle 08:00)')
            atexit.register(self._ferma_scheduler)
        except Exception as e:
            logger.error('[Scheduler] ERRORE avvio: %s', e)

    def _ferma_scheduler(self):
        try:
            if hasattr(self, '_sched') and self._sched.running:
                self._sched.shutdown(wait=False)
                logger.info('[Scheduler] Fermato con successo.')
        except Exception:
            pass

    def _backup_automatico(self):
        try:
            if not settings.configured:
                return
            from paghe.models import GestoreBackup
            GestoreBackup.objects.create(tipo_backup='COMPLETO', note_opzionali='Backup automatico schedulato')
            puliti = GestoreBackup._pulisci_backup_vecchi()
            msg = f'[Backup] Backup automatico completato.'
            if puliti > 0:
                msg += f' Puliti {puliti} backup precedenti.'
            logger.info(msg)
        except Exception as e:
            logger.error('[Backup] ERRORE: %s', e)

    def _notifica_scadenze_settimanale(self):
        try:
            from paghe.notifiche_scadenze import invia_notifiche_scadenze
            report = invia_notifiche_scadenze()
            logger.info('[Notifiche] Report settimanale: %s', report)
        except Exception as e:
            logger.error('[Notifiche] ERRORE nell\'invio settimanale: %s', e)

    def _verifica_requirements(self):
        """Legge requirements.txt e installa pacchetti mancanti."""
        from importlib.metadata import distribution, PackageNotFoundError
        req_file = Path(__file__).resolve().parent.parent / 'requirements.txt'
        if not req_file.exists():
            logger.info('[Setup] requirements.txt non trovato, skip')
            return
        logger.info('[Setup] Verifica pacchetti Python...')
        installati = 0
        with open(req_file) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                pkg_name = line.split('==')[0].split('>=')[0].split('~=')[0].strip()
                try:
                    distribution(pkg_name)
                    continue
                except PackageNotFoundError:
                    pass
                logger.info('[Setup] Installazione %s in corso...', line)
                subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', line],
                    check=True, stdout=sys.stdout, stderr=sys.stderr
                )
                logger.info('[Setup] %s installato.', pkg_name)
                installati += 1
        logger.info('[Setup] %d pacchetti verificati (%d installati)', installati, installati)

    def _verifica_migrazioni(self):
        """Esegue migrate se necessario (primo avvio o migrazioni pendenti)."""
        from django.db import connections
        from django.db.migrations.executor import MigrationExecutor
        from django.conf import settings

        db_path = settings.DATABASES['default']['NAME']
        if not os.path.exists(db_path):
            logger.info('[Setup] Database non ancora creato. Avvio migrate...')
            subprocess.run(
                [sys.executable, 'manage.py', 'migrate', '--run-syncdb'],
                cwd=settings.BASE_DIR,
                check=True, stdout=sys.stdout, stderr=sys.stderr
            )
            logger.info('[Setup] Database creato e migrazioni completate.')
            return

        try:
            connection = connections['default']
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            if plan:
                logger.info('[Setup] %d migrazioni pendenti. Esecuzione...', len(plan))
                subprocess.run(
                    [sys.executable, 'manage.py', 'migrate'],
                    cwd=settings.BASE_DIR,
                    check=True, stdout=sys.stdout, stderr=sys.stderr
                )
                logger.info('[Setup] Migrazioni completate.')
            else:
                logger.info('[Setup] Migrazioni OK (nessuna in sospeso)')
        except Exception as e:
            logger.warning('[Setup] Controllo migrazioni fallito: %s', e)

    def _verifica_playwright(self):
        logger.info('[Playwright] Controllo pacchetto Python...')
        try:
            from importlib.metadata import version as _v
            logger.info('[Playwright] OK (%s)', _v("playwright"))
        except ImportError:
            logger.warning('[Playwright] NON INSTALLATO')
            logger.info('[Playwright] Installazione in corso...')
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', 'playwright'],
                check=True, stdout=sys.stdout, stderr=sys.stderr
            )
            logger.info('[Playwright] Installato con successo.')

        logger.info('[Playwright] Controllo browser Chromium...')
        try:
            from playwright.sync_api import sync_playwright
            p = sync_playwright().start()
            executable_path = p.chromium.executable_path
            logger.info('[Playwright] OK (%s)', executable_path)
            p.stop()
        except Exception:
            logger.warning('[Playwright] NON INSTALLATO')
            logger.info('[Playwright] Installazione Chromium in corso...')
            subprocess.run(
                [sys.executable, '-m', 'playwright', 'install', 'chromium'],
                check=True, stdout=sys.stdout, stderr=sys.stderr
            )
            logger.info('[Playwright] Chromium installato con successo.')

    def _verifica_chromedriver(self):
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', 'Accessing the database during app initialization')
                from paghe.views._common_imports import get_opzioni
                opzioni = get_opzioni()
        except Exception:
            logger.info('[Chromedriver] Database non ancora disponibile (skip).')
            return
        if not opzioni or not opzioni.chromedriver_exe:
            logger.info('[Chromedriver] Nessun path configurato in OpzioniSoftware.')
            return

        path = Path(opzioni.chromedriver_exe)
        if not path.is_absolute():
            path = Path(__file__).resolve().parent.parent / path

        if path.exists():
            logger.info('[Chromedriver] OK (%s)', path)
            return

        logger.warning('[Chromedriver] NON TROVATO in: %s', path)
        logger.info('[Chromedriver] Download automatico in corso...')
        try:
            from importlib.metadata import distribution, PackageNotFoundError
            try:
                distribution('chromedriver_autoinstaller')
            except PackageNotFoundError:
                logger.info('[Chromedriver] Installazione chromedriver-autoinstaller...')
                subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', 'chromedriver-autoinstaller'],
                    check=True, stdout=sys.stdout, stderr=sys.stderr
                )
                logger.info('[Chromedriver] chromedriver-autoinstaller installato.')
        except Exception:
            pass
        try:
            import chromedriver_autoinstaller
            download_dir = str(path.parent)
            os.makedirs(download_dir, exist_ok=True)
            result = chromedriver_autoinstaller.install(path=download_dir)
            if result:
                logger.info('[Chromedriver] Scaricato in: %s', result)
                if result != str(path):
                    import shutil
                    shutil.copy2(result, str(path))
                    logger.info('[Chromedriver] Copiato in: %s', path)
            else:
                logger.error('[Chromedriver] ERRORE: download fallito (Chrome non installato?)')
        except Exception as e:
            logger.error('[Chromedriver] ERRORE: %s', e)
