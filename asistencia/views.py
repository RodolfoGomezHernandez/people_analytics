from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from .forms import CargaEstadiaForm
from .models import RegistroAsistencia, Anomalia
from .services import procesar_estadia


@login_required
def index(request):

    if request.method == 'POST':
        form = CargaEstadiaForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                resultado = procesar_estadia(request.FILES['archivo'])
                messages.success(
                    request,
                    f"✅ Estadía procesada. "
                    f"Nuevos: {resultado['registros_creados']} | "
                    f"Actualizados: {resultado['registros_actualizados']} | "
                    f"RUTs no encontrados: {resultado['ruts_no_encontrados']} | "
                    f"Anomalías: {resultado['anomalias_creadas']}"
                )
                if resultado['errores']:
                    for err in resultado['errores'][:5]:
                        messages.warning(request, f"⚠️ {err}")
            except ValueError as e:
                messages.error(request, f"❌ {str(e)}")
            except Exception as e:
                messages.error(request, f"❌ Error inesperado: {str(e)}")
            return redirect('asistencia_index')
    else:
        form = CargaEstadiaForm()

    hoy = timezone.now().date()
    registros_hoy  = (
        RegistroAsistencia.objects
        .filter(fecha=hoy)
        .select_related('colaborador')
        .order_by('colaborador__nombre_completo')
    )
    total_hoy      = registros_hoy.count()
    anomalias_hoy  = Anomalia.objects.filter(registro__fecha=hoy).count()
    sin_salida_hoy = registros_hoy.filter(hora_salida__isnull=True).count()

    ultimas_fechas = (
        RegistroAsistencia.objects
        .values('fecha')
        .distinct()
        .order_by('-fecha')[:7]
    )

    context = {
        'form'           : form,
        'hoy'            : hoy,
        'total_hoy'      : total_hoy,
        'anomalias_hoy'  : anomalias_hoy,
        'sin_salida_hoy' : sin_salida_hoy,
        'registros_hoy'  : registros_hoy[:50],
        'ultimas_fechas' : ultimas_fechas,
    }
    return render(request, 'asistencia/index.html', context)