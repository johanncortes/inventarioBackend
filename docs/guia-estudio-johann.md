# Guía de estudio — Backend SGIL (parte de Johann)

Guía para preparar la **demo** y la **defensa oral** de la EVA2. Está pensada para leerla en GitHub, con el código abierto al lado.

**Cómo usarla:**
1. Lee las secciones 1 a 3 para entender el sistema completo (≈ 30 min).
2. Recorre el código con la sección 4, abriendo cada archivo enlazado.
3. Ensaya la demo con la sección 5 **en tu computador**, siguiendo los pasos al pie de la letra.
4. Practica las preguntas de la sección 6: **contesta en voz alta antes de abrir la respuesta** (clic en ▶).
5. Haz los ejercicios de código de la sección 7 (el profe puede pedir un cambio en vivo).

> Regla de oro de la defensa: **explica siempre con un ejemplo de nuestro sistema**. No "un serializer convierte objetos", sino "el `RecursoSerializer` convierte un Recurso en JSON y agrega el nombre de la categoría con `source='categoria.nombre'`".

---

## Índice

1. [El sistema en 1 minuto](#1-el-sistema-en-1-minuto)
2. [Cómo viaja una petición (el diagrama que tienes que saber dibujar)](#2-cómo-viaja-una-petición)
3. [Los conceptos, explicados con nuestro código](#3-los-conceptos-explicados-con-nuestro-código)
4. [Recorrido por los archivos](#4-recorrido-por-los-archivos)
5. [Guion de la demo paso a paso](#5-guion-de-la-demo-paso-a-paso)
6. [Preguntas y respuestas](#6-preguntas-y-respuestas)
7. [Cómo codear: recetas y ejercicios en vivo](#7-cómo-codear-recetas-y-ejercicios-en-vivo)
8. [Códigos de respuesta HTTP que vas a ver](#8-códigos-de-respuesta-http-que-vas-a-ver)
9. [Decisiones de diseño (para declarar en la demo)](#9-decisiones-de-diseño-para-declarar-en-la-demo)
10. [Comandos útiles](#10-comandos-útiles)
11. [Autoevaluación final](#11-autoevaluación-final)

---

## 1. El sistema en 1 minuto

**Qué decir en la presentación del alcance:**

> "El SGIL es el sistema de inventario de los laboratorios de Ciencias Básicas que hicimos en la EVA1 como frontend. En la EVA2 construimos su **backend**: una API REST con **Django REST Framework** y **MySQL**. Cada pantalla de la EVA1 tiene su modelo y su endpoint. Yo hice la **base del proyecto, los usuarios con sus roles y todo el inventario**: categorías, torres, salas, recursos, unidades con número de serie y el historial de movimientos. Martín hizo las reservas y Diego las incidencias y alertas. Todo se demuestra desde la **API navegable** de DRF."

**Lo que hay en el backend (mi parte):**

| Qué | Dónde | Historias |
|---|---|---|
| Proyecto, MySQL, DRF, paginación de 9 | `sgil/settings.py`, `sgil/urls.py` | CA-01.3 |
| Página de inicio `/api/` con todos los endpoints | `sgil/raiz.py` | — |
| Perfil con el rol (encargado, docente, departamento) | `usuarios/models.py` | RNF-03 |
| Permisos por rol | `usuarios/permisos.py` | RNF-03 |
| CRUD de usuarios + `/api/usuarios/yo/` | `usuarios/serializers.py`, `usuarios/views.py` | HU-15, RF-14 |
| Categorías, torres y salas | `inventario/models.py` … | RF-08, RF-10, RNF-05 |
| Recursos y unidades con n° de serie | `inventario/…` | HU-01, HU-11, HU-12, HU-13 |
| Filtros, búsqueda, orden y paginación | `inventario/views.py` | HU-01, HU-13 |
| Historial: cambio de estado, entradas, salidas, cambio de ubicación | `inventario/movimientos.py`, `views.py` | HU-02, HU-06, HU-14, RNF-06 |
| Datos de prueba | `*/fixtures/*.json` | — |

**Números para recordar:** 7 modelos míos (Perfil, Categoria, Torre, Sala, Recurso, Unidad, Movimiento) · 8 endpoints · 3 roles · 9 por página · 5 estados · 10 recursos y 101 unidades de prueba.

---

## 2. Cómo viaja una petición

Esto es lo más importante de toda la guía. Si entiendes este camino, puedes responder casi cualquier pregunta.

Ejemplo: el encargado hace `POST /api/recursos/` para agregar un recurso.

```
 Navegador (API navegable)
     │  POST /api/recursos/   {"nombre": "Multímetro", "categoria": 1, "sala": 2, ...}
     ▼
 1. sgil/urls.py ─────────── busca la ruta: path('api/', include('inventario.urls'))
     ▼
 2. inventario/urls.py ───── el DefaultRouter sabe que "recursos" es RecursoViewSet
     ▼                       y que POST a la lista = acción "create"
 3. AUTENTICACIÓN ────────── ¿quién es? SessionAuthentication (cookie del "Log in")
     ▼                       o TokenAuthentication (encabezado "Authorization: Token ...")
 4. PERMISOS ─────────────── EsEncargadoOSoloLectura.has_permission()
     │                       ¿es POST? → ¿el rol es encargado? Si no → 403
     ▼
 5. SERIALIZER ───────────── RecursoSerializer(data=...)
     │                       valida tipos, que la categoría exista, validate_fecha_adquisicion(),
     │                       validate()... Si algo falla → 400 con el mensaje
     ▼
 6. MODELO ───────────────── Recurso.save() arma codigo_ubicacion "B307-B1-M2"
     ▼
 7. MySQL ────────────────── PyMySQL ejecuta el INSERT en la tabla inventario_recurso
     ▼
 8. RESPUESTA ────────────── el serializer convierte el recurso guardado en JSON → 201 Created
```

**Para un GET de listado** (`GET /api/recursos/?search=multimetro&page=2`) los pasos 5 y 6 cambian:
`get_queryset()` → **filtros** (DjangoFilterBackend, SearchFilter, OrderingFilter) → **paginación** (9 por página) → serializer con `many=True` → JSON con `count`, `next`, `previous` y `results`.

---

## 3. Los conceptos, explicados con nuestro código

### 3.1 Modelo

Una clase de Python = una tabla de MySQL. Cada atributo = una columna.

```python
class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)   # columna VARCHAR(100) única
    descripcion = models.CharField(max_length=120)
    usa_stock_minimo = models.BooleanField(default=False)
```

- `unique=True` → MySQL no deja repetir el nombre.
- `blank=True` → el campo puede quedar vacío en los formularios (validación).
- `null=True` → la columna acepta NULL en la base (se usa en números y fechas opcionales: `stock_minimo`, `fecha_adquisicion`).
- `choices` → limita los valores (los 5 estados, los 3 roles).
- `editable=False` → no aparece en formularios: `Sala.codigo` y `Recurso.codigo_ubicacion` los arma `save()`.
- `auto_now_add=True` → Django pone la fecha al crear (`Movimiento.fecha`).

### 3.2 Relaciones y `on_delete`

| Relación | Tipo | `on_delete` | Por qué |
|---|---|---|---|
| Perfil → User | `OneToOneField` | `CASCADE` | Un perfil no tiene sentido sin su usuario |
| Sala → Torre | `ForeignKey` | `PROTECT` | No se borra una torre que tiene salas |
| Recurso → Categoria | `ForeignKey` | `PROTECT` | No se borra una categoría con recursos |
| Recurso → Sala | `ForeignKey` | `PROTECT` | No se borra una sala con recursos |
| Unidad → Recurso | `ForeignKey` | `CASCADE` | Si se borra el recurso, sus unidades se van con él |
| Movimiento → Recurso | `ForeignKey` | `CASCADE` | El historial pertenece al recurso |
| Movimiento → Unidad | `ForeignKey` | `SET_NULL` | El registro queda aunque se borre la unidad |
| Movimiento → User | `ForeignKey` | `PROTECT` | Un usuario con historial no se borra (se desactiva) |
| Reserva → Recurso (Martín) | `ForeignKey` | `PROTECT` | No se borra un recurso con reservas |

**`related_name`** es el nombre de la relación "al revés": como `Unidad.recurso` tiene `related_name='unidades'`, desde un recurso se escribe `recurso.unidades.all()`. Eso usa el serializer para anidar las unidades.

### 3.3 Migración

Es un archivo de Python que describe un **cambio en la estructura** de la base (crear una tabla, agregar una columna). `makemigrations` lo **genera** comparando los modelos con las migraciones anteriores; `migrate` lo **aplica** en MySQL. Las mías: `usuarios/0001`, `inventario/0001` (Categoria, Torre, Sala), `0002` (Recurso, Unidad) y `0003` (Movimiento).

### 3.4 Serializer

Traduce **objeto de Python ⇄ JSON** y **valida** lo que llega.

```python
class RecursoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)  # dato de otra tabla
    unidades = UnidadSerializer(many=True, read_only=True)                               # anidado
    cantidad_total = serializers.SerializerMethodField()                                  # calculado

    def get_cantidad_total(self, recurso):
        return recurso.obtener_cantidad_total()

    def validate_fecha_adquisicion(self, fecha):        # valida UN campo
        if fecha is not None and fecha > timezone.localdate():
            raise serializers.ValidationError('La fecha de adquisición no puede ser futura.')
        return fecha
```

| Herramienta | Para qué | Ejemplo nuestro |
|---|---|---|
| `ModelSerializer` | Arma los campos solo, leyendo el modelo | Todos |
| `source='a.b'` | Saca un dato de un objeto relacionado | `categoria_nombre`, `sala_codigo`, `torre` |
| Serializer anidado `many=True` | Muestra una lista relacionada dentro | `unidades` dentro del recurso |
| `SerializerMethodField` | Valor calculado con un método `get_<campo>` | `cantidades`, `cantidad_total`, `usuario_nombre` |
| `read_only=True` / `read_only_fields` | Se muestra pero no se escribe | `codigo_ubicacion`, `fecha`, `usuario` |
| `write_only=True` | Se escribe pero nunca se muestra | `contrasena`, `numero_unidad_nueva` |
| `validate_<campo>()` | Valida un campo | `validate_letra`, `validate_numero`, `validate_correo` |
| `validate()` | Valida cruzando varios campos | Sala repetida, movimientos, "al menos un encargado" |
| `validators = []` | Quita el validador automático para poner un mensaje propio | `SalaSerializer`, `UnidadSerializer` |
| `create()` / `update()` | Cambia cómo se guarda | `MovimientoSerializer.create`, `UsuarioSerializer.create` |

### 3.5 ModelViewSet vs APIView

- **`ModelViewSet`**: una clase con las 5 acciones del CRUD (`list`, `create`, `retrieve`, `update`/`partial_update`, `destroy`). Lo usamos para todo lo que es una tabla: categorías, torres, salas, recursos, unidades, movimientos, usuarios.
- **`APIView`**: escribes tú el `get()`/`post()`. Lo usamos para respuestas **calculadas** que no son una tabla: `YoView` (`/api/usuarios/yo/`) y `RaizAPI` (`/api/`). Martín la usa en disponibilidad y Diego en alertas.

Ganchos que usamos en los ViewSets:

| Método | Cuándo corre | Ejemplo nuestro |
|---|---|---|
| `get_queryset()` | Al buscar los objetos | Filtro `?estado=` de recursos |
| `perform_create()` | Justo antes de guardar algo nuevo | Movimiento: `serializer.save(usuario=self.request.user)` |
| `perform_update()` | Justo antes de guardar una edición | Recurso: si cambió la ubicación, crea el Movimiento |
| `destroy()` | Al borrar | `borrar_o_avisar()`: 400 en vez de 500 si hay `PROTECT` |
| `http_method_names` | Qué métodos HTTP acepta | Movimientos sin put/patch/delete; usuarios sin delete |

### 3.6 Router

`DefaultRouter` crea las URLs de un ViewSet:

| URL | GET | POST | PUT / PATCH | DELETE |
|---|---|---|---|---|
| `/api/recursos/` | listar (`list`) | crear (`create`) | — | — |
| `/api/recursos/{id}/` | ver (`retrieve`) | — | editar (`update` / `partial_update`) | borrar (`destroy`) |

Los nombres de las rutas son `recurso-list` y `recurso-detail` (los usa `sgil/raiz.py` con `reverse()`).

### 3.7 Autenticación y permisos

- **Autenticación = ¿quién eres?** `SessionAuthentication` (cookie que deja el "Log in") y `TokenAuthentication` (encabezado `Authorization: Token abc123`, para el front en la Unidad IV).
- **Permiso = ¿puedes hacer esto?** Por defecto `IsAuthenticated` (sin sesión → 403). Cada vista agrega su permiso por rol de `usuarios/permisos.py`.

```python
class EsEncargadoOSoloLectura(BasePermission):
    def has_permission(self, request, view):
        rol = obtener_rol(request.user)
        if rol is None:
            return False                   # sin rol → 403
        if es_lectura(request):            # GET, HEAD, OPTIONS (SAFE_METHODS)
            return True
        return rol == Perfil.ENCARGADO     # escribir → solo encargado
```

- `has_permission` → se revisa **antes** de todo, para la vista completa.
- `has_object_permission` → se revisa con **un objeto** (ej: "¿esta reserva es tuya?"). La usa Martín en `EsDuenoOEncargado`.

### 3.8 Filtrar, buscar, ordenar y paginar

| | Parámetro | Quién lo hace | Ejemplo |
|---|---|---|---|
| **Filtrar** | valor exacto o rango de un campo | `DjangoFilterBackend` + `filterset_fields` | `?categoria=1`, `?fecha_adquisicion__gte=2024-01-01` |
| **Buscar** | texto libre en varios campos | `SearchFilter` + `search_fields` | `?search=multimetro` |
| **Ordenar** | por un campo | `OrderingFilter` + `ordering_fields` | `?ordering=-fecha_adquisicion` |
| **Paginar** | página | `PageNumberPagination`, `PAGE_SIZE: 9` | `?page=2` |

Los tres primeros están en `DEFAULT_FILTER_BACKENDS` de `settings.py`, así que sirven en todas las vistas.

### 3.9 Otros conceptos que aparecen

- **`transaction.atomic()`** → "todo o nada". Si falla algo a la mitad, MySQL deshace todo. Lo usamos al registrar un movimiento (cambiar la unidad + guardar el registro), al cambiar la ubicación y al crear un usuario (User + Perfil).
- **`select_related` / `prefetch_related`** → evitan hacer una consulta por cada fila. El listado de recursos hace **3 consultas** en total, tenga 9 o 900 recursos.
- **`Q(...) | Q(...)`** → condición "o" en una consulta (filtro de estado).
- **`distinct()`** → que un recurso no salga repetido.
- **PyMySQL** → driver de MySQL escrito solo en Python; `pymysql.install_as_MySQLdb()` en `sgil/__init__.py` lo hace pasar por `mysqlclient`, que es el que Django busca.
- **Fixtures** → archivos JSON con datos que se cargan con `loaddata`.

---

## 4. Recorrido por los archivos

Abre cada archivo y busca lo que dice la columna "Fíjate en".

### `sgil/` — configuración

| Archivo | Qué hace | Fíjate en |
|---|---|---|
| [sgil/settings.py](../sgil/settings.py) | Configuración | `INSTALLED_APPS` (marcadores por integrante), `DATABASES` (MySQL), `LANGUAGE_CODE = 'es-cl'`, `TIME_ZONE`, bloque `REST_FRAMEWORK` |
| [sgil/__init__.py](../sgil/__init__.py) | Conecta PyMySQL | `pymysql.install_as_MySQLdb()` |
| [sgil/urls.py](../sgil/urls.py) | URLs principales | `api-auth/` (Log in), `api/` (raíz), `api/token/`, los `include()` |
| [sgil/raiz.py](../sgil/raiz.py) | Página `/api/` | Por qué existe (comentario de arriba), `AllowAny`, `reverse()` |

### `usuarios/`

| Archivo | Qué hace | Fíjate en |
|---|---|---|
| [models.py](../usuarios/models.py) | `Perfil` | `OneToOneField`, `related_name='perfil'`, `ROLES` |
| [permisos.py](../usuarios/permisos.py) | Permisos | `obtener_rol()` (superusuario = encargado), `SAFE_METHODS`, las 3 clases |
| [serializers.py](../usuarios/serializers.py) | Usuarios | `source='first_name'`, `source='perfil.rol'`, `contrasena` write_only, `create_user`, regla del último encargado |
| [views.py](../usuarios/views.py) | Vistas | `UsuarioViewSet` sin delete, `YoView` con `request.user` |
| [urls.py](../usuarios/urls.py) | Rutas | `usuarios/yo/` **antes** del router (y por qué) |
| [admin.py](../usuarios/admin.py) | Admin | `StackedInline` del perfil dentro del usuario |

### `inventario/`

| Archivo | Qué hace | Fíjate en |
|---|---|---|
| [models.py](../inventario/models.py) | 6 modelos | `ESTADOS`, cada `on_delete` con su comentario, `Sala.save()`, `Recurso.save()`, `obtener_cantidades()`, `unique_together` |
| [ubicacion.py](../inventario/ubicacion.py) | Código de ubicación | `"B307" + "Bodega 1" + "Mueble 2" → "B307-B1-M2"` |
| [serializers.py](../inventario/serializers.py) | 6 serializers | `source=`, anidado, `SerializerMethodField`, `validators = []`, `MovimientoSerializer.validate()` y `create()` |
| [movimientos.py](../inventario/movimientos.py) | Reglas del historial | `validar_cambio_estado`, `validar_entrada`, `validar_salida` (devuelven mensaje o `''`, igual que el front), `aplicar_movimiento` |
| [views.py](../inventario/views.py) | 6 ViewSets | `borrar_o_avisar`, filtros de `RecursoViewSet`, `get_queryset` (estado), `perform_update` (ubicación), `MovimientoViewSet` (`perform_create`, `http_method_names`) |
| [urls.py](../inventario/urls.py) | Router | `router.register(...)` |
| [fixtures/inventario.json](../inventario/fixtures/inventario.json) | Datos de prueba | ids 1 a 10 iguales al front |

### Cómo funciona un movimiento (lo más largo de explicar)

```
POST /api/movimientos/  {"tipo": "salida", "recurso": 1, "unidad": 13,
                         "subtipo": "dano_irreparable", "motivo": "Se cayó"}
  │
  ├─ MovimientoViewSet: permiso EsEncargadoODepartamento (POST → solo encargado)
  ├─ MovimientoSerializer.validate()
  │    ├─ tipo permitido (no cambio_ubicacion ni alta a mano)
  │    ├─ la unidad 13 es del recurso 1
  │    ├─ movimientos.validar_salida() → '' (sin error)
  │    └─ completa: estado_nuevo = 'dado_de_baja', estado_anterior = 'danado', cantidad = 1
  ├─ perform_create → serializer.save(usuario=request.user)
  └─ MovimientoSerializer.create()  dentro de transaction.atomic():
       ├─ movimientos.aplicar_movimiento() → la unidad 13 pasa a dado_de_baja
       │                                      valor_anterior "Dañado", valor_nuevo "Dado de baja"
       └─ movimiento.save() → queda en el historial con fecha automática
```

---

## 5. Guion de la demo paso a paso

### Antes de la demo (el día anterior y 10 min antes)

1. Base limpia: Workbench → `bd/crear_bd.sql` → ⚡.
2. Terminal:
   ```powershell
   venv\Scripts\activate
   python manage.py migrate
   python manage.py loaddata usuarios inventario reservas incidencias
   python manage.py runserver
   ```
   (Sin `reservas incidencias` si Martín y Diego todavía no suben sus fixtures.)
3. Ten abiertas dos pestañas: `http://127.0.0.1:8000/api/` y esta guía.
4. Ten a mano: `encargado@prueba.cl`, `docente@prueba.cl`, `departamento@prueba.cl` — clave `prueba123`.

> En la API navegable, para mandar JSON usa la pestaña **Raw data** del formulario de abajo, con *Media type* `application/json`.

### Paso 1 — Alcance (1–2 min)

Muestra el diagrama de relaciones (sección 6 del README) y la tabla de alcance (sección 3 del plan). Abre `http://127.0.0.1:8000/api/`: *"Esta es la raíz: lista todos los endpoints del sistema."*

### Paso 2 — Sin sesión → 403

Abre `/api/recursos/`.
- **Se ve:** `403 Forbidden` — "Las credenciales de autenticación no se proveyeron."
- **Decir:** *"`DEFAULT_PERMISSION_CLASSES` es `IsAuthenticated`: sin iniciar sesión no se ve nada."*

### Paso 3 — Docente: lee, pero no escribe

**Log in** con `docente@prueba.cl`.
1. `/api/recursos/` → **200**, 9 recursos, `count: 10`.
2. `/api/usuarios/yo/` → "Prof. Ana Morales", rol `docente`.
3. En `/api/categorias/`, Raw data → `{"nombre": "Prueba", "descripcion": "x"}` → POST → **403** "Solo el encargado de laboratorio puede crear, editar o eliminar."
4. `/api/movimientos/` → **403** (el docente no ve el historial).
- **Decir:** *"El permiso `EsEncargadoOSoloLectura` deja pasar GET a cualquier rol, pero POST solo al encargado."*

### Paso 4 — Encargado: CRUD de configuración

**Log out** → **Log in** con `encargado@prueba.cl`.
1. `/api/categorias/` → POST:
   ```json
   {"nombre": "Equipo de demostración", "descripcion": "Categoría creada en la demo", "usa_numero_serie": true}
   ```
   → **201**. Anota el `id`.
2. POST de nuevo lo mismo → **400** "Ya existe categoría con este nombre."
3. `/api/torres/` → POST `{"letra": "1"}` → **400** "La torre debe ser una sola letra".

### Paso 5 — Crear un recurso

`/api/recursos/` → POST (cambia `categoria` por el id que anotaste):
```json
{"nombre": "Multímetro de demostración", "categoria": 7, "sala": 2,
 "bodega": "Bodega 1", "mueble": "Mueble 4", "fecha_adquisicion": "2025-03-10"}
```
- **Se ve:** **201** con `"codigo_ubicacion": "B307-B1-M4"`, `"sala_codigo": "B307"`, `"torre": "B"`.
- **Decir:** *"No mandé el código de ubicación: lo arma `Recurso.save()` con la misma regla del front."*
- Extra: cambia la fecha a `"2099-01-01"` → **400** "no puede ser futura" (CA-13.1).

Anota el `id` del recurso. Agrégale una unidad en `/api/unidades/`:
```json
{"recurso": 11, "numero": "DEMO-001"}
```
Y otra vez el mismo número → **400** "El número "DEMO-001" ya está registrado…" (CA-12.2).

### Paso 6 — Filtros, búsqueda y paginación

| URL | Qué mostrar |
|---|---|
| `/api/recursos/` | `count: 11`, 9 resultados y `next` |
| `/api/recursos/?page=2` | Los 2 que faltan |
| `/api/recursos/?search=multimetro` | Encuentra "Multímetro" **sin tilde** |
| `/api/recursos/?categoria=1` | Solo instrumentos |
| `/api/recursos/?sala__torre=2` | Solo torre C |
| `/api/recursos/?estado=danado` | Multímetro y termómetro |
| `/api/recursos/?ordering=-fecha_adquisicion` | Más nuevos primero |
| Botón **Filtros** | El formulario de django-filter |

- **Decir:** *"Filtrar es por valor exacto, buscar es texto libre en varios campos, y ordenar cambia el orden. Todo sale paginado de a 9 como en el front."*

### Paso 7 — Ficha y cambio de ubicación

1. `/api/recursos/1/` → muestra `cantidades` (12, 0, 1, 1, 0), `cantidad_total: 14` y las 14 unidades anidadas.
2. Vuelve a tu recurso de demo: `/api/recursos/11/` → PATCH (Raw data):
   ```json
   {"sala": 5, "bodega": "Bodega 2", "mueble": "Sin mueble"}
   ```
   → `"codigo_ubicacion": "C210-B2"`.
3. `/api/movimientos/?recurso=11` → aparece `cambio_ubicacion` de `B307-B1-M4` a `C210-B2`, con tu usuario.
- **Decir:** *"`perform_update` compara la ubicación de antes y de después y, si cambió, deja el movimiento en el historial (CA-11.3)."*

### Paso 8 — Salida por daño irreparable

`/api/movimientos/` → POST (usa el id de la unidad DEMO-001):
```json
{"tipo": "salida", "recurso": 11, "unidad": 102, "subtipo": "dano_irreparable", "motivo": "Se cayó al piso"}
```
- **Se ve:** **201**, `valor_anterior: "Disponible"`, `valor_nuevo: "Dado de baja"`, `usuario_nombre: "Pedro Soto"`.
- Repite el mismo POST → **400** "La unidad DEMO-001 ya está dada de baja."
- Abre `/api/movimientos/{id}/` e intenta **DELETE** → **405** (RNF-06).

### Paso 9 — Eliminar el recurso de prueba

`/api/recursos/11/` → **DELETE** → **204**.
- Extra: `/api/categorias/1/` → DELETE → **400** "No se puede eliminar: hay recursos en esta categoría." → *"Eso es `on_delete=PROTECT`; sin `borrar_o_avisar` sería un error 500."*

### Paso 10 (si preguntan) — Departamento

Log in con `departamento@prueba.cl`: ve `/api/movimientos/` (200) pero el POST da 403; `/api/usuarios/` da 403 y `/api/usuarios/yo/` funciona.

---

## 6. Preguntas y respuestas

Contesta en voz alta y después abre la respuesta.

### 6.1 Las 13 preguntas del plan

<details><summary><b>1. ¿Qué hace un serializer? ¿Qué diferencia hay entre <code>ModelSerializer</code> y uno normal?</b></summary>

Convierte objetos de Django en JSON para responder, y valida el JSON que llega antes de guardarlo. Un `Serializer` normal obliga a declarar cada campo a mano y escribir `create()` y `update()`; un `ModelSerializer` lee el modelo y arma solo los campos, las validaciones básicas (tipos, largo máximo, únicos) y el `create`/`update`. Ejemplo: `CategoriaSerializer` es solo `model = Categoria` y `fields = [...]`.
</details>

<details><summary><b>2. ¿Por qué usaron <code>ModelViewSet</code> en unas partes y <code>APIView</code> en otras?</b></summary>

`ModelViewSet` cuando el endpoint es el CRUD de una tabla: con una clase tengo listar, crear, ver, editar y borrar. `APIView` cuando la respuesta es calculada y no corresponde a una tabla: `/api/usuarios/yo/` devuelve el usuario conectado y `/api/` arma la lista de enlaces. Martín y Diego la usan para disponibilidad y alertas, que se calculan.
</details>

<details><summary><b>3. ¿Qué hace el <code>DefaultRouter</code>? ¿Qué URLs crea para un ViewSet?</b></summary>

Genera las URLs del ViewSet automáticamente. Con `router.register('recursos', RecursoViewSet)` crea `/api/recursos/` (GET listar, POST crear) y `/api/recursos/{id}/` (GET ver, PUT/PATCH editar, DELETE borrar), con los nombres `recurso-list` y `recurso-detail`. El `DefaultRouter`, además, crea una página raíz; como cada app tiene su router, hicimos nuestra propia raíz en `sgil/raiz.py` para que liste todo.
</details>

<details><summary><b>4. ¿Qué es una migración? ¿Qué pasa si dos personas generan la <code>0002</code> en la misma app?</b></summary>

Es un archivo que describe un cambio en la estructura de la base. `makemigrations` lo genera y `migrate` lo aplica en MySQL. Si dos personas generan una `0002` distinta en la misma app, las dos dependen de la `0001` y Django detecta un **conflicto** ("Conflicting migrations"): hay que hacer `makemigrations --merge` o rehacer una. Por eso cada uno trabaja en su propia app (cada app tiene su carpeta de migraciones) y se hace Pull antes de generar una.
</details>

<details><summary><b>5. ¿Qué significa <code>on_delete=PROTECT</code> frente a <code>CASCADE</code>? ¿Por qué la Unidad usa <code>CASCADE</code> y la Reserva <code>PROTECT</code>?</b></summary>

`CASCADE` borra también los objetos relacionados; `PROTECT` impide el borrado y lanza `ProtectedError`. La Unidad usa `CASCADE` porque una unidad no existe sin su recurso: si elimino el recurso, sus unidades sobran. La Reserva usa `PROTECT` porque es un compromiso con un docente: no se puede borrar un recurso que tiene reservas. En la API convertimos el `ProtectedError` en una respuesta 400 con mensaje (`borrar_o_avisar`), en vez de un error 500.
</details>

<details><summary><b>6. ¿Para qué sirve <code>related_name</code>? ¿Cómo aparecen las unidades dentro del recurso?</b></summary>

Es el nombre de la relación vista desde el otro lado. `Unidad.recurso` tiene `related_name='unidades'`, así que `recurso.unidades.all()` da sus unidades. En `RecursoSerializer` declaro `unidades = UnidadSerializer(many=True, read_only=True)`: como el campo se llama igual que el `related_name`, DRF las busca solo y las muestra anidadas en la ficha.
</details>

<details><summary><b>7. ¿Cómo distingue la API a un usuario con sesión de uno sin sesión? ¿Qué diferencia hay entre sesión y token?</b></summary>

DRF prueba las clases de `DEFAULT_AUTHENTICATION_CLASSES`. Con **sesión**, el "Log in" guarda una cookie y en cada petición Django reconoce al usuario por ella (es lo que usa el navegador). Con **token**, el cliente manda `Authorization: Token <clave>` en cada petición; sirve para el front en React (Unidad IV). Si ninguna reconoce al usuario, `request.user` es anónimo e `IsAuthenticated` responde 403.
</details>

<details><summary><b>8. ¿Dónde se revisa el rol? ¿Qué diferencia hay entre <code>has_permission</code> y <code>has_object_permission</code>?</b></summary>

En `usuarios/permisos.py`: `obtener_rol(user)` lee `user.perfil.rol` (y el superusuario cuenta como encargado). Cada clase de permiso la usa en `has_permission`, que se revisa antes de ejecutar la vista y vale para toda la vista (ej: "¿es POST y eres encargado?"). `has_object_permission` se revisa con un objeto concreto, al hacer `get_object()` (ej: "¿esta reserva es tuya?"); la usa Martín para que el docente edite solo sus reservas.
</details>

<details><summary><b>9. ¿Cómo funciona la paginación? ¿Por qué 9 por página?</b></summary>

`PageNumberPagination` con `PAGE_SIZE: 9` en `settings.py`. La respuesta trae `count` (total), `next` y `previous` (enlaces) y `results` (los 9 de esa página); se cambia con `?page=2`. Son 9 porque el inventario del front muestra 9 tarjetas por página (CA-01.3, una grilla de 3×3).
</details>

<details><summary><b>10. ¿Qué diferencia hay entre filtrar (<code>?categoria=2</code>), buscar (<code>?search=</code>) y ordenar (<code>?ordering=</code>)?</b></summary>

Filtrar compara un campo con un valor exacto o un rango (`DjangoFilterBackend` + `filterset_fields`): `?categoria=2`, `?fecha_adquisicion__gte=2024-01-01`. Buscar busca un texto dentro de varios campos a la vez (`SearchFilter` + `search_fields`): `?search=fluke` busca en nombre, marca, n° de serie y n° de las unidades. Ordenar cambia el orden (`OrderingFilter`): `?ordering=-fecha_adquisicion`, con `-` para invertir. Se pueden combinar.
</details>

<details><summary><b>11. ¿Dónde se valida que no se reserven (o muevan) más unidades de las que hay? ¿Por qué ahí y no en la vista?</b></summary>

En las reservas lo hace Martín en el `validate()` del serializer con `disponibilidad.py`. En mi parte, en `MovimientoSerializer.validate()`, que llama a `movimientos.validar_cantidad_en_origen()` ("Solo hay 7 unidad(es) en estado Disponible"). Va en el serializer porque es validar datos: así el error sale como 400 con el mensaje en el campo, sirve para crear desde cualquier vista y la vista queda corta. Además la lógica en un archivo aparte se puede probar sola.
</details>

<details><summary><b>12. ¿Por qué el historial y las incidencias no se pueden borrar?</b></summary>

Por RNF-06: el historial es la trazabilidad del inventario. Si se pudiera editar o borrar, no serviría para saber qué pasó. En `MovimientoViewSet` puse `http_method_names = ['get', 'post', 'head', 'options']`: PUT, PATCH y DELETE responden 405. Además, las cantidades y los estados solo cambian con un movimiento, así ningún cambio queda fuera del historial.
</details>

<details><summary><b>13. ¿Cómo se conecta Django con MySQL? ¿Qué hace PyMySQL?</b></summary>

En `DATABASES` de `settings.py` con `ENGINE: 'django.db.backends.mysql'`, la base `sgil_db` y el usuario `sgil`. Ese motor busca el driver `MySQLdb` (mysqlclient), que hay que compilar y falla en Windows. PyMySQL es un driver escrito solo en Python; en `sgil/__init__.py`, `pymysql.install_as_MySQLdb()` lo registra con ese nombre y Django lo usa sin notar la diferencia. `cryptography` es necesaria para la contraseña de MySQL 8.
</details>

### 6.2 Modelos y base de datos

<details><summary><b>¿Por qué el rol está en un modelo Perfil y no en el User?</b></summary>

El `User` es de Django y no conviene modificarlo. La forma simple de agregarle datos es un modelo aparte con `OneToOneField`: cada usuario tiene un perfil. Se accede con `user.perfil.rol` gracias a `related_name='perfil'`.
</details>

<details><summary><b>¿Cómo se arma el código "B307-B1-M2"?</b></summary>

En dos pasos. `Sala.save()` arma el código de la sala: letra de la torre + número = "B307". `Recurso.save()` llama a `generar_codigo_ubicacion()` de `inventario/ubicacion.py`: código de la sala + bodega abreviada ("Bodega 1" → "B1") + mueble abreviado ("Mueble 2" → "M2"). Si la bodega es "Sala" y no hay mueble, queda "B308-SALA". Es la misma regla de `src/utils/ubicacion.ts` del front.
</details>

<details><summary><b>¿Qué pasa si cambio la letra de una torre?</b></summary>

`Torre.save()` vuelve a guardar cada sala (`self.salas.all()`), y `Sala.save()` vuelve a guardar cada recurso. Así "B307" pasa a "D307" y "B307-B1-M2" a "D307-B1-M2" automáticamente.
</details>

<details><summary><b>¿Cómo se guardan las cantidades si un recurso tiene unidades y otro no?</b></summary>

Hay dos casos, igual que en el front. Los equipos e instrumentos (categoría con `usa_numero_serie`) tienen una `Unidad` por cada aparato, con su estado. Los insumos, reactivos y muebles usan los 5 campos `cantidad_disponible`, `cantidad_en_uso`, etc. `Recurso.obtener_cantidades()` resuelve los dos: si tiene unidades las cuenta por estado; si no, devuelve los campos. Martín y Diego usan este mismo método.
</details>

<details><summary><b>¿Por qué no guardan la cantidad total?</b></summary>

Porque se puede calcular sumando los estados y, si se guardara aparte, podría quedar desactualizada. Se calcula cada vez con `obtener_cantidad_total()` y se muestra con un `SerializerMethodField`.
</details>

<details><summary><b>¿Qué es <code>unique_together</code> y dónde lo usan?</b></summary>

Exige que una combinación de campos no se repita. `Sala`: (torre, número), no hay dos salas 307 en la torre B. `Unidad`: (recurso, número), el número de serie no se repite dentro del mismo recurso (CA-12.2), pero dos recursos distintos sí pueden tener una "0001".
</details>

<details><summary><b>¿Qué guarda un Movimiento?</b></summary>

Tipo (cambio de estado, entrada, salida, cambio de ubicación, alta), subtipo (adquisición, préstamo, reposición, daño reparable o irreparable), recurso, unidad (si aplica), usuario, fecha automática, estado anterior y nuevo, cantidad, motivo, valor anterior y nuevo en texto ("Disponible" → "Dañado" o "B307-B1-M2" → "C210-B2") y la fecha de la entrada. Son los campos de `CambioEstado.ts` del front.
</details>

<details><summary><b>¿Por qué la fecha del movimiento se ve distinta en MySQL que en la API?</b></summary>

Con `USE_TZ = True`, Django guarda las fechas en UTC en la base y las convierte a `America/Santiago` al mostrarlas. En MySQL se ve 3 horas más; en la API se ve la hora de Chile.
</details>

<details><summary><b>¿Por qué la búsqueda encuentra "Termómetro" escribiendo "termometro"?</b></summary>

Porque la base se creó con `COLLATE utf8mb4_unicode_ci`: esa forma de comparar no distingue mayúsculas ni tildes ("ci" = case insensitive). Por eso también "FLK-0001" y "flk-0001" cuentan como repetidos.
</details>

### 6.3 Serializers y validaciones

<details><summary><b>¿Qué valida la API al crear un recurso?</b></summary>

Que estén los campos obligatorios (nombre, categoría, sala, bodega, mueble), que la categoría y la sala existan, que las cantidades no sean negativas (`PositiveIntegerField`) y que la fecha de adquisición no sea futura (`validate_fecha_adquisicion`, CA-13.1). Al editar, además, que no cambien las cantidades a mano: se cambian con un movimiento.
</details>

<details><summary><b>¿Para qué pusieron <code>validators = []</code> en Sala y Unidad?</b></summary>

`unique_together` hace que DRF agregue un validador automático con un mensaje genérico ("Los campos torre, numero deben formar un conjunto único"). Lo quité y revisé lo mismo en `validate()` para dar un mensaje claro: "La sala B307 ya existe."
</details>

<details><summary><b>¿Por qué en el <code>validate()</code> se revisa <code>self.instance</code>?</b></summary>

`self.instance` es el objeto que se está editando; al crear es `None`. Sirve para dos cosas: excluir el mismo objeto cuando reviso repetidos (una sala no choca consigo misma) y, en un PATCH, tomar el valor actual de los campos que no vinieron.
</details>

<details><summary><b>¿Por qué la contraseña es <code>write_only</code>?</b></summary>

Para que se pueda mandar al crear el usuario pero nunca aparezca en las respuestas. Además se guarda **encriptada** con `create_user` / `set_password` (en la base queda `pbkdf2_sha256$...`), y se valida con los validadores de Django: mínimo 8 caracteres, que no sea muy común y que no sean solo números.
</details>

<details><summary><b>¿Cómo se evita que alguien registre un movimiento a nombre de otro?</b></summary>

`usuario` está en `read_only_fields`: si alguien lo manda en el JSON, se ignora. Lo pone `perform_create` con `serializer.save(usuario=self.request.user)`, que es quien inició sesión.
</details>

<details><summary><b>¿Qué pasa si falla algo a la mitad de un movimiento?</b></summary>

`MovimientoSerializer.create()` usa `transaction.atomic()`: cambiar la unidad (o las cantidades) y guardar el registro van juntos. Si algo falla, MySQL deshace todo; nunca queda un cambio sin su registro ni un registro sin su cambio.
</details>

### 6.4 Vistas, permisos y URLs

<details><summary><b>¿Por qué <code>usuarios/yo/</code> va antes que el router?</b></summary>

Django revisa las rutas en orden y usa la primera que coincide. El router tiene `usuarios/{id}/`, y "yo" calzaría como si fuera un id: se iría al CRUD (solo encargado) y daría 403 o 404. Poniéndola antes, "yo" llega a `YoView`.
</details>

<details><summary><b>¿Por qué el superusuario cuenta como encargado?</b></summary>

Porque `createsuperuser` no crea Perfil. En `obtener_rol()`, si `user.is_superuser` devuelvo encargado; así el administrador del sistema puede usar la API. Un usuario normal sin perfil no tiene rol y no ve nada.
</details>

<details><summary><b>¿Qué hace <code>borrar_o_avisar()</code>?</b></summary>

Intenta `objeto.delete()`. Si hay otros datos que dependen de él con `PROTECT`, Django lanza `ProtectedError`; la función lo atrapa y responde **400** con un mensaje ("No se puede eliminar: hay recursos en esta categoría"). Sin ella, la API respondería un error 500.
</details>

<details><summary><b>¿Cómo funciona el filtro <code>?estado=danado</code> si el estado no es un campo del recurso?</b></summary>

Lo programé en `get_queryset()`: leo `self.request.query_params.get('estado')`, reviso que sea un estado válido (si no, 400) y filtro con `Q(unidades__estado=estado) | Q(cantidad_danado__gt=0)`: recursos que tienen una unidad dañada **o** cantidad dañada mayor que 0. `distinct()` evita que un recurso salga repetido si tiene varias unidades dañadas.
</details>

<details><summary><b>¿Cuántas consultas hace el listado de recursos?</b></summary>

Tres, sin importar cuántos recursos haya: una para contar (paginación), una para los recursos con su categoría, sala y torre (`select_related`, un JOIN) y una para todas las unidades de esa página (`prefetch_related`). Sin eso serían decenas de consultas.
</details>

<details><summary><b>¿Por qué <code>/api/</code> se ve sin iniciar sesión?</b></summary>

`RaizAPI` tiene `permission_classes = [AllowAny]` porque solo muestra enlaces, no datos. Cada endpoint revisa sus propios permisos: `/api/recursos/` sigue dando 403 sin sesión.
</details>

<details><summary><b>¿Qué pasa si un usuario desactivado intenta entrar?</b></summary>

`is_active = False` hace que Django rechace su login (CA-15.3). Por eso los usuarios no se borran: se desactivan, y su historial y sus reservas quedan. Además, la API no deja desactivar ni quitarle el rol al último encargado activo.
</details>

### 6.5 Preguntas de "¿y si…?"

<details><summary><b>¿Cómo agregarían un rol nuevo, por ejemplo "ayudante"?</b></summary>

Agrego la opción en `Perfil.ROLES`, hago `makemigrations usuarios` (cambia el `choices`) y `migrate`, y decido qué puede hacer: lo agrego en las clases de `permisos.py` donde corresponda (por ejemplo, que pueda leer movimientos en `EsEncargadoODepartamento`).
</details>

<details><summary><b>¿Cómo conectará el front de React con esta API en la Unidad IV?</b></summary>

El login hará `POST /api/token/` con correo y contraseña y guardará el token. Después cada `fetch` manda `Authorization: Token <clave>`. Con `/api/usuarios/yo/` sabe el nombre y el rol para armar el menú. Habría que agregar CORS (`django-cors-headers`) porque el front corre en otro puerto.
</details>

<details><summary><b>¿Qué pasa si dos encargados mueven la misma unidad al mismo tiempo?</b></summary>

Cada movimiento va en una transacción y se valida contra el estado actual. En un caso extremo (exactamente al mismo tiempo) las dos validaciones podrían pasar; para evitarlo se usaría `select_for_update()`, que bloquea la fila mientras dura la transacción. Para el uso de un laboratorio no lo consideramos necesario.
</details>

<details><summary><b>¿Por qué la fecha de adquisición es opcional si el front la pide?</b></summary>

Porque la carga desde Excel (HU-16) no trae fecha: el front lee el Excel y hace un `POST /api/recursos/` por fila. Si la API la exigiera, esa carga fallaría. Sí se valida que no sea futura.
</details>

<details><summary><b>¿Dónde están las pruebas?</b></summary>

Cada paso lo probé contra la API (con los 3 roles, los casos de error y la base limpia). Como mejora, la fase 4 propone un `tests.py` por app con `APITestCase`: crear sin sesión → 403, crear como encargado → 201.
</details>

---

## 7. Cómo codear: recetas y ejercicios en vivo

### 7.1 Recetas

**Agregar un campo a un modelo** (ej: `modelo` en Recurso)
1. `inventario/models.py`: `modelo = models.CharField(max_length=60, blank=True)`
2. `python manage.py makemigrations inventario` → crea `0004_recurso_modelo.py`
3. `python manage.py migrate`
4. `inventario/serializers.py`: agregar `'modelo'` a `fields` de `RecursoSerializer`
5. Si se busca por él: agregarlo a `search_fields` en `views.py`
6. Probar en `/api/recursos/` → el campo aparece en el formulario.

**Agregar un endpoint CRUD nuevo** (ej: Proveedor)
1. Modelo en `models.py` → `makemigrations` → `migrate`
2. `class ProveedorSerializer(serializers.ModelSerializer)` con `model` y `fields`
3. `class ProveedorViewSet(viewsets.ModelViewSet)` con `queryset`, `serializer_class` y `permission_classes`
4. `router.register('proveedores', ProveedorViewSet)` en `inventario/urls.py`
5. `'proveedores': url('proveedor-list')` en `sgil/raiz.py`

**Agregar una validación**
- De un campo → `def validate_<campo>(self, valor):` en el serializer; `raise serializers.ValidationError('mensaje')` o `return valor`.
- De varios campos → `def validate(self, datos):`; devolver `datos`.

**Agregar un filtro** → agregar el campo a `filterset_fields` (exacto) o con lista de lookups: `'stock_minimo': ['gte', 'lte']`.

**Agregar un permiso** → clase en `usuarios/permisos.py` que herede de `BasePermission`, con `message` y `has_permission()` que use `obtener_rol()`; ponerla en `permission_classes` de la vista.

### 7.2 Ejercicios (intenta antes de abrir la solución)

<details><summary><b>E1. Que se pueda buscar recursos también por proveedor.</b></summary>

En `RecursoViewSet`:
```python
search_fields = ['nombre', 'marca', 'numero_serie', 'unidades__numero', 'proveedor']
```
Probar: `/api/recursos/?search=andina` → Sulfato de cobre.
</details>

<details><summary><b>E2. Que el listado de categorías salga de a 3 por página solo en esa vista.</b></summary>

```python
from rest_framework.pagination import PageNumberPagination

class PaginacionDeTres(PageNumberPagination):
    page_size = 3

class CategoriaViewSet(viewsets.ModelViewSet):
    ...
    pagination_class = PaginacionDeTres
```
</details>

<details><summary><b>E3. Mostrar en cada sala cuántos recursos tiene.</b></summary>

En `SalaSerializer`:
```python
cantidad_recursos = serializers.SerializerMethodField()

def get_cantidad_recursos(self, sala):
    return sala.recursos.count()   # related_name='recursos' de Recurso.sala
```
y agregar `'cantidad_recursos'` a `fields`.
</details>

<details><summary><b>E4. Que el nombre de una categoría tenga al menos 3 letras.</b></summary>

En `CategoriaSerializer`:
```python
def validate_nombre(self, valor):
    if len(valor.strip()) < 3:
        raise serializers.ValidationError('El nombre debe tener al menos 3 letras.')
    return valor.strip()
```
</details>

<details><summary><b>E5. Filtrar recursos por stock mínimo (ej: los que piden 5 o más).</b></summary>

En `filterset_fields` de `RecursoViewSet`:
```python
'stock_minimo': ['gte', 'lte'],
```
Probar: `/api/recursos/?stock_minimo__gte=5` → Guantes de nitrilo.
</details>

<details><summary><b>E6. Que el departamento también pueda ver la lista de usuarios (solo leer).</b></summary>

En `UsuarioViewSet`, cambiar `permission_classes = [EsEncargado]` por `[EsEncargadoODepartamento]` (importándolo): esa clase deja al encargado todo y al departamento solo los métodos de lectura.
</details>

<details><summary><b>E7. Un endpoint <code>GET /api/recursos/{id}/historial/</code> con los movimientos de ese recurso.</b></summary>

Con una acción extra del ViewSet (`@action`):
```python
from rest_framework.decorators import action

class RecursoViewSet(viewsets.ModelViewSet):
    ...
    @action(detail=True)
    def historial(self, request, pk=None):
        recurso = self.get_object()
        movimientos = recurso.movimientos.all()          # related_name='movimientos'
        return Response(MovimientoSerializer(movimientos, many=True).data)
```
El router crea la URL solo. (Hoy lo mismo se logra con `/api/movimientos/?recurso={id}`.)
</details>

### 7.3 Flujo de trabajo (Git)

1. GitHub Desktop: *Fetch origin* → *Pull* en `main` → *New branch* (`feature/...`).
2. Programar **un** paso.
3. `python manage.py check` y probar en el navegador.
4. Marcar **solo** los archivos de ese paso → mensaje `feat(app): ...` → *Commit*.
5. Al terminar el bloque: `makemigrations --check`, *Push*, *Create Pull Request*, revisor cruzado.

---

## 8. Códigos de respuesta HTTP que vas a ver

| Código | Significa | Cuándo pasa en el SGIL |
|---|---|---|
| **200** OK | Todo bien | GET, PUT, PATCH |
| **201** Created | Se creó | POST correcto |
| **204** No Content | Se borró | DELETE correcto |
| **400** Bad Request | Datos inválidos | Validación del serializer, `?estado=roto`, borrar algo con `PROTECT` |
| **403** Forbidden | No puedes | Sin sesión, o tu rol no tiene permiso |
| **404** Not Found | No existe | `/api/recursos/999/` |
| **405** Method Not Allowed | Ese método no existe aquí | DELETE de un movimiento o de un usuario, POST a `/yo/` |
| **500** Server Error | Error del programa | No debería pasar: por eso `borrar_o_avisar` |

<details><summary><b>¿Por qué sin sesión da 403 y no 401?</b></summary>

401 significa "falta autenticarse" y obliga a mandar el encabezado `WWW-Authenticate`. DRF usa la primera clase de autenticación para eso; la primera es `SessionAuthentication`, que no tiene ese encabezado, así que DRF responde 403. Si `TokenAuthentication` fuera la primera, respondería 401.
</details>

---

## 9. Decisiones de diseño (para declarar en la demo)

| Decisión | Por qué |
|---|---|
| Se inicia sesión con el **correo** (el `username` es el correo en minúsculas) | Igual que el login del front |
| Las categorías no tienen "clave" | En el front era el nombre del documento en Firestore; aquí lo reemplaza el `id` |
| Equipos e instrumentos tienen **unidades** con n° de serie en los datos de prueba | En la API esas categorías se mueven por unidad (HU-12) |
| La fecha de adquisición es **opcional** (pero no futura) | La carga Excel no trae fecha |
| **"Dado de baja" es definitivo** | Una unidad dada de baja salió del inventario; el front lo permitía |
| Las cantidades y el estado de las unidades **solo cambian con un movimiento** | Todo queda en el historial (HU-06, RNF-06) |
| Al borrar un recurso se borra su historial (`CASCADE`) | Si no, ningún recurso con movimientos se podría eliminar; mientras exista, el historial no se edita ni se borra |
| Los usuarios no se borran, se desactivan | Tienen historial, reservas e incidencias (CA-15.3) |
| Siempre queda al menos un encargado activo | Si no, nadie podría administrar los usuarios (misma regla del front) |
| Raíz `/api/` propia | Cada app tiene su router; la raíz automática solo mostraba una app |
| **Pendiente de decidir en grupo:** recuperar contraseña y correos (RF-09) | Requiere un servicio de correo; opción: backend de consola de Django |

---

## 10. Comandos útiles

| Comando | Para qué |
|---|---|
| `venv\Scripts\activate` | Activar el entorno virtual (Windows) |
| `python manage.py runserver` | Levantar el servidor en `http://127.0.0.1:8000/` |
| `python manage.py check` | Revisar que el proyecto no tenga errores |
| `python manage.py makemigrations <app>` | Generar migraciones de una app |
| `python manage.py migrate` | Aplicar migraciones en MySQL |
| `python manage.py makemigrations --check` | Confirmar que no falta ninguna migración |
| `python manage.py showmigrations` | Ver qué migraciones están aplicadas |
| `python manage.py loaddata usuarios inventario` | Cargar los datos de prueba |
| `python manage.py createsuperuser` | Crear un usuario para `/admin/` |
| `python manage.py shell` | Consola de Python con Django (probar consultas) |
| `pip install -r requirements.txt` | Instalar las dependencias |

Para probar en la consola (`python manage.py shell`):

```python
from inventario.models import Recurso
r = Recurso.objects.get(pk=1)
r.codigo_ubicacion            # 'B307-B1-M2'
r.obtener_cantidades()        # {'disponible': 12, 'en_uso': 0, 'danado': 1, ...}
r.unidades.filter(estado='danado')
r.movimientos.all()
```

---

## 11. Autoevaluación final

Marca cada punto cuando puedas hacerlo **sin mirar**:

- [ ] Dibujar el camino de una petición (sección 2) y explicar cada paso.
- [ ] Explicar los 7 modelos y cada `on_delete`.
- [ ] Explicar `source=`, el serializer anidado y `SerializerMethodField` con `RecursoSerializer`.
- [ ] Explicar la diferencia entre `ModelViewSet` y `APIView` con un ejemplo de cada uno.
- [ ] Explicar las 3 clases de permisos y `obtener_rol()`.
- [ ] Diferenciar filtrar, buscar, ordenar y paginar, con URLs de ejemplo.
- [ ] Explicar paso a paso qué pasa al registrar una salida por daño irreparable.
- [ ] Explicar cómo se registra solo el cambio de ubicación.
- [ ] Explicar por qué el historial no se edita ni se borra y cómo se logra.
- [ ] Explicar sesión vs token y cómo se conectará el front.
- [ ] Explicar cómo se conecta Django con MySQL.
- [ ] Hacer la demo completa (sección 5) sin errores, en menos de 6 minutos.
- [ ] Hacer al menos 3 ejercicios de la sección 7.2 sin mirar la solución.
- [ ] Explicar también, en términos generales, las apps de Martín (reservas, disponibilidad) y Diego (incidencias, alertas): la defensa evalúa que los tres conozcan todo el sistema.
