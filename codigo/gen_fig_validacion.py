"""
gen_fig_validacion.py
================================================================================
Figuras de VALIDACION de la replica frente al paper original (ingles):

  figures/fig_validacion_fuzzificacion.png
      Las curvas de fuzzificacion trazadas desde el codigo (lineas) con los
      valores IMPRESOS en el paper (marcadores x) encima: Tablas II, V, IV y VI.
  figures/fig_ejemplo_fuzzificacion.png
      Fuzzificacion de un caso concreto (t = 8 s, a = 4 veh, q = 6 veh).
  figures/fig_validacion_tablas.png
      Tabla I y Tabla VIII: replica vs. valores publicados.

Uso:  python gen_fig_validacion.py   (requiere resultados/resultados_oficiales.json)
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import fuzzy_logic as fl
import paper_data as pdta

T = np.arange(1, 11)
Q = np.arange(4, 33)
COL = plt.cm.tab10


def _panel(ax, xs, code_sets, paper_sets, title, xlabel, legend_loc, ncol=1):
    worst = 0.0
    for i, (name, vals) in enumerate(code_sets):
        ax.plot(xs, vals, color=COL(i), lw=1.8, marker="o", ms=4, label=name)
        ref = paper_sets[name if name in paper_sets else name.split("(")[-1].rstrip(")")]
        ax.plot(xs, ref, linestyle="none", marker="x", ms=9, mew=1.6, color="k", zorder=5)
        worst = max(worst, float(np.max(np.abs(np.array(vals) - np.array(ref)))))
    ax.plot([], [], "kx", ms=9, mew=1.6, label="valor impreso en el paper")
    ax.set_title(f"{title}\nmáx |código − paper| = {worst:.3f}", fontsize=10.5)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("grado de pertenencia μ")
    ax.set_ylim(-0.06, 1.42)
    ax.set_yticks([0, .2, .4, .6, .8, 1.0])
    ax.grid(True, lw=0.5, color="#d5dbe0")
    ax.legend(fontsize=8, loc="upper center", ncol=3)
    return worst


def fig_validacion_fuzz():
    fig, axs = plt.subplots(2, 2, figsize=(12.5, 9))
    fig.suptitle("Validación de la fuzzificación: curvas del código vs. valores impresos "
                 "en el paper original", fontsize=13.5, fontweight="bold", y=0.985)
    w = []
    w.append(_panel(axs[0, 0], T, list(fl.MU_TIME.items()), pdta.TABLE_II,
                    "(a) Tiempo T / extensión E — Tabla II", "t (s)", "upper left"))
    mt = [(f"mt({b})", [fl.mt_arr(b, a) for a in T]) for b in pdta.TABLE_V]
    w.append(_panel(axs[0, 1], T, mt, pdta.TABLE_V,
                    "(b) Arribos con «more than» — Tabla V", "a (veh)", "lower right", 2))
    w.append(_panel(axs[1, 0], Q, list(fl.MU_QUEUE.items()), pdta.TABLE_IV,
                    "(c) Cola Q — Tabla IV", "q (veh)", "upper right", 2))
    lt = [(f"lt({b})", [fl.lt_queue(b, q) for q in Q]) for b in pdta.TABLE_VI]
    w.append(_panel(axs[1, 1], Q, lt, pdta.TABLE_VI,
                    "(d) Cola con «less than» — Tabla VI", "q (veh)", "lower left", 2))
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig("figures/fig_validacion_fuzzificacion.png", dpi=130)
    plt.close(fig)
    return w


def fig_ejemplo():
    t0, a0, q0 = 8, 4, 6
    fig, axs = plt.subplots(1, 3, figsize=(14, 4.4))
    ax = axs[0]
    for i, (n, v) in enumerate(fl.MU_TIME.items()):
        ax.plot(T, v, color=COL(i), lw=1.6, marker="o", ms=4, label=n)
        ax.plot([t0], [v[t0 - 1]], "o", ms=11, mfc="none", mec=COL(i), mew=2)
    ax.axvline(t0, color="#555", ls="--", lw=1)
    ax.set_title(f"T = {t0} s  →  long 0.5, verylong 0.5", fontsize=10.5)
    ax.set_xlabel("t (s)")
    ax.legend(fontsize=8, loc="upper center", ncol=3)
    ax = axs[1]
    for i, b in enumerate(pdta.TABLE_V):
        v = [fl.mt_arr(b, a) for a in T]
        ax.plot(T, v, color=COL(i), lw=1.6, marker="o", ms=4, label=f"mt({b})")
        ax.plot([a0], [v[a0 - 1]], "o", ms=11, mfc="none", mec=COL(i), mew=2)
    ax.axvline(a0, color="#555", ls="--", lw=1)
    g = {b: fl.mt_arr(b, a0) for b in pdta.TABLE_V}
    ax.set_title(f"A = {a0} veh  →  " + ", ".join(f"{b} {v:g}" for b, v in g.items() if v), fontsize=9.5)
    ax.set_xlabel("a (veh)")
    ax.legend(fontsize=7.5, loc="upper center", ncol=3)
    ax = axs[2]
    for i, b in enumerate(pdta.TABLE_VI):
        v = [fl.lt_queue(b, q) for q in Q]
        ax.plot(Q, v, color=COL(i), lw=1.6, marker="o", ms=3.5, label=f"lt({b})")
        ax.plot([q0], [fl.lt_queue(b, q0)], "o", ms=11, mfc="none", mec=COL(i), mew=2)
    ax.axvline(q0, color="#555", ls="--", lw=1)
    ax.set_title(f"Q = {q0} veh  →  lt(verysmall) {fl.lt_queue('verysmall', q0):g}, "
                 f"las demás 1", fontsize=10)
    ax.set_xlabel("q (veh)")
    ax.legend(fontsize=7.5, loc="upper center", ncol=3)
    for ax in axs:
        ax.set_ylim(-0.06, 1.45)
        ax.set_yticks([0, .2, .4, .6, .8, 1.0])
        ax.set_ylabel("grado de pertenencia μ")
        ax.grid(True, lw=0.5, color="#d5dbe0")
    fig.suptitle(f"Fuzzificación de un caso concreto: t = {t0} s, a = {a0} veh, q = {q0} veh "
                 "(los círculos son los grados que entran a las reglas)",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig("figures/fig_ejemplo_fuzzificacion.png", dpi=130)
    plt.close(fig)


def fig_tablas():
    res = json.load(open("resultados/resultados_oficiales.json"))
    fig, axs = plt.subplots(1, 3, figsize=(14.5, 4.9))

    def scatter(ax, x, y, lim, label, color, hollow=False, log=False):
        ax.scatter(x, y, s=34, label=label, edgecolors=color,
                   facecolors="none" if hollow else color, linewidths=1.4)
        lo, hi = lim
        ax.plot([lo, hi], [lo, hi], "k-", lw=1)
        if not log:
            ax.fill_between([lo, hi], [0.9 * lo, 0.9 * hi], [1.1 * lo, 1.1 * hi],
                            color="#cfd8e6", alpha=0.6, label="±10 %")
        ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
        ax.grid(True, lw=0.5, color="#d5dbe0")
        ax.set_aspect("equal")

    t1 = res["table_I"]
    ax = axs[0]
    p = [pdta.TABLE_I[(r["ns"], r["ew"])] for r in t1]
    scatter(ax, [a for a, b in p], [r["sim"] for r in t1], (5, 33), "simulación vs 'Model'", "#2b6cb0")
    scatter(ax, [b for a, b in p], [r["formula"] for r in t1], (5, 33), "fórmula vs 'Formula'", "#c05621", hollow=True)
    ax.set_title("Tabla I — modelo de ciclo fijo", fontsize=11)
    ax.set_xlabel("paper (s/veh)"); ax.set_ylabel("réplica (s/veh)")
    ax.legend(fontsize=8, loc="upper left")

    cal = res["table_VIII"]["calibrada"]
    pz = [pdta.TABLE_VIII[(r["ns"], r["ew"])][1] for r in cal]
    ax = axs[1]
    scatter(ax, pz, [r["fuzzy"] for r in cal], (4, 26), "difuso, lectura calibrada", "#2f855a")
    ax.set_title("Tabla VIII — difuso, lectura calibrada", fontsize=11)
    ax.set_xlabel("paper (s/veh)"); ax.set_ylabel("réplica (s/veh)")
    ax.legend(fontsize=8, loc="upper left")

    lit = res["table_VIII"]["literal"]
    ax = axs[2]
    scatter(ax, pz, [r["fuzzy"] for r in lit], (3, 900), "difuso, lectura literal", "#c53030", log=True)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_title("Tabla VIII — difuso, lectura literal (escala log)", fontsize=11)
    ax.set_xlabel("paper (s/veh)"); ax.set_ylabel("réplica (s/veh)")
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig("figures/fig_validacion_tablas.png", dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    w = fig_validacion_fuzz()
    print("máx |código − paper| por panel:", [f"{x:.3f}" for x in w])
    fig_ejemplo()
    fig_tablas()
    print("figuras de validación generadas")
