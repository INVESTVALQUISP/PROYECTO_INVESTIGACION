"""
comparadores.py
================================================================================
Comparacion de controladores con el MISMO protocolo de 16 flujos y NUMEROS ALEATORIOS COMUNES (CRN): para cada
replica k todos los controladores ven exactamente las mismas llegadas (semilla k, k = 0..19), de modo que las
diferencias se analizan como pares.

Controladores:
  fijo           ciclo fijo con ajustes de Webster y verdes redondeados al entero (linea base oficial de la replica)
  fijo_sin_red   ciclo fijo con los verdes SIN redondear (redondeo acumulado: el promedio de cada verde es exacto)
  actuado        controlador accionado por detector (extension por hueco, 3 s), verde de 7 a 57 s (comparador adicional)
  difuso         controlador de Pappis y Mamdani con sus 25 reglas, lectura calibrada y decision por maximo con umbral
  difuso_centroide  las mismas 25 reglas y lectura, pero con defuzzificacion por centroide (variante, no es la del paper)

Para cada flujo: media, desviacion estandar de la muestra, IC 95 %; prueba de rangos con signo de Wilcoxon por pares
(con correccion de Holm entre los 16 flujos). Entre flujos: prueba de Friedman.

Salida: resultados/comparadores.json     Uso:  python codigo/comparadores.py [--reps 20]
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import argparse
import json
import math
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

import estadistica as es
import traffic_model as tm

DUR = 7200
CONTROLADORES = {
    "fijo": (tm.simulate_fixed_cycle, {}),
    "fijo_sin_red": (tm.simulate_fixed_cycle, dict(rounding="dither")),
    "actuado": (tm.simulate_actuated, {}),
    "difuso": (tm.simulate_fuzzy, dict(tm.CALIBRADA)),
    "difuso_centroide": (tm.simulate_fuzzy, dict(tm.CALIBRADA, defuzz="centroid")),
}


def _celda(args):
    ns, ew, reps = args
    l1, l2 = ns / 3600.0, ew / 3600.0
    return dict(ns=ns, ew=ew, **{k: [float(fn(l1, l2, r, duration=DUR, **kw)) for r in range(reps)]
                                 for k, (fn, kw) in CONTROLADORES.items()})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=20)
    args = ap.parse_args()
    t0 = time.time()
    with ProcessPoolExecutor() as ex:
        cells = list(ex.map(_celda, [(a, b, args.reps) for a, b in tm.COMBINATIONS]))
    rows = []
    for c in cells:
        r = dict(ns=c["ns"], ew=c["ew"])
        for k in CONTROLADORES:
            m, sd, lo, hi = es.ic95(c[k])
            r[k] = dict(mean=m, sd=sd, lo=lo, hi=hi, values=c[k])
        rows.append(r)
    pares = {"difuso_vs_fijo": ("difuso", "fijo"), "difuso_vs_actuado": ("difuso", "actuado"),
             "fijo_sin_red_vs_fijo": ("fijo_sin_red", "fijo"), "centroide_vs_difuso": ("difuso_centroide", "difuso")}
    tests = {}
    for name, (a, b) in pares.items():
        ps = [es.wilcoxon(r[a]["values"], r[b]["values"]) for r in rows]
        adj = es.holm([p["p"] for p in ps])
        tests[name] = [dict(p=p["p"], p_holm=h, metodo=p["metodo"]) for p, h in zip(ps, adj)]
        for r, t in zip(rows, tests[name]):
            r.setdefault("tests", {})[name] = t
    M = np.array([[r[k]["mean"] for k in CONTROLADORES] for r in rows])
    resumen = dict(
        medias=dict(zip(CONTROLADORES, M.mean(axis=0).tolist())),
        friedman_entre_flujos=es.friedman(M),
        mejor_que_fijo={k: int((M[:, i] < M[:, 0]).sum()) for i, k in enumerate(CONTROLADORES)},
        significativo_holm_difuso_vs_fijo=int(sum(1 for t in tests["difuso_vs_fijo"] if t["p_holm"] < 0.05 and True)),
        significativo_holm_difuso_vs_actuado=int(sum(1 for t in tests["difuso_vs_actuado"] if t["p_holm"] < 0.05)),
        wilcoxon_entre_flujos={n: es.wilcoxon(M[:, list(CONTROLADORES).index(a)], M[:, list(CONTROLADORES).index(b)])
                               for n, (a, b) in pares.items()})
    # ajustes de Webster (sin redondear y redondeados) de cada par de flujos
    webster = []
    for ns, ew in tm.COMBINATIONS:
        C0, g1, g2 = tm.webster_optimum(ns / 3600.0, ew / 3600.0)
        r1, r2 = math.floor(g1 + 0.5), math.floor(g2 + 0.5)
        webster.append(dict(ns=ns, ew=ew, C0=C0, g1=g1, g2=g2, r1=r1, r2=r2, Ceff=r1 + r2 + 10))
    out = dict(reps=args.reps, duration=DUR, semillas="k = 0..%d para todos los controladores (CRN)" % (args.reps - 1),
               rows=rows, webster=webster, resumen=resumen, segundos=time.time() - t0)
    json.dump(out, open("resultados/comparadores.json", "w"), indent=1)
    print(f"{'N-S':>5} {'E-W':>5} | " + " ".join(f"{k:>16}" for k in CONTROLADORES))
    for r in rows:
        print(f"{r['ns']:5d} {r['ew']:5d} | " + " ".join(f"{r[k]['mean']:16.2f}" for k in CONTROLADORES))
    print({k: round(v, 2) for k, v in resumen["medias"].items()}, resumen["mejor_que_fijo"],
          "Friedman p =", resumen["friedman_entre_flujos"]["p"])
    print(f"{time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
