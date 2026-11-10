"""
Página de inicio de la API (/api/): la lista de todos los endpoints del SGIL.

¿Por qué una vista propia? Cada app tiene su DefaultRouter, y cada router crea
su propia página /api/. Django usa solo la PRIMERA que encuentra, así que la
raíz automática mostraría solo los endpoints de una app. Esta vista va antes
que los include() en sgil/urls.py y junta los de todas las apps, incluidas las
vistas calculadas (/yo/, disponibilidad, alertas), que un router no lista.

Archivo compartido: cada integrante agrega sus endpoints dentro de sus marcadores.
"""
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView


class RaizAPI(APIView):
    """Endpoints del Sistema de Gestión de Inventario de Laboratorios (SGIL).

    Para usarlos, inicia sesión con "Log in" (arriba a la derecha).
    """

    # Cualquiera puede ver la lista de enlaces (no muestra datos). Cada endpoint
    # revisa después sus propios permisos.
    permission_classes = [AllowAny]

    def get_view_name(self):
        """Título que muestra la API navegable."""
        return 'API del SGIL'

    def get(self, request, format=None):
        # reverse() arma la URL completa a partir del NOMBRE de la ruta.
        # Los ViewSets registrados en un router se llaman <modelo>-list.
        def url(nombre):
            return reverse(nombre, request=request, format=format)

        endpoints = {
            # ===== Usuarios e inventario (Johann) =====
            'token': url('token'),
            'usuarios/yo': url('usuario-yo'),
            'usuarios': url('usuario-list'),
            'categorias': url('categoria-list'),
            'torres': url('torre-list'),
            'salas': url('sala-list'),
            'recursos': url('recurso-list'),
            'unidades': url('unidad-list'),
            'movimientos': url('movimiento-list'),
            # ===== Fin Usuarios e inventario (Johann) =====

            # ===== Reservas (Martín) =====
            # Ej: 'reservas': url('reserva-list'),
            # ===== Fin Reservas (Martín) =====

            # ===== Incidencias (Diego) =====
            'incidencias': url('incidencia-list'),
            'alertas': url('alerta-list'),
            # ===== Fin Incidencias (Diego) =====
        }
        return Response(endpoints)
