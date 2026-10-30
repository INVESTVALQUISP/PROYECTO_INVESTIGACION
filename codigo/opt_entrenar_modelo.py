"""
opt_entrenar_modelo.py
================================================================================
Entrena con CMA-ES un controlador para minimizar el retardo medio normalizado (frente al actuado por detector) en
caudales sorteados al azar (no son los de la Tabla VIII). Modelos:

  mlp      politica neuronal de verde/cambio cada segundo (cota de lo posible)           opt_politicas.PoliticaStop
  flcs     difuso nuevo de 27 reglas, decide cada segundo (interpretable)               opt_flc2.FuzzySegundo
  afinado  las 25 reglas de Pappis y Mamdani con 30 parametros afinados (cada 10 s)     opt_flc.PappisAfinado

Uso:
  python opt_entrenar_modelo.py --modelo flcs --gens 150 --out resultados/opt/flcs_preview.json
  python opt_entrenar_modelo.py --modelo flcs --causal --gens 150 --out resultados/opt/flcs_causal.json
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import argparse
import json
import os
import time

import numpy as np

import opt_es
import opt_flc
import opt_flc2
import opt_politicas
from opt_entrenar import (escenarios_entrenamiento, escenarios_validacion, correr_referencias, H_ENTRENA)
from sim_batch import BatchSim


def construir(modelo, theta, args):
    """(simulador, controlador) para un vector de parametros."""
    if modelo == "mlp":
        return (lambda arr: BatchSim(arr, max_green=args.max_green)), opt_politicas.PoliticaStop(theta, args.hidden, not args.causal, args.gmin)
    if modelo == "flcs":
        return (lambda arr: BatchSim(arr, max_green=args.max_green)), opt_flc2.FuzzySegundo(theta, not args.causal, args.gmin)
    if modelo == "afinado":
        return (lambda arr: BatchSim(arr)), opt_flc.PappisAfinado(theta)
    raise ValueError(modelo)


def punto_inicial(modelo, args, rng):
    if modelo == "mlp":
        n = opt_politicas.n_parametros(args.hidden)
        x0 = rng.normal(0, 0.1, n)
        x0[-1] = -0.5
        return x0, args.sigma, None
    if modelo == "flcs":
        return opt_flc2.THETA0.copy(), args.sigma, None
    return opt_flc.THETA_PAPER.copy(), args.sigma, opt_flc.LIMITES


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", choices=["mlp", "flcs", "afinado"], required=True)
    ap.add_argument("--hidden", type=int, default=8)
    ap.add_argument("--causal", action="store_true", help="sin vista adelante de llegadas")
    ap.add_argument("--gens", type=int, default=150)
    ap.add_argument("--n", type=int, default=64, help="escenarios de entrenamiento")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--gmin", type=int, default=7)
    ap.add_argument("--max-green", type=int, default=57)
    ap.add_argument("--sigma", type=float, default=0.3)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    fl, arr = escenarios_entrenamiento(args.n, H_ENTRENA, seed=1)
    ref = correr_referencias(arr, fl, args.max_green)["actuado"]["delay"]

    def fitness(theta):
        mk, ctrl = construir(args.modelo, theta, args)
        r = mk(arr).run(ctrl, metrics=False)
        return float(np.mean(np.minimum(r["delay"] / ref, 20.0)))

    rng = np.random.default_rng(args.seed)
    x0, sigma0, bounds = punto_inicial(args.modelo, args, rng)
    print(f"modelo {args.modelo}: {len(x0)} parametros; objetivo inicial {fitness(x0):.4f} (1.0 = actuado)", flush=True)
    t0 = time.time()

    def log(g, gb, best, mean, sigma):
        if g % 10 == 0 or g == args.gens - 1:
            print(f"gen {g:4d}  mejor gen {gb:.4f}  mejor {best:.4f}  media {mean:.3f}  sigma {sigma:.3f}  ({time.time()-t0:.0f} s)", flush=True)

    def guardar(bx, bf, h, parcial=True):
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out + (".parcial" if parcial else ""), "w") as f:
            json.dump(dict(modelo=args.modelo, theta=bx.tolist(), hidden=args.hidden, preview=not args.causal, gmin=args.gmin,
                           max_green=args.max_green, fitness_train=bf, historial=h, parcial=parcial), f)

    best_x, best_f, hist = opt_es.minimize(fitness, x0, sigma0, args.gens, seed=args.seed, log=log, bounds=bounds,
                                           ckpt=lambda bx, bf, h: guardar(bx, bf, h, True))
    fl_v, arr_v = escenarios_validacion(64)
    refs_v = correr_referencias(arr_v, fl_v, args.max_green)
    mk, ctrl = construir(args.modelo, best_x, args)
    rv = mk(arr_v).run(ctrl)
    print(f"entrenamiento: {best_f:.4f} (1.0 = actuado)  validacion: {np.mean(rv['delay'] / refs_v['actuado']['delay']):.4f}")
    guardar(best_x, best_f, hist, parcial=False)


if __name__ == "__main__":
    main()
