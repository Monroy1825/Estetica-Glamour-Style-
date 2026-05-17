from django.urls import path
from . import views

app_name = 'operaciones'

urlpatterns = [
    # CITAS
    path('citas/', views.cita_list, name='cita_list'),
    path('citas/nueva/', views.cita_create, name='cita_create'),
    path('citas/horarios-ocupados/', views.horarios_ocupados, name='horarios_ocupados'),
    path('citas/<int:pk>/', views.cita_detail, name='cita_detail'),
    path('citas/<int:pk>/editar/', views.cita_update, name='cita_update'),
    path('citas/<int:pk>/eliminar/', views.cita_delete, name='cita_delete'),
    path('citas/batch-delete/', views.cita_batch_delete, name='cita_batch_delete'),
    
    # VENTAS
    path('ventas/', views.venta_list, name='venta_list'),
    path('ventas/nueva/', views.venta_create, name='venta_create'),
    path('ventas/<int:pk>/', views.venta_detail, name='venta_detail'),
    path('ventas/<int:pk>/editar/', views.venta_update, name='venta_update'),
    path('ventas/<int:pk>/eliminar/', views.venta_delete, name='venta_delete'),
    path('ventas/<int:pk>/ticket/', views.venta_ticket, name='venta_ticket'),
    path('ventas/batch-delete/', views.venta_batch_delete, name='venta_batch_delete'),
    
    # COMPRAS
    path('compras/', views.compra_list, name='compra_list'),
    path('compras/nueva/', views.compra_create, name='compra_create'),
    path('compras/<int:pk>/', views.compra_detail, name='compra_detail'),
    path('compras/<int:pk>/editar/', views.compra_update, name='compra_update'),
    path('compras/<int:pk>/eliminar/', views.compra_delete, name='compra_delete'),
    
    # COTIZACIONES
    path('cotizaciones/', views.cotizacion_list, name='cotizacion_list'),
    path('cotizaciones/nueva/', views.cotizacion_create, name='cotizacion_create'),
    path('cotizaciones/<int:pk>/', views.cotizacion_detail, name='cotizacion_detail'),
    path('cotizaciones/<int:pk>/editar/', views.cotizacion_update, name='cotizacion_update'),
    path('cotizaciones/<int:pk>/eliminar/', views.cotizacion_delete, name='cotizacion_delete'),
    
    # PROVEEDORES
    path('proveedores/', views.proveedor_list, name='proveedor_list'),
    
    # PAGOS
    path('confirmar-pago/<int:cliente_id>/', views.confirmar_pago, name='confirmar_pago'),
    
    # REPORTES
    path('reportes/margenes/', views.reporte_margenes, name='reporte_margenes'),
    path('reportes/margenes-mejorado/', views.reporte_margenes_mejorado, name='reporte_margenes_mejorado'),
    
    # CRUD PRODUCTOS (NUEVOS)
    path('productos/', views.ProductoListView.as_view(), name='producto_list'),
    path('productos/crear/', views.ProductoCreateView.as_view(), name='producto_create'),
    path('productos/<int:pk>/editar/', views.ProductoUpdateView.as_view(), name='producto_update'),
    path('productos/<int:pk>/eliminar/', views.ProductoDeleteView.as_view(), name='producto_delete'),
    
    # CRUD SERVICIOS (NUEVOS)
    path('servicios/', views.ServicioListView.as_view(), name='servicio_list'),
    path('servicios/crear/', views.ServicioCreateView.as_view(), name='servicio_create'),
    path('servicios/<int:pk>/editar/', views.ServicioUpdateView.as_view(), name='servicio_update'),
    path('servicios/<int:pk>/eliminar/', views.ServicioDeleteView.as_view(), name='servicio_delete'),
    
    # VENTA DESDE CITA (NUEVO)
    path('citas/<int:cita_id>/crear-venta/', views.VentaFromCitaView.as_view(), name='venta_from_cita'),

    # Agrega al final del archivo
    path('citas/<int:pk>/cambiar-estado/', views.cita_cambiar_estado, name='cita_cambiar_estado'),
    path('citas/<int:pk>/reagendar/', views.cita_reagendar, name='cita_reagendar'),
]



