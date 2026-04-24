from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.timezone import now
from apps.clientes.models import Cliente
from apps.operaciones.models import Cita, Venta
from django.db.models.functions import TruncMonth
from django.db.models import Count

@login_required
def dashboard(request):
    hoy = now().date()
    mes_actual = now().month

    total_clientes = Cliente.objects.count()
    citas_hoy = Cita.objects.filter(fecha_inicio__date=hoy).count()
    ventas_mes = Venta.objects.filter(fecha__month=mes_actual).count()

    # DATOS PARA GRAFICA (ventas por mes)
    ventas_por_mes = (
        Venta.objects
        .annotate(mes=TruncMonth('fecha'))
        .values('mes')
        .annotate(total=Count('id'))
        .order_by('mes')
    )

    labels = [v['mes'].strftime('%b') for v in ventas_por_mes]
    data = [v['total'] for v in ventas_por_mes]

    return render(request, 'dashboard.html', {
        'total_clientes': total_clientes,
        'citas_hoy': citas_hoy,
        'ventas_mes': ventas_mes,
        'labels': labels,
        'data': data,
    })