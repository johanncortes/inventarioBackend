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

Backend del **Sistema de Gestión de Inventario de Laboratorios (SGIL)** del Departamento de Ciencias Básicas, hecho con **Django 4.2 + Django REST Framework 3.16 + MySQL**.

Es el backend del mismo sistema de la EVA1. En esta etapa **no se conecta el frontend** (eso es la Unidad IV): todo se usa y se demuestra desde la **API navegable de DRF**, en el navegador.

Programación de Aplicaciones — Unidad III · Equipo: Johann Cortés, Martín Zepeda Puelles, Diego Cortés.

| Integrante | Área | Apps |
|---|---|---|
| Johann | Base del proyecto, usuarios e inventario | `sgil/`, `usuarios/`, `inventario/` |
| Martín | Reservas | `reservas/` |
| Diego | Incidencias y alertas | `incidencias/` |

El plan completo está en [docs/plan-eva2-backend.md](docs/plan-eva2-backend.md).

---

## 1. Requisitos

- **Python 3.11 o 3.12**. Django 4.2 no es compatible oficialmente con Python 3.13: si tienes la 3.13, instala también la 3.11 desde python.org.
- **MySQL Community Server 8** + **MySQL Workbench**. En Windows, instálalos con el *MySQL Installer*; anota la contraseña de `root` y deja el servicio **MySQL80** con inicio automático.
- Git / GitHub Desktop.

Funciona igual en **Windows y macOS**: el driver de MySQL es PyMySQL (no hay que compilar nada).

## 2. Instalación

### 2.1 Crear la base de datos (una sola vez, y cada vez que quieras dejarla limpia)

1. Abre MySQL Workbench y conéctate como `root`.
   - En la versión nueva de Workbench, si no aparece ninguna conexión, créala con el **+** junto a *Database Connections*: Host `127.0.0.1`, Port `3306`, User `root`.
2. Abre [bd/crear_bd.sql](bd/crear_bd.sql) (o copia su contenido en el editor) y ejecútalo con el **rayo ⚡**.
3. Crea la base `sgil_db` y el usuario `sgil` / `sgil123` que usa Django.

> ⚠️ El script **borra** la base `sgil_db` si ya existía. Úsalo también para dejarla limpia antes de la demo.

Alternativa por terminal (Windows):

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p -e "source bd/crear_bd.sql"
```

### 2.2 Levantar el proyecto

**Windows** (PowerShell, en la terminal de VS Code, dentro de la carpeta del repo):

```powershell
py -3.11 -m venv venv                 # crea el entorno virtual con Python 3.11
venv\Scripts\activate                 # debe aparecer (venv) al inicio de la línea
pip install -r requirements.txt
python manage.py migrate              # crea las tablas en MySQL
python manage.py loaddata usuarios inventario
python manage.py createsuperuser      # opcional, solo para entrar a /admin/
python manage.py runserver
```

**macOS:**

```bash
python3.11 -m venv venv
source venv/bin/activate
# el resto de los comandos es igual al de Windows
```

Después abre **http://127.0.0.1:8000/api/** e inicia sesión con **Log in** (arriba a la derecha).

### 2.3 Problemas típicos en Windows

| Síntoma | Solución |
|---|---|
| `venv\Scripts\activate` da error de "ejecución de scripts deshabilitada" | Una sola vez: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y volver a activar |
| `python` abre la Microsoft Store | Usar `py` en vez de `python`, o desactivar los "alias de ejecución de aplicaciones" de Python en Configuración de Windows |
| `Can't connect to MySQL server on 'localhost'` | El servicio no está corriendo: `services.msc` → **MySQL80** → Iniciar |
| `Access denied for user 'sgil'@'localhost'` | Falta ejecutar `bd/crear_bd.sql` |
| `cryptography is required for sha256_password or caching_sha2_password` | Falta `cryptography` en el venv: `pip install -r requirements.txt` con el venv activado |
| VS Code no reconoce Django (subrayado amarillo) | `Ctrl+Shift+P` → *Python: Select Interpreter* → el de `venv` |
| `loaddata` da error de clave duplicada | La base ya tenía datos: ejecuta de nuevo `bd/crear_bd.sql` → `migrate` → `loaddata` |

---

## 3. Usuarios de prueba

Todos tienen la contraseña **`prueba123`**. Se inicia sesión con el **correo**.

| Correo | Nombre | Rol |
|---|---|---|
| `encargado@prueba.cl` | Pedro Soto | Encargado de laboratorio |
| `docente@prueba.cl` | Prof. Ana Morales | Docente |
| `departamento@prueba.cl` | Luis Sergio Torres | Departamento |
| `carlos.fuentes@prueba.cl` | Prof. Carlos Fuentes | Docente |
| `jorge.paredes@prueba.cl` | Prof. Jorge Paredes | Docente |

Los datos del inventario son los mismos del front (`src/data/` de la EVA1): 6 categorías, torres B y C, 5 salas, 10 recursos (con 101 unidades con número de serie) y 4 movimientos del historial. Incluye un insumo bajo su stock mínimo (guantes de nitrilo) para probar las alertas.

---

## 4. Autenticación y permisos

- **Sesión:** el botón **Log in** de la API navegable.
- **Token** (para el front en la Unidad IV): `POST /api/token/` con `username` (el correo) y `password` → `{"token": "..."}`. Después se manda el encabezado `Authorization: Token <clave>`.
- Sin sesión, todos los endpoints responden **403** (salvo la página `/api/`, que solo muestra los enlaces).

| Recurso de la API | Sin sesión | Docente | Departamento | Encargado |
|---|---|---|---|---|
| Categorías, torres, salas, recursos, unidades | 403 | Solo leer | Solo leer | CRUD completo |
| Movimientos (historial) | 403 | 403 | Solo leer | Leer y registrar (no editar ni borrar) |
| Usuarios | 403 | Solo `/yo/` | Solo `/yo/` | Crear, cambiar rol, desactivar |

Los permisos están en [usuarios/permisos.py](usuarios/permisos.py).

---

## 5. Endpoints

Todos los listados están **paginados de a 9** (`?page=2`) y aceptan **búsqueda** (`?search=`) y **orden** (`?ordering=campo`, o `-campo` para invertir).

### 5.1 Usuarios (Johann)

| Método | URL | Qué hace |
|---|---|---|
| POST | `/api/token/` | Entrega el token de un usuario |
| GET | `/api/usuarios/yo/` | Datos y rol del usuario conectado (cualquier rol) |
| GET, POST | `/api/usuarios/` | Listar y crear usuarios (con `contrasena`) |
| GET, PUT, PATCH | `/api/usuarios/{id}/` | Ver, cambiar rol, desactivar (`"activo": false`). No hay DELETE |

Filtros: `?perfil__rol=docente`, `?is_active=true`, `?search=morales`.

Reglas: el correo no se repite (CA-15.2); un usuario desactivado no puede iniciar sesión (CA-15.3); siempre debe quedar al menos un encargado activo.

### 5.2 Inventario (Johann)

| Método | URL | Qué hace |
|---|---|---|
| GET, POST | `/api/categorias/` | Categorías con descripción breve (RF-08) |
| GET, POST | `/api/torres/` | Torres (una letra: B, C…) |
| GET, POST | `/api/salas/` | Salas; el código (`B307`) se arma solo. Filtro `?torre=` |
| GET, POST | `/api/recursos/` | Inventario (HU-01, HU-11, HU-12, HU-13) |
| GET, POST | `/api/unidades/` | Unidades con número de serie. Filtros `?recurso=` y `?estado=` |
| GET, POST | `/api/movimientos/` | Historial (HU-06) y registro de cambios de estado, entradas y salidas (HU-02, HU-14) |

Cada uno tiene además `/{id}/` para ver (GET), editar (PUT/PATCH) y eliminar (DELETE), salvo los movimientos, que **no se editan ni se borran** (RNF-06).

**Filtros del inventario** (`/api/recursos/`):

| Filtro | Ejemplo |
|---|---|
| Buscar por nombre, marca o n° de serie (sin importar tildes ni mayúsculas) | `?search=multimetro` |
| Categoría | `?categoria=1` |
| Sala (laboratorio) | `?sala=2` |
| Torre | `?sala__torre=1` |
| Estado (recursos con al menos 1 unidad en ese estado) | `?estado=danado` |
| Antigüedad (fecha de adquisición entre dos fechas) | `?fecha_adquisicion__gte=2024-01-01&fecha_adquisicion__lte=2024-12-31` |
| Orden | `?ordering=-fecha_adquisicion` |

**Ficha de un recurso** (`GET /api/recursos/{id}/`): trae el nombre de la categoría, la sala y la torre, el código de ubicación (`B307-B1-M2`), las cantidades por estado, la cantidad total y sus unidades anidadas.

**Registrar un movimiento** (`POST /api/movimientos/`). El usuario y la fecha se guardan solos. Los equipos e instrumentos se mueven de a una unidad (`unidad`); los insumos y reactivos, por cantidad (`estado_anterior` + `cantidad`):

| Tipo | Campos | Qué hace |
|---|---|---|
| `cambio_estado` | `recurso`, `estado_nuevo`, `motivo` + (`unidad` o `estado_anterior` y `cantidad`) | Pasa unidades de un estado a otro |
| `entrada` | `recurso`, `subtipo` (`adquisicion`, `prestamo`, `reposicion`), `fecha_movimiento` + (`numero_unidad_nueva` o `cantidad`) | Agrega unidades en "disponible" |
| `salida` | `recurso`, `subtipo` (`dano_reparable` → mantención, `dano_irreparable` → dado de baja), `motivo` + (`unidad` o `estado_anterior` y `cantidad`) | Saca unidades por daño |

Al cambiar la sala, la bodega o el mueble de un recurso (`PATCH /api/recursos/{id}/`), el **cambio de ubicación queda solo en el historial** (CA-11.3).

Reglas que valida la API:
- La fecha de adquisición no puede ser futura (CA-13.1).
- El número de serie no se repite dentro de un recurso (CA-12.2).
- No se mueven más unidades de las que hay en ese estado.
- Una unidad dada de baja ya no cambia de estado.
- Las cantidades y el estado de las unidades **solo cambian con un movimiento**, para que todo quede en el historial.
- No se puede eliminar una categoría, sala o torre que todavía tiene recursos o salas (responde 400 con el motivo).

**Carga desde Excel:** el front lee el Excel y hace un `POST /api/recursos/` por cada fila.

<!-- ===== Reservas (Martín) ===== -->
### 5.3 Reservas (Martín)

_Pendiente: endpoints de reservas y disponibilidad._
<!-- ===== Fin Reservas (Martín) ===== -->

<!-- ===== Incidencias (Diego) ===== -->
### 5.4 Incidencias y alertas (Diego)

_Pendiente: endpoints de incidencias y alertas._
<!-- ===== Fin Incidencias (Diego) ===== -->

---

## 6. Estructura del proyecto

```
├── manage.py
├── requirements.txt
├── bd/crear_bd.sql           # crea la base y el usuario de MySQL
├── docs/plan-eva2-backend.md # plan del equipo
├── sgil/                     # configuración: settings.py, urls.py, raiz.py (página /api/)
├── usuarios/                 # Perfil (rol), permisos por rol, CRUD de usuarios, /yo/
├── inventario/               # categorías, torres, salas, recursos, unidades e historial
│   ├── ubicacion.py          #   arma el código de ubicación "B307-B1-M2"
│   └── movimientos.py        #   reglas de cambio de estado, entradas y salidas
├── reservas/                 # Martín
└── incidencias/              # Diego
```

Relaciones entre modelos:

```
User ──1:1── Perfil (rol: encargado | docente | departamento)

Torre ──< Sala ──< Recurso >── Categoria
                     │
                     ├──< Unidad (n° de serie, estado)
                     └──< Movimiento >── User   (historial)
```

## 7. Antes de subir cambios

```powershell
python manage.py check                       # sin errores
python manage.py makemigrations --check      # no debe quedar nada sin migrar
```

Para probar en una base limpia: `bd/crear_bd.sql` → `migrate` → `loaddata`.
