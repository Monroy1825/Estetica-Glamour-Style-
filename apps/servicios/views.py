from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404, redirect
from .models import Servicio, Producto
from .forms import ServicioForm, ProductoForm


@login_required
def servicio_list(request):
    queryset = Servicio.objects.filter(activo=True)
    paginator = Paginator(queryset, 10)
    page = request.GET.get('page')
    try:
        servicios = paginator.page(page)
    except PageNotAnInteger:
        servicios = paginator.page(1)
    except EmptyPage:
        servicios = paginator.page(paginator.num_pages)
    return render(request, 'servicios/servicio_list.html', {'servicios': servicios})


@login_required
def servicio_create(request):
    if request.method == 'POST':
        form = ServicioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('servicios:servicio_list')
    else:
        form = ServicioForm()
    return render(request, 'servicios/servicio_form.html', {'titulo': 'Nuevo Servicio', 'form': form})


@login_required
def servicio_detail(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    return render(request, 'servicios/servicio_detail.html', {'servicio': servicio})


@login_required
def servicio_update(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    if request.method == 'POST':
        form = ServicioForm(request.POST, instance=servicio)
        if form.is_valid():
            form.save()
            return redirect('servicios:servicio_list')
    else:
        form = ServicioForm(instance=servicio)
    return render(request, 'servicios/servicio_form.html', {'titulo': 'Editar Servicio', 'form': form})


@login_required
def servicio_delete(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    if request.method == 'POST':
        servicio.activo = False
        servicio.save()
        return redirect('servicios:servicio_list')
    return render(request, 'servicios/servicio_confirm_delete.html', {'servicio': servicio})


@login_required
def producto_list(request):
    queryset = Producto.objects.filter(activo=True)
    paginator = Paginator(queryset, 10)
    page = request.GET.get('page')
    try:
        productos = paginator.page(page)
    except PageNotAnInteger:
        productos = paginator.page(1)
    except EmptyPage:
        productos = paginator.page(paginator.num_pages)
    return render(request, 'servicios/producto_list.html', {'productos': productos})


@login_required
def producto_create(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('servicios:producto_list')
    else:
        form = ProductoForm()
    return render(request, 'servicios/producto_form.html', {'titulo': 'Nuevo Producto', 'form': form})


@login_required
def producto_detail(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    return render(request, 'servicios/producto_detail.html', {'producto': producto})


@login_required
def producto_update(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            return redirect('servicios:producto_list')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'servicios/producto_form.html', {'titulo': 'Editar Producto', 'form': form})


@login_required
def producto_delete(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.activo = False
        producto.save()
        return redirect('servicios:producto_list')
    return render(request, 'servicios/producto_confirm_delete.html', {'producto': producto})
