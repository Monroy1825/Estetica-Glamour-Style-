from django.urls import path
from . import views_reportes

urlpatterns = [
    path('', views_reportes.reporte_ventas, name='reporte_ventas'),
    path('citas/', views_reportes.reporte_citas, name='reporte_citas'),
    path('stock/', views_reportes.reporte_stock, name='reporte_stock'),
    path('ventas/pdf/', views_reportes.reporte_ventas_pdf, name='reporte_ventas_pdf'),
    path('citas/pdf/', views_reportes.reporte_citas_pdf, name='reporte_citas_pdf'),
]
