from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from .models import Cliente
from .forms import ClienteForm


@login_required
def cliente_list(request):
    query = request.GET.get('q')

    queryset = Cliente.objects.all()

    if query:
        queryset = queryset.filter(nombre__icontains=query)

    paginator = Paginator(queryset, 10)
    page = request.GET.get('page')

    try:
        clientes = paginator.page(page)
    except PageNotAnInteger:
        clientes = paginator.page(1)
    except EmptyPage:
        clientes = paginator.page(paginator.num_pages)

    return render(request, 'clientes/list.html', {'clientes': clientes})

@login_required
def cliente_create(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente creado correctamente')
            return redirect('clientes:list')
        else:
            messages.error(request, 'Error al crear el cliente')
    else:
        form = ClienteForm()
    return render(request, 'clientes/form.html', {'titulo': 'Nuevo Cliente', 'form': form})


@login_required
def cliente_detail(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    return render(request, 'clientes/detail.html', {'cliente': cliente})


@login_required
def cliente_update(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado correctamente')
            return redirect('clientes:list')
        else:
            messages.error(request, 'Error al actualizar el cliente')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'clientes/form.html', {'titulo': 'Editar Cliente', 'form': form})


@login_required
def cliente_delete(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.delete()
        messages.success(request, 'Cliente eliminado correctamente')
        return redirect('clientes:list')
    return render(request, 'clientes/confirm_delete.html', {'cliente': cliente})