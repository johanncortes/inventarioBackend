"""
Configuración de la app reservas.

Django la registra en settings.py (INSTALLED_APPS) para que cree sus tablas
con migrate y descubra sus modelos en el admin.
Cubre HU-03 (reservar recursos) y HU-07 (disponibilidad).
"""
from django.apps import AppConfig


class ReservasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reservas'
    verbose_name = 'Reservas'

