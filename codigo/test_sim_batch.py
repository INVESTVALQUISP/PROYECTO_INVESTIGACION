"""
test_sim_batch.py
================================================================================
El simulador VECTORIZADO (sim_batch.py, R escenarios a la vez) da exactamente los mismos retardos que el
simulador de referencia (traffic_model.py), escenario por escenario y con las dos convenciones de retardo:
  * con residuo     (espera de todos los vehiculos hasta el horizonte)  -> traffic_model.simulate_*(include_residual=True)
  * solo servidos   (convencion del articulo original)                  -> include_residual=False
para los cinco controladores de referencia (ciclo fijo con redondeo al entero mas proximo y con reparto exacto,
actuado por detector, difuso de Pappis y Mamdani en sus dos lecturas), y que PappisAfinado con los parametros
del paper reproduce a PappisFuzzy. Ademas: la contabilidad D = suma por segundo de las colas y la conservacion
de vehiculos (llegadas = servidos + cola final).
Uso:  python test_sim_batch.py
"""
import sys

import numpy as np

import traffic_model as tm
from opt_controladores import FixedCycle, Actuated, PappisFuzzy
from opt_flc import PappisAfinado, THETA_PAPER
from sim_batch import make_arrivals, BatchSim

fails = 0


def check(name, ok, detail=""):
    global fails
    print(f"  [{'OK' if ok else 'FALLO'}] {name} {detail}")
    fails += 0 if ok else 1


flows = [(360, 360), (360, 2160), (1080, 1800), (1440, 1440)]
seeds = [0, 1]
H = 2400
lam_ns = np.array([a / 3600 for a, b in flows for s in seeds])
lam_ew = np.array([b / 3600 for a, b in flows for s in seeds])
sd = np.array([s for a, b in flows for s in seeds])
arr = make_arrivals(lam_ns, lam_ew, sd, H)


def ref(fn, **kw):
    a = [fn(x, y, s, duration=H, include_residual=False, **kw) for x, y, s in zip(lam_ns, lam_ew, sd)]
    b = [fn(x, y, s, duration=H, include_residual=True, **kw) for x, y, s in zip(lam_ns, lam_ew, sd)]
    return np.array(a), np.array(b)


print("Simulador vectorizado == simulador de referencia (8 escenarios de 2400 s)")
casos = [
    ("ciclo fijo (entero mas proximo)", BatchSim(arr, max_green=None), FixedCycle(lam_ns, lam_ew), tm.simulate_fixed_cycle, {}),
    ("ciclo fijo (reparto exacto)", BatchSim(arr, max_green=None), FixedCycle(lam_ns, lam_ew, "dither"), tm.simulate_fixed_cycle, dict(rounding="dither")),
    ("actuado por detector", BatchSim(arr, max_green=57), Actuated(7, 3), tm.simulate_actuated, {}),
    ("Pappis y Mamdani, lectura calibrada", BatchSim(arr), PappisFuzzy(), tm.simulate_fuzzy, tm.CALIBRADA),
    ("Pappis y Mamdani, lectura literal", BatchSim(arr), PappisFuzzy("arrivals", "predicted", "total"), tm.simulate_fuzzy, tm.LITERAL),
    ("PappisAfinado(parametros del paper)", BatchSim(arr), PappisAfinado(THETA_PAPER), tm.simulate_fuzzy, tm.CALIBRADA),
]
for nombre, sim, ctrl, fn, kw in casos:
    res = sim.run(ctrl)
    a, b = ref(fn, **kw)
    check(nombre, np.allclose(res["delay_served"], a, rtol=0, atol=1e-9) and np.allclose(res["delay"], b, rtol=0, atol=1e-9),
          f"(dif max {max(np.abs(res['delay_served'] - a).max(), np.abs(res['delay'] - b).max()):.1e})")

print("Conservacion y contabilidad")
res = BatchSim(arr).run(PappisFuzzy())
n_llegadas = arr.n_arrivals
check("D = suma por segundo de las colas (D_ns + D_ew)", np.array_equal(res["D"], res["D_ns"] + res["D_ew"]))
check("el retardo con residuo es >= el de solo servidos", bool(np.all(res["delay"] >= res["delay_served"] - 1e-12)))
check("llegadas = suma acumulada de arr_ns y arr_ew en [0, H)", np.array_equal(n_llegadas, arr.arr_ns[:, :H].sum(1) + arr.arr_ew[:, :H].sum(1)))
check("mismos numeros aleatorios que traffic_model._make_arrivals",
      all(np.array_equal(arr.arr_ns[i, :H + 60], tm._make_arrivals(lam_ns[i], lam_ew[i], int(sd[i]), H)[0]) and
          np.array_equal(arr.arr_ew[i, :H + 60], tm._make_arrivals(lam_ns[i], lam_ew[i], int(sd[i]), H)[1]) for i in range(len(sd))))

print("TODO OK" if fails == 0 else f"{fails} FALLOS")
sys.exit(1 if fails else 0)
