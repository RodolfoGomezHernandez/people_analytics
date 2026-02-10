from django.contrib import admin
from .models import Colaborador

@admin.register(Colaborador)
class ColaboradorAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombre_completo', 'cargo', 'centro_costo', 'activo')
    search_fields = ('rut', 'nombre_completo')
    list_filter = ('activo', 'centro_costo')
