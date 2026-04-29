from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Count # Importante para los totales
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

            # 🔴 VALIDAR CRUCE DE HORARIOS
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

            # 🔥 GUARDAR BIEN (AQUI ESTA LA CLAVE)
            cita = form.save(commit=False)
            cita.fecha_inicio = fecha_inicio
            cita.fecha_fin = fecha_fin
            cita.save()

            messages.success(request, '¡La cita se ha creado exitosamente!')
            return redirect('operaciones:cita_list')

    else:
        form = CitaForm()

    return render(request, 'operaciones/cita_form.html', {
        'titulo': 'Nueva Cita',
        'form': form
    })


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

            empleado_id = form.cleaned_data['empleado'].id
            fecha_inicio = form.cleaned_data['fecha_inicio']
            fecha_fin = form.cleaned_data['fecha_fin']  # 👈 ya viene del form limpio

            # 🔴 VALIDAR CRUCE DE HORARIOS
            citas_conflicto = Cita.objects.filter(
                empleado_id=empleado_id,
                activo=True,
            ).filter(
                Q(fecha_inicio__lt=fecha_fin) & Q(fecha_fin__gt=fecha_inicio)
            ).exclude(pk=cita.pk)

            if citas_conflicto.exists():
                messages.error(request, 'El empleado ya tiene una cita en ese horario.')
                return render(request, 'operaciones/cita_form.html', {
                    'titulo': 'Editar Cita',
                    'form': form
                })

            # 🔥 FORZAR ACTUALIZACIÓN CORRECTA
            cita = form.save(commit=False)
            cita.fecha_inicio = fecha_inicio
            cita.fecha_fin = fecha_fin  # 👈 ESTA ES LA CLAVE
            cita.save()

            messages.success(request, '¡Cita actualizada correctamente!')
            return redirect('operaciones:cita_list')

    else:
        form = CitaForm(instance=cita)

    return render(request, 'operaciones/cita_form.html', {
        'titulo': 'Editar Cita',
        'form': form
    })


@login_required
def cita_delete(request, pk):
    cita = get_object_or_404(Cita, pk=pk)
    if request.method == 'POST':
        cita.activo = False
        cita.save()
        messages.success(request, 'La cita ha sido eliminada del sistema.')
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
            messages.success(request, 'Datos de venta actualizados.')
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
        messages.success(request, 'El registro de venta ha sido eliminado.')
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
            compra = form.save(commit=False)
            compra.cantidad = cantidad
            compra.save()
            producto.stock_actual += cantidad
            producto.save()
            messages.success(request, '¡Compra registrada correctamente!')
            return redirect('operaciones:compra_list')
    else:
        form = CompraForm()
    return render(request, 'operaciones/compra_form.html', {'titulo': 'Nueva Compra', 'form': form})


@login_required
def compra_detail(request, pk):
    compra = get_object_or_404(Compra.objects.select_related('empleado'), pk=pk)
    return render(request, 'operaciones/compra_detail.html', {'compra': compra})


@login_required
def compra_update(request, pk):
    compra = get_object_or_404(Compra, pk=pk)
    if request.method == 'POST':
        form = CompraForm(request.POST, instance=compra)
        if form.is_valid():
            compra = form.save(commit=False)
            compra.cantidad = form.cleaned_data['cantidad']
            compra.save()
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
        messages.success(request, 'Registro de compra eliminado.')
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
            messages.success(request, '¡Cotización generada exitosamente!')
            return redirect('operaciones:cotizacion_list')
    else:
        form = CotizacionForm()
    return render(request, 'operaciones/cotizacion_form.html', {'titulo': 'Nueva Cotización', 'form': form})


@login_required
def cotizacion_detail(request, pk):
    cotizacion = get_object_or_404(Cotizacion.objects.select_related('cliente', 'servicio', 'producto'), pk=pk)
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
    return render(request, 'operaciones/cotizacion_form.html', {'titulo': 'Editar Cotización', 'form': form})


@login_required
def cotizacion_delete(request, pk):
    cotizacion = get_object_or_404(Cotizacion, pk=pk)
    if request.method == 'POST':
        cotizacion.activo = False
        cotizacion.save()
        messages.success(request, 'Cotización eliminada.')
        return redirect('operaciones:cotizacion_list')
    return render(request, 'operaciones/cotizacion_confirm_delete.html', {'cotizacion': cotizacion})


# --- Proveedores (Catálogo Agrupado) ---
@login_required
def proveedor_list(request):
    proveedores = Compra.objects.values('proveedor').annotate(
        total_compras=Count('id'),
        inversion_total=Sum('precio_unitario')
    ).order_by('-inversion_total')
    return render(request, 'operaciones/proveedor_list.html', {'proveedores': proveedores})