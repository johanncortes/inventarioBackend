"""
Permisos por rol del SGIL (RNF-03). Archivo compartido: lo usan las vistas de
inventario, usuarios, reservas e incidencias.

Cómo funciona un permiso en DRF: antes de ejecutar la vista, DRF llama a
has_permission(request, view). Si devuelve True, sigue; si devuelve False,
responde 403 con el texto de "message".

Resumen (tabla "Permisos por rol" del plan):
- EsEncargado ................. solo el encargado (gestión de usuarios).
- EsEncargadoOSoloLectura ..... todos leen, solo el encargado crea/edita/borra
                                (categorías, torres, salas, recursos, unidades).
- EsEncargadoODepartamento .... el encargado todo, el departamento solo lee y el
                                docente nada (movimientos, incidencias, alertas).
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import Perfil


def obtener_rol(user):
    """Devuelve el rol del usuario ('encargado', 'docente', 'departamento') o None si no tiene."""
    # Sin sesión no hay rol (DRF ya responde 403 por IsAuthenticated, esto es por seguridad).
    if not user or not user.is_authenticated:
        return None

    # El superusuario (creado con createsuperuser) no tiene Perfil,
    # pero se considera encargado para poder administrar todo.
    if user.is_superuser:
        return Perfil.ENCARGADO

    # hasattr evita el error si al usuario nunca se le creó su Perfil.
    if hasattr(user, 'perfil'):
        return user.perfil.rol

    return None


def es_lectura(request):
    """True si la petición solo lee datos.

    SAFE_METHODS son GET, HEAD y OPTIONS: los métodos que no cambian nada.
    La API navegable usa OPTIONS para dibujar sus formularios.
    """
    return request.method in SAFE_METHODS


class EsEncargado(BasePermission):
    """Solo el encargado de laboratorio puede usar la vista (cualquier método)."""

    message = 'Solo el encargado de laboratorio puede realizar esta acción.'

    def has_permission(self, request, view):
        return obtener_rol(request.user) == Perfil.ENCARGADO


class EsEncargadoOSoloLectura(BasePermission):
    """Cualquier usuario con rol puede leer; solo el encargado puede crear, editar o borrar."""

    message = 'Solo el encargado de laboratorio puede crear, editar o eliminar.'

    def has_permission(self, request, view):
        rol = obtener_rol(request.user)

        # Un usuario sin rol no ve nada.
        if rol is None:
            return False

        if es_lectura(request):
            return True

        return rol == Perfil.ENCARGADO


class EsEncargadoODepartamento(BasePermission):
    """El encargado puede todo, el departamento solo leer y el docente recibe 403."""

    message = 'Esta sección es solo para el encargado de laboratorio y el departamento.'

    def has_permission(self, request, view):
        rol = obtener_rol(request.user)

        if rol == Perfil.ENCARGADO:
            return True

        if rol == Perfil.DEPARTAMENTO:
            return es_lectura(request)

        return False
