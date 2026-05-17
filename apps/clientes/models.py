from django.db import models

class Cliente(models.Model):
    TIPO_CLIENTE_CHOICES = [
        ('registrado', 'Cliente Registrado'),
        ('venta_rapida', 'Venta Rápida (Ocasional)'),
    ]
    
    nombre = models.CharField(max_length=50)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    tipo_cliente = models.CharField(max_length=20, choices=TIPO_CLIENTE_CHOICES, default='registrado', verbose_name='Tipo de cliente')
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nombre']

    def save(self, *args, **kwargs):
        if self.nombre:
            self.nombre = self.nombre.title()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.tipo_cliente == 'venta_rapida':
            return f'{self.nombre} (⚡ Venta rápida)'
        return self.nombre