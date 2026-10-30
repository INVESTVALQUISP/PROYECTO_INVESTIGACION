"""
simulador_opt.py
================================================================================
Compara el controlador de Pappis y Mamdani (1977) con el controlador optimizado FLC-O (u otro modelo entrenado de
resultados/opt/) sobre las MISMAS llegadas de vehiculos, y lo muestra en pantalla o lo guarda.

  * Figura: colas de los dos brazos y fase de cada controlador durante una ventana de tiempo, con el retardo medio.
  * Animacion: las colas como barras y los semaforos de cada controlador avanzando en el tiempo (--gif o --mp4).

Uso:
  python simulador_opt.py                                   # escenario del articulo, abre una ventana
  python simulador_opt.py --ns 1080 --ew 1800 --seed 5 --seconds 1200
  python simulador_opt.py --guardar salidas/comparacion.png --sin-ventana
  python simulador_opt.py --gif salidas/comparacion.gif --sin-ventana     # animacion
  python simulador_opt.py --modelo flcopt_g5                            # otro modelo entrenado
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import argparse
import json
import os

import matplotlib
import numpy as np

import opt_flc2
from opt_controladores import PappisFuzzy
from opt_entrenar import construir
from opt_nombres import finales
from sim_batch import BatchSim

AZUL, NARANJA, GRIS, VERDE, ROJO = "#2b6cb0", "#d9822b", "#888888", "#1f9d55", "#c0392b"


def cargar(nombre):
    m = json.load(open(f"resultados/opt/{nombre}.json"))
    th = np.array(m["theta"])
    if m.get("modelo") == "flcopt":
        ctrl = opt_flc2.FuzzyOpt(th, True, m["gmin"])
    elif m.get("modelo") == "flcs":
        ctrl = opt_flc2.FuzzySegundo(th, m.get("preview", True), m["gmin"])
    else:
        raise SystemExit(f"el modelo {nombre} no es un controlador difuso (use flcopt o flcs)")
    return m, ctrl


def correr(ns, ew, seed, seconds, nombre):
    m, ctrl = cargar(nombre)
    arr = construir(np.array([[ns, ew]], dtype=float), [seed], seconds)
    rp = BatchSim(arr).run(PappisFuzzy(), trace=True)
    rf = BatchSim(arr, max_green=m.get("max_green", 57)).run(ctrl, trace=True)
    return rp, rf


def resumen(r, nombre):
    ph = r["trace_phase"][0]
    cambios = int(r["n_switch"][0])
    return (f"{nombre}: retardo medio {r['delay'][0]:.2f} s/veh · cola maxima {int(max(r['qmax_ns'][0], r['qmax_ew'][0]))} veh · "
            f"{cambios} cambios de fase · verde medio {np.sum(ph < 2) / max(1, cambios):.1f} s")


def figura(rp, rf, t0, T, titulo_f="FLC-O"):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, 1, figsize=(10, 5.2), sharex=True)
    t = np.arange(t0, t0 + T)
    for a, r, tit in ((ax[0], rp, "Pappis y Mamdani (1977)"), (ax[1], rf, titulo_f)):
        q = r["trace_q"][0, t0:t0 + T]
        ph = r["trace_phase"][0, t0:t0 + T]
        a.plot(t, q[:, 0], color=AZUL, lw=1.1, label="cola N-S")
        a.plot(t, q[:, 1], color=NARANJA, lw=1.1, label="cola E-W")
        top = max(q.max() + 2, 14)
        for val, col in ((0, AZUL), (1, NARANJA), (2, GRIS)):
            a.fill_between(t, 0, top, where=ph == val, color=col, alpha=0.12 if val < 2 else 0.25, lw=0, step="post")
        a.set_ylim(0, top)
        a.set_ylabel("vehículos")
        a.set_title(f"{tit}: retardo medio {r['delay'][0]:.1f} s/veh en {r['trace_q'].shape[1]} s", loc="left", fontsize=10)
    ax[0].legend(frameon=False, ncol=2, loc="upper right")
    ax[1].set_xlabel("tiempo (s); fondo azul: verde N-S, naranja: verde E-W, gris: tiempo perdido")
    fig.tight_layout()
    return fig


def animar(rp, rf, t0, T, paso, salida, titulo_f="FLC-O"):
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter
    fig, axs = plt.subplots(1, 2, figsize=(8, 4))
    tops = max(rp["trace_q"][0].max(), rf["trace_q"][0].max()) + 2
    barras, lamp, txt = [], [], []
    for a, tit in zip(axs, ("Pappis y Mamdani (1977)", titulo_f)):
        a.set_xlim(-0.8, 3.2)
        a.set_ylim(0, tops)
        a.set_xticks([0.5, 2.0])
        a.set_xticklabels(["N-S", "E-W"])
        a.set_ylabel("cola (veh)")
        a.set_title(tit, fontsize=10)
        barras.append(a.bar([0.5, 2.0], [0, 0], width=0.8, color=[AZUL, NARANJA]))
        lamp.append([a.scatter([0.5], [tops - 1], s=260, color=GRIS, zorder=5), a.scatter([2.0], [tops - 1], s=260, color=GRIS, zorder=5)])
        txt.append(a.text(0.02, 0.02, "", transform=a.transAxes, fontsize=8))
    cab = fig.suptitle("", fontsize=10)

    def cuadro(k):
        t = t0 + k * paso
        for i, r in enumerate((rp, rf)):
            q = r["trace_q"][0, t]
            ph = int(r["trace_phase"][0, t])
            for b, h in zip(barras[i], q):
                b.set_height(h)
            lamp[i][0].set_color(VERDE if ph == 0 else ROJO)
            lamp[i][1].set_color(VERDE if ph == 1 else ROJO)
            if ph == 2:
                lamp[i][0].set_color(GRIS)
                lamp[i][1].set_color(GRIS)
            txt[i].set_text(f"cola total {int(q.sum())} veh" + ("  · tiempo perdido" if ph == 2 else ""))
        cab.set_text(f"t = {t} s")
        return []

    n = int(T // paso)
    ani = FuncAnimation(fig, cuadro, frames=n, interval=100, blit=False)
    ani.save(salida, writer=PillowWriter(fps=10))
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description="Compara Pappis y Mamdani con FLC-O sobre las mismas llegadas")
    ap.add_argument("--ns", type=float, default=720, help="flujo N-S (veh/h)")
    ap.add_argument("--ew", type=float, default=2160, help="flujo E-W (veh/h)")
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--seconds", type=int, default=1200, help="duracion simulada (s)")
    ap.add_argument("--modelo", default="", help="modelo entrenado de resultados/opt/ (por defecto, el FLC-O elegido)")
    ap.add_argument("--desde", type=int, default=300, help="inicio de la ventana mostrada (s)")
    ap.add_argument("--ventana", type=int, default=400, help="largo de la ventana mostrada (s)")
    ap.add_argument("--guardar", default="", help="guarda la figura en este PNG")
    ap.add_argument("--gif", default="", help="guarda una animacion GIF")
    ap.add_argument("--sin-ventana", action="store_true", help="no abre ventana (solo guarda)")
    args = ap.parse_args()
    if args.sin_ventana:
        matplotlib.use("Agg")
    nombre = args.modelo or finales().get("flc")
    if not nombre:
        raise SystemExit("no hay un FLC-O elegido (resultados/opt/modelos_finales.json); use --modelo")
    rp, rf = correr(args.ns, args.ew, args.seed, args.seconds, nombre)
    print(resumen(rp, "Pappis y Mamdani"))
    print(resumen(rf, f"FLC-O ({nombre})"))
    t0 = min(args.desde, max(0, args.seconds - args.ventana))
    T = min(args.ventana, args.seconds - t0)
    fig = figura(rp, rf, t0, T)
    if args.guardar:
        os.makedirs(os.path.dirname(args.guardar) or ".", exist_ok=True)
        fig.savefig(args.guardar, dpi=150)
        print("guardado", args.guardar)
    if args.gif:
        os.makedirs(os.path.dirname(args.gif) or ".", exist_ok=True)
        animar(rp, rf, t0, T, 2, args.gif)
        print("guardado", args.gif)
    if not args.sin_ventana:
        import matplotlib.pyplot as plt
        plt.show()


if __name__ == "__main__":
    main()
