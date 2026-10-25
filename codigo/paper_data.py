"""
paper_data.py
================================================================================
Valores publicados por Pappis & Mamdani (1977), transcritos de la IMAGEN del
paper original (no del texto OCR). Se usan solo para comparar.
"""

# Tabla I: (N-S, E-W) -> (retardo del modelo, retardo de la formula) en s/veh
TABLE_I = {
    (360, 360): (7.2, 7.4), (360, 720): (7.4, 7.9), (360, 1080): (7.9, 8.4),
    (360, 1440): (8.4, 9.0), (360, 1800): (9.3, 10.2), (360, 2160): (12.3, 12.9),
    (360, 2520): (15.8, 18.9), (720, 720): (9.7, 10.0), (720, 1080): (10.8, 11.6),
    (720, 1440): (12.7, 13.8), (720, 1800): (15.9, 17.3), (720, 2160): (21.8, 24.9),
    (1080, 1080): (13.6, 14.9), (1080, 1440): (17.9, 19.7), (1080, 1800): (25.8, 29.2),
    (1440, 1440): (27.3, 30.7),
}

# Tabla VIII: (N-S, E-W) -> (vehiculo-actuado, difuso) en s/veh
TABLE_VIII = {
    (360, 360): (7.2, 5.7), (360, 720): (7.4, 6.1), (360, 1080): (7.9, 6.6),
    (360, 1440): (8.4, 7.3), (360, 1800): (9.3, 8.4), (360, 2160): (12.3, 10.0),
    (360, 2520): (15.8, 13.6), (720, 720): (9.7, 7.4), (720, 1080): (10.8, 8.8),
    (720, 1440): (12.7, 10.9), (720, 1800): (15.9, 14.1), (720, 2160): (21.8, 18.5),
    (1080, 1080): (13.6, 12.0), (1080, 1440): (17.9, 15.4), (1080, 1800): (25.8, 21.6),
    (1440, 1440): (27.3, 22.9),
}

# Tabla V (mt) y Tabla VI (lt), tal como aparecen impresas
TABLE_V = {   # arribos 1..10
    "none":    [.5, .8, .9, 1, 1, 1, 1, 1, 1, 1],
    "afew":    [0, .5, .8, .9, 1, 1, 1, 1, 1, 1],
    "few":     [0, 0, .5, .8, .9, 1, 1, 1, 1, 1],
    "medium":  [0, 0, 0, .5, .8, .9, 1, 1, 1, 1],
    "many":    [0, 0, 0, 0, .5, .8, .9, 1, 1, 1],
    "toomany": [0, 0, 0, 0, 0, .5, .8, .9, 1, 1],
}
# Tabla VI: lt(X)(q) para q = 4..32 -> '1' hasta el escalon, luego .5 .3 .1 y ceros
def _lt_row(n_ones):
    return [1.0] * n_ones + [.5, .3, .1] + [0.0] * (29 - n_ones - 3)

TABLE_VI = {
    "verysmall": _lt_row(1),    # 1 .5 .3 .1 0 ...
    "small":     _lt_row(5),
    "smallplus": _lt_row(9),
    "medium":    _lt_row(13),
    "long":      _lt_row(17),
    "verylong":  _lt_row(21),
}

# Tabla VII (ejemplo de la pag. 7): x, x', Q y la fila final "Fuzzy Algorithm"
EXAMPLE_X = [0, 1, 0, 1, 1, 1, 1, 0, 0, 1]
EXAMPLE_XP = [0, 1, 0, 0, 1, 0, 0, 1, 0, 0]
EXAMPLE_Q = 5
EXAMPLE_BETA = [0, 1, 1, 2, 3, 4, 5, 5, 5, 6]
EXAMPLE_BETA_P = [5, 6, 6, 6, 7, 7, 7, 8, 8, 8]
EXAMPLE_ROW_VII = {   # por regla (2.a intervencion) y fila agregada
    "R1": [0, .5, 0, 0, 0, 0, 0, 0, 0, 0],
    "R2": [0, 0, 0, .3, 0, 0, 0, 0, 0, 0],
    "R3": [0, 0, 0, 0, .1, .1, 0, 0, 0, 0],
    "R4": [0, 0, 0, 0, 0, .1, .1, 0, 0, 0],
    "R5": [0, 0, 0, 0, 0, 0, 0, .5, .5, .8],
    "algoritmo": [0, .5, 0, .3, .1, .1, .1, .5, .5, .8],
}


# Tablas II, III y IV (conjuntos base), tal como se imprimen
TABLE_II = {   # tiempo / extension, t = 1..10 s
    "veryshort": [1, .5, 0, 0, 0, 0, 0, 0, 0, 0],
    "short":     [0, .5, 1, .5, 0, 0, 0, 0, 0, 0],
    "medium":    [0, 0, 0, .5, 1, .5, 0, 0, 0, 0],
    "long":      [0, 0, 0, 0, 0, .5, 1, .5, 0, 0],
    "verylong":  [0, 0, 0, 0, 0, 0, 0, .5, 1, 1],
}
TABLE_III = {  # arribos, a = 1..10
    "none":    [.5, .2, .1, 0, 0, 0, 0, 0, 0, 0],
    "afew":    [1, .5, .2, .1, 0, 0, 0, 0, 0, 0],
    "few":     [.5, 1, .5, .2, .1, 0, 0, 0, 0, 0],
    "medium":  [.2, .5, 1, .5, .2, .1, 0, 0, 0, 0],
    "many":    [.1, .2, .5, 1, .5, .2, .1, 0, 0, 0],
    "toomany": [0, .1, .2, .5, 1, .5, .2, .1, 0, 0],
}

def _bump(n_zeros):
    """Fila de la Tabla IV (q = 4..32): n ceros, '.5 .7 .9 1 .9 .7 .5', ceros."""
    return [0.0] * n_zeros + [.5, .7, .9, 1.0, .9, .7, .5] + [0.0] * (29 - n_zeros - 7)

TABLE_IV = {   # colas, q = 4..32 ('verysmall' arranca con 0 y .5 en q=4 y q=5)
    "verysmall": [0, .5, .7, .9, 1.0, .9, .7, .5] + [0.0] * 21,
    "small": _bump(5), "smallplus": _bump(9), "medium": _bump(13),
    "long": _bump(17), "verylong": _bump(21),
}
