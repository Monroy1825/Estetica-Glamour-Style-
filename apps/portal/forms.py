from django import forms
from apps.servicios.models import Servicio
from apps.empleados.models import Empleado

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


class CitaPublicaForm(forms.Form):
    nombre = forms.CharField(
        max_length=50,
        label='Nombre completo',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu nombre completo',
        })
    )
    telefono = forms.CharField(
        max_length=20,
        label='Telefono',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej. 5512345678',
        })
    )
    email = forms.EmailField(
        required=False,
        label='Correo electronico (opcional)',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Para enviarte confirmacion',
        })
    )
    servicio = forms.ModelChoiceField(
        queryset=Servicio.objects.filter(activo=True),
        empty_label='-- Selecciona un servicio --',
        label='Servicio',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    empleado = forms.ModelChoiceField(
        queryset=Empleado.objects.filter(activo=True, rol__in=['estilista', 'colorista', 'manicurista']),
        empty_label='-- Selecciona una estilista --',
        label='Estilista / Especialista',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    fecha = forms.DateField(
        label='Fecha',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    horario = forms.ChoiceField(
        choices=HORARIOS,
        label='Horario',
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class ConsultaForm(forms.Form):
    telefono = forms.CharField(
        max_length=20,
        label='Numero de telefono',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'El numero con el que te registraste',
        })
    )