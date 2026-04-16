# Estética Glamour Style

## Descripción
Sistema de gestión para un salón de belleza desarrollado con Django y PostgreSQL.
Permite administrar las operaciones diarias del negocio desde una sola plataforma.

## Objetivo
Digitalizar y centralizar la gestión de clientes, empleados, servicios, productos,
citas, ventas, compras y cotizaciones de un salón de belleza.

## Funcionalidades principales
- Dashboard con estadísticas: total de clientes, citas del día y ventas del mes
- Gestión de Clientes: registro, búsqueda, edición y eliminación
- Gestión de Empleados: CRUD completo con roles (estilista, colorista, manicurista, etc.)
- Catálogo de Servicios: corte, color, tratamiento, uñas, maquillaje
- Catálogo de Productos: control de stock con alerta de stock bajo
- Citas: agendado con cliente, empleado y servicio asignado
- Ventas: registro con método de pago y estatus
- Compras: registro de compras a proveedores
- Cotizaciones: generación y seguimiento de cotizaciones por cliente
- Autenticación: login/logout con acceso protegido en todas las vistas

## Tecnologías utilizadas
- Python 3.11
- Django 5.0.2
- PostgreSQL 15
- Docker y Docker Compose
- Bootstrap 5
- Chart.js

## Requisitos previos
- Docker Desktop instalado y corriendo

## Instalación y ejecución
```bash
# 1. Clonar el repositorio
git clone https://github.com/Monroy1825/Estetica-Glamour-Style-.git
cd Estetica-Glamour-Style-

# 2. Configurar variables de entorno
cp .env.example .env

# 3. Levantar los contenedores
docker compose up --build -d

# 4. Aplicar migraciones
docker compose exec web python manage.py migrate

# 5. Cargar datos de prueba
docker compose exec web python manage.py populate_db

# 6. Abrir en el navegador
http://localhost:8000
```

## Credenciales de prueba
| Usuario | Contraseña |
|---------|------------|
| admin   | admin123   |

## Variables de entorno
| Variable | Descripción |
|----------|-------------|
| SECRET_KEY | Clave secreta de Django |
| DEBUG | Modo debug (True en desarrollo) |
| ALLOWED_HOSTS | Hosts permitidos |
| POSTGRES_DB | Nombre de la base de datos |
| POSTGRES_USER | Usuario de PostgreSQL |
| POSTGRES_PASSWORD | Contraseña de PostgreSQL |
| POSTGRES_HOST | Host de la base de datos |
| POSTGRES_PORT | Puerto de PostgreSQL |
