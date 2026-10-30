"""
opt_mdp.py
================================================================================
Politica OPTIMA por programacion dinamica (iteracion de valor relativa) para caudales CONOCIDOS y sin vista adelante.

Es una cota de referencia, no un controlador realizable: supone que el controlador conoce las tasas de llegada
(p_ns, p_ew por segundo) y ve las dos colas, pero no ve llegadas futuras. Sirve para saber cuanto se puede mejorar
con la informacion de colas y tasas, y se compara con los controladores que no conocen los caudales.

Proceso de decision de Markov (un paso = 1 s), identico a sim_batch:
  estado de verde  G(fase, q_ns, q_ew)
  accion           continuar (llegadas y descarga de 1 veh/s del brazo con verde) o cambiar (empieza el tiempo perdido)
  tiempo perdido   L_j(fase destino, q_ns, q_ew), j = 1..LOST-1 segundos ya perdidos; el segundo LOST abre el verde
  costo por paso   q_ns + q_ew al final del segundo   (suma de colas = retardo total, ecuacion del articulo)
Sin minimo ni maximo de verde. Colas truncadas a QMAX. Se minimiza el costo medio por segundo con iteracion de valor
relativa (se resta cada vez el valor del estado de referencia, G(fase 0, colas vacias)).
"""
import numpy as np

QMAX = 90
LOST = 5


def resolver(p_ns, p_ew, iters=20000, tol=1e-7, qmax=QMAX, lost=LOST):
    """Devuelve (cambiar[fase, q_ns, q_ew] bool, costo medio por segundo = suma media de colas, iteraciones)."""
    Q = qmax + 1
    q1, q2 = np.meshgrid(np.arange(Q), np.arange(Q), indexing="ij")
    llegadas = [(0, 0, (1 - p_ns) * (1 - p_ew)), (1, 0, p_ns * (1 - p_ew)), (0, 1, (1 - p_ns) * p_ew), (1, 1, p_ns * p_ew)]

    def tras(a1, a2, desc):
        """Colas al final del segundo (llegadas y descarga del brazo desc = 0 ninguno, 1 N-S, 2 E-W)."""
        n1 = np.minimum(q1 + a1, qmax)
        n2 = np.minimum(q2 + a2, qmax)
        if desc == 1:
            n1 = np.maximum(n1 - 1, 0)
        elif desc == 2:
            n2 = np.maximum(n2 - 1, 0)
        return n1, n2

    t_verde = [[(*tras(a1, a2, 1 + ph), pr) for a1, a2, pr in llegadas] for ph in (0, 1)]   # por fase con verde
    t_perdido = [(*tras(a1, a2, 0), pr) for a1, a2, pr in llegadas]
    VG = np.zeros((2, Q, Q))
    VL = np.zeros((lost - 1, 2, Q, Q))
    it = 0
    for it in range(1, iters + 1):
        cont = np.zeros((2, Q, Q))
        cambiar = np.zeros((2, Q, Q))
        VLn = np.zeros_like(VL)
        for ph in (0, 1):
            for n1, n2, pr in t_verde[ph]:
                cont[ph] += pr * (n1 + n2 + VG[ph][n1, n2])
            for n1, n2, pr in t_perdido:
                cambiar[ph] += pr * (n1 + n2 + VL[0][1 - ph][n1, n2])
                for j in range(lost - 1):                  # j = segundos ya perdidos - 1
                    sig = VL[j + 1][ph][n1, n2] if j < lost - 2 else VG[ph][n1, n2]
                    VLn[j][ph] += pr * (n1 + n2 + sig)
        VGn = np.minimum(cont, cambiar)
        g = float(VGn[0, 0, 0])                    # costo medio por segundo (valor del estado de referencia)
        VGn -= g
        VLn -= g
        delta = max(np.abs(VGn - VG).max(), np.abs(VLn - VL).max())
        VG, VL = VGn, VLn
        if it > 100 and delta < tol:
            break
    return cambiar < cont, g, it


class PoliticaMDP:
    """Controlador para BatchSim(max_green=None): corta el verde cuando la politica optima lo indica.
    tablas: (R, 2, Q, Q) bool, la politica de cada escenario (cada uno con sus caudales conocidos)."""

    def __init__(self, tablas):
        self.tablas = tablas

    def stop(self, sim, t, green):
        Q = self.tablas.shape[2] - 1
        idx = np.arange(sim.arr.R)
        return green & self.tablas[idx, sim.phase.astype(int), np.minimum(sim.q_ns, Q), np.minimum(sim.q_ew, Q)]
