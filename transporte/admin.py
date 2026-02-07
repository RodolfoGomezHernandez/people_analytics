from django.contrib import admin
from .models import Vehiculo, Conductor, Ruta, RegistroSalida

@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    # Agregamos 'tarifa_base' para que la veas rápido
    list_display = ('patente', 'tipo', 'modelo', 'capacidad', 'tarifa_base', 'activo')
    list_filter = ('tipo', 'activo')

@admin.register(Conductor)
class ConductorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'empresa_externa', 'activo')
    list_filter = ('empresa_externa', 'activo')

@admin.register(Ruta)
class RutaAdmin(admin.ModelAdmin):
    # QUITAMOS 'valor_servicio' porque ya no existe en el modelo
    list_display = ('nombre', 'origen', 'destino', 'activo') 

@admin.register(RegistroSalida)
class RegistroSalidaAdmin(admin.ModelAdmin):
    # Agregamos 'valor_viaje' para que controles los cobros
    list_display = ('fecha_registro', 'vehiculo', 'ruta', 'cantidad_pasajeros', 'valor_viaje', 'ocupacion_porcentaje')
    list_filter = ('fecha_registro', 'ruta', 'vehiculo')
    readonly_fields = ('fecha_registro', 'ocupacion_porcentaje')