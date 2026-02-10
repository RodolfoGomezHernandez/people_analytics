from django.db import models

class Colaborador(models.Model):
    # Identificador único (RUT)
    rut = models.CharField(max_length=20, primary_key=True, unique=True, verbose_name="RUT")
    
    # Datos informativos de la Ficha GREX
    nombre_completo = models.CharField(max_length=255)
    cargo = models.CharField(max_length=100, null=True, blank=True)
    centro_costo = models.CharField(max_length=100, null=True, blank=True)
    
    # Estado (Para dar de baja sin borrar historial)
    activo = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre_completo} ({self.rut})"

    class Meta:
        verbose_name = "Colaborador"
        verbose_name_plural = "Dotación (Colaboradores)"