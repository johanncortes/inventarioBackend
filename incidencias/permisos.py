"""
Permisos específicos de la app incidencias (Diego, RNF-03).

Reglas de acceso para Incidencias y Alertas (según plan EVA2 sección 3 y 9):
- Docente: 403 Prohibido (no tiene acceso ni a incidencias ni a alertas).
- Departamento: Solo lectura (GET, HEAD, OPTIONS).
- Encargado: Acceso completo (lectura, registro y avance de estados).
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission

from usuarios.models import Perfil
from usuarios.permisos import obtener_rol


class PermisoIncidencias(BasePermission):
    """Permiso para el endpoint de incidencias.

    - Encargado: puede leer y crear/modificar incidencias.
    - Departamento: solo lectura (SAFE_METHODS).
    - Docente / Sin rol: 403 Forbidden.
    """

    message = 'Solo el encargado puede registrar o modificar incidencias. El departamento solo tiene acceso de lectura.'

    def has_permission(self, request, view):
        rol = obtener_rol(request.user)

        # Sin rol o docente: no entra
        if rol is None or rol == Perfil.DOCENTE:
            return False

        # El encargado puede realizar cualquier acción
        if rol == Perfil.ENCARGADO:
            return True

        # El departamento solo puede consultar
        if rol == Perfil.DEPARTAMENTO:
            return request.method in SAFE_METHODS

        return False
