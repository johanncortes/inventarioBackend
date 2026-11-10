"""
Serializers de la app inventario.

Un serializer convierte un objeto de Django (una fila de la base) en JSON para
la API, y al revés: valida el JSON que llega en un POST/PUT/PATCH antes de guardarlo.
ModelSerializer arma los campos solo, leyendo el modelo.

Aquí: Categoria, Torre y Sala (página "Configuración", RF-08, RF-10, RNF-05).
Recurso y Unidad se agregan en J10.
"""
from rest_framework import serializers

from .models import Categoria, Sala, Torre


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
