"""
opt_flc.py
================================================================================
Controladores difusos OPTIMIZABLES para sim_batch.

PappisAfinado   conserva la estructura del paper (25 reglas, mismas tablas de pertenencia, inferencia min-max,
                intervenciones a los 7, 17, 27, 37 y 47 s, extension de 0 a 10 s) y solo AFINA 30 numeros:
                    tau          umbral de decision (paper: 0.5)
                    sA, oA       entrada A' = sA * A + oA   (escala y desplazamiento del universo de arribos)
                    sQ, oQ       entrada Q' = sQ * Q + oQ   (idem para la cola)
                    delta[25]    desplazamiento (s) del conjunto de tiempo/extension de cada regla
                Las tablas discretas se interpolan linealmente para evaluarlas en valores reales.
                theta = (tau, sA, oA, sQ, oQ, delta_1..delta_25); el valor del paper es
                (0.5, 1, 0, 1, 0, 0, ..., 0).
"""
import numpy as np

from opt_controladores import PappisFuzzy, decidir_extension

THETA_PAPER = np.array([0.5, 1.0, 0.0, 1.0, 0.0] + [0.0] * 25)
LIMITES = (np.array([0.2, 0.4, -4.0, 0.4, -8.0] + [-4.0] * 25),
           np.array([0.95, 2.5, 4.0, 2.5, 8.0] + [4.0] * 25))


def _interp(tabla, x):
    """tabla (m, n) evaluada en los indices reales x (m, p) fila a fila; extremos constantes."""
    n = tabla.shape[-1]
    x = np.clip(x, 0, n - 1)
    i0 = np.minimum(np.floor(x).astype(int), n - 2)
    f = x - i0
    return (1 - f) * np.take_along_axis(tabla, i0, -1) + f * np.take_along_axis(tabla, i0 + 1, -1)


class PappisAfinado(PappisFuzzy):
    def __init__(self, theta=THETA_PAPER, **kw):
        super().__init__(**kw)
        th = np.asarray(theta, dtype=float)
        self.threshold = float(th[0])
        self.sA, self.oA, self.sQ, self.oQ = th[1:5]
        delta = th[5:30].reshape(5, 5)
        e = np.arange(1, 11, dtype=float)
        # T y E comparten etiqueta en las 25 reglas: un unico conjunto de tiempo desplazado por regla
        self.TE = np.zeros((5, 5, 10))
        for k in range(5):
            for r in range(5):
                base = self.T[k, r]                       # mu_T(e), e = 1..10
                self.TE[k, r] = np.interp(e - delta[k, r], e, base, left=base[0], right=base[-1])

    def grados(self, ctx):
        k = ((ctx.el - 7) // 10).astype(int)
        cum_g = np.cumsum(ctx.wg, axis=1)
        e = np.arange(1, 11)[None, :]
        beta = np.minimum(e, ctx.q_g[:, None] + cum_g) if self.a_mode == "crossing" else cum_g
        q_cross = ctx.red_since_green if self.queue_source == "green_arrivals" else ctx.q_r
        qv = np.repeat(q_cross[:, None], 10, axis=1) if self.q_mode == "current" else q_cross[:, None] + np.cumsum(ctx.wr, axis=1)
        xa = np.clip(self.sA * beta + self.oA, 0, 10)
        xq = np.clip(self.sQ * qv + self.oQ, 0, 33)
        grade = np.zeros((len(k), 10))
        for r in range(5):
            mt = _interp(self.MT[k, r], xa)
            lt = _interp(self.LT[k, r], xq)
            grade = np.maximum(grade, np.minimum(self.TE[k, r], np.minimum(mt, lt)))
        return grade

    def decide(self, sim, ctx):
        return decidir_extension(self.grados(ctx), self.threshold)
