from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from datetime import datetime
import json


from .models import Cita, Venta, Compra, Cotizacion, VentaCabecera, VentaDetalle
from apps.servicios.models import Producto, Servicio
from .forms import CitaForm, CompraForm, CotizacionForm


def _paginate(queryset, request):
    paginator = Paginator(queryset, 10)
    page = request.GET.get('page')
    try:
        return paginator.page(page)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)


# ========== CITAS ==========

@login_required
def horarios_ocupados(request):
    empleado_id = request.GET.get('empleado')
    fecha = request.GET.get('fecha')
    cita_id = request.GET.get('cita_id')

    if not empleado_id or not fecha:
        return JsonResponse({'ocupados': []})

    try:
        fecha_dt = datetime.strptime(fecha, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'ocupados': []})

    citas = Cita.objects.filter(
        empleado_id=empleado_id,
        fecha_inicio__date=fecha_dt,
        activo=True,
        estado__in=['pendiente', 'confirmada'],
    )

    if cita_id:
        citas = citas.exclude(pk=cita_id)

    ocupados = [
        {
            'inicio': timezone.localtime(c.fecha_inicio).strftime('%H:%M'),
            'fin':    timezone.localtime(c.fecha_fin).strftime('%H:%M'),
        }
        for c in citas
    ]
    return JsonResponse({'ocupados': ocupados})

@login_required
def cita_list(request):
    from apps.empleados.models import Empleado
    from apps.clientes.models import Cliente
    
    empleados_con_citas = []
    empleados = Empleado.objects.filter(activo=True)
    todos_empleados = empleados  # Para el modal de reagendar
    
    for empleado in empleados:
        citas_empleado = Cita.objects.filter(
            activo=True,
            empleado=empleado
        ).select_related('cliente', 'servicio').prefetch_related(
            'servicios_adicionales__servicio'
        ).order_by('-fecha_inicio')
        
        if citas_empleado.exists():
            clientes = Cliente.objects.filter(
                citas__empleado=empleado,
                citas__activo=True
            ).distinct()
            
            empleados_con_citas.append({
                'empleado': empleado,
                'citas': citas_empleado,
                'clientes': clientes,
                'total_citas': citas_empleado.count()
            })
    
    return render(request, 'operaciones/cita_list.html', {
        'empleados_con_citas': empleados_con_citas,
        'empleados': todos_empleados,
    })

@login_required
def cita_create(request):
    from apps.servicios.models import Servicio as ServicioModel
    from .models import CitaServicioAdicional
    servicios = ServicioModel.objects.filter(activo=True)

    if request.method == 'POST':
        form = CitaForm(request.POST)
        if form.is_valid():
            empleado_id = form.cleaned_data['empleado'].id
            fecha_inicio = form.cleaned_data['fecha_inicio']
            fecha_fin = form.cleaned_data['fecha_fin']

            citas_conflicto = Cita.objects.filter(
                empleado_id=empleado_id,
                activo=True,
            ).filter(
                Q(fecha_inicio__lt=fecha_fin) & Q(fecha_fin__gt=fecha_inicio)
            )

            if citas_conflicto.exists():
                messages.error(request, 'El empleado ya tiene una cita en ese horario.')
                return render(request, 'operaciones/cita_form.html', {
                    'titulo': 'Nueva Cita',
                    'form': form,
                    'servicios': servicios,
                })

            cita = form.save(commit=False)
            cita.fecha_inicio = fecha_inicio
            cita.fecha_fin = fecha_fin
            cita.save()

            servicios_json = request.POST.get('servicios_adicionales_json', '[]')
            try:
                servicios_data = json.loads(servicios_json)
                for s in servicios_data:
                    CitaServicioAdicional.objects.create(
                        cita=cita,
                        servicio_id=s['id'],
                    )
            except (json.JSONDecodeError, KeyError):
                pass

            # Recalcular duracion y fecha_fin sumando todos los servicios
            from datetime import timedelta
            total_minutos = cita.servicio.duracion_minutos
            for sa in cita.servicios_adicionales.all():
                total_minutos += sa.servicio.duracion_minutos
            cita.duracion_horas = round(total_minutos / 60, 1)
            cita.fecha_fin = cita.fecha_inicio + timedelta(minutes=total_minutos)
            cita.save()

            messages.success(request, '¡La cita se ha creado exitosamente!')
            return redirect('operaciones:cita_list')
    else:
        initial = {}
        cliente_id = request.GET.get('cliente')
        empleado_id = request.GET.get('empleado')
        if cliente_id:
            initial['cliente'] = cliente_id
        if empleado_id:
            initial['empleado'] = empleado_id
        form = CitaForm(initial=initial)

    return render(request, 'operaciones/cita_form.html', {
        'titulo': 'Nueva Cita',
        'form': form,
        'horarios_ocupados': _get_horarios_ocupados(),
        'cliente_id': request.GET.get('cliente'),
        'servicios': servicios,
    })

def _get_horarios_ocupados():
    citas = Cita.objects.filter(activo=True).values('empleado_id', 'fecha_inicio')
    ocupados = {}
    for c in citas:
        emp_id = str(c['empleado_id'])
        fecha = c['fecha_inicio'].strftime('%Y-%m-%d')
        hora = c['fecha_inicio'].strftime('%H:%M')
        clave = f"{emp_id}_{fecha}"
        if clave not in ocupados:
            ocupados[clave] = []
        ocupados[clave].append(hora)
    return json.dumps(ocupados)

@login_required
def cita_detail(request, pk):
    cita = get_object_or_404(
        Cita.objects.select_related('cliente', 'empleado', 'servicio').prefetch_related('servicios_adicionales__servicio'),
        pk=pk
    )
    return render(request, 'operaciones/cita_detail.html', {'cita': cita})

@login_required
def cita_update(request, pk):
    from apps.servicios.models import Servicio as ServicioModel
    from .models import CitaServicioAdicional
    cita = get_object_or_404(Cita, pk=pk)
    estado_anterior = cita.estado
    tiene_venta = VentaCabecera.objects.filter(detalles__cita=cita, activo=True).exists()
    servicios = ServicioModel.objects.filter(activo=True)

    servicios_actuales = list(cita.servicios_adicionales.filter(activo=True).values('servicio_id', 'servicio__nombre', 'servicio__precio_base'))
    servicios_actuales_json = json.dumps([
        {'id': str(s['servicio_id']), 'nombre': s['servicio__nombre'], 'precio': str(s['servicio__precio_base'])}
        for s in servicios_actuales
    ])

    if request.method == 'POST':
        form = CitaForm(request.POST, instance=cita)
        if form.is_valid():
            cita = form.save(commit=False)
            nuevo_estado = form.cleaned_data.get('estado')

            if nuevo_estado == 'completada' and estado_anterior != 'completada':
                venta_existente = VentaCabecera.objects.filter(detalles__cita=cita, activo=True).exists()
                if not venta_existente:
                    _crear_venta_desde_cita(cita)
                    messages.success(request, '¡Cita actualizada y venta generada automáticamente!')
            
            cita.save()

            # Actualizar servicios adicionales
            servicios_json = request.POST.get('servicios_adicionales_json', '[]')
            try:
                servicios_data = json.loads(servicios_json)
                cita.servicios_adicionales.all().delete()
                for s in servicios_data:
                    CitaServicioAdicional.objects.create(
                        cita=cita,
                        servicio_id=s['id'],
                    )
            except (json.JSONDecodeError, KeyError):
                pass

            # Recalcular duracion y fecha_fin sumando todos los servicios
            from datetime import timedelta
            total_minutos = cita.servicio.duracion_minutos
            for sa in cita.servicios_adicionales.all():
                total_minutos += sa.servicio.duracion_minutos
            cita.duracion_horas = round(total_minutos / 60, 1)
            cita.fecha_fin = cita.fecha_inicio + timedelta(minutes=total_minutos)
            cita.save()

            messages.success(request, '¡Cita actualizada correctamente!')
            return redirect('operaciones:cita_list')
    else:
        form = CitaForm(instance=cita)

    return render(request, 'operaciones/cita_form.html', {
        'titulo': 'Editar Cita',
        'form': form,
        'cita_id': cita.pk,
        'tiene_venta': tiene_venta,
        'servicios': servicios,
        'servicios_actuales': servicios_actuales,
        'servicios_actuales_json': servicios_actuales_json,
    })

@login_required
def cita_delete(request, pk):
    cita = get_object_or_404(Cita, pk=pk)
    if request.method == 'POST':
        cita.activo = False
        cita.save()
        messages.success(request, 'La cita ha sido eliminada.')
        return redirect('operaciones:cita_list')
    return render(request, 'operaciones/cita_confirm_delete.html', {'cita': cita})


def _crear_venta_desde_cita(cita, metodo_pago='efectivo'):
    precio_base = float(cita.servicio.precio_base)
    total = precio_base

    cabecera = VentaCabecera.objects.create(
        cliente=cita.cliente,
        empleado=cita.empleado,
        metodo_pago=metodo_pago,
        estatus='pagada',
        subtotal=0,
        total=0,
        activo=True,
    )
    VentaDetalle.objects.create(
        venta=cabecera,
        tipo='servicio',
        servicio=cita.servicio,
        cita=cita,
        descripcion=cita.servicio.nombre,
        cantidad=1,
        precio_unitario=precio_base,
        subtotal=precio_base,
        activo=True,
    )
    for extra in cita.servicios_adicionales.filter(activo=True):
        precio_extra = float(extra.servicio.precio_base)
        VentaDetalle.objects.create(
            venta=cabecera,
            tipo='servicio',
            servicio=extra.servicio,
            cita=cita,
            descripcion=f'+ {extra.servicio.nombre}',
            cantidad=1,
            precio_unitario=precio_extra,
            subtotal=precio_extra,
            activo=True,
        )
        total += precio_extra

    cabecera.subtotal = total
    cabecera.total = total
    cabecera.save()
    return cabecera


# ========== VENTAS ==========

@login_required
def venta_list(request):
    qs = VentaCabecera.objects.filter(activo=True).select_related('cliente', 'empleado').prefetch_related('detalles')

    total_ventas = qs.count()
    total_ingresos = qs.aggregate(total=Sum('total'))['total'] or 0
    ventas_pagadas = qs.filter(estatus='pagada').count()
    ventas_pendientes = qs.filter(estatus='pendiente').count()

    paginator = Paginator(qs, 10)
    page = request.GET.get('page')
    try:
        ventas = paginator.page(page)
    except PageNotAnInteger:
        ventas = paginator.page(1)
    except EmptyPage:
        ventas = paginator.page(paginator.num_pages)

    return render(request, 'operaciones/venta_list.html', {
        'ventas': ventas,
        'total_ventas': total_ventas,
        'total_ingresos': total_ingresos,
        'ventas_pagadas': ventas_pagadas,
        'ventas_pendientes': ventas_pendientes,
    })

@login_required
def venta_create(request):
    from apps.clientes.models import Cliente
    from apps.empleados.models import Empleado
    from apps.servicios.models import Producto
    
    citas_disponibles = Cita.objects.filter(
        activo=True, 
        estado__in=['confirmada', 'pendiente']
    ).select_related('cliente', 'empleado', 'servicio').order_by('-fecha_inicio')
    
    clientes = Cliente.objects.filter(activo=True)
    empleados = Empleado.objects.filter(activo=True)
    productos = Producto.objects.filter(activo=True, stock_actual__gt=0)
    
    if request.method == 'POST':
        cliente_id = request.POST.get('cliente') or request.POST.get('cliente_producto')
        empleado_id = request.POST.get('empleado') or request.POST.get('empleado_producto') or request.POST.get('empleado_directa')
        cita_id = request.POST.get('cita')
        metodo_pago = request.POST.get('metodo_pago')
        productos_json = request.POST.get('productos_json', '[]')
        tipo_venta = request.POST.get('tipo_venta', 'cita')
        
        productos_data = json.loads(productos_json) if productos_json else []
        
        # Crear cliente para venta directa
        if tipo_venta == 'directa':
            nombre_nuevo = request.POST.get('cliente_nuevo_nombre', '').strip().upper()
            telefono_nuevo = request.POST.get('cliente_nuevo_telefono', '')
            email_nuevo = request.POST.get('cliente_nuevo_email', '')
            
            if nombre_nuevo:
                # Buscar si ya existe un cliente con ese nombre
                cliente, created = Cliente.objects.get_or_create(
                    nombre=nombre_nuevo,
                    defaults={
                        'telefono': telefono_nuevo or '0000000000',
                        'email': email_nuevo,
                        'tipo_cliente': 'venta_rapida',
                        'activo': True
                    }
                )
                cliente_id = cliente.id
            else:
                messages.error(request, 'Debe ingresar el nombre del cliente')
                return render(request, 'operaciones/venta_form.html', {
                    'titulo': 'Nueva Venta',
                    'citas_disponibles': citas_disponibles,
                    'clientes': clientes,
                    'empleados': empleados,
                    'productos': productos,
                })
        else:
            if not cliente_id:
                messages.error(request, 'Debe seleccionar una cita')
                return render(request, 'operaciones/venta_form.html', {
                    'titulo': 'Nueva Venta',
                    'citas_disponibles': citas_disponibles,
                    'clientes': clientes,
                    'empleados': empleados,
                    'productos': productos,
                })
            cliente = get_object_or_404(Cliente, pk=cliente_id)
        
        empleado = get_object_or_404(Empleado, pk=empleado_id)
        cita = None
        if cita_id:
            cita = get_object_or_404(Cita, pk=cita_id)
        
        cabecera = VentaCabecera.objects.create(
            cliente=cliente,
            empleado=empleado,
            metodo_pago=metodo_pago,
            estatus='pendiente',
            subtotal=0,
            total=0,
            activo=True,
        )
        total = 0

        # Detalle del servicio de cita
        if cita:
            precio_servicio = float(cita.servicio.precio_base)
            VentaDetalle.objects.create(
                venta=cabecera,
                tipo='servicio',
                servicio=cita.servicio,
                cita=cita,
                descripcion=cita.servicio.nombre,
                cantidad=1,
                precio_unitario=precio_servicio,
                subtotal=precio_servicio,
                activo=True,
            )
            total += precio_servicio

            for extra in cita.servicios_adicionales.filter(activo=True):
                precio_extra = float(extra.servicio.precio_base)
                VentaDetalle.objects.create(
                    venta=cabecera,
                    tipo='servicio',
                    servicio=extra.servicio,
                    cita=cita,
                    descripcion=f'+ {extra.servicio.nombre}',
                    cantidad=1,
                    precio_unitario=precio_extra,
                    subtotal=precio_extra,
                    activo=True,
                )
                total += precio_extra

        # Detalle de cada producto
        for prod_data in productos_data:
            producto = get_object_or_404(Producto, pk=prod_data['id'])
            cantidad = prod_data['cantidad']
            if producto.stock_actual >= cantidad:
                precio_prod = float(producto.precio_venta)
                VentaDetalle.objects.create(
                    venta=cabecera,
                    tipo='producto',
                    producto=producto,
                    descripcion=producto.nombre,
                    cantidad=cantidad,
                    precio_unitario=precio_prod,
                    precio_costo_unitario=float(producto.costo),
                    subtotal=precio_prod * cantidad,
                    activo=True,
                )
                total += precio_prod * cantidad
                producto.stock_actual -= cantidad
                producto.save()

        cabecera.subtotal = total
        cabecera.total = total
        cabecera.save()

        messages.success(request, '¡Venta registrada con exito!')
        return redirect('operaciones:venta_ticket', pk=cabecera.pk)
    
    return render(request, 'operaciones/venta_form.html', {
        'titulo': 'Nueva Venta',
        'citas_disponibles': citas_disponibles,
        'clientes': clientes,
        'empleados': empleados,
        'productos': productos,
    })

@login_required
def venta_ticket(request, pk):
    cabecera = get_object_or_404(
        VentaCabecera.objects.select_related('cliente', 'empleado').prefetch_related(
            'detalles__servicio', 'detalles__producto', 'detalles__cita'
        ),
        pk=pk
    )
    detalles = cabecera.detalles.filter(activo=True)
    es_comprobante = request.GET.get('pagado') == '1'
    hay_pendientes = cabecera.estatus == 'pendiente'

    return render(request, 'operaciones/venta_ticket.html', {
        'cabecera': cabecera,
        'detalles': detalles,
        'total': cabecera.total,
        'cliente': cabecera.cliente,
        'hay_pendientes': hay_pendientes,
        'es_comprobante': es_comprobante,
    })

@login_required
def venta_update(request, pk):
    cabecera = get_object_or_404(VentaCabecera, pk=pk)
    if request.method == 'POST':
        metodo_pago = request.POST.get('metodo_pago', cabecera.metodo_pago)
        estatus = request.POST.get('estatus', cabecera.estatus)
        cabecera.metodo_pago = metodo_pago
        cabecera.estatus = estatus
        cabecera.save()
        messages.success(request, 'Venta actualizada.')
        return redirect('operaciones:venta_list')
    return render(request, 'operaciones/venta_update.html', {
        'cabecera': cabecera,
        'metodo_opciones': VentaCabecera.METODO_PAGO_CHOICES,
        'estatus_opciones': VentaCabecera.ESTATUS_CHOICES,
    })

@login_required
def venta_delete(request, pk):
    cabecera = get_object_or_404(VentaCabecera, pk=pk)
    if request.method == 'POST':
        cabecera.activo = False
        cabecera.save()
        messages.success(request, 'Venta eliminada.')
        return redirect('operaciones:venta_list')
    return render(request, 'operaciones/venta_confirm_delete.html', {'venta': cabecera})


# ========== COMPRAS ==========

@login_required
def compra_list(request):
    qs = Compra.objects.filter(activo=True).select_related('empleado', 'producto')
    
    total_compras = qs.count()
    total_inversion = 0
    for c in qs:
        total_inversion += float(c.precio_unitario) * c.cantidad
    proveedores_distintos = qs.values('proveedor').distinct().count()
    total_productos = qs.values('producto').distinct().count()
    
    paginator = Paginator(qs, 10)
    page = request.GET.get('page')
    try:
        compras = paginator.page(page)
    except PageNotAnInteger:
        compras = paginator.page(1)
    except EmptyPage:
        compras = paginator.page(paginator.num_pages)
    
    return render(request, 'operaciones/compra_list.html', {
        'compras': compras,
        'total_compras': total_compras,
        'total_inversion': total_inversion,
        'proveedores_distintos': proveedores_distintos,
        'total_productos': total_productos,
    })

@login_required
def compra_create(request):
    if request.method == 'POST':
        form = CompraForm(request.POST)
        if form.is_valid():
            producto = form.cleaned_data['producto']
            cantidad = form.cleaned_data['cantidad']
            precio_unitario = form.cleaned_data['precio_unitario']
            compra = form.save()
            
            # Actualizar stock
            producto.stock_actual += cantidad
            
            # Actualizar precio de compra (promedio)
            nuevo_total_compra = (producto.precio_compra * (producto.stock_actual - cantidad) + precio_unitario * cantidad) / producto.stock_actual
            producto.precio_compra = round(nuevo_total_compra, 2)
            
            # Actualizar precio de venta si se solicitó
            nuevo_precio_venta = request.POST.get('nuevo_precio_venta')
            if nuevo_precio_venta:
                producto.precio_venta = float(nuevo_precio_venta)
            
            producto.save()
            
            messages.success(request, f'¡Compra registrada! Stock actual: {producto.stock_actual} unidades')
            return redirect('operaciones:compra_list')
    else:
        form = CompraForm()
    
    return render(request, 'operaciones/compra_form.html', {'titulo': 'Nueva Compra', 'form': form})
@login_required
def compra_detail(request, pk):
    compra = get_object_or_404(Compra.objects.select_related('empleado', 'producto'), pk=pk)
    return render(request, 'operaciones/compra_detail.html', {'compra': compra})

@login_required
def compra_update(request, pk):
    compra = get_object_or_404(Compra, pk=pk)
    if request.method == 'POST':
        form = CompraForm(request.POST, instance=compra)
        if form.is_valid():
            form.save()
            messages.success(request, 'Compra actualizada.')
            return redirect('operaciones:compra_list')
    else:
        form = CompraForm(instance=compra)
    return render(request, 'operaciones/compra_form.html', {'titulo': 'Editar Compra', 'form': form})

@login_required
def compra_delete(request, pk):
    compra = get_object_or_404(Compra, pk=pk)
    if request.method == 'POST':
        compra.activo = False
        compra.save()
        messages.success(request, 'Compra eliminada.')
        return redirect('operaciones:compra_list')
    return render(request, 'operaciones/compra_confirm_delete.html', {'compra': compra})


# ========== COTIZACIONES ==========

@login_required
def cotizacion_list(request):
    qs = Cotizacion.objects.filter(activo=True).select_related('cliente', 'servicio', 'producto')
    return render(request, 'operaciones/cotizacion_list.html', {'cotizaciones': _paginate(qs, request)})

@login_required
def cotizacion_create(request):
    if request.method == 'POST':
        form = CotizacionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Cotización generada!')
            return redirect('operaciones:cotizacion_list')
    else:
        form = CotizacionForm()
    return render(request, 'operaciones/cotizacion_form.html', {'titulo': 'Nueva Cotización', 'form': form})

@login_required
def cotizacion_detail(request, pk):
    cotizacion = get_object_or_404(
        Cotizacion.objects.select_related('cliente', 'servicio', 'producto'), pk=pk
    )
    return render(request, 'operaciones/cotizacion_detail.html', {'cotizacion': cotizacion})

@login_required
def cotizacion_update(request, pk):
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    if request.method == 'POST':
        form = CotizacionForm(request.POST, instance=cotizacion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cotización actualizada.')
            return redirect('operaciones:cotizacion_list')
    else:
        form = CotizacionForm(instance=cotizacion)
    return render(request, 'operaciones/cotizacion_form.html', {
        'titulo': 'Editar Cotización', 'form': form
    })

@login_required
def cotizacion_delete(request, pk):
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    if request.method == 'POST':
        cotizacion.activo = False
        cotizacion.save()
        messages.success(request, 'Cotización eliminada.')
        return redirect('operaciones:cotizacion_list')
    return render(request, 'operaciones/cotizacion_confirm_delete.html', {'cotizacion': cotizacion})


# ========== PROVEEDORES ==========

@login_required
def proveedor_list(request):
    proveedores = Compra.objects.values('proveedor').annotate(
        total_compras=Count('id'),
        inversion_total=Sum('precio_unitario')
    ).order_by('-inversion_total')
    return render(request, 'operaciones/proveedor_list.html', {'proveedores': proveedores})


# ========== CONFIRMAR PAGO ==========

@login_required
def confirmar_pago(request, cliente_id=None, pk=None):
    venta_pk = pk or cliente_id
    if request.method == 'POST':
        cabecera = get_object_or_404(VentaCabecera, pk=venta_pk, activo=True)
        cabecera.estatus = 'pagada'
        cabecera.save()
        messages.success(request, f'Pago confirmado. Total: ${cabecera.total}')
        return redirect(f'/operaciones/ventas/{cabecera.pk}/ticket/?pagado=1')

    return redirect('operaciones:venta_list')



# ========== ELIMINACIÓN MASIVA ==========

from django.views.decorators.http import require_POST

@login_required
@require_POST
def cita_batch_delete(request):
    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
        
        if not ids:
            return JsonResponse({'success': False, 'error': 'No se seleccionaron citas'})
        
        citas_eliminadas = Cita.objects.filter(pk__in=ids, activo=True).update(activo=False)
        
        return JsonResponse({
            'success': True,
            'eliminadas': citas_eliminadas,
            'mensaje': f'Se eliminaron {citas_eliminadas} cita(s) correctamente'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def venta_batch_delete(request):
    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])

        if not ids:
            return JsonResponse({'success': False, 'error': 'No se seleccionaron ventas'})

        eliminadas = VentaCabecera.objects.filter(pk__in=ids, activo=True).update(activo=False)

        return JsonResponse({
            'success': True,
            'eliminadas': eliminadas,
            'mensaje': f'Se eliminaron {eliminadas} venta(s) correctamente'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ========== REPORTE DE MÁRGENES BÁSICO ==========

@login_required
def reporte_margenes(request):
    from django.db.models import Sum
    
    ventas_productos = Venta.objects.filter(
        activo=True,
        producto__isnull=False,
        estatus='pagada'
    ).select_related('producto', 'cliente')
    
    productos_margen = []
    for venta in ventas_productos:
        margen = venta.margen_ganancia
        porcentaje = venta.porcentaje_ganancia
        
        productos_margen.append({
            'producto': venta.producto.nombre,
            'precio_venta': venta.total,
            'costo': float(venta.producto.costo),
            'margen': margen,
            'porcentaje': porcentaje,
            'fecha': venta.fecha,
            'cliente': venta.cliente.nombre,
            'cantidad': 1
        })
    
    productos_margen.sort(key=lambda x: x['margen'], reverse=True)
    
    total_ventas = ventas_productos.count()
    margen_total = sum(p['margen'] for p in productos_margen)
    promedio_margen = margen_total / total_ventas if total_ventas > 0 else 0
    
    return render(request, 'operaciones/reporte_margenes.html', {
        'productos_margen': productos_margen,
        'total_ventas': total_ventas,
        'margen_total': margen_total,
        'promedio_margen': promedio_margen,
    })


# ========== CRUD PRODUCTOS (VISTAS CLASE) ==========

class ProductoListView(ListView):
    model = Producto
    template_name = 'operaciones/producto_list.html'
    context_object_name = 'productos'
    paginate_by = 10

    def get_queryset(self):
        queryset = Producto.objects.filter(activo=True)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(nombre__icontains=search)
        return queryset

class ProductoCreateView(CreateView):
    model = Producto
    template_name = 'operaciones/producto_form.html'
    fields = ['nombre', 'descripcion', 'precio_venta', 'costo', 'stock_actual', 'stock_minimo']
    success_url = reverse_lazy('operaciones:producto_list')

    def form_valid(self, form):
        messages.success(self.request, 'Producto creado exitosamente')
        return super().form_valid(form)

class ProductoUpdateView(UpdateView):
    model = Producto
    template_name = 'operaciones/producto_form.html'
    fields = ['nombre', 'descripcion', 'precio_venta', 'costo', 'stock_actual', 'stock_minimo']
    success_url = reverse_lazy('operaciones:producto_list')

    def form_valid(self, form):
        messages.success(self.request, 'Producto actualizado exitosamente')
        return super().form_valid(form)

class ProductoDeleteView(DeleteView):
    model = Producto
    template_name = 'operaciones/producto_confirm_delete.html'
    success_url = reverse_lazy('operaciones:producto_list')

    def delete(self, request, *args, **kwargs):
        producto = self.get_object()
        producto.activo = False
        producto.save()
        messages.success(request, 'Producto eliminado exitosamente')
        return redirect(self.success_url)


# ========== CRUD SERVICIOS (VISTAS CLASE) ==========

class ServicioListView(ListView):
    model = Servicio
    template_name = 'operaciones/servicio_list.html'
    context_object_name = 'servicios'
    paginate_by = 10

    def get_queryset(self):
        queryset = Servicio.objects.filter(activo=True)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(nombre__icontains=search)
        return queryset

class ServicioCreateView(CreateView):
    model = Servicio
    template_name = 'operaciones/servicio_form.html'
    fields = ['nombre', 'descripcion', 'precio_base', 'precio_costo', 'duracion_minutos']
    success_url = reverse_lazy('operaciones:servicio_list')

    def form_valid(self, form):
        messages.success(self.request, 'Servicio creado exitosamente')
        return super().form_valid(form)

class ServicioUpdateView(UpdateView):
    model = Servicio
    template_name = 'operaciones/servicio_form.html'
    fields = ['nombre', 'descripcion', 'precio_base', 'precio_costo', 'duracion_minutos']
    success_url = reverse_lazy('operaciones:servicio_list')

    def form_valid(self, form):
        messages.success(self.request, 'Servicio actualizado exitosamente')
        return super().form_valid(form)

class ServicioDeleteView(DeleteView):
    model = Servicio
    template_name = 'operaciones/servicio_confirm_delete.html'
    success_url = reverse_lazy('operaciones:servicio_list')

    def delete(self, request, *args, **kwargs):
        servicio = self.get_object()
        servicio.activo = False
        servicio.save()
        messages.success(request, 'Servicio eliminado exitosamente')
        return redirect(self.success_url)



# ========== REPORTE DE MÁRGENES MEJORADO ==========

@login_required
def reporte_margenes_mejorado(request):
    """Reporte mejorado con márgenes de ganancia para productos y servicios"""
    from django.db.models import Sum
    
    # Reporte de productos
    productos_data = []
    productos = Producto.objects.filter(activo=True)
    for producto in productos:
        ventas = Venta.objects.filter(producto=producto, estatus='pagada', activo=True)
        cantidad_vendida = ventas.count()
        total_ventas = ventas.aggregate(total=Sum('total'))['total'] or 0
        
        if producto.precio_costo > 0:
            margen_porcentaje = ((producto.precio_venta - producto.precio_costo) / producto.precio_costo) * 100
        else:
            margen_porcentaje = 0
        
        productos_data.append({
            'nombre': producto.nombre,
            'precio_venta': float(producto.precio_venta),
            'precio_costo': float(producto.precio_costo),
            'margen_neto': float(producto.precio_venta - producto.precio_costo),
            'margen_porcentaje': margen_porcentaje,
            'cantidad_vendida': cantidad_vendida,
            'total_ventas': float(total_ventas),
            'stock_actual': producto.stock_actual,
        })
    
    # Reporte de servicios
    servicios_data = []
    servicios = Servicio.objects.filter(activo=True)
    for servicio in servicios:
        citas = Cita.objects.filter(servicio=servicio, estado='completada')
        cantidad_realizada = citas.count()
        
        if servicio.precio_costo > 0:
            margen_porcentaje = ((servicio.precio_base - servicio.precio_costo) / servicio.precio_costo) * 100
        else:
            margen_porcentaje = 0

        servicios_data.append({
            'nombre': servicio.nombre,
            'precio_venta': float(servicio.precio_base),
            'precio_costo': float(servicio.precio_costo),
            'margen_neto': float(servicio.precio_base - servicio.precio_costo),
            'margen_porcentaje': margen_porcentaje,
            'cantidad_realizada': cantidad_realizada,
            'duracion': servicio.duracion_minutos,
        })
    
    # Ordenar por margen porcentual
    productos_data.sort(key=lambda x: x['margen_porcentaje'], reverse=True)
    servicios_data.sort(key=lambda x: x['margen_porcentaje'], reverse=True)
    
    # Estadísticas generales
    total_ingresos = Venta.objects.filter(estatus='pagada', activo=True).aggregate(total=Sum('total'))['total'] or 0
    total_costo = 0
    
    for p in productos_data:
        total_costo += p['precio_costo'] * p['cantidad_vendida']
    
    for s in servicios_data:
        total_costo += s['precio_costo'] * s['cantidad_realizada']
    
    margen_total = float(total_ingresos) - total_costo
    margen_promedio = (margen_total / float(total_ingresos) * 100) if total_ingresos > 0 else 0
    
    return render(request, 'operaciones/reporte_margenes_mejorado.html', {
        'productos': productos_data,
        'servicios': servicios_data,
        'total_ingresos': float(total_ingresos),
        'total_costo': total_costo,
        'margen_total': margen_total,
        'margen_promedio': margen_promedio,
    })




# ========== ACCIONES RÁPIDAS PARA CITAS ==========

@login_required
def cita_cambiar_estado(request, pk):
    """Cambiar estado de una cita vía AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nuevo_estado = data.get('estado')
            cita = get_object_or_404(Cita, pk=pk, activo=True)
            
            estados_validos = ['pendiente', 'confirmada', 'completada', 'cancelada']
            if nuevo_estado not in estados_validos:
                return JsonResponse({'success': False, 'error': 'Estado no válido'})
            
            cita.estado = nuevo_estado
            cita.save()
            
            if nuevo_estado == 'completada':
                venta_existente = VentaCabecera.objects.filter(detalles__cita=cita, activo=True).exists()
                if not venta_existente:
                    _crear_venta_desde_cita(cita)
            
            return JsonResponse({
                'success': True,
                'nuevo_estado': nuevo_estado,
                'estado_display': cita.get_estado_display(),
                'badge_class': get_badge_class(nuevo_estado)
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@login_required
def cita_reagendar(request, pk):
    """Reagendar una cita vía AJAX"""
    if request.method == 'POST':
        try:
            import json
            from datetime import datetime
            from django.utils import timezone
            
            data = json.loads(request.body)
            cita = get_object_or_404(Cita, pk=pk, activo=True)
            
            nueva_fecha = data.get('fecha')
            nueva_hora = data.get('hora')
            nuevo_empleado_id = data.get('empleado_id')
            
            if nueva_fecha and nueva_hora:
                # Crear datetime con zona horaria usando make_aware
                fecha_hora_naive = datetime.strptime(f"{nueva_fecha} {nueva_hora}", "%Y-%m-%d %H:%M")
                fecha_hora = timezone.make_aware(fecha_hora_naive)
                
                # Obtener la fecha/hora actual
                ahora = timezone.now()
                
                if fecha_hora < ahora:
                    return JsonResponse({
                        'success': False, 
                        'error': 'No se puede reagendar a una fecha u hora anterior a la actual'
                    })
                
                cita.fecha_inicio = fecha_hora
                cita.fecha_fin = fecha_hora + timezone.timedelta(hours=cita.duracion_horas)
            
            if nuevo_empleado_id:
                from apps.empleados.models import Empleado
                cita.empleado = get_object_or_404(Empleado, pk=nuevo_empleado_id)
            
            cita.save()
            
            return JsonResponse({
                'success': True,
                'nueva_fecha': cita.fecha_inicio.strftime('%d/%m/%Y %H:%M'),
                'empleado_nombre': cita.empleado.nombre
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


def get_badge_class(estado):
    """Retorna la clase CSS para el badge según el estado"""
    clases = {
        'pendiente': 'bg-warning',
        'confirmada': 'bg-info',
        'completada': 'bg-success',
        'cancelada': 'bg-danger'
    }
    return clases.get(estado, 'bg-secondary')