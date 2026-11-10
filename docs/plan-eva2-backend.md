# Plan de implementación — EVA2: API REST con Django REST Framework

Equipo: **Johann Cortés, Martín Zepeda Puelles, Diego Cortés**.
Asignatura: Programación de Aplicaciones (prof. Luis Rojas Rubio) — Unidad III, Backend.

Es el **backend del mismo sistema de la EVA1** (SGIL, inventario de laboratorios de Ciencias Básicas). Solo backend: **no se conecta el frontend** (eso es la Unidad IV). Todo se demuestra desde la **interfaz navegable de DRF** (no Postman ni curl).

Cada integrante tiene un **área** (la misma del plan de la EVA1) y **al menos 10 commits propios e incrementales** (la meta es ~14 para tener margen).

| Integrante | Área | Apps de Django | Modelos | Historias |
|---|---|---|---|---|
| **Johann** | Base del proyecto, usuarios e inventario | `sgil/`, `usuarios/`, `inventario/` | Perfil, Categoria, Torre, Sala, Recurso, Unidad, Movimiento | HU-01, HU-02, HU-06, HU-11 a HU-15 |
| **Martín** | Reservas | `reservas/` | Reserva | HU-03, HU-07, HU-08, "Mis reservas" |
| **Diego** | Incidencias y alertas | `incidencias/` | Incidencia (+ alertas calculadas) | HU-04, HU-05, HU-09, HU-10 |

---

## 1. Qué pide la pauta y dónde se cumple

| Criterio (ponderación) | Cómo lo cumplimos | Quién lo demuestra |
|---|---|---|
| Funcionalidad y alcance EVA1 (30%) | Cada pantalla de la EVA1 tiene su modelo y endpoint (tabla de la sección 3). CRUD completo en Categoria, Torre, Sala, Recurso y Unidad. | Los tres |
| Defensa oral (20%) | Cada uno explica su app y **también** las demás (sección 11). | Los tres |
| Modelado y relaciones (15%) | FK entre Recurso–Categoria–Sala–Torre, Unidad–Recurso, Reserva–Recurso/Sala/Usuario, Incidencia–Recurso/Unidad/Usuario, Movimiento–Recurso/Unidad/Usuario y Perfil–User (1 a 1). Los serializers muestran los nombres relacionados y las unidades anidadas. | Johann (modelo), Martín y Diego (sus FK) |
| Autenticación y permisos (15%) | Sesión (botón "Log in" de la API navegable) + token (para la Unidad IV). Sin sesión: 403. Docente: lee y reserva. Departamento: lee inventario, incidencias y alertas. Encargado: todo. | Johann (base), Martín (dueño de la reserva), Diego (incidencias/alertas) |
| Filtrado, búsqueda y paginación (10%) | `django-filter` + `SearchFilter` + `OrderingFilter` en todos los listados; `PageNumberPagination` de **9 por página** (igual que CA-01.3). | Los tres |
| GitHub (10%) | `main` funcional, ramas por bloque, PR con revisión cruzada, ≥10 commits por persona. | Los tres |

---

## 2. Tecnologías y estructura

- **Python + Django 4.2 + Django REST Framework 3.16** (las mismas versiones del Laboratorio 6).
- **django-filter** (filtros con formulario en la API navegable).
- **MySQL Community Server + MySQL Workbench**, como en la clase del viernes. Driver: **PyMySQL** + **cryptography** (no necesita compilar nada en macOS ni Windows). Si el viernes el profe usó `mysqlclient` y les funcionó a los tres, usen ese.
- Editor: **VS Code o Google Antigravity**. Commits: **GitHub Desktop**.

Repositorio nuevo (sugerencia de nombre: `Proyecto_C.Basicas_API`). Lo crea Diego en su cuenta, como los anteriores, e invita a Johann y Martín; Johann sube la estructura base.

```
Proyecto_C.Basicas_API/
├── manage.py
├── requirements.txt
├── README.md                 # cómo levantar el proyecto + tabla de endpoints
├── CLAUDE.md                 # reglas de código para la IA (sección 6)
├── bd/crear_bd.sql           # crea la base y el usuario de MySQL
├── docs/plan-eva2-backend.md # este archivo
├── sgil/                     # configuración (settings.py, urls.py)
├── usuarios/                 # Johann: Perfil, permisos, usuarios
├── inventario/               # Johann: categorías, salas, recursos, unidades, historial
├── reservas/                 # Martín
└── incidencias/              # Diego (incluye alertas.py)
```

**¿Por qué una app por área?** Cada app tiene sus propios `models.py`, `serializers.py`, `views.py`, `urls.py` y **su propia carpeta de migraciones**. En el Lab 6 todo estaba en `catalogo/` y chocaron las migraciones ("dejo la migración de Oferta como 0002"). Así no pasa.

### Relaciones entre modelos

```
User ──1:1── Perfil (rol: encargado | docente | departamento)

Torre ──< Sala ──< Recurso >── Categoria
                     │
                     ├──< Unidad (n° de serie, estado)
                     ├──< Movimiento >── User        (historial: estado, entrada, salida, ubicación)
                     ├──< Reserva >── Sala, User      (Martín)
                     └──< Incidencia >── Unidad, User (Diego)

Alertas: no se guardan, se CALCULAN desde Recurso y Unidad (igual que en el front).
```

`──<` = "uno a muchos" (una FK en el modelo de la derecha). Los campos van en `snake_case` (estilo de Python): `fecha_adquisicion`, `hora_inicio`. En la Unidad IV el front se adapta a esos nombres.

---

## 3. Alcance: cada funcionalidad de la EVA1 → su endpoint

Esta tabla es la que se muestra en la **presentación del alcance** (1–2 min).

| Funcionalidad comprometida en la EVA1 | Modelo | Endpoint | Resp. |
|---|---|---|---|
| Login con 3 roles y usuario conectado | User + Perfil | `/api-auth/login/`, `/api/usuarios/yo/`, `/api/token/` | Johann |
| Inventario: buscador, filtros (categoría, torre, sala, estado, antigüedad), 9 por página | Recurso | `GET /api/recursos/?search=&categoria=&sala__torre=&estado=&page=` | Johann |
| Ficha del recurso con sus unidades | Recurso + Unidad | `GET /api/recursos/{id}/` | Johann |
| Agregar / editar / eliminar recurso (ubicación, n° de serie, fecha de adquisición) | Recurso, Unidad | `/api/recursos/`, `/api/unidades/` | Johann |
| Cambiar estado, entradas y salidas | Movimiento | `POST /api/movimientos/` | Johann |
| Historial del recurso (no se edita ni borra) | Movimiento | `GET /api/movimientos/?recurso={id}` | Johann |
| Cambiar ubicación (queda en el historial) | Recurso + Movimiento | `PATCH /api/recursos/{id}/` | Johann |
| Configuración: categorías (con descripción), torres y salas | Categoria, Torre, Sala | `/api/categorias/`, `/api/torres/`, `/api/salas/` | Johann |
| Configuración: usuarios (agregar, cambiar rol, desactivar) | User + Perfil | `/api/usuarios/` | Johann |
| Carga desde Excel | Recurso | El front lee el Excel y hace `POST /api/recursos/` por fila (se declara así) | Johann |
| Reservar, "Mis reservas", cancelar | Reserva | `/api/reservas/` | Martín |
| Unidades disponibles y salas libres en un horario | (calculado) | `GET /api/disponibilidad/?recurso=&fecha=&hora_inicio=&hora_fin=` | Martín |
| Registrar incidencias y avanzar su estado | Incidencia | `/api/incidencias/` | Diego |
| Panel de alertas con contador y filtro por tipo | (calculado) | `GET /api/alertas/?tipo=` | Diego |

🔶 **Decidir como grupo** (y declararlo en la demo): **recuperar contraseña** y **correos** (RF-09) dependen de un servicio de correo. Opción simple: `EMAIL_BACKEND` de consola de Django, que "envía" el correo imprimiéndolo en la terminal (ver extras opcionales de Martín y Johann). Si no alcanza, se declaran fuera de esta etapa.

### Permisos por rol

| Recurso de la API | Sin sesión | Docente | Departamento | Encargado |
|---|---|---|---|---|
| Categorías, torres, salas, recursos, unidades | 403 | Solo leer | Solo leer | CRUD completo |
| Movimientos (historial) | 403 | 403 | Solo leer | Leer y crear (no editar ni borrar) |
| Usuarios | 403 | Solo `/yo/` | Solo `/yo/` | Crear, cambiar rol, desactivar |
| Reservas | 403 | Crear; ve y edita **solo las suyas** | Leer todas | Leer todas y cancelar |
| Incidencias | 403 | 403 | Solo leer | Crear y avanzar estado (no borrar) |
| Alertas | 403 | 403 | Leer | Leer |

---

## 4. Reglas para no pisarnos

1. **Cada uno trabaja en su app.** Archivos compartidos: `sgil/settings.py`, `sgil/urls.py`, `requirements.txt`, `README.md` y `usuarios/permisos.py`. Antes de tocarlos se avisa en el grupo, el cambio va en un commit pequeño aparte, y se usan los mismos marcadores del Lab 6: `# ===== Reservas (Martín) =====` … `# ===== Fin Reservas (Martín) =====`.
2. **Migraciones:** cada uno genera solo las de su app (`python manage.py makemigrations reservas`). Nunca se editan ni se borran migraciones ya subidas, ni las de otra app. Antes de generar una migración: **Pull** de `main`.
3. **Una rama por bloque**, siempre desde `main` actualizado (GitHub Desktop: *Fetch origin* → *Pull* → *New branch*).
4. **Antes de cada commit:** `python manage.py check` sin errores, `runserver` y probar el endpoint en el navegador.
5. **Antes del PR:** `python manage.py makemigrations --check` (no debe quedar nada sin migrar) y probar en una base limpia (sección 10).
6. **Revisión cruzada de PR** (igual que en la EVA1): a Johann lo revisa Martín, a Martín Diego y a Diego Johann. El merge lo hace quien revisa, en GitHub.
7. **Un commit = un avance que funciona.** Nada de subir todo de una vez: la pauta no acepta commits que suban todo el trabajo junto. En GitHub Desktop se marcan solo los archivos de ese paso antes de *Commit*.
8. **Identidad de Git:** en GitHub Desktop (*Settings → Git*) el nombre y el correo deben ser los de su cuenta de GitHub; si no, los commits no se cuentan como suyos. Cada uno hace **sus** commits desde **su** computador.
9. **Nunca subir:** `venv/`, `__pycache__/`, `.env`, `db.sqlite3` (van en `.gitignore`).

---

## 5. Orden de trabajo

| Fase | Johann | Martín | Diego |
|---|---|---|---|
| **0. Base** (primero; bloquea a los demás) | J1–J7: proyecto, MySQL, DRF, Perfil, permisos y modelos de inventario | Instala MySQL, corre `bd/crear_bd.sql`, clona y levanta la base de Johann | Igual que Martín |
| **1** | J8–J13: CRUD de configuración y recursos, filtros, validaciones | M1–M5: modelo y CRUD de Reserva | D1–D5: modelo y CRUD de Incidencia |
| **2** | J14–J16: historial (Movimiento) | M6–M11: validaciones de horario, stock, sala; permisos y cancelar | D6–D9: validaciones, permisos, estados y filtros |
| **3** | J17–J19: usuarios y datos de prueba | M12–M15: filtros, disponibilidad, datos de prueba | D10–D14: alertas y datos de prueba |
| **4. Cierre** (los tres) | Base limpia, ensayo de la demo con el guion y las preguntas (secciones 10 y 11) | | |

**Importante:** Martín y Diego necesitan `Recurso`, `Unidad`, `Sala` y los permisos de `usuarios/permisos.py` para sus FK y sus vistas. Por eso el PR de la fase 0 se integra a `main` **antes que todo**. Mientras tanto, ellos dejan MySQL listo y leen este plan.

> Completen aquí la fecha de la demo: **____** · Fecha límite fase 0: **____** · Fecha límite fases 1–3: **____**

---

## 6. Cómo escribir el código (copiar a `CLAUDE.md`)

- Mismo estilo del Lab 6: **`ModelViewSet` + `DefaultRouter`** para los CRUD. **`APIView`** solo para lo calculado (disponibilidad, alertas, `/yo/`). Así mostramos las dos formas que pide la pauta.
- Código **simple**, de estudiante de pregrado: `if/else` claros, funciones cortas, nada de metaclases, mixins propios ni herencias complicadas.
- La lógica (validar, calcular disponibilidad, aplicar un movimiento, calcular alertas) va en archivos aparte (`disponibilidad.py`, `movimientos.py`, `alertas.py`) o en el `validate()` del serializer, no metida en la vista.
- Nombres en **español** (`fecha_adquisicion`, `unidades_disponibles`).
- **Comentarios en español** en todos los archivos: al inicio, qué hace el archivo y qué HU/RF cubre; antes de cada clase o función, qué hace; y el **porqué** de lo que no es obvio (qué hace `source=`, por qué `PROTECT`, qué hace `perform_create`).
- No instalar paquetes fuera de `requirements.txt` sin preguntar al grupo.

---

## 7. Plan de Johann: base, usuarios e inventario

### Fase 0 — Base (PR `feature/base-proyecto`, se integra primero)

| # | Mensaje de commit | Archivos | Qué se aprende / explica |
|---|---|---|---|
| J1 | `chore: crea el proyecto Django sgil con requirements y .gitignore` | `manage.py`, `sgil/`, `requirements.txt`, `.gitignore`, `.gitattributes`, `CLAUDE.md` | `startproject`, entorno virtual, `pip freeze > requirements.txt` |
| J2 | `chore: configura MySQL, idioma y zona horaria` | `sgil/settings.py`, `sgil/__init__.py`, `bd/crear_bd.sql` | `DATABASES` con `ENGINE` mysql; `pymysql.install_as_MySQLdb()`; `es-cl` y `America/Santiago` |
| J3 | `chore: configura DRF con autenticación, filtros y paginación de 9` | `settings.py`, `sgil/urls.py` | Bloque `REST_FRAMEWORK` (abajo); `api-auth/` para el botón "Log in"; `api/token/` |
| J4 | `feat(usuarios): crea el modelo Perfil con el rol del usuario` | `usuarios/models.py`, migración, `admin.py` | `OneToOneField` con `User`; `choices`; Perfil dentro del admin del usuario (`StackedInline`) |
| J5 | `feat(usuarios): agrega permisos por rol` | `usuarios/permisos.py` | `obtener_rol(user)`, `EsEncargado`, `EsEncargadoOSoloLectura`, `EsEncargadoODepartamento`; `has_permission` y `SAFE_METHODS` |
| J6 | `feat(inventario): crea los modelos Categoria, Torre y Sala` | `inventario/models.py`, migración | `unique=True`; `Sala.codigo` ("B307") armado en `save()`; `__str__` |
| J7 | `feat(inventario): crea los modelos Recurso y Unidad con sus relaciones` | `models.py`, migración, `admin.py` | `ForeignKey` y `related_name='unidades'`; cantidades por estado para insumos; `unique_together` (recurso, número) → CA-12.2 |

Configuración de J2 y J3 (referencia):

```python
# sgil/settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'sgil_db',
        'USER': 'sgil',
        'PASSWORD': 'sgil123',   # solo es la base local de cada uno
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',  # API navegable
        'rest_framework.authentication.TokenAuthentication',    # para la Unidad IV
    ],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 9,  # igual que el inventario del front (CA-01.3)
}
# INSTALLED_APPS: 'rest_framework', 'rest_framework.authtoken', 'django_filters', 'usuarios', 'inventario'
```

```sql
-- bd/crear_bd.sql  (se ejecuta en MySQL Workbench con el usuario root)
DROP DATABASE IF EXISTS sgil_db;
CREATE DATABASE sgil_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'sgil'@'localhost' IDENTIFIED BY 'sgil123';
GRANT ALL PRIVILEGES ON sgil_db.* TO 'sgil'@'localhost';
GRANT ALL PRIVILEGES ON test_sgil_db.* TO 'sgil'@'localhost';  -- por si hacemos tests
FLUSH PRIVILEGES;
```

### Fases 1 a 3

| # | Rama | Mensaje de commit | Archivos | Qué se aprende / explica |
|---|---|---|---|---|
| J8 | `feature/inventario-configuracion` | `feat(inventario): agrega serializers y ViewSets de categorías, torres y salas` | `serializers.py`, `views.py` | `ModelSerializer`; `ModelViewSet` con `EsEncargadoOSoloLectura` (RF-08, RNF-05) |
| J9 | `feature/inventario-configuracion` | `feat(inventario): conecta el router de inventario a /api/` | `inventario/urls.py`, `sgil/urls.py` | `DefaultRouter` y `include()` |
| J10 | `feature/inventario-recursos` | `feat(inventario): agrega serializer de Recurso con categoría, sala y unidades anidadas` | `serializers.py` | `source='categoria.nombre'`, `UnidadSerializer(many=True, read_only=True)`, `SerializerMethodField` para la cantidad total |
| J11 | `feature/inventario-recursos` | `feat(inventario): agrega CRUD de recursos y unidades` | `views.py`, `urls.py` | `RecursoViewSet` y `UnidadViewSet`; si el recurso tiene reservas o incidencias, `ProtectedError` → respuesta 400 con mensaje (no error 500) |
| J12 | `feature/inventario-recursos` | `feat(inventario): agrega filtros, búsqueda y orden al listado de recursos` | `views.py` | `filterset_fields` (categoría, sala, torre, `fecha_adquisicion` gte/lte → HU-13), `search_fields` (nombre, marca, n° de serie), `ordering_fields`; filtro `estado` con `query_params` |
| J13 | `feature/inventario-recursos` | `feat(inventario): valida fecha no futura y número de serie único` | `serializers.py` | `validate_fecha_adquisicion` (CA-13.1); mensaje claro si se repite el número (CA-12.2) |
| J14 | `feature/inventario-historial` | `feat(inventario): crea el modelo Movimiento para el historial` | `models.py`, migración | Tipos: cambio de estado, entrada, salida, cambio de ubicación (CA-06.1); `auto_now_add`; FK al usuario |
| J15 | `feature/inventario-historial` | `feat(inventario): aplica cambios de estado, entradas y salidas al registrar un movimiento` | `movimientos.py`, `serializers.py`, `views.py` | `validate()`: no mover más unidades de las que hay; daño irreparable → dado de baja (HU-02, HU-14); `perform_create` guarda el usuario |
| J16 | `feature/inventario-historial` | `feat(inventario): registra el cambio de ubicación y bloquea editar o borrar el historial` | `views.py` | `perform_update` compara la ubicación y crea el Movimiento (CA-11.3); `http_method_names` sin put/patch/delete (RNF-06); orden `-fecha` (CA-06.3) |
| J17 | `feature/usuarios` | `feat(usuarios): agrega CRUD de usuarios para el encargado` | `usuarios/serializers.py`, `views.py`, `urls.py` | Crear User + Perfil con `set_password`; correo único (CA-15.2); desactivar con `is_active` (Django ya impide su login → CA-15.3); sin delete |
| J18 | `feature/usuarios` | `feat(usuarios): agrega /api/usuarios/yo/ con el perfil del usuario conectado` | `views.py`, `urls.py` | `APIView` con `request.user` |
| J19 | `feature/datos-prueba` | `chore: agrega datos de prueba de usuarios e inventario` | `usuarios/fixtures/usuarios.json`, `inventario/fixtures/inventario.json` | `loaddata`; los mismos datos de `src/data/` del front (Pedro Soto, Prof. Ana Morales, Luis Sergio Torres; contraseña `prueba123`) |
| J20 | `feature/datos-prueba` | `docs: completa el README con instalación, base de datos y endpoints de inventario` | `README.md` | Pasos de la sección 7.1 |

Extra opcional: `POST /api/usuarios/cambiar_contrasena/` (`APIView` con `check_password` / `set_password`) para respaldar "cambiar contraseña" del front.

**Demo de Johann:** sin sesión → 403 en `/api/recursos/`. Login como docente → ve el listado pero el POST da 403. Login como encargado → crea una categoría y un recurso, filtra por categoría, busca "multímetro", pasa a la página 2, mueve el recurso de sala y muestra el movimiento en el historial, registra la salida por daño irreparable de una unidad (queda "dado de baja") y elimina el recurso de prueba.

### 7.1 Cómo levantar el proyecto (va al README)

El proyecto tiene que funcionar igual en **Windows y macOS**, porque cada uno trabaja en su equipo y la demo puede ser en cualquiera. Por eso se usa PyMySQL (no hay que compilar nada) y nunca se escriben rutas como `C:\...` en el código: en `settings.py` siempre `BASE_DIR / 'carpeta'`.

**Windows (PowerShell en la terminal de VS Code o Antigravity)**

Antes de empezar:
- Instalar Python 3.11 o 3.12 desde python.org, marcando **"Add python.exe to PATH"**.
- Instalar MySQL con el **MySQL Installer**: *Server* + *Workbench*. Anotar la contraseña de `root` y dejar el servicio **MySQL80** con inicio automático.

```powershell
# 1. En MySQL Workbench: conectarse como root, abrir bd/crear_bd.sql y ejecutarlo (rayo ⚡)
# 2. En la terminal, dentro de la carpeta del repo:
python -m venv venv                  # si "python" no existe, usar: py -m venv venv
venv\Scripts\activate                # debe aparecer (venv) al inicio de la línea
pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata usuarios inventario reservas incidencias
python manage.py createsuperuser     # opcional, para el /admin/
python manage.py runserver
# 3. Abrir http://127.0.0.1:8000/api/ e iniciar sesión con "Log in" (arriba a la derecha)
```

Problemas típicos en Windows:

| Síntoma | Solución |
|---|---|
| `venv\Scripts\activate` da error de "ejecución de scripts deshabilitada" | Una sola vez: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y volver a activar |
| `python` abre la Microsoft Store | Usar `py` en vez de `python`, o desactivar los "alias de ejecución de aplicaciones" de Python en Configuración de Windows |
| `Can't connect to MySQL server on 'localhost'` | El servicio no está corriendo: `services.msc` → **MySQL80** → Iniciar |
| `cryptography is required for sha256_password or caching_sha2_password` | Falta `cryptography` en el venv: `pip install -r requirements.txt` con el venv activado |
| VS Code no reconoce Django (subrayado amarillo) | `Ctrl+Shift+P` → *Python: Select Interpreter* → el de `venv` |

**macOS**

```bash
python3 -m venv venv
source venv/bin/activate
# (el resto de los comandos es igual al de Windows)
```

**Saltos de línea (Windows y Mac en el mismo repo):** en J1 se agrega un `.gitattributes` con la línea `* text=auto`. Así GitHub Desktop no marca todos los archivos como cambiados solo porque Windows usa otro tipo de salto de línea.

---

## 8. Plan de Martín: Reservas

| # | Rama | Mensaje de commit | Archivos | Qué se aprende / explica |
|---|---|---|---|---|
| M1 | `feature/reservas-modelo` | `feat(reservas): crea la app reservas y la registra en settings` | `reservas/`, `settings.py` (archivo compartido: avisar) | `startapp`; `INSTALLED_APPS` |
| M2 | `feature/reservas-modelo` | `feat(reservas): crea el modelo Reserva relacionado con recurso, sala y docente` | `models.py`, migración | FK a otra app con texto (`'inventario.Recurso'`); `on_delete=PROTECT` (no se borra un recurso con reservas) |
| M3 | `feature/reservas-modelo` | `feat(reservas): agrega ReservaSerializer con recurso, sala y docente legibles` | `serializers.py` | `source='recurso.nombre'`, `source='sala.codigo'`, `source='docente.get_full_name'` |
| M4 | `feature/reservas-modelo` | `feat(reservas): agrega ReservaViewSet y lo conecta al router` | `views.py`, `urls.py`, `sgil/urls.py` | `ModelViewSet`, `DefaultRouter`, `include()` |
| M5 | `feature/reservas-modelo` | `feat(reservas): asigna automáticamente el docente conectado` | `views.py`, `serializers.py` | `perform_create` con `serializer.save(docente=self.request.user)`; `read_only_fields` |
| M6 | `feature/reservas-validaciones` | `feat(reservas): valida fecha no pasada y término posterior al inicio` | `serializers.py` | `validate()` y `ValidationError` (CA-03.3) |
| M7 | `feature/reservas-validaciones` | `feat(reservas): agrega función para saber si dos horarios se cruzan` | `reservas/disponibilidad.py` | `se_cruzan(inicio1, fin1, inicio2, fin2)` comparando horas |
| M8 | `feature/reservas-validaciones` | `feat(reservas): impide reservar más unidades de las disponibles en ese horario` | `disponibilidad.py`, `serializers.py` | `unidades_disponibles(recurso, fecha, inicio, fin)`: disponibles menos reservas que se cruzan (HU-07, HU-08) |
| M9 | `feature/reservas-validaciones` | `feat(reservas): impide usar una sala reservada por otro docente en ese horario` | `disponibilidad.py`, `serializers.py` | CA-08.3: el mismo docente sí puede reservar varios recursos para su sala |
| M10 | `feature/reservas-permisos` | `feat(reservas): el docente solo ve y edita sus propias reservas` | `views.py`, `reservas/permisos.py` | `get_queryset()` según el rol (RNF-08); `has_object_permission` (`EsDuenoOEncargado`) |
| M11 | `feature/reservas-permisos` | `feat(reservas): permite cancelar una reserva y muestra su estado` | `models.py` (+ migración), `serializers.py`, `views.py` | Campo `cancelada`; `SerializerMethodField` estado: Programada / En curso / Realizada / Cancelada (CA-03.4); sin delete (RNF-06) |
| M12 | `feature/reservas-filtros` | `feat(reservas): agrega filtros por fecha, recurso y sala, y búsqueda por asignatura` | `views.py` | `filterset_fields`, `search_fields`, `ordering = ['fecha', 'hora_inicio']` |
| M13 | `feature/reservas-disponibilidad` | `feat(reservas): agrega la vista de disponibilidad con unidades y salas libres` | `views.py`, `urls.py` | `APIView` con `request.query_params` (CA-03.2 y salas libres de RF-03) |
| M14 | `feature/reservas-datos` | `chore(reservas): registra Reserva en el admin y agrega datos de prueba` | `admin.py`, `fixtures/reservas.json` | Incluir el caso real: termómetros ocupados el 09/10 a las 08:30 (cambiar a una fecha futura) |
| M15 | `feature/reservas-datos` | `docs: documenta los endpoints de reservas en el README` | `README.md` (compartido, en su sección) | — |

Extra opcional (RF-09): al crear o cancelar, `send_mail()` con el backend de consola: el "correo" aparece en la terminal del `runserver`. Se demuestra en vivo.

**Demo de Martín:** login como docente. Reservar más termómetros de los que hay en ese horario → error claro. Elegir una sala ocupada por otro docente → error. Reservar con éxito. Mostrar que solo ve sus reservas, filtrar por fecha y cancelar una. Abrir `/api/disponibilidad/` con un horario. Login como encargado → ve las reservas de todos.

---

## 9. Plan de Diego: Incidencias y alertas

| # | Rama | Mensaje de commit | Archivos | Qué se aprende / explica |
|---|---|---|---|---|
| D1 | `feature/incidencias-modelo` | `feat(incidencias): crea la app incidencias y la registra en settings` | `incidencias/`, `settings.py` (compartido: avisar) | `startapp` |
| D2 | `feature/incidencias-modelo` | `feat(incidencias): crea el modelo Incidencia con recurso, unidad, docente presente y quien la registra` | `models.py`, migración | Varias FK; dos FK al mismo modelo `User` → `related_name` distinto; `choices` de estado |
| D3 | `feature/incidencias-modelo` | `feat(incidencias): agrega IncidenciaSerializer con nombres del recurso y los usuarios` | `serializers.py` | `source=`, campos de solo lectura |
| D4 | `feature/incidencias-modelo` | `feat(incidencias): agrega IncidenciaViewSet y lo conecta al router` | `views.py`, `urls.py`, `sgil/urls.py` | `ModelViewSet`, `DefaultRouter` |
| D5 | `feature/incidencias-modelo` | `feat(incidencias): guarda sola la fecha, quién la registra y el estado pendiente` | `models.py`, `views.py` | `auto_now_add`, `default='pendiente'`, `perform_create` (HU-10) |
| D6 | `feature/incidencias-validaciones` | `feat(incidencias): exige el detalle si hay personas afectadas y que la unidad sea del recurso` | `serializers.py` | `validate()` cruzando campos (HU-04, CA-12.4) |
| D7 | `feature/incidencias-validaciones` | `feat(incidencias): el encargado registra y el departamento solo consulta` | `incidencias/permisos.py`, `views.py` | Permiso propio con `obtener_rol()` de `usuarios/permisos.py`; el docente recibe 403 (RNF-03) |
| D8 | `feature/incidencias-validaciones` | `feat(incidencias): avanza el estado pendiente, en revisión y resuelta sin retroceder` | `serializers.py`, `views.py` | `validate_estado` con `self.instance`; sin delete (RNF-06) |
| D9 | `feature/incidencias-filtros` | `feat(incidencias): agrega filtros por estado y recurso, búsqueda y orden por fecha` | `views.py` | `filterset_fields`, `search_fields`, `ordering = ['-fecha']` |
| D10 | `feature/alertas` | `feat(alertas): calcula alertas de reparación, mantención y reposición` | `incidencias/alertas.py` | Recorrer recursos con `for` + `if`: dañados → reparación, en mantención → mantención, insumo bajo el stock mínimo → reposición (HU-09). Al calcularse no se duplican y desaparecen solas (CA-09.4, CA-05.3) |
| D11 | `feature/alertas` | `feat(alertas): agrega la vista /api/alertas/ para encargado y departamento` | `views.py`, `urls.py` | `APIView` con `permission_classes = [EsEncargadoODepartamento]` (CA-05.4) |
| D12 | `feature/alertas` | `feat(alertas): filtra por tipo y entrega las alertas paginadas con su contador` | `views.py` | `?tipo=`; `PageNumberPagination().paginate_queryset(lista, request)` → `count` es el contador del menú (CA-05.1, CA-05.2) |
| D13 | `feature/incidencias-datos` | `chore(incidencias): registra Incidencia en el admin y agrega datos de prueba` | `admin.py`, `fixtures/incidencias.json` | Dejar recursos dañados y guantes de nitrilo bajo el mínimo para que haya alertas |
| D14 | `feature/incidencias-datos` | `docs: documenta los endpoints de incidencias y alertas en el README` | `README.md` (en su sección) | — |

**Demo de Diego:** login como encargado. Registrar una incidencia marcando personas afectadas sin detalle → error. Corregirla → nace "pendiente" con fecha y usuario automáticos. Avanzarla a "resuelta" y mostrar que no se puede volver atrás ni borrar. Login como departamento → ve las incidencias pero no puede crear. Abrir `/api/alertas/`, filtrar por `reposicion` y mostrar el contador. Docente → 403 en ambos.

---

## 10. Fase 4: cierre (los tres)

Checklist de la sección 8 de la pauta:

- [ ] `main` actualizada y funcionando.
- [ ] **Base limpia:** ejecutar de nuevo `bd/crear_bd.sql` → `migrate` → `loaddata` sin errores, en los **tres** computadores.
- [ ] Cada uno tiene **≥10 commits** en GitHub (*Insights → Contributors* del repo).
- [ ] Flujo completo probado desde la API navegable en el computador de la demo (CRUD, login de los 3 roles, filtros, búsqueda, paginación).
- [ ] Alcance acordado (tabla de la sección 3) y decisión 🔶 tomada.
- [ ] Repo accesible para el profesor (invitarlo como colaborador o dejarlo público).

Opcional, si queda tiempo: un `tests.py` por app con `APITestCase` (crear sin sesión → 403, crear como encargado → 201).

### Guion de la demo (15–20 min)

| Momento | Quién | Qué se muestra |
|---|---|---|
| Alcance (1–2 min) | Johann | Diagrama de relaciones (sección 2) y tabla de alcance (sección 3) |
| Autenticación y permisos | Johann | Sin sesión → 403; docente vs. encargado |
| Inventario | Johann | CRUD, filtros, búsqueda, paginación, historial |
| Reservas | Martín | Validaciones, "mis reservas", cancelar, disponibilidad |
| Incidencias y alertas | Diego | Validaciones, estados, permisos por rol, alertas filtradas |
| Preguntas (5–7 min) | Los tres | — |

---

## 11. Preguntas probables del docente (todos deben saber responderlas)

1. ¿Qué hace un serializer? ¿Qué diferencia hay entre `ModelSerializer` y uno normal?
2. ¿Por qué usaron `ModelViewSet` en unas partes y `APIView` en otras?
3. ¿Qué hace el `DefaultRouter`? ¿Qué URLs crea para un ViewSet?
4. ¿Qué es una migración? ¿Qué pasa si dos personas generan la `0002` en la misma app?
5. ¿Qué significa `on_delete=PROTECT` frente a `CASCADE`? ¿Por qué la Unidad usa `CASCADE` y la Reserva `PROTECT`?
6. ¿Para qué sirve `related_name`? ¿Cómo aparecen las unidades dentro del recurso?
7. ¿Cómo distingue la API a un usuario con sesión de uno sin sesión? ¿Qué diferencia hay entre sesión y token?
8. ¿Dónde se revisa el rol? ¿Qué diferencia hay entre `has_permission` y `has_object_permission`?
9. ¿Cómo funciona la paginación? ¿Por qué 9 por página?
10. ¿Qué diferencia hay entre filtrar (`?categoria=2`), buscar (`?search=`) y ordenar (`?ordering=`)?
11. ¿Dónde se valida que no se reserven más unidades de las que hay? ¿Por qué ahí y no en la vista?
12. ¿Por qué el historial y las incidencias no se pueden borrar?
13. ¿Cómo se conecta Django con MySQL? ¿Qué hace PyMySQL?

---

## 12. Para empezar con la IA (opcional)

Prompt corto para Claude Code o Antigravity, una vez que el plan y `CLAUDE.md` estén en el repo:

> Lee `docs/plan-eva2-backend.md` y `CLAUDE.md`. Haz solo el commit **J1** (o el que toque), muéstrame qué cambiaste y espera mi confirmación antes de seguir.

Un commit por pedido: así cada avance queda separado en GitHub Desktop y cada uno entiende lo que sube.
