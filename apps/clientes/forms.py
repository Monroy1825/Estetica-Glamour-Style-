from django import forms
from .models import Cliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'telefono', 'email']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo', 'style': 'text-transform: uppercase'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        for field_name, value in cleaned_data.items():
            field = self.fields.get(field_name)
            if isinstance(value, str) and field_name != 'email' and not isinstance(field, forms.ChoiceField):
                cleaned_data[field_name] = value.upper()
        return cleaned_data
