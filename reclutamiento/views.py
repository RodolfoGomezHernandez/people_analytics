import requests
import re
import unicodedata
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from twilio.twiml.messaging_response import MessagingResponse
from core.decorators import group_required

from .forms import SolicitudDotacionForm
from .models import Candidato

# ==========================================
# 1. FUNCIONES DE AYUDA (ROBUSTAS)
# ==========================================

def normalizar_texto(texto):
    """Convierte a Mayúsculas y elimina tildes (Ej: JOSÉ -> JOSE)"""
    if not texto: return ""
    return ''.join(c for c in unicodedata.normalize('NFD', texto.upper()) if unicodedata.category(c) != 'Mn')

def validar_rut_chileno(rut_raw):
    """
    Valida formato y Dígito Verificador (Módulo 11).
    Retorna True solo si el RUT es real y válido.
    """
    # 1. Limpieza total
    rut_limpio = rut_raw.replace('.', '').replace('-', '').upper()
    
    # 2. Verificar formato base (números + K)
    if not re.match(r'^\d{7,8}[0-9K]$', rut_limpio):
        return False

    # 3. Algoritmo Módulo 11
    cuerpo = rut_limpio[:-1]
    dv_ingresado = rut_limpio[-1]

    suma = 0
    multiplo = 2
    
    for c in reversed(cuerpo):
        suma += int(c) * multiplo
        multiplo += 1
        if multiplo == 8: multiplo = 2
    
    resto = suma % 11
    resultado = 11 - resto
    
    if resultado == 11: dv_calculado = '0'
    elif resultado == 10: dv_calculado = 'K'
    else: dv_calculado = str(resultado)
    
    return dv_ingresado == dv_calculado

def guardar_imagen_twilio(url_imagen, nombre_archivo):
    """
    Descarga la imagen de forma segura usando las credenciales de settings.
    Vital para evitar errores 403 Forbidden al descargar media de Twilio.
    """
    if not url_imagen: return None
    try:
        # Autenticación requerida para descargar media de Twilio
        response = requests.get(
            url_imagen, 
            auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        )
        if response.status_code == 200:
            return ContentFile(response.content, name=nombre_archivo)
    except Exception as e:
        print(f"Error crítico descargando imagen: {e}")
    return None

# ==========================================
# 2. VISTAS (WEBHOOK)
# ==========================================

@login_required
@group_required('Reclutamiento')
def crear_solicitud(request):
    if request.method == 'POST':
        form = SolicitudDotacionForm(request.POST)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.solicitante = f"{request.user.first_name} {request.user.last_name}"
            solicitud.save()
            messages.success(request, '¡Solicitud creada exitosamente!')
            return redirect('dashboard')
    else:
        form = SolicitudDotacionForm()
    return render(request, 'reclutamiento/crear_solicitud.html', {'form': form})

@csrf_exempt
def whatsapp_webhook(request):
    if request.method == 'POST':
        # Datos entrantes
        mensaje = request.POST.get('Body', '').strip()
        telefono = request.POST.get('From', '')
        num_media = int(request.POST.get('NumMedia', 0))
        media_url = request.POST.get('MediaUrl0', None)
        
        # Identificar o crear candidato
        candidato, created = Candidato.objects.get_or_create(
            telefono=telefono,
            defaults={'rut': 'TEMP', 'nombre_completo': 'Anonimo'}
        )
        
        # Objeto de respuesta XML
        resp = MessagingResponse()
        msg = resp.message()

        # ---------------------------------------------------------
        # MÁQUINA DE ESTADOS (FLUJO COMPLETO)
        # ---------------------------------------------------------

        # 0. INICIO / RESET
        if created or mensaje.lower() in ['reset', 'hola', 'inicio', 'volver']:
            candidato.stage = 'ESPERANDO_RUT'
            candidato.save()
            msg.body("¡Hola! 👋 Bienvenido a Reclutamiento Aurora Australis.\n\nPara postular, escribe tu *RUT*.\n\n📝 *Ejemplo:* 12.345.678-9")
            return HttpResponse(str(resp), content_type='application/xml')

        # 1. VALIDACIÓN RUT (Estricta + Módulo 11)
        if candidato.stage == 'ESPERANDO_RUT':
            # A. Validación Visual (Regex)
            if not re.match(r'^\d{1,2}\.\d{3}\.\d{3}-[\dkK]$', mensaje):
                msg.body("❌ *Formato incorrecto.*\n\nDebes usar puntos y guión.\nEjemplo válido: *12.345.678-9*")
                return HttpResponse(str(resp), content_type='application/xml')

            # B. Validación Matemática (Algoritmo)
            if validar_rut_chileno(mensaje):
                candidato.rut = mensaje.upper()
                candidato.stage = 'ESPERANDO_NOMBRE'
                candidato.save()
                msg.body("✅ RUT Validado.\n\nPor favor, escribe tu *Nombre Completo*.")
            else:
                msg.body("⛔ *RUT Inválido.*\n\nEl dígito verificador no coincide o el RUT no es real. Verifica tus datos.")
        
        # 2. NOMBRE -> PIDE FOTO FRONTAL
        elif candidato.stage == 'ESPERANDO_NOMBRE':
            nombre_limpio = normalizar_texto(mensaje)
            candidato.nombre_completo = nombre_limpio
            candidato.stage = 'ESPERANDO_FOTO_FRONTAL'
            candidato.save()
            
            msg.body(
                f"Gusto en saludarte, {nombre_limpio}. 📸\n\n"
                "Comencemos con las fotos.\n"
                "Envía una foto de tu *CÉDULA DE IDENTIDAD (Frente)*.\n\n"
                "💡 *Tip:* Asegúrate de que se lean bien los textos."
            )

        # 3. FOTO FRONTAL -> PIDE DORSO
        elif candidato.stage == 'ESPERANDO_FOTO_FRONTAL':
            if num_media > 0 and media_url:
                archivo = guardar_imagen_twilio(media_url, f"{candidato.rut}_frente.jpg")
                if archivo:
                    candidato.foto_cedula_frente.save(f"{candidato.rut}_frente.jpg", archivo, save=True)
                    candidato.stage = 'ESPERANDO_FOTO_DORSO'
                    candidato.save()
                    msg.body("¡Recibida! ✅\n\nAhora envía una foto de la *Parte Trasera* de tu carnet.")
                else:
                    msg.body("❌ Error al guardar la imagen. Inténtalo de nuevo.")
            else:
                msg.body("⚠️ No detecté una imagen.\nPor favor presiona la cámara 📷 y envía la foto *FRONTAL* del carnet.")

        # 4. FOTO DORSO -> PIDE SELFIE
        elif candidato.stage == 'ESPERANDO_FOTO_DORSO':
            if num_media > 0 and media_url:
                archivo = guardar_imagen_twilio(media_url, f"{candidato.rut}_dorso.jpg")
                if archivo:
                    candidato.foto_cedula_dorso.save(f"{candidato.rut}_dorso.jpg", archivo, save=True)
                    candidato.stage = 'ESPERANDO_SELFIE'
                    candidato.save()
                    msg.body("Perfecto. 👤 *Último paso:*\n\nEnvíame una *SELFIE* actual para validar tu identidad.")
            else:
                msg.body("⚠️ Por favor envía la foto de la parte *TRASERA*.")

        # 5. SELFIE -> FINALIZAR
        elif candidato.stage == 'ESPERANDO_SELFIE':
            if num_media > 0 and media_url:
                archivo = guardar_imagen_twilio(media_url, f"{candidato.rut}_selfie.jpg")
                if archivo:
                    candidato.foto_selfie.save(f"{candidato.rut}_selfie.jpg", archivo, save=True)
                    # AQUÍ IRÍA EL RECONOCIMIENTO FACIAL (PENDIENTE)
                    
                    candidato.stage = 'COMPLETADO'
                    candidato.estado = 'REVISION'
                    candidato.save()
                    msg.body("🎉 *¡Postulación Exitosa!*\n\nHemos recibido tus fotos y datos. El equipo de RRHH te contactará pronto.")
            else:
                msg.body("⚠️ Esperando tu Selfie.\nTómate una foto y envíala para terminar.")

        elif candidato.stage == 'COMPLETADO':
            msg.body("Tu postulación ya está registrada. ¡Mucho éxito!")

        return HttpResponse(str(resp), content_type='application/xml')
    
    return HttpResponse("Error", status=400)