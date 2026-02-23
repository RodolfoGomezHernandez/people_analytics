from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    """Vista principal del sistema. Solo navegación y bienvenida."""
    return render(request, 'core/dashboard.html')