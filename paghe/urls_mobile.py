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
]
