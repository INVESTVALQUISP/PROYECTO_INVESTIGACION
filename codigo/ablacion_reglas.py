"""
ablacion_reglas.py
================================================================================
Experimento EXPLORATORIO (no forma parte de la replica): que pasa si se usan menos
reglas. Mantiene las reglas del paper tal cual, solo quita algunas, y mide el retardo
con la lectura calibrada. Guarda resultados/ablacion_reglas.json.

Variantes: A) 25 reglas del paper; B) una sola base (la de 7 s) en las 5 intervenciones;
C) sin 'veryshort'; D) tres reglas por intervencion; E) solo extremos; F) solo 'veryshort'.

Uso:  python ablacion_reglas.py [--reps 10] [--duration 7200]
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import argparse
import json

import numpy as np

import fuzzy_logic as fl
import paper_data as pdta
import traffic_model as tm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=10)
    ap.add_argument("--duration", type=int, default=7200)
    args = ap.parse_args()
    R = fl.RULES

    def keep(labels):
        return {k: [r for r in v if r[0] in labels] for k, v in R.items()}

    variants = {
        "A": ("Paper: 5 reglas por intervención", 25, R),
        "B": ("Una sola base (la de 7 s) en las 5 intervenciones", 5, {k: R[7] for k in R}),
        "C": ("Sin la regla veryshort", 20, keep({"short", "medium", "long", "verylong"})),
        "D": ("Tres reglas (veryshort, medium, verylong)", 15, keep({"veryshort", "medium", "verylong"})),
        "E": ("Solo extremos (veryshort, verylong)", 10, keep({"veryshort", "verylong"})),
        "F": ("Solo veryshort", 5, keep({"veryshort"})),
    }
    res = json.load(open("resultados/resultados_oficiales.json"))["table_VIII"]["calibrada"]
    fixed = np.array([next(r["fixed"] for r in res if (r["ns"], r["ew"]) == c) for c in tm.COMBINATIONS])
    paper = np.array([pdta.TABLE_VIII[c][1] for c in tm.COMBINATIONS])
    out = dict(reps=args.reps, duration=args.duration, variants=[])
    for key, (name, n, rules) in variants.items():
        d = np.array([tm.average(tm.simulate_fuzzy, a / 3600, b / 3600, args.reps, args.duration, 100000,
                                 ruleset=rules, **tm.CALIBRADA)[0] for a, b in tm.COMBINATIONS])
        row = dict(key=key, name=name, n_rules=n, mean_dm=float(d.mean()), max_dm=float(d.max()),
                   err_vs_paper=float(np.mean(np.abs(d - paper) / paper) * 100), wins=int((d < fixed).sum()))
        out["variants"].append(row)
        print(f"{key}. {name:55s} reglas distintas={n:2d} d_m medio={row['mean_dm']:7.2f} mejora al fijo en {row['wins']}/16", flush=True)
    json.dump(out, open("resultados/ablacion_reglas.json", "w"), indent=1)


if __name__ == "__main__":
    main()
