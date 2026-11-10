"""
Serializers de la app reservas.

ReservaSerializer convierte un objeto Reserva a JSON y viceversa.
Incluye validaciones de horario (CA-03.3) y disponibilidad (HU-07, HU-08).

Lógica de negocio:
  - validate(): valida que la fecha no sea pasada, que la hora de fin sea
    posterior a la de inicio y que haya unidades disponibles (usa disponibilidad.py).
  - Se importa disponibilidad aquí (y no en la vista) para mantener la lógica
    fuera de la capa de presentación (guía del plan, sección 6).
"""
from django.utils import timezone
from rest_framework import serializers

from .disponibilidad import sala_esta_ocupada, unidades_disponibles
from .models import Reserva


class ReservaSerializer(serializers.ModelSerializer):
    """Serializer de Reserva con nombres legibles del recurso, sala y docente.

    Los campos de solo lectura (docente_nombre, recurso_nombre, sala_codigo,
    estado) se calculan al devolver la reserva pero no se piden al crear.
    """

    # source='recurso.nombre': lee el campo 'nombre' del objeto relacionado 'recurso'.
    # Así el JSON devuelve el nombre en vez del id.
    recurso_nombre = serializers.CharField(source='recurso.nombre', read_only=True)

    # source='sala.codigo': el código de la sala (ej. "B307"). Puede ser None.
    sala_codigo = serializers.CharField(source='sala.codigo', read_only=True, allow_null=True)

    # source='docente.get_full_name': el nombre completo del docente.
    docente_nombre = serializers.CharField(source='docente.get_full_name', read_only=True)

    # El estado calculado (Programada, En curso, Realizada, Cancelada).
    # SerializerMethodField llama a get_estado() y pone su resultado en el JSON.
    estado = serializers.SerializerMethodField()

    class Meta:
        model = Reserva
        fields = [
            'id',
            'docente',          # id del docente (write); docente_nombre para leer
            'docente_nombre',
            'recurso',          # id del recurso (write); recurso_nombre para leer
            'recurso_nombre',
            'sala',             # id de la sala (write, opcional); sala_codigo para leer
            'sala_codigo',
            'cantidad',
            'fecha',
            'hora_inicio',
            'hora_fin',
            'asignatura',
            'motivo',
            'cancelada',
            'estado',
            'creada_en',
        ]
        # El docente lo asigna perform_create (no el formulario).
        # creada_en la pone Django solo (auto_now_add).
        # estado y los _nombre/_codigo se calculan (no se escriben en la base).
        read_only_fields = ['docente', 'creada_en', 'estado',
                            'docente_nombre', 'recurso_nombre', 'sala_codigo']

    def get_estado(self, reserva):
        """Calcula el estado textual de la reserva (CA-03.4).

        - Cancelada: si reserva.cancelada es True.
        - Programada: si la fecha+hora de inicio aún no llegó.
        - En curso: si ya empezó pero no ha terminado.
        - Realizada: si ya terminó.

        Se usan datetimes con zona horaria (timezone.now()) para comparar
        correctamente con la fecha y hora guardadas.
        """
        if reserva.cancelada:
            return 'Cancelada'

        # timezone.now() devuelve la hora actual en UTC; .date() y .time() extraen la parte.
        ahora = timezone.localtime(timezone.now())
        hoy = ahora.date()
        hora_ahora = ahora.time()

        if reserva.fecha > hoy:
            return 'Programada'

        if reserva.fecha == hoy:
            if hora_ahora < reserva.hora_inicio:
                return 'Programada'
            if hora_ahora <= reserva.hora_fin:
                return 'En curso'

        return 'Realizada'

    def validate(self, datos):
        """Valida los datos de la reserva antes de guardarla.

        Reglas (CA-03.3, HU-07, HU-08):
        1. La fecha no puede ser pasada.
        2. La hora de fin debe ser posterior a la de inicio.
        3. Deben haber unidades disponibles del recurso en ese horario.
        4. La sala no puede estar ocupada por otro docente en ese horario.
        """
        from django.utils.timezone import now

        fecha = datos.get('fecha')
        hora_inicio = datos.get('hora_inicio')
        hora_fin = datos.get('hora_fin')
        recurso = datos.get('recurso')
        sala = datos.get('sala')
        cantidad = datos.get('cantidad', 1)

        # 1. La fecha no puede ser del pasado (CA-03.3).
        if fecha and fecha < now().date():
            raise serializers.ValidationError(
                {'fecha': 'No se puede reservar en una fecha pasada.'}
            )

        # 2. La hora de fin debe ser posterior a la de inicio.
        if hora_inicio and hora_fin and hora_fin <= hora_inicio:
            raise serializers.ValidationError(
                {'hora_fin': 'La hora de fin debe ser posterior a la de inicio.'}
            )

        # Solo validar disponibilidad si todos los campos necesarios están presentes.
        if recurso and fecha and hora_inicio and hora_fin:

            # 3. Verificar que haya suficientes unidades disponibles (HU-07, HU-08).
            # Se excluye la reserva actual al editar (self.instance), para que no
            # choque consigo misma.
            reserva_actual = self.instance
            disponibles = unidades_disponibles(
                recurso, fecha, hora_inicio, hora_fin, excluir=reserva_actual
            )
            if cantidad > disponibles:
                raise serializers.ValidationError(
                    {
                        'cantidad': (
                            f'No hay suficientes unidades disponibles. '
                            f'Disponibles en ese horario: {disponibles}.'
                        )
                    }
                )

            # 4. La sala no puede estar ocupada por otro docente en ese horario (CA-08.3).
            # El mismo docente sí puede reservar varios recursos para su sala.
            if sala:
                docente = self.context['request'].user
                if sala_esta_ocupada(sala, fecha, hora_inicio, hora_fin,
                                     docente=docente, excluir=reserva_actual):
                    raise serializers.ValidationError(
                        {
                            'sala': (
                                f'La sala {sala.codigo} ya está reservada por otro docente '
                                f'en ese horario.'
                            )
                        }
                    )

        return datos

