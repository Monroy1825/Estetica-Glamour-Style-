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
    qs = Cita.objects.filter(activo=True).select_related('cliente', 'empleado', 'servicio')
    return render(request, 'operaciones/cita_list.html', {'citas': _paginate(qs, request)})


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


# --- Ventas ---

@login_required
def venta_list(request):
    qs = Venta.objects.filter(activo=True).select_related('cliente', 'empleado', 'producto')
    return render(request, 'operaciones/venta_list.html', {'ventas': _paginate(qs, request)})

@login_required
def venta_create(request):
    if request.method == 'POST':
        form = VentaForm(request.POST)
        if form.is_valid():
            cita = form.cleaned_data.get('cita')
            producto = form.cleaned_data.get('producto')
            if producto is not None:
                if producto.stock_actual <= 0:
                    messages.error(request, f'Sin stock disponible para "{producto}". No se pudo registrar la venta.')
                else:
                    venta = form.save()
                    producto.stock_actual -= 1
                    producto.save()
                    messages.success(request, '¡Venta registrada con éxito!')
                    return redirect('operaciones:venta_list')
            else:
                form.save()
                messages.success(request, '¡Venta registrada con éxito!')
                return redirect('operaciones:venta_list')
            
            # Caso 3: Ambos (cita y producto) - CREAR DOS VENTAS SEPARADAS
            elif cita and producto:
                # Obtener precios
                precio_servicio = float(cita.servicio.precio_base)
                precio_producto = float(producto.precio_venta)
                
                # Crear venta para el servicio
                venta_servicio = Venta(
                    cliente=form.cleaned_data['cliente'],
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
                
                # Verificar stock del producto
                if producto.stock_actual <= 0:
                    messages.warning(request, f'Producto "{producto.nombre}" sin stock. Solo se registró el servicio.')
                else:
                    # Crear venta para el producto
                    venta_producto = Venta(
                        cliente=form.cleaned_data['cliente'],
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
                    producto.stock_actual -= 1
                    producto.save()
                
                messages.success(request, f'¡Ventas registradas! Servicio: ${precio_servicio}, Producto: ${precio_producto}')
                return redirect('operaciones:venta_list')
            
            else:
                messages.error(request, 'Debe seleccionar al menos una cita o un producto')
                return render(request, 'operaciones/venta_form.html', {'titulo': 'Nueva Venta', 'form': form})
                
    else:
        form = VentaForm()
    
    return render(request, 'operaciones/venta_form.html', {'titulo': 'Nueva Venta', 'form': form})

@login_required
def venta_detail(request, pk):
    venta = get_object_or_404(Venta.objects.select_related('cliente', 'empleado', 'producto'), pk=pk)
    return render(request, 'operaciones/venta_detail.html', {'venta': venta})

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
    qs = Compra.objects.filter(activo=True).select_related('empleado')
    return render(request, 'operaciones/compra_list.html', {'compras': _paginate(qs, request)})


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
            
            ventas.update(estatus='pagada')
            
            messages.success(
                request, 
                f'Pago confirmado correctamente. {cantidad} venta(s) pagada(s). Total: ${total}'
            )
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
    
