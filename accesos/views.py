from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from dotacion.models import Colaborador
from .models import RegistroVisita

def _formatear_rut(rut_raw):
    """Formatea RUT chileno: 12.345.678-9. Retorna None si es inválido."""
    if not rut_raw:
        return rut_raw
    rut = str(rut_raw).upper().replace('.', '').replace('-', '').strip()
    if len(rut) < 2:
        return rut_raw
    cuerpo, dv = rut[:-1], rut[-1]
    try:
        return f"{int(cuerpo):,}".replace(',', '.') + '-' + dv
    except ValueError:
        return rut_raw
@login_required
def control(request):
    es_guardia = request.user.groups.filter(name='Guardias').exists()
    es_admin   = request.user.is_superuser or request.user.is_staff

    if not es_guardia and not es_admin:
        from django.shortcuts import redirect
        return redirect('/')

    if request.method == 'POST':
        rut            = _formatear_rut(request.POST.get('rut', '').strip())
        nombre         = request.POST.get('nombre', '').strip().upper()
        empresa        = request.POST.get('empresa', '').strip().upper()
        estado_dot     = request.POST.get('estado_dotacion', 'EXTERNO')
        quien_autoriza = request.POST.get('quien_autoriza', '').strip().upper()
        a_quien_visita = request.POST.get('a_quien_visita', '').strip().upper()
        lugar          = request.POST.get('lugar', '').strip().upper()
        numero_tarjeta = request.POST.get('numero_tarjeta', '').strip()
        patente        = request.POST.get('patente', '').strip().upper()
        
    RegistroVisita.objects.create(
            rut             = rut,
            nombre          = nombre,
            empresa         = empresa,
            estado_dotacion = estado_dot,
            quien_autoriza  = quien_autoriza,
            a_quien_visita  = a_quien_visita,
            lugar           = lugar,
            numero_tarjeta  = numero_tarjeta,
            patente         = patente,
            registrado_por  = request.user,
        )

    # Personas adentro ahora
    adentro = RegistroVisita.objects.filter(
        fecha       = timezone.localdate(),
        hora_salida = None,
    ).order_by('-hora_entrada')

    # Historial del día completo
    historial = RegistroVisita.objects.filter(
        fecha = timezone.localdate(),
    ).exclude(hora_salida=None).order_by('-hora_entrada')

    return render(request, 'accesos/control.html', {
        'adentro'  : adentro,
        'historial': historial,
        'es_admin' : es_admin,
    })


@login_required
def api_buscar_rut(request):
    """Consulta dotación por RUT y devuelve estado + nombre."""
    rut = request.GET.get('rut', '').strip()

    if not rut:
        return JsonResponse({'encontrado': False})

    try:
        colaborador = Colaborador.objects.get(rut=rut)
        return JsonResponse({
            'encontrado'  : True,
            'nombre'      : colaborador.nombre_completo,
            'estado'      : colaborador.estado,
            'cargo'       : colaborador.cargo or '',
            'empresa'     : colaborador.centro_costo or '',
        })
    except Colaborador.DoesNotExist:
        return JsonResponse({'encontrado': False, 'estado': 'EXTERNO'})


@login_required
@require_POST
def api_registrar_salida(request, pk):
    """Marca la hora de salida de un registro."""
    registro = get_object_or_404(RegistroVisita, pk=pk)

    if registro.hora_salida:
        return JsonResponse({'ok': False, 'error': 'Ya tiene salida registrada'})

    registro.hora_salida = timezone.now()
    registro.save()

    return JsonResponse({
        'ok'         : True,
        'hora_salida': registro.hora_salida.strftime('%H:%M'),
        'duracion'   : registro.duracion,
    })