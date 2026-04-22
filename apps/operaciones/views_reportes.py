from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Venta, Cita
from apps.servicios.models import Producto


@login_required
def reporte_ventas(request):
    ventas = Venta.objects.filter(activo=True).select_related('cliente', 'empleado', 'producto').order_by('-fecha')
    return render(request, 'reportes/reporte_ventas.html', {'ventas': ventas})


@login_required
def reporte_citas(request):
    citas = Cita.objects.filter(activo=True).select_related('cliente', 'empleado', 'servicio').order_by('-fecha_inicio')
    return render(request, 'reportes/reporte_citas.html', {'citas': citas})


@login_required
def reporte_stock(request):
    productos = Producto.objects.filter(activo=True).order_by('nombre')
    return render(request, 'reportes/reporte_stock.html', {'productos': productos})
