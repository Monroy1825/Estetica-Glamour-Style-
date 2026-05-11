import io
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from .models import Venta, Cita, Compra
from apps.servicios.models import Producto

MESES = [
    (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
    (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
    (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre'),
]


# ==================== REPORTE DE VENTAS ====================
@login_required
def reporte_ventas(request):
    hoy = timezone.now()
    
    # Obtener parámetros de filtro
    mes_desde = request.GET.get('mes_desde')
    mes_hasta = request.GET.get('mes_hasta')
    anio = int(request.GET.get('anio', hoy.year))
    
    # Si no hay filtros, usar el mes actual
    if not mes_desde and not mes_hasta:
        mes_desde = str(hoy.month)
        mes_hasta = str(hoy.month)
    
    ventas = Venta.objects.filter(activo=True, fecha__year=anio).select_related(
        'cliente', 'empleado', 'producto', 'cita__servicio'
    )
    
    # Aplicar filtro de rango de meses
    if mes_desde and mes_hasta:
        ventas = ventas.filter(
            Q(fecha__month__gte=int(mes_desde), fecha__month__lte=int(mes_hasta))
        )
    elif mes_desde:
        ventas = ventas.filter(fecha__month=int(mes_desde))
    elif mes_hasta:
        ventas = ventas.filter(fecha__month=int(mes_hasta))
    
    ventas = ventas.order_by('-fecha')
    
    # Calcular totales para las estadísticas
    total_ventas = ventas.count()
    total_ingresos = ventas.aggregate(total=Sum('total'))['total'] or 0
    clientes_atendidos = ventas.values('cliente').distinct().count()
    
    # Obtener nombre de los meses seleccionados
    nombre_mes_desde = dict(MESES).get(int(mes_desde) if mes_desde else None, '')
    nombre_mes_hasta = dict(MESES).get(int(mes_hasta) if mes_hasta else None, '')
    
    # Rango de años (últimos 3 años)
    anio_actual = hoy.year
    years = range(anio_actual - 2, anio_actual + 1)
    
    return render(request, 'reportes/reporte_ventas.html', {
        'ventas': ventas,
        'meses': MESES,
        'years': years,
        'mes_desde': mes_desde,
        'mes_hasta': mes_hasta,
        'anio_seleccionado': anio,
        'nombre_mes_desde': nombre_mes_desde,
        'nombre_mes_hasta': nombre_mes_hasta,
        'total_ventas': total_ventas,
        'total_ingresos': total_ingresos,
        'clientes_atendidos': clientes_atendidos,
    })


# ==================== REPORTE DE CITAS ====================
@login_required
def reporte_citas(request):
    hoy = timezone.now()
    
    mes_desde = request.GET.get('mes_desde')
    mes_hasta = request.GET.get('mes_hasta')
    anio = int(request.GET.get('anio', hoy.year))
    
    if not mes_desde and not mes_hasta:
        mes_desde = str(hoy.month)
        mes_hasta = str(hoy.month)
    
    citas = Cita.objects.filter(activo=True, fecha_inicio__year=anio).select_related(
        'cliente', 'empleado', 'servicio'
    )
    
    if mes_desde and mes_hasta:
        citas = citas.filter(
            Q(fecha_inicio__month__gte=int(mes_desde), fecha_inicio__month__lte=int(mes_hasta))
        )
    elif mes_desde:
        citas = citas.filter(fecha_inicio__month=int(mes_desde))
    elif mes_hasta:
        citas = citas.filter(fecha_inicio__month=int(mes_hasta))
    
    citas = citas.order_by('-fecha_inicio')
    
    total_citas = citas.count()
    citas_completadas = citas.filter(estado='completada').count()
    citas_pendientes = citas.filter(estado='pendiente').count()
    
    years = range(anio - 2, anio + 1)
    
    return render(request, 'reportes/reporte_citas.html', {
        'citas': citas,
        'meses': MESES,
        'years': years,
        'mes_desde': mes_desde,
        'mes_hasta': mes_hasta,
        'anio_seleccionado': anio,
        'total_citas': total_citas,
        'citas_completadas': citas_completadas,
        'citas_pendientes': citas_pendientes,
    })


# ==================== REPORTE DE STOCK ====================
@login_required
def reporte_stock(request):
    productos = Producto.objects.filter(activo=True).order_by('nombre')
    total_productos = productos.count()
    stock_total = productos.aggregate(total=Sum('stock_actual'))['total'] or 0
    productos_bajo_stock = productos.filter(stock_actual__lte=5).count()
    
    return render(request, 'reportes/reporte_stock.html', {
        'productos': productos,
        'total_productos': total_productos,
        'stock_total': stock_total,
        'productos_bajo_stock': productos_bajo_stock,
    })


# ==================== REPORTE DE COMPRAS ====================
@login_required
def reporte_compras(request):
    hoy = timezone.now()
    
    mes_desde = request.GET.get('mes_desde')
    mes_hasta = request.GET.get('mes_hasta')
    anio = int(request.GET.get('anio', hoy.year))
    
    if not mes_desde and not mes_hasta:
        mes_desde = str(hoy.month)
        mes_hasta = str(hoy.month)
    
    compras = Compra.objects.filter(activo=True, fecha__year=anio).select_related('empleado', 'producto')
    
    if mes_desde and mes_hasta:
        compras = compras.filter(
            Q(fecha__month__gte=int(mes_desde), fecha__month__lte=int(mes_hasta))
        )
    elif mes_desde:
        compras = compras.filter(fecha__month=int(mes_desde))
    elif mes_hasta:
        compras = compras.filter(fecha__month=int(mes_hasta))
    
    compras = compras.order_by('-fecha')
    
    total_compras = compras.count()
    total_inversion = 0
    for c in compras:
        total_inversion += float(c.precio_unitario) * c.cantidad
    
    proveedores_distintos = compras.values('proveedor').distinct().count()
    years = range(anio - 2, anio + 1)
    
    return render(request, 'reportes/reporte_compras.html', {
        'compras': compras,
        'meses': MESES,
        'years': years,
        'mes_desde': mes_desde,
        'mes_hasta': mes_hasta,
        'anio_seleccionado': anio,
        'total_compras': total_compras,
        'total_inversion': total_inversion,
        'proveedores_distintos': proveedores_distintos,
    })


# ==================== FUNCIONES PARA PDF ====================
def _build_pdf(title, subtitle, headers, rows):
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    hoy = timezone.now()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph('Estética Glamour Style', styles['Title']))
    elements.append(Paragraph(subtitle, styles['Heading2']))
    elements.append(Paragraph(f'Generado: {hoy.strftime("%d/%m/%Y %H:%M")}', styles['Normal']))
    elements.append(Spacer(1, 12))

    data = [headers] + rows
    table = Table(data, repeatRows=1)

    style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7b2d8b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f3e6f7')))
    table.setStyle(TableStyle(style))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer


@login_required
def reporte_ventas_pdf(request):
    hoy = timezone.now()
    mes_desde = request.GET.get('mes_desde')
    mes_hasta = request.GET.get('mes_hasta')
    anio = int(request.GET.get('anio', hoy.year))
    
    if not mes_desde and not mes_hasta:
        mes_desde = str(hoy.month)
        mes_hasta = str(hoy.month)
    
    ventas = Venta.objects.filter(activo=True, fecha__year=anio).select_related('cliente', 'empleado', 'producto')
    
    if mes_desde and mes_hasta:
        ventas = ventas.filter(
            Q(fecha__month__gte=int(mes_desde), fecha__month__lte=int(mes_hasta))
        )
    
    ventas = ventas.order_by('-fecha')
    
    nombre_mes_desde = dict(MESES).get(int(mes_desde), '')
    nombre_mes_hasta = dict(MESES).get(int(mes_hasta), '')
    
    if mes_desde == mes_hasta:
        periodo = f'{nombre_mes_desde} {anio}'
    else:
        periodo = f'{nombre_mes_desde} - {nombre_mes_hasta} {anio}'

    headers = ['#', 'Fecha', 'Cliente', 'Empleado', 'Producto/Servicio', 'Total', 'Método', 'Estatus']
    rows = [
        [
            str(v.pk),
            v.fecha.strftime('%d/%m/%Y'),
            str(v.cliente),
            str(v.empleado),
            str(v.producto) if v.producto else (str(v.cita.servicio) if v.cita else '—'),
            f'${v.total}',
            v.get_metodo_pago_display(),
            v.get_estatus_display(),
        ]
        for v in ventas
    ]

    buffer = _build_pdf('Ventas', f'Reporte de Ventas - {periodo}', headers, rows)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_ventas_{periodo}.pdf"'
    return response


@login_required
def reporte_citas_pdf(request):
    hoy = timezone.now()
    mes_desde = request.GET.get('mes_desde')
    mes_hasta = request.GET.get('mes_hasta')
    anio = int(request.GET.get('anio', hoy.year))
    
    if not mes_desde and not mes_hasta:
        mes_desde = str(hoy.month)
        mes_hasta = str(hoy.month)
    
    citas = Cita.objects.filter(activo=True, fecha_inicio__year=anio).select_related('cliente', 'empleado', 'servicio')
    
    if mes_desde and mes_hasta:
        citas = citas.filter(
            Q(fecha_inicio__month__gte=int(mes_desde), fecha_inicio__month__lte=int(mes_hasta))
        )
    
    citas = citas.order_by('-fecha_inicio')
    
    nombre_mes_desde = dict(MESES).get(int(mes_desde), '')
    nombre_mes_hasta = dict(MESES).get(int(mes_hasta), '')
    
    if mes_desde == mes_hasta:
        periodo = f'{nombre_mes_desde} {anio}'
    else:
        periodo = f'{nombre_mes_desde} - {nombre_mes_hasta} {anio}'

    headers = ['#', 'Fecha inicio', 'Fecha fin', 'Cliente', 'Empleado', 'Servicio', 'Estado']
    rows = [
        [
            str(c.pk),
            c.fecha_inicio.strftime('%d/%m/%Y %H:%M'),
            c.fecha_fin.strftime('%d/%m/%Y %H:%M'),
            str(c.cliente),
            str(c.empleado),
            str(c.servicio),
            c.get_estado_display(),
        ]
        for c in citas
    ]

    buffer = _build_pdf('Citas', f'Reporte de Citas - {periodo}', headers, rows)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_citas_{periodo}.pdf"'
    return response


@login_required
def reporte_compras_pdf(request):
    hoy = timezone.now()
    mes_desde = request.GET.get('mes_desde')
    mes_hasta = request.GET.get('mes_hasta')
    anio = int(request.GET.get('anio', hoy.year))
    
    if not mes_desde and not mes_hasta:
        mes_desde = str(hoy.month)
        mes_hasta = str(hoy.month)
    
    compras = Compra.objects.filter(activo=True, fecha__year=anio).select_related('empleado', 'producto')
    
    if mes_desde and mes_hasta:
        compras = compras.filter(
            Q(fecha__month__gte=int(mes_desde), fecha__month__lte=int(mes_hasta))
        )
    
    compras = compras.order_by('-fecha')
    
    nombre_mes_desde = dict(MESES).get(int(mes_desde), '')
    nombre_mes_hasta = dict(MESES).get(int(mes_hasta), '')
    
    if mes_desde == mes_hasta:
        periodo = f'{nombre_mes_desde} {anio}'
    else:
        periodo = f'{nombre_mes_desde} - {nombre_mes_hasta} {anio}'

    headers = ['#', 'Fecha', 'Producto', 'Proveedor', 'Empleado', 'Cantidad', 'Precio Unit.', 'Total']
    rows = [
        [
            str(c.pk),
            c.fecha.strftime('%d/%m/%Y'),
            str(c.producto),
            c.proveedor,
            str(c.empleado),
            str(c.cantidad),
            f'${c.precio_unitario}',
            f'${c.total_compra}',
        ]
        for c in compras
    ]

    buffer = _build_pdf('Compras', f'Reporte de Compras - {periodo}', headers, rows)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_compras_{periodo}.pdf"'
    return response


@login_required
def reporte_stock_pdf(request):
    productos = Producto.objects.filter(activo=True).order_by('nombre')
    
    headers = ['#', 'Producto', 'Precio Compra', 'Precio Venta', 'Stock Actual', 'Presentación']
    rows = [
        [
            str(p.pk),
            p.nombre,
            f'${p.precio_compra}',
            f'${p.precio_venta}',
            str(p.stock_actual),
            p.presentacion or '—',
        ]
        for p in productos
    ]
    
    buffer = _build_pdf('Stock', 'Reporte de Inventario - Stock Actual', headers, rows)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_stock.pdf"'
    return response