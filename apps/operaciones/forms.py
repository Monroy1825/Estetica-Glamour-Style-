from django import forms
from .models import Cita, Venta, Compra, Cotizacion
from apps.servicios.models import Producto
from datetime import datetime


# =========================
# CITAS
# =========================
class CitaForm(forms.ModelForm):


    HORARIOS = [
        ("10:00-11:00", "10:00 AM - 11:00 AM"),
        ("11:00-12:00", "11:00 AM - 12:00 PM"),
        ("12:00-13:00", "12:00 PM - 1:00 PM"),
        ("13:00-14:00", "1:00 PM - 2:00 PM"),
        ("17:00-18:00", "5:00 PM - 6:00 PM"),
        ("18:00-19:00", "6:00 PM - 7:00 PM"),
        ("19:00-20:00", "7:00 PM - 8:00 PM"),
        ("20:00-21:00", "8:00 PM - 9:00 PM"),
    ]

    horario = forms.ChoiceField(
        choices=HORARIOS,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Cita
        fields = ['cliente', 'empleado', 'servicio', 'fecha_inicio', 'horario', 'estado']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'empleado': forms.Select(attrs={'class': 'form-select'}),
            'servicio': forms.Select(attrs={'class': 'form-select'}),

           
            'fecha_inicio': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}
            ),

            'estado': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha = cleaned_data.get('fecha_inicio')
        rango = cleaned_data.get('horario')

        if not fecha or not rango:
            return cleaned_data

        inicio_str, fin_str = rango.split('-')

        fecha_str = fecha.strftime("%Y-%m-%d")

        fecha_inicio = datetime.strptime(f"{fecha_str} {inicio_str}", "%Y-%m-%d %H:%M")
        fecha_fin = datetime.strptime(f"{fecha_str} {fin_str}", "%Y-%m-%d %H:%M")

        cleaned_data['fecha_inicio'] = fecha_inicio
        cleaned_data['fecha_fin'] = fecha_fin

        return cleaned_data


# =========================
# VENTAS
# =========================
class VentaForm(forms.ModelForm):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(activo=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = Venta
        fields = ['cliente', 'empleado', 'producto', 'metodo_pago', 'tipo', 'estatus', 'vigencia_hasta', 'total']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'empleado': forms.Select(attrs={'class': 'form-select'}),
            'metodo_pago': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'estatus': forms.Select(attrs={'class': 'form-select'}),
            'vigencia_hasta': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d',
            ),
            'total': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
        }


# =========================
# COMPRAS
# =========================
class CompraForm(forms.ModelForm):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(activo=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Producto',
    )
    cantidad = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        label='Cantidad comprada',
    )

    class Meta:
        model = Compra
        fields = ['producto', 'cantidad', 'empleado', 'proveedor', 'precio_unitario'] 
        widgets = {
            'empleado': forms.Select(attrs={'class': 'form-select'}),
            'proveedor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del proveedor'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
        }


# =========================
# COTIZACIONES
# =========================
class CotizacionForm(forms.ModelForm):
    class Meta:
        model = Cotizacion
        fields = ['cliente', 'servicio', 'producto', 'vigencia', 'estado']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'servicio': forms.Select(attrs={'class': 'form-select'}),
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'vigencia': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d',
            ),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }