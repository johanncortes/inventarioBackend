# Configuración de la app incidencias (la usa INSTALLED_APPS en sgil/settings.py).
from django.apps import AppConfig


class IncidenciasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'incidencias'
    verbose_name = 'Incidencias y alertas'

