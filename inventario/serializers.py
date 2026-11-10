"""
Serializers de la app inventario.

Un serializer convierte un objeto de Django (una fila de la base) en JSON para
la API, y al revés: valida el JSON que llega en un POST/PUT/PATCH antes de guardarlo.
ModelSerializer arma los campos solo, leyendo el modelo.

- Categoria, Torre y Sala: página "Configuración" (RF-08, RF-10, RNF-05).
- Recurso y Unidad: inventario y ficha del recurso (HU-01, HU-11, HU-12, HU-13).
"""
from rest_framework import serializers

from .models import Categoria, Recurso, Sala, Torre, Unidad


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

    def get_cantidades(self, recurso):
        """Cuántas unidades hay en cada estado (ver Recurso.obtener_cantidades)."""
        return recurso.obtener_cantidades()

    def get_cantidad_total(self, recurso):
        """La suma de todos los estados: lo que muestra la tarjeta del inventario."""
        return recurso.obtener_cantidad_total()
