"""
Vistas de la app usuarios.

- UsuarioViewSet: el encargado agrega usuarios, cambia su rol y los desactiva (HU-15, RF-14).
- YoView: datos del usuario conectado, para cualquier rol (el front muestra su nombre
  y arma el menú según el rol).
"""
from django.contrib.auth.models import User
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .permisos import EsEncargado, obtener_rol
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


class YoView(APIView):
    """GET /api/usuarios/yo/: devuelve el usuario que inició sesión, con su rol.

    APIView (y no ViewSet) porque no es un CRUD: es una sola respuesta calculada
    a partir de request.user, el usuario que DRF reconoció por la sesión o el token.
    No usa EsEncargado: cualquier usuario conectado puede ver sus propios datos.
    Sin sesión responde 403 (IsAuthenticated de settings.py).
    """

    def get(self, request):
        datos = UsuarioSerializer(request.user).data
        # obtener_rol también resuelve al superusuario (no tiene Perfil, pero es encargado).
        datos['rol'] = obtener_rol(request.user)
        return Response(datos)
