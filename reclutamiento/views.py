import requests
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from twilio.twiml.messaging_response import MessagingResponse

from .forms import SolicitudDotacionForm
from .models import Candidato

# --- TUS CREDENCIALES DE TWILIO ---
TWILIO_ACCOUNT_SID = 'AC36b4398fe37dada1a6ff2d4f87470ea3' # <--- REVISA QUE ESTÉN TUS CREDENCIALES AQUÍ
TWILIO_AUTH_TOKEN = '9747ab239285cef9c7023e5bdb80af28'   # <--- REVISA QUE ESTÉN TUS CREDENCIALES AQUÍ

# ==========================================
# PARTE 1: VISTA PARA GERENTES (WEB)
# ==========================================
@login_required
def crear_solicitud(request):
    if request.method == 'POST':
        form = SolicitudDotacionForm(request.POST)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.solicitante = f"{request.user.first_name} {request.user.last_name}"
            solicitud.save()
            messages.success(request, '¡Solicitud creada exitosamente! RRHH ha sido notificado.')
            return redirect('dashboard')
    else:
        form = SolicitudDotacionForm()

    return render(request, 'reclutamiento/crear_solicitud.html', {'form': form})

# ==========================================
# PARTE 2: LÓGICA DEL BOT (WHATSAPP)
# ==========================================

def guardar_imagen_twilio(url_imagen, nombre_archivo):
    """Descarga la imagen desde Twilio y la prepara para Django"""
    if not url_imagen:
        return None
    # Twilio requiere autenticación para descargar media
    response = requests.get(url_imagen, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
    if response.status_code == 200:
        return ContentFile(response.content, name=nombre_archivo)
    return None

@csrf_exempt
def whatsapp_webhook(request):
    if request.method == 'POST':
        mensaje = request.POST.get('Body', '').strip()
        telefono = request.POST.get('From', '')
        
        # Verificar si viene una imagen
        num_media = int(request.POST.get('NumMedia', 0))
        media_url = request.POST.get('MediaUrl0', None)
        
        candidato, created = Candidato.objects.get_or_create(
            telefono=telefono,
            defaults={'rut': 'TEMP', 'nombre_completo': 'Anonimo'}
        )
        
        resp = MessagingResponse()
        msg = resp.message()

        # --- MÁQUINA DE ESTADOS ---
        
        # REINICIO
        if created or mensaje.lower() in ['reset', 'hola', 'hola aurora']:
            candidato.stage = 'ESPERANDO_RUT'
            candidato.save()
            msg.body("¡Hola! 👋 Bienvenido a Reclutamiento Aurora Australis.\n\nPara postular, por favor escribe tu *RUT*.")
            return HttpResponse(str(resp), content_type='application/xml')

        # 1. RUT
        if candidato.stage == 'ESPERANDO_RUT':
            candidato.rut = mensaje
            candidato.stage = 'ESPERANDO_NOMBRE'
            candidato.save()
            msg.body("Gracias. Ahora escribe tu *Nombre Completo*.")
        
        # 2. NOMBRE
        elif candidato.stage == 'ESPERANDO_NOMBRE':
            candidato.nombre_completo = mensaje.title()
            candidato.stage = 'ESPERANDO_FOTO_FRONTAL'
            candidato.save()
            msg.body(f"Un gusto, {candidato.nombre_completo}. 📸\n\nPor favor envía una foto de tu *Cédula (Frente)*.")

        # 3. FOTO FRONTAL
        elif candidato.stage == 'ESPERANDO_FOTO_FRONTAL':
            if num_media > 0 and media_url:
                archivo = guardar_imagen_twilio(media_url, f"{candidato.rut}_frente.jpg")
                if archivo:
                    candidato.foto_cedula_frente.save(f"{candidato.rut}_frente.jpg", archivo, save=True)
                    candidato.stage = 'ESPERANDO_FOTO_DORSO'
                    candidato.save()
                    msg.body("¡Recibida! Ahora envía la foto de la *Parte Trasera*.")
                else:
                    msg.body("❌ Error al descargar la imagen. Intenta de nuevo.")
            else:
                msg.body("⚠️ Por favor envía una imagen, no texto.")

        # 4. FOTO DORSO
        elif candidato.stage == 'ESPERANDO_FOTO_DORSO':
            if num_media > 0 and media_url:
                archivo = guardar_imagen_twilio(media_url, f"{candidato.rut}_dorso.jpg")
                if archivo:
                    candidato.foto_cedula_dorso.save(f"{candidato.rut}_dorso.jpg", archivo, save=True)
                    candidato.stage = 'ESPERANDO_SELFIE'
                    candidato.save()
                    msg.body("Excelente. Último paso: Envíame una *Selfie* actual.")
            else:
                msg.body("⚠️ Envía la foto de la parte trasera.")

        # 5. SELFIE
        elif candidato.stage == 'ESPERANDO_SELFIE':
            if num_media > 0 and media_url:
                archivo = guardar_imagen_twilio(media_url, f"{candidato.rut}_selfie.jpg")
                if archivo:
                    candidato.foto_selfie.save(f"{candidato.rut}_selfie.jpg", archivo, save=True)
                    candidato.stage = 'COMPLETADO'
                    candidato.estado = 'REVISION'
                    candidato.save()
                    msg.body("🎉 ¡Listo! Tus datos y fotos han sido guardados exitosamente. RRHH te contactará pronto.")
            else:
                msg.body("⚠️ Envía una selfie.")

        elif candidato.stage == 'COMPLETADO':
            msg.body("Tu postulación ya está registrada. Si quieres postular de nuevo, escribe 'Reset'.")

        return HttpResponse(str(resp), content_type='application/xml')
    
    return HttpResponse("Error", status=400)