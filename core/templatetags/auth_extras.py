from django import template

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    """
    Pregunta si el usuario pertenece a un grupo.
    Uso en HTML: {% if request.user|has_group:"NombreGrupo" %}
    """
    # 1. El Jefe (Superusuario) siempre tiene permiso
    if user.is_superuser:
        return True
    
    # 2. Verificar si pertenece al grupo
    return user.groups.filter(name=group_name).exists()