"""
Vistas de la app inventario.

Un ModelViewSet arma en una sola clase las 5 acciones del CRUD:
listar y crear (GET y POST a /api/categorias/), y ver, editar y borrar
(GET, PUT/PATCH y DELETE a /api/categorias/{id}/). El router las conecta a
las URLs (inventario/urls.py, J9).

Permisos (RF-08, RNF-05): todos los roles leen, solo el encargado crea,
edita y borra → EsEncargadoOSoloLectura (usuarios/permisos.py).
"""
from django.db.models.deletion import ProtectedError
from rest_framework import status, viewsets
from rest_framework.response import Response

from usuarios.permisos import EsEncargadoOSoloLectura

from .models import Categoria, Recurso, Sala, Torre, Unidad
from .serializers import (
    CategoriaSerializer,
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
