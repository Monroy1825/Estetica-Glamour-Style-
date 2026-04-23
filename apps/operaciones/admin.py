from django.contrib import admin
from .models import Cita, Venta, Compra, Cotizacion


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'empleado', 'servicio', 'fecha_inicio', 'estado', 'activo')
    search_fields = ('cliente__nombre', 'empleado__nombre', 'servicio__nombre')
    list_filter = ('estado', 'fecha_inicio', 'activo')


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'empleado', 'fecha', 'tipo', 'metodo_pago', 'estatus', 'total', 'activo')
    search_fields = ('cliente__nombre', 'empleado__nombre')
    list_filter = ('estatus', 'tipo', 'metodo_pago', 'fecha', 'activo')


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ('proveedor', 'empleado', 'fecha', 'precio_unitario', 'activo')
    search_fields = ('proveedor', 'empleado__nombre')
    list_filter = ('fecha', 'activo')


@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'servicio', 'producto', 'fecha', 'vigencia', 'estado', 'activo')
    search_fields = ('cliente__nombre',)
    list_filter = ('estado', 'fecha', 'activo')
