"""
URLs principales del proyecto SGIL.

Cada app (usuarios, inventario, reservas, incidencias) tiene su propio urls.py
y se conecta aquí con include(). Es un archivo compartido: cada integrante
agrega su línea dentro de sus marcadores.
"""
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]
