from django.contrib import admin
from .models import Empleado


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'rol', 'fecha_ingreso', 'activo')
    search_fields = ('nombre', 'telefono')
    list_filter = ('rol', 'fecha_ingreso', 'activo')
