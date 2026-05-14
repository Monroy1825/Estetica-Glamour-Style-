from django.shortcuts import render, redirect
from django.core.mail import send_mail
from datetime import datetime, timedelta
from .forms import CitaPublicaForm, ConsultaForm
from apps.clientes.models import Cliente
from apps.operaciones.models import Cita


def portal_index(request):
    return render(request, 'portal/index.html')


def agendar_cita(request):
    form = CitaPublicaForm()
    if request.method == 'POST':
        form = CitaPublicaForm(request.POST)
        if form.is_valid():
            nombre = form.cleaned_data['nombre'].title()
            telefono = form.cleaned_data['telefono']
            email = form.cleaned_data.get('email', '')
            servicio = form.cleaned_data['servicio']
            empleado = form.cleaned_data['empleado']
            fecha = form.cleaned_data['fecha']
            horario_str = form.cleaned_data['horario']

            fecha_str = fecha.strftime('%Y-%m-%d')
            fecha_inicio = datetime.strptime(f'{fecha_str} {horario_str}', '%Y-%m-%d %H:%M')
            fecha_fin = fecha_inicio + timedelta(hours=1)

            cliente, _ = Cliente.objects.get_or_create(
                telefono=telefono,
                defaults={'nombre': nombre, 'email': email or ''}
            )

            cita = Cita.objects.create(
                cliente=cliente,
                empleado=empleado,
                servicio=servicio,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                duracion_horas=1.0,
                estado='pendiente',
            )

            if email:
                send_mail(
                    subject='Confirmacion de cita - Glamour Style',
                    message=(
                        f'Hola {nombre},\n\n'
                        f'Tu cita ha sido registrada con exito.\n\n'
                        f'Servicio: {servicio.nombre}\n'
                        f'Estilista: {empleado.nombre}\n'
                        f'Fecha: {fecha_inicio.strftime("%d/%m/%Y a las %H:%M")}\n\n'
                        f'Te esperamos en Glamour Style.\n'
                    ),
                    from_email='noreply@glamourstyle.com',
                    recipient_list=[email],
                    fail_silently=True,
                )

            return redirect('portal:confirmacion', pk=cita.pk)

    return render(request, 'portal/agendar.html', {'form': form})


def confirmacion(request, pk):
    try:
        cita = Cita.objects.select_related('cliente', 'empleado', 'servicio').get(pk=pk)
    except Cita.DoesNotExist:
        return redirect('portal:index')
    return render(request, 'portal/confirmacion.html', {'cita': cita})


def consultar_citas(request):
    citas = None
    form = ConsultaForm()
    if request.method == 'POST':
        form = ConsultaForm(request.POST)
        if form.is_valid():
            telefono = form.cleaned_data['telefono']
            try:
                cliente = Cliente.objects.get(telefono=telefono, activo=True)
                citas = Cita.objects.filter(
                    cliente=cliente, activo=True
                ).select_related('servicio', 'empleado').order_by('-fecha_inicio')[:10]
            except Cliente.DoesNotExist:
                citas = []
    return render(request, 'portal/consultar.html', {'form': form, 'citas': citas})