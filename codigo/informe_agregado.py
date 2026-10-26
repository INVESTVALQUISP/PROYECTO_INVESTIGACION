"""
informe_agregado.py
================================================================================
Activacion y disparo de las reglas AGREGADOS sobre n = 20 replicas de 7200 s y varios regimenes de trafico (en vez de
una sola trayectoria de 1800 s con una semilla): para cada flujo, por replica, la proporcion de decisiones en que cada
regla R1..R5 (de cualquier intervencion) se activa y en que dispara (decide), la proporcion de cortes del verde y de
extensiones de 10 s; luego media y desviacion estandar de la muestra entre replicas.

Salida: resultados/disparos_agregados.json     Uso:  python codigo/informe_agregado.py [--reps 20]
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import argparse
import json
from concurrent.futures import ProcessPoolExecutor

import numpy as np

import estadistica as es
import sim_engine as se

FLUJOS = [(360, 360), (720, 720), (720, 2160), (1440, 1440)]
NOMBRES = {(360, 360): "simétrico bajo", (720, 720): "simétrico medio", (720, 2160): "asimétrico (artículo)",
           (1440, 1440): "simétrico pesado"}
DUR = 7200


def _rep(args):
    ns, ew, k = args
    sim = se.StepSim(se.SimConfig(lam_ns=ns / 3600, lam_ew=ew / 3600, seed=k, duration=DUR, a_mode="crossing",
                                  q_mode="current", predicted_q=False))
    sim.run_all()
    dec = [d for _, _, d in sim.decisions]
    n = len(dec)
    ext = [d for d in dec if not d.cut]
    out = dict(n=n, cortes=sum(d.cut for d in dec) / n, e10=sum(d.e_star == 10 for d in ext) / n,
               e_media=float(np.mean([d.e_star for d in ext])) if ext else 0.0, dm=sim.dm)
    out["activa"] = [sum(d.activation[i] > 0 for d in dec) / n for i in range(5)]
    out["dispara"] = [sum(i in d.winners for d in ext) / max(1, len(ext)) for i in range(5)]
    out["por_interv"] = {str(k_): sum(d.intervention == k_ for d in dec) / n for k_ in (7, 17, 27, 37, 47)}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=20)
    args = ap.parse_args()
    with ProcessPoolExecutor() as ex:
        res = list(ex.map(_rep, [(ns, ew, k) for ns, ew in FLUJOS for k in range(args.reps)]))
    out = dict(reps=args.reps, duration=DUR, semillas="k = 0..%d" % (args.reps - 1), flujos=[])
    for i, (ns, ew) in enumerate(FLUJOS):
        R = res[i * args.reps:(i + 1) * args.reps]
        def ms(key):
            a = np.array([r[key] for r in R], float)
            return dict(mean=a.mean(axis=0).tolist(), sd=a.std(axis=0, ddof=1).tolist())
        out["flujos"].append(dict(ns=ns, ew=ew, nombre=NOMBRES[(ns, ew)], decisiones_por_replica=ms("n"), cortes=ms("cortes"),
                                  e10=ms("e10"), e_media=ms("e_media"), dm=ms("dm"), activa=ms("activa"), dispara=ms("dispara"),
                                  por_interv=dict(zip(("7", "17", "27", "37", "47"),
                                                      [np.mean([r["por_interv"][k] for r in R]) for k in ("7", "17", "27", "37", "47")]))))
        f = out["flujos"][-1]
        print(f"{ns}/{ew} {NOMBRES[(ns, ew)]:24s} dec/rep={f['decisiones_por_replica']['mean']:.0f} cortes={100*f['cortes']['mean']:.1f}% "
              f"e*=10: {100*f['e10']['mean']:.1f}% | dispara R1..R5 (%): " + " ".join(f"{100*v:.1f}" for v in f["dispara"]["mean"]))
    json.dump(out, open("resultados/disparos_agregados.json", "w"), indent=1)


if __name__ == "__main__":
    main()
