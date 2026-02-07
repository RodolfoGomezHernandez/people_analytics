from django import forms
from .models import Vehiculo, Conductor, RegistroSalida
from core.validators import validar_rut 
from .models import Vehiculo, Conductor, RegistroSalida, Ruta

# --- MIXIN DE ESTILOS Y VALIDACIÓN BASE ---
class EstiloFormMixin:
    """Mixin para dar estilos Tailwind a todos los campos y forzar requeridos"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Estilo visual
            field.widget.attrs.update({
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors'
            })
            
            # Validación: Forzamos requerido (excepto campos opcionales lógicos)
            if field_name not in ['empresa_externa', 'activo', 'motivo']:
                field.required = True
                field.widget.attrs.update({'required': 'required'})

# --- 1. FORMULARIO DE VEHÍCULO ---
class VehiculoForm(EstiloFormMixin, forms.ModelForm):
    class Meta:
        model = Vehiculo
        # ACTUALIZADO: Usamos 'tarifa_base' en lugar de 'costo_fijo_diario'
        fields = ['patente', 'tipo', 'marca', 'modelo', 'capacidad', 'tarifa_base']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'bg-white'}),
        }
        labels = {
            'tarifa_base': 'Tarifa Base (Costo por Salida)',
            'capacidad': 'Capacidad de Pasajeros'
        }
    
    # Mantenemos tu lógica de limpiar patente
    def clean_patente(self):
        patente = self.cleaned_data.get('patente')
        if patente:
            return patente.upper().replace(" ", "").strip()
        return patente

# --- 2. FORMULARIO DE CONDUCTOR ---
class ConductorForm(EstiloFormMixin, forms.ModelForm):
    class Meta:
        model = Conductor
        fields = ['nombre', 'rut', 'telefono', 'empresa_externa']
        labels = {
            'rut': 'RUT',
            'telefono': 'Teléfono de Contacto'
        }
        help_texts = {
            'rut': 'Ej: 12.345.678-9 (Validamos el dígito verificador)'
        }

    # Mantenemos tu lógica de limpiar nombres (Mayúsculas + Sin Tildes + Con Ñ)
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            nombre = nombre.upper().strip()
            replacements = (("Á", "A"), ("É", "E"), ("Í", "I"), ("Ó", "O"), ("Ú", "U"), ("Ü", "U"))
            for accented, unaccented in replacements:
                nombre = nombre.replace(accented, unaccented)
        return nombre

    # Mantenemos tu lógica de validar y formatear RUT
    def clean_rut(self):
        rut = self.cleaned_data.get('rut')
        validar_rut(rut) # Validador matemático
        
        # Formato: XX.XXX.XXX-X
        rut_limpio = rut.upper().replace("-", "").replace(".", "")
        cuerpo = rut_limpio[:-1]
        dv = rut_limpio[-1]
        try:
            rut_formateado = f"{int(cuerpo):,}".replace(",", ".") + "-" + dv
        except ValueError:
            raise forms.ValidationError("Error al formatear el RUT.")
        return rut_formateado

# --- 3. FORMULARIO GUARDIA (REGISTRO RÁPIDO) ---
class RegistroGuardiaForm(EstiloFormMixin, forms.ModelForm):
    class Meta:
        model = RegistroSalida
        # El guardia solo ve lo operativo, NO ve precios
        fields = ['ruta', 'vehiculo', 'conductor', 'cantidad_pasajeros']
        widgets = {
            'ruta': forms.Select(attrs={'class': 'bg-white'}),
            'vehiculo': forms.Select(attrs={'class': 'bg-white'}),
            'conductor': forms.Select(attrs={'class': 'bg-white'}),
        }
        labels = {
            'cantidad_pasajeros': 'Pasajeros a Bordo'
        }

    # Mantenemos tu validación de capacidad vs pasajeros
    def clean(self):
        cleaned_data = super().clean()
        vehiculo = cleaned_data.get('vehiculo')
        pasajeros = cleaned_data.get('cantidad_pasajeros')

        if vehiculo and pasajeros:
            if pasajeros > vehiculo.capacidad:
                raise forms.ValidationError(f"¡Error! El vehículo {vehiculo.modelo} solo acepta {vehiculo.capacidad} pasajeros.")

# --- 4. NUEVO: FORMULARIO ADMIN (EDICIÓN COMPLETA) ---
class EdicionAdminForm(EstiloFormMixin, forms.ModelForm):
    class Meta:
        model = RegistroSalida
        # La admin puede editar TODO, incluido el dinero (valor_viaje)
        fields = ['ruta', 'vehiculo', 'conductor', 'cantidad_pasajeros', 'valor_viaje']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Destacamos el campo de dinero visualmente para la jefa
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