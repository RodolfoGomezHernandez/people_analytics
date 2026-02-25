from django.db import models
from datetime import date
from django.contrib.auth.models import User

class Colaborador(models.Model):

    ESTADO_CHOICES = [
        ('VIGENTE',     'Vigente'),
        ('FINIQUITADO', 'Finiquitado'),
        ('BLOQUEADO',   'Bloqueado'),
    ]

    # Identificación
    rut             = models.CharField(max_length=20, primary_key=True, unique=True, verbose_name="RUT")
    nombre_completo = models.CharField(max_length=255)
    codigo_ficha    = models.CharField(max_length=20, null=True, blank=True)

    # Datos Organizacionales
    cargo                   = models.CharField(max_length=100, null=True, blank=True)
    centro_costo            = models.CharField(max_length=100, null=True, blank=True)
    area                    = models.CharField(max_length=100, null=True, blank=True)
    seccion                 = models.CharField(max_length=100, null=True, blank=True)
    turno                   = models.CharField(max_length=150, null=True, blank=True)
    tipo_contrato           = models.CharField(max_length=50,  null=True, blank=True)
    estado_ficha            = models.CharField(max_length=50,  null=True, blank=True)
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
    escolaridad     = models.CharField(max_length=100, null=True, blank=True)
    es_recomendable = models.BooleanField(default=True)

    # Contacto
    email    = models.EmailField(null=True, blank=True)
    telefono = models.CharField(max_length=50, null=True, blank=True)

    # Estado — reemplaza activo
    estado     = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='VIGENTE', db_index=True)
    motivo_bloqueo = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ── Compatibilidad con código existente ──────────────
    @property
    def activo(self):
        return self.estado == 'VIGENTE'

    @property
    def edad(self):
        if not self.fecha_nacimiento: return None
        today = date.today()
        return today.year - self.fecha_nacimiento.year - (
            (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )

    @property
    def meses_permanencia(self):
        if not self.fecha_ingreso: return None
        fin   = date.today() if self.activo else (self.fecha_termino_contrato or date.today())
        delta = (fin.year - self.fecha_ingreso.year) * 12 + (fin.month - self.fecha_ingreso.month)
        return max(delta, 0)

    def __str__(self):
        return f"{self.nombre_completo} ({self.rut})"

    class Meta:
        verbose_name        = "Colaborador"
        verbose_name_plural = "Dotación Completa"


class HistorialEstado(models.Model):

    ESTADO_CHOICES = [
        ('VIGENTE',     'Vigente'),
        ('FINIQUITADO', 'Finiquitado'),
        ('BLOQUEADO',   'Bloqueado'),
    ]

    colaborador     = models.ForeignKey(
        Colaborador,
        on_delete    = models.CASCADE,
        related_name = 'historial_estados'
    )

    # Transición
    estado_anterior = models.CharField(max_length=20, choices=ESTADO_CHOICES)
    estado_nuevo    = models.CharField(max_length=20, choices=ESTADO_CHOICES)
    motivo          = models.TextField(help_text="Obligatorio al bloquear")

    # Auditoría
    cambiado_por    = models.ForeignKey(
        User,
        on_delete    = models.SET_NULL,
        null         = True,
        related_name = 'cambios_estado_realizados'
    )
    fecha           = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.colaborador.rut} | {self.estado_anterior} → {self.estado_nuevo} | {self.fecha.strftime('%d/%m/%Y')}"

    class Meta:
        ordering            = ['-fecha']
        verbose_name        = "Historial de Estado"
        verbose_name_plural = "Historial de Estados"