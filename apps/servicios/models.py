from django.db import models


class Servicio(models.Model):
    CATEGORIA_CHOICES = [
        ('corte', 'Corte'),
        ('color', 'Color'),
        ('tratamiento', 'Tratamiento'),
        ('unas', 'Uñas'),
        ('maquillaje', 'Maquillaje'),
    ]
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    precio_base = models.DecimalField(max_digits=8, decimal_places=2)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        ordering = ['nombre']

    def save(self, *args, **kwargs):
        if self.nombre:
            self.nombre = self.nombre.title()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    PRESENTACION_CHOICES = [
        ('', '— Selecciona presentación —'),
        ('botella', 'Botella'),
        ('frasco', 'Frasco'),
        ('tubo', 'Tubo'),
        ('sachet', 'Sachet'),
        ('lata', 'Lata'),
        ('caja', 'Caja'),
        ('pieza', 'Pieza'),
        ('paquete', 'Paquete'),
        ('otro', 'Otro'),
    ]

    nombre = models.CharField(max_length=100)
    marca = models.CharField(max_length=100, blank=True)
    presentacion = models.CharField(
        max_length=50,
        blank=True,
        choices=PRESENTACION_CHOICES,
        verbose_name='Presentación',
        help_text='Tipo de envase o presentación del producto'
    )
    tamano = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Tamaño',
        help_text='Selecciona la medida del producto'
    )
    tamano_personalizado = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Tamaño personalizado',
        help_text='Si el tamaño no está en la lista, escríbelo aquí'
    )
    costo = models.DecimalField(max_digits=8, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=8, decimal_places=2)
    stock_actual = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=5)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']

    def get_tamano_final(self):
        return self.tamano_personalizado if self.tamano_personalizado else self.tamano

    def __str__(self):
        tamano = self.get_tamano_final()
        return f'{self.nombre} ({tamano})' if tamano else self.nombre