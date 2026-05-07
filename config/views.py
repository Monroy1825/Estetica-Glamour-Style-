from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.timezone import now
from django.utils import timezone as tz_module
from django.db.models import Count, F
from django.db.models.functions import TruncHour, TruncDate
from datetime import timedelta, date
import calendar as cal_lib
from apps.clientes.models import Cliente
from apps.operaciones.models import Cita, Venta
from apps.servicios.models import Producto


@login_required
def dashboard(request):
    hoy = now().date()
    mes_actual = now().month

    total_clientes = Cliente.objects.count()
    citas_hoy = Cita.objects.filter(fecha_inicio__date=hoy, activo=True).count()
    ventas_mes = Venta.objects.filter(fecha__month=mes_actual, activo=True).count()

    citas_hoy_lista = (
        Cita.objects
        .filter(fecha_inicio__date=hoy, activo=True)
        .select_related('cliente', 'empleado', 'servicio')
        .order_by('fecha_inicio')[:2]
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

    return render(request, 'dashboard.html', {
        'total_clientes': total_clientes,
        'citas_hoy': citas_hoy,
        'ventas_mes': ventas_mes,
        'stock_bajo': stock_bajo,
        'citas_hoy_lista': citas_hoy_lista,
        'ventas_recientes': ventas_recientes,
        'notificaciones': notificaciones,
        'citas_pendientes_hoy': citas_pendientes_hoy,
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