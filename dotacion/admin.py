from django.contrib import admin
from .models import Colaborador

@admin.register(Colaborador)
class ColaboradorAdmin(admin.ModelAdmin):
    # 1. Columnas de la tabla (Lo que ya tienes + contacto)
    list_display = (
        'rut', 
        'nombre_completo', 
        'cargo', 
        'centro_costo', 
        'nacionalidad', 
        'sexo', 
        'edad',             # Campo calculado (property)
        'es_recomendable', 
        'activo'
    )
    
    # 2. Barra de Búsqueda (Search)
    # Agrega 'email' y 'cargo' para buscar rápido
    search_fields = ('rut', 'nombre_completo', 'email', 'cargo')
    
    # 3. Filtros Laterales (AQUÍ ESTÁ LA MAGIA)
    # Esto crea el sidebar derecho para filtrar tus KPIs inmediatamente
    list_filter = (
        'activo',           # Req 3: Vigentes
        'sexo',             # Req 6: Sexo
        'nacionalidad',     # Req 8: Nacionalidad
        'comuna',           # Req 7: Localidad
        'escolaridad',      # Req 9: Escolaridad
        'es_recomendable',  # Req 10: Recomendable
        'centro_costo',     # Req 1 y 2: Por áreas
        'fecha_ingreso',    # Req 1: Contrataciones por fecha
    )

    # Opcional: Para que 'edad' (que es calculado) se vea bien
    def edad(self, obj):
        return obj.edad
    
    edad.short_description = 'Edad'