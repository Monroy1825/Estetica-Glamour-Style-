from django.urls import path
from . import views

app_name = 'portal'

urlpatterns = [
    path('', views.portal_index, name='index'),
    path('agendar/', views.agendar_cita, name='agendar'),
    path('confirmacion/<int:pk>/', views.confirmacion, name='confirmacion'),
    path('consultar/', views.consultar_citas, name='consultar'),
]
