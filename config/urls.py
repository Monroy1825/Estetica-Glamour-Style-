from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from .views import dashboard
from apps.operaciones import views as operaciones_views 

urlpatterns = [
    path('administ/', admin.site.urls),
    path('auth/', include('django.contrib.auth.urls')),
    path('clientes/', include('apps.clientes.urls')),
    path('empleados/', include('apps.empleados.urls')),
    path('servicios/', include('apps.servicios.urls')),
    path('operaciones/', include('apps.operaciones.urls')),
    

    path('proveedores/', operaciones_views.proveedor_list, name='proveedor_list'),

    path('', dashboard, name='dashboard'),
]