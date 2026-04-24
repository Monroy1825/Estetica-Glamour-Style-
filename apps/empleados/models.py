from django.db import models


class Empleado(models.Model):
    ROL_CHOICES = [
        ('estilista', 'Estilista'),
        ('colorista', 'Colorista'),
        ('manicurista', 'Manicurista'),
        ('recepcionista', 'Recepcionista'),
        ('gerente', 'Gerente'),
    ]

    nombre = models.CharField(max_length=50)
    telefono = models.CharField(max_length=50)
    rol = models.CharField(max_length=50, choices=ROL_CHOICES)
    fecha_ingreso = models.DateField()
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'
        ordering = ['nombre']

    def save(self, *args, **kwargs):
        if self.nombre:
            self.nombre = self.nombre.title()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.nombre} ({self.get_rol_display()})'
