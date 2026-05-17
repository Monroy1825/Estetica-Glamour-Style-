from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.timezone import now
from django.utils import timezone as tz_module
from django.db.models import Count, F
from django.db.models.functions import TruncHour, TruncDate
from datetime import timedelta, date
import calendar as cal_lib
import json
from apps.clientes.models import Cliente
from apps.transacciones.models import Cita, Venta
from apps.servicios.models import Producto


@login_required
def dashboard(request):
    hoy = now().date()
    mes_actual = now().month

    total_clientes = Cliente.objects.count()
    citas_hoy = Cita.objects.filter(fecha_inicio__date=date.today(), activo=True).count()
    ventas_mes = Venta.objects.filter(fecha__month=mes_actual, activo=True).count()

    citas_hoy_lista = (
        Cita.objects
        .filter(fecha_inicio__date=date.today(), activo=True)
        .select_related('cliente', 'empleado', 'servicio')
        .order_by('fecha_inicio')
    )

    ventas_recientes = (
        Venta.objects
        .filter(activo=True)
        .select_related('cliente', 'empleado')
        .order_by('-fecha')[:3]
    )

    stock_bajo = Producto.objects.filter(activo=True, stock_actual__lte=F('stock_minimo')).count()
    citas_pendientes_hoy = Cita.objects.filter(fecha_inicio__date=hoy, estado='pendiente', activo=True).count()
    notificaciones = stock_bajo + citas_pendientes_hoy


    labels_ventas = []
    data_ventas = []
    data_citas = []
    for i in range(1, 32):
        labels_ventas.append(str(i))
        data_ventas.append(
            Venta.objects.filter(fecha__day=i, fecha__month=hoy.month, activo=True).count()
        )
        data_citas.append(
            Cita.objects.filter(fecha_inicio__day=i, fecha_inicio__month=hoy.month, activo=True).count()
        )

    return render(request, 'dashboard.html', {
        'total_clientes': total_clientes,
        'citas_hoy': citas_hoy,
        'ventas_mes': ventas_mes,
        'stock_bajo': stock_bajo,
        'citas_hoy_lista': citas_hoy_lista,
        'ventas_recientes': ventas_recientes,
        'notificaciones': notificaciones,
        'citas_pendientes_hoy': citas_pendientes_hoy,
        'labels_ventas': json.dumps(labels_ventas),
        'data_ventas': json.dumps(data_ventas),
        'data_citas': json.dumps(data_citas),
    })


@login_required
def dashboard_chart_data(request):
    periodo = request.GET.get('periodo', 'mes')
    hoy = now().date()
    tz = tz_module.get_current_timezone()

    if periodo == 'dia':
        ventas_qs = (
            Venta.objects
            .filter(activo=True, fecha__date=hoy)
            .annotate(slot=TruncHour('fecha', tzinfo=tz))
            .values('slot')
            .annotate(total=Count('id'))
        )
        citas_qs = (
            Cita.objects
            .filter(activo=True, fecha_inicio__date=hoy)
            .annotate(slot=TruncHour('fecha_inicio', tzinfo=tz))
            .values('slot')
            .annotate(total=Count('id'))
        )
        ventas_dict = {v['slot'].hour: v['total'] for v in ventas_qs}
        citas_dict = {c['slot'].hour: c['total'] for c in citas_qs}
        labels = [f'{h:02d}:00' for h in range(24)]
        ventas_data = [ventas_dict.get(h, 0) for h in range(24)]
        citas_data = [citas_dict.get(h, 0) for h in range(24)]

    elif periodo == 'semana':
        inicio = hoy - timedelta(days=6)
        dias = [inicio + timedelta(days=i) for i in range(7)]
        ventas_qs = (
            Venta.objects
            .filter(activo=True, fecha__date__range=[inicio, hoy])
            .annotate(slot=TruncDate('fecha', tzinfo=tz))
            .values('slot')
            .annotate(total=Count('id'))
        )
        citas_qs = (
            Cita.objects
            .filter(activo=True, fecha_inicio__date__range=[inicio, hoy])
            .annotate(slot=TruncDate('fecha_inicio', tzinfo=tz))
            .values('slot')
            .annotate(total=Count('id'))
        )
        ventas_dict = {v['slot']: v['total'] for v in ventas_qs}
        citas_dict = {c['slot']: c['total'] for c in citas_qs}
        DIAS_ES = ['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom']
        labels = [DIAS_ES[d.weekday()] + ' ' + str(d.day) for d in dias]
        ventas_data = [ventas_dict.get(d, 0) for d in dias]
        citas_data = [citas_dict.get(d, 0) for d in dias]

    else:  # mes
        anio = hoy.year
        mes = hoy.month
        dias_mes = cal_lib.monthrange(anio, mes)[1]
        dias = [date(anio, mes, d) for d in range(1, dias_mes + 1)]
        ventas_qs = (
            Venta.objects
            .filter(activo=True, fecha__month=mes, fecha__year=anio)
            .annotate(slot=TruncDate('fecha', tzinfo=tz))
            .values('slot')
            .annotate(total=Count('id'))
        )
        citas_qs = (
            Cita.objects
            .filter(activo=True, fecha_inicio__month=mes, fecha_inicio__year=anio)
            .annotate(slot=TruncDate('fecha_inicio', tzinfo=tz))
            .values('slot')
            .annotate(total=Count('id'))
        )
        ventas_dict = {v['slot']: v['total'] for v in ventas_qs}
        citas_dict = {c['slot']: c['total'] for c in citas_qs}
        labels = [str(d.day) for d in dias]
        ventas_data = [ventas_dict.get(d, 0) for d in dias]
        citas_data = [citas_dict.get(d, 0) for d in dias]

    return JsonResponse({'labels': labels, 'ventas': ventas_data, 'citas': citas_data})


# ========== NUEVA FUNCIÓN - AGREGAR AL FINAL ==========
@login_required
def reporte_margenes(request):
    """Reporte de márgenes de ganancia por producto"""
    
    # Ventas de productos con su margen
    ventas_productos = Venta.objects.filter(
        activo=True,
        producto__isnull=False,
        estatus='pagada'
    ).select_related('producto', 'cliente')
    
    # Agrupar por producto
    productos_margen = []
    for venta in ventas_productos:
        # Calcular margen manualmente por si las propiedades no existen
        costo = float(venta.producto.costo) if venta.producto else 0
        precio_venta = float(venta.total)
        margen = precio_venta - costo
        porcentaje = ((precio_venta - costo) / costo * 100) if costo > 0 else 0
        
        productos_margen.append({
            'producto': venta.producto.nombre,
            'precio_venta': precio_venta,
            'costo': costo,
            'margen': margen,
            'porcentaje': porcentaje,
            'fecha': venta.fecha,
            'cliente': venta.cliente.nombre,
            'cantidad': 1
        })
    
    # Ordenar por margen (mayor a menor)
    productos_margen.sort(key=lambda x: x['margen'], reverse=True)
    
    # Estadísticas
    total_ventas = ventas_productos.count()
    margen_total = sum(p['margen'] for p in productos_margen)
    promedio_margen = margen_total / total_ventas if total_ventas > 0 else 0
    
    return render(request, 'operaciones/reporte_margenes.html', {
        'productos_margen': productos_margen,
        'total_ventas': total_ventas,
        'margen_total': margen_total,
        'promedio_margen': promedio_margen,
    })
