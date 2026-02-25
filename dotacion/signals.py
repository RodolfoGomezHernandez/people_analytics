from django.dispatch import Signal

# ── Señales públicas que cualquier app puede escuchar ─
# Cada señal incluye el colaborador y contexto relevante

colaborador_bloqueado = Signal()
# kwargs: colaborador, motivo, cambiado_por

colaborador_desbloqueado = Signal()
# kwargs: colaborador, motivo, cambiado_por

colaborador_finiquitado = Signal()
# kwargs: colaborador, motivo, cambiado_por

colaborador_creado = Signal()
# kwargs: colaborador

colaborador_actualizado = Signal()
# kwargs: colaborador, campos_modificados