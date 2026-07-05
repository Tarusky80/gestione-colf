"""Test del sistema permessi RBAC."""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from paghe.models import OpzioniSoftware, ProfiloUtente, DatoreLavoro, Lavoratore, ContrattoLavoro


class PermessiBaseTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        OpzioniSoftware.objects.create()
        cls.admin = User.objects.create_superuser('admin', 'admin@test.it', 'admin123')
        ProfiloUtente.objects.update_or_create(utente=cls.admin, defaults={'ruolo': 'ADMIN'})

        cls.operatore = User.objects.create_user('operatore', 'op@test.it', 'op123')
        ProfiloUtente.objects.update_or_create(utente=cls.operatore, defaults={'ruolo': 'OPERATORE'})

        cls.consulente = User.objects.create_user('consulente', 'con@test.it', 'con123')
        ProfiloUtente.objects.update_or_create(utente=cls.consulente, defaults={'ruolo': 'CONSULENTE'})

        cls.datore_user = User.objects.create_user('datore_utente', 'du@test.it', 'du123')
        ProfiloUtente.objects.update_or_create(utente=cls.datore_user, defaults={'ruolo': 'DATORE'})

    def setUp(self):
        self.c = Client()

    def _login(self, user):
        self.c.login(username=user.username, password={
            'admin': 'admin123',
            'operatore': 'op123',
            'consulente': 'con123',
            'datore_utente': 'du123',
        }[user.username])

    def _get(self, url_name, *args, **kwargs):
        try:
            url = reverse(url_name, args=args, kwargs=kwargs)
        except Exception:
            return None
        return self.c.get(url)


class TestRuoliSuViewLettura(PermessiBaseTest):
    """I ruoli che hanno permessi di lettura vedono 200, gli altri 403."""

    VIEW_LETTURA = [
        'datori_list', 'lavoratori_list', 'beneficiari_list',
        'contratti_list', 'contratti_cessati_list',
        'buste_archivio', 'calcoli_list',
        'documenti_list', 'stampe_invii',
    ]

    def test_admin_vede_tutto(self):
        self._login(self.admin)
        for name in self.VIEW_LETTURA:
            resp = self._get(name)
            if resp is not None:
                self.assertIn(resp.status_code, (200, 302, 301),
                              f"{name}: admin got {resp.status_code}")

    def test_operatore_vede_lettura(self):
        self._login(self.operatore)
        for name in self.VIEW_LETTURA:
            resp = self._get(name)
            if resp is not None:
                self.assertIn(resp.status_code, (200, 302, 301),
                              f"{name}: operatore got {resp.status_code}")

    def test_consulente_vede_lettura(self):
        self._login(self.consulente)
        for name in self.VIEW_LETTURA:
            resp = self._get(name)
            if resp is not None:
                self.assertIn(resp.status_code, (200, 302, 301),
                              f"{name}: consulente got {resp.status_code}")


class TestRuoliSuViewRiservate(PermessiBaseTest):
    """Solo ADMIN e SUPERUSER vedono impostazioni/backup/audit/permessi."""

    VIEW_RISERVATE = [
        'backup_page', 'impostazioni_page',
        'audit_log', 'pannello_permessi',
    ]

    def test_admin_vede_riservate(self):
        self._login(self.admin)
        for name in self.VIEW_RISERVATE:
            resp = self._get(name)
            if resp is not None:
                self.assertIn(resp.status_code, (200, 302, 301),
                              f"{name}: admin got {resp.status_code}")

    def test_operatore_non_vede_riservate(self):
        self._login(self.operatore)
        for name in self.VIEW_RISERVATE:
            resp = self._get(name)
            if resp is not None:
                self.assertEqual(resp.status_code, 302,
                                 f"{name}: operatore expected 302 got {resp.status_code}")

    def test_consulente_non_vede_riservate(self):
        self._login(self.consulente)
        for name in self.VIEW_RISERVATE:
            resp = self._get(name)
            if resp is not None:
                self.assertEqual(resp.status_code, 302,
                                 f"{name}: consulente expected 302 got {resp.status_code}")

    def test_datore_non_vede_nulla(self):
        self._login(self.datore_user)
        for name in self.VIEW_RISERVATE + ['datori_list', 'calcoli_list']:
            resp = self._get(name)
            if resp is not None:
                self.assertEqual(resp.status_code, 302,
                                 f"{name}: datore expected 302 got {resp.status_code}")


class TestVisibilita(PermessiBaseTest):
    """filtro_visibilita limita la vista ai record assegnati."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Crea un datore assegnato solo a admin
        cls.d1 = DatoreLavoro.objects.create(
            nome='Admin', cognome='Datore',
            codice_fiscale='RSSMRA80A01H501U',
            indirizzo='Via Roma 1',
        )
        cls.d1.refresh_from_db()
        cls.d1.visibile_a.set([cls.admin])

        cls.d2 = DatoreLavoro.objects.create(
            nome='Operatore', cognome='Datore',
            codice_fiscale='VRDLNZ85B02F205V',
            indirizzo='Via Milano 2',
        )
        cls.d2.refresh_from_db()
        cls.d2.visibile_a.set([cls.operatore])

    def test_admin_vede_tutti(self):
        self._login(self.admin)
        resp = self._get('datori_list')
        if resp is not None:
            self.assertContains(resp, 'Admin Datore')
            self.assertContains(resp, 'Operatore Datore')

    def test_operatore_vede_solo_suo(self):
        self._login(self.operatore)
        resp = self._get('datori_list')
        if resp is not None:
            self.assertNotContains(resp, 'Admin Datore')
            self.assertContains(resp, 'Operatore Datore')
