from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
import json
from django.db.models.functions import TruncWeek
from datetime import date, timedelta

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

  # ── KPIs base ─────────────────────────────────────────────────
    vigentes        = Colaborador.objects.filter(activo=True)
    total_vigentes  = vigentes.count()
    total_historico = Colaborador.objects.count()

    sin_contacto = vigentes.filter(
        Q(email__isnull=True) | Q(email='') |
        Q(telefono__isnull=True) | Q(telefono='')
    ).count()

    # ── Contrataciones por semana (últimas 52 semanas) ─────────────
    hoy          = date.today()
    inicio_52    = hoy - timedelta(weeks=52)

    contrataciones_raw = (
        Colaborador.objects
        .filter(fecha_ingreso__isnull=False, fecha_ingreso__gte=inicio_52)
        .annotate(semana=TruncWeek('fecha_ingreso'))
        .values('semana')
        .annotate(total=Count('rut'))
        .order_by('semana')
    )
    chart_contrataciones_labels = json.dumps(
        [r['semana'].strftime('%d/%m/%Y') for r in contrataciones_raw]
    )
    chart_contrataciones_values = json.dumps(
        [r['total'] for r in contrataciones_raw]
    )

    # ── Dotación activa por semana (últimas 52 semanas) ────────────
    # 1 sola query, cálculo en Python para evitar N queries
    todos = list(
        Colaborador.objects
        .filter(fecha_ingreso__isnull=False)
        .values('fecha_ingreso', 'fecha_termino_contrato')
    )

    semana_cursor = inicio_52 - timedelta(days=inicio_52.weekday())  # lunes
    dotacion_labels  = []
    dotacion_values  = []

    while semana_cursor <= hoy:
        count = sum(
            1 for c in todos
            if c['fecha_ingreso'] <= semana_cursor
            and (
                c['fecha_termino_contrato'] is None
                or c['fecha_termino_contrato'] >= semana_cursor
            )
        )
        dotacion_labels.append(semana_cursor.strftime('%d/%m/%Y'))
        dotacion_values.append(count)
        semana_cursor += timedelta(weeks=1)

    chart_dotacion_labels = json.dumps(dotacion_labels)
    chart_dotacion_values = json.dumps(dotacion_values)

    # ── Gráficos demográficos (existentes) ─────────────────────────
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
        if   18 <= edad <= 25: rangos['18-25'] += 1
        elif 26 <= edad <= 35: rangos['26-35'] += 1
        elif 36 <= edad <= 45: rangos['36-45'] += 1
        elif 46 <= edad <= 55: rangos['46-55'] += 1
        elif edad >= 56:       rangos['56+']   += 1

    context = {
        'form'                          : form,
        'kpi_vigentes'                  : total_vigentes,
        'kpi_historico'                 : total_historico,
        'kpi_sin_contacto'              : sin_contacto,
        # Nuevos
        'chart_dotacion_labels'         : chart_dotacion_labels,
        'chart_dotacion_values'         : chart_dotacion_values,
        'chart_contrataciones_labels'   : chart_contrataciones_labels,
        'chart_contrataciones_values'   : chart_contrataciones_values,
        # Existentes
        'chart_sexo_labels'             : json.dumps([d['sexo'] for d in sexo_data]),
        'chart_sexo_values'             : json.dumps([d['total'] for d in sexo_data]),
        'chart_nacionalidad_labels'     : json.dumps([d['nacionalidad'] for d in nacionalidad_data]),
        'chart_nacionalidad_values'     : json.dumps([d['total'] for d in nacionalidad_data]),
        'chart_comuna_labels'           : json.dumps([d['comuna'] for d in comuna_data]),
        'chart_comuna_values'           : json.dumps([d['total'] for d in comuna_data]),
        'chart_edad_labels'             : json.dumps(list(rangos.keys())),
        'chart_edad_values'             : json.dumps(list(rangos.values())),
    }
    return render(request, 'dotacion/index.html', context)