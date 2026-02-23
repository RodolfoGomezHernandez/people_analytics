from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),

    # Dashboard principal (raíz)
    path('', dashboard, name='dashboard'),

    # Módulos independientes
    path('dotacion/', include('dotacion.urls')),
    path('asistencia/', include('asistencia.urls')),
    path('reclutamiento/', include('reclutamiento.urls')),
    path('transporte/', include('transporte.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)