from django import forms
from .models import Servicio, Producto


class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ['nombre', 'categoria', 'precio_base']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del servicio'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'precio_base': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
        }


class ProductoForm(forms.ModelForm):

    TAMANO_CHOICES = [
        ('', '— Selecciona un tamaño —'),
        # Volumen
        ('15 ml', '15 ml'), ('30 ml', '30 ml'), ('50 ml', '50 ml'),
        ('75 ml', '75 ml'), ('100 ml', '100 ml'), ('120 ml', '120 ml'),
        ('150 ml', '150 ml'), ('200 ml', '200 ml'), ('250 ml', '250 ml'),
        ('300 ml', '300 ml'), ('350 ml', '350 ml'), ('400 ml', '400 ml'),
        ('500 ml', '500 ml'), ('750 ml', '750 ml'), ('1 L', '1 L'),
        ('1.5 L', '1.5 L'), ('2 L', '2 L'), ('5 L', '5 L'),
        # Peso
        ('10 g', '10 g'), ('25 g', '25 g'), ('50 g', '50 g'),
        ('75 g', '75 g'), ('100 g', '100 g'), ('150 g', '150 g'),
        ('200 g', '200 g'), ('250 g', '250 g'), ('300 g', '300 g'),
        ('400 g', '400 g'), ('500 g', '500 g'), ('750 g', '750 g'),
        ('1 kg', '1 kg'), ('2 kg', '2 kg'), ('5 kg', '5 kg'),

        # Paquetes
        ('paquete chico', 'Paquete chico'),
        ('paquete mediano', 'Paquete mediano'),
        ('paquete grande', 'Paquete grande'),
        # Otro
        ('otro', 'Otro — escribir abajo'),
    ]

    tamano = forms.ChoiceField(
        choices=TAMANO_CHOICES,
        required=False,
        label='Tamaño',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'onchange': """
                var val = this.value;
                var campo = document.getElementById('id_tamano_personalizado');
                var wrapper = document.getElementById('wrapper_personalizado');
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
        fields = ['nombre', 'marca', 'tamano', 'tamano_personalizado',
                  'costo', 'precio_venta', 'stock_actual', 'stock_minimo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del producto'}),
            'marca': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Marca'}),
            'tamano_personalizado': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Escribe el tamaño exacto: Ej: 180 ml, kit 3 pzas...',
                'id': 'id_tamano_personalizado',
            }),
            'costo': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'precio_venta': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'stock_actual': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }
        labels = {
            'tamano_personalizado': 'Tamaño personalizado',
            'stock_actual': 'Existencia',  # Cambiado de 'Cantidad en existencia' a solo 'Existencia'
            'stock_minimo': 'Cantidad mínima de alerta',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            preset_values = [c[0] for c in self.TAMANO_CHOICES if c[0]]
            if self.instance.tamano in preset_values:
                self.fields['tamano'].initial = self.instance.tamano
            elif self.instance.tamano:
                self.fields['tamano'].initial = 'otro'

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