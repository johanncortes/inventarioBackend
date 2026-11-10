# Reglas de código del proyecto SGIL — API (EVA2)

Backend del Sistema de Gestión de Inventario de Laboratorios (SGIL) con Django 4.2 + Django REST Framework 3.16 + MySQL.
El plan completo está en `docs/plan-eva2-backend.md`. Leerlo antes de hacer cualquier cambio.

## Áreas (no tocar la app de otro integrante)

- **Johann:** `sgil/`, `usuarios/`, `inventario/`
- **Martín:** `reservas/`
- **Diego:** `incidencias/` (incluye `alertas.py`)

Archivos compartidos: `sgil/settings.py`, `sgil/urls.py`, `requirements.txt`, `README.md` y `usuarios/permisos.py`.
Los cambios en ellos van en un commit pequeño aparte y dentro de marcadores:
`# ===== Reservas (Martín) =====` … `# ===== Fin Reservas (Martín) =====`.

## Cómo escribir el código

- **`ModelViewSet` + `DefaultRouter`** para los CRUD. **`APIView`** solo para lo calculado (disponibilidad, alertas, `/yo/`).
- Código **simple**, de estudiante de pregrado: `if/else` claros, funciones cortas, nada de metaclases, mixins propios ni herencias complicadas.
- La lógica (validar, calcular disponibilidad, aplicar un movimiento, calcular alertas) va en archivos aparte
  (`disponibilidad.py`, `movimientos.py`, `alertas.py`) o en el `validate()` del serializer, no dentro de la vista.
- Nombres en **español** y en `snake_case` (`fecha_adquisicion`, `unidades_disponibles`).
- **Comentarios en español** en todos los archivos:
  - al inicio, qué hace el archivo y qué HU/RF cubre;
  - antes de cada clase o función, qué hace;
  - el **porqué** de lo que no es obvio (qué hace `source=`, por qué `PROTECT`, qué hace `perform_create`).
- Rutas siempre con `BASE_DIR / 'carpeta'`, nunca `C:\...` (el proyecto corre en Windows y macOS).
- No instalar paquetes fuera de `requirements.txt` sin preguntar al grupo.

## Migraciones

- Cada uno genera solo las de su app: `python manage.py makemigrations <app>`.
- Nunca editar ni borrar migraciones ya subidas, ni las de otra app.

## Forma de trabajar con la IA

- Un pedido = **un commit** del plan (J1, J2, M1, D1…). Mostrar qué se cambió y esperar confirmación antes de seguir.
- Antes de dar un paso por terminado: `python manage.py check` sin errores.
- Nunca subir `venv/`, `__pycache__/`, `.env` ni `db.sqlite3`.
