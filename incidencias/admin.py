"""
Admin de la app incidencias (/admin/).

Permite revisar las incidencias registradas con filtros por estado, fecha y
recurso, además de búsqueda por descripción o persona afectada.
"""
from django.contrib import admin

from .models import Incidencia


@admin.register(Incidencia)
class IncidenciaAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'recurso',
        'unidad',
        'estado',
        'hay_afectados',
        'docente_presente',
        'registrada_por',
        'fecha',
    ]
    list_filter = ['estado', 'hay_afectados', 'recurso__categoria', 'fecha']
    search_fields = ['descripcion', 'detalle_afectados', 'recurso__nombre', 'unidad__numero']
    ordering = ['-fecha']
