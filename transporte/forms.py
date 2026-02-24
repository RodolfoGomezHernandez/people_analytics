from django import forms
from .models import Vehiculo, Conductor, RegistroSalida, Ruta
from core.validators import validar_rut 

# --- MIXIN DE ESTILOS Y VALIDACIÓN BASE ---
class EstiloFormMixin:
    """Mixin para dar estilos Tailwind a todos los campos y forzar requeridos"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Estilo visual diferenciado para checkboxes
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': 'w-5 h-5 text-blue-600 rounded border-gray-300 focus:ring-blue-500'
                })
            else:
                field.widget.attrs.update({
                    'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors'
                })
            
            # Validación: Forzamos requerido (excepto campos opcionales)
            campos_opcionales = ['empresa_externa', 'nombre_empresa_externa', 'activo', 'motivo', 'salidas_multiples', 'telefono']
            if field_name not in campos_opcionales:
                field.required = True
                field.widget.attrs.update({'required': 'required'})

# --- 1. FORMULARIO DE VEHÍCULO ---
class VehiculoForm(EstiloFormMixin, forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = ['patente', 'tipo', 'capacidad', 'tarifa_base']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'bg-white'}),
        }
        labels = {
            'tarifa_base': 'Tarifa Base (Costo por Salida)',
            'capacidad': 'Capacidad de Pasajeros'
        }
    
    def clean_patente(self):
        patente = self.cleaned_data.get('patente')
        if patente:
            return patente.upper().replace(" ", "").strip()
        return patente

# --- 2. FORMULARIO DE CONDUCTOR ---
class ConductorForm(EstiloFormMixin, forms.ModelForm):
    class Meta:
        model = Conductor
        # NUEVO: Se agregó 'nombre_empresa_externa'
        fields = ['nombre', 'rut', 'telefono', 'empresa_externa', 'nombre_empresa_externa']
        labels = {
            'rut': 'RUT',
            'telefono': 'Teléfono de Contacto',
            'empresa_externa': '¿Es conductor externo?',
            'nombre_empresa_externa': 'Nombre Empresa Externa'
        }
        help_texts = {
            'rut': 'Ej: 12.345.678-9',
            'nombre_empresa_externa': 'Obligatorio si es conductor externo.'
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            nombre = nombre.upper().strip()
            replacements = (("Á", "A"), ("É", "E"), ("Í", "I"), ("Ó", "O"), ("Ú", "U"), ("Ü", "U"))
            for accented, unaccented in replacements:
                nombre = nombre.replace(accented, unaccented)
        return nombre

    def clean_rut(self):
        rut = self.cleaned_data.get('rut')
        validar_rut(rut) 
        rut_limpio = rut.upper().replace("-", "").replace(".", "")
        cuerpo = rut_limpio[:-1]
        dv = rut_limpio[-1]
        try:
            rut_formateado = f"{int(cuerpo):,}".replace(",", ".") + "-" + dv
        except ValueError:
            raise forms.ValidationError("Error al formatear el RUT.")
        return rut_formateado

    # NUEVO: Validación cruzada para la empresa externa
    def clean(self):
        cleaned_data = super().clean()
        es_externo = cleaned_data.get('empresa_externa')
        nombre_emp = cleaned_data.get('nombre_empresa_externa')
        if es_externo and not nombre_emp:
            self.add_error('nombre_empresa_externa', 'Debe indicar el nombre de la empresa externa.')
        return cleaned_data

# --- 3. FORMULARIO GUARDIA (REGISTRO RÁPIDO) ---
class RegistroGuardiaForm(EstiloFormMixin, forms.ModelForm):
    # NUEVO: Checkbox para mantener la ventana abierta
    salidas_multiples = forms.BooleanField(
        required=False, 
        label="Registro múltiple (Mantener ventana abierta)",
    )

    class Meta:
        model = RegistroSalida
        # NUEVO: Se agregó 'tipo_movimiento'
        fields = ['tipo_movimiento', 'ruta', 'vehiculo', 'conductor', 'cantidad_pasajeros', 'paradas_intermedias']
        widgets = {
            'tipo_movimiento': forms.Select(attrs={'class': 'bg-white font-bold text-blue-700'}),
            'ruta': forms.Select(attrs={'class': 'bg-white'}),
            'vehiculo': forms.Select(attrs={'class': 'bg-white'}),
            'conductor': forms.Select(attrs={'class': 'bg-white'}),
            'paradas_intermedias': forms.HiddenInput(), 
        }
        labels = {
            'cantidad_pasajeros': 'Pasajeros a Bordo',
            'tipo_movimiento': '¿Entrada o Salida?'
        }

    def clean(self):
        cleaned_data = super().clean()
        vehiculo = cleaned_data.get('vehiculo')
        pasajeros = cleaned_data.get('cantidad_pasajeros')

        if vehiculo and pasajeros:
            if pasajeros > vehiculo.capacidad:
                raise forms.ValidationError(f"¡Error! El vehículo {vehiculo.modelo} solo acepta {vehiculo.capacidad} pasajeros.")

# --- 4. FORMULARIO ADMIN (EDICIÓN COMPLETA) ---
class EdicionAdminForm(EstiloFormMixin, forms.ModelForm):
    class Meta:
        model = RegistroSalida
        # AGREGAMOS 'paradas_intermedias' al final
        fields = ['tipo_movimiento', 'ruta', 'vehiculo', 'conductor', 'cantidad_pasajeros', 'valor_viaje', 'paradas_intermedias']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'valor_viaje' in self.fields:
            self.fields['valor_viaje'].widget.attrs.update({
                'class': 'w-full px-4 py-2 border border-yellow-400 bg-yellow-50 rounded-lg font-bold text-slate-700'
            })

class RutaForm(EstiloFormMixin, forms.ModelForm):
    class Meta:
        model = Ruta
        fields = ['nombre', 'origen', 'destino']
        widgets = {
            'origen': forms.TextInput(attrs={'placeholder': 'Ej: Planta Aurora'}),
            'destino': forms.TextInput(attrs={'placeholder': 'Ej: Plaza de Armas'}),
        }