from django import forms
from .models import Empleado

class EmpleadoForm(forms.ModelForm):
    # Horarios disponibles (solo los mismos que en citas)
    HORARIOS = [
        ('10:00', '10:00 AM'),
        ('11:00', '11:00 AM'),
        ('12:00', '12:00 PM'),
        ('13:00', '01:00 PM'),
        ('17:00', '05:00 PM'),
        ('18:00', '06:00 PM'),
        ('19:00', '07:00 PM'),
        ('20:00', '08:00 PM'),
    ]
    
    horario_entrada = forms.ChoiceField(choices=HORARIOS, required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    horario_salida = forms.ChoiceField(choices=HORARIOS, required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    
    class Meta:
        model = Empleado
        fields = [
            'nombre', 'telefono', 'email', 'fecha_nacimiento', 'direccion',
            'rol', 'fecha_ingreso', 'horario_entrada', 'horario_salida', 'dias_descanso',
            'comision', 'sueldo_base', 'especialidades', 'años_experiencia', 'activo'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'data-tipo': 'telefono'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'fecha_ingreso': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'dias_descanso': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Domingo, Lunes'}),
            'comision': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'sueldo_base': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'especialidades': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Ej: Corte de dama, Coloración, Uñas'}),
            'años_experiencia': forms.NumberInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }