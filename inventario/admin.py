"""
Admin de la app inventario (/admin/).

Sirve para revisar y corregir datos a mano. La API es la forma principal de
usar el sistema; el admin es una ayuda para el encargado y para el equipo.
"""
from django.contrib import admin

from .models import Categoria, Recurso, Sala, Torre, Unidad


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion', 'usa_stock_minimo', 'usa_numero_serie']
    search_fields = ['nombre']


@admin.register(Torre)
class TorreAdmin(admin.ModelAdmin):
    list_display = ['letra']


@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'torre', 'numero']
    list_filter = ['torre']


class UnidadInline(admin.TabularInline):
    """Muestra las unidades (n° de serie y estado) dentro de la página del recurso, como tabla."""

    model = Unidad
    extra = 0  # no muestra filas vacías de más


@admin.register(Recurso)
class RecursoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'codigo_ubicacion', 'cantidad_disponible', 'fecha_adquisicion']
    list_filter = ['categoria', 'sala__torre', 'sala']
    search_fields = ['nombre', 'marca', 'numero_serie']
    inlines = [UnidadInline]


@admin.register(Unidad)
class UnidadAdmin(admin.ModelAdmin):
    list_display = ['numero', 'recurso', 'estado']
    list_filter = ['estado']
    search_fields = ['numero', 'recurso__nombre']
