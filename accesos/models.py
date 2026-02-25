from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class RegistroVisita(models.Model):

    ESTADO_DOTACION_CHOICES = [
        ('VIGENTE',     'Vigente'),
        ('FINIQUITADO', 'Finiquitado'),
        ('BLOQUEADO',   'Bloqueado'),
        ('EXTERNO',     'Externo / No encontrado'),
    ]

    # ── Identificación del visitante ──────────────────
    rut             = models.CharField(max_length=20)
    nombre          = models.CharField(max_length=255)
    empresa         = models.CharField(max_length=100, blank=True)
    estado_dotacion = models.CharField(
        max_length=20,
        choices=ESTADO_DOTACION_CHOICES,
        default='EXTERNO'
    )

    # ── Datos de la visita ────────────────────────────
    quien_autoriza  = models.CharField(max_length=100)
    a_quien_visita  = models.CharField(max_length=100)
    lugar           = models.CharField(max_length=100)
    numero_tarjeta  = models.CharField(max_length=20, blank=True)
    patente         = models.CharField(max_length=15, blank=True)

    # ── Tiempos ───────────────────────────────────────
    fecha           = models.DateField(default=timezone.localdate)
    hora_entrada    = models.DateTimeField(default=timezone.now)
    hora_salida     = models.DateTimeField(null=True, blank=True)

    # ── Auditoría ─────────────────────────────────────
    registrado_por  = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, related_name='visitas_registradas'
    )

    @property
    def esta_adentro(self):
        return self.hora_salida is None

    @property
    def duracion(self):
        if not self.hora_salida: return None
        delta = self.hora_salida - self.hora_entrada
        h, rem = divmod(int(delta.total_seconds()), 3600)
        m = rem // 60
        return f"{h}h {m:02d}m"

    def __str__(self):
        return f"{self.nombre} ({self.rut}) — {self.fecha}"

    class Meta:
        ordering        = ['-hora_entrada']
        verbose_name    = "Registro de Visita"
        verbose_name_plural = "Registro de Visitas"