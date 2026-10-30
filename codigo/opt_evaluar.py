"""
opt_evaluar.py
================================================================================
Evaluacion de los controladores (referencias, optimizados y cotas) sobre conjuntos de PRUEBA que no se usaron para
entrenar, con la misma estadistica del resto del proyecto (estadistica.py):

  oficial      los 16 pares de caudales de la Tabla VIII x semillas 0..19, 7200 s (numeros aleatorios comunes)
  no_vistos    64 pares sorteados (caudales y semillas 500000+ distintos de los de validacion), 7200 s
  variable     demanda que cambia en el tiempo (perfil por tramos de 600 s, factor 0.4 a 1.6 sobre un caudal base)
  saturado     caudales cerca de la saturacion (suma de 3000 a 3300 veh/h)

El retardo es el medio por vehiculo CON residuo (toda la espera hasta el horizonte). Para cada controlador y cada par
de caudales: media y desviacion estandar de las 20 replicas, IC 95 % (t de Student), y Wilcoxon pareado frente a cada
referencia con correccion de Holm sobre los 16 pares.
"""
import numpy as np

import estadistica as est
import traffic_model as tm
from opt_entrenar import construir, escenarios_oficiales, escenarios_validacion, H_PRUEBA
from sim_batch import BatchSim, make_arrivals


def perfil_variable(R, N, seed, tramo=600, lo=0.4, hi=1.6):
    """Factor de demanda (R, N), constante por tramos de 'tramo' s, uniforme en [lo, hi], distinto en cada escenario."""
    rng = np.random.default_rng(seed)
    n_t = int(np.ceil(N / tramo))
    f = rng.uniform(lo, hi, size=(R, n_t))
    return np.repeat(f, tramo, axis=1)[:, :N]


def escenarios_variables(n=64, H=H_PRUEBA, seed=7):
    rng = np.random.default_rng(seed)
    base = np.column_stack([rng.uniform(300, 1200, n), rng.uniform(300, 1200, n)])
    perfil = perfil_variable(n, H + 60, seed + 1)
    return base, construir(base, 300000 + np.arange(n), H, perfil=perfil)


def escenarios_saturados(n=32, H=H_PRUEBA, seed=9):
    rng = np.random.default_rng(seed)
    fl = []
    while len(fl) < n:
        s = rng.uniform(3000, 3300)
        a = rng.uniform(0.2, 0.8) * s
        fl.append((a, s - a))
    fl = np.array(fl)
    return fl, construir(fl, 400000 + np.arange(n), H)


def resumen_por_par(delay, flujos, reps=20):
    """Media, sd e IC95 por par de caudales (los escenarios vienen agrupados por par: reps consecutivos)."""
    out = []
    for i in range(0, len(delay), reps):
        x = delay[i:i + reps]
        m, sd, lo, hi = est.ic95(x)
        out.append(dict(ns=float(flujos[i][0]), ew=float(flujos[i][1]), media=m, sd=sd, ic_lo=lo, ic_hi=hi))
    return out


def comparar(delay_a, delay_b, reps=20):
    """Wilcoxon pareado por par de caudales (a vs b) con Holm. Devuelve mejora % media y conteos."""
    ps, difs = [], []
    n_par = len(delay_a) // reps
    for i in range(n_par):
        x, y = delay_a[i * reps:(i + 1) * reps], delay_b[i * reps:(i + 1) * reps]
        ps.append(est.wilcoxon(x, y)["p"])
        difs.append((y.mean() - x.mean()) / y.mean() * 100.0)      # % que a mejora a b
    p_holm = est.holm(ps)
    return dict(mejora_media_pct=float(np.mean(difs)), mejora_por_par=[float(d) for d in difs],
                p_holm=[float(p) for p in p_holm],
                mejor_signif=int(sum(1 for d, p in zip(difs, p_holm) if d > 0 and p < 0.05)),
                peor_signif=int(sum(1 for d, p in zip(difs, p_holm) if d < 0 and p < 0.05)),
                n_par=n_par)
