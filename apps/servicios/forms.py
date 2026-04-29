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

    tamano = forms.CharField(
        required=False,
        label='Tamaño',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = Producto
        fields = ['nombre', 'marca', 'presentacion', 'tamano',
                  'costo', 'precio_venta', 'stock_actual', 'stock_minimo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del producto'}),
            'marca': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Marca'}),
            'presentacion': forms.Select(attrs={'class': 'form-select'}),
            'costo': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'precio_venta': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'stock_actual': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }
