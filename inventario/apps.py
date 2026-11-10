# Configuración de la app inventario (la usa INSTALLED_APPS en sgil/settings.py).
from django.apps import AppConfig


class InventarioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventario'
    verbose_name = 'Inventario'
