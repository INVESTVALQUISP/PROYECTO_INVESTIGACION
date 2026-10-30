"""
opt_politicas.py
================================================================================
Politicas de control de la interseccion que deciden CADA SEGUNDO si se sigue en verde o se cambia de fase,
a partir de un vector de caracteristicas. Sirven como COTA de lo que se puede lograr con la informacion
disponible (red neuronal pequena entrenada con CMA-ES) y como punto de comparacion de los controladores
difusos. Se usan con sim_batch.BatchSim (hook 'stop').

Caracteristicas (todas normalizadas aprox. a [0, 1]):
    q_g, q_r        colas del brazo con verde y del brazo en rojo
    el              segundos de verde transcurridos
    wg3, wg10       llegadas al brazo con verde en los proximos 3 y 10 s   (VISTA ADELANTE, como en el paper)
    wr3, wr10       llegadas al brazo en rojo en los proximos 3 y 10 s     (VISTA ADELANTE)
    pg5, pr5        llegadas por segundo en los ultimos 5 s (verde, rojo)  (causal)
    pg20, pr20      llegadas por segundo en los ultimos 20 s               (causal)
    cola_vacia      1 si el brazo con verde no tiene cola
Con preview=False las cuatro caracteristicas de vista adelante valen 0: la politica es CAUSAL (solo usa lo ya ocurrido).
"""
import numpy as np

NOMBRES = ["q_g", "q_r", "el", "wg3", "wg10", "wr3", "wr10", "pg5", "pr5", "pg20", "pr20", "cola_vacia"]
F = len(NOMBRES) + 1       # + sesgo


def caracteristicas(sim, t, preview=True):
    a = sim.arr
    ns = sim.phase == 0
    q_g = np.where(ns, sim.q_ns, sim.q_ew).astype(np.float32)
    q_r = np.where(ns, sim.q_ew, sim.q_ns).astype(np.float32)
    el = (t - sim.tstart).astype(np.float32)
    c0_ns, c0_ew = a.C_ns[:, t], a.C_ew[:, t]
    X = np.empty((a.R, F), dtype=np.float32)
    X[:, 0] = 1.0
    X[:, 1] = q_g / 10
    X[:, 2] = q_r / 10
    X[:, 3] = el / 30
    if preview:
        for col, k in ((4, 3), (5, 10)):
            X[:, col] = np.where(ns, a.C_ns[:, t + k] - c0_ns, a.C_ew[:, t + k] - c0_ew) / k
            X[:, col + 2] = np.where(ns, a.C_ew[:, t + k] - c0_ew, a.C_ns[:, t + k] - c0_ns) / k
    else:
        X[:, 4:8] = 0.0
    for col, k in ((8, 5), (10, 20)):
        tp = max(t - k, 0)
        kk = max(t - tp, 1)
        X[:, col] = np.where(ns, c0_ns - a.C_ns[:, tp], c0_ew - a.C_ew[:, tp]) / kk
        X[:, col + 1] = np.where(ns, c0_ew - a.C_ew[:, tp], c0_ns - a.C_ns[:, tp]) / kk
    X[:, 12] = (q_g == 0)
    return X


def n_parametros(hidden):
    return F + 1 if hidden == 0 else F * hidden + hidden + hidden + 1


class PoliticaStop:
    """Corta el verde cuando la salida de la red es positiva (y el verde ya paso el minimo gmin).
    hidden=0: politica lineal; hidden>0: perceptron de una capa oculta con tanh."""

    def __init__(self, theta, hidden=8, preview=True, gmin=7):
        theta = np.asarray(theta, dtype=np.float32)
        self.hidden, self.preview, self.gmin = hidden, preview, gmin
        if hidden == 0:
            self.w = theta[:F]
            self.b = theta[F]
        else:
            i = F * hidden
            self.W1 = theta[:i].reshape(F, hidden)
            self.b1 = theta[i:i + hidden]
            self.w2 = theta[i + hidden:i + 2 * hidden]
            self.b2 = theta[i + 2 * hidden]

    def stop(self, sim, t, green):
        el = t - sim.tstart
        cand = green & (el >= self.gmin)
        if not cand.any():
            return cand
        X = caracteristicas(sim, t, self.preview)
        if self.hidden == 0:
            s = X @ self.w + self.b
        else:
            s = np.tanh(X @ self.W1 + self.b1) @ self.w2 + self.b2
        return cand & (s > 0)
