from django.contrib import admin
from .models import Servicio, Producto


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio_base', 'activo')
    search_fields = ('nombre',)
    list_filter = ('categoria', 'activo')


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'marca', 'costo', 'precio_venta', 'stock_actual', 'stock_minimo', 'activo')
    search_fields = ('nombre', 'marca')
    list_filter = ('marca', 'activo')
