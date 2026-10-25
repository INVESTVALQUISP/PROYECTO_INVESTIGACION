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

import numpy as np

import paper_data as pdta
import traffic_model as tm


def deterministic_arrivals(l1, l2, seed, duration):
    rng = np.random.default_rng(seed)
    out = []
    for lam in (l1, l2):
        c = np.floor(np.arange(duration + 61) * lam + rng.random())
        out.append((c[1:] > c[:-1]).astype(int))
    return out[0], out[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=10)
    ap.add_argument("--duration", type=int, default=7200)
    args = ap.parse_args()
    bern = tm._make_arrivals
    rows = []
    for ns, ew in tm.COMBINATIONS:
        l1, l2 = ns / 3600, ew / 3600
        r = {"ns": ns, "ew": ew}
        for name, gen in (("bernoulli", bern), ("fijas", deterministic_arrivals)):
            tm._make_arrivals = gen
            r[f"fixed_{name}"] = float(np.mean([tm.simulate_fixed_cycle(l1, l2, k, args.duration)
                                                for k in range(args.reps)]))
            r[f"fuzzy_{name}"] = float(np.mean([tm.simulate_fuzzy(l1, l2, 100000 + k, args.duration,
                                                                  **tm.CALIBRADA) for k in range(args.reps)]))
        rows.append(r)
        print(ns, ew, {k: round(v, 2) for k, v in r.items() if k not in ("ns", "ew")}, flush=True)
    tm._make_arrivals = bern
    p1 = np.array([pdta.TABLE_I[(r["ns"], r["ew"])][0] for r in rows])
    p8 = np.array([pdta.TABLE_VIII[(r["ns"], r["ew"])][1] for r in rows])
    err = lambda key, ref: float(np.mean([abs(r[key] - p) / p for r, p in zip(rows, ref)]) * 100)
    out = dict(reps=args.reps, duration=args.duration, rows=rows,
               err_table_I={"bernoulli": err("fixed_bernoulli", p1), "fijas": err("fixed_fijas", p1)},
               err_table_VIII={"bernoulli": err("fuzzy_bernoulli", p8), "fijas": err("fuzzy_fijas", p8)})
    json.dump(out, open("resultados/llegadas_fijas_vs_aleatorias.json", "w"), indent=1)
    print(out["err_table_I"], out["err_table_VIII"])


if __name__ == "__main__":
    main()
