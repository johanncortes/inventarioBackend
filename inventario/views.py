"""
Vistas de la app inventario.

Un ModelViewSet arma en una sola clase las 5 acciones del CRUD:
listar y crear (GET y POST a /api/categorias/), y ver, editar y borrar
(GET, PUT/PATCH y DELETE a /api/categorias/{id}/). El router las conecta a
las URLs (inventario/urls.py, J9).

Permisos (RF-08, RNF-05): todos los roles leen, solo el encargado crea,
edita y borra → EsEncargadoOSoloLectura (usuarios/permisos.py).
"""
from django.db import transaction
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from usuarios.permisos import EsEncargadoODepartamento, EsEncargadoOSoloLectura

from .models import ESTADOS, Categoria, Movimiento, Recurso, Sala, Torre, Unidad
from .serializers import (
    CategoriaSerializer,
    MovimientoSerializer,
    RecursoSerializer,
    SalaSerializer,
    TorreSerializer,
    UnidadSerializer,
)


def borrar_o_avisar(objeto, mensaje):
    """Borra el objeto. Si otros datos dependen de él (on_delete=PROTECT), responde 400 con un mensaje.

    Sin esto, Django lanza ProtectedError y la API respondería un error 500.
    """
    try:
        objeto.delete()
    except ProtectedError:
        return Response({'detail': mensaje}, status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_204_NO_CONTENT)


class CategoriaViewSet(viewsets.ModelViewSet):
    """CRUD de categorías (RF-08)."""

    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [EsEncargadoOSoloLectura]
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['nombre']

    def destroy(self, request, *args, **kwargs):
        """No se puede borrar una categoría que todavía tiene recursos."""
        return borrar_o_avisar(self.get_object(), 'No se puede eliminar: hay recursos en esta categoría.')


class TorreViewSet(viewsets.ModelViewSet):
    """CRUD de torres (RF-10)."""

    queryset = Torre.objects.all()
    serializer_class = TorreSerializer
    permission_classes = [EsEncargadoOSoloLectura]

    def destroy(self, request, *args, **kwargs):
        """No se puede borrar una torre que todavía tiene salas."""
        return borrar_o_avisar(self.get_object(), 'No se puede eliminar: la torre todavía tiene salas.')


class SalaViewSet(viewsets.ModelViewSet):
    """CRUD de salas (RF-10)."""

    # select_related trae la torre en la misma consulta (evita una consulta por cada sala).
    queryset = Sala.objects.select_related('torre').all()
    serializer_class = SalaSerializer
    permission_classes = [EsEncargadoOSoloLectura]
    filterset_fields = ['torre']           # /api/salas/?torre=1
    search_fields = ['codigo']             # /api/salas/?search=B30
    ordering_fields = ['codigo']

    def destroy(self, request, *args, **kwargs):
        """No se puede borrar una sala que todavía tiene recursos."""
        return borrar_o_avisar(self.get_object(), 'No se puede eliminar: hay recursos en esta sala.')


class RecursoViewSet(viewsets.ModelViewSet):
    """CRUD de recursos: listado del inventario, ficha, agregar, editar y eliminar (HU-01, HU-11, HU-12)."""

    # select_related trae la categoría, la sala y su torre en la MISMA consulta (son FK).
    # prefetch_related trae las unidades de todos los recursos en UNA consulta extra
    # (son "muchos" por recurso). Sin esto, la página haría una consulta por cada recurso.
    queryset = Recurso.objects.select_related('categoria', 'sala__torre').prefetch_related('unidades')
    serializer_class = RecursoSerializer
    permission_classes = [EsEncargadoOSoloLectura]

    # Filtros del inventario (HU-01, HU-13). django-filter los muestra como
    # formulario en el botón "Filtros" de la API navegable.
    #   ?categoria=2                    → recursos de esa categoría
    #   ?sala=5                         → recursos de esa sala (laboratorio)
    #   ?sala__torre=1                  → recursos de esa torre ("__" sigue la FK: sala → torre)
    #   ?fecha_adquisicion__gte=2024-01-01&fecha_adquisicion__lte=2024-12-31
    #                                   → antigüedad: adquiridos entre esas fechas (CA-13.3)
    filterset_fields = {
        'categoria': ['exact'],
        'sala': ['exact'],
        'sala__torre': ['exact'],
        'fecha_adquisicion': ['gte', 'lte'],
    }

    # Buscador (?search=multimetro): busca el texto dentro de estos campos.
    # unidades__numero también encuentra un recurso por el n° de serie de una de sus unidades.
    # MySQL compara sin importar mayúsculas ni tildes (collation utf8mb4_unicode_ci),
    # igual que el buscador del front.
    search_fields = ['nombre', 'marca', 'numero_serie', 'unidades__numero']

    # Orden (?ordering=-fecha_adquisicion: el "-" invierte el orden, más nuevos primero).
    ordering_fields = ['nombre', 'fecha_adquisicion', 'codigo_ubicacion']
    ordering = ['nombre']

    def get_queryset(self):
        """Agrega el filtro ?estado=danado: recursos con AL MENOS 1 unidad en ese estado (HU-01).

        No es un campo del modelo (el estado está en las unidades o en las cantidades),
        por eso se lee a mano desde request.query_params.
        """
        recursos = super().get_queryset()
        estado = self.request.query_params.get('estado')

        if estado is None or estado == '':
            return recursos

        estados_validos = [valor for valor, texto in ESTADOS]
        if estado not in estados_validos:
            raise ValidationError({'estado': f'Estado no válido. Usa uno de: {", ".join(estados_validos)}.'})

        # Q permite unir dos condiciones con "o" (|):
        #   - tiene una unidad con ese estado (equipos e instrumentos), o
        #   - su campo cantidad_<estado> es mayor que 0 (insumos, reactivos...).
        # distinct() evita que un recurso salga repetido si tiene varias unidades en ese estado.
        campo_cantidad = f'cantidad_{estado}__gt'
        return recursos.filter(Q(unidades__estado=estado) | Q(**{campo_cantidad: 0})).distinct()

    def perform_update(self, serializer):
        """Guarda los cambios del recurso y, si cambió su ubicación, lo deja en el historial (HU-11, CA-11.3).

        perform_update se ejecuta al editar (PUT o PATCH). Se compara el código de
        ubicación de antes y de después: si es distinto, se crea un Movimiento
        de tipo "cambio_ubicacion" con las dos ubicaciones.
        """
        ubicacion_anterior = serializer.instance.codigo_ubicacion

        # transaction.atomic(): el recurso y su movimiento se guardan juntos o no se guarda ninguno.
        with transaction.atomic():
            recurso = serializer.save()
            if recurso.codigo_ubicacion != ubicacion_anterior:
                Movimiento.objects.create(
                    tipo=Movimiento.CAMBIO_UBICACION,
                    recurso=recurso,
                    usuario=self.request.user,
                    valor_anterior=ubicacion_anterior,
                    valor_nuevo=recurso.codigo_ubicacion,
                )

    def destroy(self, request, *args, **kwargs):
        """Un recurso con reservas o incidencias no se puede borrar (on_delete=PROTECT en esas apps)."""
        return borrar_o_avisar(
            self.get_object(),
            'No se puede eliminar: el recurso tiene reservas o incidencias registradas.',
        )


class UnidadViewSet(viewsets.ModelViewSet):
    """CRUD de unidades con número de serie de equipos e instrumentos (HU-12, RF-11)."""

    queryset = Unidad.objects.select_related('recurso')
    serializer_class = UnidadSerializer
    permission_classes = [EsEncargadoOSoloLectura]
    filterset_fields = ['recurso', 'estado']   # /api/unidades/?recurso=3&estado=danado

    def destroy(self, request, *args, **kwargs):
        """Una unidad con incidencias registradas no se puede borrar."""
        return borrar_o_avisar(self.get_object(), 'No se puede eliminar: la unidad tiene incidencias registradas.')


class MovimientoViewSet(viewsets.ModelViewSet):
    """Historial de movimientos (HU-06) y registro de cambios de estado, entradas y salidas (HU-02, HU-14).

    Permisos: el encargado lee y registra; el departamento solo lee; el docente recibe 403.
    """

    queryset = Movimiento.objects.select_related('recurso', 'unidad', 'usuario')
    serializer_class = MovimientoSerializer
    permission_classes = [EsEncargadoODepartamento]
    filterset_fields = ['recurso', 'unidad', 'tipo']   # /api/movimientos/?recurso=3

    # El historial no se edita ni se borra (RNF-06): solo se permite leer (GET) y
    # registrar (POST). HEAD y OPTIONS son de solo lectura (la API navegable usa OPTIONS).
    # Un PUT, PATCH o DELETE responde 405 "Método no permitido".
    http_method_names = ['get', 'post', 'head', 'options']

    # El más nuevo primero (CA-06.3). ?ordering=fecha lo invierte.
    ordering = ['-fecha']
    ordering_fields = ['fecha']

    def perform_create(self, serializer):
        """Guarda quién registró el movimiento: el usuario conectado.

        perform_create se ejecuta justo antes de guardar. Así el usuario no se
        escribe en el formulario (no se puede registrar a nombre de otro).
        """
        serializer.save(usuario=self.request.user)
