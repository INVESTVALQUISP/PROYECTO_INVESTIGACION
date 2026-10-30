"""
opt_controladores.py
================================================================================
Controladores para el simulador por lotes (sim_batch.py). Los tres primeros reproducen, escenario a escenario
y de forma exacta, a los de traffic_model.py:

  FixedCycle    ciclo fijo con los ajustes optimos de Webster (conoce los caudales)
  Actuated      verde por detector con extension por hueco (gap-out)
  PappisFuzzy   controlador difuso de Pappis y Mamdani (1977): 25 reglas, inferencia min-max,
                decision = argmax del grado, umbral 0.5

Los controladores optimizados (opt_flc.py, opt_politicas.py) usan la misma interfaz.
"""
import math

import numpy as np

import fuzzy_logic as fl
from traffic_model import webster_optimum


# ---------------------------------------------------------------------------
# Ciclo fijo de Webster
# ---------------------------------------------------------------------------
class FixedCycle:
    """Verde efectivo de cada fase fijo. rounding='nearest' (protocolo oficial) o 'dither' (promedio exacto)."""

    def __init__(self, lam_ns, lam_ew, rounding="nearest"):
        lam_ns = np.atleast_1d(np.asarray(lam_ns, dtype=float))
        lam_ew = np.atleast_1d(np.asarray(lam_ew, dtype=float))
        w = [webster_optimum(a, b) for a, b in zip(lam_ns, lam_ew)]
        self.g1 = np.array([x[1] for x in w])
        self.g2 = np.array([x[2] for x in w])
        self.rounding = rounding

    def reset(self, sim):
        self.cycle = np.zeros(sim.arr.R, dtype=np.int64)
        self.gk = np.zeros((sim.arr.R, 2), dtype=np.int64)

    def on_green_start(self, sim, idx, t):
        ph = sim.phase[idx]
        if self.rounding == "nearest":
            g = np.where(ph == 0, np.floor(self.g1[idx] + 0.5), np.floor(self.g2[idx] + 0.5)).astype(np.int64)
        else:
            new = idx[ph == 0]
            if len(new):
                k = self.cycle[new] + 1
                self.cycle[new] = k
                for j, gj in enumerate((self.g1, self.g2)):
                    self.gk[new, j] = np.floor(k * gj[new] + 0.5) - np.floor((k - 1) * gj[new] + 0.5)
            g = self.gk[idx, ph]
        return t + g


# ---------------------------------------------------------------------------
# Verde por detector (gap-out)
# ---------------------------------------------------------------------------
class Actuated:
    """Termina el verde cuando, pasado el minimo, no hay demanda en el brazo con verde (cola vacia y sin llegadas
    en los ultimos 'gap' s) y el otro brazo tiene vehiculos esperando. El maximo lo da BatchSim(max_green=...)."""

    def __init__(self, min_green=7, gap=3):
        self.min_green, self.gap = min_green, gap

    def stop(self, sim, t, green):
        ns = sim.phase == 0
        q_g = np.where(ns, sim.q_ns, sim.q_ew)
        q_o = np.where(ns, sim.q_ew, sim.q_ns)
        el = t - sim.tstart
        demanda = (q_g > 0) | ((t - sim.last_arr) < self.gap)
        return green & (el >= self.min_green) & ~demanda & (q_o > 0)


# ---------------------------------------------------------------------------
# Controlador difuso de Pappis y Mamdani (1977), vectorizado
# ---------------------------------------------------------------------------
def _tabla_mt(base):          # indice a = 0..10 (0 = fuera del universo)
    return np.array([fl.mt_arr(base, a) if a >= 1 else 0.0 for a in range(11)])


def _tabla_lt(base):          # indice q = 0..33 (q > 32 se trata como 33 -> 0)
    if base == "any":
        return np.ones(34)
    return np.array([fl.lt_queue(base, q) for q in range(34)])


def _tablas_reglas(rules=None):
    rules = rules or fl.RULES
    K = len(fl.INTERVENTIONS)
    T = np.zeros((K, 5, 10)); MT = np.zeros((K, 5, 11)); LT = np.zeros((K, 5, 34)); E = np.zeros((K, 5, 10))
    for k, it in enumerate(fl.INTERVENTIONS):
        for r, (t_, a_, q_, e_) in enumerate(rules[it]):
            T[k, r] = fl.MU_TIME[t_]
            MT[k, r] = _tabla_mt(a_)
            LT[k, r] = _tabla_lt(q_)
            E[k, r] = fl.MU_TIME[e_]
    return T, MT, LT, E


def decidir_extension(grade, threshold):
    """grade (n, 10) para e = 1..10: 0 si el maximo < umbral; si no, la e de mayor grado (empate: la mayor)."""
    best = grade.max(axis=1)
    e = 10 - np.argmax(grade[:, ::-1], axis=1)
    return np.where(best < threshold, 0, e)


class PappisFuzzy:
    """Las 25 reglas del Apendice. Intervenciones a los 7, 17, 27, 37 y 47 s de verde (BatchSim(gmin=7, delta=10,
    max_green=57)). Lectura de las entradas A y Q como en traffic_model (CALIBRADA por defecto)."""

    def __init__(self, a_mode="crossing", q_mode="current", queue_source="green_arrivals", threshold=0.5):
        self.a_mode, self.q_mode, self.queue_source, self.threshold = a_mode, q_mode, queue_source, threshold
        self.T, self.MT, self.LT, self.E = _tablas_reglas()

    def grados(self, ctx):
        k = ((ctx.el - 7) // 10).astype(int)
        cum_g = np.cumsum(ctx.wg, axis=1)
        cum_r = np.cumsum(ctx.wr, axis=1)
        e = np.arange(1, 11)[None, :]
        beta = np.minimum(e, ctx.q_g[:, None] + cum_g) if self.a_mode == "crossing" else cum_g
        q_cross = ctx.red_since_green if self.queue_source == "green_arrivals" else ctx.q_r
        qv = q_cross[:, None] + cum_r if self.q_mode == "predicted" else np.repeat(q_cross[:, None], 10, axis=1)
        ia = np.minimum(beta, 10)
        iq = np.minimum(qv, 33)
        kk = k[:, None]
        grade = np.zeros((len(k), 10))
        for r in range(5):
            g = np.minimum(np.minimum(self.T[k, r], self.MT[kk, r, ia]), np.minimum(self.LT[kk, r, iq], self.E[k, r]))
            grade = np.maximum(grade, g)
        return grade

    def decide(self, sim, ctx):
        return decidir_extension(self.grados(ctx), self.threshold)


# ---------------------------------------------------------------------------
# Presion maxima (max-pressure), version de dos fases en una interseccion aislada
# ---------------------------------------------------------------------------
class MaxPressure:
    """Cambia de fase cuando la presion del brazo en rojo (su cola) supera a la del brazo con verde en al menos
    'margen' vehiculos, pasado el verde minimo. En una interseccion aislada la presion de un brazo es su cola
    (no hay tramo aguas abajo). El maximo lo da BatchSim(max_green=...)."""

    def __init__(self, min_green=7, margen=0):
        self.min_green, self.margen = min_green, margen

    def stop(self, sim, t, green):
        ns = sim.phase == 0
        q_g = np.where(ns, sim.q_ns, sim.q_ew)
        q_r = np.where(ns, sim.q_ew, sim.q_ns)
        return green & ((t - sim.tstart) >= self.min_green) & ((q_r - q_g) >= self.margen)
