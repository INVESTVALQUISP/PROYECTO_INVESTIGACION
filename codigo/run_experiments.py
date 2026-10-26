"""
run_experiments.py
================================================================================
Replica los resultados de Pappis & Mamdani (1977), IEEE SMC-7(10):
  * Tabla I   : validacion del modelo (ciclo fijo con ajustes optimos de Webster):
                simulacion vs. 'Model' del paper y formula de Webster vs. 'Formula'.
  * Tabla VIII: controlador difuso vs. linea base. En el paper la columna
                'vehicle-actuated' repite los valores de la Tabla I ('Model'),
                es decir, la simulacion de ciclo fijo optimo (pag. 3).

Protocolo oficial (por defecto): 20 replicas x 7200 s por combinacion, semillas 0..19 con numeros
aleatorios comunes (CRN): el ciclo fijo y el difuso ven las mismas llegadas en cada replica.

Uso:
  python run_experiments.py                       # oficial, ambas lecturas
  python run_experiments.py --config calibrada    # solo una
  python run_experiments.py --quick               # 5 x 3600 s (solo para probar)
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import argparse
import json
import time

import numpy as np

import paper_data as pdta
import traffic_model as tm

CONFIGS = {"literal": tm.LITERAL, "calibrada": tm.CALIBRADA}


def table_I(reps, duration):
    rows = []
    for ns, ew in tm.COMBINATIONS:
        lns, lew = ns / 3600.0, ew / 3600.0
        d_sim, sd = tm.average(tm.simulate_fixed_cycle, lns, lew, reps, duration, 0)
        rows.append(dict(ns=ns, ew=ew, sim=d_sim, sd=sd, formula=tm.webster_delay_formula(lns, lew)))
    return rows


def table_VIII(reps, duration, cfg):
    rows = tm.run_table(reps=reps, duration=duration, base_seed=0, **cfg)
    return [dict(ns=r[0], ew=r[1], fixed=r[2], fuzzy=r[3], improvement=r[4]) for r in rows]


def print_I(rows):
    print("\nTABLA I - Validacion del modelo (ciclo fijo, ajustes optimos de Webster)")
    print(f"{'N-S':>5} {'E-W':>5} | {'sim':>6} {'paper':>6} {'err%':>6} | {'formula':>7} {'paper':>6} {'err%':>6}")
    print("-" * 62)
    for r in rows:
        pm, pf = pdta.TABLE_I[(r["ns"], r["ew"])]
        print(f"{r['ns']:5d} {r['ew']:5d} | {r['sim']:6.2f} {pm:6.1f} {100*(r['sim']-pm)/pm:+6.1f} |"
              f" {r['formula']:7.2f} {pf:6.1f} {100*(r['formula']-pf)/pf:+6.1f}")
    e_sim = [abs(r["sim"] - pdta.TABLE_I[(r["ns"], r["ew"])][0]) / pdta.TABLE_I[(r["ns"], r["ew"])][0] for r in rows]
    e_for = [abs(r["formula"] - pdta.TABLE_I[(r["ns"], r["ew"])][1]) / pdta.TABLE_I[(r["ns"], r["ew"])][1] for r in rows]
    print(f"error relativo medio: simulacion {100*np.mean(e_sim):.1f}% | formula {100*np.mean(e_for):.1f}%")


def print_VIII(rows, name):
    print(f"\nTABLA VIII - difuso [{name}] vs. linea base (ciclo fijo optimo)")
    print(f"{'N-S':>5} {'E-W':>5} | {'fijo':>6} {'(paper)':>7} | {'difuso':>7} {'(paper)':>7} {'err%':>6} | {'mejora%':>7} {'(paper)':>7}")
    print("-" * 78)
    errs, wins = [], 0
    for r in rows:
        pf, pz = pdta.TABLE_VIII[(r["ns"], r["ew"])]
        err = 100 * (r["fuzzy"] - pz) / pz
        errs.append(abs(err))
        wins += r["fuzzy"] < r["fixed"]
        print(f"{r['ns']:5d} {r['ew']:5d} | {r['fixed']:6.2f} {pf:7.1f} | {r['fuzzy']:7.2f} {pz:7.1f} {err:+6.1f} |"
              f" {r['improvement']:+7.1f} {100*(pf-pz)/pf:+7.0f}")
    print(f"difuso mejor que el fijo en {wins}/16 celdas (paper: 16/16) | "
          f"error relativo vs paper: medio {np.mean(errs):.1f}%  maximo {np.max(errs):.1f}%")


def main():
    ap = argparse.ArgumentParser(description="Replica Pappis & Mamdani (1977).")
    ap.add_argument("--config", choices=["literal", "calibrada", "ambas"], default="ambas")
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--duration", type=int, default=7200)
    ap.add_argument("--quick", action="store_true", help="5 x 3600 s (NO es el protocolo oficial)")
    ap.add_argument("--out", default="resultados/resultados_oficiales.json")
    args = ap.parse_args()
    reps, duration = (5, 3600) if args.quick else (args.reps, args.duration)
    print(f"Protocolo: {reps} replicas x {duration} s{'  (RAPIDO, no oficial)' if args.quick else ''}")

    t0 = time.time()
    out = {"reps": reps, "duration": duration, "table_I": table_I(reps, duration), "table_VIII": {}}
    print_I(out["table_I"])
    names = ["literal", "calibrada"] if args.config == "ambas" else [args.config]
    for name in names:
        out["table_VIII"][name] = table_VIII(reps, duration, CONFIGS[name])
        print_VIII(out["table_VIII"][name], name)
    if not args.quick:
        with open(args.out, "w") as f:
            json.dump(out, f, indent=1)
        print(f"\nGuardado en {args.out}")
    print(f"Tiempo total: {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
