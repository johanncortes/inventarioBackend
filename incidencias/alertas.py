"""
Cálculo dinámico de alertas operativas del inventario (Diego, HU-05, HU-09).

¿Por qué se calculan y no se guardan en la base de datos?
Las alertas no son registros históricos estáticos; dependen del estado actual
de cada recurso y sus unidades:
- Si un equipo se daña, nace una alerta de reparación.
- Si se envía al taller o a mantención, la alerta pasa a ser de mantención.
- Cuando vuelve a estar disponible, la alerta desaparece sola (CA-05.3, CA-09.4).
- Si un insumo se repone por encima de su stock mínimo, la alerta de reposición desaparece sola.
De esta manera nunca se duplican ni quedan desfasadas respecto a la realidad del inventario.

Tipos de alertas:
1. 'reparacion': Unidades o recursos en estado 'danado'.
2. 'mantencion': Unidades o recursos en estado 'en_mantencion'.
3. 'reposicion': Recursos (insumos o reactivos con usa_stock_minimo=True o stock_minimo definido)
                 cuya cantidad disponible es menor o igual al stock_minimo establecido.
"""
from inventario.models import DANADO, EN_MANTENCION, Recurso


def calcular_alertas():
    """Recorre todos los recursos y sus unidades y devuelve la lista de alertas activas.

    Cada alerta es un diccionario con:
    - tipo: 'reparacion' | 'mantencion' | 'reposicion'
    - tipo_texto: 'Reparación requerida' | 'En mantención' | 'Reposición necesaria'
    - recurso_id: id del recurso
    - recurso_nombre: nombre del recurso
    - sala_codigo: código de la sala donde está ubicado (ej: 'B307')
    - codigo_ubicacion: ubicación exacta (ej: 'B307-B1-M2')
    - cantidad_afectada: cuántas unidades están en esa condición
    - stock_minimo: stock mínimo configurado (solo en reposición)
    - stock_actual: cantidad disponible actual (solo en reposición)
    - mensaje: descripción clara para el encargado / departamento
    """
    alertas = []

    # select_related para sala y categoria; prefetch_related para unidades
    recursos = Recurso.objects.select_related('categoria', 'sala').prefetch_related('unidades').all()

    for recurso in recursos:
        cantidades = recurso.obtener_cantidades()

        # 1. Alerta de Reparación (recursos o unidades dañadas)
        danadas = cantidades.get(DANADO, 0)
        if danadas > 0:
            alertas.append({
                'tipo': 'reparacion',
                'tipo_texto': 'Reparación requerida',
                'recurso_id': recurso.id,
                'recurso_nombre': recurso.nombre,
                'sala_codigo': recurso.sala.codigo,
                'codigo_ubicacion': recurso.codigo_ubicacion,
                'cantidad_afectada': danadas,
                'stock_minimo': None,
                'stock_actual': cantidades.get('disponible', 0),
                'mensaje': f'{recurso.nombre} tiene {danadas} unidad(es) dañada(s) que requiere(n) reparación.',
            })

        # 2. Alerta de Mantención (recursos o unidades en mantención)
        en_mantencion = cantidades.get(EN_MANTENCION, 0)
        if en_mantencion > 0:
            alertas.append({
                'tipo': 'mantencion',
                'tipo_texto': 'En mantención',
                'recurso_id': recurso.id,
                'recurso_nombre': recurso.nombre,
                'sala_codigo': recurso.sala.codigo,
                'codigo_ubicacion': recurso.codigo_ubicacion,
                'cantidad_afectada': en_mantencion,
                'stock_minimo': None,
                'stock_actual': cantidades.get('disponible', 0),
                'mensaje': f'{recurso.nombre} tiene {en_mantencion} unidad(es) actualmente en mantención.',
            })

        # 3. Alerta de Reposición (insumos o reactivos bajo o igual al stock mínimo)
        if recurso.stock_minimo is not None and recurso.stock_minimo > 0:
            disponible = cantidades.get('disponible', 0)
            if disponible <= recurso.stock_minimo:
                alertas.append({
                    'tipo': 'reposicion',
                    'tipo_texto': 'Reposición necesaria',
                    'recurso_id': recurso.id,
                    'recurso_nombre': recurso.nombre,
                    'sala_codigo': recurso.sala.codigo,
                    'codigo_ubicacion': recurso.codigo_ubicacion,
                    'cantidad_afectada': recurso.stock_minimo - disponible,
                    'stock_minimo': recurso.stock_minimo,
                    'stock_actual': disponible,
                    'mensaje': (
                        f'{recurso.nombre} tiene {disponible} unidades disponibles, '
                        f'por debajo o igual a su stock mínimo ({recurso.stock_minimo}).'
                    ),
                })

    return alertas
