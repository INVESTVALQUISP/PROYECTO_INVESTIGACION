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
    mu_mt(A)(x) = 0           si x < x0
                 1 - mu_A(x)  si x >= x0
    mu_lt(A)(x) = 1 - mu_A(x) si x < x0
                 0            si x >= x0
  (Verificado contra la Tabla III para los 6 mt(...) y contra la Tabla VI
   para lt(verysmall) y lt(medium). Correccion del 08/10/2026: la version
   previa devolvia mu_A(x) para x < x0 en mt, lo cual contradice la Tabla III;
   el comportamiento para x >= x0 no cambio.)
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
    "verylong":  [0] * 21 + [.5, .7, .9, 1, .9, .7, .5, 0.0],        # pico q=28 (Tab. IV paper)
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
    """mu_mt(A)(a) para arribos (universo 1..10).

    Segun la definicion de la pags. 4 y la Tabla III del paper:
      mu_mt(A)(x) = 0          si x < x0
                     1 - mu_A(x) si x >= x0
    (Verificado contra la Tabla III para los seis conjuntos.)
    """
    if a < 1:
        return 0.0          # fuera del universo -> sin pertenencia
    a = min(10, int(a))
    f = MU_ARR[base]
    x0 = _peak(f, lo=1)
    if a < x0:
        return 0.0
    return 1.0 - f[a - 1]


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
# REGLAS DEL APENDICE (25 reglas = 5 intervenciones x 5 reglas, a los 7,17,27,37,47 s)
# Verificadas contra la IMAGEN de las pags. 715-716 del paper original (el texto OCR
# desordena las columnas).
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
        ("long",      "medium",  "verysmall", "long"),
        ("verylong",  "many",    "small",     "verylong"),
    ],
    37: [
        ("veryshort", "none",    "any",       "veryshort"),
        ("short",     "afew",    "smallplus", "short"),
        ("medium",    "medium",  "smallplus", "medium"),
        ("long",      "many",    "medium",    "long"),
        ("verylong",  "toomany", "long",      "verylong"),
    ],
    47: [
        ("veryshort", "none",    "any",       "veryshort"),
        ("short",     "afew",    "long",      "short"),
        ("medium",    "medium",  "long",      "medium"),
        ("long",      "toomany", "verylong",  "long"),
        ("verylong",  "toomany", "verylong",  "verylong"),
    ],
}

INTERVENTIONS = [7, 17, 27, 37, 47]


def _resolve_modes(mode, predicted_q, a_mode, q_mode):
    """Traduce los parametros historicos (mode, predicted_q) a (a_mode, q_mode).

    a_mode : como se cuenta A, los vehiculos que cruzan el punto critico en e s
        'arrivals' -> beta_e = arribos acumulados detectados (ejemplo, pag. 7)
        'crossing' -> beta_e = min(e, cola_verde + arribos acumulados): cruces
                      reales, limitados por el flujo de saturacion (1 veh/s)
    q_mode : en que valor se evalua la membresia de Q
        'predicted' -> beta'_e = Q + arribos acumulados del brazo en rojo (ejemplo, pag. 7)
        'current'   -> la cola actual Q (constante en e)

    Regla de resolucion (ningun parametro se ignora):
      * a_mode y q_mode, si se dan, mandan.
      * si no se da a_mode: 'crossing' para mode='capacity' y 'arrivals' para mode='literal'.
      * si no se da q_mode: 'predicted' si predicted_q es verdadero y 'current' si es falso;
        predicted_q=None toma el valor por defecto del modo (capacity -> False, literal -> True).
    """
    if a_mode is None:
        a_mode = "crossing" if mode == "capacity" else "arrivals"
    if q_mode is None:
        if predicted_q is None:
            predicted_q = mode != "capacity"
        q_mode = "predicted" if predicted_q else "current"
    return a_mode, q_mode


def _beta_and_q(arrivals_green, arrivals_cross, q_cross, q_green, a_mode, q_mode):
    """Vectores beta_e (vehiculos que cruzan) y q_e (cola evaluada), e = 1..10."""
    cum = np.cumsum(np.asarray(arrivals_green, dtype=int))
    cum_cross = np.cumsum(np.asarray(arrivals_cross, dtype=int))
    if a_mode == "crossing":
        beta = np.minimum(np.arange(1, 11), q_green + cum)
    else:
        beta = cum
    qv = q_cross + cum_cross if q_mode == "predicted" else np.full(10, q_cross)
    return beta.astype(int), qv.astype(int)


def fuzzy_decision(arrivals_green, arrivals_cross, q_cross, rules,
                   predicted_q=None, q_green=0, mode="literal",
                   a_mode=None, q_mode=None):
    """
    Calcula el vector de confianza grade[e] para e = 1..10 s (extensiones).

    arrivals_green : 10 valores 0/1 = arribos en el brazo con derecho de paso
                     durante los proximos 10 s (los que cruzaran el punto critico).
    arrivals_cross : 10 valores 0/1 = arribos en el brazo en rojo (se suman a su cola).
    q_cross        : cola Q del brazo en rojo en el instante de la intervencion.
    rules          : las 5 reglas de la intervencion en curso.
    q_green        : cola actual del brazo con derecho de paso (solo a_mode='crossing').
    a_mode, q_mode : ver _resolve_modes. Por compatibilidad tambien se acepta el
                     par historico (mode='literal'|'capacity', predicted_q).

    Para cada e (T = e), la regla (T, A, Q, E) aporta
        min(mu_T(e), mu_mt(A)(beta_e), mu_lt(Q)(q_e), mu_E(e))
    y las reglas se unen con max ("else" = max, pag. 6).

    Devuelve array grade de longitud 11 (los indices 1..10 se usan).
    """
    a_mode, q_mode = _resolve_modes(mode, predicted_q, a_mode, q_mode)
    beta, qv = _beta_and_q(arrivals_green, arrivals_cross, q_cross, q_green, a_mode, q_mode)
    grade = np.zeros(11)
    for e in range(1, 11):
        a, q = int(beta[e - 1]), int(qv[e - 1])
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
                             predicted_q=None, q_green=0, mode="literal",
                             a_mode=None, q_mode=None):
    """
    Igual que fuzzy_decision pero devuelve la matriz de grados FILA POR REGLA
    (util para graficar la Fig. 3 del paper: "aggregated membership functions").
    Shape: (n_reglas, 11).  La fila i-esima es el grado aportado por la regla i
    (antes del maximo).  El grado agregado = max sobre filas.
    """
    a_mode, q_mode = _resolve_modes(mode, predicted_q, a_mode, q_mode)
    beta, qv = _beta_and_q(arrivals_green, arrivals_cross, q_cross, q_green, a_mode, q_mode)
    out = np.zeros((len(rules), 11))
    for r, (T, A_base, Q_base, E) in enumerate(rules):
        for e in range(1, 11):
            a, q = int(beta[e - 1]), int(qv[e - 1])
            gQ = ANY if Q_base == "any" else lt_queue(Q_base, q)
            out[r, e] = min(mu_time(T, e), mt_arr(A_base, a), gQ, mu_time(E, e))
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


def decide_extension_centroid(grade, threshold=0.5):
    """VARIANTE (no es la del paper): defuzzificacion por centroide del grado agregado g(e), e = 1..10.

      * si max(grade) < threshold -> 0 (se corta el verde, igual que en el paper)
      * sino                      -> e* = redondeo del centroide  sum(e g(e)) / sum(g(e)),  1 <= e* <= 10
    """
    g = np.asarray(grade[1:11], dtype=float)
    if g.max() < threshold:
        return 0
    c = float((np.arange(1, 11) * g).sum() / g.sum())
    return int(min(10, max(1, round(c))))


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
