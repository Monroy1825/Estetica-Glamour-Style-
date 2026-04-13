from django.urls import path
from . import views

app_name = 'empleados'

urlpatterns = [
    path('', views.empleado_list, name='list'),
    path('nuevo/', views.empleado_create, name='create'),
    path('<int:pk>/', views.empleado_detail, name='detail'),
    path('<int:pk>/editar/', views.empleado_update, name='update'),
    path('<int:pk>/eliminar/', views.empleado_delete, name='delete'),
]
