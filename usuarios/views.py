"""
Vistas de la app usuarios.

- UsuarioViewSet: el encargado agrega usuarios, cambia su rol y los desactiva (HU-15, RF-14).
"""
from django.contrib.auth.models import User
from rest_framework import viewsets

from .permisos import EsEncargado
from .serializers import UsuarioSerializer


class UsuarioViewSet(viewsets.ModelViewSet):
    """CRUD de usuarios, solo para el encargado. No se borran: se desactivan (CA-15.3)."""

    # select_related('perfil') trae el rol en la misma consulta.
    queryset = User.objects.select_related('perfil').order_by('first_name')
    serializer_class = UsuarioSerializer
    permission_classes = [EsEncargado]

    # Sin 'delete': un usuario con reservas, incidencias o historial no se puede
    # borrar; se desactiva con "activo": false (Django ya no lo deja iniciar sesión).
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']

    filterset_fields = ['is_active', 'perfil__rol']     # /api/usuarios/?perfil__rol=docente
    search_fields = ['first_name', 'email']              # /api/usuarios/?search=morales
    ordering_fields = ['first_name', 'email']
