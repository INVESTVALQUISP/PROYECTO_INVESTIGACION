"""
ablacion_reglas.py
================================================================================
Experimento EXPLORATORIO (no forma parte de la replica): que pasa si se usan menos
reglas. Mantiene las reglas del paper tal cual, solo quita algunas, y mide el retardo
con la lectura calibrada. Guarda resultados/ablacion_reglas.json.

Variantes: A) 25 reglas del paper; B) una sola base (la de 7 s) en las 5 intervenciones;
C) sin 'veryshort'; D) tres reglas por intervencion; E) solo extremos; F) solo 'veryshort'.

Protocolo: 20 replicas x 7200 s, semillas 0..19 con numeros aleatorios comunes (CRN): todas las variantes y el ciclo
fijo ven las mismas llegadas en cada replica. Se informan media, desviacion estandar (n-1) e IC 95 % del retardo medio
de los 16 flujos por replica, la prueba de Friedman entre las 6 variantes y la prueba de Wilcoxon pareada de cada
variante frente a la de 25 reglas, con correccion de Holm.

Uso:  python ablacion_reglas.py [--reps 20] [--duration 7200]
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import argparse
import json
from concurrent.futures import ProcessPoolExecutor

import numpy as np

import estadistica as es
import fuzzy_logic as fl
import paper_data as pdta
import traffic_model as tm

R = fl.RULES


def _keep(labels):
    return {k: [r for r in v if r[0] in labels] for k, v in R.items()}


VARIANTES = {
    "A": ("Paper: 5 reglas por intervención", 25, R),
    "B": ("Una sola base (la de 7 s) en las 5 intervenciones", 5, {k: R[7] for k in R}),
    "C": ("Sin la regla veryshort", 20, _keep({"short", "medium", "long", "verylong"})),
    "D": ("Tres reglas (veryshort, medium, verylong)", 15, _keep({"veryshort", "medium", "verylong"})),
    "E": ("Solo extremos (veryshort, verylong)", 10, _keep({"veryshort", "verylong"})),
    "F": ("Solo veryshort", 5, _keep({"veryshort"})),
}


def _tarea(args):
    key, (ns, ew), reps, dur = args
    rules = VARIANTES[key][2]
    return [tm.simulate_fuzzy(ns / 3600, ew / 3600, k, dur, ruleset=rules, **tm.CALIBRADA) for k in range(reps)]


def _fijo(args):
    (ns, ew), reps, dur = args
    return [tm.simulate_fixed_cycle(ns / 3600, ew / 3600, k, dur) for k in range(reps)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--duration", type=int, default=7200)
    args = ap.parse_args()
    cells = tm.COMBINATIONS
    paper = np.array([pdta.TABLE_VIII[c][1] for c in cells])
    with ProcessPoolExecutor() as ex:
        fixed = np.array(list(ex.map(_fijo, [(c, args.reps, args.duration) for c in cells])))               # (16, reps)
        res = list(ex.map(_tarea, [(k, c, args.reps, args.duration) for k in VARIANTES for c in cells]))
    D = {k: np.array(res[i * len(cells):(i + 1) * len(cells)]) for i, k in enumerate(VARIANTES)}          # (16, reps)
    rep_mean = {k: D[k].mean(axis=0) for k in D}                                                          # d_m medio de los 16 flujos por replica
    out = dict(reps=args.reps, duration=args.duration, semillas="k = 0..%d (CRN)" % (args.reps - 1), variants=[])
    ps = {k: es.wilcoxon(rep_mean[k], rep_mean["A"]) for k in VARIANTES if k != "A"}
    adj = dict(zip(ps, es.holm([ps[k]["p"] for k in ps])))
    for key, (name, n, _) in VARIANTES.items():
        d = D[key].mean(axis=1)
        m, sd, lo, hi = es.ic95(rep_mean[key])
        row = dict(key=key, name=name, n_rules=n, mean_dm=float(d.mean()), max_dm=float(d.max()),
                   err_vs_paper=float(np.mean(np.abs(d - paper) / paper) * 100), wins=int((d < fixed.mean(axis=1)).sum()),
                   dm_rep_mean=m, dm_rep_sd=sd, dm_rep_lo=lo, dm_rep_hi=hi)
        if key != "A":
            row["wilcoxon_vs_A_p"] = ps[key]["p"]
            row["wilcoxon_vs_A_p_holm"] = adj[key]
            row["wilcoxon_vs_A_metodo"] = ps[key]["metodo"]
        out["variants"].append(row)
        print(f"{key}. {name:55s} reglas={n:2d} d_m={m:7.2f} ±{sd:6.2f}  mejora al fijo en {row['wins']}/16"
              + (f"  Wilcoxon vs A: p_Holm={adj[key]:.3g}" if key != "A" else ""), flush=True)
    M = np.array([rep_mean[k] for k in VARIANTES]).T                                                      # (reps, 6)
    out["friedman"] = es.friedman(M)
    out["friedman_variantes"] = list(VARIANTES)
    print("Friedman:", out["friedman"]["chi2"], out["friedman"]["p"])
    json.dump(out, open("resultados/ablacion_reglas.json", "w"), indent=1)


if __name__ == "__main__":
    main()
