from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework.authentication import BaseAuthentication
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from paghe.models import DatoreLavoro, AccessoDatore
from paghe.auth_backends import DatoreAuthBackend
from django.utils import timezone


class DatoreJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        raw = request.META.get('HTTP_AUTHORIZATION', '')
        if not raw:
            raw = request.query_params.get('token', '')
            if raw:
                raw = 'Bearer ' + raw
        if isinstance(raw, bytes):
            raw = raw.decode()
        if not raw.startswith('Bearer '):
            return None
        token_str = raw[7:]
        if not token_str:
            return None
        try:
            validated = AccessToken(token_str)
        except Exception:
            return None
        if validated.get('tipo') == 'datore':
            cf = validated.get('datore_cf')
            if cf is None:
                return None
            try:
                datore = DatoreLavoro.objects.get(codice_fiscale=cf)
                datore.is_authenticated = True
                datore.is_active = True
                return (datore, validated)
            except DatoreLavoro.DoesNotExist:
                return None
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user_id = validated.get('user_id')
        if user_id:
            try:
                user = User.objects.get(pk=user_id)
                return (user, validated)
            except User.DoesNotExist:
                return None
        return None

    def authenticate_header(self, request):
        return 'Bearer'


class DatoreTokenObtainView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        cf = request.data.get('codice_fiscale', '').upper().strip()
        password = request.data.get('password', '')
        if not cf or not password:
            return Response({'error': 'Inserisci codice fiscale e password.'}, status=status.HTTP_400_BAD_REQUEST)
        backend = DatoreAuthBackend()
        datore = backend.authenticate(request, codice_fiscale=cf, password=password)
        if not datore:
            return Response({'error': 'Codice fiscale o password errati.'}, status=status.HTTP_401_UNAUTHORIZED)
        AccessoDatore.objects.filter(datore=datore).update(ultimo_accesso=timezone.now())
        refresh = RefreshToken()
        refresh['datore_cf'] = datore.codice_fiscale
        refresh['tipo'] = 'datore'
        refresh['nome'] = datore.nome_cognome
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'nome': datore.nome_cognome,
            'codice_fiscale': datore.codice_fiscale,
        })
