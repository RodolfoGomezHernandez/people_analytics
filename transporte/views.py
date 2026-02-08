from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Avg, Count
from django.db.models.functions import TruncWeek
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from datetime import datetime, date, timedelta # <--- Importante
from django.utils.timezone import now # <--- ESTE ES EL QUE FALTABA
import openpyxl

from .models import Vehiculo, Conductor, RegistroSalida, Ruta
from .forms import VehiculoForm, ConductorForm, RegistroGuardiaForm, EdicionAdminForm, RutaForm

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

# --- 3. VISTA ADMIN: Dashboard Completo (CON MEMORIA DE SESIÓN) ---
@login_required
def dashboard_transporte(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return redirect('transporte_home')

    # --- LÓGICA DE MEMORIA (SESIONES) ---
    # 1. Intentamos obtener fechas de la URL
    inicio_get = request.GET.get('inicio')
    fin_get = request.GET.get('fin')

    # 2. Si hay datos en URL, actualizamos la sesión
    if inicio_get:
        request.session['transporte_inicio'] = inicio_get
    if fin_get:
        request.session['transporte_fin'] = fin_get

    # 3. Recuperamos de la sesión o definimos defaults (Mes actual)
    fecha_hoy = now().date()
    inicio_defecto = date(fecha_hoy.year, fecha_hoy.month, 1).strftime('%Y-%m-%d')
    fin_defecto = fecha_hoy.strftime('%Y-%m-%d')

    fecha_inicio = request.session.get('transporte_inicio', inicio_defecto)
    fecha_fin = request.session.get('transporte_fin', fin_defecto)

    # --- 4. PAGINACIÓN Y FILTRADO ---
    items_por_pagina = request.GET.get('page_size', '10')
    if items_por_pagina not in ['10', '20', '50', '100']:
        items_por_pagina = '10'
    
    # Filtramos por las fechas de memoria
    registros_tabla = RegistroSalida.objects.filter(
        fecha_registro__date__range=[fecha_inicio, fecha_fin]
    ).select_related('vehiculo', 'ruta').order_by('-fecha_registro')

    # Limite duro de 3000 para performance
    registros_tabla = registros_tabla[:3000]

    paginator = Paginator(registros_tabla, int(items_por_pagina))
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Generar rango de páginas inteligente (ej: 1 ... 5 6 7 ... 20)
    custom_range = paginator.get_elided_page_range(page_obj.number, on_each_side=1, on_ends=1)

    context = {
        'page_obj': page_obj,
        'page_size': items_por_pagina,
        'custom_range': custom_range,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
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
    
    headers = ['Fecha', 'Vehículo', 'Ruta', 'Pasajeros', 'Costo Final', 'Usuario']
    ws.append(headers)
    
    for r in RegistroSalida.objects.all().select_related('vehiculo', 'ruta', 'registrado_por'):
        ws.append([
            r.fecha_registro.strftime("%d/%m/%Y %H:%M"),
            r.vehiculo.patente,
            r.ruta.nombre,
            r.cantidad_pasajeros,
            r.valor_viaje,
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
            return redirect('crear_vehiculo')
    else:
        form = VehiculoForm()
    
    vehiculos_existentes = Vehiculo.objects.filter(activo=True).order_by('patente')
    return render(request, 'transporte/crear_vehiculo.html', {
        'form': form, 
        'titulo': 'Nuevo Vehículo',
        'lista_vehiculos': vehiculos_existentes
    })

@login_required
def crear_conductor(request):
    if request.method == 'POST':
        form = ConductorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Conductor registrado.')
            return redirect('crear_conductor')
    else:
        form = ConductorForm()

    conductores_existentes = Conductor.objects.filter(activo=True).order_by('nombre')
    return render(request, 'transporte/crear_conductor.html', {
        'form': form, 
        'titulo': 'Nuevo Conductor',
        'lista_conductores': conductores_existentes
    })

@login_required
def gestion_rutas(request):
    if not request.user.is_staff and not request.user.is_superuser:
        return redirect('transporte_home')
        
    if request.method == 'POST':
        form = RutaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ruta creada correctamente.')
            return redirect('gestion_rutas')
    else:
        form = RutaForm()
    
    rutas = Ruta.objects.filter(activo=True)
    return render(request, 'transporte/gestion_rutas.html', {'form': form, 'rutas': rutas})

# --- 6. API DASHBOARD (MODIFICADA PARA NUEVOS GRÁFICOS) ---
@login_required
def api_datos_dashboard(request):
    if not request.user.is_superuser: return JsonResponse({'error': '403'}, status=403)

    inicio = request.GET.get('inicio')
    fin = request.GET.get('fin')
    registros = RegistroSalida.objects.all()
    if inicio and fin: registros = registros.filter(fecha_registro__date__range=[inicio, fin])

    # 1. Curva Semanal
    curva_raw = registros.annotate(semana=TruncWeek('fecha_registro')).values('semana').annotate(total=Sum('valor_viaje')).order_by('semana')
    curva_costos = [{'mes': f"Semana {x['semana'].strftime('%d/%m')}", 'total': x['total']} for x in curva_raw if x['semana']]

    # 2. Datos existentes
    ocupacion_vehiculo = list(registros.values('vehiculo__patente').annotate(avg_ocupacion=Avg('ocupacion_porcentaje')).order_by('-avg_ocupacion'))
    ocupacion_tipo = list(registros.values('vehiculo__tipo').annotate(avg_ocupacion=Avg('ocupacion_porcentaje')))
    costo_tipo = list(registros.values('vehiculo__tipo').annotate(total_costo=Sum('valor_viaje')))
    
    # 3. CPP General
    tot_costo = registros.aggregate(Sum('valor_viaje'))['valor_viaje__sum'] or 0
    tot_pax = registros.aggregate(Sum('cantidad_pasajeros'))['cantidad_pasajeros__sum'] or 1
    cpp_gen = tot_costo / tot_pax

    # 4. CPP Vehículo y Tipo
    cpp_vehiculo = [{'label': i['vehiculo__patente'], 'value': round(i['c']/i['p'] if i['p']>0 else 0)} 
                    for i in registros.values('vehiculo__patente').annotate(c=Sum('valor_viaje'), p=Sum('cantidad_pasajeros'))]
    
    cpp_tipo = [{'label': i['vehiculo__tipo'], 'value': round(i['c']/i['p'] if i['p']>0 else 0)} 
                for i in registros.values('vehiculo__tipo').annotate(c=Sum('valor_viaje'), p=Sum('cantidad_pasajeros'))]

    # 5. Costo Total por Ruta
    costo_ruta = list(registros.values('ruta__nombre').annotate(total=Sum('valor_viaje')).order_by('-total'))

    # 6. Costo por Pasajero por Ruta
    cpp_ruta_raw = registros.values('ruta__nombre').annotate(c=Sum('valor_viaje'), p=Sum('cantidad_pasajeros'))
    cpp_ruta = [{'label': i['ruta__nombre'], 'value': round(i['c']/i['p'] if i['p']>0 else 0)} for i in cpp_ruta_raw]
    cpp_ruta.sort(key=lambda x: x['value'], reverse=True)

    return JsonResponse({
        'curva_costos': curva_costos,
        'ocupacion_vehiculo': ocupacion_vehiculo,
        'ocupacion_tipo': ocupacion_tipo,
        'costo_tipo': costo_tipo,
        'cpp_general': round(cpp_gen),
        'cpp_vehiculo': cpp_vehiculo,
        'cpp_tipo': cpp_tipo,
        'costo_ruta': costo_ruta,
        'cpp_ruta': cpp_ruta,
    })