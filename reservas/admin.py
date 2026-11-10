"""
Admin de la app reservas.

Registra el modelo Reserva para que el encargado pueda administrarlo
desde /admin/. Útil para cargar datos de prueba y depurar.
"""
from django.contrib import admin

from .models import Reserva


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    """Panel de administración de reservas."""

    # Columnas que se ven en la lista de reservas del admin.
    list_display = ['docente', 'recurso', 'sala', 'fecha', 'hora_inicio', 'hora_fin', 'cancelada']

    # Filtros de la barra lateral derecha del admin.
    list_filter = ['cancelada', 'fecha', 'recurso']

    # Buscador del admin (distinto del buscador de la API).
    search_fields = ['docente__first_name', 'docente__last_name', 'recurso__nombre', 'asignatura']

    # Ordenar por fecha ascendente en el admin.
    ordering = ['fecha', 'hora_inicio']

