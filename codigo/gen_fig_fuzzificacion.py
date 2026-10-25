"""
gen_fig_fuzzificacion.py
================================================================================
Genera figures/fig_fuzzificacion.png: las CURVAS DE FUZIFICACION del
controlador de Pappis & Mamdani (1977), ploteadas desde los MISMOS datos que
usa la replica (fuzzy_logic.py):

  (a) Tabla II  - conjuntos de TIEMPO / EXTENSION  T,  t = 1..10 s
  (b) Tabla V   - conjuntos de ARRIBOS A con el operador "more than" (mt)
                  (conjuntos base: Tabla III), a = 1..10 veh
  (c) Tabla IV  - conjuntos de COLA Q,  q = 4..32 veh
  (d) Tabla VI  - conjuntos de COLA Q con el operador "less than" (lt)
                  (conjuntos base: Tabla IV), q = 4..32 veh

Uso:  python gen_fig_fuzzificacion.py
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import fuzzy_logic as fl

T = np.arange(1, 11)                      # 1..10 s
A = np.arange(1, 11)                      # 1..10 veh
Q = np.arange(4, 33)                      # 4..32 veh

EST = dict(linewidth=1.8, markersize=4.5, marker="o", markevery=1)


def plot_sets(ax, xs, sets, xlabel, ylabel="grado de pertenencia μ"):
    for i, (name, vals) in enumerate(sets):
        ax.plot(xs, vals, label=name, color=plt.cm.tab10(i), **EST)
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_ylim(-0.06, 1.42)
    ax.set_yticks([0, .2, .4, .6, .8, 1.0])
    ax.grid(True, lw=0.5, color="#d5dbe0")
    ax.tick_params(labelsize=9)


def main():
    fig, axs = plt.subplots(2, 2, figsize=(12.5, 9.0))
    fig.suptitle("Curvas de fuzzificación — conjuntos lingüísticos del controlador "
                 "difuso (Pappis & Mamdani, 1977)",
                 fontsize=14, fontweight="bold", y=0.985)

    # (a) TIEMPO / EXTENSION  (Tabla II) ------------------------------------
    ax = axs[0, 0]
    plot_sets(ax, T, fl.MU_TIME.items(), "t (s) — tiempo de verde / extensión")
    ax.set_title("(a) Tiempo T y extensión E (Tabla II)\nuniverso: 1…10 s",
                 fontsize=11)
    ax.legend(fontsize=8.5, loc="upper center", ncol=3)

    # (b) ARRIBOS con mt  (Tabla III) ---------------------------------------
    ax = axs[0, 1]
    mt_sets = {b: [fl.mt_arr(b, a) for a in A] for b in
               ("none", "afew", "few", "medium", "many", "toomany")}
    plot_sets(ax, A, ((f"mt({b})", v) for b, v in mt_sets.items()),
              "a (veh) — arribos en los próximos 10 s")
    ax.set_title("(b) Arribos A con operador «more than» (Tabla V; base Tabla III)\n"
                 "mt(x) = «al menos x»: crece con a", fontsize=11)
    ax.legend(fontsize=8.5, loc="upper center", ncol=3)

    # (c) COLA  (Tabla IV) ---------------------------------------------------
    ax = axs[1, 0]
    plot_sets(ax, Q, fl.MU_QUEUE.items(), "q (veh) — cola del brazo en rojo")
    ax.set_title("(c) Cola Q (Tabla IV)\nuniverso: 4…32 veh, picos en 8…28",
                 fontsize=11)
    ax.legend(fontsize=8.5, loc="upper center", ncol=3)

    # (d) COLA con lt  (Tabla V) --------------------------------------------
    ax = axs[1, 1]
    lt_sets = {b: [fl.lt_queue(b, q) for q in Q] for b in
               ("verysmall", "small", "smallplus", "medium", "long", "verylong")}
    plot_sets(ax, Q, ((f"lt({b})", v) for b, v in lt_sets.items()),
              "q (veh) — cola del brazo en rojo")
    ax.set_title("(d) Cola Q con operador «less than» (Tabla VI; base Tabla IV)\n"
                 "lt(x) = «menor que x»: decrece con q", fontsize=11)
    ax.legend(fontsize=8.5, loc="upper center", ncol=3)

    fig.tight_layout(rect=(0, 0, 1, 0.965))
    fig.savefig("figures/fig_fuzzificacion.png", dpi=140)
    print("guardado: figures/fig_fuzzificacion.png")


if __name__ == "__main__":
    main()
