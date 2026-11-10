"""
Lógica de disponibilidad para la app reservas.

Contiene las funciones que calculan si un recurso o sala está disponible
en un horario dado. Se importan desde el serializer (validate()) y desde
la vista de disponibilidad (M13).

Funciones:
  - se_cruzan(): comprueba si dos intervalos de hora se solapan (M7).
  - unidades_disponibles(): cuántas unidades del recurso están libres (M8).
  - sala_esta_ocupada(): si la sala ya la tiene otro docente en ese horario (M9).

¿Por qué aquí y no en la vista? La lógica de negocio va en archivos separados
(disponibilidad.py, movimientos.py...) para que sea más fácil de probar y de
entender (guía del plan, sección 6).
"""
from inventario.models import DISPONIBLE


def se_cruzan(inicio1, fin1, inicio2, fin2):
    """Comprueba si el intervalo [inicio1, fin1) se cruza con [inicio2, fin2).

    Dos horarios se cruzan cuando uno empieza antes de que el otro termine Y
    termina después de que el otro empiece. Es la negación de "uno acaba antes
    de que el otro empiece o viceversa".

    Ejemplos:
      08:30–10:00 y 09:00–11:00 → True  (se solapan)
      08:30–10:00 y 10:00–11:00 → False (toca solo el límite, no se solapan)
      08:30–10:00 y 07:00–08:30 → False
    """
    # Se cruzan si: inicio1 < fin2  Y  fin1 > inicio2.
    return inicio1 < fin2 and fin1 > inicio2


def unidades_disponibles(recurso, fecha, hora_inicio, hora_fin, excluir=None):
    """Calcula cuántas unidades del recurso están libres en el horario indicado.

    Usa Recurso.obtener_cantidades() (definido por Johann en inventario/models.py)
    para saber cuántas unidades hay en estado 'disponible', luego resta las que
    ya están reservadas en ese horario. HU-07, HU-08.

    Args:
        recurso: objeto Recurso.
        fecha: objeto date de la reserva nueva.
        hora_inicio: objeto time del inicio del horario.
        hora_fin: objeto time del fin del horario.
        excluir: objeto Reserva a ignorar (para no chocar consigo misma al editar).

    Returns:
        Número entero de unidades disponibles (puede ser 0 o negativo si hay problema).
    """
    # Usamos obtener_cantidades() de Johann: misma regla que el front.
    # Si tiene unidades con número de serie, las cuenta; si no, usa los campos.
    cantidades = recurso.obtener_cantidades()
    total_disponible = cantidades.get(DISPONIBLE, 0)

    # Buscar las reservas activas (no canceladas) del mismo recurso en la misma fecha.
    # Importamos aquí para evitar importación circular al inicio del módulo.
    from .models import Reserva

    reservas_del_dia = Reserva.objects.filter(
        recurso=recurso,
        fecha=fecha,
        cancelada=False,
    )

    # Excluir la reserva actual cuando se edita (para que no choque consigo misma).
    if excluir is not None:
        reservas_del_dia = reservas_del_dia.exclude(pk=excluir.pk)

    # Sumar las unidades ya reservadas en horarios que se cruzan con el pedido.
    reservadas = 0
    for reserva in reservas_del_dia:
        if se_cruzan(hora_inicio, hora_fin, reserva.hora_inicio, reserva.hora_fin):
            reservadas += reserva.cantidad

    return total_disponible - reservadas


def sala_esta_ocupada(sala, fecha, hora_inicio, hora_fin, docente=None, excluir=None):
    """Comprueba si la sala ya está reservada por OTRO docente en el horario dado.

    El mismo docente sí puede tener varios recursos reservados en su sala (CA-08.3).

    Args:
        sala: objeto Sala.
        fecha: objeto date.
        hora_inicio: objeto time del inicio.
        hora_fin: objeto time del fin.
        docente: User que hace la nueva reserva (se excluyen sus propias reservas).
        excluir: objeto Reserva a ignorar (al editar).

    Returns:
        True si la sala está ocupada por otro docente, False si está libre.
    """
    from .models import Reserva

    reservas_sala = Reserva.objects.filter(
        sala=sala,
        fecha=fecha,
        cancelada=False,
    )

    # Excluir las reservas del mismo docente (CA-08.3: puede reservar varios recursos).
    if docente is not None:
        reservas_sala = reservas_sala.exclude(docente=docente)

    # Excluir la reserva actual al editar.
    if excluir is not None:
        reservas_sala = reservas_sala.exclude(pk=excluir.pk)

    # Comprobar si alguna se cruza con el horario pedido.
    for reserva in reservas_sala:
        if se_cruzan(hora_inicio, hora_fin, reserva.hora_inicio, reserva.hora_fin):
            return True

    return False

