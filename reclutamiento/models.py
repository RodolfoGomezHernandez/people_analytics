from django.db import models
from django.utils import timezone
# Importamos Colaborador solo si necesitamos vincular (opcional por ahora)

class SolicitudDotacion(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente de Aprobación'),
        ('ABIERTA', 'Buscando Candidatos'),
        ('CERRADA', 'Completada'),
        ('RECHAZADA', 'Rechazada'),
    ]
    
    # ¿Quién pide? (Idealmente el usuario logueado, por ahora texto libre)
    solicitante = models.CharField(max_length=100, help_text="Nombre del Jefe/Gerente")
    area = models.CharField(max_length=100)
    cargo = models.CharField(max_length=100)
    cantidad = models.IntegerField(default=1)
    fecha_necesidad = models.DateField(help_text="¿Para cuándo se necesita?")
    motivo = models.TextField(blank=True, help_text="Ej: Reemplazo, Aumento de temporada")
    
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.cargo} ({self.cantidad}) - {self.area}"

class Candidato(models.Model):
    ESTADOS_PROCESO = [
        ('NUEVO', 'Recién llegado (Bot)'),
        ('REVISION', 'En revisión de documentos'),
        ('APTO', 'Aprobado para entrevista'),
        ('CONTRATADO', 'Contratado (Enviar a Grex)'),
        ('DESCARTADO', 'Descartado'),
    ]

    # Datos Personales (Capturados por WhatsApp)
    rut = models.CharField(max_length=12, unique=True)
    nombre_completo = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20, help_text="Número de WhatsApp")
    email = models.EmailField(blank=True, null=True)
    
    # Documentos (Fotos)
    foto_cedula_frente = models.ImageField(upload_to='candidatos/cedulas/', blank=True, null=True)
    foto_cedula_dorso = models.ImageField(upload_to='candidatos/cedulas/', blank=True, null=True)
    foto_selfie = models.ImageField(upload_to='candidatos/selfies/', blank=True, null=True)
    
    # Gestión
    solicitud_asociada = models.ForeignKey(SolicitudDotacion, on_delete=models.SET_NULL, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS_PROCESO, default='NUEVO')
    fecha_postulacion = models.DateTimeField(auto_now_add=True)
    
    # Campo para IA futura (Score de coincidencia)
    
    observacion_ia = models.TextField(blank=True, null=True)

    stage = models.CharField(max_length=50, default='INICIO')
    def __str__(self):
        return f"{self.nombre_completo} ({self.rut})"
