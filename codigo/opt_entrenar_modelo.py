"""
opt_entrenar_modelo.py
================================================================================
Entrena con CMA-ES un controlador para minimizar el retardo medio normalizado (frente al actuado por detector) en
caudales sorteados al azar (no son los de la Tabla VIII). Modelos:

  mlp      politica neuronal de verde/cambio cada segundo (cota de lo posible)           opt_politicas.PoliticaStop
  flcs     difuso nuevo de 27 reglas, decide cada segundo (interpretable)               opt_flc2.FuzzySegundo
  flcopt   difuso de 27 reglas con horizontes de vista adelante aprendidos (42 parametros)  opt_flc2.FuzzyOpt
  flcs4    difuso de 81 reglas con el hueco desde la ultima llegada como 4a variable     opt_flc2.FuzzyGap
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
from opt_entrenar import (escenarios_entrenamiento, escenarios_validacion, correr_referencias, actuado_afinado, H_ENTRENA)
from sim_batch import BatchSim


def construir(modelo, theta, args):
    """(simulador, controlador) para un vector de parametros."""
    if modelo == "mlp":
        return (lambda arr: BatchSim(arr, max_green=args.max_green)), opt_politicas.PoliticaStop(theta, args.hidden, not args.causal, args.gmin, args.gaps)
    if modelo == "flcs4":
        return (lambda arr: BatchSim(arr, max_green=args.max_green)), opt_flc2.FuzzyGap(theta, not args.causal, args.gmin)
    if modelo == "flcopt":
        return (lambda arr: BatchSim(arr, max_green=args.max_green)), opt_flc2.FuzzyOpt(theta, True, args.gmin)
    if modelo == "flcs":
        return (lambda arr: BatchSim(arr, max_green=args.max_green)), opt_flc2.FuzzySegundo(theta, not args.causal, args.gmin)
    if modelo == "afinado":
        return (lambda arr: BatchSim(arr)), opt_flc.PappisAfinado(theta)
    raise ValueError(modelo)


def punto_inicial(modelo, args, rng):
    if modelo == "flcs4":
        return opt_flc2.THETA0_GAP.copy(), args.sigma, None
    if modelo == "flcopt":
        return opt_flc2.THETA0_OPT.copy(), args.sigma, None
    if modelo == "mlp" and args.hidden == 0 and args.warm:
        # lineal que imita al actuado: corta si la cola del verde esta vacia y hay cola en el rojo
        f = opt_politicas.n_car(args.gaps)
        x0 = np.zeros(f + 1)
        x0[1], x0[2], x0[12], x0[f] = -100.0, 30.0, 6.0, -6.5      # q_g, q_r, cola_vacia, sesgo
        return x0, args.sigma, None
    if modelo == "mlp":
        n = opt_politicas.n_parametros(args.hidden, args.gaps)
        x0 = rng.normal(0, 0.1, n)
        x0[-1] = -0.5
        return x0, args.sigma, None
    if modelo == "flcs":
        return opt_flc2.THETA0.copy(), args.sigma, None
    return opt_flc.THETA_PAPER.copy(), args.sigma, opt_flc.LIMITES


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", choices=["mlp", "flcs", "flcs4", "flcopt", "afinado"], required=True)
    ap.add_argument("--hidden", type=int, default=8)
    ap.add_argument("--causal", action="store_true", help="sin vista adelante de llegadas")
    ap.add_argument("--warm", action="store_true", help="(mlp lineal) arranca desde una regla que imita al actuado")
    ap.add_argument("--gaps", action="store_true", help="(mlp) agrega el hueco desde la ultima llegada como caracteristica")
    ap.add_argument("--gens", type=int, default=150)
    ap.add_argument("--n", type=int, default=64, help="escenarios de entrenamiento")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--gmin", type=int, default=7)
    ap.add_argument("--max-green", type=int, default=57)
    ap.add_argument("--sigma", type=float, default=0.3)
    ap.add_argument("--suma-max", type=float, default=3000, help="suma maxima de caudales (veh/h) de los escenarios sorteados")
    ap.add_argument("--ref", choices=["actuado", "actuado_af"], default="actuado", help="controlador que normaliza el objetivo")
    ap.add_argument("--resume", action="store_true", help="si existe OUT.parcial, arranca desde su mejor theta (reinicio en caliente)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    fl, arr = escenarios_entrenamiento(args.n, H_ENTRENA, seed=1, suma_max=args.suma_max)

    def referencia(a, f):
        return (actuado_afinado(a) if args.ref == "actuado_af" else correr_referencias(a, f, 57)["actuado"])["delay"]

    ref = referencia(arr, fl)

    def fitness(theta):
        mk, ctrl = construir(args.modelo, theta, args)
        r = mk(arr).run(ctrl, metrics=False)
        return float(np.mean(np.minimum(r["delay"] / ref, 20.0)))

    rng = np.random.default_rng(args.seed)
    x0, sigma0, bounds = punto_inicial(args.modelo, args, rng)
    if args.resume and os.path.exists(args.out + ".parcial"):
        x0 = np.array(json.load(open(args.out + ".parcial"))["theta"])
        sigma0 = min(sigma0, 0.15)
        print("reanudando desde", args.out + ".parcial", flush=True)
    print(f"modelo {args.modelo}: {len(x0)} parametros; objetivo inicial {fitness(x0):.4f} (1.0 = actuado)", flush=True)
    t0 = time.time()

    def log(g, gb, best, mean, sigma):
        if g % 10 == 0 or g == args.gens - 1:
            print(f"gen {g:4d}  mejor gen {gb:.4f}  mejor {best:.4f}  media {mean:.3f}  sigma {sigma:.3f}  ({time.time()-t0:.0f} s)", flush=True)

    def guardar(bx, bf, h, parcial=True):
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out + (".parcial" if parcial else ""), "w") as f:
            json.dump(dict(modelo=args.modelo, theta=bx.tolist(), hidden=args.hidden, preview=not args.causal, gmin=args.gmin, gaps=args.gaps,
                           max_green=args.max_green, fitness_train=bf, historial=h, parcial=parcial, suma_max=args.suma_max, ref=args.ref), f)

    best_x, best_f, hist = opt_es.minimize(fitness, x0, sigma0, args.gens, seed=args.seed, log=log, bounds=bounds,
                                           ckpt=lambda bx, bf, h: guardar(bx, bf, h, True))
    fl_v, arr_v = escenarios_validacion(64, suma_max=args.suma_max)
    mk, ctrl = construir(args.modelo, best_x, args)
    rv = mk(arr_v).run(ctrl)
    print(f"entrenamiento: {best_f:.4f} (1.0 = {args.ref})  validacion: {np.mean(rv['delay'] / referencia(arr_v, fl_v)):.4f}")
    guardar(best_x, best_f, hist, parcial=False)


if __name__ == "__main__":
    main()
