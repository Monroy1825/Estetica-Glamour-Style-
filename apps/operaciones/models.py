from django.db import models
from apps.clientes.models import Cliente
from apps.empleados.models import Empleado
from apps.servicios.models import Servicio, Producto


class Cita(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='citas')
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='citas')
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name='citas')
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    activo = models.BooleanField(default=True)
    permitir_multiple = models.BooleanField(
        default=False,
        verbose_name='Permitir horario compartido',
        help_text='Marcar si el cliente necesita más de un servicio en este bloque'
    )

    class Meta:
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f'{self.cliente} - {self.servicio} ({self.fecha_inicio:%d/%m/%Y})'


class CitaServicioAdicional(models.Model):
    """Servicios extra que se agregan a una cita existente."""
    cita = models.ForeignKey(Cita, on_delete=models.CASCADE, related_name='servicios_adicionales')
    servicio = models.ForeignKey('servicios.Servicio', on_delete=models.CASCADE)
    nota = models.CharField(max_length=200, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Servicio adicional'
        verbose_name_plural = 'Servicios adicionales'

    def __str__(self):
        return f'{self.servicio} (extra en cita #{self.cita_id})'


class Venta(models.Model):
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia'),
    ]
    TIPO_CHOICES = [
        ('servicio', 'Servicio'),
        ('producto', 'Producto'),
        ('mixto', 'Mixto'),
    ]
    ESTATUS_CHOICES = [
        ('pagada', 'Pagada'),
        ('pendiente', 'Pendiente'),
        ('cancelada', 'Cancelada'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='ventas')
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='ventas')
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, blank=True, related_name='ventas')
    fecha = models.DateTimeField(auto_now_add=True)
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    estatus = models.CharField(max_length=20, choices=ESTATUS_CHOICES, default='pendiente')
    vigencia_hasta = models.DateField(null=True, blank=True)
    total = models.FloatField()
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-fecha']

    def __str__(self):
        return f'Venta #{self.pk} - {self.cliente} (${self.total})'


class Compra(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='compras')
    producto = models.ForeignKey(
        Producto, 
        on_delete=models.CASCADE, 
        related_name='compras',
        verbose_name='Producto'
    )
    proveedor = models.CharField(max_length=50)
    fecha = models.DateTimeField(auto_now_add=True)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad = models.PositiveIntegerField(default=1)
    activo = models.BooleanField(default=True)

    @property
    def total_compra(self):
        return self.precio_unitario * self.cantidad

    class Meta:
        verbose_name = 'Compra'
        verbose_name_plural = 'Compras'
        ordering = ['-fecha']

    def __str__(self):
        return f'Compra #{self.pk} - {self.producto.nombre} ({self.cantidad} x ${self.precio_unitario})'


class Cotizacion(models.Model):
    ESTADO_CHOICES = [
        ('vigente', 'Vigente'),
        ('aceptada', 'Aceptada'),
        ('vencida', 'Vencida'),
        ('rechazada', 'Rechazada'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='cotizaciones')
    servicio = models.ForeignKey(Servicio, on_delete=models.SET_NULL, null=True, blank=True, related_name='cotizaciones')
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, blank=True, related_name='cotizaciones')
    fecha = models.DateTimeField(auto_now_add=True)
    vigencia = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='vigente')
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Cotización'
        verbose_name_plural = 'Cotizaciones'
        ordering = ['-fecha']

    def __str__(self):
        return f'Cotización #{self.pk} - {self.cliente}'