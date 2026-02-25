from django.urls import path
from . import views

urlpatterns = [
    path('',                                    views.index,            name='dotacion_index'),
    path('api/kpis/',                           views.api_kpis,         name='dotacion_api_kpis'),
    path('api/buscar/',                         views.api_buscar,       name='dotacion_api_buscar'),
    path('bloqueados/',                         views.lista_bloqueados, name='dotacion_bloqueados'),
    path('bloqueados/desbloquear/<int:pk>/',    views.desbloquear_persona, name='dotacion_desbloquear'),
    path('bloqueados/plantilla/',         views.descargar_plantilla_bloqueados, name='dotacion_plantilla_bloqueados'),
    path('bloqueados/carga-masiva/',      views.carga_masiva_bloqueados,        name='dotacion_carga_masiva_bloqueados'),
]