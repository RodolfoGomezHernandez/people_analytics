from django.db import models
from dotacion.models import Colaborador # Relación directa con la nueva app

class RegistroAsistencia(models.Model):
    # Relación con el empleado
    colaborador = models.ForeignKey(Colaborador, on_delete=models.CASCADE, related_name='asistencias')
    
    # Datos temporales
    fecha = models.DateField()
    hora_entrada = models.TimeField(null=True, blank=True)
    hora_salida = models.TimeField(null=True, blank=True)
    
    # Auditoría del archivo origen
    archivo_origen = models.ForeignKey('core.CargaInformacion', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ('colaborador', 'fecha') # Un registro por persona por día
        verbose_name = "Registro Diario"
        verbose_name_plural = "Registros de Asistencia"

class Anomalia(models.Model):
    TIPOS = [
        ('AUSENCIA', 'Ausencia Injustificada'),
        ('ATRASO', 'Atraso en Entrada'),
        ('SIN_MARCA', 'Falta Marca Salida'),
        ('TURNO_EXTRA', 'Asistencia fuera de turno'),
    ]
    
    registro = models.ForeignKey(RegistroAsistencia, on_delete=models.CASCADE, related_name='anomalias')
    tipo = models.CharField(max_length=50, choices=TIPOS)
    observacion = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.registro.colaborador}"