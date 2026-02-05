from django import forms
from .models import SolicitudDotacion

class SolicitudDotacionForm(forms.ModelForm):
    class Meta:
        model = SolicitudDotacion
        fields = ['area', 'cargo', 'cantidad', 'fecha_necesidad', 'motivo']
        widgets = {
            'area': forms.TextInput(attrs={'class': 'w-full p-2 border rounded-lg', 'placeholder': 'Ej: Operaciones'}),
            'cargo': forms.TextInput(attrs={'class': 'w-full p-2 border rounded-lg', 'placeholder': 'Ej: Operario de Grúa'}),
            'cantidad': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded-lg', 'min': 1}),
            'fecha_necesidad': forms.DateInput(attrs={'class': 'w-full p-2 border rounded-lg', 'type': 'date'}),
            'motivo': forms.Textarea(attrs={'class': 'w-full p-2 border rounded-lg', 'rows': 3, 'placeholder': 'Describa por qué necesita este personal...'}),
        }