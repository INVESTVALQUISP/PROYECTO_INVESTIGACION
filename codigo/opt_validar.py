"""
opt_validar.py
================================================================================
Evalua modelos entrenados en el conjunto de VALIDACION (64 pares sorteados, semillas 200000+, 7200 s) y los ordena por
retardo medio normalizado por el del actuado afinado (1.0 = igual). Sirve para elegir entre variantes SIN mirar el
conjunto de prueba.
Uso:  python opt_validar.py flcopt_g5 flcopt_g4 flcopt_g3 [--suma-max 3300]
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import argparse

import numpy as np

from opt_entrenar import escenarios_validacion, actuado_afinado
from opt_evaluacion_final import cargar_modelos, construir_modelo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("modelos", nargs="+")
    ap.add_argument("--suma-max", type=float, default=3300)
    args = ap.parse_args()
    fl, arr = escenarios_validacion(64, suma_max=args.suma_max)
    ref = actuado_afinado(arr)["delay"]
    todos = cargar_modelos()
    filas = []
    for nombre in args.modelos:
        mk, ctrl = construir_modelo(todos[nombre])
        r = mk(arr).run(ctrl)
        filas.append((float(np.mean(r["delay"] / ref)), float(np.mean(r["delay"])), nombre))
    for ratio, d, n in sorted(filas):
        print(f"{n:28s} validacion/actuado afinado = {ratio:.4f}   retardo medio {d:.2f} s/veh")


if __name__ == "__main__":
    main()
