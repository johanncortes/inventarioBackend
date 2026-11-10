"""
Serializers de la app inventario.

Un serializer convierte un objeto de Django (una fila de la base) en JSON para
la API, y al revés: valida el JSON que llega en un POST/PUT/PATCH antes de guardarlo.
ModelSerializer arma los campos solo, leyendo el modelo.

- Categoria, Torre y Sala: página "Configuración" (RF-08, RF-10, RNF-05).
- Recurso y Unidad: inventario y ficha del recurso (HU-01, HU-11, HU-12, HU-13).
- Movimiento: historial, cambios de estado, entradas y salidas (HU-02, HU-06, HU-14).
"""
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from . import movimientos
from .models import DISPONIBLE, Categoria, Movimiento, Recurso, Sala, Torre, Unidad


class CategoriaSerializer(serializers.ModelSerializer):
    """Categoría con su descripción breve y si usa stock mínimo o número de serie."""

    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'descripcion', 'usa_stock_minimo', 'usa_numero_serie']


class TorreSerializer(serializers.ModelSerializer):
    """Torre identificada por una letra (B, C...)."""

    # Se declara a mano para validar la letra con nuestros propios mensajes
    # (si no, DRF usa su validador de "único" con un mensaje genérico).
    letra = serializers.CharField(max_length=1)

    class Meta:
        model = Torre
        fields = ['id', 'letra']

    def validate_letra(self, valor):
        """La torre es UNA letra de la A a la Z y no se puede repetir (igual que el front)."""
        letra = valor.strip().upper()

        if len(letra) != 1 or letra < 'A' or letra > 'Z':
            raise serializers.ValidationError('La torre debe ser una sola letra, ej: "D".')

        repetidas = Torre.objects.filter(letra=letra)
        # self.instance es la torre que se está editando (None si se está creando).
        # Al editar, la torre no choca consigo misma.
        if self.instance is not None:
            repetidas = repetidas.exclude(pk=self.instance.pk)
        if repetidas.exists():
            raise serializers.ValidationError(f'La torre {letra} ya existe.')

        return letra


class SalaSerializer(serializers.ModelSerializer):
    """Sala de una torre. Se crea con la torre (id) y el número; el código "B307" se arma solo."""

    # source='torre.letra' saca el dato de la torre relacionada: así el JSON
    # muestra "B" además del id de la torre, sin tener que hacer otra consulta.
    torre_letra = serializers.CharField(source='torre.letra', read_only=True)

    class Meta:
        model = Sala
        fields = ['id', 'torre', 'torre_letra', 'numero', 'codigo']
        # codigo no se escribe: lo arma Sala.save().
        read_only_fields = ['codigo']
        # Se quita el validador automático de unique_together (torre, numero)
        # para revisar lo mismo en validate() con un mensaje más claro.
        validators = []

    def validate_numero(self, valor):
        """El número de sala son solo dígitos: "307"."""
        numero = valor.strip()
        if not numero.isdigit():
            raise serializers.ValidationError('El número de sala debe ser un número, ej: "305".')
        return numero

    def validate(self, datos):
        """Revisa que no exista otra sala con el mismo número en la misma torre."""
        # En un PATCH puede venir solo uno de los dos campos: el otro se toma de la sala actual.
        torre = datos.get('torre')
        numero = datos.get('numero')
        if self.instance is not None:
            if torre is None:
                torre = self.instance.torre
            if numero is None:
                numero = self.instance.numero

        repetidas = Sala.objects.filter(torre=torre, numero=numero)
        if self.instance is not None:
            repetidas = repetidas.exclude(pk=self.instance.pk)
        if repetidas.exists():
            raise serializers.ValidationError(f'La sala {torre.letra}{numero} ya existe.')

        return datos


class UnidadSerializer(serializers.ModelSerializer):
    """Una unidad con su número de serie y su estado (HU-12)."""

    # get_estado_display: el texto del estado ("Dañado") además del valor guardado ("danado").
    estado_texto = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = Unidad
        fields = ['id', 'recurso', 'numero', 'estado', 'estado_texto']
        # Se quita el validador automático de unique_together (recurso, numero),
        # que da un mensaje genérico, para revisarlo en validate() con uno claro.
        validators = []

    # Número vacío (CA-12.1): no hace falta revisarlo a mano. DRF quita los espacios
    # y responde "Este campo no puede estar en blanco." antes de llegar a validate().

    def validate(self, datos):
        """El número no se puede repetir dentro del mismo recurso (CA-12.2).

        MySQL compara sin importar mayúsculas (utf8mb4_unicode_ci), así que
        "abc-1" y "ABC-1" cuentan como repetidos, igual que en el front.
        """
        # En un PATCH puede venir solo uno de los dos campos: el otro se toma de la unidad actual.
        recurso = datos.get('recurso')
        numero = datos.get('numero')
        if self.instance is not None:
            if recurso is None:
                recurso = self.instance.recurso
            if numero is None:
                numero = self.instance.numero

        repetidas = Unidad.objects.filter(recurso=recurso, numero=numero)
        if self.instance is not None:
            repetidas = repetidas.exclude(pk=self.instance.pk)
        if repetidas.exists():
            raise serializers.ValidationError(
                {'numero': f'El número "{numero}" ya está registrado en {recurso.nombre}. '
                           'Cada unidad debe tener un número distinto.'}
            )

        return datos


class RecursoSerializer(serializers.ModelSerializer):
    """Recurso con los nombres de su categoría y ubicación, sus cantidades y sus unidades.

    Para crear o editar se mandan los id (categoria, sala); los campos *_nombre,
    *_codigo y las cantidades calculadas son solo para mostrar (read_only).
    """

    # source= saca el dato del objeto relacionado, así el front muestra
    # "Instrumento" y "B307" sin tener que pedir la categoría o la sala aparte.
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    sala_codigo = serializers.CharField(source='sala.codigo', read_only=True)
    torre = serializers.CharField(source='sala.torre.letra', read_only=True)

    # Las unidades van ANIDADAS dentro del recurso (la ficha las muestra en una tabla).
    # many=True porque son varias; read_only porque se crean en /api/unidades/ (J11).
    # Usa related_name='unidades' del modelo Unidad.
    unidades = UnidadSerializer(many=True, read_only=True)

    # SerializerMethodField: el valor lo calcula el método get_<nombre> de abajo.
    cantidades = serializers.SerializerMethodField()
    cantidad_total = serializers.SerializerMethodField()

    class Meta:
        model = Recurso
        fields = [
            'id', 'nombre',
            'categoria', 'categoria_nombre',
            'sala', 'sala_codigo', 'torre', 'bodega', 'mueble', 'codigo_ubicacion',
            # Cantidades que se escriben a mano (recursos sin n° de serie: insumos, reactivos...)
            'cantidad_disponible', 'cantidad_en_uso', 'cantidad_danado',
            'cantidad_en_mantencion', 'cantidad_dado_de_baja',
            # Cantidades calculadas (sirven para todos los recursos, con o sin unidades)
            'cantidades', 'cantidad_total',
            'unidades',
            'numero_serie', 'marca', 'proveedor', 'observacion',
            'stock_minimo', 'fecha_adquisicion',
        ]
        read_only_fields = ['codigo_ubicacion']

    def validate_fecha_adquisicion(self, fecha):
        """La fecha de adquisición no puede ser futura (HU-13, CA-13.1).

        Es opcional (puede venir vacía): la carga desde Excel no trae fecha
        y la ficha muestra "Sin fecha".
        """
        # timezone.localdate() es el día de hoy en Chile (TIME_ZONE = 'America/Santiago').
        if fecha is not None and fecha > timezone.localdate():
            raise serializers.ValidationError('La fecha de adquisición no puede ser futura.')
        return fecha

    def get_cantidades(self, recurso):
        """Cuántas unidades hay en cada estado (ver Recurso.obtener_cantidades)."""
        return recurso.obtener_cantidades()

    def get_cantidad_total(self, recurso):
        """La suma de todos los estados: lo que muestra la tarjeta del inventario."""
        return recurso.obtener_cantidad_total()


class MovimientoSerializer(serializers.ModelSerializer):
    """Un registro del historial. Al CREARLO se aplica el cambio en el inventario (HU-02, HU-14).

    Qué se manda en el POST según el tipo:
    - cambio_estado: recurso, estado_nuevo, motivo y
        · equipos/instrumentos: unidad
        · insumos/reactivos: estado_anterior y cantidad
    - entrada: recurso, subtipo (adquisicion/prestamo/reposicion), fecha_movimiento y
        · equipos/instrumentos: numero_unidad_nueva
        · insumos/reactivos: cantidad
    - salida: recurso, subtipo (dano_reparable/dano_irreparable), motivo y
        · equipos/instrumentos: unidad
        · insumos/reactivos: estado_anterior y cantidad
    """

    # Textos para mostrar en la tabla del historial (solo lectura).
    tipo_texto = serializers.CharField(source='get_tipo_display', read_only=True)
    recurso_nombre = serializers.CharField(source='recurso.nombre', read_only=True)
    unidad_numero = serializers.CharField(source='unidad.numero', read_only=True, default='')
    usuario_nombre = serializers.SerializerMethodField()

    # write_only: se recibe en el POST pero no se muestra en las respuestas.
    # No es un campo del modelo: sirve para crear la unidad que entra (equipos e instrumentos).
    numero_unidad_nueva = serializers.CharField(write_only=True, required=False, default='')

    class Meta:
        model = Movimiento
        fields = [
            'id', 'tipo', 'tipo_texto', 'subtipo',
            'recurso', 'recurso_nombre', 'unidad', 'unidad_numero', 'numero_unidad_nueva',
            'estado_anterior', 'estado_nuevo', 'cantidad', 'motivo',
            'valor_anterior', 'valor_nuevo',
            'fecha', 'fecha_movimiento', 'usuario', 'usuario_nombre',
        ]
        # usuario lo pone la vista (perform_create); fecha, Django; los valores, aplicar_movimiento().
        read_only_fields = ['fecha', 'usuario', 'valor_anterior', 'valor_nuevo']
        # cantidad tiene default=0 en el modelo; aquí se deja opcional para que
        # los equipos (que mueven 1 unidad) no tengan que mandarla.
        extra_kwargs = {'cantidad': {'required': False}}

    def get_usuario_nombre(self, movimiento):
        """Nombre completo de quien registró el movimiento, o su usuario si no tiene nombre."""
        nombre = movimiento.usuario.get_full_name()
        if nombre == '':
            return movimiento.usuario.username
        return nombre

    def validate(self, datos):
        """Revisa el movimiento con las reglas de inventario/movimientos.py y completa los estados."""
        tipo = datos['tipo']
        recurso = datos['recurso']
        unidad = datos.get('unidad')
        estado_anterior = datos.get('estado_anterior', '')
        estado_nuevo = datos.get('estado_nuevo', '')
        cantidad = datos.get('cantidad')
        motivo = datos.get('motivo', '')
        subtipo = datos.get('subtipo', '')
        numero_unidad_nueva = datos.get('numero_unidad_nueva', '').strip()

        # Los cambios de ubicación y las altas no se mandan a mano: los registra el
        # sistema al editar o crear el recurso (J16).
        if tipo not in [Movimiento.CAMBIO_ESTADO, Movimiento.ENTRADA, Movimiento.SALIDA]:
            raise serializers.ValidationError(
                {'tipo': 'Aquí solo se registran cambios de estado, entradas y salidas. '
                         'El cambio de ubicación se hace editando el recurso.'}
            )

        # La unidad elegida tiene que ser de ESE recurso.
        if unidad is not None and unidad.recurso_id != recurso.id:
            raise serializers.ValidationError({'unidad': f'La unidad {unidad.numero} no es de {recurso.nombre}.'})

        if tipo == Movimiento.CAMBIO_ESTADO:
            error = movimientos.validar_cambio_estado(recurso, unidad, estado_anterior, estado_nuevo, cantidad, motivo)
        elif tipo == Movimiento.ENTRADA:
            error = movimientos.validar_entrada(recurso, subtipo, cantidad, datos.get('fecha_movimiento'),
                                                numero_unidad_nueva)
        else:
            error = movimientos.validar_salida(recurso, unidad, subtipo, estado_anterior, cantidad, motivo)

        if error != '':
            raise serializers.ValidationError(error)

        # Completa los datos que se deducen solos, para que el historial quede completo.
        if tipo == Movimiento.ENTRADA:
            datos['estado_anterior'] = ''
            datos['estado_nuevo'] = DISPONIBLE
            datos['unidad'] = None
            if numero_unidad_nueva != '':
                datos['cantidad'] = 1
        else:
            if tipo == Movimiento.SALIDA:
                datos['estado_nuevo'] = movimientos.estado_nuevo_de_salida(subtipo)
            else:
                datos['subtipo'] = ''  # un cambio de estado no tiene subtipo
            if unidad is not None:
                # Con n° de serie se mueve 1 unidad, desde el estado que tiene ahora.
                datos['estado_anterior'] = unidad.estado
                datos['cantidad'] = 1

        datos['numero_unidad_nueva'] = numero_unidad_nueva
        return datos

    def create(self, datos):
        """Aplica el cambio en el inventario y guarda el registro del historial.

        transaction.atomic(): si algo falla a la mitad, no se guarda NADA
        (ni el cambio del recurso ni el registro). Todo o nada.
        """
        numero_unidad_nueva = datos.pop('numero_unidad_nueva', '')
        with transaction.atomic():
            movimiento = Movimiento(**datos)
            movimientos.aplicar_movimiento(movimiento, numero_unidad_nueva)
            movimiento.save()
        return movimiento
