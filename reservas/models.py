"""
Modelos de la app reservas.

- Reserva: una solicitud de un docente para usar un recurso (y/o sala) en un
  horario específico (HU-03, HU-07, HU-08).

Relaciones:
  Docente (User) ──< Reserva >── Recurso
                           └──> Sala

Los campos son los de las pantallas del front (src/types/Reserva.ts), pero en
snake_case: horaInicio → hora_inicio.
"""
from django.contrib.auth.models import User
from django.db import models

# Referencia cruzada a otra app: se usa el string 'app.Modelo' para evitar
# importaciones circulares (si se importara directamente, habría un ciclo).
# on_delete=PROTECT: no se puede borrar un Recurso o Sala que tiene reservas.


class Reserva(models.Model):
    """Una reserva de un recurso (y opcionalmente una sala) para un horario.

    Ejemplo: Prof. Ana Morales reserva 5 termómetros en la sala B307
    el 15/10/2024 de 08:30 a 10:00 para la asignatura Química I.
    """

    # El docente que hace la reserva. Lo asigna la vista (perform_create),
    # no el formulario, para que no se pueda reservar a nombre de otro.
    # PROTECT: un docente con reservas no se borra (se desactiva, HU-15).
    docente = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='reservas',
    )

    # El recurso que se reserva (FK a otra app: se usa el string 'app.Modelo').
    # PROTECT: no se puede borrar un recurso con reservas.
    recurso = models.ForeignKey(
        'inventario.Recurso',
        on_delete=models.PROTECT,
        related_name='reservas',
    )

    # La sala donde se va a usar el recurso. Es opcional (blank=True, null=True):
    # hay recursos que se llevan fuera del laboratorio.
    # PROTECT: no se puede borrar una sala con reservas.
    sala = models.ForeignKey(
        'inventario.Sala',
        on_delete=models.PROTECT,
        related_name='reservas',
        null=True,
        blank=True,
    )

    # Cuántas unidades del recurso se necesitan (HU-07, HU-08).
    cantidad = models.PositiveIntegerField(default=1)

    # Fecha y horario de la reserva (CA-03.3).
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    # Nombre de la asignatura o actividad (para los filtros y el historial).
    asignatura = models.CharField(max_length=100, blank=True)

    # Motivo u observación opcional del docente.
    motivo = models.TextField(blank=True)

    # True si el encargado o el propio docente la canceló (M11).
    # No se usa delete para conservar el historial (RNF-06).
    cancelada = models.BooleanField(default=False)

    # auto_now_add: Django pone la fecha y hora al crear el registro.
    # Sirve para saber cuándo se hizo la reserva (distinto de cuándo se usa).
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'reserva'
        verbose_name_plural = 'reservas'
        ordering = ['fecha', 'hora_inicio']  # las más próximas primero

    def __str__(self):
        return (
            f'{self.docente.get_full_name()} — {self.recurso.nombre}'
            f' ({self.fecha} {self.hora_inicio}–{self.hora_fin})'
        )

