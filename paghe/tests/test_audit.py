"""Test per audit log: signals, middleware, _log_audit."""
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from paghe.models import AuditLog, OpzioniSoftware, DatoreLavoro
from paghe.signals import _log_audit, _serializza
from core.audit_middleware import _audit_thread, get_audit_user, get_audit_ip
from decimal import Decimal


class LogAuditTest(TestCase):
    def test_crea_audit_log_senza_utente(self):
        _log_audit('TestModel', 1, 'CREAZIONE', 'test')
        self.assertEqual(AuditLog.objects.count(), 1)
        entry = AuditLog.objects.first()
        self.assertEqual(entry.modello_coinvolto, 'TestModel')
        self.assertEqual(entry.pk_oggetto, '1')
        self.assertEqual(entry.azione, 'CREAZIONE')
        self.assertEqual(entry.dettagli, 'test')
        self.assertIsNone(entry.utente)

    def test_crea_audit_log_con_utente_valido(self):
        u = User.objects.create_user('testuser')
        _audit_thread.user = u
        _log_audit('TestModel', 1, 'MODIFICA')
        entry = AuditLog.objects.first()
        self.assertEqual(entry.utente, u)

    def test_crea_audit_log_utente_inesistente(self):
        fake = User(pk=999, username='fantasma')
        _audit_thread.user = fake
        _log_audit('TestModel', 1, 'MODIFICA')
        entry = AuditLog.objects.first()
        self.assertIsNone(entry.utente)

    def test_crea_audit_log_con_ip(self):
        _audit_thread.ip = '192.168.1.1'
        _log_audit('TestModel', 1, 'CREAZIONE')
        entry = AuditLog.objects.first()
        self.assertEqual(entry.indirizzo_ip, '192.168.1.1')

    def test_dettagli_troncati_a_255(self):
        _log_audit('TestModel', 1, 'CREAZIONE', 'x' * 300)
        entry = AuditLog.objects.first()
        self.assertEqual(len(entry.dettagli), 255)

    def test_pk_oggetto_vuoto_se_none(self):
        _log_audit('TestModel', None, 'AZIONE')
        entry = AuditLog.objects.first()
        self.assertEqual(entry.pk_oggetto, '')

    def test_dati_precedenti_successivi_json(self):
        _log_audit('TestModel', 1, 'MODIFICA',
                    dati_prec={'campo': 'vecchio'},
                    dati_succ={'campo': 'nuovo'})
        entry = AuditLog.objects.first()
        self.assertEqual(entry.dati_precedenti, {'campo': 'vecchio'})
        self.assertEqual(entry.dati_successivi, {'campo': 'nuovo'})


class SignalAuditTest(TestCase):
    def test_post_save_crea_audit_log(self):
        OpzioniSoftware.objects.create()
        self.assertTrue(AuditLog.objects.filter(azione='CREAZIONE',
                       modello_coinvolto='OpzioniSoftware').exists())

    def test_post_delete_crea_audit_log(self):
        op = OpzioniSoftware.objects.create()
        pk = op.pk
        op.delete()
        self.assertTrue(AuditLog.objects.filter(azione='ELIMINAZIONE',
                       pk_oggetto=str(pk)).exists())


class SerializzaTest(TestCase):
    def test_serializza_date(self):
        dl = DatoreLavoro.objects.create(
            codice_fiscale='RSSMRA85M01H501U',
            nome_cognome='Mario Rossi',
            nome='Mario',
            cognome='Rossi',
            indirizzo='Via Test 1',
            comune='Roma',
            provincia='RM',
        )
        data = _serializza(dl)
        self.assertEqual(data['nome_cognome'], 'Mario Rossi')
        self.assertEqual(data['codice_fiscale'], 'RSSMRA85M01H501U')

    def test_serializza_decimal(self):
        dl = DatoreLavoro.objects.create(
            codice_fiscale='RSSMRA85M01H501X',
            nome_cognome='Luigi Verdi',
            nome='Luigi',
            cognome='Verdi',
            indirizzo='Via Test 2',
            comune='Milano',
            provincia='MI',
        )
        data = _serializza(dl)
        for v in data.values():
            if isinstance(v, Decimal):
                self.assertIsInstance(v, float)


class AuditMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        _audit_thread.user = 'sporco'
        _audit_thread.ip = 'sporco'

    def test_process_response_reset(self):
        from core.audit_middleware import AuditMiddleware
        mw = AuditMiddleware(lambda r: None)
        request = self.factory.get('/')
        mw.process_response(request, None)
        self.assertIsNone(get_audit_user())
        self.assertIsNone(get_audit_ip())
