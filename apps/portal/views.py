from django.shortcuts import render, redirect
from django.core.mail import send_mail
from datetime import datetime, timedelta
import random
from .forms import CitaPublicaForm, ConsultaCodigoForm, ConsultaTelefonoForm
from apps.clientes.models import Cliente
from apps.transacciones.models import Cita, CitaServicioAdicional
from apps.servicios.models import Servicio


def _generar_codigo():
    while True:
        codigo = f'GLM-{random.randint(1000, 9999)}'
        if not Cita.objects.filter(codigo_confirmacion=codigo).exists():
            return codigo


def portal_index(request):
    return render(request, 'portal/index.html')


def agendar_cita(request):
    import json
    error_servicios = ''

    if request.method == 'POST':
        form = CitaPublicaForm(request.POST)
        servicios_data_raw = request.POST.get('servicios_data', '[]')

        try:
            servicios_data = json.loads(servicios_data_raw)
        except (ValueError, TypeError):
            servicios_data = []

        if not servicios_data:
            error_servicios = 'Selecciona al menos un servicio con fecha y horario.'

        if form.is_valid() and not error_servicios:
            nombre = form.cleaned_data['nombre'].title()
            telefono = form.cleaned_data['telefono']
            email = form.cleaned_data.get('email', '')
            empleado = form.cleaned_data['empleado']

            cliente, _ = Cliente.objects.get_or_create(
                telefono=telefono,
                defaults={'nombre': nombre, 'email': email or ''}
            )

            codigo = _generar_codigo()
            citas_creadas = []

            for item in servicios_data:
                try:
                    servicio = Servicio.objects.get(id=item['id'], activo=True)
                    fecha_inicio = datetime.strptime(f"{item['fecha']} {item['horario']}", '%Y-%m-%d %H:%M')
                    fecha_fin = fecha_inicio + timedelta(minutes=servicio.duracion_minutos)
                    cita = Cita.objects.create(
                        cliente=cliente,
                        empleado=empleado,
                        servicio=servicio,
                        fecha_inicio=fecha_inicio,
                        fecha_fin=fecha_fin,
                        duracion_horas=round(servicio.duracion_minutos / 60, 2),
                        estado='pendiente',
                        codigo_confirmacion=codigo,
                    )
                    citas_creadas.append(cita)
                except (Servicio.DoesNotExist, KeyError, ValueError):
                    continue

            if citas_creadas and email:
                lineas = '\n'.join(
                    f"  - {c.servicio.nombre}: {c.fecha_inicio.strftime('%d/%m/%Y a las %H:%M')}"
                    for c in citas_creadas
                )
                send_mail(
                    subject='Confirmacion de cita - Glamour Style',
                    message=(
                        f'Hola {nombre},\n\n'
                        f'Tu(s) cita(s) han sido registradas con exito.\n\n'
                        f'{lineas}\n\n'
                        f'Estilista: {empleado.nombre}\n\n'
                        f'Tu codigo de confirmacion es: {codigo}\n'
                        f'Guardalo para consultar tus citas en cualquier momento.\n\n'
                        f'Te esperamos en Glamour Style.\n'
                    ),
                    from_email='noreply@glamourstyle.com',
                    recipient_list=[email],
                    fail_silently=True,
                )

            if citas_creadas:
                return redirect('portal:confirmacion', pk=citas_creadas[0].pk)
    else:
        form = CitaPublicaForm()
        servicios_data_raw = '[]'

    import json as _json
    from apps.empleados.models import Empleado
    servicios = Servicio.objects.filter(activo=True).order_by('nombre')
    empleados = Empleado.objects.filter(activo=True).order_by('nombre')
    empleados_json = _json.dumps([
        {'id': e.id, 'nombre': e.nombre, 'dias_descanso': e.dias_descanso or ''}
        for e in empleados
    ])
    return render(request, 'portal/agendar.html', {
        'form': form,
        'servicios': servicios,
        'empleados': empleados,
        'empleados_json': empleados_json,
        'error_servicios': error_servicios,
        'servicios_data_raw': servicios_data_raw if request.method == 'POST' else '[]',
    })


def confirmacion(request, pk):
    try:
        cita = Cita.objects.select_related('cliente', 'empleado', 'servicio').get(pk=pk)
    except Cita.DoesNotExist:
        return redirect('portal:index')
    todas_citas = Cita.objects.filter(
        codigo_confirmacion=cita.codigo_confirmacion
    ).select_related('servicio').order_by('fecha_inicio')
    return render(request, 'portal/confirmacion.html', {'cita': cita, 'todas_citas': todas_citas})


def consultar_citas(request):
    cita = None
    citas_por_telefono = None
    not_found = False
    modo = request.POST.get('modo', 'codigo')
    form_codigo = ConsultaCodigoForm()
    form_telefono = ConsultaTelefonoForm()

    if request.method == 'POST':
        if modo == 'telefono':
            form_telefono = ConsultaTelefonoForm(request.POST)
            if form_telefono.is_valid():
                telefono = form_telefono.cleaned_data['telefono'].strip()
                clientes = Cliente.objects.filter(telefono=telefono, activo=True)
                if clientes.exists():
                    citas_por_telefono = Cita.objects.filter(
                        cliente__in=clientes, activo=True
                    ).select_related('servicio', 'empleado', 'cliente').order_by('-fecha_inicio')
                    if not citas_por_telefono.exists():
                        not_found = True
                        citas_por_telefono = None
                else:
                    not_found = True
        else:
            form_codigo = ConsultaCodigoForm(request.POST)
            if form_codigo.is_valid():
                codigo = form_codigo.cleaned_data['codigo'].strip().upper()
                todas = Cita.objects.filter(
                    codigo_confirmacion=codigo, activo=True
                ).select_related('cliente', 'servicio', 'empleado').order_by('fecha_inicio')
                if todas.exists():
                    cita = todas.first()
                    citas_por_telefono = todas
                else:
                    not_found = True

    return render(request, 'portal/consultar.html', {
        'form_codigo': form_codigo,
        'form_telefono': form_telefono,
        'cita': cita,
        'citas_por_telefono': citas_por_telefono,
        'not_found': not_found,
        'modo': modo,
    })
