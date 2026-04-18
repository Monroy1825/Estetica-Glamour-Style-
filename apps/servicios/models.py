from django.db import models


class Servicio(models.Model):
    CATEGORIA_CHOICES = [
        ('corte', 'Corte'),
        ('color', 'Color'),
        ('tratamiento', 'Tratamiento'),
        ('unas', 'Uñas'),
        ('maquillaje', 'Maquillaje'),
        ('otro', 'Otro'),
    ]

    nombre = models.CharField(max_length=50)
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        ordering = ['categoria', 'nombre']

    def __str__(self):
        return f'{self.nombre} - ${self.precio_base}'


class Producto(models.Model):
    nombre = models.CharField(max_length=50)
    marca = models.CharField(max_length=50)
    costo = models.FloatField()
    precio_venta = models.FloatField()
    stock_actual = models.IntegerField()
    stock_minimo = models.IntegerField()
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.marca})'

    @property
    def stock_bajo(self):
        return self.stock_actual <= self.stock_minimo
