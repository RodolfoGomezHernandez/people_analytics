from django.urls import path
from . import views

urlpatterns = [
    path('',                        views.index,            name='dotacion_index'),
    path('api/kpis/',               views.api_kpis,         name='dotacion_api_kpis'),
    path('estados/',                views.gestion_estados,  name='dotacion_estados'),
    path('estados/cambiar/<str:rut>/', views.cambiar_estado, name='dotacion_cambiar_estado'),
    path('api/buscar/',             views.api_buscar,       name='dotacion_api_buscar'),
]