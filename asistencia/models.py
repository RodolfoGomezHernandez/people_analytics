
from django.db import models


class Colaborador(models.Model):
    rut = models.CharField(max_length=15, unique=True, primary_key=True)
    codigo_ficha = models.CharField(max_length=20, blank=True, null=True)
    nombres = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100, blank=True, null=True)
    
    # Datos Organizacionales
    area = models.CharField(max_length=100, blank=True, null=True)
    seccion = models.CharField(max_length=100, blank=True, null=True)
    cargo = models.CharField(max_length=150, blank=True, null=True)
    estado_ficha = models.CharField(max_length=20, default='Vigente')
    turno = models.CharField(max_length=100, blank=True, null=True, help_text="Turno asignado en Grex")
    
    # Datos Demográficos
    fecha_ingreso = models.DateField(null=True, blank=True)
    sexo = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    comuna = models.CharField(max_length=100, blank=True, null=True)
    escolaridad = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.nombres} {self.apellido_paterno} ({self.rut})"

    class Meta:
        verbose_name = "Colaborador"
        verbose_name_plural = "Colaboradores"

# En core/models.py

class Marcaje(models.Model):
    # Vinculación directa con el Colaborador por RUT
    colaborador = models.ForeignKey(Colaborador, on_delete=models.CASCADE, related_name='marcajes')
    
    fecha = models.DateField()
    hora = models.TimeField()
    tipo_movimiento = models.CharField(max_length=50) # Entrada / Salida
    dispositivo = models.CharField(max_length=100, blank=True, null=True)
    
    # Para evitar duplicados si subes el mismo excel dos veces
    class Meta:
        verbose_name = "Marcaje"
        unique_together = ('colaborador', 'fecha', 'hora') 

    def __str__(self):
        return f"{self.colaborador} - {self.fecha} {self.hora}"
    

#CONFIGURACIÓN DE REGLAS DE ASISTENCIA Y ANOMALÍAS

class ReglaAsistencia(models.Model):
    nombre = models.CharField(max_length=50, help_text="Ej: Turno Día Packing")
    
    # Filtros de Aplicación (El sistema buscará la regla más específica)
    area = models.CharField(max_length=100, blank=True, null=True)
    seccion = models.CharField(max_length=100, blank=True, null=True)
    
    # NUEVO: Discriminador de Turno
    palabra_clave_turno = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        help_text="Texto que debe contener el turno del colaborador para aplicar esta regla. Ej: '08:00' o 'NOCHE'"
    )

    # Definición Horaria
    entrada_teorica = models.TimeField()
    salida_teorica = models.TimeField()
    es_turno_noche = models.BooleanField(default=False, help_text="Marcar si la jornada termina al día siguiente.")

    # Colación
    inicio_colacion = models.TimeField()
    fin_colacion = models.TimeField()
    tiempo_maximo_colacion = models.IntegerField(default=60)
    
    holgura_minutos = models.IntegerField(default=15)

    def __str__(self):
        return f"{self.nombre} ({self.entrada_teorica} - {self.salida_teorica})"

class Anomalia(models.Model):
    TIPOS = [
        ('FALTA', 'Ausencia injustificada'),
        ('ATRASO', 'Atraso en entrada'),
        ('SALIDA_ANTICIPADA', 'Salida antes de hora'),
        ('EXCESO_COLACION', 'Exceso tiempo colación'),
        ('IMPAR', 'Marcaje impar (falta entrada o salida)'),
    ]
    
    colaborador = models.ForeignKey(Colaborador, on_delete=models.CASCADE)
    fecha = models.DateField()
    tipo = models.CharField(max_length=50, choices=TIPOS)
    detalle = models.TextField(blank=True) # Ej: "Tomó 85 min de colación (Permitido: 60)"
    minutos_perdidos = models.IntegerField(default=0) # Clave para tu gráfico de HH perdidas

    class Meta:
        verbose_name = "Anomalía Detectada"
        unique_together = ('colaborador', 'fecha', 'tipo')

    def __str__(self):
        return f"{self.fecha} - {self.colaborador.rut} - {self.tipo}"

