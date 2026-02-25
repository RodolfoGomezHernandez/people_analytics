from django.db import models
from datetime import date

class Colaborador(models.Model):
    # Identificación
    rut             = models.CharField(max_length=20, primary_key=True, unique=True, verbose_name="RUT")
    nombre_completo = models.CharField(max_length=255)
    codigo_ficha    = models.CharField(max_length=20, null=True, blank=True)

    # Datos Organizacionales
    cargo            = models.CharField(max_length=100, null=True, blank=True)
    centro_costo     = models.CharField(max_length=100, null=True, blank=True)
    area             = models.CharField(max_length=100, null=True, blank=True)
    seccion          = models.CharField(max_length=100, null=True, blank=True)
    turno            = models.CharField(max_length=150, null=True, blank=True)
    tipo_contrato    = models.CharField(max_length=50,  null=True, blank=True)
    estado_ficha     = models.CharField(max_length=50,  null=True, blank=True)
    fecha_ingreso           = models.DateField(null=True, blank=True)
    fecha_termino_contrato  = models.DateField(null=True, blank=True)

    # Datos Demográficos
    fecha_nacimiento = models.DateField(null=True, blank=True)
    sexo             = models.CharField(max_length=20,  null=True, blank=True)
    estado_civil     = models.CharField(max_length=30,  null=True, blank=True)
    nacionalidad     = models.CharField(max_length=50,  null=True, blank=True)
    comuna           = models.CharField(max_length=50,  null=True, blank=True)
    ciudad           = models.CharField(max_length=50,  null=True, blank=True)
    direccion        = models.CharField(max_length=255, null=True, blank=True)

    # Perfil
    escolaridad      = models.CharField(max_length=100, null=True, blank=True)
    es_recomendable  = models.BooleanField(default=True)

    # Contacto
    email    = models.EmailField(null=True, blank=True)
    telefono = models.CharField(max_length=50, null=True, blank=True)

    # Estado
    activo     = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def edad(self):
        if not self.fecha_nacimiento:
            return None
        today = date.today()
        return today.year - self.fecha_nacimiento.year - (
            (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )

    @property
    def meses_permanencia(self):
        if not self.fecha_ingreso:
            return None
        fin = date.today() if self.activo else (self.fecha_termino_contrato or date.today())
        delta = (fin.year - self.fecha_ingreso.year) * 12 + (fin.month - self.fecha_ingreso.month)
        return max(delta, 0)

    @property
    def datos_pendientes(self):
        pendientes = []
        if not self.email:    pendientes.append('Email')
        if not self.telefono: pendientes.append('Teléfono')
        if not self.direccion: pendientes.append('Dirección')
        return pendientes

    def __str__(self):
        return f"{self.nombre_completo} ({self.rut})"

    class Meta:
        verbose_name          = "Colaborador"
        verbose_name_plural   = "Dotación Completa"