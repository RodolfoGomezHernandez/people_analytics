from django.urls import path
from . import views

urlpatterns = [
    path('nueva-solicitud/', views.crear_solicitud, name='crear_solicitud'),
    path('bot/incoming/', views.whatsapp_webhook, name='whatsapp_webhook'),
]