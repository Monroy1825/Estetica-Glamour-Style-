from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Venta, VentaDetalle, Cita


@receiver(pre_save, sender=Cita)
def crear_venta_desde_cita(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Cita.objects.get(pk=instance.pk)
            if instance.estado == 'completada' and old_instance.estado != 'completada':
                Venta.objects.create(
                    cliente=instance.cliente,
                    empleado=instance.empleado,
                    cita=instance,
                    total=float(instance.servicio.precio_base) if instance.servicio else 0,
                    metodo_pago='efectivo',
                    tipo='servicio',
                    estatus='pagada',
                    origen='cita'
                )
        except Cita.DoesNotExist:
            pass
