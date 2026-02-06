from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def group_required(*group_names):
    """
    Decorador para restringir el acceso a vistas basado en los grupos del usuario.
    Uso: @group_required('Administradores', 'RRHH')
    
    Si el usuario es Superuser, siempre pasa.
    Si no tiene el grupo, redirige al login (o podrías lanzar 403).
    """
    def in_groups(user):
        if user.is_authenticated:
            # La "Llave Maestra": El superusuario siempre entra
            if user.is_superuser:
                return True
            
            # Verifica si el usuario tiene alguno de los grupos permitidos
            if user.groups.filter(name__in=group_names).exists():
                return True
        return False

    return user_passes_test(in_groups, login_url='login') # Redirige al login si falla