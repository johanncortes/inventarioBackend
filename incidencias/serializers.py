"""
Serializers de la app incidencias (Diego).

Un serializer convierte una Incidencia (una fila de la base) en JSON para la
API, y al revés: valida el JSON que llega en un POST/PUT/PATCH antes de guardarlo.

- IncidenciaSerializer: registrar y consultar incidencias (HU-04, HU-10).
"""
from rest_framework import serializers

from .models import Incidencia


def nombre_de(usuario):
    """Nombre completo del usuario, o su nombre de usuario si no tiene nombre. None si no hay usuario."""
    if usuario is None:
        return None
    nombre = usuario.get_full_name()
    if nombre == '':
        return usuario.username
    return nombre


# Flujo permitido de estados (HU-10): solo avanzar, nunca retroceder
# pendiente -> en_revision -> resuelta
TRANSICIONES_VALIDAS = {
    Incidencia.PENDIENTE: [Incidencia.PENDIENTE, Incidencia.EN_REVISION],
    Incidencia.EN_REVISION: [Incidencia.EN_REVISION, Incidencia.RESUELTA],
    Incidencia.RESUELTA: [Incidencia.RESUELTA],
}


class IncidenciaSerializer(serializers.ModelSerializer):
    """Incidencia con los nombres del recurso, la unidad y los usuarios.

    Para crear se mandan solo: recurso, unidad (opcional), descripcion,
    docente_presente (opcional), hay_afectados y detalle_afectados.
    La fecha, el estado y quién la registra los guarda el sistema (D5, HU-10).
    """

    # source= saca el dato del objeto relacionado: así el JSON muestra
    # "Multímetro Fluke 87V" además del id del recurso, sin pedirlo aparte.
    recurso_nombre = serializers.CharField(source='recurso.nombre', read_only=True)

    # La unidad es opcional: default='' evita un error cuando la incidencia no tiene unidad.
    unidad_numero = serializers.CharField(source='unidad.numero', read_only=True, default='')

    # get_estado_display: el texto del estado ("En revisión") además del valor guardado ("en_revision").
    estado_texto = serializers.CharField(source='get_estado_display', read_only=True)

    # SerializerMethodField: el valor lo calcula el método get_<nombre> de abajo.
    docente_presente_nombre = serializers.SerializerMethodField()
    registrada_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Incidencia
        fields = [
            'id',
            'recurso', 'recurso_nombre',
            'unidad', 'unidad_numero',
            'descripcion',
            'docente_presente', 'docente_presente_nombre',
            'hay_afectados', 'detalle_afectados',
            'estado', 'estado_texto',
            'fecha',
            'registrada_por', 'registrada_por_nombre',
        ]
        # Al crear (POST), estos 3 campos no se escriben a mano:
        # - fecha: auto_now_add del modelo (momento exacto).
        # - registrada_por: lo pone la vista con request.user (perform_create, D5).
        # - estado: nace siempre en 'pendiente' (default del modelo, D5).
        read_only_fields = ['fecha', 'registrada_por']
        extra_kwargs = {
            'estado': {'required': False},
        }

    def validate_estado(self, nuevo_estado):
        """Valida que el estado solo pueda avanzar (pendiente -> en_revision -> resuelta) y no retroceder (D8, HU-10)."""
        # Si se está creando (self.instance is None), el default es 'pendiente'
        if self.instance is None:
            return nuevo_estado

        estado_actual = self.instance.estado
        permitidos = TRANSICIONES_VALIDAS.get(estado_actual, [])

        if nuevo_estado not in permitidos:
            raise serializers.ValidationError(
                f'No se puede cambiar el estado de "{self.instance.get_estado_display()}" '
                f'a "{dict(Incidencia.ESTADOS).get(nuevo_estado, nuevo_estado)}". El estado solo puede avanzar sin retroceder.'
            )

        return nuevo_estado

    def validate(self, datos):
        """Validaciones de negocio al registrar o editar una incidencia (HU-04, CA-12.4).

        1. Si hay personas afectadas (hay_afectados=True), el detalle es obligatorio.
        2. Si se selecciona una unidad, debe pertenecer al recurso indicado.
        """
        # En caso de PATCH, tomar los valores existentes si no vienen en la petición
        recurso = datos.get('recurso')
        if recurso is None and self.instance is not None:
            recurso = self.instance.recurso

        unidad = datos.get('unidad')
        if 'unidad' not in datos and self.instance is not None:
            unidad = self.instance.unidad

        hay_afectados = datos.get('hay_afectados')
        if hay_afectados is None and self.instance is not None:
            hay_afectados = self.instance.hay_afectados

        detalle_afectados = datos.get('detalle_afectados', '')
        if 'detalle_afectados' not in datos and self.instance is not None:
            detalle_afectados = self.instance.detalle_afectados

        # Regla 1 (HU-04, CA-04.2): si hay personas afectadas, exigir detalle
        if hay_afectados and not detalle_afectados.strip():
            raise serializers.ValidationError({
                'detalle_afectados': 'Debe especificar el detalle de las personas afectadas.'
            })

        # Regla 2 (CA-12.4): si se indica una unidad, debe pertenecer al recurso
        if unidad is not None and recurso is not None:
            if unidad.recurso_id != recurso.id:
                raise serializers.ValidationError({
                    'unidad': f'La unidad "{unidad.numero}" no pertenece al recurso {recurso.nombre}.'
                })

        return datos

    def get_docente_presente_nombre(self, incidencia):
        """Nombre del docente que estaba presente (None si no se indicó)."""
        return nombre_de(incidencia.docente_presente)

    def get_registrada_por_nombre(self, incidencia):
        """Nombre de quien registró la incidencia."""
        return nombre_de(incidencia.registrada_por)
