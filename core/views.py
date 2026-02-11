from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import date
import json

# Importamos modelos y formularios
from .forms import CargaArchivoForm
from dotacion.models import Colaborador
from .services import procesar_archivo_dotacion, procesar_archivo_asistencia

def calcular_edad(fecha_nacimiento):
    if not fecha_nacimiento: return 0
    today = date.today()
    return today.year - fecha_nacimiento.year - ((today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))

@login_required
def dashboard(request):
    # --- LÓGICA DE CARGA (Sin cambios) ---
    if request.method == 'POST':
        form = CargaArchivoForm(request.POST, request.FILES)
        if form.is_valid():
            carga = form.save(commit=False)
            carga.usuario = request.user
            carga.save()
            try:
                if carga.tipo == 'DOTACION':
                    procesar_archivo_dotacion(carga)
                    messages.success(request, f"✅ Dotación actualizada. {carga.log_errores}")
                elif carga.tipo == 'ASISTENCIA':
                    messages.warning(request, "⚠️ Módulo Asistencia en construcción.")
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f"❌ Error crítico: {str(e)}")
                return redirect('dashboard')
    else:
        form = CargaArchivoForm()

    # --- LÓGICA DE KPIS (NUEVO) ---
    
    # 1. Filtros Base (Vigentes)
    colaboradores = Colaborador.objects.filter(activo=True)
    total_activos = colaboradores.count()
    
    # 2. Distribución por Sexo (KPI 6)
    sexo_data = list(colaboradores.values('sexo').annotate(total=Count('sexo')).order_by('-total'))
    
    # 3. Nacionalidad (KPI 8)
    nacionalidad_data = list(colaboradores.values('nacionalidad').annotate(total=Count('nacionalidad')).order_by('-total')[:5]) # Top 5
    
    # 4. Comunas (KPI 7)
    comuna_data = list(colaboradores.values('comuna').annotate(total=Count('comuna')).order_by('-total')[:7]) # Top 7
    
    # 5. Rango Etario (KPI 4) - Calculado en Python
    edades = [c.edad for c in colaboradores if c.fecha_nacimiento]
    rangos = {'18-25': 0, '26-35': 0, '36-45': 0, '46-55': 0, '56+': 0}
    for edad in edades:
        if edad is None: continue
        if 18 <= edad <= 25: rangos['18-25'] += 1
        elif 26 <= edad <= 35: rangos['26-35'] += 1
        elif 36 <= edad <= 45: rangos['36-45'] += 1
        elif 46 <= edad <= 55: rangos['46-55'] += 1
        elif edad >= 56: rangos['56+'] += 1

    # 6. Datos Faltantes (KPI 11)
    sin_email = colaboradores.filter(Q(email__isnull=True) | Q(email='')).count()
    sin_telefono = colaboradores.filter(Q(telefono__isnull=True) | Q(telefono='')).count()
    
    # Contexto para el template
    context = {
        'form': form,
        'kpi_total': Colaborador.objects.count(),
        'kpi_activos': total_activos,
        'kpi_sin_contacto': sin_email + sin_telefono,
        
        # Datos para Gráficos (JSON para JS)
        'chart_sexo_labels': json.dumps([d['sexo'] for d in sexo_data]),
        'chart_sexo_values': json.dumps([d['total'] for d in sexo_data]),
        
        'chart_nacionalidad_labels': json.dumps([d['nacionalidad'] for d in nacionalidad_data]),
        'chart_nacionalidad_values': json.dumps([d['total'] for d in nacionalidad_data]),
        
        'chart_comuna_labels': json.dumps([d['comuna'] for d in comuna_data]),
        'chart_comuna_values': json.dumps([d['total'] for d in comuna_data]),
        
        'chart_edad_labels': json.dumps(list(rangos.keys())),
        'chart_edad_values': json.dumps(list(rangos.values())),
    }
    
    return render(request, 'core/dashboard.html', context)