from django.contrib import admin
from .models import SolicitudDotacion, Candidato

@admin.register(SolicitudDotacion)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = ('cargo', 'area', 'cantidad', 'fecha_necesidad', 'estado')
    list_filter = ('estado', 'area')
    search_fields = ('cargo', 'solicitante')

@admin.register(Candidato)
class CandidatoAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'rut', 'telefono', 'estado', 'fecha_postulacion')
    list_filter = ('estado',)
    search_fields = ('rut', 'nombre_completo')