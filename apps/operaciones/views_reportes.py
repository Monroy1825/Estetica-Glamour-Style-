import io

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from .models import Venta, Cita
from apps.servicios.models import Producto

MESES = [
    (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
    (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
    (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre'),
]


@login_required
def reporte_ventas(request):
    hoy = timezone.now()
    mes = int(request.GET.get('mes', hoy.month))
    anio = hoy.year
    ventas = (
        Venta.objects.filter(activo=True, fecha__month=mes, fecha__year=anio)
        .select_related('cliente', 'empleado', 'producto')
        .order_by('-fecha')
    )
    return render(request, 'reportes/reporte_ventas.html', {
        'ventas': ventas,
        'meses': MESES,
        'mes_actual': mes,
    })


@login_required
def reporte_citas(request):
    hoy = timezone.now()
    mes = int(request.GET.get('mes', hoy.month))
    anio = hoy.year
    citas = (
        Cita.objects.filter(activo=True, fecha_inicio__month=mes, fecha_inicio__year=anio)
        .select_related('cliente', 'empleado', 'servicio')
        .order_by('-fecha_inicio')
    )
    return render(request, 'reportes/reporte_citas.html', {
        'citas': citas,
        'meses': MESES,
        'mes_actual': mes,
    })


@login_required
def reporte_stock(request):
    productos = Producto.objects.filter(activo=True).order_by('nombre')
    return render(request, 'reportes/reporte_stock.html', {'productos': productos})


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
    mes = int(request.GET.get('mes', hoy.month))
    anio = hoy.year
    nombre_mes = dict(MESES)[mes]

    ventas = (
        Venta.objects.filter(activo=True, fecha__month=mes, fecha__year=anio)
        .select_related('cliente', 'empleado', 'producto')
        .order_by('-fecha')
    )

    headers = ['#', 'Fecha', 'Cliente', 'Empleado', 'Producto', 'Total', 'Método', 'Estatus']
    rows = [
        [
            str(v.pk),
            v.fecha.strftime('%d/%m/%Y'),
            str(v.cliente),
            str(v.empleado),
            str(v.producto) if v.producto else '—',
            f'${v.total}',
            v.get_metodo_pago_display(),
            v.get_estatus_display(),
        ]
        for v in ventas
    ]

    buffer = _build_pdf('Ventas', f'Reporte de Ventas — {nombre_mes} {anio}', headers, rows)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_ventas_{nombre_mes}_{anio}.pdf"'
    return response


@login_required
def reporte_citas_pdf(request):
    hoy = timezone.now()
    mes = int(request.GET.get('mes', hoy.month))
    anio = hoy.year
    nombre_mes = dict(MESES)[mes]

    citas = (
        Cita.objects.filter(activo=True, fecha_inicio__month=mes, fecha_inicio__year=anio)
        .select_related('cliente', 'empleado', 'servicio')
        .order_by('-fecha_inicio')
    )

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

    buffer = _build_pdf('Citas', f'Reporte de Citas — {nombre_mes} {anio}', headers, rows)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_citas_{nombre_mes}_{anio}.pdf"'
    return response
