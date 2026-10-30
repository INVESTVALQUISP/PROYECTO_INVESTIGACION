"""
test_opt.py
================================================================================
Pruebas de los componentes de la optimizacion (opt_*.py):
  1. CMA-ES minimiza una esfera de 10 dimensiones y la funcion de Rosenbrock de 5 dimensiones;
  2. la particion de Ruspini de FLC-O suma 1 en todo punto y vale (1,0,0) / (0,0,1) fuera de los nudos;
  3. la programacion dinamica concuerda con la simulacion de su propia politica (caudales 720 / 1440 veh/h, menos de 2 %);
  4. FLC-O y la politica neuronal son deterministas (misma entrada, mismo retardo) y respetan el verde minimo y maximo;
  5. PappisAfinado con los parametros del paper reproduce a PappisFuzzy y cambia al modificar un parametro.
Uso:  python test_opt.py
"""
import sys

import numpy as np

import opt_es
import opt_flc2
from opt_controladores import PappisFuzzy
from opt_flc import PappisAfinado, THETA_PAPER
from opt_mdp import resolver, PoliticaMDP
from opt_politicas import PoliticaStop, n_parametros
from sim_batch import make_arrivals, BatchSim

fails = 0


def check(name, ok, detail=""):
    global fails
    print(f"  [{'OK' if ok else 'FALLO'}] {name} {detail}")
    fails += 0 if ok else 1


print("CMA-ES")
x, f, _ = opt_es.minimize(lambda v: float(np.sum((v - 1.5) ** 2)), np.zeros(10), 0.5, 120, workers=1, seed=1)
check("esfera de 10 dimensiones", f < 1e-3, f"(f = {f:.1e})")
ros = lambda v: float(np.sum(100.0 * (v[1:] - v[:-1] ** 2) ** 2 + (1 - v[:-1]) ** 2))
x, f, _ = opt_es.minimize(ros, np.zeros(5), 0.5, 400, workers=1, seed=1)
check("Rosenbrock de 5 dimensiones", f < 1e-2, f"(f = {f:.1e})")

print("Particion de Ruspini de FLC-O")
xs = np.linspace(-1, 100, 2001)
mu = opt_flc2.ruspini(xs, (2.0, 5.0, 9.0))
check("suma 1 en todo punto", np.allclose(mu.sum(axis=1), 1.0))
check("(1,0,0) antes de k1 y (0,0,1) desde k3", np.allclose(mu[xs <= 2.0], [1, 0, 0]) and np.allclose(mu[xs >= 9.0], [0, 0, 1]))
check("pico de 'medio' en k2", abs(float(opt_flc2.ruspini(np.array([5.0]), (2.0, 5.0, 9.0))[0, 1]) - 1.0) < 1e-12)

print("Programacion dinamica frente a simulacion")
p1, p2 = 720 / 3600, 1440 / 3600
pol, g, it = resolver(p1, p2, qmax=50, tol=1e-6)
arr = make_arrivals(p1, p2, np.arange(16) + 7000, 12000)
r = BatchSim(arr, max_green=None).run(PoliticaMDP(np.broadcast_to(pol[None], (16,) + pol.shape)))
pred = g / (p1 + p2)
check("retardo predicho (ley de Little) = retardo simulado", abs(r["delay"].mean() - pred) / pred < 0.02,
      f"(predicho {pred:.2f}, simulado {r['delay'].mean():.2f} s/veh)")

print("Controladores entrenables")
arr = make_arrivals([0.2, 0.3], [0.5, 0.2], [11, 12], 1800)
flc = opt_flc2.FuzzyOpt(opt_flc2.THETA0_OPT, True, 5)
r1 = BatchSim(arr, max_green=90).run(flc, trace=True)
r2 = BatchSim(arr, max_green=90).run(opt_flc2.FuzzyOpt(opt_flc2.THETA0_OPT, True, 5))
check("FLC-O es determinista", np.array_equal(r1["D"], r2["D"]))
# duracion de cada verde: entre gmin y max_green
ph = r1["trace_phase"]
ok = True
for i in range(ph.shape[0]):
    runs, cur, n = [], ph[i, 0], 1
    for v in ph[i, 1:]:
        if v == cur:
            n += 1
        else:
            runs.append((cur, n)); cur, n = v, 1
    for fase, n in runs[1:]:             # se omite el primer verde (empieza en t = 0) y el ultimo (puede cortarse por el horizonte)
        if fase < 2 and not (5 <= n <= 90):
            ok = False
check("todo verde dura entre g_min = 5 y g_max = 90 s", ok)
th = np.random.default_rng(0).normal(0, 0.2, n_parametros(8))
a = BatchSim(arr, max_green=57).run(PoliticaStop(th, 8, True, 7))
b = BatchSim(arr, max_green=57).run(PoliticaStop(th, 8, True, 7))
check("la politica neuronal es determinista", np.array_equal(a["D"], b["D"]))

print("Pappis y Mamdani afinado")
arr = make_arrivals([0.2, 0.3], [0.5, 0.2], [21, 22], 1800)
base = BatchSim(arr).run(PappisFuzzy())
check("con los parametros del paper reproduce a PappisFuzzy", np.array_equal(base["D"], BatchSim(arr).run(PappisAfinado(THETA_PAPER))["D"]))
th = THETA_PAPER.copy()
th[0] = 0.8
check("cambiar el umbral cambia el resultado", not np.array_equal(base["D"], BatchSim(arr).run(PappisAfinado(th))["D"]))

print("TODO OK" if fails == 0 else f"{fails} FALLOS")
sys.exit(1 if fails else 0)
