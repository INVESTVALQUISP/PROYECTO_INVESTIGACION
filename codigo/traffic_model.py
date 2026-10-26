"""
traffic_model.py
================================================================================
Modelo de la interseccion de trafico de Pappis & Mamdani (1977).

Hechos del paper (Seccion II y "The control process", pags. 2-3, 709):
  * Dos calles unidireccionales: N-S (N->S) y E-W (E->W), un carril cada una,
    sin giros.
  * Flujo de saturacion s = 3600 veh/h = 1 veh/s en ambos brazos.
    (Los vehiculos salen de la cola a razon constante = flujo de saturacion.)
  * Tiempo perdido total L = 10 s/ciclo. Ambar = 3 s; el verde efectivo
    termina a la mitad del ambar. Modelamos la transicion entre fases con
    LOST = 5 s (cada cambio de fase "pierde" 5 s -> 10 s/ciclo).
  * Arribos: por cada intervalo de 1 s se genera un numero pseudoaleatorio y
    se compara con la tasa media de arribo (veh/s). q_n = 1 si llega un
    vehiculo, 0 en caso contrario.  -> proceso Bernoulli de 1 veh/s max.
  * Retardo medio por vehiculo: d_m = D / (sumatoria de q_n)   [ec. (7)].

Controlador difuso (Apendice):
  * La intervencion ocurre cada 10 s durante el verde efectivo de una fase;
    la primera justo despues de los primeros 7 s. Intervenciones a los
    7, 17, 27, 37, 47 s -> verde efectivo maximo = 57 s.
  * En cada intervencion se decide la extension del verde (1..10 s) usando
    los pads de deteccion (look-ahead de ~10 s de arribos).
"""

import math

import numpy as np
from fuzzy_logic import RULES, INTERVENTIONS, fuzzy_decision, decide_extension, decide_extension_centroid

SAT = 1.0          # flujo de saturacion (veh/s)
LOST = 5.0         # tiempo perdido por cambio de fase (s) -> 10 s / ciclo

# ---------------------------------------------------------------------------
# Configuraciones del controlador difuso
# ---------------------------------------------------------------------------
# El paper fija las reglas y los conjuntos, pero NO especifica con precision como
# su programa obtenia A y Q a partir del estado de la simulacion (ver README,
# seccion "Interpretaciones"). Se dejan dos lecturas explicitas:
#
#  LITERAL  : lectura textual del ejemplo de la pag. 7
#             A = arribos acumulados detectados (beta_e)
#             Q = cola TOTAL del brazo en rojo, evaluada en la cola predicha beta'_e
#  CALIBRADA: A = vehiculos que realmente cruzan el punto critico en e s (limitados
#             por el flujo de saturacion, lo que incluye la cola del verde);
#             Q = vehiculos llegados al brazo en rojo desde que empezo el verde
#                 actual (cola "construida durante la fase"), en su valor actual.
#             Es la unica lectura de las probadas que reproduce la Tabla VIII en
#             todo el rango de caudales (ver fidelity_audit.py).
# Ambas lecturas se dan de forma explicita (a_mode, q_mode, predicted_q, queue_source): ningun parametro se ignora.
LITERAL = dict(mode="literal", a_mode="arrivals", q_mode="predicted", predicted_q=True, queue_source="total")
CALIBRADA = dict(mode="capacity", a_mode="crossing", q_mode="current", predicted_q=False, queue_source="green_arrivals")


class Sim:
    """Estado de una simulacion: colas FIFO (tiempos de arribo) y acumuladores."""

    def __init__(self, arr_ns, arr_ew, lost=LOST):
        self.arr_ns = arr_ns
        self.arr_ew = arr_ew
        self.lost = lost
        self.q_ns = []          # cola N-S: lista FIFO de tiempos de arribo
        self.q_ew = []          # cola E-W
        self.total_delay = 0.0
        self.total_arrivals = 0

    def _arrive(self, phase, t):
        q = self.q_ns if phase == 0 else self.q_ew
        q.append(t)
        self.total_arrivals += 1

    def residual_delay(self, horizon):
        """Espera acumulada hasta 'horizon' de los vehiculos que siguen en cola al final de la simulacion.

        El acumulador total_delay solo suma la espera de quien ya salio; con esta cantidad, total_delay +
        residual_delay es exactamente la suma por segundo de las colas (ecuaciones del articulo):
        sum_{n=0}^{T-1} (Q_NS,n + Q_EW,n)."""
        return float(sum(horizon - t0 for t0 in self.q_ns) + sum(horizon - t0 for t0 in self.q_ew))

    def _discharge(self, phase, t):
        q = self.q_ns if phase == 0 else self.q_ew
        if q:
            self.total_delay += (t - q.pop(0))

    # -- un segundo de simulacion (cada segundo se procesa UNA sola vez) ------
    def tick(self, t, green_phase):
        """Arribos en ambos brazos y, si hay fase verde, descarga de 1 veh/s."""
        if self.arr_ns[t]:
            self._arrive(0, t)
        if self.arr_ew[t]:
            self._arrive(1, t)
        if green_phase is not None:
            self._discharge(green_phase, t)

    def fuzzy_inputs(self, phase, g0, t, queue_source="green_arrivals"):
        """Entradas del controlador en la intervencion del instante t (justo antes
        de procesar el segundo t, es decir, tras t - g0 s de verde).

        Devuelve (arribos_verde[10], arribos_rojo[10], Q_rojo, cola_verde).
        Las ventanas son los 10 s siguientes (pads de deteccion, pag. 3 y 7).
        """
        arr_g = self.arr_ns if phase == 0 else self.arr_ew
        arr_r = self.arr_ew if phase == 0 else self.arr_ns
        q_green = len(self.q_ns if phase == 0 else self.q_ew)
        if queue_source == "total":
            q_red = len(self.q_ew if phase == 0 else self.q_ns)
        else:   # "green_arrivals": llegados al brazo en rojo desde el inicio del verde
            q_red = int(arr_r[g0:t].sum())
        return arr_g[t:t + 10].tolist(), arr_r[t:t + 10].tolist(), q_red, q_green

    # -- fase con derecho de paso, controlada por el controlador difuso -------
    def run_green_fuzzy(self, phase, t_start, duration, mode="capacity", predicted_q=None,
                        ruleset=None, threshold=0.5, trace=None,
                        queue_source="green_arrivals", a_mode=None, q_mode=None, defuzz="max"):
        """Intervenciones tras 7, 17, 27, 37 y 47 s de verde efectivo (pag. 3).

        En cada una se decide la extension e* (0 = cambiar de fase ya). Si e* = 10
        se re-interviene 10 s despues; si e* < 10 el verde termina tras e* s
        (pag. 8). Verde efectivo total = 7 + sum(e*) <= 57 s.
        """
        t = t_start
        ii = 0
        green_end = None
        rules = ruleset if ruleset is not None else RULES
        while t < duration:
            if ii < len(INTERVENTIONS) and t == t_start + INTERVENTIONS[ii]:
                wg, wr, q_red, q_green = self.fuzzy_inputs(phase, t_start, t, queue_source)
                grade = fuzzy_decision(wg, wr, q_red, rules[INTERVENTIONS[ii]],
                                       predicted_q=predicted_q, q_green=q_green, mode=mode,
                                       a_mode=a_mode, q_mode=q_mode)
                e_star = (decide_extension_centroid if defuzz == "centroid" else decide_extension)(grade, threshold)
                if trace is not None:
                    trace(phase, t - t_start, q_green, q_red, grade, e_star)
                green_end = t + e_star
                ii += 1
            if green_end is not None and t >= green_end:
                break
            self.tick(t, phase)
            t += 1
        return t

    # -- fase con derecho de paso, control ACCIONADO por vehiculo (comparador adicional) ----
    def run_green_actuated(self, phase, t_start, duration, min_green=7, max_green=57, gap=3):
        """Verde accionado por detector (extension por hueco, 'gap-out'), con los mismos limites que el difuso.

          * verde minimo de min_green s (7 s, como la primera intervencion del difuso);
          * pasado el minimo, el verde sigue mientras haya demanda en el brazo con paso (vehiculos en cola o una
            llegada en los ultimos 'gap' s); termina cuando no la hay (hueco) y el brazo contrario tiene vehiculos
            esperando; si el contrario esta vacio, el verde se mantiene;
          * verde maximo de max_green s (57 s, el maximo del difuso).
        Parametros fijos y no ajustados a ningun resultado."""
        arr_g = self.arr_ns if phase == 0 else self.arr_ew
        q_g = self.q_ns if phase == 0 else self.q_ew
        q_o = self.q_ew if phase == 0 else self.q_ns
        t = t_start
        last_arr = t_start
        while t < duration:
            el = t - t_start
            if el >= max_green:
                break
            if el >= min_green:
                demanda = len(q_g) > 0 or (t - last_arr) < gap
                if (not demanda) and len(q_o) > 0:
                    break
            self.tick(t, phase)
            if arr_g[t]:
                last_arr = t
            t += 1
        return t

    # -- fase con derecho de paso, control de ciclo fijo (para validacion) ----
    def run_green_fixed(self, phase, t_start, g_i, duration):
        t = t_start
        green_end = t_start + g_i
        while t < duration and t < green_end:
            self.tick(t, phase)
            t += 1
        return t

    def transition(self, t, duration):
        """Tiempo perdido: ambos brazos en rojo, solo arribos."""
        for _ in range(int(self.lost)):
            if t >= duration:
                break
            self.tick(t, None)
            t += 1
        return t


# ---------------------------------------------------------------------------
# Parametros de ciclo fijo optimo de Webster (ec. (9)-(10) del paper)
# ---------------------------------------------------------------------------
def webster_optimum(lam_ns, lam_ew, L=10.0, s=SAT):
    y1 = lam_ns / s
    y2 = lam_ew / s
    Y = y1 + y2
    if Y >= 1.0:
        Y = 0.95
    C0 = (1.5 * L + 5.0) / (1.0 - Y)
    # Reparto de verde PROPORCIONAL AL FLUJO (verde mas largo a la fase mas
    # cargada). NOTA: el paper escribe g_i = (1 - y_i/Y)(C0-L), pero esa forma
    # entregaria MAS verde a la fase LIGERA y saturaria la interseccion; la
    # asignacion fisicamente correcta (y la que reproduce el Cuadro I) es
    # g_i = (y_i/Y)(C0 - L).
    g1 = (y1 / Y) * (C0 - L)
    g2 = (y2 / Y) * (C0 - L)
    return C0, g1, g2


def webster_delay_formula(lam_ns, lam_ew, L=10.0, s=SAT):
    """Retardo medio esperado (columna 'Formula' de la Tabla I, formula de
    Webster [6], pag. 3):  d = C(1-l)^2 / (2(1-lX)) + X^2 / (2q(1-X))
                               - 0.65 (C/q^2)^(1/3) X^(2+5l),
    con l = g/C, X = q/(l s). Se evalua en cada brazo con los ajustes optimos
    (ec. 8-10) y se pondera por el flujo de cada brazo."""
    C0, g1, g2 = webster_optimum(lam_ns, lam_ew, L, s)
    total, flow = 0.0, 0.0
    for q, g in ((lam_ns, g1), (lam_ew, g2)):
        lam = g / C0
        X = q / (lam * s)
        d = (C0 * (1 - lam) ** 2 / (2 * (1 - lam * X)) + X ** 2 / (2 * q * (1 - X))
             - 0.65 * (C0 / q ** 2) ** (1 / 3) * X ** (2 + 5 * lam))
        total += q * d
        flow += q
    return total / flow


# ---------------------------------------------------------------------------
# Simulaciones
# ---------------------------------------------------------------------------
def _make_arrivals(lam_ns, lam_ew, seed, duration):
    rng = np.random.default_rng(seed)
    N = duration + 60
    arr_ns = (rng.random(N) < lam_ns).astype(int)
    arr_ew = (rng.random(N) < lam_ew).astype(int)
    return arr_ns, arr_ew


def simulate_fuzzy(lam_ns, lam_ew, seed, duration=7200, lost=LOST,
                  mode="capacity", predicted_q=None, ruleset=None, threshold=0.5,
                  queue_source="green_arrivals", a_mode=None, q_mode=None, include_residual=False, defuzz="max"):
    arr_ns, arr_ew = _make_arrivals(lam_ns, lam_ew, seed, duration)
    sim = Sim(arr_ns, arr_ew, lost=lost)
    t = 0
    phase = 0
    while t < duration:
        t = sim.run_green_fuzzy(phase, t, duration, mode=mode, predicted_q=predicted_q,
                                ruleset=ruleset, threshold=threshold,
                                queue_source=queue_source, a_mode=a_mode, q_mode=q_mode, defuzz=defuzz)
        t = sim.transition(t, duration)
        phase = 1 - phase
    extra = sim.residual_delay(duration) if include_residual else 0.0
    return (sim.total_delay + extra) / sim.total_arrivals


def simulate_fixed_cycle(lam_ns, lam_ew, seed, duration=7200, lost=LOST, include_residual=False, rounding="nearest"):
    """Ciclo fijo con los ajustes optimos de Webster.

    rounding="nearest": cada verde efectivo se redondea al entero mas proximo (protocolo oficial; el modelo avanza en
                        pasos de 1 s).
    rounding="dither" : los verdes se reparten en numeros enteros de modo que su PROMEDIO sea exactamente g1 y g2 sin
                        redondear (redondeo acumulado: g_k = round(k g) - round((k-1) g)); mide el efecto de redondear.
    """
    C0, g1, g2 = webster_optimum(lam_ns, lam_ew)
    arr_ns, arr_ew = _make_arrivals(lam_ns, lam_ew, seed, duration)
    sim = Sim(arr_ns, arr_ew, lost=lost)
    t = 0
    phase = 0
    cycle = 0
    # el modelo avanza en unidades de 1 s (pag. 2): verde efectivo en s enteros
    g = [math.floor(g1 + 0.5), math.floor(g2 + 0.5)]
    while t < duration:
        if rounding == "dither" and phase == 0:
            k = cycle + 1
            g = [math.floor(k * g1 + 0.5) - math.floor((k - 1) * g1 + 0.5),
                 math.floor(k * g2 + 0.5) - math.floor((k - 1) * g2 + 0.5)]
            cycle += 1
        t = sim.run_green_fixed(phase, t, g[phase], duration)
        t = sim.transition(t, duration)
        phase = 1 - phase
    extra = sim.residual_delay(duration) if include_residual else 0.0
    return (sim.total_delay + extra) / sim.total_arrivals


def simulate_actuated(lam_ns, lam_ew, seed, duration=7200, lost=LOST, include_residual=False,
                      min_green=7, max_green=57, gap=3):
    """Comparador accionado por vehiculo (extension por hueco), ver Sim.run_green_actuated."""
    arr_ns, arr_ew = _make_arrivals(lam_ns, lam_ew, seed, duration)
    sim = Sim(arr_ns, arr_ew, lost=lost)
    t = 0
    phase = 0
    while t < duration:
        t = sim.run_green_actuated(phase, t, duration, min_green=min_green, max_green=max_green, gap=gap)
        t = sim.transition(t, duration)
        phase = 1 - phase
    extra = sim.residual_delay(duration) if include_residual else 0.0
    return (sim.total_delay + extra) / sim.total_arrivals


def average(sim_func, lam_ns, lam_ew, reps=30, duration=7200, base_seed=0, **kwargs):
    """Promedia 'reps' replicas independientes para reducir la varianza."""
    vals = [sim_func(lam_ns, lam_ew, base_seed + k, duration=duration, **kwargs)
            for k in range(reps)]
    return float(np.mean(vals)), float(np.std(vals, ddof=1))   # desviacion estandar de la muestra (n-1)


# Combinaciones de caudal del Cuadro VIII del paper (veh/h)
COMBINATIONS = [
    (360, 360), (360, 720), (360, 1080), (360, 1440),
    (360, 1800), (360, 2160), (360, 2520),
    (720, 720), (720, 1080), (720, 1440), (720, 1800), (720, 2160),
    (1080, 1080), (1080, 1440), (1080, 1800),
    (1440, 1440),
]


def run_table(reps=30, duration=7200, base_seed=0, mode="capacity", predicted_q=None,
              queue_source="green_arrivals", a_mode=None, q_mode=None):
    """Reproduce el Cuadro VIII: compara control de ciclo fijo (linea base de
    actuation por vehiculo eficaz) contra controlador difuso, con numeros aleatorios comunes
    (semillas base_seed .. base_seed + reps - 1 para ambos controladores)."""
    rows = []
    for ns, ew in COMBINATIONS:
        lns, lew = ns / 3600.0, ew / 3600.0
        dm_fixed, sd_fixed = average(simulate_fixed_cycle, lns, lew, reps, duration, base_seed)
        # numeros aleatorios comunes (CRN): fijo y difuso ven las MISMAS llegadas en cada replica
        dm_fz, sd_fz = average(simulate_fuzzy, lns, lew, reps, duration,
                               base_seed, mode=mode, predicted_q=predicted_q,
                               queue_source=queue_source, a_mode=a_mode, q_mode=q_mode)
        imp = (dm_fixed - dm_fz) / dm_fixed * 100.0
        rows.append((ns, ew, dm_fixed, dm_fz, imp))
    return rows
