from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
import json

from .forms import CargaFichasForm
from .models import Colaborador
from .services import procesar_fichas


@login_required
def index(request):
    """Vista principal de Dotación: carga de archivo + KPIs básicos."""

    if request.method == 'POST':
        form = CargaFichasForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                resultado = procesar_fichas(request.FILES['archivo'])
                messages.success(
                    request,
                    f"✅ Carga completa. "
                    f"Nuevos: {resultado['creados']} | "
                    f"Actualizados: {resultado['actualizados']} | "
                    f"Omitidos: {resultado['omitidos']}"
                )
                if resultado['errores']:
                    messages.warning(
                        request,
                        f"⚠️ {len(resultado['errores'])} filas con error."
                    )
                    for err in resultado['errores'][:5]:
                        messages.warning(request, err)
            except ValueError as e:
                messages.error(request, f"❌ {str(e)}")
            except Exception as e:
                messages.error(request, f"❌ Error inesperado: {str(e)}")
            return redirect('dotacion_index')
    else:
        form = CargaFichasForm()

    # ── KPIs ──────────────────────────────────────────────────────
    vigentes       = Colaborador.objects.filter(activo=True)
    total_vigentes = vigentes.count()
    total_historico = Colaborador.objects.count()

    sin_contacto = vigentes.filter(
        Q(email__isnull=True) | Q(email='') |
        Q(telefono__isnull=True) | Q(telefono='')
    ).count()

    sexo_data = list(
        vigentes.exclude(sexo__isnull=True).exclude(sexo='')
        .values('sexo').annotate(total=Count('sexo')).order_by('-total')
    )
    nacionalidad_data = list(
        vigentes.exclude(nacionalidad__isnull=True).exclude(nacionalidad='')
        .values('nacionalidad').annotate(total=Count('nacionalidad'))
        .order_by('-total')[:6]
    )
    comuna_data = list(
        vigentes.exclude(comuna__isnull=True).exclude(comuna='')
        .values('comuna').annotate(total=Count('comuna'))
        .order_by('-total')[:8]
    )

    rangos = {'18-25': 0, '26-35': 0, '36-45': 0, '46-55': 0, '56+': 0}
    for c in vigentes.filter(fecha_nacimiento__isnull=False):
        edad = c.edad
        if edad is None:
            continue
        if 18 <= edad <= 25:   rangos['18-25'] += 1
        elif 26 <= edad <= 35: rangos['26-35'] += 1
        elif 36 <= edad <= 45: rangos['36-45'] += 1
        elif 46 <= edad <= 55: rangos['46-55'] += 1
        elif edad >= 56:       rangos['56+']   += 1

    context = {
        'form'                      : form,
        'kpi_vigentes'              : total_vigentes,
        'kpi_historico'             : total_historico,
        'kpi_sin_contacto'          : sin_contacto,
        'chart_sexo_labels'         : json.dumps([d['sexo'] for d in sexo_data]),
        'chart_sexo_values'         : json.dumps([d['total'] for d in sexo_data]),
        'chart_nacionalidad_labels' : json.dumps([d['nacionalidad'] for d in nacionalidad_data]),
        'chart_nacionalidad_values' : json.dumps([d['total'] for d in nacionalidad_data]),
        'chart_comuna_labels'       : json.dumps([d['comuna'] for d in comuna_data]),
        'chart_comuna_values'       : json.dumps([d['total'] for d in comuna_data]),
        'chart_edad_labels'         : json.dumps(list(rangos.keys())),
        'chart_edad_values'         : json.dumps(list(rangos.values())),
    }
    return render(request, 'dotacion/index.html', context)