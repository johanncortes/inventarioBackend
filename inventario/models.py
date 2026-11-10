"""
Modelos de la app inventario.

- Categoria, Torre y Sala: la "Configuración" del sistema (RF-08, RF-10, RNF-05).
- Recurso y Unidad: se agregan en J7. Movimiento (historial): en J14.

Relaciones: Torre ──< Sala ──< Recurso >── Categoria

Los campos son los mismos del front (src/types/Configuracion.ts), pero en
snake_case: usaStockMinimo → usa_stock_minimo.
"""
from django.db import models


class Categoria(models.Model):
    """Tipo de recurso: Instrumento, Insumo, Equipo, Reactivo, Mobiliario, Instalación (RF-08)."""

    # unique=True: no puede haber dos categorías con el mismo nombre.
    # Si se repite, el serializer responde 400 con un mensaje claro.
    nombre = models.CharField(max_length=100, unique=True)

    # Descripción breve y obligatoria (RF-08): máximo 120 caracteres, igual que el front.
    descripcion = models.CharField(max_length=120)

    # True si los recursos se gastan y hay que reponerlos (insumos y reactivos):
    # piden un stock mínimo y generan alertas de reposición (HU-09).
    usa_stock_minimo = models.BooleanField(default=False)

    # True si cada unidad se identifica por número de serie (equipos e instrumentos, HU-12).
    usa_numero_serie = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'
        ordering = ['nombre']  # los listados salen en orden alfabético

    def __str__(self):
        return self.nombre


class Torre(models.Model):
    """Edificio del campus donde están los laboratorios. Se identifica por una letra: B, C."""

    letra = models.CharField(max_length=1, unique=True)

    class Meta:
        verbose_name = 'torre'
        verbose_name_plural = 'torres'
        ordering = ['letra']

    def __str__(self):
        return f'Torre {self.letra}'

    def save(self, *args, **kwargs):
        """Guarda la letra en mayúscula y actualiza el código de sus salas si la letra cambió."""
        self.letra = self.letra.upper()  # "b" → "B"
        super().save(*args, **kwargs)

        # Si la torre cambió de letra (B → D), "B307" tiene que pasar a ser "D307".
        # related_name='salas' (en Sala) permite escribir torre.salas.all().
        for sala in self.salas.all():
            sala.save()


class Sala(models.Model):
    """Sala o laboratorio de una torre. Su código es la letra de la torre + el número: "B307"."""

    # ForeignKey = muchas salas pertenecen a una torre.
    # PROTECT: no se puede borrar una torre que todavía tiene salas
    # (Django lanza ProtectedError en vez de borrar las salas en cascada).
    torre = models.ForeignKey(Torre, on_delete=models.PROTECT, related_name='salas')

    numero = models.CharField(max_length=10)  # "307" (solo dígitos, se valida en el serializer)

    # editable=False: no aparece en los formularios; lo arma save() solo.
    codigo = models.CharField(max_length=12, unique=True, editable=False)

    class Meta:
        verbose_name = 'sala'
        verbose_name_plural = 'salas'
        ordering = ['codigo']
        # No puede haber dos salas con el mismo número en la misma torre.
        # DRF lo revisa solo y responde 400 si se repite.
        unique_together = ['torre', 'numero']

    def __str__(self):
        return self.codigo

    def save(self, *args, **kwargs):
        """Arma el código ("B" + "307" = "B307") antes de guardar."""
        self.codigo = f'{self.torre.letra}{self.numero}'
        super().save(*args, **kwargs)
