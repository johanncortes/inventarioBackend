"""
Modelos de la app incidencias (Diego).

- Incidencia: un problema con un recurso del laboratorio (algo se rompió, se
  derramó un reactivo, alguien se lastimó...). La registra el encargado y
  avanza por los estados pendiente → en revisión → resuelta (HU-04, HU-10).

Las alertas (HU-05, HU-09) NO se guardan en la base: se calculan cada vez en
incidencias/alertas.py desde Recurso y Unidad (igual que en el front).

Relaciones: Recurso ──< Incidencia >── Unidad
                           ├── User (docente presente)
                           └── User (quien la registra)
"""
from django.contrib.auth.models import User
from django.db import models

from inventario.models import Recurso, Unidad


class Incidencia(models.Model):
    """Una incidencia de un recurso: qué pasó, con qué unidad, quién estaba y quién la registró."""

    # Estados de una incidencia (HU-10). Solo avanzan, nunca retroceden.
    PENDIENTE = 'pendiente'
    EN_REVISION = 'en_revision'
    RESUELTA = 'resuelta'
    ESTADOS = [
        (PENDIENTE, 'Pendiente'),
        (EN_REVISION, 'En revisión'),
        (RESUELTA, 'Resuelta'),
    ]

    # PROTECT: no se puede borrar un recurso que tiene incidencias registradas
    # (Django lanza ProtectedError y la vista de inventario responde 400).
    # related_name='incidencias' permite escribir recurso.incidencias.all().
    recurso = models.ForeignKey(Recurso, on_delete=models.PROTECT, related_name='incidencias')

    # La unidad exacta que tuvo el problema (equipos e instrumentos con n° de serie).
    # Es opcional (null=True, blank=True): los insumos y reactivos no tienen unidades.
    unidad = models.ForeignKey(
        Unidad, on_delete=models.PROTECT, null=True, blank=True, related_name='incidencias'
    )

    descripcion = models.TextField()  # qué pasó

    # Hay DOS FK al mismo modelo User. Por eso cada una necesita un related_name
    # distinto: si no, Django no sabría qué devolver con user.incidencia_set
    # y el check da error (fields.E304).
    #
    # El docente que estaba en el laboratorio cuando pasó (opcional).
    # limit_choices_to: la lista del formulario solo muestra usuarios con rol docente.
    docente_presente = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='incidencias_presenciadas',
        limit_choices_to={'perfil__rol': 'docente'},
    )

    # Quién registró la incidencia: lo guarda solo la vista con request.user
    # (perform_create, D5). Así no se puede registrar a nombre de otro (HU-10).
    # PROTECT: un usuario con incidencias no se borra (se desactiva, HU-15).
    registrada_por = models.ForeignKey(User, on_delete=models.PROTECT, related_name='incidencias_registradas')

    # ¿Hubo personas afectadas? Si es True, hay que contar qué les pasó (HU-04).
    hay_afectados = models.BooleanField(default=False)
    detalle_afectados = models.TextField(blank=True)

    # Nace siempre en "pendiente" (default=PENDIENTE, D5).
    # Solo cambia editando la incidencia en PUT/PATCH (D8).
    estado = models.CharField(max_length=20, choices=ESTADOS, default=PENDIENTE)

    # auto_now_add: Django pone la fecha y hora al crear el registro, y no se puede cambiar.
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'incidencia'
        verbose_name_plural = 'incidencias'
        ordering = ['-fecha']  # la más nueva primero

    def __str__(self):
        return f'{self.recurso.nombre} — {self.get_estado_display()}'
