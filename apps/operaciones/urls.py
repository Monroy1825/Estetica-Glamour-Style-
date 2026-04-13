from django.urls import path
from . import views

app_name = 'operaciones'

urlpatterns = [
    # Citas
    path('citas/', views.cita_list, name='cita_list'),
    path('citas/nueva/', views.cita_create, name='cita_create'),
    path('citas/<int:pk>/', views.cita_detail, name='cita_detail'),
    path('citas/<int:pk>/editar/', views.cita_update, name='cita_update'),
    path('citas/<int:pk>/eliminar/', views.cita_delete, name='cita_delete'),
    # Ventas
    path('ventas/', views.venta_list, name='venta_list'),
    path('ventas/nueva/', views.venta_create, name='venta_create'),
    path('ventas/<int:pk>/', views.venta_detail, name='venta_detail'),
    path('ventas/<int:pk>/editar/', views.venta_update, name='venta_update'),
    path('ventas/<int:pk>/eliminar/', views.venta_delete, name='venta_delete'),
    # Compras
    path('compras/', views.compra_list, name='compra_list'),
    path('compras/nueva/', views.compra_create, name='compra_create'),
    path('compras/<int:pk>/', views.compra_detail, name='compra_detail'),
    path('compras/<int:pk>/editar/', views.compra_update, name='compra_update'),
    path('compras/<int:pk>/eliminar/', views.compra_delete, name='compra_delete'),
    # Cotizaciones
    path('cotizaciones/', views.cotizacion_list, name='cotizacion_list'),
    path('cotizaciones/nueva/', views.cotizacion_create, name='cotizacion_create'),
    path('cotizaciones/<int:pk>/', views.cotizacion_detail, name='cotizacion_detail'),
    path('cotizaciones/<int:pk>/editar/', views.cotizacion_update, name='cotizacion_update'),
    path('cotizaciones/<int:pk>/eliminar/', views.cotizacion_delete, name='cotizacion_delete'),
]
