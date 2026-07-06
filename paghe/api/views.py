import os

from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from paghe.models import (
    ContrattoAttivo, BustaPaga, DocumentoArchiviato,
    RichiestaModificaDatore, ProgettoRegionale, OpzioniSoftware,
    AccessoDatore
)
from paghe.views._helpers import _cerca_comune_per_nome

from .auth import DatoreJWTAuthentication, DatoreTokenObtainView
from .permissions import IsDatore
from .serializers import (
    DatoreProfiloSerializer, ContrattoSerializer,
    DocumentoArchiviatoSerializer, RichiestaModificaDatoreSerializer,
    DatiStudioSerializer
)
import contextlib


class DatoreLoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        return DatoreTokenObtainView().post(request)


class TokenRefreshView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework_simplejwt.exceptions import TokenError
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token richiesto.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            return Response({'access': str(token.access_token)})
        except TokenError:
            return Response({'error': 'Token non valido o scaduto.'}, status=status.HTTP_401_UNAUTHORIZED)


class DatoreProfiloView(APIView):
    authentication_classes = [DatoreJWTAuthentication]
    permission_classes = [IsAuthenticated, IsDatore]

    def get(self, request):
        datore = request.user
        provincia = request.GET.get('provincia') or datore.provincia or ''
        cap = request.GET.get('cap') or datore.cap or ''
        if not provincia and datore.comune:
            info = _cerca_comune_per_nome(datore.comune) or {}
            provincia = info.get('sigla', provincia)
            cap = info.get('cap', cap)
        data = DatoreProfiloSerializer(datore).data
        data['provincia'] = provincia
        data['cap'] = cap
        data['has_accesso'] = AccessoDatore.objects.filter(datore=datore, accesso_abilitato=True).exists()
        ultimo = AccessoDatore.objects.filter(datore=datore, accesso_abilitato=True).values_list('ultimo_accesso', flat=True).first()
        data['ultimo_accesso'] = ultimo.isoformat() if ultimo else None
        return Response(data)

    def patch(self, request):
        datore = request.user
        allowed = {'email', 'telefono'}
        changed = {}
        for field in allowed:
            if field in request.data:
                val = request.data[field].strip()
                setattr(datore, field, val)
                changed[field] = val
        if changed:
            datore.save(update_fields=list(changed.keys()))
        return Response(DatoreProfiloSerializer(datore).data)


class ContrattiListView(APIView):
    authentication_classes = [DatoreJWTAuthentication]
    permission_classes = [IsAuthenticated, IsDatore]

    def get(self, request):
        datore = request.user
        contratto_prefetch = Prefetch(
            'progetto',
            queryset=ProgettoRegionale.objects.select_related('beneficiario', 'tipo')
        )
        contratti = ContrattoAttivo.objects.filter(
            datore=datore
        ).select_related(
            'lavoratore', 'parametri_minimi', 'parametri_minimi__livello', 'ente_bilaterale'
        ).prefetch_related(contratto_prefetch).order_by('-data_assunzione', 'lavoratore__nome_cognome')

        serializer = ContrattoSerializer(contratti, many=True, context={'request': request})
        return Response(serializer.data)


class DocumentiListView(APIView):
    authentication_classes = [DatoreJWTAuthentication]
    permission_classes = [IsAuthenticated, IsDatore]

    def get(self, request):
        datore = request.user
        tipo = request.query_params.get('tipo', '')
        testo = request.query_params.get('testo', '').lower()
        qs = DocumentoArchiviato.objects.filter(
            datore=datore, visibile_al_datore=True
        ).select_related('contratto__lavoratore', 'contratto').prefetch_related(
            Prefetch('contratto__progetto', queryset=ProgettoRegionale.objects.select_related('beneficiario', 'tipo'))
        ).order_by('-creato_il')

        if tipo:
            qs = qs.filter(tipo=tipo)
        if testo:
            qs = qs.filter(
                contratto__lavoratore__nome_cognome__icontains=testo
            ) | qs.filter(
                contratto__progetto__beneficiario__nome_cognome__icontains=testo
            )

        serializer = DocumentoArchiviatoSerializer(qs, many=True, context={'request': request})
        tipi_disponibili = list(DocumentoArchiviato.objects.filter(
            datore=datore, visibile_al_datore=True
        ).values_list('tipo', flat=True).distinct().order_by('tipo'))

        return Response({
            'documenti': serializer.data,
            'tipi_disponibili': tipi_disponibili,
        })


class RichiesteListCreateView(APIView):
    authentication_classes = [DatoreJWTAuthentication]
    permission_classes = [IsAuthenticated, IsDatore]

    def get(self, request):
        datore = request.user
        richieste = RichiestaModificaDatore.objects.filter(
            datore=datore, eliminata=False
        ).order_by('-creato_il')[:50]
        serializer = RichiestaModificaDatoreSerializer(richieste, many=True)
        return Response(serializer.data)

    def post(self, request):
        datore = request.user
        data = request.data
        tipo = data.get('tipo', '').strip()
        if tipo not in dict(RichiestaModificaDatore.TIPO_SCELTE):
            return Response({'error': 'Tipo richiesta non valido.'}, status=status.HTTP_400_BAD_REQUEST)
        contratto_pk = data.get('contratto_pk')
        contratto = None
        if contratto_pk:
            with contextlib.suppress(ValueError, ContrattoAttivo.DoesNotExist):
                contratto = ContrattoAttivo.objects.get(pk=int(contratto_pk), datore=datore)
        richiesta = RichiestaModificaDatore.objects.create(
            datore=datore,
            contratto=contratto,
            tipo=tipo,
            campo=data.get('campo', '').strip(),
            etichetta_campo=data.get('etichetta', '') or data.get('campo', '').strip(),
            valore_attuale=data.get('valore_attuale', '').strip(),
            valore_richiesto=data.get('valore_richiesto', '').strip(),
            nota_datore=data.get('nota', '').strip(),
            stato='INVIATA',
        )
        serializer = RichiestaModificaDatoreSerializer(richiesta)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RichiestaDetailView(APIView):
    authentication_classes = [DatoreJWTAuthentication]
    permission_classes = [IsAuthenticated, IsDatore]

    def get(self, request, pk):
        datore = request.user
        richiesta = get_object_or_404(RichiestaModificaDatore, pk=pk, datore=datore, eliminata=False)
        serializer = RichiestaModificaDatoreSerializer(richiesta)
        return Response(serializer.data)


class DownloadView(APIView):
    authentication_classes = [DatoreJWTAuthentication]
    permission_classes = [IsAuthenticated, IsDatore]

    def get(self, request, pk, modello='documento'):
        datore = request.user
        if modello == 'busta':
            busta = get_object_or_404(BustaPaga, pk=pk, contratto__datore=datore)
            if not busta.documento or not busta.documento.visibile_al_datore:
                return HttpResponse('Documento non disponibile.', status=404)
            doc = busta.documento
        else:
            doc = get_object_or_404(DocumentoArchiviato, pk=pk, datore=datore, visibile_al_datore=True)
        path = doc.file_path
        if not os.path.exists(path):
            return HttpResponse('File non trovato.', status=404)
        response = FileResponse(open(path, 'rb'), content_type='application/pdf')
        filename = doc.file_name or 'documento.pdf'
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response


def referenza_pdf_view(request, slug):
    import logging, traceback
    logger = logging.getLogger('paghe')
    token_str = request.GET.get('token', '')
    if not token_str:
        return HttpResponse('Token mancante.', status=401)
    from rest_framework_simplejwt.tokens import AccessToken
    from rest_framework_simplejwt.exceptions import TokenError
    from paghe.models import DatoreLavoro
    try:
        validated = AccessToken(token_str)
        if validated.get('tipo') != 'datore':
            return HttpResponse('Token non valido.', status=401)
        cf = validated.get('datore_cf')
        if not cf:
            return HttpResponse('Token non valido.', status=401)
        request.user = DatoreLavoro.objects.get(codice_fiscale=cf)
    except (TokenError, DatoreLavoro.DoesNotExist, Exception) as e:
        logger.warning("referenza_pdf_view auth errore: %s", e)
        return HttpResponse('Non autorizzato.', status=401)

    try:
        from paghe.views._ccnl import _genera_pdf_bytes as _ccnl_bytes
        from paghe.views._inquadramento import _genera_inquadramento_pdf_bytes
        from paghe.views._tabelle_retributive import _genera_tabelle_pdf_bytes
        from paghe.views._contributi_ccnl import _genera_contributi_pdf_bytes
        from paghe.views._guide import _genera_guida_pdf

        if slug == 'ccnl':
            pdf_bytes = _ccnl_bytes()
            filename = 'CCNL.pdf'
        elif slug == 'inquadramento':
            pdf_bytes = _genera_inquadramento_pdf_bytes(request)
            filename = 'Inquadramento.pdf'
        elif slug == 'tabelle':
            pdf_bytes = _genera_tabelle_pdf_bytes(request)
            filename = 'Tabelle_Retributive.pdf'
        elif slug == 'contributi':
            pdf_bytes = _genera_contributi_pdf_bytes(request)
            filename = 'Contributi_INPS.pdf'
        elif slug == 'assunzione':
            pdf_bytes = _genera_guida_pdf('assunzione', request)
            filename = 'Guida_Assunzione.pdf'
        elif slug == 'decalogo':
            pdf_bytes = _genera_guida_pdf('decalogo_colloquio', request)
            filename = 'Decalogo_Colloquio.pdf'
        elif slug == 'cessazione':
            pdf_bytes = _genera_guida_pdf('cessazione', request)
            filename = 'Guida_Cessazione.pdf'
        else:
            return HttpResponse('Documento non trovato.', status=404)
        logger.info("referenza_pdf_view: %s generato (%d byte)", slug, len(pdf_bytes))
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = len(pdf_bytes)
        return response
    except Exception as e:
        logger.error("referenza_pdf_view errore per %s: %s\n%s", slug, e, traceback.format_exc())
        return HttpResponse('Errore generazione PDF: ' + str(e), status=500)


class DatiStudioView(APIView):
    authentication_classes = [DatoreJWTAuthentication]
    permission_classes = [IsAuthenticated, IsDatore]

    def get(self, request):
        opzioni = OpzioniSoftware.objects.first()
        if not opzioni:
            return Response({})
        serializer = DatiStudioSerializer(opzioni)
        data = serializer.data
        if data.get('logo'):
            request_build = request
            data['logo_url'] = request_build.build_absolute_uri(data['logo'])
        return Response(data)
