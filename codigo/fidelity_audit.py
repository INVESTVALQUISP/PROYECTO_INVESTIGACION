"""
fidelity_audit.py
================================================================================
Auditoria de las lecturas de A y Q del controlador (las unicas variables que el paper no define):
las 8 combinaciones de
  A  ('a_mode'):
      arrivals  -> beta_e = arribos acumulados detectados en e s (literal del ejemplo, pag. 7)
      crossing  -> beta_e = min(e, cola_verde + arribos acumulados): cruces reales (flujo de saturacion 1 veh/s)
  Q  ('q_mode'): en que valor se evalua la membresia de Q
      predicted -> Q + arribos acumulados del brazo en rojo (ejemplo, pag. 7)
      current   -> la cola actual
  cola Q ('queue_source'):
      total          -> toda la cola del brazo en rojo
      green_arrivals -> solo los llegados desde que empezo el verde actual
Las 25 reglas del paper van fijas. Se comparan con la Tabla VIII del paper.

Protocolo: 20 replicas x 7200 s, semillas 0..19 con numeros aleatorios comunes (CRN: todas las lecturas y el ciclo
fijo ven las mismas llegadas en cada replica). Se informan la media y la desviacion estandar (muestra, n-1) del error
medio por replica y el numero de flujos en que el difuso mejora al fijo con significancia (Wilcoxon pareado + Holm).

Uso:  python fidelity_audit.py [--reps 20] [--duration 7200]
Salida: resultados/fidelity_audit.json
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import argparse
import itertools
import json
from concurrent.futures import ProcessPoolExecutor

import numpy as np

import estadistica as es
import paper_data as pdta
import traffic_model as tm


def _tarea(args):
    (a_mode, q_mode, qsrc), (ns, ew), reps, dur = args
    return [tm.simulate_fuzzy(ns / 3600, ew / 3600, k, dur, a_mode=a_mode, q_mode=q_mode, queue_source=qsrc)
            for k in range(reps)]


def _fijo(args):
    (ns, ew), reps, dur = args
    return [tm.simulate_fixed_cycle(ns / 3600, ew / 3600, k, dur) for k in range(reps)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--duration", type=int, default=7200)
    ap.add_argument("--out", default="resultados/fidelity_audit.json")
    args = ap.parse_args()
    cells = tm.COMBINATIONS
    pap = np.array([pdta.TABLE_VIII[c][1] for c in cells])
    variants = list(itertools.product(["arrivals", "crossing"], ["predicted", "current"], ["total", "green_arrivals"]))
    with ProcessPoolExecutor() as ex:
        fixed = np.array(list(ex.map(_fijo, [(c, args.reps, args.duration) for c in cells])))          # (16, reps)
        res = list(ex.map(_tarea, [(v, c, args.reps, args.duration) for v in variants for c in cells]))
    results = []
    print(f"{args.reps} replicas x {args.duration} s, CRN | referencia: Tabla VIII (difuso)\n")
    print(f"{'A':9s} {'Q evaluada':10s} {'cola Q':15s} | {'error medio':>11} {'DE':>6} {'maximo':>8} {'mejor que fijo':>15} {'signif.':>8}")
    for vi, (a_mode, q_mode, qsrc) in enumerate(variants):
        D = np.array(res[vi * len(cells):(vi + 1) * len(cells)])                                   # (16, reps)
        d = D.mean(axis=1)
        err = 100 * np.abs(d - pap) / pap
        err_rep = (100 * np.abs(D - pap[:, None]) / pap[:, None]).mean(axis=0)                     # error medio de cada replica
        m, sd, lo, hi = es.ic95(err_rep)
        wins = int((d < fixed.mean(axis=1)).sum())
        ps = [es.wilcoxon(D[c], fixed[c])["p"] for c in range(len(cells))]
        adj = es.holm(ps)
        wins_sig = int(sum(1 for c in range(len(cells)) if adj[c] < 0.05 and d[c] < fixed[c].mean()))
        results.append(dict(a_mode=a_mode, q_mode=q_mode, queue_source=qsrc, delays=d.tolist(),
                            mean_err=float(err.mean()), max_err=float(err.max()), wins=wins, wins_sig=wins_sig,
                            err_rep_mean=m, err_rep_sd=sd, err_rep_lo=lo, err_rep_hi=hi))
        print(f"{a_mode:9s} {q_mode:10s} {qsrc:15s} | {err.mean():10.1f}% {sd:6.1f} {err.max():7.1f}% {wins:12d}/16 {wins_sig:6d}/16", flush=True)
    json.dump(dict(reps=args.reps, duration=args.duration, semillas="k = 0..%d (CRN)" % (args.reps - 1),
                   fixed=fixed.mean(axis=1).tolist(), paper=pap.tolist(), variants=results),
              open(args.out, "w"), indent=1)
    print(f"\nGuardado en {args.out}")


if __name__ == "__main__":
    main()
