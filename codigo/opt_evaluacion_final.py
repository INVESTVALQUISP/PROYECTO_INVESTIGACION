"""
opt_evaluacion_final.py
================================================================================
Evalua todos los controladores en los conjuntos de PRUEBA (ver opt_evaluar.py) y guarda
resultados/opt/evaluacion_final.json con los retardos por escenario, el resumen por par de caudales y las
comparaciones pareadas (Wilcoxon + Holm).

Controladores (nombre -> como se construye):
  fijo           ciclo fijo de Webster (conoce los caudales)
  actuado        actuado por detector original (gap 3 s, minimo 7 s, maximo 57 s)
  actuado_af     actuado afinado en entrenamiento (resultados/opt/actuado_afinado.json)
  maxpressure    presion maxima afinada (resultados/opt/maxpressure_afinado.json)
  pappis         controlador de Pappis y Mamdani, lectura calibrada (replica)
  mdp            politica optima por programacion dinamica (conoce los caudales; cota, no realizable)
  y los modelos entrenados que existan en resultados/opt/*.json (mlp_*, flcs_*, afinado_*)

Uso:  python opt_evaluacion_final.py [--rapido]
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import argparse
import glob
import json
import os
import time

import numpy as np

import opt_evaluar as ev
import opt_flc
import opt_flc2
import opt_mdp
import opt_politicas
from opt_controladores import FixedCycle, Actuated, PappisFuzzy, MaxPressure
from opt_entrenar import escenarios_oficiales, escenarios_validacion
from sim_batch import BatchSim

OUT = "resultados/opt"


def cargar_modelos():
    """{nombre: dict del json} de los modelos entrenados."""
    out = {}
    for p in sorted(glob.glob(f"{OUT}/*.json")):
        d = json.load(open(p))
        if isinstance(d, dict) and "theta" in d:
            out[os.path.splitext(os.path.basename(p))[0]] = d
    return out


def construir_modelo(d):
    modelo = d.get("modelo", "mlp")
    th = np.array(d["theta"])
    mg = d.get("max_green", 57)
    if modelo == "mlp":
        return (lambda arr: BatchSim(arr, max_green=mg)), opt_politicas.PoliticaStop(th, d["hidden"], d["preview"], d["gmin"], d.get("gaps", False))
    if modelo == "flcs4":
        return (lambda arr: BatchSim(arr, max_green=mg)), opt_flc2.FuzzyGap(th, d["preview"], d["gmin"])
    if modelo == "flcs":
        return (lambda arr: BatchSim(arr, max_green=mg)), opt_flc2.FuzzySegundo(th, d["preview"], d["gmin"])
    if modelo == "afinado":
        return (lambda arr: BatchSim(arr)), opt_flc.PappisAfinado(th)
    raise ValueError(modelo)


def correr_todos(arr, fl, modelos, mdp_tablas=None):
    ln, le = fl[:, 0] / 3600.0, fl[:, 1] / 3600.0
    af = json.load(open(f"{OUT}/actuado_afinado.json"))["mejor"]
    mp = json.load(open(f"{OUT}/maxpressure_afinado.json"))["mejor"]
    res = {
        "fijo": BatchSim(arr, max_green=None).run(FixedCycle(ln, le)),
        "actuado": BatchSim(arr, max_green=57).run(Actuated(7, 3)),
        "actuado_af": BatchSim(arr, max_green=af["max_green"]).run(Actuated(af["min_green"], af["gap"])),
        "maxpressure": BatchSim(arr, max_green=mp["max_green"]).run(MaxPressure(mp["min_green"], mp["margen"])),
        "pappis": BatchSim(arr).run(PappisFuzzy()),
    }
    if mdp_tablas is not None:
        res["mdp"] = BatchSim(arr, max_green=None).run(opt_mdp.PoliticaMDP(mdp_tablas))
    for nombre, d in modelos.items():
        mk, ctrl = construir_modelo(d)
        res[nombre] = mk(arr).run(ctrl)
    return res


def tablas_mdp(fl):
    """Politica optima por cada par de caudales distinto (conoce los caudales)."""
    cache, out = {}, []
    for a, b in fl:
        k = (round(a, 3), round(b, 3))
        if k not in cache:
            cache[k] = opt_mdp.resolver(a / 3600.0, b / 3600.0, qmax=80, tol=1e-6)[0]
        out.append(cache[k])
    return np.stack(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rapido", action="store_true", help="5 replicas y 3600 s (solo para probar)")
    ap.add_argument("--sin-mdp", action="store_true")
    args = ap.parse_args()
    reps, H = (5, 3600) if args.rapido else (20, 7200)
    modelos = cargar_modelos()
    print("modelos entrenados:", list(modelos), flush=True)
    t0 = time.time()
    salida = {}
    conjuntos = {"oficial": escenarios_oficiales(reps, H)}
    if not args.rapido:
        conjuntos["no_vistos"] = escenarios_validacion(64, H)
        conjuntos["variable"] = ev.escenarios_variables(64, H)
        conjuntos["saturado"] = ev.escenarios_saturados(32, H)
    for nombre, (fl, arr) in conjuntos.items():
        mdp = None if args.sin_mdp else tablas_mdp(fl)
        res = correr_todos(arr, fl, modelos, mdp)
        info = dict(flujos=fl.tolist(), H=H, delay={k: v["delay"].tolist() for k, v in res.items()},
                    delay_servidos={k: v["delay_served"].tolist() for k, v in res.items()},
                    delay_ns={k: v["delay_ns"].tolist() for k, v in res.items()},
                    delay_ew={k: v["delay_ew"].tolist() for k, v in res.items()},
                    qmax={k: np.maximum(v["qmax_ns"], v["qmax_ew"]).tolist() for k, v in res.items()},
                    cambios_fase={k: v["n_switch"].tolist() for k, v in res.items()})
        if nombre == "oficial":
            info["por_par"] = {k: ev.resumen_por_par(np.array(info["delay"][k]), fl, reps) for k in res}
            refs = [r for r in ("fijo", "actuado", "actuado_af", "pappis") if r in res]
            info["comparaciones"] = {f"{a}__vs__{b}": ev.comparar(np.array(info["delay"][a]), np.array(info["delay"][b]), reps)
                                     for a in res for b in refs if a != b}
        salida[nombre] = info
        medias = {k: float(np.mean(v)) for k, v in info["delay"].items()}
        print(f"[{nombre}] ({len(fl)} escenarios, {time.time()-t0:.0f} s) retardo medio:",
              {k: round(v, 2) for k, v in medias.items()}, flush=True)
    sufijo = "_rapido" if args.rapido else ""
    with open(f"{OUT}/evaluacion_final{sufijo}.json", "w") as f:
        json.dump(salida, f)
    print("guardado", f"{OUT}/evaluacion_final{sufijo}.json")


if __name__ == "__main__":
    main()
