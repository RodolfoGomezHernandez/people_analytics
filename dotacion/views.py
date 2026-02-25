from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.db.models.functions import TruncWeek
from datetime import date, timedelta
import json

from .forms import CargaFichasForm
from .models import Colaborador
from .services import procesar_fichas


@login_required
def index(request):
    """Vista principal: solo maneja carga de archivo. Los datos van por API."""

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
                    messages.warning(request, f"⚠️ {len(resultado['errores'])} filas con error.")
                    for err in resultado['errores'][:5]:
                        messages.warning(request, err)
            except ValueError as e:
                messages.error(request, f"❌ {str(e)}")
            except Exception as e:
                messages.error(request, f"❌ Error inesperado: {str(e)}")
            return redirect('dotacion_index')
    else:
        form = CargaFichasForm()

    # Fechas por defecto para el filtro (se pasan al template para inicializar el JS)
    hoy = date.today()
    fecha_inicio_default = date(hoy.year, 1, 1).strftime('%Y-%m-%d')
    fecha_fin_default    = hoy.strftime('%Y-%m-%d')

    return render(request, 'dotacion/index.html', {
        'form'                : form,
        'fecha_inicio_default': fecha_inicio_default,
        'fecha_fin_default'   : fecha_fin_default,
    })


@login_required
def api_kpis(request):
    """API que devuelve todos los datos para los gráficos según rango de fechas."""

    inicio_str = request.GET.get('inicio')
    fin_str    = request.GET.get('fin')

    hoy = date.today()

    try:
        from datetime import datetime
        inicio = datetime.strptime(inicio_str, '%Y-%m-%d').date() if inicio_str else date(hoy.year, 1, 1)
        fin    = datetime.strptime(fin_str,    '%Y-%m-%d').date() if fin_str    else hoy
    except ValueError:
        inicio = date(hoy.year, 1, 1)
        fin    = hoy

    # ── Colaboradores vigentes al final del periodo ────────────────────
    vigentes = Colaborador.objects.filter(
        activo=True,
        fecha_ingreso__lte=fin
    )

    # ── KPIs numéricos ─────────────────────────────────────────────────
    total_vigentes  = vigentes.count()
    total_historico = Colaborador.objects.count()
    sin_contacto    = vigentes.filter(
        Q(email__isnull=True) | Q(email='') |
        Q(telefono__isnull=True) | Q(telefono='')
    ).count()

    # ── 1. Dotación activa por semana ──────────────────────────────────
    todos = list(
        Colaborador.objects
        .filter(fecha_ingreso__isnull=False, fecha_ingreso__lte=fin)
        .values('fecha_ingreso', 'fecha_termino_contrato')
    )

    semana = inicio - timedelta(days=inicio.weekday())
    dotacion_labels, dotacion_values = [], []
    while semana <= fin:
        count = sum(
            1 for c in todos
            if c['fecha_ingreso'] <= semana
            and (c['fecha_termino_contrato'] is None or c['fecha_termino_contrato'] >= semana)
        )
        dotacion_labels.append(semana.strftime('%d/%m/%Y'))
        dotacion_values.append(count)
        semana += timedelta(weeks=1)

    # ── 2. Contrataciones por semana (dentro del periodo) ──────────────
    contrataciones_raw = (
        Colaborador.objects
        .filter(fecha_ingreso__isnull=False, fecha_ingreso__range=[inicio, fin])
        .annotate(semana=TruncWeek('fecha_ingreso'))
        .values('semana')
        .annotate(total=Count('rut'))
        .order_by('semana')
    )
    contrataciones_labels = [r['semana'].strftime('%d/%m/%Y') for r in contrataciones_raw]
    contrataciones_values = [r['total'] for r in contrataciones_raw]

    # ── 3. Rango etario ────────────────────────────────────────────────
    rangos = {'18-25': 0, '26-35': 0, '36-45': 0, '46-55': 0, '56+': 0}
    for c in vigentes.filter(fecha_nacimiento__isnull=False):
        edad = c.edad
        if edad is None: continue
        if   18 <= edad <= 25: rangos['18-25'] += 1
        elif 26 <= edad <= 35: rangos['26-35'] += 1
        elif 36 <= edad <= 45: rangos['36-45'] += 1
        elif 46 <= edad <= 55: rangos['46-55'] += 1
        elif edad >= 56:       rangos['56+']   += 1

    # ── 4. Nivel educacional ───────────────────────────────────────────
    escolaridad_data = list(
        vigentes.exclude(escolaridad__isnull=True).exclude(escolaridad='')
        .values('escolaridad').annotate(total=Count('rut'))
        .order_by('-total')
    )

    # ── 5. Nacionalidades ──────────────────────────────────────────────
    nacionalidad_data = list(
        vigentes.exclude(nacionalidad__isnull=True).exclude(nacionalidad='')
        .values('nacionalidad').annotate(total=Count('rut'))
        .order_by('-total')[:8]
    )

    # ── 6. Sectores / Comunas ──────────────────────────────────────────
    comuna_data = list(
        vigentes.exclude(comuna__isnull=True).exclude(comuna='')
        .values('comuna').annotate(total=Count('rut'))
        .order_by('-total')[:12]
    )

    # ── 7. Género ──────────────────────────────────────────────────────
    sexo_data = list(
        vigentes.exclude(sexo__isnull=True).exclude(sexo='')
        .values('sexo').annotate(total=Count('rut')).order_by('-total')
    )

    # ── 8. Permanencia (en rangos de meses) ────────────────────────────
    rangos_perm = {
        '< 3 meses': 0, '3-6 meses': 0, '6-12 meses': 0,
        '1-2 años': 0, '2-5 años': 0, '5+ años': 0
    }
    for c in vigentes.filter(fecha_ingreso__isnull=False):
        m = c.meses_permanencia
        if m is None: continue
        if   m < 3:   rangos_perm['< 3 meses']  += 1
        elif m < 6:   rangos_perm['3-6 meses']   += 1
        elif m < 12:  rangos_perm['6-12 meses']  += 1
        elif m < 24:  rangos_perm['1-2 años']     += 1
        elif m < 60:  rangos_perm['2-5 años']     += 1
        else:         rangos_perm['5+ años']      += 1

    # ── 9. Personal de planta (tipo contrato Indefinido) ───────────────
    planta_data = list(
        vigentes.exclude(tipo_contrato__isnull=True).exclude(tipo_contrato='')
        .values('tipo_contrato').annotate(total=Count('rut'))
        .order_by('-total')
    )

    return JsonResponse({
        # KPIs
        'kpi_vigentes'  : total_vigentes,
        'kpi_historico' : total_historico,
        'kpi_sin_contacto': sin_contacto,
        # Gráficos
        'dotacion'        : {'labels': dotacion_labels,        'values': dotacion_values},
        'contrataciones'  : {'labels': contrataciones_labels,  'values': contrataciones_values},
        'edad'            : {'labels': list(rangos.keys()),     'values': list(rangos.values())},
        'escolaridad'     : {'labels': [d['escolaridad'] for d in escolaridad_data],  'values': [d['total'] for d in escolaridad_data]},
        'nacionalidad'    : {'labels': [d['nacionalidad'] for d in nacionalidad_data],'values': [d['total'] for d in nacionalidad_data]},
        'comuna'          : {'labels': [d['comuna'] for d in comuna_data],            'values': [d['total'] for d in comuna_data]},
        'sexo'            : {'labels': [d['sexo'] for d in sexo_data],                'values': [d['total'] for d in sexo_data]},
        'permanencia'     : {'labels': list(rangos_perm.keys()), 'values': list(rangos_perm.values())},
        'tipo_contrato'   : {'labels': [d['tipo_contrato'] for d in planta_data],     'values': [d['total'] for d in planta_data]},
    })