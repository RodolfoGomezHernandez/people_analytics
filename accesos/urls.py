from django.urls import path
from . import views

urlpatterns = [
    path('',              views.control,         name='accesos_control'),
    path('api/buscar/',   views.api_buscar_rut,  name='accesos_api_buscar'),
    path('api/salida/<int:pk>/', views.api_registrar_salida, name='accesos_api_salida'),
]