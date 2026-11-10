"""
Admin de la app usuarios (/admin/).

Muestra el Perfil (rol) DENTRO de la página de cada usuario, para crear el
usuario y asignarle su rol en una sola pantalla.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Perfil


class PerfilInline(admin.StackedInline):
    """Muestra el formulario del Perfil debajo de los datos del usuario."""

    model = Perfil
    can_delete = False  # un usuario siempre debe tener su perfil
    verbose_name_plural = 'perfil'


class UsuarioAdmin(UserAdmin):
    """El admin de usuarios de Django, pero con el Perfil agregado y el rol en el listado."""

    inlines = [PerfilInline]
    list_display = ['username', 'first_name', 'last_name', 'email', 'obtener_rol', 'is_active']

    @admin.display(description='rol')
    def obtener_rol(self, usuario):
        # Un usuario creado sin perfil (por ejemplo, con createsuperuser) no tiene rol.
        if hasattr(usuario, 'perfil'):
            return usuario.perfil.get_rol_display()
        return '—'


# Django ya registró User con su admin original; se quita para registrar el nuestro.
admin.site.unregister(User)
admin.site.register(User, UsuarioAdmin)
