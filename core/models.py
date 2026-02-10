from django.db import models

class CargaInformacion(models.Model):
    TIPOS_ARCHIVO = [
        ('DOTACION', 'Archivo de Fichas (Dotación)'),
        ('ASISTENCIA', 'Archivo de Asistencia (Estadía)'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPOS_ARCHIVO)
    archivo = models.FileField(upload_to='cargas/%Y/%m/')
    usuario = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    
    fecha_carga = models.DateTimeField(auto_now_add=True)
    procesado = models.BooleanField(default=False)
    log_errores = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.fecha_carga.strftime('%d/%m/%Y')}"

    class Meta:
        verbose_name = "Carga de Información"
        verbose_name_plural = "Cargas de Información"