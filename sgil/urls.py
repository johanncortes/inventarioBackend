"""
URLs principales del proyecto SGIL.

Cada app (usuarios, inventario, reservas, incidencias) tiene su propio urls.py
y se conecta aquí con include(). Es un archivo compartido: cada integrante
agrega su línea dentro de sus marcadores.
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer

from .raiz import RaizAPI

urlpatterns = [
    path('admin/', admin.site.urls),

    # Login y logout de la API navegable (agrega el botón "Log in" arriba a la derecha).
    path('api-auth/', include('rest_framework.urls')),

    # Página de inicio con TODOS los endpoints (ver sgil/raiz.py).
    # Va antes que los include(): Django usa la primera ruta que coincide con /api/.
    path('api/', RaizAPI.as_view(), name='api-raiz'),

    # Entrega el token de un usuario: POST con username y password → {"token": "..."}.
    # Lo usará el front en la Unidad IV.
    # La vista de DRF solo responde JSON; con BrowsableAPIRenderer también se ve en
    # el navegador, con un formulario para probarla desde la API navegable.
    path(
        'api/token/',
        ObtainAuthToken.as_view(renderer_classes=[JSONRenderer, BrowsableAPIRenderer]),
        name='token',
    ),

    # ===== Usuarios e inventario (Johann) =====
    # include() suma las URLs de inventario/urls.py delante de "api/": /api/categorias/, etc.
    path('api/', include('inventario.urls')),
    path('api/', include('usuarios.urls')),
    # ===== Fin Usuarios e inventario (Johann) =====

    # ===== Reservas (Martín) =====
    path('api/', include('reservas.urls')),
    # ===== Fin Reservas (Martín) =====

    # ===== Incidencias (Diego) =====
    # /api/incidencias/ (incidencias/urls.py)
    path('api/', include('incidencias.urls')),
    # ===== Fin Incidencias (Diego) =====
]
