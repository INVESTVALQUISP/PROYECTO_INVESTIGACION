"""
opt_afinar_referencias.py
================================================================================
Afina por busqueda en rejilla los controladores de referencia con los MISMOS escenarios de entrenamiento que los
controladores aprendidos (64 pares sorteados, semillas 100000+, 3600 s, suma de caudales hasta 3300 veh/h) y el mismo
rango de verde minimo (3 a 7 s) y maximo (57, 80 y 90 s). El criterio es el de la Ec. del objetivo del articulo: media del
retardo dividido por el del actuado original (hueco 3 s, verde de 7 a 57 s) en el mismo escenario (1 = igual al actuado).

  actuado         hueco 1-3 s x verde minimo 3-7 s x maximo 57/80/90 s            -> resultados/opt/actuado_afinado.json
  actuado_vista   actuado con la vista adelante de 10 s (opt_controladores.ActuatedPreview): ventana de llegadas esperadas
                  en el brazo con verde 1-10 s y, opcionalmente, en el brazo en rojo (0, 3 o 6 s)
                                                                                    -> resultados/opt/actuado_vista_afinado.json
  maxpressure     margen 0-16 veh x verde minimo 3-7 s x maximo 57/80/90 s         -> resultados/opt/maxpressure_afinado.json

Por omision solo recalcula y COMPARA con lo guardado (no sobreescribe), salvo actuado_vista, que se escribe si no existe.
Con --escribir sobreescribe el archivo de la referencia pedida.
Uso:  python opt_afinar_referencias.py [--que actuado actuado_vista maxpressure] [--escribir]
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import argparse
import itertools
import json
import os

import numpy as np

from opt_controladores import Actuated, ActuatedPreview, MaxPressure
from opt_entrenar import escenarios_entrenamiento, H_ENTRENA
from sim_batch import BatchSim

OUT = "resultados/opt"
MINS = (3, 4, 5, 6, 7)
MAXS = (57, 80, 90)


def _ratio(arr, ctrl, mg, base):
    return float(np.mean(BatchSim(arr, max_green=mg).run(ctrl)["delay"] / base))


def rejillas(que):
    if que == "actuado":
        return [((g, m, x), dict(gap=g, min_green=m, max_green=x), (lambda g=g, m=m: Actuated(m, g)))
                for g, m, x in itertools.product((1, 2, 3), MINS, MAXS)]
    if que == "actuado_vista":
        return [((g, gr, m, x), dict(gap=g, gap_rojo=gr, min_green=m, max_green=x), (lambda g=g, gr=gr, m=m: ActuatedPreview(m, g, gr)))
                for g, gr, m, x in itertools.product((1, 2, 3, 4, 5, 6, 8, 10), (0, 3, 6), MINS, MAXS)]
    if que == "maxpressure":
        return [((mg, m, x), dict(margen=mg, min_green=m, max_green=x), (lambda mg=mg, m=m: MaxPressure(m, mg)))
                for mg, m, x in itertools.product((0, 1, 2, 3, 5, 8, 12, 16), (3, 4, 5, 7), MAXS)]
    raise ValueError(que)


def afinar(que, arr, base):
    filas = []
    for clave, par, mk in rejillas(que):
        filas.append((_ratio(arr, mk(), par["max_green"], base), par))
    filas.sort(key=lambda f: f[0])
    return filas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--que", nargs="+", default=["actuado", "actuado_vista", "maxpressure"])
    ap.add_argument("--escribir", action="store_true")
    args = ap.parse_args()
    fl, arr = escenarios_entrenamiento(64, H_ENTRENA, seed=1, suma_max=3300)
    base = BatchSim(arr, max_green=57).run(Actuated(7, 3))["delay"]
    for que in args.que:
        filas = afinar(que, arr, base)
        mejor = dict(filas[0][1], ratio=filas[0][0])
        ruta = f"{OUT}/{que}_afinado.json" if que != "actuado_vista" else f"{OUT}/actuado_vista_afinado.json"
        print(f"{que}: mejor {mejor}")
        if os.path.exists(ruta) and not args.escribir:
            ant = json.load(open(ruta))["mejor"]
            iguales = all(abs(ant[k] - mejor[k]) < 1e-9 for k in mejor)
            print(f"  guardado {ant} -> {'REPRODUCE lo guardado' if iguales else 'DIFIERE de lo guardado'}")
            continue
        nota = {"actuado": "rejilla: hueco 1-3, verde minimo 3-7, maximo 57/80/90 (mismo limite de 90 s que los controladores entrenados)",
                "actuado_vista": "rejilla: ventana de llegadas esperadas en verde 1-6, 8 y 10 s, en rojo 0, 3 y 6 s, verde minimo 3-7, maximo 57/80/90; actuado con la misma vista adelante de 10 s que Pappis y Mamdani y FLC-O",
                "maxpressure": "rejilla: margen 0-16, verde minimo 3-7, maximo 57/80/90"}[que]
        json.dump({"mejor": mejor, "nota": nota, "todos": [[f[0]] + [f[1][k] for k in f[1] if k != "max_green"] + [f[1]["max_green"]] for f in filas]},
                  open(ruta, "w"))
        print("  escrito", ruta)


if __name__ == "__main__":
    main()
