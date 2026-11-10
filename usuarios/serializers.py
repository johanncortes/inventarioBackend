"""
Serializers de la app usuarios (HU-15, RF-14).

El encargado administra los usuarios desde "Configuración": agregar, cambiar
el rol y desactivar. Los nombres de los campos son los del front
(src/types/Usuario.ts): nombre, correo, rol y activo. Por dentro se guardan en
el User de Django y en su Perfil:
    nombre → first_name      correo → email y username (se inicia sesión con el correo)
    rol    → perfil.rol      activo → is_active
"""
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from .models import Perfil
from .permisos import obtener_rol


def contar_encargados_activos(excepto=None):
    """Cuántos usuarios activos tienen rol de encargado, sin contar al usuario "excepto"."""
    cantidad = 0
    for usuario in User.objects.filter(is_active=True).select_related('perfil'):
        if usuario != excepto and obtener_rol(usuario) == Perfil.ENCARGADO:
            cantidad = cantidad + 1
    return cantidad


class UsuarioSerializer(serializers.ModelSerializer):
    """Un usuario con su rol. Para crear se pide además la contraseña."""

    # source= conecta el nombre del front con el campo de Django.
    nombre = serializers.CharField(source='first_name', max_length=150)
    correo = serializers.EmailField(source='email')
    activo = serializers.BooleanField(source='is_active', required=False, default=True)

    # El rol está en el Perfil (otra tabla): source='perfil.rol' lo saca de user.perfil.rol.
    rol = serializers.ChoiceField(source='perfil.rol', choices=Perfil.ROLES)

    # write_only: se recibe al crear (o para cambiarla), pero NUNCA se muestra.
    # style input_type password: la API navegable muestra puntitos en vez del texto.
    contrasena = serializers.CharField(
        write_only=True, required=False, style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ['id', 'nombre', 'correo', 'rol', 'activo', 'contrasena', 'last_login']
        read_only_fields = ['last_login']

    def validate_nombre(self, valor):
        nombre = valor.strip()
        if nombre == '':
            raise serializers.ValidationError('Escribe el nombre del usuario.')
        return nombre

    def validate_correo(self, valor):
        """El correo se guarda en minúsculas y no se puede repetir (CA-15.2)."""
        correo = valor.strip().lower()
        repetidos = User.objects.filter(username=correo)
        if self.instance is not None:
            repetidos = repetidos.exclude(pk=self.instance.pk)
        if repetidos.exists():
            raise serializers.ValidationError(f'Ya existe un usuario con el correo {correo}.')
        return correo

    def validate_contrasena(self, valor):
        """Usa los validadores de Django (largo mínimo, no muy común, no solo números)."""
        validate_password(valor)
        return valor

    def validate(self, datos):
        """Al crear se exige contraseña. Al editar, debe quedar al menos un encargado activo."""
        if self.instance is None and 'contrasena' not in datos:
            raise serializers.ValidationError({'contrasena': 'Escribe la contraseña inicial del usuario.'})

        if self.instance is not None:
            # Cómo quedaría el usuario después del cambio (si un dato no viene, se mantiene).
            rol_nuevo = datos.get('perfil', {}).get('rol', obtener_rol(self.instance))
            activo_nuevo = datos.get('is_active', self.instance.is_active)
            sigue_siendo_encargado = rol_nuevo == Perfil.ENCARGADO and activo_nuevo
            # Si deja de ser encargado activo, tiene que haber OTRO encargado activo.
            # Si no, nadie podría volver a administrar los usuarios.
            if not sigue_siendo_encargado and contar_encargados_activos(excepto=self.instance) == 0:
                raise serializers.ValidationError('Debe quedar al menos un encargado activo.')

        return datos

    def create(self, datos):
        """Crea el User (con la contraseña encriptada) y su Perfil, juntos."""
        rol = datos['perfil']['rol']
        with transaction.atomic():
            # create_user guarda la contraseña con set_password (encriptada), nunca en texto.
            usuario = User.objects.create_user(
                username=datos['email'],
                email=datos['email'],
                password=datos['contrasena'],
                first_name=datos['first_name'],
                is_active=datos.get('is_active', True),
            )
            Perfil.objects.create(usuario=usuario, rol=rol)
        return usuario

    def update(self, usuario, datos):
        """Cambia el nombre, el correo, el rol, si está activo y (si viene) la contraseña."""
        with transaction.atomic():
            if 'first_name' in datos:
                usuario.first_name = datos['first_name']
            if 'email' in datos:
                usuario.email = datos['email']
                usuario.username = datos['email']  # se inicia sesión con el correo
            if 'is_active' in datos:
                # is_active=False: Django ya no lo deja iniciar sesión (CA-15.3).
                usuario.is_active = datos['is_active']
            if 'contrasena' in datos:
                usuario.set_password(datos['contrasena'])
            usuario.save()

            if 'perfil' in datos:
                # Se usa el MISMO perfil que ya tiene el usuario (así la respuesta muestra el
                # rol nuevo). Un superusuario creado por consola no tiene Perfil: se le crea.
                if hasattr(usuario, 'perfil'):
                    perfil = usuario.perfil
                else:
                    perfil = Perfil(usuario=usuario)
                perfil.rol = datos['perfil']['rol']
                perfil.save()
        return usuario
