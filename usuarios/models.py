"""
Modelos de la app usuarios.

Django ya trae el modelo User (usuario, contraseña, nombre, correo, is_active).
Aquí solo se agrega el Perfil, que guarda el ROL de cada usuario dentro del SGIL.
Cubre HU-15 (gestión de usuarios y roles) y la base de los permisos (RNF-03).
"""
from django.contrib.auth.models import User
from django.db import models


class Perfil(models.Model):
    """Datos extra de un usuario: por ahora, su rol en el sistema."""

    # Roles del sistema. La primera parte es lo que se guarda en la base
    # y la segunda es lo que se muestra en el admin y en la API navegable.
    ENCARGADO = 'encargado'
    DOCENTE = 'docente'
    DEPARTAMENTO = 'departamento'
    ROLES = [
        (ENCARGADO, 'Encargado de laboratorio'),
        (DOCENTE, 'Docente'),
        (DEPARTAMENTO, 'Departamento'),
    ]

    # OneToOneField = relación 1 a 1: cada User tiene un solo Perfil y viceversa.
    # CASCADE: si se borra el usuario, se borra también su perfil.
    # related_name='perfil' permite escribir user.perfil.rol desde el usuario.
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')

    # choices limita el campo a los tres roles; el admin lo muestra como lista.
    rol = models.CharField(max_length=20, choices=ROLES, default=DOCENTE)

    class Meta:
        verbose_name = 'perfil'
        verbose_name_plural = 'perfiles'

    def __str__(self):
        # get_rol_display() devuelve el texto del rol ("Docente") en vez del valor guardado.
        return f'{self.usuario.username} ({self.get_rol_display()})'
