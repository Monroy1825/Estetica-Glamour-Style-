from apps.servicios.models import Producto
from apps.operaciones.models import Cita, Cotizacion
from django.utils.timezone import now


def notificaciones(request):
    if not request.user.is_authenticated:
        return {}

    lista = []
    hoy = now().date()

    for p in Producto.objects.filter(activo=True):
        if p.stock_actual <= p.stock_minimo:
            lista.append({
                'tipo': 'danger',
                'icono': '📦',
                'mensaje': f'{p.nombre} tiene stock bajo ({p.stock_actual} unidades)',
                'url': '/servicios/productos/'
            })

    citas = Cita.objects.filter(
        fecha_inicio__date=hoy,
        estado='pendiente',
        activo=True
    ).select_related('cliente')
    for c in citas:
        lista.append({
            'tipo': 'warning',
            'icono': '🗓️',
            'mensaje': f'Cita pendiente: {c.cliente} a las {c.fecha_inicio.strftime("%H:%M")}',
            'url': '/operaciones/citas/'
        })

    cotizaciones = Cotizacion.objects.filter(
        vigencia__lt=hoy,
        estado='vigente',
        activo=True
    ).select_related('cliente')
    for c in cotizaciones:
        lista.append({
            'tipo': 'info',
            'icono': '📋',
            'mensaje': f'Cotizacion de {c.cliente} esta vencida',
            'url': '/operaciones/cotizaciones/'
        })

    citas_pendientes_hoy = sum(1 for n in lista if n['tipo'] == 'warning')

    return {
        'notificaciones_lista': lista,
        'total_notificaciones': len(lista),
        'citas_pendientes_hoy': citas_pendientes_hoy,
    }
