from django.contrib import admin
from .models import RegistroAsistencia, Anomalia

@admin.register(RegistroAsistencia)
class RegistroAsistenciaAdmin(admin.ModelAdmin):
    list_display = ('colaborador', 'fecha', 'hora_entrada', 'hora_salida', 'archivo_origen')
    list_filter = ('fecha', 'archivo_origen')
    search_fields = ('colaborador__rut', 'colaborador__nombre_completo')

@admin.register(Anomalia)
class AnomaliaAdmin(admin.ModelAdmin):
    list_display = ('registro', 'tipo', 'observacion')
    list_filter = ('tipo',)