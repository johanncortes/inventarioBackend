# SGIL — Sistema de Gestión de Inventario de Laboratorios (Backend)

Backend de la EVA2: API REST con Django REST Framework.
Equipo: Johann Cortés, Martín Zepeda Puelles, Diego Cortés.
Asignatura: Programación de Aplicaciones — Unidad III.

---

## Cómo levantar el proyecto

### Requisitos previos

- Python 3.11 o 3.12 (con "Add python.exe to PATH" marcado en Windows)
- MySQL Community Server + Workbench (servicio MySQL80 corriendo)

### Windows (PowerShell)

```powershell
# 1. En MySQL Workbench: conectarse como root, abrir bd/crear_bd.sql y ejecutarlo (rayo ⚡)
# 2. En la terminal, dentro de la carpeta del repo:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata usuarios inventario reservas incidencias
python manage.py runserver
# 3. Abrir http://127.0.0.1:8000/api/ e iniciar sesión con "Log in"
```

### macOS

```bash
python3 -m venv venv
source venv/bin/activate
# (el resto igual que Windows)
```

### Usuarios de prueba (contraseña: `prueba123`)

| Usuario | Rol |
|---|---|
| `pedro.soto` | Encargado |
| `ana.morales` | Docente |
| `luis.torres` | Departamento |

---

## Endpoints de la API

Página de inicio: **http://127.0.0.1:8000/api/**

### Johann — Usuarios e inventario

| Método | URL | Descripción |
|---|---|---|
| POST | `/api-auth/login/` | Login de la API navegable |
| POST | `/api/token/` | Obtener token (Unidad IV) |
| GET | `/api/usuarios/yo/` | Perfil del usuario conectado |
| GET/POST | `/api/usuarios/` | Listar y crear usuarios (encargado) |
| GET/POST | `/api/categorias/` | CRUD de categorías |
| GET/POST | `/api/torres/` | CRUD de torres |
| GET/POST | `/api/salas/` | CRUD de salas |
| GET/POST | `/api/recursos/` | Inventario: listar y crear |
| GET/PATCH/DELETE | `/api/recursos/{id}/` | Ficha, editar y eliminar recurso |
| GET/POST | `/api/unidades/` | CRUD de unidades (n° de serie) |
| GET/POST | `/api/movimientos/` | Historial y registrar movimientos |

Filtros de recursos: `?search=&categoria=&sala=&sala__torre=&estado=&fecha_adquisicion__gte=&fecha_adquisicion__lte=&page=`

### Martín — Reservas

| Método | URL | Descripción |
|---|---|---|
| GET | `/api/reservas/` | Listar reservas (docente: solo las suyas; encargado y departamento: todas) |
| POST | `/api/reservas/` | Crear reserva (docente) |
| GET | `/api/reservas/{id}/` | Ver detalle de una reserva |
| PATCH | `/api/reservas/{id}/` | Editar o cancelar (`{"cancelada": true}`) |
| GET | `/api/disponibilidad/` | Unidades libres y salas disponibles en un horario |

Filtros de reservas: `?fecha=&recurso=&sala=&cancelada=&search=`

Parámetros de disponibilidad: `?recurso=<id>&fecha=<YYYY-MM-DD>&hora_inicio=<HH:MM>&hora_fin=<HH:MM>`

### Diego — Incidencias y alertas

| Método | URL | Descripción |
|---|---|---|
| GET/POST | `/api/incidencias/` | Listar y registrar incidencias |
| GET/PATCH | `/api/incidencias/{id}/` | Ver y avanzar estado |
| GET | `/api/alertas/` | Panel de alertas calculadas |

Filtros de alertas: `?tipo=reparacion|mantencion|reposicion`

---

