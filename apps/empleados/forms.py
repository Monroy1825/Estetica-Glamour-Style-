from django import forms
from .models import Empleado


class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Empleado
        fields = ['nombre', 'telefono', 'rol', 'fecha_ingreso']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo', 'style': 'text-transform: uppercase'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'fecha_ingreso': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d',
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        for field_name, value in cleaned_data.items():
            field = self.fields.get(field_name)
            if isinstance(value, str) and field_name != 'email' and not isinstance(field, forms.ChoiceField):
                cleaned_data[field_name] = value.upper()
        return cleaned_data
