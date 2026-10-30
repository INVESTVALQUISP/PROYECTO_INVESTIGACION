"""
opt_flc2.py
================================================================================
Controlador difuso NUEVO, de pocas reglas, que decide cada segundo si el verde sigue o se cambia de fase.

Variables linguisticas (3 conjuntos cada una, particion de Ruspini con tres nudos k1 < k2 < k3: "bajo" es 1 hasta k1,
"medio" es un triangulo con pico en k2, "alto" es 1 desde k3):
    G  demanda en verde  = cola del brazo con verde + llegadas esperadas en los proximos h s en ese brazo
    R  presion en rojo   = cola del brazo en rojo  + llegadas esperadas en los proximos 5 s en ese brazo
    E  verde transcurrido (s)
Base de 27 reglas  "SI G es g_i Y R es r_j Y E es e_k ENTONCES cambiar = c_ijk", con consecuentes numericos c_ijk
(conjuntos de salida de un solo punto). Inferencia: fuerza de la regla = producto de las tres pertenencias; salida
    s = sum(w_ijk c_ijk) / sum(w_ijk)      (centro de gravedad de los consecuentes; Mamdani con salidas singleton,
                                             equivalente a Takagi-Sugeno de orden cero)
Se corta el verde si s > 0 (y el verde ya paso el minimo gmin). Parametros: 9 nudos + 27 consecuentes = 36.

Las llegadas esperadas son las del futuro cercano (vista adelante, como las almohadillas de deteccion del paper) o, con
preview=False, la tasa observada en los ultimos 10 s por el horizonte correspondiente (controlador CAUSAL).
"""
import numpy as np

N_PARAM = 36
H_VERDE = 4          # horizonte (s) de las llegadas esperadas en el brazo con verde
H_ROJO = 5           # horizonte (s) de las llegadas esperadas en el brazo en rojo (el tiempo perdido)


def _nudos(p):
    """3 nudos crecientes a partir de 3 numeros libres: k1 = |p0|, k2 = k1 + |p1| + 0.05, k3 = k2 + |p2| + 0.05."""
    k1 = abs(p[0])
    k2 = k1 + abs(p[1]) + 0.05
    k3 = k2 + abs(p[2]) + 0.05
    return k1, k2, k3


def ruspini(x, k):
    """Pertenencias (n, 3) a bajo / medio / alto de x segun los nudos k = (k1, k2, k3)."""
    k1, k2, k3 = k
    bajo = np.clip((k2 - x) / (k2 - k1), 0, 1)
    alto = np.clip((x - k2) / (k3 - k2), 0, 1)
    medio = 1 - bajo - alto
    # fuera de [k1, k3] bajo/alto valen 1 y medio 0
    bajo = np.where(x <= k1, 1.0, bajo)
    alto = np.where(x >= k3, 1.0, alto)
    medio = np.where((x <= k1) | (x >= k3), 0.0, medio)
    return np.stack([bajo, medio, alto], axis=1)


THETA0 = np.concatenate([
    [0.0, 2.0, 3.0],          # G: nudos 0, 2.05, 5.1
    [0.0, 8.0, 12.0],         # R: nudos 0, 8.05, 20.1
    [7.0, 18.0, 30.0],        # E: nudos 7, 25.05, 55.1
    # consecuentes c[g, r, e]: cambiar (+) si la demanda en verde es baja y hay presion en rojo
    np.array([[[(1.0 if (g == 0 and r >= 1) else (0.5 if (g == 1 and r == 2) else -1.0)) for e in range(3)]
               for r in range(3)] for g in range(3)]).ravel(),
])


class FuzzySegundo:
    def __init__(self, theta, preview=True, gmin=7):
        th = np.asarray(theta, dtype=float)
        self.kG, self.kR, self.kE = _nudos(th[0:3]), _nudos(th[3:6]), _nudos(th[6:9])
        self.kE = tuple(x + 0.0 for x in self.kE)
        self.c = th[9:36]
        self.preview, self.gmin = preview, gmin

    def entradas(self, sim, t):
        a = sim.arr
        ns = sim.phase == 0
        q_g = np.where(ns, sim.q_ns, sim.q_ew)
        q_r = np.where(ns, sim.q_ew, sim.q_ns)
        c0_ns, c0_ew = a.C_ns[:, t], a.C_ew[:, t]
        if self.preview:
            w_g = np.where(ns, a.C_ns[:, t + H_VERDE] - c0_ns, a.C_ew[:, t + H_VERDE] - c0_ew)
            w_r = np.where(ns, a.C_ew[:, t + H_ROJO] - c0_ew, a.C_ns[:, t + H_ROJO] - c0_ns)
        else:
            tp = max(t - 10, 0)
            kk = max(t - tp, 1)
            r_g = np.where(ns, c0_ns - a.C_ns[:, tp], c0_ew - a.C_ew[:, tp]) / kk
            r_r = np.where(ns, c0_ew - a.C_ew[:, tp], c0_ns - a.C_ns[:, tp]) / kk
            w_g, w_r = r_g * H_VERDE, r_r * H_ROJO
        return q_g + w_g, q_r + w_r, (t - sim.tstart)

    def score(self, G, R, E):
        w = (ruspini(G, self.kG)[:, :, None, None] * ruspini(R, self.kR)[:, None, :, None]
             * ruspini(E, self.kE)[:, None, None, :]).reshape(len(G), 27)
        return (w @ self.c) / (w.sum(1) + 1e-9)

    def stop(self, sim, t, green):
        cand = green & ((t - sim.tstart) >= self.gmin)
        if not cand.any():
            return cand
        G, R, E = self.entradas(sim, t)
        return cand & (self.score(G, R, E) > 0)

    def reglas_texto(self):
        nom = ["bajo", "medio", "alto"]
        out = []
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    out.append((nom[i], nom[j], nom[k], float(self.c[i * 9 + j * 3 + k])))
        return out
