from django import forms


class CargaEstadiaForm(forms.Form):
    archivo = forms.FileField(
        label='Reporte de Estadía (.xlsx)',
        widget=forms.FileInput(attrs={
            'accept': '.xlsx',
            'class': 'block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 '
                     'file:rounded-lg file:border-0 file:font-semibold '
                     'file:bg-green-50 file:text-green-700 hover:file:bg-green-100',
        })
    )

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if archivo:
            if not archivo.name.endswith('.xlsx'):
                raise forms.ValidationError('Solo se aceptan archivos .xlsx')
            if archivo.size > 20 * 1024 * 1024:
                raise forms.ValidationError('El archivo no puede superar los 20 MB.')
        return archivo