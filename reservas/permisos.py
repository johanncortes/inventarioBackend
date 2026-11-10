"""
Permisos específicos de la app reservas (RNF-08).

EsDuenoOEncargado: se usa en has_object_permission para que un docente solo
pueda ver y editar SUS propias reservas. El encargado y el departamento ven
todas (tabla de permisos del plan, sección 3).
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission

from usuarios.permisos import obtener_rol
from usuarios.models import Perfil


class EsDuenoOEncargado(BasePermission):
    """El encargado accede a cualquier reserva; el docente solo a las suyas.

    has_object_permission se llama DESPUÉS de has_permission (que ya verificó
    que el usuario está autenticado y tiene un rol válido).
    """

    message = 'Solo puedes ver y editar tus propias reservas.'

    def has_object_permission(self, request, view, obj):
        rol = obtener_rol(request.user)

        # El encargado puede todo sobre cualquier reserva.
        if rol == Perfil.ENCARGADO:
            return True

        # El departamento solo lee (ya se chequeó en has_permission,
        # pero lo repetimos aquí por seguridad).
        if rol == Perfil.DEPARTAMENTO:
            return request.method in SAFE_METHODS

        # El docente solo ve y edita SUS reservas.
        return obj.docente == request.user

