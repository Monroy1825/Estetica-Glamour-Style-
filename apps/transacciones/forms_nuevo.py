from django import forms
from .models import VentaCabecera, VentaDetalle, Cita
from apps.servicios.models import Producto


class VentaCombinadaForm(forms.Form):
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(activo=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    empleado = forms.ModelChoiceField(
        queryset=Empleado.objects.filter(activo=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    metodo_pago = forms.ChoiceField(
        choices=VentaCabecera.METODO_PAGO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Items de la venta
    cita = forms.ModelChoiceField(
        queryset=Cita.objects.filter(activo=True, estado__in=['pendiente', 'confirmada']),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(activo=True, stock_actual__gt=0),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        cita = cleaned_data.get('cita')
        producto = cleaned_data.get('producto')
        
        if not cita and not producto:
            raise forms.ValidationError('Debe seleccionar al menos una cita o un producto')
        
        return cleaned_data
