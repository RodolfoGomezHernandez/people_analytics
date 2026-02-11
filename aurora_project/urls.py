from django.contrib import admin
from django.urls import path, include
from django.conf import settings 
from django.conf.urls.static import static
from core.views import dashboard  # Solo importamos dashboard, subir_archivo ya no se usa directo

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Ruta principal al Dashboard bonito
    path('', dashboard, name='dashboard'),
    
    # Eliminamos la ruta 'subir-informacion/' porque ya está integrada
    # path('subir-informacion/', ... ), 
    
    path('reclutamiento/', include('reclutamiento.urls')),
    path('transporte/', include('transporte.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)