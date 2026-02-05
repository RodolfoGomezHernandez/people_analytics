from django.contrib import admin

# Register your models here.
from .models import Colaborador, Marcaje, ReglaAsistencia, Anomalia

admin.site.register(Colaborador)
admin.site.register(Marcaje)


@admin.register(Anomalia)
class AnomaliaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'colaborador', 'tipo', 'minutos_perdidos')
    list_filter = ('tipo', 'fecha', 'colaborador__area')
    date_hierarchy = 'fecha'


@admin.register(ReglaAsistencia)
class ReglaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'palabra_clave_turno', 'area', 'entrada_teorica', 'es_turno_noche')
    list_filter = ('area', 'es_turno_noche')
    search_fields = ('nombre', 'area', 'seccion')
    fieldsets = (
        ('Identificación', {
            'fields': ('nombre', 'area', 'seccion', 'palabra_clave_turno')
        }),
        ('Jornada Laboral', {
            'fields': ('entrada_teorica', 'salida_teorica', 'es_turno_noche', 'holgura_minutos')
        }),
        ('Reglas de Colación', {
            'fields': ('inicio_colacion', 'fin_colacion', 'tiempo_maximo_colacion')
        }),
    )