from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from apps.clientes.models import Cliente
from apps.empleados.models import Empleado
from apps.servicios.models import Servicio, Producto
from apps.operaciones.models import Cita, Venta, Compra, Cotizacion
 
 
class Command(BaseCommand):
    help = 'Poblar la base de datos con datos de prueba de un salón mexicano'
 
    def handle(self, *args, **kwargs):
        self.stdout.write('Creando datos de prueba...')
 
        # Superusuario
        admin, _ = User.objects.get_or_create(username='admin', defaults={
            'email': 'admin@estetica.mx',
            'is_staff': True,
            'is_superuser': True,
        })
        admin.set_password('admin123')
        admin.save()
        self.stdout.write('  [OK] Superusuario: admin / admin123')
 
        # Empleados
        empleados_data = [
            ('Valeria Reyes Mora', '5512345678', 'estilista', date(2021, 3, 15)),
            ('Karla Mendoza López', '5523456789', 'colorista', date(2020, 7, 1)),
            ('Diana Flores Ruiz', '5534567890', 'manicurista', date(2022, 1, 20)),
            ('Sofía Castro Vega', '5545678901', 'recepcionista', date(2019, 11, 5)),
            ('Lucía Herrera Paz', '5556789012', 'gerente', date(2018, 5, 10)),
        ]
        empleados = []
        for nombre, telefono, rol, fecha in empleados_data:
            emp, _ = Empleado.objects.get_or_create(nombre=nombre, defaults={
                'telefono': telefono,
                'rol': rol,
                'fecha_ingreso': fecha,
            })
            empleados.append(emp)
        self.stdout.write(f'  [OK] {len(empleados)} empleados')
 
        # Clientes
        clientes_data = [
            ('Ana González Torres', '5511112222', 'ana.gonzalez@gmail.com'),
            ('María Pérez Jiménez', '5522223333', 'mperez@hotmail.com'),
            ('Laura Ramírez Cruz', '5533334444', 'laurarc@gmail.com'),
            ('Fernanda López Soto', '5544445555', 'fer.lopez@outlook.com'),
            ('Claudia Martínez Ávila', '5555556666', 'claudiam@gmail.com'),
            ('Patricia Díaz Mora', '5566667777', 'pdiaz@gmail.com'),
            ('Gabriela Sánchez Luna', '5577778888', 'gaby.sanchez@gmail.com'),
            ('Isabel Vargas Romo', '5588889999', 'isabel.v@hotmail.com'),
        ]
        clientes = []
        for nombre, telefono, email in clientes_data:
            cli, _ = Cliente.objects.get_or_create(nombre=nombre, defaults={
                'telefono': telefono,
                'email': email,
            })
            clientes.append(cli)
        self.stdout.write(f'  [OK] {len(clientes)} clientes')
 
        # Servicios
        servicios_data = [
            ('Corte Dama', 'corte', 220.00),
            ('Corte Caballero', 'corte', 120.00),
            ('Tinte Completo', 'color', 650.00),
            ('Manicure Clásico', 'unas', 150.00),
            ('Pedicure Completo', 'unas', 200.00),
            ('Tratamiento Keratina', 'tratamiento', 900.00),
        ]
        servicios = []
        for nombre, categoria, precio in servicios_data:
            srv, _ = Servicio.objects.get_or_create(nombre=nombre, defaults={
                'categoria': categoria,
                'precio_base': precio,
            })
            servicios.append(srv)
        self.stdout.write(f'  [OK] {len(servicios)} servicios')
 
        # Productos
        productos_data = [
            ('Shampoo Reparador', 'Loreal', 85.00, 145.00, 20, 5),
            ('Tinte Rubio Cenizo', 'Wella', 120.00, 210.00, 15, 4),
            ('Acondicionador Intensivo', 'Loreal', 90.00, 155.00, 18, 5),
            ('Esmalte Rojo Intenso', 'OPI', 40.00, 80.00, 3, 5),
        ]
        productos = []
        for nombre, marca, costo, pventa, stock_a, stock_m in productos_data:
            prod, _ = Producto.objects.get_or_create(nombre=nombre, defaults={
                'marca': marca,
                'costo': costo,
                'precio_venta': pventa,
                'stock_actual': stock_a,
                'stock_minimo': stock_m,
            })
            productos.append(prod)
        self.stdout.write(f'  [OK] {len(productos)} productos')
 
        now = timezone.now()
 
        # Citas
        citas_data = [
            (clientes[0], empleados[0], servicios[0], now + timedelta(days=1), now + timedelta(days=1, hours=1), 'confirmada', 1),
            (clientes[1], empleados[1], servicios[2], now + timedelta(days=2), now + timedelta(days=2, hours=2), 'pendiente', 2),
            (clientes[2], empleados[2], servicios[3], now - timedelta(days=1), now - timedelta(days=1) + timedelta(hours=1), 'completada', 1),
            (clientes[3], empleados[0], servicios[1], now - timedelta(days=3), now - timedelta(days=3) + timedelta(hours=1), 'completada', 3),
            (clientes[4], empleados[1], servicios[4], now + timedelta(days=5), now + timedelta(days=5, hours=1), 'cancelada', 4),
        ]
        for cliente, empleado, servicio, inicio, fin, estado, turno in citas_data:
            Cita.objects.get_or_create(
                cliente=cliente, empleado=empleado, servicio=servicio, fecha_inicio=inicio,
                defaults={'fecha_fin': fin, 'estado': estado, 'turno': turno}
            )
        self.stdout.write('  [OK] 5 citas')
 
        # Ventas
        ventas_data = [
            (clientes[0], empleados[3], None, 'efectivo', 'servicio', 'pagada', None, 220.00),
            (clientes[2], empleados[3], productos[0], 'tarjeta', 'producto', 'pagada', None, 145.00),
            (clientes[3], empleados[3], None, 'transferencia', 'servicio', 'pendiente', date.today() + timedelta(days=7), 650.00),
            (clientes[5], empleados[3], productos[3], 'efectivo', 'producto', 'pagada', None, 80.00),
        ]
        for cliente, empleado, producto, metodo, tipo, estatus, vigencia, total in ventas_data:
            Venta.objects.get_or_create(
                cliente=cliente, empleado=empleado, total=total,
                defaults={
                    'producto': producto,
                    'metodo_pago': metodo,
                    'tipo': tipo,
                    'estatus': estatus,
                    'vigencia_hasta': vigencia,
                }
            )
        self.stdout.write('  [OK] 4 ventas')
 
        # Compras
        compras_data = [
            (empleados[4], productos[0], 'Distribuidora Loreal México', 2450.00, 10),
            (empleados[4], productos[1], 'Wella Professionals MX', 1800.00, 8),
        ]
        for empleado, producto, proveedor, precio_unitario, cantidad in compras_data:
            Compra.objects.get_or_create(
                empleado=empleado, proveedor=proveedor,
                defaults={
                    'producto': producto,
                    'precio_unitario': precio_unitario,
                    'cantidad': cantidad,
                }
            )
        self.stdout.write('  [OK] 2 compras')
 
        # Cotizaciones
        cotizaciones_data = [
            (clientes[6], servicios[5], None, date.today() + timedelta(days=15), 'vigente'),
            (clientes[7], servicios[2], None, date.today() + timedelta(days=10), 'vigente'),
            (clientes[1], None, productos[1], date.today() - timedelta(days=5), 'vencida'),
        ]
        for cliente, servicio, producto, vigencia, estado in cotizaciones_data:
            Cotizacion.objects.get_or_create(
                cliente=cliente, vigencia=vigencia,
                defaults={
                    'servicio': servicio,
                    'producto': producto,
                    'estado': estado,
                }
            )
        self.stdout.write('  [OK] 3 cotizaciones')
 
        self.stdout.write(self.style.SUCCESS('\nBase de datos poblada correctamente.'))
 
