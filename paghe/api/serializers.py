from rest_framework import serializers
from paghe.models import DatoreLavoro, ContrattoAttivo, BustaPaga, DocumentoArchiviato, RichiestaModificaDatore, ProgettoRegionale, OpzioniSoftware
import math


class DatoreProfiloSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatoreLavoro
        fields = ['codice_fiscale', 'nome_cognome', 'nome', 'cognome',
                  'indirizzo', 'comune', 'provincia', 'cap', 'email', 'telefono']
        read_only_fields = ['codice_fiscale', 'nome_cognome']


class BustaPagaSerializer(serializers.ModelSerializer):
    documento_id = serializers.IntegerField(source='documento.pk', read_only=True)

    class Meta:
        model = BustaPaga
        fields = ['id', 'mese', 'anno', 'netto', 'lordo', 'tipo_calcolo',
                  'ore_mensili', 'documento_id']


class ProgettoMiniSerializer(serializers.ModelSerializer):
    beneficiario_nome = serializers.CharField(source='beneficiario.nome_cognome')
    tipo_nome = serializers.CharField(source='tipo.nome')

    class Meta:
        model = ProgettoRegionale
        fields = ['id', 'beneficiario_nome', 'tipo_nome', 'budget_mensile']


class ContrattoSerializer(serializers.ModelSerializer):
    lavoratore_nome = serializers.CharField(source='lavoratore.nome_cognome')
    lavoratore_cf = serializers.CharField(source='lavoratore.codice_fiscale')
    buste_paga = serializers.SerializerMethodField()
    ore_settimanali_arrotondate = serializers.SerializerMethodField()
    paga_applicata = serializers.SerializerMethodField()
    stima_trimestrale = serializers.SerializerMethodField()
    tipo_contratto_display = serializers.CharField(source='get_tipo_contratto_display', read_only=True)
    stato_display = serializers.CharField(source='get_stato_display', read_only=True)
    modalita_tfr_display = serializers.CharField(source='get_modalita_tfr_display', read_only=True)
    livello_info = serializers.SerializerMethodField()
    ente_bilaterale_info = serializers.SerializerMethodField()
    progetti = serializers.SerializerMethodField()
    note = serializers.CharField(source='note_post_it', read_only=True)

    class Meta:
        model = ContrattoAttivo
        fields = [
            'id', 'lavoratore_nome', 'lavoratore_cf', 'data_assunzione', 'data_fine',
            'codice_rapporto_inps', 'budget_di_partenza', 'ore_calcolate',
            'ore_settimanali_arrotondate', 'paga_applicata', 'stima_trimestrale',
            'tipo_contratto', 'tipo_contratto_display', 'stato', 'stato_display',
            'modalita_tfr', 'modalita_tfr_display', 'livello_info', 'ente_bilaterale_info',
            'progetti', 'data_inizio_tfr', 'is_convivente', 'paga_13ma', 'paga_ferie',
            'paga_festivi', 'applica_scatti', 'note', 'buste_paga',
        ]

    def get_ore_settimanali_arrotondate(self, obj):
        return math.ceil(obj.ore_settimanali_calcolate)

    def get_paga_applicata(self, obj):
        busta = BustaPaga.objects.filter(
            contratto=obj, stato__in=['APPROVATA', 'ARCHIVIATA'],
            documento__visibile_al_datore=True
        ).order_by('-anno', '-mese').first()
        if busta:
            return round(float(busta.paga_oraria_lorda), 4)
        return round(float(obj.paga_oraria_totale), 4) if obj.paga_oraria_totale else None

    def get_stima_trimestrale(self, obj):
        from paghe.models import TabellaContributiINPS, OpzioniSoftware
        opzioni = OpzioniSoftware.objects.first()
        ultimo = BustaPaga.objects.filter(
            contratto=obj, stato__in=['APPROVATA', 'ARCHIVIATA']
        ).order_by('-anno', '-mese').first()
        if ultimo and ultimo.totale_contributi:
            return round(float(ultimo.totale_contributi) * 3, 2)
        ore_m = obj.ore_mensili_calcolate
        ore_sett = obj.ore_settimanali_calcolate
        soglia_ore = float(opzioni.soglia_ore_contributi) if opzioni and hasattr(opzioni, 'soglia_ore_contributi') else 24.90
        if ore_sett > soglia_ore:
            fascia = TabellaContributiINPS.objects.filter(descrizione__icontains="PIU").first()
        else:
            soglia_paga_1 = float(opzioni.soglia_paga_1_contributi) if opzioni and hasattr(opzioni, 'soglia_paga_1_contributi') else 9.61
            soglia_paga_2 = float(opzioni.soglia_paga_2_contributi) if opzioni and hasattr(opzioni, 'soglia_paga_2_contributi') else 11.70
            paga_base = float(obj.parametri_minimi.paga_base) if obj.parametri_minimi else 0
            tredicesima = float(obj.parametri_minimi.tredicesima_oraria) if obj.parametri_minimi else 0
            paga_eff = paga_base + tredicesima
            if paga_eff <= soglia_paga_1:
                fascia = TabellaContributiINPS.objects.filter(descrizione="MENO 24H - FINO A 9,61").first()
            elif paga_eff <= soglia_paga_2:
                fascia = TabellaContributiINPS.objects.filter(descrizione="MENO 24H - 9,61-11,70").first()
            else:
                fascia = TabellaContributiINPS.objects.filter(descrizione="MENO 24H - OLTRE 11,70").first()
        inps_orario = float(fascia.totale) if fascia else 0.0
        ore_inps = math.ceil(ore_m) if ore_m > 0 else 0
        inps_totale = round(inps_orario * ore_inps, 4)
        ente = obj.ente_bilaterale
        cassa_orario = float(ente.totale) if ente else 0.0
        cassa_totale = round(cassa_orario * ore_inps, 4)
        return round((inps_totale + cassa_totale) * 3, 2) if ore_m > 0 else None

    def get_livello_info(self, obj):
        if obj.parametri_minimi and obj.parametri_minimi.livello:
            liv = obj.parametri_minimi.livello
            return {'codice': liv.codice, 'descrizione': obj.parametri_minimi.descrizione_corta or ''}
        return None

    def get_ente_bilaterale_info(self, obj):
        if obj.ente_bilaterale:
            return {'id': obj.ente_bilaterale.pk, 'descrizione': obj.ente_bilaterale.descrizione}
        return None

    def get_progetti(self, obj):
        return ProgettoMiniSerializer(obj.progetto.all(), many=True).data

    def get_buste_paga(self, obj):
        buste = BustaPaga.objects.filter(
            contratto=obj, stato__in=['APPROVATA', 'ARCHIVIATA'],
            documento__visibile_al_datore=True
        ).select_related('documento').order_by('-anno', '-mese')
        return BustaPagaSerializer(buste, many=True).data


class DocumentoArchiviatoSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    lavoratore_nome = serializers.SerializerMethodField()
    progetti_info = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()
    is_nuovo = serializers.SerializerMethodField()

    class Meta:
        model = DocumentoArchiviato
        fields = ['pk', 'tipo', 'tipo_display', 'titolo', 'creato_il',
                  'lavoratore_nome', 'progetti_info', 'download_url', 'is_nuovo']

    def get_lavoratore_nome(self, obj):
        if obj.contratto and obj.contratto.lavoratore:
            return obj.contratto.lavoratore.nome_cognome
        return ''

    def get_progetti_info(self, obj):
        if not obj.contratto:
            return []
        return [
            {'beneficiario': p.beneficiario.nome_cognome, 'tipo': p.tipo.nome if p.tipo else ''}
            for p in obj.contratto.progetto.all()
        ]

    def get_download_url(self, obj):
        from django.urls import reverse
        return reverse('api_documento_download', kwargs={'pk': obj.pk})

    def get_is_nuovo(self, obj):
        from django.utils import timezone
        return obj.creato_il >= (timezone.now() - timezone.timedelta(days=7)) if obj.creato_il else False


class RichiestaModificaDatoreSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    stato_display = serializers.CharField(source='get_stato_display', read_only=True)
    contratto_info = serializers.SerializerMethodField()

    class Meta:
        model = RichiestaModificaDatore
        fields = ['pk', 'tipo', 'tipo_display', 'contratto', 'contratto_info',
                  'campo', 'etichetta_campo', 'valore_attuale', 'valore_richiesto',
                  'stato', 'stato_display', 'nota_datore', 'nota_admin',
                  'creato_il', 'gestito_il']
        read_only_fields = ['pk', 'stato', 'stato_display', 'nota_admin', 'creato_il', 'gestito_il']

    def get_contratto_info(self, obj):
        if obj.contratto:
            return {'id': obj.contratto.pk, 'lavoratore': obj.contratto.lavoratore.nome_cognome}
        return None


class DatiStudioSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpzioniSoftware
        fields = ['dati_studio', 'telefono_studio', 'email_studio',
                  'nome_programma', 'versione_programma', 'logo',
                  'iban_studio', 'intestatario_iban', 'banca_iban',
                  'denominazione_studio']
