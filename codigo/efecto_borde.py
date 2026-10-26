"""
efecto_borde.py
================================================================================
Cuantifica el efecto de borde del final del horizonte (observacion del revisor sobre las ecuaciones de cola y la descarga
simulada): el acumulador total_delay solo suma la espera de los vehiculos que ya salieron, mientras que total_arrivals
cuenta todas las llegadas; los vehiculos que siguen en cola en t = T no aportan su espera.

Se calcula d_m de dos maneras con las MISMAS llegadas (mismas semillas):
  (a) acumulador original: espera de los que salieron;
  (b) con la espera residual de los que siguen en cola al final (equivale a la suma por segundo de las colas).
para el ciclo fijo y el difuso (lecturas calibrada y literal), en las 16 combinaciones de caudal.

Salida: resultados/efecto_borde.json     Uso:  python codigo/efecto_borde.py [--reps 20]
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import argparse
import json
from concurrent.futures import ProcessPoolExecutor

import numpy as np

import traffic_model as tm

DUR = 7200


def _cell(args):
    ns, ew, reps = args
    lns, lew = ns / 3600.0, ew / 3600.0
    out = {}
    for name, fn, seed0, kw in (("fijo", tm.simulate_fixed_cycle, 0, {}),
                                ("calibrada", tm.simulate_fuzzy, 0, tm.CALIBRADA),
                                ("literal", tm.simulate_fuzzy, 0, tm.LITERAL)):
        a = [fn(lns, lew, seed0 + k, duration=DUR, **kw) for k in range(reps)]
        b = [fn(lns, lew, seed0 + k, duration=DUR, include_residual=True, **kw) for k in range(reps)]
        out[name] = dict(sin_residual=float(np.mean(a)), con_residual=float(np.mean(b)),
                         dif_rel_pct=float(100 * (np.mean(b) - np.mean(a)) / np.mean(a)))
    return dict(ns=ns, ew=ew, **out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=20)
    args = ap.parse_args()
    with ProcessPoolExecutor() as ex:
        rows = list(ex.map(_cell, [(ns, ew, args.reps) for ns, ew in tm.COMBINATIONS]))
    summ = {k: dict(max_pct=max(r[k]["dif_rel_pct"] for r in rows), media_pct=float(np.mean([r[k]["dif_rel_pct"] for r in rows])))
            for k in ("fijo", "calibrada", "literal")}
    json.dump(dict(reps=args.reps, duration=DUR, rows=rows, resumen=summ), open("resultados/efecto_borde.json", "w"), indent=1)
    print(f"{'N-S':>5} {'E-W':>5} | {'fijo %':>8} {'calibrada %':>12} {'literal %':>10}")
    for r in rows:
        print(f"{r['ns']:5d} {r['ew']:5d} | {r['fijo']['dif_rel_pct']:8.3f} {r['calibrada']['dif_rel_pct']:12.3f} {r['literal']['dif_rel_pct']:10.1f}")
    print(summ)
