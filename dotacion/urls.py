from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('',                        views.index,            name='dotacion_index'),
    path('api/kpis/',               views.api_kpis,         name='dotacion_api_kpis'),
    path('estados/',                views.gestion_estados,  name='dotacion_estados'),
    path('estados/cambiar/<str:rut>/', views.cambiar_estado, name='dotacion_cambiar_estado'),
    path('api/buscar/',             views.api_buscar,       name='dotacion_api_buscar'),
    path('bloqueados/',                   views.lista_bloqueados,   name='dotacion_bloqueados'),
    path('bloqueados/desbloquear/<int:pk>/', views.desbloquear_persona, name='dotacion_desbloquear'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)