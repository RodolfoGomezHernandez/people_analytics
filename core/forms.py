from django import forms

from asistencia.models import Colaborador, Marcaje 

class ImportarFichasForm(forms.Form):
    archivo = forms.FileField(label="Seleccionar Excel de Dotación (Fichas)")

class ImportarAsistenciaForm(forms.Form):
    archivo_asistencia = forms.FileField(label="Seleccionar Excel de Asistencia (Grex)")