from django.urls import path
from . import views

app_name = 'operaciones'

urlpatterns = [
    path('proveedores/', views.proveedor_list, name='proveedor_list'),
]