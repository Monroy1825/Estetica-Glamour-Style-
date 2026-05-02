from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.timezone import now
from django.db.models import Count, F
from django.db.models.functions import TruncMonth
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

    ventas_por_mes = (
        Venta.objects
        .annotate(mes=TruncMonth('fecha'))
        .values('mes')
        .annotate(total=Count('id'))
        .order_by('mes')
    )

    MESES_ES = {
        'Jan': 'Ene', 'Feb': 'Feb', 'Mar': 'Mar', 'Apr': 'Abr',
        'May': 'May', 'Jun': 'Jun', 'Jul': 'Jul', 'Aug': 'Ago',
        'Sep': 'Sep', 'Oct': 'Oct', 'Nov': 'Nov', 'Dec': 'Dic'
    }
    labels = [MESES_ES.get(v['mes'].strftime('%b'), v['mes'].strftime('%b')) for v in ventas_por_mes]
    data = [v['total'] for v in ventas_por_mes]

    return render(request, 'dashboard.html', {
        'total_clientes': total_clientes,
        'citas_hoy': citas_hoy,
        'ventas_mes': ventas_mes,
        'stock_bajo': stock_bajo,
        'citas_hoy_lista': citas_hoy_lista,
        'ventas_recientes': ventas_recientes,
        'notificaciones': notificaciones,
        'citas_pendientes_hoy': citas_pendientes_hoy,
        'labels': labels,
        'data': data,
    })