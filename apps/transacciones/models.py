from django.db import models
from apps.clientes.models import Cliente
from apps.empleados.models import Empleado
from apps.servicios.models import Servicio, Producto
from datetime import datetime


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
    duracion_horas = models.FloatField(default=1.0, verbose_name='Duración estimada (horas)')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    turno = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Número de turno',
        help_text='Turno asignado al cliente para esta cita'
    )
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
    
    def generar_venta_automatica(self, empleado, metodo_pago='efectivo'):
        from .models import Venta
        precio_base = float(self.servicio.precio_base)
        precio_adicionales = 0
        for extra in self.servicios_adicionales.all():
            precio_adicionales += float(extra.servicio.precio_base)
        total = precio_base + precio_adicionales
        venta = Venta.objects.create(
            cliente=self.cliente,
            empleado=empleado,
            cita=self,
            metodo_pago=metodo_pago,
            tipo='servicio',
            estatus='pagada',
            total=total,
            activo=True,
            origen='cita'
        )
        return venta


class CitaServicioAdicional(models.Model):
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
    ORIGEN_CHOICES = [
        ('cita', 'Cita'),
        ('venta_directa', 'Venta directa'),
        ('cotizacion', 'Cotización'),
    ]

    cita = models.ForeignKey(
        'Cita',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ventas',
        verbose_name='Cita relacionada'
    )
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
    origen = models.CharField(max_length=20, choices=ORIGEN_CHOICES, default='venta_directa', verbose_name='Origen de la venta')
    
    # ✅ CAMPOS NUEVOS (auditoría)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='ventas_creadas')
    updated_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='ventas_actualizadas')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def margen_ganancia(self):
        if self.producto:
            costo = float(self.producto.costo)
            venta = float(self.total)
            return venta - costo
        return 0
    
    @property
    def porcentaje_ganancia(self):
        if self.producto and float(self.producto.costo) > 0:
            costo = float(self.producto.costo)
            venta = float(self.total)
            return ((venta - costo) / costo) * 100
        return 0

    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-fecha']

    def __str__(self):
        origen_texto = '📅 Cita' if self.origen == 'cita' else '🛒 Directa'
        return f'{origen_texto} #{self.pk} - {self.cliente} (${self.total})'


class Compra(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='compras')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='compras', verbose_name='Producto')
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


class VentaCabecera(models.Model):
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia'),
    ]
    ESTATUS_CHOICES = [
        ('pagada', 'Pagada'),
        ('pendiente', 'Pendiente'),
        ('cancelada', 'Cancelada'),
    ]

    folio = models.CharField(max_length=20, unique=True, editable=False)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='ventas_cabecera')
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='ventas_cabecera')
    fecha = models.DateTimeField(auto_now_add=True)
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)
    estatus = models.CharField(max_length=20, choices=ESTATUS_CHOICES, default='pendiente')
    subtotal = models.FloatField(default=0)
    total = models.FloatField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-fecha']

    def save(self, *args, **kwargs):
        if not self.folio:
            from datetime import datetime
            fecha_str = datetime.now().strftime('%Y%m%d')
            ultima_venta = VentaCabecera.objects.filter(
                folio__startswith=f'VENTA-{fecha_str}'
            ).order_by('-folio').first()
            if ultima_venta:
                ultimo_numero = int(ultima_venta.folio.split('-')[-1])
                nuevo_numero = ultimo_numero + 1
            else:
                nuevo_numero = 1
            self.folio = f'VENTA-{fecha_str}-{nuevo_numero:04d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.folio} - {self.cliente} (${self.total})'


class VentaDetalle(models.Model):
    TIPO_CHOICES = [
        ('servicio', 'Servicio'),
        ('producto', 'Producto'),
    ]
    
    venta = models.ForeignKey(VentaCabecera, on_delete=models.CASCADE, related_name='detalles')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    servicio = models.ForeignKey(Servicio, on_delete=models.SET_NULL, null=True, blank=True)
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, blank=True)
    cita = models.ForeignKey(Cita, on_delete=models.SET_NULL, null=True, blank=True)
    descripcion = models.CharField(max_length=200)
    cantidad = models.IntegerField(default=1)
    precio_unitario = models.FloatField()
    precio_costo_unitario = models.FloatField(default=0)   # ✅ NUEVO CAMPO
    subtotal = models.FloatField()
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Detalle de venta'
        verbose_name_plural = 'Detalles de venta'

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.descripcion} x{self.cantidad} = ${self.subtotal}'
