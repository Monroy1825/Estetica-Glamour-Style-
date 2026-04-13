from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404, redirect
from .models import Empleado
from .forms import EmpleadoForm


@login_required
def empleado_list(request):
    queryset = Empleado.objects.all()
    paginator = Paginator(queryset, 10)
    page = request.GET.get('page')
    try:
        empleados = paginator.page(page)
    except PageNotAnInteger:
        empleados = paginator.page(1)
    except EmptyPage:
        empleados = paginator.page(paginator.num_pages)
    return render(request, 'empleados/list.html', {'empleados': empleados})


@login_required
def empleado_create(request):
    if request.method == 'POST':
        form = EmpleadoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('empleados:list')
    else:
        form = EmpleadoForm()
    return render(request, 'empleados/form.html', {'titulo': 'Nuevo Empleado', 'form': form})


@login_required
def empleado_detail(request, pk):
    empleado = get_object_or_404(Empleado, pk=pk)
    return render(request, 'empleados/detail.html', {'empleado': empleado})


@login_required
def empleado_update(request, pk):
    empleado = get_object_or_404(Empleado, pk=pk)
    if request.method == 'POST':
        form = EmpleadoForm(request.POST, instance=empleado)
        if form.is_valid():
            form.save()
            return redirect('empleados:list')
    else:
        form = EmpleadoForm(instance=empleado)
    return render(request, 'empleados/form.html', {'titulo': 'Editar Empleado', 'form': form})


@login_required
def empleado_delete(request, pk):
    empleado = get_object_or_404(Empleado, pk=pk)
    if request.method == 'POST':
        empleado.delete()
        return redirect('empleados:list')
    return render(request, 'empleados/confirm_delete.html', {'empleado': empleado})
