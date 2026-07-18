from django.urls import path
from paghe import views

urlpatterns = [
    path('', views.mobile_dashboard, name='mobile_dashboard'),
    path('datori/', views.mobile_datori_list, name='mobile_datori_list'),
    path('datori/<str:identifier>/', views.mobile_datore_detail, name='mobile_datore_detail'),
    path('lavoratori/', views.mobile_lavoratori_list, name='mobile_lavoratori_list'),
    path('lavoratori/<str:identifier>/', views.mobile_lavoratore_detail, name='mobile_lavoratore_detail'),
    path('contratti/', views.mobile_contratti_list, name='mobile_contratti_list'),
    path('contratti/<int:pk>/', views.mobile_contratto_detail, name='mobile_contratto_detail'),
    path('buste/', views.mobile_calcoli_busta, name='mobile_calcoli_busta'),
    path('buste/archivio/', views.mobile_buste_archivio, name='mobile_buste_archivio'),
    path('documenti/', views.mobile_documenti, name='mobile_documenti'),
    path('beneficiari/', views.mobile_beneficiari_list, name='mobile_beneficiari_list'),
    path('beneficiari/<str:pk>/', views.mobile_beneficiario_detail, name='mobile_beneficiario_detail'),
    path('progetti/', views.mobile_progetti_list, name='mobile_progetti_list'),
    path('progetti/<int:pk>/', views.mobile_progetto_detail, name='mobile_progetto_detail'),
    path('about/', views.mobile_about, name='mobile_about'),
]
