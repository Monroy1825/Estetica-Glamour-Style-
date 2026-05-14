from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from datetime import datetime
import json

from .models import Cita, Venta, Compra, Cotizacion
from .forms import CitaForm, VentaForm, CompraForm, CotizacionForm


def _paginate(queryset, request):
    paginator = Paginator(queryset, 10)
    page = request.GET.get('page')
    try:
        return paginator.page(page)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)

# --- Citas ---

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
    # Importar los modelos necesarios
    from apps.empleados.models import Empleado
    from apps.clientes.models import Cliente
    
    # Agrupar por empleado
    empleados_con_citas = []
    empleados = Empleado.objects.filter(activo=True)
    
    for empleado in empleados:
        citas_empleado = Cita.objects.filter(
            activo=True, 
            empleado=empleado
        ).select_related('cliente', 'servicio').order_by('-fecha_inicio')
        
        if citas_empleado.exists():
            # Obtener clientes únicos de este empleado
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
        'empleados_con_citas': empleados_con_citas
    })

@login_required
def cita_create(request):
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
                    'form': form
                })

            cita = form.save(commit=False)
            cita.fecha_inicio = fecha_inicio
            cita.fecha_fin = fecha_fin
            cita.save()

            agregar_otra = request.POST.get('agregar_otra', 'no')
            if agregar_otra == 'si':
                messages.success(request, '¡Cita guardada! Ahora registra la siguiente cita del cliente.')
                return redirect(
                    f"{request.path}?cliente={form.cleaned_data['cliente'].id}"
                    f"&empleado={empleado_id}"
                )

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
    cita = get_object_or_404(Cita.objects.select_related('cliente', 'empleado', 'servicio'), pk=pk)
    return render(request, 'operaciones/cita_detail.html', {'cita': cita})

@login_required
def cita_update(request, pk):
    cita = get_object_or_404(Cita, pk=pk)
    if request.method == 'POST':
        form = CitaForm(request.POST, instance=cita)
        if form.is_valid():
            cita = form.save(commit=False)
            cita.save()
            messages.success(request, '¡Cita actualizada correctamente!')
            return redirect('operaciones:cita_list')
    else:
        form = CitaForm(instance=cita)
    return render(request, 'operaciones/cita_form.html', {'titulo': 'Editar Cita', 'form': form, 'cita_id': cita.pk})

@login_required
def cita_delete(request, pk):
    cita = get_object_or_404(Cita, pk=pk)
    if request.method == 'POST':
        cita.activo = False
        cita.save()
        messages.success(request, 'La cita ha sido eliminada.')
        return redirect('operaciones:cita_list')
    return render(request, 'operaciones/cita_confirm_delete.html', {'cita': cita})


@login_required
def get_precio_cita(request, cita_id):
    cita = get_object_or_404(Cita, pk=cita_id)
    return JsonResponse({'precio': float(cita.servicio.precio_base)})


# --- Ventas ---

@login_required
def venta_list(request):
    qs = Venta.objects.filter(activo=True).select_related('cliente', 'empleado', 'producto', 'cita__servicio')
    
    # Calcular estadísticas
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
    if request.method == 'POST':
        form = VentaForm(request.POST)
        if form.is_valid():
            cita = form.cleaned_data.get('cita')
            producto = form.cleaned_data.get('producto')
            cliente = form.cleaned_data['cliente']
            
            session_key = f'ticket_ventas_{cliente.id}'
            ids_sesion = request.session.get(session_key, [])

            if cita and producto:
                precio_servicio = float(cita.servicio.precio_base)
                precio_producto = float(producto.precio_venta)
                
                venta_servicio = Venta(
                    cliente=cliente,
                    empleado=form.cleaned_data['empleado'],
                    cita=cita,
                    producto=None,
                    metodo_pago=form.cleaned_data['metodo_pago'],
                    tipo='servicio',
                    estatus=form.cleaned_data.get('estatus', 'pendiente'),
                    total=precio_servicio,
                    activo=True
                )
                venta_servicio.save()
                ids_sesion.append(venta_servicio.pk)
                
                if producto.stock_actual > 0:
                    venta_producto = Venta(
                        cliente=cliente,
                        empleado=form.cleaned_data['empleado'],
                        cita=None,
                        producto=producto,
                        metodo_pago=form.cleaned_data['metodo_pago'],
                        tipo='producto',
                        estatus=form.cleaned_data.get('estatus', 'pendiente'),
                        total=precio_producto,
                        activo=True
                    )
                    venta_producto.save()
                    ids_sesion.append(venta_producto.pk)
                    producto.stock_actual -= 1
                    producto.save()
                    
                request.session[session_key] = ids_sesion
                messages.success(request, f'¡Ventas registradas!')
                return redirect('operaciones:venta_list')

            elif producto:
                if producto.stock_actual <= 0:
                    messages.error(request, f'Sin stock disponible para "{producto.nombre}".')
                else:
                    venta = form.save(commit=False)
                    venta.tipo = 'producto'
                    venta.save()
                    ids_sesion.append(venta.pk)
                    request.session[session_key] = ids_sesion
                    producto.stock_actual -= 1
                    producto.save()
                    messages.success(request, '¡Venta registrada con éxito!')
                return redirect('operaciones:venta_list')

            elif cita:
                venta = form.save(commit=False)
                venta.tipo = 'servicio'
                venta.save()
                ids_sesion.append(venta.pk)
                request.session[session_key] = ids_sesion
                messages.success(request, '¡Venta registrada con éxito!')
                return redirect('operaciones:venta_list')

            else:
                messages.error(request, 'Debe seleccionar al menos una cita o un producto')
                
    else:
        form = VentaForm()
    
    return render(request, 'operaciones/venta_form.html', {'titulo': 'Nueva Venta', 'form': form})

@login_required
def venta_detail(request, pk):
    venta = get_object_or_404(Venta.objects.select_related('cliente', 'empleado', 'producto'), pk=pk)
    return render(request, 'operaciones/venta_detail.html', {'venta': venta})

@login_required
def venta_ticket(request, pk):
    venta = get_object_or_404(Venta.objects.select_related('cliente', 'empleado', 'producto', 'cita__servicio'), pk=pk)
    cliente = venta.cliente
    
    # Verificar si es un comprobante de pago
    es_comprobante = request.GET.get('pagado') == '1'
    
    # Obtener los IDs de las ventas de esta sesión
    session_key = f'ticket_ventas_{cliente.id}'
    ids_sesion = request.session.get(session_key, [])
    
    if es_comprobante:
        # Mostrar las ventas que se pagaron en esta sesión
        ventas = Venta.objects.filter(
            id__in=ids_sesion,
            activo=True
        ).select_related('producto', 'cita__servicio').prefetch_related('cita__servicios_adicionales')
        
        # Limpiar la sesión
        request.session[session_key] = []
        hay_pendientes = False
    else:
        # Si no hay IDs en sesión, mostrar las ventas pendientes del cliente
        if ids_sesion:
            ventas = Venta.objects.filter(
                id__in=ids_sesion,
                activo=True,
                estatus='pendiente'
            ).select_related('producto', 'cita__servicio').prefetch_related('cita__servicios_adicionales')
        else:
            # Si no hay sesión, mostrar todas las ventas pendientes del cliente
            ventas = Venta.objects.filter(
                cliente=cliente,
                activo=True,
                estatus='pendiente'
            ).select_related('producto', 'cita__servicio').prefetch_related('cita__servicios_adicionales')
        
        hay_pendientes = ventas.exists()
    
    total = sum(v.total for v in ventas)
    
    # Generar folio
    from datetime import datetime
    folio = f"{cliente.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    return render(request, 'operaciones/venta_ticket.html', {
        'venta': venta,
        'ventas': ventas,
        'total': total,
        'cliente': cliente,
        'hay_pendientes': hay_pendientes,
        'es_comprobante': es_comprobante,
        'folio': folio,
    })


@login_required
def venta_update(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        form = VentaForm(request.POST, instance=venta)
        if form.is_valid():
            form.save()
            messages.success(request, 'Venta actualizada.')
            return redirect('operaciones:venta_list')
    else:
        form = VentaForm(instance=venta)
    return render(request, 'operaciones/venta_form.html', {'titulo': 'Editar Venta', 'form': form})

@login_required
def venta_delete(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        venta.activo = False
        venta.save()
        messages.success(request, 'Venta eliminada.')
        return redirect('operaciones:venta_list')
    return render(request, 'operaciones/venta_confirm_delete.html', {'venta': venta})


# --- Compras ---



@login_required
def compra_list(request):
    qs = Compra.objects.filter(activo=True).select_related('empleado', 'producto')
    
    # Calcular estadísticas
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
            compra = form.save()
            producto.stock_actual += cantidad
            producto.save()
            messages.success(request, '¡Compra registrada!')
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


# --- Cotizaciones ---

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


# --- Proveedores ---

@login_required
def proveedor_list(request):
    proveedores = Compra.objects.values('proveedor').annotate(
        total_compras=Count('id'),
        inversion_total=Sum('precio_unitario')
    ).order_by('-inversion_total')
    return render(request, 'operaciones/proveedor_list.html', {'proveedores': proveedores})


# confirmar pago
@login_required
def confirmar_pago(request, cliente_id):
    """Confirmar pago de todas las ventas pendientes de un cliente"""
    if request.method == 'POST':
        from django.db.models import Sum
        
        ventas = Venta.objects.filter(
            cliente_id=cliente_id,
            estatus='pendiente',
            activo=True
        )
        
        if ventas.exists():
            cantidad = ventas.count()
            total = ventas.aggregate(total=Sum('total'))['total']
            
            # Cambiar estatus a pagada
            ventas.update(estatus='pagada')
            
            # Obtener el ID de la primera venta para el ticket (usar cualquier venta del cliente)
            primera_venta = ventas.first()
            
            # Si por alguna razón no hay venta, buscar cualquier venta del cliente
            if not primera_venta:
                primera_venta = Venta.objects.filter(cliente_id=cliente_id, activo=True).first()
            
            messages.success(
                request, 
                f'Pago confirmado correctamente. {cantidad} venta(s) pagada(s). Total: ${total}'
            )
            
            # Redirigir al ticket
            if primera_venta:
                return redirect(f'/operaciones/ventas/{primera_venta.pk}/ticket/?imprimir=1&pagado=1')
            else:
                return redirect('operaciones:venta_list')
        else:
            messages.warning(request, 'No hay ventas pendientes para este cliente.')
    
    return redirect('operaciones:venta_list')


## ajuste para vista convinada en el ticket de venta 

@login_required
def venta_combinada_create(request):
    if request.method == 'POST':
        form = VentaCombinadaForm(request.POST)
        if form.is_valid():
            # Crear cabecera
            venta = VentaCabecera.objects.create(
                cliente=form.cleaned_data['cliente'],
                empleado=form.cleaned_data['empleado'],
                metodo_pago=form.cleaned_data['metodo_pago'],
                estatus='pendiente'
            )
            
            total = 0
            
            # Agregar servicio de la cita
            if form.cleaned_data['cita']:
                cita = form.cleaned_data['cita']
                precio = float(cita.servicio.precio_base)
                VentaDetalle.objects.create(
                    venta=venta,
                    tipo='servicio',
                    servicio=cita.servicio,
                    cita=cita,
                    descripcion=cita.servicio.nombre,
                    cantidad=1,
                    precio_unitario=precio,
                    subtotal=precio
                )
                total += precio
                
                # Servicios adicionales
                for extra in cita.servicios_adicionales.all():
                    precio_extra = float(extra.servicio.precio_base)
                    VentaDetalle.objects.create(
                        venta=venta,
                        tipo='servicio',
                        servicio=extra.servicio,
                        cita=cita,
                        descripcion=f'+ {extra.servicio.nombre}',
                        cantidad=1,
                        precio_unitario=precio_extra,
                        subtotal=precio_extra
                    )
                    total += precio_extra
            
            # Agregar producto
            if form.cleaned_data['producto']:
                producto = form.cleaned_data['producto']
                precio = float(producto.precio_venta)
                VentaDetalle.objects.create(
                    venta=venta,
                    tipo='producto',
                    producto=producto,
                    descripcion=producto.nombre,
                    cantidad=1,
                    precio_unitario=precio,
                    subtotal=precio
                )
                total += precio
                producto.stock_actual -= 1
                producto.save()
            
            # Actualizar total de la venta
            venta.subtotal = total
            venta.total = total
            venta.save()
            
            messages.success(request, f'Venta {venta.folio} creada exitosamente. Total: ${total}')
            return redirect('operaciones:venta_list')
    else:
        form = VentaCombinadaForm()
    
    return render(request, 'operaciones/venta_combinada_form.html', {'form': form})



# prueba para eliminar varias citas a la vez 

import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse


@login_required
@require_POST
def cita_batch_delete(request):
    """Eliminar múltiples citas a la vez"""
    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
        
        if not ids:
            return JsonResponse({'success': False, 'error': 'No se seleccionaron citas'})
        
        # Eliminar (desactivar) las citas
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
    """Eliminar múltiples ventas a la vez"""
    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
        
        if not ids:
            return JsonResponse({'success': False, 'error': 'No se seleccionaron ventas'})
        
        # Eliminar (desactivar) las ventas
        ventas_eliminadas = Venta.objects.filter(pk__in=ids, activo=True).update(activo=False)
        
        return JsonResponse({
            'success': True,
            'eliminadas': ventas_eliminadas,
            'mensaje': f'Se eliminaron {ventas_eliminadas} venta(s) correctamente'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

    



