"""
Arma el código de ubicación de un recurso (HU-11, RF-10).

Es la misma regla del front (src/utils/ubicacion.ts):
    sala + bodega + mueble  →  "B307" + "Bodega 1" + "Mueble 2"  →  "B307-B1-M2"
Caso especial: recursos que están en la sala misma (mesas, campanas),
con bodega "Sala" y mueble "Sin mueble"  →  "B308-SALA"
"""


def abreviar_bodega(bodega):
    """ "Bodega 1" → "B1". Cualquier otro nombre ("Sala") va en mayúsculas: "SALA". """
    bodega = bodega.strip()
    if bodega.startswith('Bodega '):
        return 'B' + bodega.replace('Bodega ', '')
    return bodega.upper()


def abreviar_mueble(mueble):
    """ "Mueble 2" → "M2". "Sin mueble" (o cualquier otro texto) no aporta nada: devuelve ''. """
    mueble = mueble.strip()
    if mueble.startswith('Mueble '):
        return 'M' + mueble.replace('Mueble ', '')
    return ''


def generar_codigo_ubicacion(codigo_sala, bodega, mueble):
    """Junta el código de la sala con la bodega y el mueble abreviados: "B307-B1-M2"."""
    codigo = codigo_sala + '-' + abreviar_bodega(bodega)

    abreviatura_mueble = abreviar_mueble(mueble)
    if abreviatura_mueble != '':
        codigo = codigo + '-' + abreviatura_mueble

    return codigo
