from django.db import models

class Empleado(models.Model):
    ROL_CHOICES = [
        ('estilista', 'Estilista'),
        ('colorista', 'Colorista'),
        ('manicurista', 'Manicurista'),
        ('recepcionista', 'Recepcionista'),
        ('gerente', 'Gerente'),
    ]
    
    # Datos personales
    nombre = models.CharField(max_length=50)
    telefono = models.CharField(max_length=50)
    email = models.EmailField(blank=True, null=True, verbose_name='Correo electrónico')
    fecha_nacimiento = models.DateField(blank=True, null=True, verbose_name='Fecha de nacimiento')
    direccion = models.TextField(blank=True, null=True, verbose_name='Dirección')
    
    # Datos laborales
    rol = models.CharField(max_length=50, choices=ROL_CHOICES)
    fecha_ingreso = models.DateField(verbose_name='Fecha de ingreso')
    horario_entrada = models.CharField(max_length=10, blank=True, null=True, 
                                       choices=[('10:00','10:00 AM'),('11:00','11:00 AM'),('12:00','12:00 PM'),('13:00','01:00 PM'),('17:00','05:00 PM'),('18:00','06:00 PM'),('19:00','07:00 PM'),('20:00','08:00 PM')],
                                       verbose_name='Hora de entrada')
    horario_salida = models.CharField(max_length=10, blank=True, null=True,
                                      choices=[('10:00','10:00 AM'),('11:00','11:00 AM'),('12:00','12:00 PM'),('13:00','01:00 PM'),('17:00','05:00 PM'),('18:00','06:00 PM'),('19:00','07:00 PM'),('20:00','08:00 PM')],
                                      verbose_name='Hora de salida')
    dias_descanso = models.CharField(max_length=100, blank=True, null=True, 
                                      help_text='Ej: Domingo, Lunes', verbose_name='Días de descanso')
    
    # Datos financieros
    comision = models.DecimalField(max_digits=5, decimal_places=2, default=0, 
                                    verbose_name='Comisión (%)', help_text='Porcentaje sobre ventas')
    sueldo_base = models.DecimalField(max_digits=10, decimal_places=2, default=0, 
                                       verbose_name='Sueldo base')
    
    # Datos profesionales
    especialidades = models.TextField(blank=True, null=True, 
                                       help_text='Ej: Corte, Color, Uñas', verbose_name='Especialidades')
    años_experiencia = models.IntegerField(default=0, verbose_name='Años de experiencia')
    
    # Estado
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