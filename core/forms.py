from django import forms
from .models import CargaInformacion

class CargaArchivoForm(forms.ModelForm):
    class Meta:
        model = CargaInformacion
        fields = ['tipo', 'archivo']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'archivo': forms.FileInput(attrs={'class': 'form-control'}),
        }