import math
from decimal import Decimal
from datetime import date
from django.test import TestCase
from paghe.models import (
    DatoreLavoro, Lavoratore, Beneficiario, Livello, ParametriCCNL,
    TabellaContributiINPS, TabellaCasse, TabellaScattiAnzianita,
    TipoProgettoRegionale, ProgettoRegionale, ContrattoLavoro,
    OpzioniSoftware
)


class OreCalcolateTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Livello.objects.create(codice='A', colore='#5E6AD2')
        ParametriCCNL.objects.create(
            livello=Livello.objects.get(codice='A'), anno=2026,
            paga_base=8.00, tredicesima_oraria=0.50, ferie_orarie=0.30,
            festivi_orari=0.20, tfr_orario=0.60,
            ind_funzione_mensile=50, ind_minori_6_mensile_ft=35,
            ind_assistenza_piu_persone_non_conv=0.40,
            ind_minori_6_anni_non_conv=0.80,
            ind_cert_qualita=0.25, ind_cert_qualita_mensile=30,
            ind_piu_assistiti_mensile=40,
            ind_assistenza_piu_persone_ft=30,
            ind_assistenza_piu_persone_pt=20,
            ind_funzione_conviventi=50,
            ind_notturno_base=0.30, ind_notturno_20=0.20,
            convivenza_pranzo=3.50, convivenza_cena=3.00,
            convivenza_alloggio=2.00,
            descrizione_corta='Test Livello A',
        )
        TabellaCasse.objects.create(codice='E', quota_datore=0.10, quota_lavoratore=0.05, totale=0.15)
        TabellaContributiINPS.objects.create(descrizione="MENO 24H - FINO A 9,61", quota_datore=0.60, quota_lavoratore=0.40, totale=1.70)
        TabellaContributiINPS.objects.create(descrizione="MENO 24H - 9,61-11,70", quota_datore=1.44, quota_lavoratore=0.48, totale=1.92)
        TabellaContributiINPS.objects.create(descrizione="MENO 24H - OLTRE 11,70", quota_datore=1.75, quota_lavoratore=0.59, totale=2.34)
        TabellaContributiINPS.objects.create(descrizione="PIU' DI 24H", quota_datore=0.70, quota_lavoratore=0.50, totale=1.24)
        TabellaScattiAnzianita.objects.create(livello='A', valore_scatto=0.26)
        OpzioniSoftware.objects.create(
            nome_programma='Test', soglia_ore_contributi=24.90,
            giorni_mensili_std=26, mesi_annuali_std=12
        )
        TipoProgettoRegionale.objects.create(nome='Test Tipo', colore='#10b981')
        cls.beneficiario = Beneficiario.objects.create(
            codice_fiscale='BNFCRS00A01H501X', nome_cognome='Test Beneficiario'
        )
        cls.progetto = ProgettoRegionale.objects.create(
            beneficiario=cls.beneficiario, tipo=TipoProgettoRegionale.objects.first(),
            data_inizio=date(2026, 1, 1), budget_annuale=6000, mesi=12,
            budget_mensile=500
        )
        cls.datore = DatoreLavoro.objects.create(
            codice_fiscale='DTRPLA00A01H501X', nome_cognome='Test Datore'
        )
        cls.lavoratore = Lavoratore.objects.create(
            codice_fiscale='LVRPLA00A01H501X', nome_cognome='Test Lavoratore'
        )

    def _make_contratto(self, **kwargs):
        defaults = dict(
            datore=self.datore, lavoratore=self.lavoratore,
            parametri_minimi=ParametriCCNL.objects.first(),
            ente_bilaterale=TabellaCasse.objects.first(),
            data_assunzione=date(2026, 1, 1),
            tipo_contratto='INDETERMINATO', modalita_tfr='INCLUSO',
            paga_13ma=True, paga_ferie=True, paga_festivi=True,
        )
        defaults.update(kwargs)
        c = ContrattoLavoro.objects.create(**defaults)
        return c

    def test_ore_calcolate_con_progetto(self):
        c = self._make_contratto()
        c.progetto.add(self.progetto)
        c.save()
        # Paga base 8 + 13ma 0.50 + ferie 0.30 + festivi 0.20 + TFR 0.60 = 9.60
        # budget 500, ceil(500 / 9.60) = ceil(52.08) = 53
        self.assertEqual(c.ore_calcolate, 53)

    def test_ore_calcolate_senza_progetto(self):
        c = self._make_contratto()
        c.save()
        self.assertEqual(c.ore_calcolate, 0)

    def test_ore_calcolate_con_molti_progetti(self):
        p2 = ProgettoRegionale.objects.create(
            beneficiario=self.beneficiario, tipo=TipoProgettoRegionale.objects.first(),
            data_inizio=date(2026, 1, 1), budget_annuale=3600, mesi=12, budget_mensile=300
        )
        c = self._make_contratto()
        c.progetto.add(self.progetto, p2)
        c.save()
        # Budget totale = 500 + 300 = 800
        # Paga: 8 + 0.50 + 0.30 + 0.20 + 0.60 = 9.60
        # ceil(800 / 9.60) = ceil(83.33) = 84
        self.assertEqual(c.ore_calcolate, 84)

    def test_ore_calcolate_con_tfr_separato_70(self):
        c = self._make_contratto(modalita_tfr='SEPARATO_70')
        c.progetto.add(self.progetto)
        c.save()
        # Paga: 8 + 0.50 + 0.30 + 0.20 + (0.60 * 0.70) = 9.42
        # ceil(500 / 9.42) = ceil(53.07) = 54
        self.assertEqual(c.ore_calcolate, 54)

    def test_ore_calcolate_con_tfr_separato_100(self):
        c = self._make_contratto(modalita_tfr='SEPARATO_100')
        c.progetto.add(self.progetto)
        c.save()
        # Paga: 8 + 0.50 + 0.30 + 0.20 = 9.00 (TFR escluso)
        # ceil(500 / 9.00) = ceil(55.55) = 56
        self.assertEqual(c.ore_calcolate, 56)

    def test_ore_calcolate_con_indennita(self):
        c = self._make_contratto(
            ind_funzione_conviventi=True,
            ind_certificazione_qualita=True,
        )
        c.progetto.add(self.progetto)
        c.refresh_from_db()
        ore = float(c.ore_calcolate)
        self.assertGreater(ore, 0)

    def test_ore_aggiornate_se_budget_cambia(self):
        c = self._make_contratto()
        c.progetto.add(self.progetto)
        c.refresh_from_db()
        ore_iniziali = float(c.ore_calcolate)
        self.assertGreater(ore_iniziali, 0)
        # Cambia budget del progetto
        ProgettoRegionale.objects.filter(pk=self.progetto.pk).update(budget_mensile=1000)
        # Carica contratto fresco dal DB e salva per ricalcolo
        c2 = ContrattoLavoro.objects.get(pk=c.pk)
        c2.save()
        c2.refresh_from_db()
        self.assertNotEqual(float(c2.ore_calcolate), ore_iniziali)

    def test_budget_di_partenza_property(self):
        p2 = ProgettoRegionale.objects.create(
            beneficiario=self.beneficiario, tipo=TipoProgettoRegionale.objects.first(),
            data_inizio=date(2026, 1, 1), budget_annuale=2400, mesi=12, budget_mensile=200
        )
        c = self._make_contratto()
        c.progetto.add(self.progetto, p2)
        self.assertEqual(c.budget_di_partenza, 700.0)

    def test_paga_oraria_totale_property(self):
        c = self._make_contratto()
        c.progetto.add(self.progetto)
        c.save()
        self.assertGreater(c.paga_oraria_totale, 0)
