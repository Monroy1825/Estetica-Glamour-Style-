from django.urls import path
from . import views

app_name = 'servicios'

urlpatterns = [
    # Servicios
    path('', views.servicio_list, name='servicio_list'),
    path('nuevo/', views.servicio_create, name='servicio_create'),
    path('<int:pk>/', views.servicio_detail, name='servicio_detail'),
    path('<int:pk>/editar/', views.servicio_update, name='servicio_update'),
    path('<int:pk>/eliminar/', views.servicio_delete, name='servicio_delete'),
    # Productos
    path('productos/', views.producto_list, name='producto_list'),
    path('productos/nuevo/', views.producto_create, name='producto_create'),
    path('productos/<int:pk>/', views.producto_detail, name='producto_detail'),
    path('productos/<int:pk>/editar/', views.producto_update, name='producto_update'),
    path('productos/<int:pk>/eliminar/', views.producto_delete, name='producto_delete'),
    path('productos/<int:producto_id>/precio/', views.get_precio_producto, name='get_precio_producto'),
]
