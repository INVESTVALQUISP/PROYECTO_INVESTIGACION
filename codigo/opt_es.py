"""
opt_es.py
================================================================================
Optimizador por estrategia evolutiva con adaptacion de la matriz de covarianza (CMA-ES), solo con NumPy.
Sigue el algoritmo de Hansen (2016), "The CMA Evolution Strategy: A Tutorial", arXiv:1604.00772:
(mu/mu_w, lambda)-CMA-ES con pesos logaritmicos, adaptacion de paso por longitud de camino acumulado
(CSA), actualizacion de rango uno y de rango mu de la covarianza.

Minimiza una funcion f(theta) (aqui, el retardo medio normalizado de un controlador en un conjunto de escenarios
de entrenamiento). La poblacion se evalua en paralelo con multiprocessing (fork): los datos pesados
(llegadas de los escenarios) viven en variables globales del proceso padre y no se copian.
"""
import multiprocessing as mp

import numpy as np

_F = None          # funcion objetivo del proceso (se hereda por fork)


def _eval_one(theta):
    return _F(theta)


class CMAES:
    def __init__(self, x0, sigma0, popsize=None, seed=0, bounds=None):
        self.n = n = len(x0)
        self.rng = np.random.default_rng(seed)
        self.mean = np.asarray(x0, dtype=float).copy()
        self.sigma = float(sigma0)
        self.lam = popsize or (4 + int(3 * np.log(n)))
        self.mu = self.lam // 2
        w = np.log(self.mu + 0.5) - np.log(np.arange(1, self.mu + 1))
        self.w = w / w.sum()
        self.mueff = 1.0 / np.sum(self.w ** 2)
        self.cc = (4 + self.mueff / n) / (n + 4 + 2 * self.mueff / n)
        self.cs = (self.mueff + 2) / (n + self.mueff + 5)
        self.c1 = 2 / ((n + 1.3) ** 2 + self.mueff)
        self.cmu = min(1 - self.c1, 2 * (self.mueff - 2 + 1 / self.mueff) / ((n + 2) ** 2 + self.mueff))
        self.damps = 1 + 2 * max(0, np.sqrt((self.mueff - 1) / (n + 1)) - 1) + self.cs
        self.pc = np.zeros(n)
        self.ps = np.zeros(n)
        self.B = np.eye(n)
        self.D = np.ones(n)
        self.C = np.eye(n)
        self.invsqrtC = np.eye(n)
        self.chiN = np.sqrt(n) * (1 - 1 / (4 * n) + 1 / (21 * n ** 2))
        self.gen = 0
        self.bounds = bounds

    def ask(self):
        z = self.rng.standard_normal((self.lam, self.n))
        y = z @ (self.B * self.D).T
        x = self.mean + self.sigma * y
        if self.bounds is not None:
            x = np.clip(x, self.bounds[0], self.bounds[1])
        return x

    def tell(self, x, f):
        order = np.argsort(f)
        x = x[order]
        old = self.mean.copy()
        self.mean = self.w @ x[: self.mu]
        y = (self.mean - old) / self.sigma
        self.ps = (1 - self.cs) * self.ps + np.sqrt(self.cs * (2 - self.cs) * self.mueff) * (self.invsqrtC @ y)
        hsig = (np.linalg.norm(self.ps) / np.sqrt(1 - (1 - self.cs) ** (2 * (self.gen + 1))) / self.chiN
                < 1.4 + 2 / (self.n + 1))
        self.pc = (1 - self.cc) * self.pc + hsig * np.sqrt(self.cc * (2 - self.cc) * self.mueff) * y
        ys = (x[: self.mu] - old) / self.sigma
        self.C = ((1 - self.c1 - self.cmu) * self.C
                  + self.c1 * (np.outer(self.pc, self.pc) + (1 - hsig) * self.cc * (2 - self.cc) * self.C)
                  + self.cmu * (ys.T * self.w) @ ys)
        self.sigma *= np.exp((self.cs / self.damps) * (np.linalg.norm(self.ps) / self.chiN - 1))
        self.sigma = min(self.sigma, 1e3)
        self.gen += 1
        if self.gen % max(1, int(1 / (10 * self.n * (self.c1 + self.cmu)))) == 0:   # descomposicion espectral esporadica
            self.C = (self.C + self.C.T) / 2
            d2, self.B = np.linalg.eigh(self.C)
            d2 = np.maximum(d2, 1e-20)
            self.D = np.sqrt(d2)
            self.invsqrtC = (self.B / self.D) @ self.B.T
        return float(f[order[0]]), x[0]


def minimize(f, x0, sigma0=0.3, generations=100, popsize=None, seed=0, workers=None, log=None, bounds=None,
             f_polish=None):
    """Devuelve (mejor theta, mejor f, historial). f debe ser una funcion de nivel de modulo/closure (fork)."""
    global _F
    _F = f
    es = CMAES(x0, sigma0, popsize, seed, bounds)
    hist = []
    best_x, best_f = np.asarray(x0, dtype=float), np.inf
    pool = None
    workers = workers or max(1, mp.cpu_count())
    if workers > 1:
        pool = mp.get_context("fork").Pool(workers)
    try:
        for g in range(generations):
            X = es.ask()
            fx = np.array(pool.map(_eval_one, list(X))) if pool else np.array([f(x) for x in X])
            gb, gx = es.tell(X, fx)
            if gb < best_f:
                best_f, best_x = gb, gx.copy()
            hist.append((g, gb, float(np.mean(fx)), es.sigma))
            if log:
                log(g, gb, best_f, float(np.mean(fx)), es.sigma)
    finally:
        if pool:
            pool.close()
            pool.join()
    return best_x, best_f, hist
