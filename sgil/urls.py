"""
URLs principales del proyecto SGIL.

Cada app (usuarios, inventario, reservas, incidencias) tiene su propio urls.py
y se conecta aquí con include(). Es un archivo compartido: cada integrante
agrega su línea dentro de sus marcadores.
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('admin/', admin.site.urls),

    # Login y logout de la API navegable (agrega el botón "Log in" arriba a la derecha).
    path('api-auth/', include('rest_framework.urls')),

    # Entrega el token de un usuario: POST con username y password → {"token": "..."}.
    # Lo usará el front en la Unidad IV.
    path('api/token/', obtain_auth_token),

    # ===== Usuarios e inventario (Johann) =====
    # include() suma las URLs de inventario/urls.py delante de "api/": /api/categorias/, etc.
    path('api/', include('inventario.urls')),
    path('api/', include('usuarios.urls')),
    # ===== Fin Usuarios e inventario (Johann) =====

    # ===== Reservas (Martín) =====
    # ===== Fin Reservas (Martín) =====

    # ===== Incidencias (Diego) =====
    # ===== Fin Incidencias (Diego) =====
]
