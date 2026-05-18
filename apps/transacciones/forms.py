from django import forms
from datetime import datetime, timedelta
from .models import Cita, Compra, Cotizacion, VentaCabecera
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
    servicio = forms.ModelChoiceField(
        queryset=Servicio.objects.filter(activo=True),
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = Cita
        fields = ["cliente", "empleado", "servicio", "fecha_inicio", "horario", "duracion_horas", "estado"]
        widgets = {
            "cliente": forms.Select(attrs={"class": "form-select"}),
            "empleado": forms.Select(attrs={"class": "form-select"}),
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



class CompraForm(forms.ModelForm):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(activo=True),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Producto",
    )
    cantidad = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
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


