"""
opt_entrenar_politica.py
================================================================================
Entrena con CMA-ES una politica de verde/cambio de fase (opt_politicas.PoliticaStop) para minimizar el retardo
medio normalizado (frente al actuado por detector) en caudales sorteados al azar.

Uso:
  python opt_entrenar_politica.py --hidden 8 --gens 200 --out resultados/opt/politica_mlp_preview.json
  python opt_entrenar_politica.py --hidden 8 --causal --gens 200 --out resultados/opt/politica_mlp_causal.json
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import argparse
import json
import os
import time

import numpy as np

import opt_es
from opt_entrenar import (escenarios_entrenamiento, escenarios_validacion, correr_referencias, H_ENTRENA)
from opt_politicas import PoliticaStop, n_parametros
from sim_batch import BatchSim


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hidden", type=int, default=8)
    ap.add_argument("--causal", action="store_true", help="sin vista adelante de llegadas")
    ap.add_argument("--gens", type=int, default=200)
    ap.add_argument("--n", type=int, default=64, help="escenarios de entrenamiento")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--gmin", type=int, default=7)
    ap.add_argument("--max-green", type=int, default=57)
    ap.add_argument("--sigma", type=float, default=0.3)
    ap.add_argument("--out", default="resultados/opt/politica.json")
    args = ap.parse_args()
    preview = not args.causal

    fl, arr = escenarios_entrenamiento(args.n, H_ENTRENA, seed=1)
    ref = correr_referencias(arr, fl, args.max_green)["actuado"]["delay"]

    def fitness(theta):
        r = BatchSim(arr, max_green=args.max_green).run(PoliticaStop(theta, args.hidden, preview, args.gmin), metrics=False)
        return float(np.mean(np.minimum(r["delay"] / ref, 20.0)))

    n = n_parametros(args.hidden)
    rng = np.random.default_rng(args.seed)
    x0 = rng.normal(0, 0.1, n)
    x0[-1] = -0.5
    t0 = time.time()

    def log(g, gb, best, mean, sigma):
        if g % 10 == 0 or g == args.gens - 1:
            print(f"gen {g:4d}  mejor gen {gb:.4f}  mejor {best:.4f}  media {mean:.3f}  sigma {sigma:.3f}  ({time.time()-t0:.0f} s)", flush=True)

    best_x, best_f, hist = opt_es.minimize(fitness, x0, args.sigma, args.gens, seed=args.seed, log=log)
    fl_v, arr_v = escenarios_validacion(64)
    refs_v = correr_referencias(arr_v, fl_v, args.max_green)
    rv = BatchSim(arr_v, max_green=args.max_green).run(PoliticaStop(best_x, args.hidden, preview, args.gmin))
    print(f"entrenamiento: {best_f:.4f} (1.0 = actuado)  validacion: {np.mean(rv['delay'] / refs_v['actuado']['delay']):.4f}")
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(dict(theta=best_x.tolist(), hidden=args.hidden, preview=preview, gmin=args.gmin, max_green=args.max_green,
                       fitness_train=best_f, historial=hist), f)


if __name__ == "__main__":
    main()
