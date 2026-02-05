from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from datetime import date, datetime, timedelta # <--- ESTO ES LO QUE FALTABA

from .forms import ImportarFichasForm, ImportarAsistenciaForm
from asistencia.utils import importar_fichas_grex, importar_asistencia_grex, analizar_asistencia_dia
from asistencia.models import Colaborador, Marcaje, Anomalia, ReglaAsistencia

@login_required
def dashboard(request):
    # Formularios
    form_fichas = ImportarFichasForm()
    form_asistencia = ImportarAsistenciaForm()
    
    # Datos para visualización
    colaboradores = Colaborador.objects.all().order_by('-fecha_ingreso')[:5]
    total_colaboradores = Colaborador.objects.count()
    total_marcajes = Marcaje.objects.count()
    
    if request.method == 'POST':
        if 'btn_fichas' in request.POST:
            form_fichas = ImportarFichasForm(request.POST, request.FILES)
            if form_fichas.is_valid():
                try:
                    c, a = importar_fichas_grex(request.FILES['archivo'])
                    messages.success(request, f"Fichas: {c} creadas, {a} actualizadas.")
                except Exception as e:
                    messages.error(request, f"Error en Fichas: {e}")
                    
        elif 'btn_asistencia' in request.POST:
            form_asistencia = ImportarAsistenciaForm(request.POST, request.FILES)
            if form_asistencia.is_valid():
                try:
                    nuevos, no_encontrados = importar_asistencia_grex(request.FILES['archivo_asistencia'])
                    messages.success(request, f"Asistencia: {nuevos} marcajes cargados.")
                    if no_encontrados > 0:
                        messages.warning(request, f"Atención: {no_encontrados} marcajes ignorados (RUT no existe en BD).")
                except Exception as e:
                    messages.error(request, f"Error en Asistencia: {e}")
            
            return redirect('dashboard')

    return render(request, 'core/dashboard.html', {
        'form_fichas': form_fichas,
        'form_asistencia': form_asistencia,
        'colaboradores': colaboradores,
        'total_db': total_colaboradores,
        'total_marcajes': total_marcajes
    })

# En core/views.py

@login_required
def reportes(request):
    # 1. Determinar Fecha Seleccionada
    fecha_input = request.GET.get('fecha')
    if fecha_input:
        try:
            fecha_seleccionada = datetime.strptime(fecha_input, '%Y-%m-%d').date()
        except:
            fecha_seleccionada = date.today()
    else:
        fecha_seleccionada = date.today()

    # 2. Calcular Rango Semanal (Lunes a Domingo)
    # weekday(): 0=Lunes, 6=Domingo
    inicio_semana = fecha_seleccionada - timedelta(days=fecha_seleccionada.weekday())
    fin_semana = inicio_semana + timedelta(days=6)

    # 3. EJECUTAR ANÁLISIS EN BUCLE (Día por día)
    total_anomalias_creadas = 0
    dia_actual = inicio_semana
    
    # Recorremos cada día de la semana seleccionada
    while dia_actual <= fin_semana:
        # Solo procesamos días pasados o hoy (no el futuro)
        if dia_actual <= date.today():
            c = analizar_asistencia_dia(dia_actual)
            total_anomalias_creadas += c
        dia_actual += timedelta(days=1)

    # 4. OBTENER DATOS DE LA SEMANA COMPLETA
    qs = Anomalia.objects.filter(fecha__range=[inicio_semana, fin_semana])
    
    # KPIs
    total_minutos = qs.aggregate(Sum('minutos_perdidos'))['minutos_perdidos__sum'] or 0
    horas_perdidas = round(total_minutos / 60, 1)
    dinero_perdido = int(horas_perdidas * 5000)

    # Gráficos
    datos_tipo = qs.values('tipo').annotate(total=Count('id')).order_by('-total')
    datos_area = qs.values('colaborador__area').annotate(
        total=Count('id'),
        minutos=Sum('minutos_perdidos')
    ).order_by('-minutos')

    return render(request, 'core/reportes.html', {
        'fecha': fecha_seleccionada,
        'inicio_semana': inicio_semana, # Pasamos esto al template
        'fin_semana': fin_semana,       # Y esto también
        'creadas': qs.count(), # Total real en BD
        'horas_perdidas': horas_perdidas,
        'dinero_perdido': dinero_perdido,
        'datos_tipo': list(datos_tipo), 
        'datos_area': list(datos_area)
    })