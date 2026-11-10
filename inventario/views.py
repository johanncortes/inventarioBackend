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

from .models import Categoria, Sala, Torre
from .serializers import CategoriaSerializer, SalaSerializer, TorreSerializer


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
