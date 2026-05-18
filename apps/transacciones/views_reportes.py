import io
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count, ExpressionWrapper, FloatField, F
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
    
    # Calcular estadísticas
    total_compras = compras.count()
    total_inversion = 0
    for c in compras:
        total_inversion += float(c.precio_unitario) * c.cantidad
    
    proveedores_distintos = compras.values('proveedor').distinct().count()
    promedio_compra = total_inversion / total_compras if total_compras > 0 else 0
    
    # Obtener nombres de meses
    nombre_mes_desde = dict(MESES).get(int(mes_desde) if mes_desde else None, '')
    nombre_mes_hasta = dict(MESES).get(int(mes_hasta) if mes_hasta else None, '')
    
    years = range(anio - 2, anio + 1)
    
    return render(request, 'reportes/reporte_compras.html', {
        'compras': compras,
        'meses': MESES,
        'years': years,
        'mes_desde': mes_desde,
        'mes_hasta': mes_hasta,
        'anio_seleccionado': anio,
        'nombre_mes_desde': nombre_mes_desde,
        'nombre_mes_hasta': nombre_mes_hasta,
        'total_compras': total_compras,
        'total_inversion': total_inversion,
        'proveedores_distintos': proveedores_distintos,
        'promedio_compra': promedio_compra,
    })

# ==================== HELPERS DE GRÁFICAS ====================

def _make_bar(categories, values, title, width=340, height=180, bar_colors=None):
    from reportlab.graphics.shapes import Drawing, String
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.lib import colors as rl_colors

    if not categories or not any(v > 0 for v in values):
        return None

    d = Drawing(width, height)
    d.add(String(width / 2, height - 12, title,
                 textAnchor='middle', fontSize=9, fontName='Helvetica-Bold',
                 fillColor=rl_colors.HexColor('#7b2d8b')))

    bc = VerticalBarChart()
    bc.x = 42
    bc.y = 28
    bc.width = width - 58
    bc.height = height - 52
    bc.data = [list(values)]
    bc.bars[0].strokeColor = rl_colors.white
    bc.bars[0].strokeWidth = 0.5
    if bar_colors:
        for i, color in enumerate(bar_colors):
            if i < len(values):
                bc.bars[0, i].fillColor = rl_colors.HexColor(color)
    else:
        bc.bars[0].fillColor = rl_colors.HexColor('#7b2d8b')
    bc.categoryAxis.categoryNames = list(categories)
    bc.categoryAxis.labels.fontSize = 7
    bc.categoryAxis.labels.angle = 30 if len(categories) > 3 else 0
    bc.categoryAxis.labels.dy = -10 if len(categories) > 3 else -5
    bc.valueAxis.labels.fontSize = 7
    bc.valueAxis.visibleGrid = True
    bc.valueAxis.gridStrokeColor = rl_colors.HexColor('#e9ecef')
    bc.valueAxis.gridStrokeDashArray = [2, 2]

    d.add(bc)
    return d


# ==================== FUNCIONES PARA PDF ====================
def _build_pdf(title, subtitle, headers, rows, stats=None, charts=None):
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib import colors as C
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER

    PRIMARY       = C.HexColor('#7b2d8b')
    PRIMARY_DARK  = C.HexColor('#5e2069')
    PRIMARY_LIGHT = C.HexColor('#f3e6f7')
    WHITE         = C.white
    GRAY_100      = C.HexColor('#f8f9fa')
    GRAY_200      = C.HexColor('#e9ecef')
    GRAY_600      = C.HexColor('#6c757d')
    GRAY_800      = C.HexColor('#343a40')

    STATUS_BG = {
        'Pagada': C.HexColor('#d4edda'),    'pagada': C.HexColor('#d4edda'),
        'Pendiente': C.HexColor('#fff3cd'), 'pendiente': C.HexColor('#fff3cd'),
        'Cancelada': C.HexColor('#f8d7da'), 'cancelada': C.HexColor('#f8d7da'),
        'Completada': C.HexColor('#d4edda'),'completada': C.HexColor('#d4edda'),
        'Confirmada': C.HexColor('#d1ecf1'),'confirmada': C.HexColor('#d1ecf1'),
    }
    STATUS_FG = {
        'Pagada': C.HexColor('#155724'),    'pagada': C.HexColor('#155724'),
        'Pendiente': C.HexColor('#856404'), 'pendiente': C.HexColor('#856404'),
        'Cancelada': C.HexColor('#721c24'), 'cancelada': C.HexColor('#721c24'),
        'Completada': C.HexColor('#155724'),'completada': C.HexColor('#155724'),
        'Confirmada': C.HexColor('#0c5460'),'confirmada': C.HexColor('#0c5460'),
    }

    hoy = timezone.now()
    buffer = io.BytesIO()
    MARGIN = 30
    PAGE_W, _ = landscape(letter)
    CW = PAGE_W - 2 * MARGIN

    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(letter),
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
    )

    S = getSampleStyleSheet()
    def ps(name, **kw):
        return ParagraphStyle(name, parent=S['Normal'], **kw)

    sty_wt = ps('wt', fontSize=20, fontName='Helvetica-Bold', textColor=WHITE)
    sty_ws = ps('ws', fontSize=11, fontName='Helvetica',      textColor=C.HexColor('#e8cff0'))
    sty_wd = ps('wd', fontSize=8,  fontName='Helvetica',      textColor=C.HexColor('#c9a8d8'))
    sty_sv = ps('sv', fontSize=22, fontName='Helvetica-Bold', textColor=PRIMARY,  alignment=TA_CENTER)
    sty_sl = ps('sl', fontSize=8,  fontName='Helvetica',      textColor=GRAY_600, alignment=TA_CENTER, spaceBefore=2)
    sty_th = ps('th', fontSize=8,  fontName='Helvetica-Bold', textColor=WHITE)
    sty_td = ps('td', fontSize=8,  fontName='Helvetica',      textColor=GRAY_800)

    elements = []

    # ── ENCABEZADO ───────────────────────────────────────────────
    from reportlab.platypus import Image as RLImage
    from django.conf import settings
    from reportlab.lib.enums import TA_RIGHT, TA_CENTER
    import os as _os

    LOGO_SIZE = 52
    LEFT_W    = 120
    RIGHT_W   = CW - LEFT_W
    logo_path = str(settings.BASE_DIR / 'static' / 'img' / 'logo.png')

    sty_company = ps('co', fontSize=11, fontName='Helvetica-Bold',
                     textColor=WHITE, alignment=TA_CENTER, spaceBefore=5)
    sty_rpt     = ps('rp', fontSize=15, fontName='Helvetica-Bold',
                     textColor=WHITE, alignment=TA_RIGHT)
    sty_dt      = ps('dt', fontSize=8,  fontName='Helvetica',
                     textColor=C.HexColor('#c9a8d8'), alignment=TA_RIGHT, spaceBefore=26)

    logo_cell = RLImage(logo_path, width=LOGO_SIZE, height=LOGO_SIZE) \
        if _os.path.exists(logo_path) else Paragraph('', sty_td)

    left_col = Table(
        [[logo_cell],
         [Paragraph('Glamour Style', sty_company)]],
        colWidths=[LEFT_W],
    )
    left_col.setStyle(TableStyle([
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    right_col = Table(
        [[Paragraph(subtitle, sty_rpt)],
         [Spacer(1, 18)],
         [Paragraph(f'Generado: {hoy.strftime("%d/%m/%Y  %H:%M")}', sty_dt)]],
        colWidths=[RIGHT_W - 24],
    )
    right_col.setStyle(TableStyle([
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    hdr = Table(
        [[left_col, right_col]],
        colWidths=[LEFT_W, RIGHT_W],
    )
    hdr.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), PRIMARY),
        ('LEFTPADDING',   (0, 0), (0,  -1), 20),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 24),
        ('TOPPADDING',    (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(hdr)
    elements.append(Spacer(1, 14))

    # ── TARJETAS DE ESTADÍSTICAS ─────────────────────────────────
    if stats:
        n = len(stats)
        card_w = CW / n

        def _card(lbl, val):
            inner = Table(
                [[Paragraph(val, sty_sv)],
                 [Paragraph(lbl, sty_sl)]],
                colWidths=[card_w - 14],
            )
            inner.setStyle(TableStyle([
                ('BACKGROUND',    (0, 0), (-1, -1), PRIMARY_LIGHT),
                ('TOPPADDING',    (0, 0), (-1, -1), 14),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
                ('LEFTPADDING',   (0, 0), (-1, -1), 8),
                ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
                ('LINEBEFORE',    (0, 0), (0,  -1),  5, PRIMARY),
                ('BOX',           (0, 0), (-1, -1),  0.5, GRAY_200),
            ]))
            return inner

        cards_tbl = Table(
            [[_card(lbl, val) for lbl, val in stats]],
            colWidths=[card_w] * n,
        )
        cards_tbl.setStyle(TableStyle([
            ('LEFTPADDING',  (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(cards_tbl)
        elements.append(Spacer(1, 14))

    # ── GRÁFICAS ─────────────────────────────────────────────────
    if charts:
        valid = [c for c in charts if c is not None]
        if valid:
            ct = Table([valid], colWidths=[c.width for c in valid])
            ct.setStyle(TableStyle([
                ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
                ('BOX',           (0, 0), (-1, -1),  0.5, GRAY_200),
                ('BACKGROUND',    (0, 0), (-1, -1), WHITE),
                ('TOPPADDING',    (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING',   (0, 0), (-1, -1), 14),
                ('RIGHTPADDING',  (0, 0), (-1, -1), 14),
            ]))
            elements.append(ct)
            elements.append(Spacer(1, 14))

    # ── TABLA DE DATOS ───────────────────────────────────────────
    th_row = [Paragraph(h, sty_th) for h in headers]
    data = [th_row] + [[Paragraph(str(cell), sty_td) for cell in row] for row in rows]

    tbl = Table(data, repeatRows=1)
    ts = [
        ('BACKGROUND',    (0,  0), (-1,  0), PRIMARY),
        ('LINEBELOW',     (0,  0), (-1,  0),  1.5, PRIMARY_DARK),
        ('ALIGN',         (0,  0), (-1, -1), 'LEFT'),
        ('VALIGN',        (0,  0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0,  0), (-1, -1),  6),
        ('BOTTOMPADDING', (0,  0), (-1, -1),  6),
        ('LEFTPADDING',   (0,  0), (-1, -1),  8),
        ('RIGHTPADDING',  (0,  0), (-1, -1),  8),
        ('GRID',          (0,  0), (-1, -1),  0.3, GRAY_200),
    ]
    for i in range(1, len(data)):
        ts.append(('BACKGROUND', (0, i), (-1, i), WHITE if i % 2 != 0 else GRAY_100))
    for i, row in enumerate(rows, start=1):
        last = str(row[-1])
        if last in STATUS_BG:
            ts += [
                ('BACKGROUND', (-1, i), (-1, i), STATUS_BG[last]),
                ('TEXTCOLOR',  (-1, i), (-1, i), STATUS_FG[last]),
                ('FONTNAME',   (-1, i), (-1, i), 'Helvetica-Bold'),
            ]
    tbl.setStyle(TableStyle(ts))
    elements.append(tbl)

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

    total_ventas = ventas.count()
    total_ingresos = ventas.aggregate(total=Sum('total'))['total'] or 0
    promedio = round(total_ingresos / total_ventas, 2) if total_ventas > 0 else 0
    clientes_atendidos = ventas.values('cliente').distinct().count()

    stats = [
        ('Total Ventas', str(total_ventas)),
        ('Ingresos Totales', f'${total_ingresos:,.2f}'),
        ('Promedio por Venta', f'${promedio:,.2f}'),
        ('Clientes Atendidos', str(clientes_atendidos)),
    ]

    estatus_map = {e['estatus']: e['n'] for e in ventas.values('estatus').annotate(n=Count('id'))}
    chart_estatus = _make_bar(
        ['Pagada', 'Pendiente', 'Cancelada'],
        [estatus_map.get('pagada', 0), estatus_map.get('pendiente', 0), estatus_map.get('cancelada', 0)],
        'Estatus de Ventas',
        bar_colors=['#28a745', '#ffc107', '#dc3545'],
    )

    metodo_map = {m['metodo_pago']: m['n'] for m in ventas.values('metodo_pago').annotate(n=Count('id'))}
    chart_metodo = _make_bar(
        ['Efectivo', 'Tarjeta', 'Transferencia'],
        [metodo_map.get('efectivo', 0), metodo_map.get('tarjeta', 0), metodo_map.get('transferencia', 0)],
        'Ventas por Método de Pago',
    )

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

    buffer = _build_pdf('Ventas', f'Reporte de Ventas - {periodo}', headers, rows, stats=stats, charts=[chart_estatus, chart_metodo])
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

    total_citas = citas.count()
    citas_completadas = citas.filter(estado='completada').count()
    citas_pendientes = citas.filter(estado='pendiente').count()

    stats = [
        ('Total Citas', str(total_citas)),
        ('Completadas', str(citas_completadas)),
        ('Pendientes', str(citas_pendientes)),
    ]

    estado_map = {e['estado']: e['n'] for e in citas.values('estado').annotate(n=Count('id'))}
    chart_estado = _make_bar(
        ['Pendiente', 'Confirmada', 'Completada', 'Cancelada'],
        [estado_map.get('pendiente', 0), estado_map.get('confirmada', 0),
         estado_map.get('completada', 0), estado_map.get('cancelada', 0)],
        'Estado de Citas',
        width=300,
        bar_colors=['#ffc107', '#17a2b8', '#28a745', '#dc3545'],
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

    buffer = _build_pdf('Citas', f'Reporte de Citas - {periodo}', headers, rows, stats=stats, charts=[chart_estado])
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

    total_compras = compras.count()
    total_inversion = sum(float(c.precio_unitario) * c.cantidad for c in compras)
    promedio_compra = round(total_inversion / total_compras, 2) if total_compras > 0 else 0
    proveedores_distintos = compras.values('proveedor').distinct().count()

    stats = [
        ('Total Compras', str(total_compras)),
        ('Total Inversión', f'${total_inversion:,.2f}'),
        ('Promedio por Compra', f'${promedio_compra:,.2f}'),
        ('Proveedores', str(proveedores_distintos)),
    ]

    prov_qs = list(
        compras.values('proveedor').annotate(
            total=Sum(ExpressionWrapper(F('precio_unitario') * F('cantidad'), output_field=FloatField()))
        ).order_by('-total')[:5]
    )
    chart_prov = _make_bar(
        [p['proveedor'][:14] for p in prov_qs],
        [float(p['total']) for p in prov_qs],
        'Top Proveedores por Inversión ($)',
        width=480,
    ) if prov_qs else None

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

    buffer = _build_pdf('Compras', f'Reporte de Compras - {periodo}', headers, rows, stats=stats, charts=[chart_prov])
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
            f'${p.costo}',
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
    
    # Obtener nombres de meses
    nombre_mes_desde = dict(MESES).get(int(mes_desde) if mes_desde else None, '')
    nombre_mes_hasta = dict(MESES).get(int(mes_hasta) if mes_hasta else None, '')
    
    years = range(anio - 2, anio + 1)
    
    return render(request, 'reportes/reporte_citas.html', {
        'citas': citas,
        'meses': MESES,
        'years': years,
        'mes_desde': mes_desde,
        'mes_hasta': mes_hasta,
        'anio_seleccionado': anio,
        'nombre_mes_desde': nombre_mes_desde,
        'nombre_mes_hasta': nombre_mes_hasta,
        'total_citas': total_citas,
        'citas_completadas': citas_completadas,
        'citas_pendientes': citas_pendientes,
    })