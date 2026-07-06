from django.urls import path
from . import views

urlpatterns = [
    path('token/', views.DatoreLoginView.as_view(), name='api_token'),
    path('token/refresh/', views.TokenRefreshView.as_view(), name='api_token_refresh'),
    path('datore/profilo/', views.DatoreProfiloView.as_view(), name='api_datore_profilo'),
    path('contratti/', views.ContrattiListView.as_view(), name='api_contratti'),
    path('documenti/', views.DocumentiListView.as_view(), name='api_documenti'),
    path('richieste/', views.RichiesteListCreateView.as_view(), name='api_richieste'),
    path('richieste/<int:pk>/', views.RichiestaDetailView.as_view(), name='api_richiesta_detail'),
    path('buste-paga/<int:pk>/download/', views.DownloadView.as_view(), {'modello': 'busta'}, name='api_busta_download'),
    path('documenti/<int:pk>/download/', views.DownloadView.as_view(), {'modello': 'documento'}, name='api_documento_download'),
    path('studio/', views.DatiStudioView.as_view(), name='api_studio'),
    path('referenza-pdf/<slug:slug>/', views.referenza_pdf_view, name='api_referenza_pdf'),
]
