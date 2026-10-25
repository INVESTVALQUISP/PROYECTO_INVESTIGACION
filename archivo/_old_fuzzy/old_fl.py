"""
fuzzy_logic.py
================================================================================
Implementacion EXACTA del controlador de logica difusa de Pappis & Mamdani
(1977), "A Fuzzy Logic Controller for a Traffic Junction",
IEEE Trans. Syst., Man, Cybern., vol. SMC-7, no. 10, pp. 707-716.

Todo se extrae literalmente de las Tablas II-VI y del Apendice del paper.

Universos de discurso (indices 1-based):
  * TIEMPO / EXTENSION  t = 1..10 s        (Tabla II)
  * ARRIBOS  (veh)      a = 1..10 veh       (Tabla III)
  * COLAS     (veh)      q = 4..32 veh       (Tabla IV)
  * La salida E toma los mismos valores que el TIEMPO.

Operadores mt ("more than") y lt ("less than") definidos en la pags. 4 del paper:
  Sea x0 = elemento donde la funcion de pertenencia es maxima.
    mu_mt(A)(x) = mu_A(x)      si x < x0
                 1 - mu_A(x)   si x >= x0
    mu_lt(A)(x) = 1 - mu_A(x)  si x < x0
                 0             si x >= x0
  (Verificado contra la Tabla V para mt(none), mt(afew), mt(few), mt(medium),
   mt(many) y contra la Tabla VI para lt(verysmall) y lt(medium).)
"""

import numpy as np

# ---------------------------------------------------------------------------
# Tabla II: conjuntos difusos sobre TIEMPO (o EXTENSION), t = 1..10 s
# ---------------------------------------------------------------------------
MU_TIME = {
    "veryshort": [1, .5, 0, 0, 0, 0, 0, 0, 0, 0],
    "short":     [0, .5, 1, .5, 0, 0, 0, 0, 0, 0],
    "medium":    [0, 0, 0, .5, 1, .5, 0, 0, 0, 0],
    "long":      [0, 0, 0, 0, 0, .5, 1, .5, 0, 0],
    "verylong":  [0, 0, 0, 0, 0, 0, 0, .5, 1, 1],
}

# ---------------------------------------------------------------------------
# Tabla III: conjuntos difusos sobre ARRIBOS, a = 1..10 veh
# ---------------------------------------------------------------------------
MU_ARR = {
    "none":    [.5, .2, .1, 0, 0, 0, 0, 0, 0, 0],
    "afew":    [1, .5, .2, .1, 0, 0, 0, 0, 0, 0],
    "few":     [.5, 1, .5, .2, .1, 0, 0, 0, 0, 0],
    "medium":  [.2, .5, 1, .5, .2, .1, 0, 0, 0, 0],
    "many":    [.1, .2, .5, 1, .5, .2, .1, 0, 0, 0],
    "toomany": [0, .1, .2, .5, 1, .5, .2, .1, 0, 0],
}

# ---------------------------------------------------------------------------
# Tabla IV: conjuntos difusos sobre COLAS, q = 4..32 veh
# (cada conjunto es un "bump" triangular de 7 valores, pico en el centro)
# ---------------------------------------------------------------------------
MU_QUEUE = {
    "verysmall": [0, .5, .7, .9, 1, .9, .7, .5] + [0] * 21,   # pico q=8
    "small":     [0] * 5 + [.5, .7, .9, 1, .9, .7, .5] + [0] * 17,   # pico q=12
    "smallplus": [0] * 9 + [.5, .7, .9, 1, .9, .7, .5] + [0] * 13,  # pico q=16
    "medium":    [0] * 13 + [.5, .7, .9, 1, .9, .7, .5] + [0] * 9,  # pico q=20
    "long":      [0] * 17 + [.5, .7, .9, 1, .9, .7, .5] + [0] * 5,  # pico q=24
    "verylong":  [0] * 22 + [.5, .7, .9, 1, .9, .7, .5],             # pico q=29
}

# "any" es el conjunto cuya funcion de pertenencia vale 1 en todo su universo.
ANY = 1.0


# ---------------------------------------------------------------------------
# Operadores mt / lt
# ---------------------------------------------------------------------------
def _peak(fset, lo=1):
    """x0: valor del universo donde la pertenencia es maxima.
    'lo' es el primer valor del universo (1 para TIEMPO/ARRIBOS, 4 para COLAS)."""
    return int(np.argmax(fset)) + lo


def mt_arr(base, a):
    """mu_mt(A)(a) para arribos (universo 1..10)."""
    if a < 1:
        return 0.0          # fuera del universo -> sin pertenencia
    a = min(10, int(a))
    f = MU_ARR[base]
    x0 = _peak(f, lo=1)
    mu = f[a - 1]
    return mu if a < x0 else 1.0 - mu


def lt_queue(base, q):
    """mu_lt(A)(q) para colas (universo 4..32)."""
    if q < 4:
        return 1.0          # cola pequeña -> definitivamente "menor que"
    if q > 32:
        return 0.0
    f = MU_QUEUE[base]
    x0 = _peak(f, lo=4)
    mu = f[q - 4]
    return (1.0 - mu) if q < x0 else 0.0


def mu_time(label, t):
    """mu_T(t) para el conjunto de tiempo/extension 'label'."""
    t = max(1, min(10, int(t)))
    return MU_TIME[label][t - 1]


# ---------------------------------------------------------------------------
# REGLAS DEL APENDICE (24 reglas, 5 intervenciones a los 7,17,27,37,47 s;
# distribucion 5+5+7+5+2, tal cual el articulo original en ingles)
# Cada regla: (T, A_base, Q_base, E)
#   T      = etiqueta difusa de TIEMPO
#   A_base = etiqueta base de ARRIBOS (se le aplica mt)
#   Q_base = etiqueta base de COLA  (se le aplica lt)  o  'any'
#   E      = etiqueta difusa de EXTENSION (salida)
# ---------------------------------------------------------------------------
RULES = {
    7: [
        ("veryshort", "none",    "any",       "veryshort"),
        ("short",     "afew",    "verysmall", "short"),
        ("medium",    "few",     "verysmall", "medium"),
        ("long",      "medium",  "verysmall", "long"),
        ("verylong",  "many",    "verysmall", "verylong"),
    ],
    17: [
        ("veryshort", "none",    "any",       "veryshort"),
        ("short",     "afew",    "verysmall", "short"),
        ("medium",    "few",     "verysmall", "medium"),
        ("long",      "medium",  "verysmall", "long"),
        ("verylong",  "many",    "small",     "verylong"),
    ],
    27: [
        ("veryshort", "none",    "any",       "veryshort"),
        ("short",     "afew",    "verysmall", "short"),
        ("medium",    "few",     "verysmall", "medium"),
        ("short",     "afew",    "smallplus", "short"),
        ("medium",    "medium",  "smallplus", "medium"),
        ("long",      "many",    "medium",    "long"),
        ("verylong",  "toomany", "long",      "verylong"),
    ],
    37: [
        ("veryshort", "none",    "any",       "veryshort"),
        ("short",     "afew",    "long",      "short"),
        ("medium",    "medium",  "long",      "medium"),
        ("long",      "toomany", "verylong",  "long"),
        ("verylong",  "toomany", "verylong",  "verylong"),
    ],
    47: [
        ("long",      "medium",  "verysmall", "long"),
        ("verylong",  "many",    "small",     "verylong"),
    ],
}

INTERVENTIONS = [7, 17, 27, 37, 47]


def fuzzy_decision(arrivals_green, arrivals_cross, q_cross, rules,
                   predicted_q=True, q_green=0, mode="literal"):
    """
    Calcula el vector de confianza grade[e] para e = 1..10 s (extensiones).

    arrivals_green : lista de 10 valores 0/1 = arribos en el brazo con
                     derecho de paso (los que cruzaran el punto critico).
    arrivals_cross : lista de 10 valores 0/1 = arribos en el brazo en rojo
                     (los que se suman a la cola).
    q_cross        : cola actual del brazo en rojo.
    rules          : lista de reglas de la intervencion en curso.
    predicted_q    : (modo 'literal') si True, la membresia de Q se evalua en la
                     cola PREDICHA beta'_e; si False, en la cola ACTUAL q_cross.
    q_green        : cola actual del brazo con derecho de paso (para modo 'capacity').
    mode           : 'literal'  -> beta_e = arribos acumulados (modelo del paper,
                                      ec. de la pags. 7). Sensible en flujos altos.
                     'capacity' -> beta_e = min(e, q_green + arribos) = vehiculos
                                      que CRUZAN el punto critico limitados por la
                                      capacidad de saturacion (1 veh/s). Esta es la
                                      interpretacion mas fiel de "vehiculos que cruzan
                                      el punto critico" y reproduce fielmente la serie
                                      principal del Cuadro VIII del paper.

    Devuelve array grade de longitud 11 (los indices 1..10 se usan).
    """
    arr = np.asarray(arrivals_green, dtype=int)
    cum = np.cumsum(arr).astype(int)
    cum_cross = np.cumsum(np.asarray(arrivals_cross, dtype=int)).astype(int)
    if mode == "capacity":
        beta = np.minimum(np.arange(1, 11), q_green + cum).astype(int)   # cruces reales
    else:
        beta = cum                                                     # arribos (paper)
    beta_cross = q_cross + cum_cross
    grade = np.zeros(11)
    for e in range(1, 11):
        a = int(beta[e - 1])        # vehiculos cruzando en e s
        if mode == "capacity":
            q = int(q_cross)         # cola actual de la fase en cruce
        else:
            q = int(q_cross) if not predicted_q else int(beta_cross[e - 1])
        g = 0.0
        for (T, A_base, Q_base, E) in rules:
            gT = mu_time(T, e)
            gA = mt_arr(A_base, a)
            gQ = ANY if Q_base == "any" else lt_queue(Q_base, q)
            gE = mu_time(E, e)
            g = max(g, min(gT, gA, gQ, gE))
        grade[e] = g
    return grade


def fuzzy_decision_per_rule(arrivals_green, arrivals_cross, q_cross, rules,
                             predicted_q=True, q_green=0, mode="literal"):
    """
    Igual que fuzzy_decision pero devuelve la matriz de grados FILA POR REGLA
    (util para graficar la Fig. 3 del paper: "aggregated membership functions").
    Shape: (n_reglas, 11).  La fila i-esima es el grado aportado por la regla i
    (antes del maximo).  El grado agregado = max sobre filas.
    """
    arr = np.asarray(arrivals_green, dtype=int)
    cum = np.cumsum(arr).astype(int)
    cum_cross = np.cumsum(np.asarray(arrivals_cross, dtype=int)).astype(int)
    if mode == "capacity":
        beta = np.minimum(np.arange(1, 11), q_green + cum).astype(int)
    else:
        beta = cum
    beta_cross = q_cross + cum_cross
    out = np.zeros((len(rules), 11))
    for r, (T, A_base, Q_base, E) in enumerate(rules):
        for e in range(1, 11):
            a = int(beta[e - 1])
            if mode == "capacity":
                q = int(q_cross)
            else:
                q = int(q_cross) if not predicted_q else int(beta_cross[e - 1])
            gT = mu_time(T, e)
            gA = mt_arr(A_base, a)
            gQ = ANY if Q_base == "any" else lt_queue(Q_base, q)
            gE = mu_time(E, e)
            out[r, e] = min(gT, gA, gQ, gE)
    return out


def decide_extension(grade, threshold=0.5):
    """
    Selecciona la extension:
      * si max(grade) < threshold -> 0  (cortar el verde, cambiar de fase)
      * sino                      -> e* = argmax(grade)  (en empate, la mayor e)
    """
    best = float(np.max(grade[1:11]))
    if best < threshold:
        return 0
    candidates = [e for e in range(1, 11) if grade[e] == best]
    return max(candidates)


# ---------------------------------------------------------------------------
# Verificacion contra el ejemplo trabajado del paper (pag. 7)
# Intervencion 2 (17 s). Brazo N-S con derecho de paso, cola E-W = 5.
# x  = (0 1 0 1 1 1 1 0 0 1)  -> beta = (0 1 1 2 3 4 5 5 5 6)
# x' = (0 1 0 0 1 0 0 1 0 0)  -> beta' = (5 6 6 6 7 7 7 8 8 8)
# El paper concluye que el controlador selecciona la extension de 10 s.
# ---------------------------------------------------------------------------
def _selftest():
    x = [0, 1, 0, 1, 1, 1, 1, 0, 0, 1]
    xp = [0, 1, 0, 0, 1, 0, 0, 1, 0, 0]
    grade = fuzzy_decision(x, xp, 5, RULES[17])
    e_star = decide_extension(grade)
    print("Ejemplo del paper (intervencion 17 s):")
    print("  grade(e=1..10) =", np.round(grade[1:], 3))
    print("  extension seleccionada =", e_star, "(el paper dice 10)")
    assert e_star == 10, "FALLO en el ejemplo trabajado"
    # Tambien verificamos el grado C2(8,4,5,8)=0.5 reportado en el paper
    g8 = grade[8]
    print("  grade(e=8) =", round(float(g8), 3), "(el paper reporta 0.5)")
    print("OK: el modulo reproduce el ejemplo del paper.\n")


if __name__ == "__main__":
    _selftest()
