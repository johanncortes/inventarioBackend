# Configuración de la app usuarios (la usa INSTALLED_APPS en sgil/settings.py).
from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usuarios'
    verbose_name = 'Usuarios'
