from django import forms
from .models import Servicio, Producto


class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ['nombre', 'categoria', 'precio_base']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del servicio', 'style': 'text-transform: uppercase'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'precio_base': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
        }

    def clean_nombre(self):
        return self.cleaned_data.get('nombre', '').upper()


class ProductoForm(forms.ModelForm):

    PRESENTACION_CHOICES = [
        ('', '— Selecciona presentación —'),
        ('botella', 'Botella'),
        ('frasco', 'Frasco'),
        ('tubo', 'Tubo'),
        ('sachet', 'Sachet'),
        ('lata', 'Lata'),
        ('caja', 'Caja'),
        ('pieza', 'Pieza'),
        ('paquete', 'Paquete'),
        ('otro', 'Otro'),
    ]

    TAMANOS_POR_PRESENTACION = {
        'botella': ['250 ml', '350 ml', '500 ml', '750 ml', '1 L', '1.5 L', '2 L'],
        'frasco': ['30 ml', '50 ml', '100 ml', '150 ml', '200 ml', '250 ml', '300 ml', '500 ml'],
        'tubo': ['50 g', '75 g', '100 g', '150 g', '200 g', '250 g'],
        'sachet': ['5 ml', '10 ml', '15 ml', '20 ml', '30 ml', '50 ml'],
        'lata': ['100 ml', '200 ml', '250 ml', '400 ml', '500 ml'],
        'caja': ['50 g', '100 g', '200 g', '500 g', '1 kg'],
        'pieza': ['1 pieza', '2 piezas', '3 piezas', '6 piezas', '12 piezas'],
        'paquete': ['paquete chico', 'paquete mediano', 'paquete grande'],
        'otro': [],
    }

    presentacion = forms.ChoiceField(
        choices=PRESENTACION_CHOICES,
        required=False,
        label='Presentación',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_presentacion',
            'onchange': 'actualizarTamanos(this.value)',
        })
    )

    tamano = forms.ChoiceField(
        choices=[('', '— Primero selecciona presentación —')],
        required=False,
        label='Tamaño',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_tamano',
            'onchange': """
                var val = this.value;
                var wrapper = document.getElementById('wrapper_personalizado');
                var campo = document.getElementById('id_tamano_personalizado');
                if (val === 'otro') {
                    wrapper.style.display = 'block';
                    campo.value = '';
                    campo.focus();
                } else {
                    wrapper.style.display = 'none';
                    campo.value = val;
                }
            """
        })
    )

    class Meta:
        model = Producto
        fields = ['nombre', 'marca', 'presentacion', 'tamano', 'tamano_personalizado',
                  'costo', 'precio_venta', 'stock_actual', 'stock_minimo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del producto'}),
            'marca': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Marca'}),
            'tamano_personalizado': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Escribe el tamaño exacto...',
                'id': 'id_tamano_personalizado',
            }),
            'costo': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'precio_venta': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'stock_actual': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }
        labels = {
            'tamano_personalizado': 'Tamaño personalizado',
            'stock_actual': 'Cantidad en existencia',
            'stock_minimo': 'Cantidad mínima de alerta',
        }

    def clean(self):
        cleaned = super().clean()
        tamano = cleaned.get('tamano', '')
        personalizado = cleaned.get('tamano_personalizado', '')
        if tamano == 'otro':
            cleaned['tamano'] = personalizado
            cleaned['tamano_personalizado'] = personalizado
        elif tamano:
            cleaned['tamano_personalizado'] = ''
        return cleaned