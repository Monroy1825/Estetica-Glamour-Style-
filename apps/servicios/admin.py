from django.contrib import admin
from .models import Servicio, Producto


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio_base')
    search_fields = ('nombre',)
    list_filter = ('categoria',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'marca', 'costo', 'precio_venta', 'stock_actual', 'stock_minimo')
    search_fields = ('nombre', 'marca')
    list_filter = ('marca',)
