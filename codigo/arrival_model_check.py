"""
arrival_model_check.py
================================================================================
Comprueba que el modelo de llegadas ALEATORIAS (Bernoulli por segundo, pag. 2 del
paper) es el que reproduce la Tabla I, frente a una alternativa de llegadas FIJAS
(un vehiculo cada 1/lambda segundos, con desfase aleatorio de la rejilla).

El paper dice: "For each successive time unit (1 s) a pseudorandom number is
generated and compared to some fixed quantity, which is equal to the mean rate of
arrival". Este script cuantifica la diferencia.

Uso:  python arrival_model_check.py [--reps 10] [--duration 7200]
      -> resultados/llegadas_fijas_vs_aleatorias.json
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import argparse
import json
from concurrent.futures import ProcessPoolExecutor

import numpy as np

import estadistica as es
import paper_data as pdta
import traffic_model as tm


def deterministic_arrivals(l1, l2, seed, duration):
    rng = np.random.default_rng(seed)
    out = []
    for lam in (l1, l2):
        c = np.floor(np.arange(duration + 61) * lam + rng.random())
        out.append((c[1:] > c[:-1]).astype(int))
    return out[0], out[1]


def _celda(args):
    ns, ew, reps, dur = args
    l1, l2 = ns / 3600, ew / 3600
    bern = tm._make_arrivals
    r = {"ns": ns, "ew": ew}
    try:
        for name, gen in (("bernoulli", bern), ("fijas", deterministic_arrivals)):
            tm._make_arrivals = gen
            r[f"fixed_{name}_reps"] = [float(tm.simulate_fixed_cycle(l1, l2, k, dur)) for k in range(reps)]
            r[f"fuzzy_{name}_reps"] = [float(tm.simulate_fuzzy(l1, l2, k, dur, **tm.CALIBRADA)) for k in range(reps)]
    finally:
        tm._make_arrivals = bern
    for name in ("bernoulli", "fijas"):
        r[f"fixed_{name}"] = float(np.mean(r[f"fixed_{name}_reps"]))
        r[f"fuzzy_{name}"] = float(np.mean(r[f"fuzzy_{name}_reps"]))
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--duration", type=int, default=7200)
    args = ap.parse_args()
    with ProcessPoolExecutor() as ex:
        rows = list(ex.map(_celda, [(ns, ew, args.reps, args.duration) for ns, ew in tm.COMBINATIONS]))
    p1 = np.array([pdta.TABLE_I[(r["ns"], r["ew"])][0] for r in rows])
    p8 = np.array([pdta.TABLE_VIII[(r["ns"], r["ew"])][1] for r in rows])

    def resumen(key, ref):
        """Error relativo medio (%) de las medias por celda y, por replica, media y desviacion estandar (n-1)."""
        cell = np.array([r[key] for r in rows])
        e_cell = np.abs(cell - ref) / ref * 100
        reps = np.array([r[key + "_reps"] for r in rows])                       # (16, reps)
        e_rep = (np.abs(reps - ref[:, None]) / ref[:, None] * 100).mean(axis=0)
        m, sd, lo, hi = es.ic95(e_rep)
        return dict(media=float(e_cell.mean()), sd=sd, lo=lo, hi=hi, e_cell=e_cell.tolist())

    out = dict(reps=args.reps, duration=args.duration, rows=rows, semillas="k = 0..%d (CRN)" % (args.reps - 1))
    out["tabla_I"] = {n: resumen(f"fixed_{n}", p1) for n in ("bernoulli", "fijas")}
    out["tabla_VIII"] = {n: resumen(f"fuzzy_{n}", p8) for n in ("bernoulli", "fijas")}
    out["err_table_I"] = {n: out["tabla_I"][n]["media"] for n in ("bernoulli", "fijas")}
    out["err_table_VIII"] = {n: out["tabla_VIII"][n]["media"] for n in ("bernoulli", "fijas")}
    out["wilcoxon_celdas"] = {
        "tabla_I": es.wilcoxon(out["tabla_I"]["bernoulli"]["e_cell"], out["tabla_I"]["fijas"]["e_cell"]),
        "tabla_VIII": es.wilcoxon(out["tabla_VIII"]["bernoulli"]["e_cell"], out["tabla_VIII"]["fijas"]["e_cell"])}
    json.dump(out, open("resultados/llegadas_fijas_vs_aleatorias.json", "w"), indent=1)
    for t in ("tabla_I", "tabla_VIII"):
        print(t, {n: (round(v["media"], 2), round(v["sd"], 2)) for n, v in out[t].items()}, "Wilcoxon p =", round(out["wilcoxon_celdas"][t]["p"], 5))


if __name__ == "__main__":
    main()
