from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

# 1. GESTIÓN DE FLOTA
class Vehiculo(models.Model):
    TIPO_CHOICES = [
        ('BUS', 'Bus'),
        ('MINIBUS', 'Minibús'), 
        ('VAN', 'Van'),
        ('AUTO', 'Automóvil'),
        ('CAMIONETA', 'Camioneta'),
    ]
    
    patente = models.CharField(max_length=10, unique=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    capacidad = models.IntegerField(help_text="Número de pasajeros")
    
    # COSTOS: El vehículo define la tarifa base
    tarifa_base = models.IntegerField(default=0, help_text="Costo estándar por servicio de este vehículo")
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.patente} ({self.get_tipo_display()}) - ${self.tarifa_base}"

# 2. GESTIÓN DE CHOFERES
class Conductor(models.Model):
    nombre = models.CharField(max_length=100)
    rut = models.CharField(max_length=12, unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    empresa_externa = models.BooleanField(default=False, help_text="¿Es externo?")
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.rut})"

# 3. RUTAS (SOLO GEOGRAFÍA)
class Ruta(models.Model):
    nombre = models.CharField(max_length=100, help_text="Ej: Planta - Centro")
    origen = models.CharField(max_length=100, default="Planta Aurora")
    destino = models.CharField(max_length=100)
    # Se eliminó valor_servicio de aquí, ya que depende del vehículo
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

# 4. REGISTRO DE CONTROL (LA GARITA)
class RegistroSalida(models.Model):
    # Campos automáticos
    fecha_registro = models.DateTimeField(auto_now_add=True)
    registrado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Datos Operativos
    ruta = models.ForeignKey(Ruta, on_delete=models.PROTECT)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.PROTECT)
    conductor = models.ForeignKey(Conductor, on_delete=models.PROTECT)
    cantidad_pasajeros = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    
    # KPIs y Finanzas
    ocupacion_porcentaje = models.FloatField(editable=False, default=0)
    valor_viaje = models.IntegerField(default=0, help_text="Costo final del servicio (Editable por Admin)")

    def save(self, *args, **kwargs):
        # 1. Cálculo de KPI: Ocupación
        if self.vehiculo.capacidad > 0:
            self.ocupacion_porcentaje = (self.cantidad_pasajeros / self.vehiculo.capacidad) * 100
        
        # 2. Cálculo de Costo: Si es nuevo y viene en 0, hereda del vehículo
        # (Esto permite que la Admin lo cambie después sin que se sobrescriba solo)
        if not self.id and self.valor_viaje == 0:
            self.valor_viaje = self.vehiculo.tarifa_base
            
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-fecha_registro']

# 5. SOLICITUDES DE TRANSPORTE (Módulo Empleados - Opcional)
class SolicitudTransporte(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADO', 'Confirmado'),
        ('EN_RUTA', 'En Ruta'),
        ('FINALIZADO', 'Finalizado'),
        ('CANCELADO', 'Cancelado'),
    ]

    solicitante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='solicitudes_transporte')
    fecha_solicitud = models.DateTimeField(default=timezone.now)
    fecha_viaje = models.DateTimeField()
    origen = models.CharField(max_length=100)
    destino = models.CharField(max_length=100)
    cantidad_pasajeros = models.IntegerField()
    motivo = models.TextField(blank=True)
    
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    conductor = models.ForeignKey(Conductor, on_delete=models.SET_NULL, null=True, blank=True)
    
    km_recorridos = models.IntegerField(default=0)
    costo_total = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')

    def __str__(self):
        return f"Viaje {self.id} - {self.destino}"