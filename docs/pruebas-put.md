# Pruebas de errores con PUT

Peticiones **PUT** para comprobar que la API rechaza los datos inválidos y los accesos sin permiso.
Cada prueba debe **fallar** con el código y el mensaje indicados. Si alguna responde **200**, el control no está funcionando (y además se guardó el cambio).

## Cómo hacerlas

1. Deja la base limpia: `bd/crear_bd.sql` → `python manage.py migrate` → `python manage.py loaddata usuarios inventario reservas incidencias`.
2. `python manage.py runserver` y entra con **Log in** usando el usuario que pide cada prueba (contraseña `prueba123`).
3. Abre la URL de la prueba, baja hasta el formulario, elige la pestaña **Raw data** con *Content type* `application/json`, pega el JSON y presiona **PUT**.

> Un PUT reemplaza el objeto **completo**: hay que mandar todos los campos obligatorios, aunque no cambien. Por eso cada JSON trae todo, y solo tiene **un** dato malo.
>
> Los mensajes pueden variar un poco en la redacción; lo importante es el código y el campo que marca el error.

| Usuario | Correo |
|---|---|
| Encargado | `encargado@prueba.cl` |
| Docente (Ana Morales, id 2) | `docente@prueba.cl` |
| Departamento | `departamento@prueba.cl` |

---

## 1. Usuarios — `/api/usuarios/{id}/` (Johann)

**1.1 Correo repetido (CA-15.2)** · Encargado · `PUT /api/usuarios/2/`
```json
{"nombre": "Prof. Ana Morales", "correo": "encargado@prueba.cl", "rol": "docente", "activo": true}
```
→ **400** `correo`: "Ya existe un usuario con el correo encargado@prueba.cl."

**1.2 Dejar el sistema sin encargado** · Encargado · `PUT /api/usuarios/1/`
```json
{"nombre": "Pedro Soto", "correo": "encargado@prueba.cl", "rol": "docente", "activo": true}
```
→ **400** "Debe quedar al menos un encargado activo."
(Si creaste un superusuario con `createsuperuser`, este cuenta como encargado y el PUT sí pasa.)

**1.3 Contraseña débil** · Encargado · `PUT /api/usuarios/2/`
```json
{"nombre": "Prof. Ana Morales", "correo": "docente@prueba.cl", "rol": "docente", "activo": true, "contrasena": "123"}
```
→ **400** `contrasena`: demasiado corta, demasiado común y solo numérica.

**1.4 Rol que no existe** · Encargado · `PUT /api/usuarios/2/`
```json
{"nombre": "Prof. Ana Morales", "correo": "docente@prueba.cl", "rol": "admin", "activo": true}
```
→ **400** `rol`: "admin" no es una elección válida.

**1.5 Docente intenta editar usuarios** · Docente · `PUT /api/usuarios/2/`
```json
{"nombre": "Ana", "correo": "docente@prueba.cl", "rol": "encargado", "activo": true}
```
→ **403** "Solo el encargado de laboratorio puede realizar esta acción."

---

## 2. Configuración: categorías, torres y salas (Johann)

**2.1 Categoría con nombre repetido** · Encargado · `PUT /api/categorias/2/`
```json
{"nombre": "Instrumento", "descripcion": "Materiales que se gastan con el uso, como guantes.", "usa_stock_minimo": true, "usa_numero_serie": false}
```
→ **400** `nombre`: ya existe una categoría con este nombre.

**2.2 Descripción de más de 120 caracteres (RF-08)** · Encargado · `PUT /api/categorias/2/`
```json
{"nombre": "Insumo", "descripcion": "Materiales que se gastan con el uso, como guantes, mascarillas, papel filtro, toallas, pipetas desechables y muchos otros elementos de laboratorio.", "usa_stock_minimo": true, "usa_numero_serie": false}
```
→ **400** `descripcion`: no puede tener más de 120 caracteres.

**2.3 Docente intenta editar una categoría** · Docente · `PUT /api/categorias/1/`
```json
{"nombre": "Instrumento", "descripcion": "Prueba"}
```
→ **403** "Solo el encargado de laboratorio puede crear, editar o eliminar."

**2.4 Torre repetida** · Encargado · `PUT /api/torres/2/`
```json
{"letra": "B"}
```
→ **400** `letra`: "La torre B ya existe."

**2.5 Torre que no es una letra** · Encargado · `PUT /api/torres/2/`
```json
{"letra": "7"}
```
→ **400** `letra`: "La torre debe ser una sola letra, ej: "D"."

**2.6 Sala repetida en la misma torre** · Encargado · `PUT /api/salas/1/`
```json
{"torre": 1, "numero": "307"}
```
→ **400** "La sala B307 ya existe."

**2.7 Número de sala con letras** · Encargado · `PUT /api/salas/1/`
```json
{"torre": 1, "numero": "30A"}
```
→ **400** `numero`: "El número de sala debe ser un número, ej: "305"."

**2.8 Sala en una torre que no existe** · Encargado · `PUT /api/salas/1/`
```json
{"torre": 99, "numero": "302"}
```
→ **400** `torre`: clave primaria "99" inválida, el objeto no existe.

---

## 3. Inventario: recursos y unidades (Johann)

Los recursos se prueban con los **guantes de nitrilo** (id 7, 2 disponibles, stock mínimo 5).

**3.1 Fecha de adquisición futura (CA-13.1)** · Encargado · `PUT /api/recursos/7/`
```json
{"nombre": "Guantes de nitrilo (caja 100 un.)", "categoria": 2, "sala": 5, "bodega": "Bodega 2", "mueble": "Mueble 1", "stock_minimo": 5, "fecha_adquisicion": "2030-01-01"}
```
→ **400** `fecha_adquisicion`: "La fecha de adquisición no puede ser futura."

**3.2 Cambiar la cantidad sin un movimiento (HU-06)** · Encargado · `PUT /api/recursos/7/`
```json
{"nombre": "Guantes de nitrilo (caja 100 un.)", "categoria": 2, "sala": 5, "bodega": "Bodega 2", "mueble": "Mueble 1", "stock_minimo": 5, "cantidad_disponible": 50}
```
→ **400** `cantidad_disponible`: "Las cantidades se cambian registrando un movimiento en /api/movimientos/…"

**3.3 PUT sin un campo obligatorio** · Encargado · `PUT /api/recursos/7/`
```json
{"nombre": "Guantes de nitrilo (caja 100 un.)", "categoria": 2, "sala": 5, "mueble": "Mueble 1"}
```
→ **400** `bodega`: "Este campo es requerido." (Con PATCH sí se puede omitir.)

**3.4 Categoría que no existe** · Encargado · `PUT /api/recursos/7/`
```json
{"nombre": "Guantes de nitrilo (caja 100 un.)", "categoria": 99, "sala": 5, "bodega": "Bodega 2", "mueble": "Mueble 1"}
```
→ **400** `categoria`: clave primaria "99" inválida.

**3.5 Departamento intenta editar un recurso** · Departamento · `PUT /api/recursos/7/` (mismo JSON de 3.1)
→ **403** "Solo el encargado de laboratorio puede crear, editar o eliminar."

**3.6 Cambiar el estado de una unidad sin un movimiento** · Encargado · `PUT /api/unidades/13/` (FLK-0013, dañada)
```json
{"recurso": 1, "numero": "FLK-0013", "estado": "disponible"}
```
→ **400** `estado`: "El estado se cambia registrando un movimiento en /api/movimientos/…"

**3.7 Número de serie repetido en el recurso (CA-12.2)** · Encargado · `PUT /api/unidades/13/`
```json
{"recurso": 1, "numero": "FLK-0001", "estado": "danado"}
```
→ **400** `numero`: "El número "FLK-0001" ya está registrado en Multímetro Fluke 87V…"

**3.8 Estado que no existe** · Encargado · `PUT /api/unidades/13/`
```json
{"recurso": 1, "numero": "FLK-0013", "estado": "roto"}
```
→ **400** `estado`: "roto" no es una elección válida.

**3.9 Editar el historial (RNF-06)** · Encargado · `PUT /api/movimientos/1/`
```json
{"motivo": "cambiado"}
```
→ **405** Método "PUT" no permitido.

---

## 4. Reservas — `/api/reservas/{id}/` (Martín)

Reservas de Ana Morales: la **1** (5 multímetros, sala B302, 10/12/2026 08:30–10:00) y la **5** (5 termómetros, sala C210, 09/12/2026 08:30–10:00). La **4** es de Carlos Fuentes y la **6**, de Jorge Paredes (3 termómetros, sala C205, misma hora que la 5).

**4.1 Fecha pasada (CA-03.3)** · Docente · `PUT /api/reservas/1/`
```json
{"recurso": 1, "sala": 1, "cantidad": 5, "fecha": "2026-01-10", "hora_inicio": "08:30", "hora_fin": "10:00", "asignatura": "Química I", "motivo": "Práctica de laboratorio: medición de temperatura", "cancelada": false}
```
→ **400** `fecha`: "No se puede reservar en una fecha pasada."

**4.2 Hora de fin antes de la de inicio (CA-03.3)** · Docente · `PUT /api/reservas/1/`
```json
{"recurso": 1, "sala": 1, "cantidad": 5, "fecha": "2026-12-10", "hora_inicio": "08:30", "hora_fin": "08:00", "asignatura": "Química I", "motivo": "Práctica de laboratorio: medición de temperatura", "cancelada": false}
```
→ **400** `hora_fin`: "La hora de fin debe ser posterior a la de inicio."

**4.3 Más unidades de las que hay (HU-07)** · Docente · `PUT /api/reservas/1/`
```json
{"recurso": 1, "sala": 1, "cantidad": 50, "fecha": "2026-12-10", "hora_inicio": "08:30", "hora_fin": "10:00", "asignatura": "Química I", "motivo": "Práctica de laboratorio: medición de temperatura", "cancelada": false}
```
→ **400** `cantidad`: "No hay suficientes unidades disponibles. Disponibles en ese horario: 12."

**4.4 Cantidad 0** · Docente · `PUT /api/reservas/1/` (mismo JSON de 4.3 con `"cantidad": 0`)
→ **400** `cantidad`: "Debes reservar al menos 1 unidad."

**4.5 Termómetros ocupados por otro docente (HU-08)** · Docente · `PUT /api/reservas/5/`
```json
{"recurso": 6, "sala": 5, "cantidad": 6, "fecha": "2026-12-09", "hora_inicio": "08:30", "hora_fin": "10:00", "asignatura": "Física II", "motivo": "Práctico de temperatura", "cancelada": false}
```
→ **400** `cantidad`: "… Disponibles en ese horario: 5." (hay 8 y Jorge Paredes tiene 3 reservados)

**4.6 Sala ocupada por otro docente (CA-08.3)** · Docente · `PUT /api/reservas/5/`
```json
{"recurso": 6, "sala": 4, "cantidad": 5, "fecha": "2026-12-09", "hora_inicio": "08:30", "hora_fin": "10:00", "asignatura": "Física II", "motivo": "Práctico de temperatura", "cancelada": false}
```
→ **400** `sala`: "La sala C205 ya está reservada por otro docente en ese horario."

**4.7 Docente edita la reserva de otro** · Docente · `PUT /api/reservas/4/`
```json
{"recurso": 2, "sala": 2, "cantidad": 2, "fecha": "2026-12-08", "hora_inicio": "14:00", "hora_fin": "15:30", "asignatura": "Electrónica Básica", "motivo": "Medición de señales", "cancelada": false}
```
→ **404** No encontrado (para ella esa reserva "no existe").

**4.8 Encargado cambia datos de una reserva** · Encargado · `PUT /api/reservas/1/`
```json
{"recurso": 1, "sala": 1, "cantidad": 5, "fecha": "2026-12-10", "hora_inicio": "08:30", "hora_fin": "10:00", "asignatura": "Otra asignatura", "motivo": "Práctica de laboratorio: medición de temperatura", "cancelada": false}
```
→ **400** `asignatura`: "El encargado solo puede cancelar reservas, no cambiar sus datos."

**4.9 Departamento intenta editar** · Departamento · `PUT /api/reservas/1/` (mismo JSON de 4.8)
→ **403** "Solo el encargado de laboratorio puede crear, editar o eliminar."

---

## 5. Incidencias — `/api/incidencias/{id}/` (Diego)

Incidencias de prueba: la **1** está *en revisión*, la **2** *pendiente* (termómetro, unidad 100) y la **3** *resuelta* (derrame de sulfato de cobre).

**5.1 Volver de "Resuelta" a "Pendiente" (HU-10)** · Encargado · `PUT /api/incidencias/3/`
```json
{"recurso": 8, "descripcion": "Derrame menor de sulfato de cobre sobre mesón de trabajo al manipular el frasco.", "docente_presente": 5, "hay_afectados": true, "detalle_afectados": "Alumno presentó irritación cutánea leve en antebrazo. Se aplicó lavado con abundante agua según protocolo.", "estado": "pendiente"}
```
→ **400** `estado`: "No se puede cambiar el estado de "Resuelta" a "Pendiente". El estado solo puede avanzar sin retroceder."

**5.2 Volver de "En revisión" a "Pendiente"** · Encargado · `PUT /api/incidencias/1/`
```json
{"recurso": 1, "unidad": 13, "descripcion": "Punta de prueba rota durante la medición de resistencia en el laboratorio de Electrónica.", "docente_presente": 2, "hay_afectados": false, "detalle_afectados": "", "estado": "pendiente"}
```
→ **400** `estado`: no se puede cambiar de "En revisión" a "Pendiente".

**5.3 Estado que no existe** · Encargado · `PUT /api/incidencias/2/`
```json
{"recurso": 6, "unidad": 100, "descripcion": "Pantalla LCD sin lectura ni retroiluminación tras finalizar la experiencia de Química.", "docente_presente": 4, "hay_afectados": false, "detalle_afectados": "", "estado": "cerrada"}
```
→ **400** `estado`: "cerrada" no es una elección válida.

**5.4 Afectados sin detalle (HU-04)** · Encargado · `PUT /api/incidencias/2/`
```json
{"recurso": 6, "unidad": 100, "descripcion": "Pantalla LCD sin lectura ni retroiluminación tras finalizar la experiencia de Química.", "docente_presente": 4, "hay_afectados": true, "detalle_afectados": "", "estado": "pendiente"}
```
→ **400** `detalle_afectados`: "Debe especificar el detalle de las personas afectadas."

**5.5 Unidad de otro recurso (CA-12.4)** · Encargado · `PUT /api/incidencias/2/`
```json
{"recurso": 6, "unidad": 1, "descripcion": "Pantalla LCD sin lectura ni retroiluminación tras finalizar la experiencia de Química.", "docente_presente": 4, "hay_afectados": false, "detalle_afectados": "", "estado": "pendiente"}
```
→ **400** `unidad`: "La unidad "FLK-0001" no pertenece al recurso Termómetro digital."

**5.6 PUT sin descripción** · Encargado · `PUT /api/incidencias/2/`
```json
{"recurso": 6, "unidad": 100, "hay_afectados": false, "estado": "pendiente"}
```
→ **400** `descripcion`: "Este campo es requerido."

**5.7 Departamento intenta avanzar el estado** · Departamento · `PUT /api/incidencias/2/` (JSON de 5.4 con `"hay_afectados": false` y `"estado": "en_revision"`)
→ **403** "Solo el encargado puede registrar o modificar incidencias. El departamento solo tiene acceso de lectura."

**5.8 Docente intenta editar** · Docente · `PUT /api/incidencias/2/` (mismo JSON de 5.7)
→ **403** (el docente no tiene acceso a incidencias).

---

## 6. Sin sesión

Cierra sesión (**Log out**) y repite cualquier PUT → **403** "Las credenciales de autenticación no se proveyeron."
