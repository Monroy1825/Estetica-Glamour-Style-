import re
from django import forms
from .models import Cliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'telefono', 'email']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo',
                'style': 'text-transform: uppercase',
                'data-tipo': 'nombre',
            }),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        if nombre and not re.match(r'^[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ\s]+$', nombre):
            raise forms.ValidationError('El nombre solo puede contener letras y espacios.')
        return nombre

    def clean_telefono(self):
        tel = self.cleaned_data.get('telefono', '').strip()
        if tel and not re.match(r'^\d{10}$', tel):
            raise forms.ValidationError('El teléfono debe tener exactamente 10 dígitos numéricos.')
        return tel

    def clean(self):
        cleaned_data = super().clean()
        for field_name, value in cleaned_data.items():
            field = self.fields.get(field_name)
            if isinstance(value, str) and field_name != 'email' and not isinstance(field, forms.ChoiceField):
                cleaned_data[field_name] = value.upper()
        return cleaned_data
