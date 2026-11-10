"""
Modelos de la app inventario.

- Categoria, Torre y Sala: la "Configuración" del sistema (RF-08, RF-10, RNF-05).
- Recurso y Unidad: el inventario (RF-01, RF-02, HU-11, HU-12, HU-13).
- Movimiento: el historial de cada recurso (HU-06, RF-13, RNF-06).

Relaciones: Torre ──< Sala ──< Recurso >── Categoria
                                  ├──< Unidad
                                  └──< Movimiento >── User

Los campos son los mismos del front (src/types/*.ts), pero en
snake_case: usaStockMinimo → usa_stock_minimo.
"""
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from .ubicacion import generar_codigo_ubicacion

# Los 5 estados operativos de un recurso o de una unidad (RF-01).
# Son los mismos valores del front (src/types/Recurso.ts). Los usan Recurso,
# Unidad y, más adelante, Movimiento e Incidencia.
DISPONIBLE = 'disponible'
EN_USO = 'en_uso'
DANADO = 'danado'
EN_MANTENCION = 'en_mantencion'
DADO_DE_BAJA = 'dado_de_baja'
ESTADOS = [
    (DISPONIBLE, 'Disponible'),
    (EN_USO, 'En uso'),
    (DANADO, 'Dañado'),
    (EN_MANTENCION, 'En mantención'),
    (DADO_DE_BAJA, 'Dado de baja'),
]


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
        """Arma el código ("B" + "307" = "B307") y actualiza el código de ubicación de sus recursos."""
        self.codigo = f'{self.torre.letra}{self.numero}'
        super().save(*args, **kwargs)

        # Si la sala cambió de código, "B307-B1-M2" de sus recursos también tiene que cambiar.
        for recurso in self.recursos.all():
            recurso.save()


class Recurso(models.Model):
    """Un recurso del laboratorio: instrumento, equipo, insumo, reactivo, mobiliario o instalación.

    Los primeros campos son los de la planilla Excel actual (descriptor, n° de serie,
    marca, proveedor, observación), igual que en el front.
    """

    nombre = models.CharField(max_length=150)  # en la planilla se llama "descriptor"

    # PROTECT: no se puede borrar una categoría o una sala que todavía tiene recursos.
    # related_name='recursos' permite escribir categoria.recursos.all() o sala.recursos.all().
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='recursos')

    # Ubicación (HU-11): la sala ya incluye la torre (sala.torre).
    sala = models.ForeignKey(Sala, on_delete=models.PROTECT, related_name='recursos')
    bodega = models.CharField(max_length=50)  # "Bodega 1" o "Sala"
    mueble = models.CharField(max_length=50)  # "Mueble 2" o "Sin mueble"
    # "B307-B1-M2": lo arma save() con inventario/ubicacion.py, no se escribe a mano.
    codigo_ubicacion = models.CharField(max_length=40, editable=False)

    # Cuántas unidades hay en cada estado (RF-01, RF-02). Se usan en los recursos
    # SIN número de serie (insumos, reactivos, mobiliario). En equipos e instrumentos
    # las cantidades se cuentan desde sus Unidades (igual que en el front).
    # PositiveIntegerField no acepta números negativos.
    cantidad_disponible = models.PositiveIntegerField(default=0)
    cantidad_en_uso = models.PositiveIntegerField(default=0)
    cantidad_danado = models.PositiveIntegerField(default=0)
    cantidad_en_mantencion = models.PositiveIntegerField(default=0)
    cantidad_dado_de_baja = models.PositiveIntegerField(default=0)

    # Campos opcionales de la planilla. blank=True: se pueden dejar vacíos.
    numero_serie = models.CharField(max_length=60, blank=True)
    marca = models.CharField(max_length=60, blank=True)
    proveedor = models.CharField(max_length=100, blank=True)
    observacion = models.TextField(blank=True)

    # Solo para insumos y reactivos: si lo disponible baja de este número hay
    # que reponer (HU-09). null=True: los demás recursos lo dejan vacío en la base.
    stock_minimo = models.PositiveIntegerField(null=True, blank=True)

    # Fecha de adquisición (RF-12, HU-13). Es opcional porque hay recursos antiguos sin fecha.
    fecha_adquisicion = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'recurso'
        verbose_name_plural = 'recursos'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.codigo_ubicacion})'

    def save(self, *args, **kwargs):
        """Arma el código de ubicación antes de guardar: "B307" + "Bodega 1" + "Mueble 2" → "B307-B1-M2"."""
        self.codigo_ubicacion = generar_codigo_ubicacion(self.sala.codigo, self.bodega, self.mueble)
        super().save(*args, **kwargs)

    def obtener_cantidades(self):
        """Devuelve cuántas unidades hay en cada estado: {'disponible': 12, 'en_uso': 0, ...}.

        Misma regla del front (utils/unidades.ts): si el recurso tiene unidades con
        número de serie, se cuentan esas unidades; si no, se usan los campos cantidad_*.
        También la usan reservas (unidades disponibles) e incidencias (alertas).
        """
        unidades = list(self.unidades.all())

        if len(unidades) == 0:
            return {
                DISPONIBLE: self.cantidad_disponible,
                EN_USO: self.cantidad_en_uso,
                DANADO: self.cantidad_danado,
                EN_MANTENCION: self.cantidad_en_mantencion,
                DADO_DE_BAJA: self.cantidad_dado_de_baja,
            }

        # Parte todo en 0 y suma 1 al estado de cada unidad.
        cantidades = {DISPONIBLE: 0, EN_USO: 0, DANADO: 0, EN_MANTENCION: 0, DADO_DE_BAJA: 0}
        for unidad in unidades:
            cantidades[unidad.estado] = cantidades[unidad.estado] + 1
        return cantidades

    def obtener_cantidad_total(self):
        """Suma las unidades de todos los estados. Ej: 12 + 0 + 1 + 1 + 0 = 14.

        No se guarda en la base porque podría quedar desactualizada: se calcula cada vez.
        """
        total = 0
        for cantidad in self.obtener_cantidades().values():
            total = total + cantidad
        return total


class Unidad(models.Model):
    """Una unidad de un equipo o instrumento, identificada por su número de serie (HU-12, RF-11).

    Ejemplo: el recurso "Multímetro Fluke 87V" tiene 14 unidades: FLK-0001, FLK-0002...
    Cada una tiene su propio estado, para saber exactamente cuál se dañó.
    """

    # CASCADE: si se borra el recurso, se borran sus unidades (no tienen sentido solas).
    # related_name='unidades' permite escribir recurso.unidades.all(); el serializer
    # de Recurso lo usa para mostrar las unidades dentro del recurso (J10).
    recurso = models.ForeignKey(Recurso, on_delete=models.CASCADE, related_name='unidades')

    numero = models.CharField(max_length=60)  # número de serie o de inventario: "FLK-0001"
    estado = models.CharField(max_length=20, choices=ESTADOS, default=DISPONIBLE)

    class Meta:
        verbose_name = 'unidad'
        verbose_name_plural = 'unidades'
        ordering = ['recurso', 'numero']
        # El número no se puede repetir DENTRO del mismo recurso (CA-12.2).
        # Dos recursos distintos sí pueden tener una unidad "0001".
        unique_together = ['recurso', 'numero']

    def __str__(self):
        return f'{self.recurso.nombre} — {self.numero}'


class Movimiento(models.Model):
    """Un registro del historial de un recurso (HU-06): qué pasó, cuándo, quién y por qué.

    Ejemplo: "El 01/10 a las 11:20, Pedro Soto pasó 1 multímetro de Disponible
    a Dañado porque tenía la punta rota".
    Los registros NO se editan ni se borran (RNF-06): la vista solo permite leer y crear (J16).
    Son los mismos campos del front (src/types/CambioEstado.ts).
    """

    # Tipos de movimiento (CA-06.1)
    CAMBIO_ESTADO = 'cambio_estado'          # unidades pasan de un estado a otro (el total no cambia)
    ENTRADA = 'entrada'                      # llegan unidades nuevas a "disponible"
    SALIDA = 'salida'                        # salen unidades por daño (a mantención o de baja)
    CAMBIO_UBICACION = 'cambio_ubicacion'    # el recurso se movió de sala, bodega o mueble
    ALTA = 'alta'                            # el recurso se agregó al inventario
    TIPOS = [
        (CAMBIO_ESTADO, 'Cambio de estado'),
        (ENTRADA, 'Entrada'),
        (SALIDA, 'Salida'),
        (CAMBIO_UBICACION, 'Cambio de ubicación'),
        (ALTA, 'Alta'),
    ]

    # Por qué entra o sale una unidad (RF-13, CA-14.1 y CA-14.2)
    ADQUISICION = 'adquisicion'
    PRESTAMO = 'prestamo'
    REPOSICION = 'reposicion'
    DANO_REPARABLE = 'dano_reparable'        # la unidad pasa a "en mantención"
    DANO_IRREPARABLE = 'dano_irreparable'    # la unidad pasa a "dado de baja"
    SUBTIPOS = [
        (ADQUISICION, 'Adquisición'),
        (PRESTAMO, 'Préstamo'),
        (REPOSICION, 'Reposición'),
        (DANO_REPARABLE, 'Daño reparable'),
        (DANO_IRREPARABLE, 'Daño irreparable'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPOS)

    # CASCADE: si el encargado elimina un recurso, su historial se va con él
    # (un historial sin recurso no sirve). Mientras el recurso exista, sus
    # movimientos no se pueden editar ni borrar por la API (RNF-06).
    recurso = models.ForeignKey(Recurso, on_delete=models.CASCADE, related_name='movimientos')

    # La unidad afectada, si se indicó (equipos e instrumentos, HU-12).
    # SET_NULL: si se borra la unidad, el movimiento queda, pero sin unidad.
    unidad = models.ForeignKey(
        Unidad, on_delete=models.SET_NULL, null=True, blank=True, related_name='movimientos'
    )

    # Quién lo registró: lo pone la vista con request.user (perform_create, J15).
    # PROTECT: un usuario con historial no se borra (se desactiva, HU-15).
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, related_name='movimientos')

    # auto_now_add: Django pone la fecha y hora al crear el registro, y no se puede cambiar.
    fecha = models.DateTimeField(auto_now_add=True)

    # Desde qué estado y a qué estado pasaron las unidades. Un cambio de
    # ubicación no tiene estados, por eso pueden quedar vacíos (blank=True).
    estado_anterior = models.CharField(max_length=20, choices=ESTADOS, blank=True)
    estado_nuevo = models.CharField(max_length=20, choices=ESTADOS, blank=True)
    cantidad = models.PositiveIntegerField(default=0)  # 0 en un cambio de ubicación

    motivo = models.TextField(blank=True)  # lo escribe el encargado

    # Valor anterior y nuevo como texto, para mostrarlos tal cual en la tabla
    # del historial: un estado ("Disponible") o una ubicación ("B307-B1-M2").
    valor_anterior = models.CharField(max_length=60, blank=True)
    valor_nuevo = models.CharField(max_length=60, blank=True)

    subtipo = models.CharField(max_length=20, choices=SUBTIPOS, blank=True)  # solo en entradas y salidas

    # Día en que ocurrió una entrada (lo escribe el encargado, CA-14.1). Es distinto
    # de "fecha", que es el momento automático en que se registró.
    fecha_movimiento = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'movimiento'
        verbose_name_plural = 'movimientos'
        ordering = ['-fecha']  # el más nuevo primero (CA-06.3)

    def __str__(self):
        # La fecha se guarda en UTC: localtime() la pasa a la hora de Chile para mostrarla.
        fecha_chile = timezone.localtime(self.fecha)
        return f'{self.get_tipo_display()} — {self.recurso.nombre} ({fecha_chile:%d/%m/%Y %H:%M})'
