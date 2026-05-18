from django import forms
from datetime import datetime, timedelta
from apps.transacciones.models import Cita, Venta, Compra, Cotizacion, VentaCabecera
from apps.servicios.models import Producto, Servicio
from apps.clientes.models import Cliente
from apps.empleados.models import Empleado


class CitaForm(forms.ModelForm):
    HORARIOS = [
        ("10:00", "10:00 AM"),
        ("11:00", "11:00 AM"),
        ("12:00", "12:00 PM"),
        ("13:00", "1:00 PM"),
        ("17:00", "5:00 PM"),
        ("18:00", "6:00 PM"),
        ("19:00", "7:00 PM"),
        ("20:00", "8:00 PM"),
    ]

    horario = forms.ChoiceField(
        choices=HORARIOS,
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = Cita
        fields = ["cliente", "empleado", "servicio", "fecha_inicio", "horario", "duracion_horas", "estado"]
        widgets = {
            "cliente": forms.Select(attrs={"class": "form-select"}),
            "empleado": forms.Select(attrs={"class": "form-select"}),
            "servicio": forms.Select(attrs={"class": "form-select"}),
            "fecha_inicio": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "estado": forms.Select(attrs={"class": "form-select"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha = cleaned_data.get("fecha_inicio")
        inicio_str = cleaned_data.get("horario")
        duracion = cleaned_data.get("duracion_horas") or 1.0

        if not fecha or not inicio_str:
            return cleaned_data

        fecha_str = fecha.strftime("%Y-%m-%d")
        fecha_inicio = datetime.strptime(f"{fecha_str} {inicio_str}", "%Y-%m-%d %H:%M")
        fecha_fin = fecha_inicio + timedelta(hours=float(duracion))

        cleaned_data["fecha_inicio"] = fecha_inicio
        cleaned_data["fecha_fin"] = fecha_fin

        empleado = cleaned_data.get("empleado")
        if empleado:
            conflictos = Cita.objects.filter(
                empleado=empleado,
                activo=True,
                estado__in=["pendiente", "confirmada"],
                fecha_inicio__lt=fecha_fin,
                fecha_fin__gt=fecha_inicio,
            )
            if self.instance and self.instance.pk:
                conflictos = conflictos.exclude(pk=self.instance.pk)
            if conflictos.exists():
                self.add_error("horario", "Este empleado ya tiene una cita en ese horario.")
        return cleaned_data


class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ["cliente", "empleado", "producto", "metodo_pago", "tipo", "estatus", "total"]
        widgets = {
            "cliente": forms.Select(attrs={"class": "form-select"}),
            "empleado": forms.Select(attrs={"class": "form-select"}),
            "producto": forms.Select(attrs={"class": "form-select"}),
            "metodo_pago": forms.Select(attrs={"class": "form-select"}),
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "estatus": forms.Select(attrs={"class": "form-select"}),
            "total": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }


class CompraForm(forms.ModelForm):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(activo=True),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Producto",
    )
    cantidad = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": "1"})
    )

    class Meta:
        model = Compra
        fields = ["producto", "cantidad", "empleado", "proveedor", "precio_unitario"]
        widgets = {
            "empleado": forms.Select(attrs={"class": "form-select"}),
            "proveedor": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre del proveedor"}),
            "precio_unitario": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }


class CotizacionForm(forms.ModelForm):
    class Meta:
        model = Cotizacion
        fields = ["cliente", "servicio", "producto", "vigencia", "estado"]
        widgets = {
            "cliente": forms.Select(attrs={"class": "form-select"}),
            "servicio": forms.Select(attrs={"class": "form-select"}),
            "producto": forms.Select(attrs={"class": "form-select"}),
            "vigencia": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "estado": forms.Select(attrs={"class": "form-select"}),
        }


class VentaCombinadaForm(forms.Form):
    """Formulario unificado para capturar ventas de servicios y/o productos."""
    
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(activo=True),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Cliente"
    )
    empleado = forms.ModelChoiceField(
        queryset=Empleado.objects.filter(activo=True),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Empleado"
    )
    metodo_pago = forms.ChoiceField(
        choices=VentaCabecera.METODO_PAGO_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Método de pago"
    )
    cita = forms.ModelChoiceField(
        queryset=Cita.objects.filter(activo=True, estado__in=["pendiente", "confirmada"]),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Cita (opcional)"
    )
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(activo=True, stock_actual__gt=0),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Producto (opcional)"
    )

    def clean(self):
        cleaned_data = super().clean()
        cita = cleaned_data.get("cita")
        producto = cleaned_data.get("producto")
        
        if not cita and not producto:
            raise forms.ValidationError(
                "Debe seleccionar al menos una cita o un producto."
            )
        return cleaned_data


class CitaPublicaForm(forms.Form):
    """Formulario público para agendar citas sin login."""
    nombre = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Tu nombre"})
    )
    telefono = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Tu teléfono"})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Tu email (opcional)"})
    )
    empleado = forms.ModelChoiceField(
        queryset=Empleado.objects.filter(activo=True),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Estilista"
    )


class ConsultaCodigoForm(forms.Form):
    codigo = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "GLM-1234",
            "style": "text-transform:uppercase;letter-spacing:2px;font-weight:600;",
        })
    )

class ConsultaTelefonoForm(forms.Form):
    telefono = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Tu número de teléfono",
        })
    )

# Alias para compatibilidad
ConsultaForm = ConsultaCodigoForm
