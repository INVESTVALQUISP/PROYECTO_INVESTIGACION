"""
gen_fig_opt.py
================================================================================
Figuras del articulo de optimizacion (se dibujan al ancho final: 7.16 in a dos columnas o 3.5 in a una):
  fig_opt_retardo.png     (a) retardo por par de caudales; (b) mejora de FLC-O frente a Pappis y Mamdani con su significancia
  fig_opt_difuso.png      funciones de pertenencia aprendidas de G, R y E y superficie de decision de FLC-O
  fig_opt_aprendizaje.png curvas de aprendizaje de CMA-ES de los modelos finales
  fig_opt_traza.png       colas y fases durante 400 s: Pappis y Mamdani frente a FLC-O (mismas llegadas)
Salida: articulo_opt/figures/
Uso:  python gen_fig_opt.py
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import opt_flc2
from opt_controladores import PappisFuzzy
from opt_entrenar import construir
from opt_nombres import ETIQUETA, clave, finales
from sim_batch import BatchSim

OUT = "articulo_opt/figures"
plt.rcParams.update({"font.size": 7, "axes.titlesize": 7.5, "axes.labelsize": 7, "legend.fontsize": 6.2, "xtick.labelsize": 6.5,
                     "ytick.labelsize": 6.5, "axes.spines.top": False, "axes.spines.right": False, "font.family": "DejaVu Sans"})
COL = {"fijo": "#8c8c8c", "actuado_af": "#2b6cb0", "pappis": "#d9822b", "flc": "#1f9d55", "mdp": "#222222", "mlp": "#8e44ad"}


def cargar_modelo(nombre):
    m = json.load(open(f"resultados/opt/{nombre}.json"))
    th = np.array(m["theta"])
    if m.get("modelo") == "flcopt":
        return m, opt_flc2.FuzzyOpt(th, True, m["gmin"])
    return m, opt_flc2.FuzzySegundo(th, m.get("preview", True), m["gmin"])


def fig_retardo(d, key):
    of = d["oficial"]
    pares = np.array(of["flujos"])[::20]
    tot = pares.sum(axis=1)
    orden = np.lexsort((pares[:, 0], tot))
    comp = of["comparaciones"][f"{key['flc']}__vs__{key['pappis']}"]
    fig, ax = plt.subplots(1, 2, figsize=(7.16, 2.5), gridspec_kw={"width_ratios": [1.35, 1]})
    x = np.arange(len(pares))
    for r, ls in (("fijo", "-"), ("actuado_af", "-"), ("pappis", "-"), ("mdp", "--"), ("flc", "-")):
        y = np.array([of["por_par"][key[r]][i]["media"] for i in orden])
        ax[0].plot(x, y, ls, color=COL[r], lw=1.9 if r == "flc" else 1.2, marker="o" if r == "flc" else None, ms=3,
                   label=ETIQUETA[r], zorder=5 if r == "flc" else 3)
    lo = np.array([of["por_par"][key["flc"]][i]["ic_lo"] for i in orden])
    hi = np.array([of["por_par"][key["flc"]][i]["ic_hi"] for i in orden])
    ax[0].fill_between(x, lo, hi, color=COL["flc"], alpha=0.25, lw=0)
    ax[0].set_xticks(x)
    ax[0].set_xticklabels([f"{int(pares[i, 0])}/{int(pares[i, 1])}" for i in orden], rotation=60, ha="right", fontsize=5.6)
    ax[0].set_xlabel("caudales N-S / E-W (veh/h), ordenados por la suma")
    ax[0].set_ylabel("retardo medio (s/veh)")
    ax[0].set_title("(a) Retardo por par de caudales (banda: IC 95 % de FLC-O)")
    ax[0].legend(frameon=False, ncol=1, loc="upper left")
    g = np.array(comp["mejora_por_par"])[orden]
    sig = np.array(comp["p_holm"])[orden] < 0.05
    ax[1].bar(x, g, color=[COL["flc"] if s else "#b8c4bd" for s in sig], width=0.75)
    ax[1].axhline(0, color="k", lw=0.6)
    ax[1].set_xticks(x)
    ax[1].set_xticklabels([f"{int(pares[i, 0])}/{int(pares[i, 1])}" for i in orden], rotation=60, ha="right", fontsize=5.6)
    ax[1].set_xlabel("caudales N-S / E-W (veh/h)")
    ax[1].set_ylabel("mejora (%)")
    ax[1].set_title("(b) Mejora frente a Pappis y Mamdani\n(verde: significativa, Holm 0.05)")
    fig.tight_layout(pad=0.5)
    fig.savefig(f"{OUT}/fig_opt_retardo.png", dpi=300)
    plt.close(fig)


def fig_difuso(nombre):
    m, c = cargar_modelo(nombre)
    fig, ax = plt.subplots(1, 4, figsize=(7.16, 2.1), gridspec_kw={"width_ratios": [1, 1, 1, 1.25]})
    for a, (titulo, k, lo, hi, et) in zip(ax[:3], (("G: demanda en verde", c.kG, 0, 14, "veh"), ("R: presión en rojo", c.kR, 0, 40, "veh"),
                                                      ("V: verde transcurrido", c.kE, 0, 90, "s"))):
        x = np.linspace(lo, hi, 400)
        mu = opt_flc2.ruspini(x, k)
        for j, (n, col) in enumerate((("bajo", "#2b6cb0"), ("medio", "#d9822b"), ("alto", "#1f9d55"))):
            a.plot(x, mu[:, j], color=col, lw=1.3, label=n)
        a.set_title(titulo)
        a.set_xlabel(et)
        a.set_ylim(-0.03, 1.08)
        a.legend(frameon=False, loc="center right", fontsize=5.8)
    ax[0].set_ylabel("pertenencia")
    # superficie de decision en el plano (G, R) para tres valores de E
    gg, rr = np.meshgrid(np.linspace(0, 14, 80), np.linspace(0, 40, 80))
    sc = []
    for e in (c.gmin + 2, 25, 60):
        s = c.score(gg.ravel(), rr.ravel(), np.full(gg.size, e, dtype=float)).reshape(gg.shape)
        sc.append(s)
    im = ax[3].contourf(gg, rr, sc[0], levels=[-5, 0, 5], colors=["#cfe8d8", "#f3d1b0"], alpha=0.95)
    for s, ls, e in zip(sc, ("-", "--", ":"), (c.gmin + 2, 25, 60)):
        ax[3].contour(gg, rr, s, levels=[0], colors="k", linewidths=1.0, linestyles=ls)
        ax[3].plot([], [], "k", ls=ls, lw=1, label=f"V = {e} s")
    ax[3].set_xlabel("G (veh)")
    ax[3].set_ylabel("R (veh)")
    ax[3].set_title("Frontera de decisión (u = 0)")
    ax[3].text(0.04, 0.93, "cambiar", transform=ax[3].transAxes, fontsize=6, color="#8a4b0f")
    ax[3].text(0.55, 0.06, "seguir en verde", transform=ax[3].transAxes, fontsize=6, color="#1c6b3f")
    ax[3].legend(frameon=False, loc="upper right", fontsize=5.6)
    fig.tight_layout(pad=0.5)
    fig.savefig(f"{OUT}/fig_opt_difuso.png", dpi=300)
    plt.close(fig)


def fig_aprendizaje(fin):
    fig, ax = plt.subplots(figsize=(3.5, 2.3))
    for rol, col, etq in (("flc", COL["flc"], "FLC-O"), ("mlp", COL["mlp"], "Política neuronal"), ("afinado", COL["pappis"], "Pappis y Mamdani afinado")):
        nom = fin.get(rol)
        if not nom or not os.path.exists(f"resultados/opt/{nom}.json"):
            continue
        h = np.array(json.load(open(f"resultados/opt/{nom}.json"))["historial"])
        ax.plot(h[:, 0], np.minimum.accumulate(h[:, 1]), color=col, lw=1.4, label=etq)
    ax.axhline(1.0, color="k", lw=0.6, ls=":")
    ax.set_xlabel("generación de CMA-ES")
    ax.set_ylabel("objetivo (1 = actuado de referencia)")
    ax.legend(frameon=False)
    fig.tight_layout(pad=0.5)
    fig.savefig(f"{OUT}/fig_opt_aprendizaje.png", dpi=300)
    plt.close(fig)


def fig_traza(nombre, flujo=(720, 2160), seed=3, t0=300, T=400):
    m, c = cargar_modelo(nombre)
    arr = construir(np.array([flujo, flujo], dtype=float), [seed, seed], 1200)
    # un solo conjunto de llegadas para los dos controladores: mismo escenario duplicado
    r_p = BatchSim(arr).run(PappisFuzzy(), trace=True)
    r_f = BatchSim(arr, max_green=m.get("max_green", 57)).run(c, trace=True)
    fig, ax = plt.subplots(2, 1, figsize=(7.16, 2.9), sharex=True)
    t = np.arange(t0, t0 + T)
    for a, r, tit in ((ax[0], r_p, "Pappis y Mamdani"), (ax[1], r_f, "FLC-O")):
        q = r["trace_q"][0, t0:t0 + T]
        ph = r["trace_phase"][0, t0:t0 + T]
        a.plot(t, q[:, 0], color="#2b6cb0", lw=1.0, label="cola N-S")
        a.plot(t, q[:, 1], color="#d9822b", lw=1.0, label="cola E-W")
        top = max(q.max() + 2, 14)
        for val, col in ((0, "#2b6cb0"), (1, "#d9822b"), (2, "#888888")):
            msk = ph == val
            a.fill_between(t, 0, top, where=msk, color=col, alpha=0.12 if val < 2 else 0.25, lw=0, step="post")
        a.set_ylim(0, top)
        a.set_ylabel("vehículos")
        a.set_title(f"{tit}: retardo medio {r['delay'][0]:.1f} s/veh en 1200 s", loc="left")
    ax[1].set_xlabel("tiempo (s); fondo azul: verde N-S, naranja: verde E-W, gris: tiempo perdido")
    ax[0].legend(frameon=False, ncol=2, loc="upper right")
    fig.tight_layout(pad=0.5)
    fig.savefig(f"{OUT}/fig_opt_traza.png", dpi=300)
    plt.close(fig)


def main():
    os.makedirs(OUT, exist_ok=True)
    d = json.load(open("resultados/opt/evaluacion_final.json"))
    fin = finales()
    key = {r: clave(r, fin) for r in ("fijo", "actuado_af", "pappis", "mdp", "flc")}
    fig_retardo(d, key)
    fig_difuso(fin["flc"])
    fig_aprendizaje(fin)
    fig_traza(fin["flc"])
    print("figuras en", OUT)


if __name__ == "__main__":
    main()
