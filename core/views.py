from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

# Importamos modelos y formularios
from .forms import CargaArchivoForm
from dotacion.models import Colaborador
from .services import procesar_archivo_dotacion, procesar_archivo_asistencia

@login_required
def dashboard(request):
    # 1. Lógica de Carga de Archivos (POST)
    if request.method == 'POST':
        form = CargaArchivoForm(request.POST, request.FILES)
        if form.is_valid():
            carga = form.save(commit=False)
            carga.usuario = request.user
            carga.save()
            
            try:
                # Procesamos según el tipo seleccionado
                if carga.tipo == 'DOTACION':
                    procesar_archivo_dotacion(carga)
                    messages.success(request, f"✅ Dotación actualizada correctamente. {carga.log_errores}")
                elif carga.tipo == 'ASISTENCIA':
                    # procesar_archivo_asistencia(carga) # Descomentar cuando tengamos el servicio listo
                    messages.warning(request, "⚠️ El procesador de asistencia aún está en construcción.")
                
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f"❌ Error crítico: {str(e)}")
                return redirect('dashboard')
    else:
        form = CargaArchivoForm()

    # 2. Lógica de KPIs (GET) - Para llenar las tarjetas de arriba
    total_colaboradores = Colaborador.objects.count()
    activos = Colaborador.objects.filter(activo=True).count()
    
    # Contrataciones últimos 30 días
    mes_pasado = timezone.now().date() - timedelta(days=30)
    nuevos_ingresos = Colaborador.objects.filter(fecha_ingreso__gte=mes_pasado).count()

    context = {
        'form': form,
        'kpi_total': total_colaboradores,
        'kpi_activos': activos,
        'kpi_nuevos': nuevos_ingresos,
    }
    
    return render(request, 'core/dashboard.html', context)

# La vista 'subir_archivo' ya no es necesaria, la integramos arriba.
def subir_archivo(request):
    return redirect('dashboard')