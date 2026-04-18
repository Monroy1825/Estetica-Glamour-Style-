from django.contrib import admin
from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'email', 'fecha_registro', 'activo')
    search_fields = ('nombre', 'telefono', 'email')
    list_filter = ('fecha_registro', 'activo')
