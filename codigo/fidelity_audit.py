"""
fidelity_audit.py
================================================================================
Auditoria de INTERPRETACION. Las reglas, los conjuntos, los operadores mt/lt, la
regla de decision y los tiempos de intervencion son datos del paper y estan
fijos. Lo que el paper NO precisa es como su programa obtenia A y Q desde el
estado de la simulacion. Este script prueba las lecturas posibles, SIN tocar las
reglas, y las compara con la Tabla VIII.

  A  ('a_mode'):
     arrivals -> A = arribos acumulados en la ventana (ejemplo de la pag. 7)
     crossing -> A = vehiculos que cruzan el punto critico en e s, limitados por
                 el flujo de saturacion (incluye la cola del brazo en verde)
  Q  ('q_mode'): en que valor se evalua la membresia de Q
     predicted -> cola + arribos del brazo en rojo durante e s (ejemplo pag. 7)
     current   -> la cola en el instante de la intervencion
  Q  ('queue_source'): que cuenta como cola del brazo en rojo
     total         -> todos los vehiculos esperando (incluye los que quedaron sin
                      despachar de su verde anterior y los llegados en el tiempo perdido)
     green_arrivals-> solo los llegados desde que empezo el verde actual

Uso:  python fidelity_audit.py [--reps 10] [--duration 7200]
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import argparse
import itertools
import json

import numpy as np

import paper_data as pdta
import traffic_model as tm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=10)
    ap.add_argument("--duration", type=int, default=7200)
    ap.add_argument("--out", default="resultados/fidelity_audit.json")
    args = ap.parse_args()
    pap = np.array([pdta.TABLE_VIII[c][1] for c in tm.COMBINATIONS])
    fixed = np.array([tm.average(tm.simulate_fixed_cycle, ns / 3600, ew / 3600, args.reps,
                                 args.duration, 0)[0] for ns, ew in tm.COMBINATIONS])
    results = []
    print(f"{args.reps} replicas x {args.duration} s | referencia: Tabla VIII (difuso)\n")
    print(f"{'A':9s} {'Q evaluada':10s} {'cola Q':15s} | {'error medio':>11} {'maximo':>8} {'mejor que fijo':>15}")
    for a_mode, q_mode, qsrc in itertools.product(["arrivals", "crossing"], ["predicted", "current"],
                                                  ["total", "green_arrivals"]):
        d = np.array([tm.average(tm.simulate_fuzzy, ns / 3600, ew / 3600, args.reps, args.duration,
                                 100000, a_mode=a_mode, q_mode=q_mode, queue_source=qsrc)[0]
                      for ns, ew in tm.COMBINATIONS])
        err = 100 * np.abs(d - pap) / pap
        wins = int((d < fixed).sum())
        results.append(dict(a_mode=a_mode, q_mode=q_mode, queue_source=qsrc, delays=d.tolist(),
                            mean_err=float(err.mean()), max_err=float(err.max()), wins=wins))
        print(f"{a_mode:9s} {q_mode:10s} {qsrc:15s} | {err.mean():10.1f}% {err.max():7.1f}% {wins:12d}/16", flush=True)
    json.dump(dict(reps=args.reps, duration=args.duration, fixed=fixed.tolist(), paper=pap.tolist(),
                   variants=results), open(args.out, "w"), indent=1)
    print(f"\nGuardado en {args.out}")


if __name__ == "__main__":
    main()
