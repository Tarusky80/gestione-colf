"""Smoke test: verifica che ogni URL name generi 200 per admin loggato."""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from paghe.models import OpzioniSoftware


class UrlSmokeTest(TestCase):
    """Visita ogni URL dell'app con admin loggato, verifica 200/302."""

    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser('admin', 'admin@test.it', 'admin123')
        OpzioniSoftware.objects.create()

    def setUp(self):
        self.c = Client()
        self.c.login(username='admin', password='admin123')

    def test_url_names(self):
        urls = [
            'dashboard', 'about_page', 'scorciatoie',
            'datori_list', 'lavoratori_list', 'beneficiari_list',
            'contratti_list', 'contratti_cessati_list',
            'backup_page', 'impostazioni_page',
            'eliminati_list', 'comparatore_page',
            'calcoli_list', 'calcoli_non_convivente',
            'calcoli_conviventi_ccnl', 'calcoli_inverso',
            'calcoli_notturno', 'calcoli_malattia',
            'calcoli_tfr', 'calcoli_sostituzione',
            'buste_archivio', 'buste_paga_massivo',
            'stampe_invii', 'agenda_page',
            'documenti_list', 'documentale_root',
            'liste_list', 'checklist_mensile',
            'audit_log', 'configurazioni_servizi',
            'iscrizione_inps', 'cessazione_inps',
            'crea_pagopa', 'crea_pagopa_manuale',
            'redigere_cu', 'log_inps',
            'riepilogo_invio_list', 'export_uniemens_csv',
            'richieste_modifica_list',
        ]
        errors = []
        for name in urls:
            try:
                url = reverse(name)
                resp = self.c.get(url)
                if resp.status_code not in (200, 302, 301):
                    errors.append(f"{name} ({url}): {resp.status_code}")
            except Exception as e:
                errors.append(f"{name}: {e}")
        self.assertEqual([], errors, f"Errori URL:\n" + "\n".join(errors))
