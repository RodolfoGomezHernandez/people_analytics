from django.db import models
from datetime import date

class Colaborador(models.Model):
    # Identificación
    rut = models.CharField(max_length=20, primary_key=True, unique=True, verbose_name="RUT")
    nombre_completo = models.CharField(max_length=255)
    
    # Datos Organizacionales
    cargo = models.CharField(max_length=100, null=True, blank=True)
    centro_costo = models.CharField(max_length=100, null=True, blank=True)
    fecha_ingreso = models.DateField(null=True, blank=True, help_text="Para cálculo de antigüedad y contrataciones")
    
    # Datos Demográficos (Para KPIs 4, 6, 7, 8)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    sexo = models.CharField(max_length=20, null=True, blank=True) # Femenino/Masculino
    nacionalidad = models.CharField(max_length=50, null=True, blank=True)
    comuna = models.CharField(max_length=50, null=True, blank=True)
    direccion = models.CharField(max_length=255, null=True, blank=True)
    
    # Perfil (Para KPI 9 y 10)
    escolaridad = models.CharField(max_length=100, null=True, blank=True)
    es_recomendable = models.BooleanField(default=True, help_text="Basado en campo Recomendable del Excel")
    
    # Contacto (Para KPI 11 - Regularización)
    email = models.EmailField(null=True, blank=True)
    telefono = models.CharField(max_length=50, null=True, blank=True)
    
    # Estado
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def edad(self):
        """Calcula la edad automáticamente"""
        if not self.fecha_nacimiento: return None
        today = date.today()
        return today.year - self.fecha_nacimiento.year - ((today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))

    @property
    def datos_pendientes(self):
        """Devuelve una lista de qué le falta (KPI 11)"""
        pendientes = []
        if not self.email: pendientes.append('Email')
        if not self.telefono: pendientes.append('Teléfono')
        if not self.direccion: pendientes.append('Dirección')
        return pendientes

    def __str__(self):
        return f"{self.nombre_completo} ({self.rut})"

    class Meta:
        verbose_name = "Colaborador"
        verbose_name_plural = "Dotación Completa"
