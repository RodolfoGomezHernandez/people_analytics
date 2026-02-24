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
    path('rutas/', views.gestion_rutas, name='gestion_rutas'),
    path('api/datos/', views.api_datos_dashboard, name='api_datos_transporte'),
    
    # NUEVO: Rutas para deshabilitar registros (Requerimiento 1.1)
    path('vehiculo/<int:vehiculo_id>/deshabilitar/', views.deshabilitar_vehiculo, name='deshabilitar_vehiculo'),
    path('conductor/<int:conductor_id>/deshabilitar/', views.deshabilitar_conductor, name='deshabilitar_conductor'),
    path('ruta/<int:ruta_id>/deshabilitar/', views.deshabilitar_ruta, name='deshabilitar_ruta'),
]