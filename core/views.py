from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import CargaArchivoForm

@login_required
def dashboard(request):
    return render(request, 'core/dashboard.html')

@login_required
def subir_archivo(request):
    if request.method == 'POST':
        form = CargaArchivoForm(request.POST, request.FILES)
        if form.is_valid():
            carga = form.save(commit=False)
            carga.usuario = request.user
            carga.save()
            messages.success(request, "Archivo cargado exitosamente. El procesamiento iniciará pronto.")
            return redirect('dashboard')
    else:
        form = CargaArchivoForm()
    
    return render(request, 'core/reportes.html', {'form': form}) # Reutilizamos reportes.html o crea uno nuevo