"""
Reglas de los movimientos del inventario: cambio de estado, entrada y salida.
Cubre: HU-02 (cambiar estado), HU-14 y RF-13 (entradas y salidas), HU-06 (historial).

Son las mismas reglas del front (src/utils/cambioEstado.ts y src/utils/movimientos.ts):
- Las funciones validar_* devuelven un mensaje de error, o '' si todo está bien.
- aplicar_movimiento() hace el cambio en el recurso o en la unidad.

Dos formas de mover unidades:
- Equipos e instrumentos (categoría con n° de serie): se indica UNA unidad por movimiento.
- Insumos, reactivos, etc.: se indica el estado de origen y una cantidad.
"""
from django.utils import timezone

from .models import DADO_DE_BAJA, DISPONIBLE, ESTADOS, Movimiento, Unidad


def texto_estado(estado):
    """ 'danado' → 'Dañado'. Busca el texto en la lista ESTADOS del modelo. """
    for valor, texto in ESTADOS:
        if valor == estado:
            return texto
    return estado


def usa_unidades(recurso):
    """True si el recurso se maneja por unidades con número de serie (equipos e instrumentos, HU-12)."""
    return recurso.categoria.usa_numero_serie


def estado_nuevo_de_salida(subtipo):
    """Daño reparable → la unidad va a mantención. Daño irreparable → se da de baja (HU-02, HU-14)."""
    if subtipo == Movimiento.DANO_IRREPARABLE:
        return DADO_DE_BAJA
    return 'en_mantencion'


def validar_cantidad_en_origen(recurso, estado_anterior, cantidad):
    """Revisa que haya suficientes unidades en el estado de origen (para recursos sin n° de serie)."""
    if estado_anterior == '':
        return 'Elige el estado de origen de las unidades.'
    if cantidad is None or cantidad < 1:
        return 'La cantidad debe ser un número entero mayor que 0.'

    # No se pueden mover más unidades de las que hay. Ej: si hay 1 dañado, no se pueden pasar 3.
    hay = recurso.obtener_cantidades()[estado_anterior]
    if cantidad > hay:
        return f'Solo hay {hay} unidad(es) en estado "{texto_estado(estado_anterior)}".'
    return ''


def validar_cambio_estado(recurso, unidad, estado_anterior, estado_nuevo, cantidad, motivo):
    """Cambio de estado (HU-02): unidades que pasan de un estado a otro. El total no cambia."""
    if estado_nuevo == '':
        return 'Elige el estado nuevo.'

    # Lo dado de baja salió del inventario para siempre: no vuelve a otro estado.
    if usa_unidades(recurso):
        if unidad is None:
            return 'Elige la unidad (n° de serie) que cambia de estado.'
        if unidad.estado == DADO_DE_BAJA:
            return f'La unidad {unidad.numero} está dada de baja: ya no puede cambiar de estado.'
        if unidad.estado == estado_nuevo:
            return f'La unidad {unidad.numero} ya está en estado "{texto_estado(estado_nuevo)}".'
    else:
        if estado_anterior == DADO_DE_BAJA:
            return 'Las unidades dadas de baja ya no pueden cambiar de estado.'
        if estado_anterior == estado_nuevo:
            return 'El estado nuevo debe ser distinto al estado actual.'
        error = validar_cantidad_en_origen(recurso, estado_anterior, cantidad)
        if error != '':
            return error

    if motivo.strip() == '':
        return 'Escribe el motivo del cambio (ej: "Punta rota").'
    return ''


def validar_entrada(recurso, subtipo, cantidad, fecha_movimiento, numero_unidad_nueva):
    """Entrada (HU-14, CA-14.1): llegan unidades nuevas a "disponible"."""
    if subtipo not in [Movimiento.ADQUISICION, Movimiento.PRESTAMO, Movimiento.REPOSICION]:
        return 'Elige el tipo de entrada: adquisición, préstamo o reposición.'

    if fecha_movimiento is None:
        return 'Elige la fecha de la entrada.'
    if fecha_movimiento > timezone.localdate():
        return 'La fecha de la entrada no puede ser futura.'

    if usa_unidades(recurso):
        # Cada unidad nueva lleva su número, distinto de los que el recurso ya tiene (CA-12.2).
        if numero_unidad_nueva == '':
            return 'Escribe el número de serie de la unidad que entra.'
        if recurso.unidades.filter(numero=numero_unidad_nueva).exists():
            return f'El número "{numero_unidad_nueva}" ya está registrado en {recurso.nombre}.'
    else:
        if cantidad is None or cantidad < 1:
            return 'La cantidad debe ser un número entero mayor que 0.'
    return ''


def validar_salida(recurso, unidad, subtipo, estado_anterior, cantidad, motivo):
    """Salida (HU-14, CA-14.2): unidades que salen por daño reparable (a mantención) o irreparable (de baja)."""
    if subtipo not in [Movimiento.DANO_REPARABLE, Movimiento.DANO_IRREPARABLE]:
        return 'Elige el tipo de salida: daño reparable o daño irreparable.'

    estado_nuevo = estado_nuevo_de_salida(subtipo)

    if usa_unidades(recurso):
        if unidad is None:
            return 'Elige la unidad (n° de serie) que sale.'
        if unidad.estado == DADO_DE_BAJA:
            return f'La unidad {unidad.numero} ya está dada de baja.'
        if unidad.estado == estado_nuevo:
            return f'La unidad {unidad.numero} ya está en estado "{texto_estado(estado_nuevo)}".'
    else:
        if estado_anterior == estado_nuevo or estado_anterior == DADO_DE_BAJA:
            return (f'Elige un estado de origen distinto de "{texto_estado(estado_nuevo)}" '
                    'y de "Dado de baja".')
        error = validar_cantidad_en_origen(recurso, estado_anterior, cantidad)
        if error != '':
            return error

    if motivo.strip() == '':
        return 'Escribe el motivo de la salida (ej: "Se cayó al piso").'
    return ''


def aplicar_movimiento(movimiento, numero_unidad_nueva=''):
    """Hace el cambio en el inventario. Se llama con el movimiento YA validado, antes de guardarlo.

    - Entrada con n° de serie: crea la unidad nueva en "disponible".
    - Entrada sin n° de serie: suma la cantidad a "disponible".
    - Cambio de estado o salida de una unidad: le cambia el estado a esa unidad.
    - Cambio de estado o salida sin unidades: resta del estado de origen y suma al nuevo.
    También llena valor_anterior y valor_nuevo, que muestra la tabla del historial.
    """
    recurso = movimiento.recurso

    if movimiento.tipo == Movimiento.ENTRADA and numero_unidad_nueva != '':
        unidad = Unidad.objects.create(recurso=recurso, numero=numero_unidad_nueva, estado=DISPONIBLE)
        movimiento.unidad = unidad

    elif movimiento.tipo == Movimiento.ENTRADA:
        recurso.cantidad_disponible = recurso.cantidad_disponible + movimiento.cantidad
        recurso.save()

    elif movimiento.unidad is not None:
        movimiento.unidad.estado = movimiento.estado_nuevo
        movimiento.unidad.save()

    else:
        # Los campos se llaman cantidad_<estado>: getattr/setattr leen y escriben
        # un campo cuyo nombre está guardado en un texto. Ej: 'cantidad_danado'.
        campo_origen = 'cantidad_' + movimiento.estado_anterior
        campo_destino = 'cantidad_' + movimiento.estado_nuevo
        setattr(recurso, campo_origen, getattr(recurso, campo_origen) - movimiento.cantidad)
        setattr(recurso, campo_destino, getattr(recurso, campo_destino) + movimiento.cantidad)
        recurso.save()

    # Texto para la tabla del historial: "Disponible" → "Dañado".
    if movimiento.estado_anterior != '':
        movimiento.valor_anterior = texto_estado(movimiento.estado_anterior)
    movimiento.valor_nuevo = texto_estado(movimiento.estado_nuevo)
