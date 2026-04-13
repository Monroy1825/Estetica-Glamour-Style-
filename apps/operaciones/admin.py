from django.contrib import admin
from .models import Cita, Venta, Compra, Cotizacion


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'empleado', 'servicio', 'fecha_inicio', 'estado')
    search_fields = ('cliente__nombre', 'empleado__nombre', 'servicio__nombre')
    list_filter = ('estado', 'fecha_inicio')


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'empleado', 'fecha', 'tipo', 'metodo_pago', 'estatus', 'total')
    search_fields = ('cliente__nombre', 'empleado__nombre')
    list_filter = ('estatus', 'tipo', 'metodo_pago', 'fecha')


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ('proveedor', 'empleado', 'fecha', 'total')
    search_fields = ('proveedor', 'empleado__nombre')
    list_filter = ('fecha',)


@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'servicio', 'producto', 'fecha', 'vigencia', 'estado')
    search_fields = ('cliente__nombre',)
    list_filter = ('estado', 'fecha')
