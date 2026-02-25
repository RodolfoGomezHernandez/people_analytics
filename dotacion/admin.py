from django.contrib import admin
from .models import Colaborador

@admin.register(Colaborador)
class ColaboradorAdmin(admin.ModelAdmin):
    list_display = (
        'rut',
        'nombre_completo',
        'cargo',
        'centro_costo',
        'nacionalidad',
        'sexo',
        'edad',
        'es_recomendable',
        'estado',           # ← reemplaza activo
    )

    search_fields = ('rut', 'nombre_completo', 'email', 'cargo')

    list_filter = (
        'estado',           # ← reemplaza activo
        'sexo',
        'nacionalidad',
        'comuna',
        'escolaridad',
        'es_recomendable',
        'centro_costo',
        'fecha_ingreso',
    )

    def edad(self, obj):
        return obj.edad
    edad.short_description = 'Edad'