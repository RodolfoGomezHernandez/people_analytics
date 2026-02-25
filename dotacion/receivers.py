"""
Receptores internos de dotación.
Las apps externas deben conectarse en su propio apps.py.
"""
from django.dispatch import receiver
from .signals import (
    colaborador_bloqueado,
    colaborador_desbloqueado,
    colaborador_finiquitado,
)


@receiver(colaborador_bloqueado)
def log_bloqueo(sender, colaborador, motivo, cambiado_por, **kwargs):
    """
    Receptor interno: puedes agregar lógica aquí.
    Ej: enviar email, notificar slack, etc.
    Por ahora solo sirve como punto de extensión.
    """
    pass


@receiver(colaborador_desbloqueado)
def log_desbloqueo(sender, colaborador, motivo, cambiado_por, **kwargs):
    pass


@receiver(colaborador_finiquitado)
def log_finiquito(sender, colaborador, motivo, cambiado_por, **kwargs):
    pass