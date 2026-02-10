from django.contrib import admin
from django.urls import path, include
from django.conf import settings 
from django.conf.urls.static import static
# Importamos las vistas correctas definidas en core/views.py
from core.views import dashboard, subir_archivo 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Rutas del Core
    path('', dashboard, name='dashboard'),
    path('subir-informacion/', subir_archivo, name='subir_archivo'), # Esta es la ruta para cargar Excel
    
    # Rutas de otras Apps
    path('reclutamiento/', include('reclutamiento.urls')),
    path('transporte/', include('transporte.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)