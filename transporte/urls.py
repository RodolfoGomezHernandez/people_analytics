from django.urls import path
from . import views

urlpatterns = [
    path('', views.transporte_home, name='transporte_home'),
    path('dashboard/', views.dashboard_transporte, name='dashboard_transporte'),
    path('control-salida/', views.registro_control_salida, name='control_salida'),


    path('editar/<int:registro_id>/', views.editar_registro, name='editar_registro'),
    
    path('nuevo-vehiculo/', views.crear_vehiculo, name='crear_vehiculo'),
    path('nuevo-conductor/', views.crear_conductor, name='crear_conductor'),
    path('exportar/', views.exportar_excel_transporte, name='exportar_excel_transporte'),
]