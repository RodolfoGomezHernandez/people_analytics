from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Avg, Count
from django.http import HttpResponse
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill

from .models import Vehiculo, Conductor, RegistroSalida, Ruta
from .forms import VehiculoForm, ConductorForm, RegistroGuardiaForm, EdicionAdminForm

# --- 1. SEMÁFORO: Decide a dónde va el usuario ---
@login_required
def transporte_home(request):
    # Si es Guardia y NO es superusuario, va a la garita
    if request.user.groups.filter(name='Guardias').exists() and not request.user.is_superuser:
        return redirect('control_salida')
    # Si es Admin o Staff, va al Dashboard
    return redirect('dashboard_transporte')

# --- 2. VISTA GUARDIA (Y ADMIN): Control de Salida ---
@login_required
def registro_control_salida(request):
    # Permitimos acceso a Guardias O Superusuarios
    es_guardia = request.user.groups.filter(name='Guardias').exists()
    es_admin = request.user.is_superuser
    
    if not es_guardia and not es_admin:
         messages.error(request, "Acceso no autorizado.")
         return redirect('dashboard_transporte')

    if request.method == 'POST':
        form = RegistroGuardiaForm(request.POST)
        if form.is_valid():
            registro = form.save(commit=False)
            registro.registrado_por = request.user
            # El valor_viaje se autocalcula en el modelo (models.py) si no se especifica
            registro.save()
            messages.success(request, f'✅ Salida registrada: {registro.vehiculo.patente}')
            return redirect('control_salida')
    else:
        form = RegistroGuardiaForm()

    # Mostramos los últimos 5 registros
    registros_hoy = RegistroSalida.objects.order_by('-fecha_registro')[:5]
    
    return render(request, 'transporte/control_salida.html', {
        'form': form, 
        'registros': registros_hoy,
        'es_admin': es_admin
    })

# --- 3. VISTA ADMIN: Dashboard Completo ---
@login_required
def dashboard_transporte(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return redirect('transporte_home')

    registros = RegistroSalida.objects.all()
    
    # KPIs CORREGIDOS (Ahora usan 'valor_viaje' en vez de ruta__valor)
    total_viajes = registros.count()
    costo_total = registros.aggregate(Sum('valor_viaje'))['valor_viaje__sum'] or 0
    ocupacion_promedio = registros.aggregate(Avg('ocupacion_porcentaje'))['ocupacion_porcentaje__avg'] or 0
    
    # Gráfico
    viajes_por_vehiculo = registros.values('vehiculo__patente').annotate(total=Count('id'))
    labels_v = [x['vehiculo__patente'] for x in viajes_por_vehiculo]
    data_v = [x['total'] for x in viajes_por_vehiculo]

    # Últimos registros para la tabla de edición
    ultimos_registros = RegistroSalida.objects.order_by('-fecha_registro')[:10]

    context = {
        'total_viajes': total_viajes,
        'costo_total': costo_total,
        'ocupacion_promedio': round(ocupacion_promedio, 1),
        'labels_v': labels_v,
        'data_v': data_v,
        'ultimos_registros': ultimos_registros, # Para la tabla con botón editar
        'vehiculos': Vehiculo.objects.filter(activo=True),
    }
    return render(request, 'transporte/dashboard_admin.html', context)

# --- 4. NUEVA: Editar Registro (Solo Admin) ---
@login_required
def editar_registro(request, registro_id):
    if not request.user.is_superuser:
        messages.error(request, "Solo administradores pueden editar registros.")
        return redirect('dashboard_transporte')
        
    registro = get_object_or_404(RegistroSalida, id=registro_id)
    
    if request.method == 'POST':
        form = EdicionAdminForm(request.POST, instance=registro)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registro actualizado correctamente.')
            return redirect('dashboard_transporte')
    else:
        form = EdicionAdminForm(instance=registro)
        
    return render(request, 'transporte/editar_registro.html', {'form': form, 'registro': registro})

# --- 5. UTILIDADES Y CREACIÓN ---
@login_required
def exportar_excel_transporte(request):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=Transporte_{datetime.now().strftime("%d%m%Y")}.xlsx'

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Bitácora"
    
    # Encabezados
    headers = ['Fecha', 'Vehículo', 'Ruta', 'Pasajeros', 'Costo Final', 'Usuario']
    ws.append(headers)
    
    for r in RegistroSalida.objects.all():
        ws.append([
            r.fecha_registro.strftime("%d/%m/%Y %H:%M"),
            r.vehiculo.patente,
            r.ruta.nombre,
            r.cantidad_pasajeros,
            r.valor_viaje, # CORREGIDO: Usamos el valor real guardado
            r.registrado_por.username if r.registrado_por else "Sistema"
        ])
    
    wb.save(response)
    return response

@login_required
def crear_vehiculo(request):
    if request.method == 'POST':
        form = VehiculoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vehículo registrado.')
            return redirect('dashboard_transporte')
    else:
        form = VehiculoForm()
    return render(request, 'transporte/crear_vehiculo.html', {'form': form, 'titulo': 'Nuevo Vehículo'})

@login_required
def crear_conductor(request):
    if request.method == 'POST':
        form = ConductorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Conductor registrado.')
            return redirect('dashboard_transporte')
    else:
        form = ConductorForm()
    return render(request, 'transporte/crear_conductor.html', {'form': form, 'titulo': 'Nuevo Conductor'})