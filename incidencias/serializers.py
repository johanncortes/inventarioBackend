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


class IncidenciaSerializer(serializers.ModelSerializer):
    """Incidencia con los nombres del recurso, la unidad y los usuarios.

    Para crear o editar se mandan los id (recurso, unidad, docente_presente);
    los campos *_nombre, *_numero y *_texto son solo para mostrar (read_only).
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

    def get_docente_presente_nombre(self, incidencia):
        """Nombre del docente que estaba presente (None si no se indicó)."""
        return nombre_de(incidencia.docente_presente)

    def get_registrada_por_nombre(self, incidencia):
        """Nombre de quien registró la incidencia."""
        return nombre_de(incidencia.registrada_por)

