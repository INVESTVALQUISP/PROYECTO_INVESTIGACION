"""
gen_fig_correcciones.py
================================================================================
Figura de las CORRECCIONES de fuzzificacion: curvas de la version previa (rojo,
discontinuo), de la version corregida (azul) y valores impresos en el paper (x).

  * Operador mt (Tabla V): la version previa devolvia mu_A(a) para a < x0.
  * Conjunto 'verylong' de colas (Tabla IV) y su lt (Tabla VI): pico en q = 29 -> 28.

Uso:  python gen_fig_correcciones.py   -> figures/fig_correcciones_fuzzificacion.png
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import importlib.util

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import fuzzy_logic as fl
import paper_data as pdta

import os
_OLD = next(p for p in ("archivo/_old_fuzzy/old_fl.py", "archivo/_extras_pospuestos/_old_fuzzy/old_fl.py") if os.path.exists(p))
spec = importlib.util.spec_from_file_location("old_fl", _OLD)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)

A = np.arange(1, 11)
Q = np.arange(4, 33)
OLD, NEW = "#c53030", "#2b6cb0"


def draw(ax, xs, v_old, v_new, v_ref, title):
    ax.plot(xs, v_old, "--", color=OLD, lw=1.6, marker="s", ms=4, label="versión previa (incorrecta)")
    ax.plot(xs, v_new, "-", color=NEW, lw=1.8, marker="o", ms=4, label="versión corregida")
    ax.plot(xs, v_ref, "kx", ms=8, mew=1.5, label="valor impreso en el paper")
    ax.set_title(title, fontsize=10)
    ax.set_ylim(-0.06, 1.15)
    ax.grid(True, lw=0.5, color="#d5dbe0")
    ax.set_ylabel("μ")


fig = plt.figure(figsize=(13, 10))
gs = fig.add_gridspec(3, 3, hspace=0.55, wspace=0.28)
for i, name in enumerate(("none", "afew", "few", "medium", "many", "toomany")):
    ax = fig.add_subplot(gs[i // 3, i % 3])
    draw(ax, A, [old.mt_arr(name, a) for a in A], [fl.mt_arr(name, a) for a in A],
         pdta.TABLE_V[name], f"mt({name})")
    ax.set_xlabel("a (veh)")
    if i == 0:
        ax.legend(fontsize=7.5, loc="lower right")
ax = fig.add_subplot(gs[2, 0])
draw(ax, Q, old.MU_QUEUE["verylong"], fl.MU_QUEUE["verylong"], pdta.TABLE_IV["verylong"],
     "Cola «verylong» (Tabla IV): pico 29 → 28")
ax.set_xlabel("q (veh)")
ax = fig.add_subplot(gs[2, 1])
draw(ax, Q, [old.lt_queue("verylong", q) for q in Q], [fl.lt_queue("verylong", q) for q in Q],
     pdta.TABLE_VI["verylong"], "lt(verylong) (Tabla VI)")
ax.set_xlabel("q (veh)")
ax = fig.add_subplot(gs[2, 2])
ax.axis("off")
ax.text(0, 0.95,
        "Qué se corrigió\n\n"
        "• mt: para a < x0 el valor debe ser 0\n  (pág. 4 y Tabla V); la versión previa\n  daba μ_A(a).\n\n"
        "• verylong: la loma de la Tabla IV está\n  centrada en q = 28 (picos 8, 12, …, 28);\n  estaba en q = 29.\n\n"
        "Con la corrección las curvas del código\ncoinciden con las tablas impresas.",
        va="top", fontsize=9.5)
fig.suptitle("Correcciones de fuzzificación: antes (rojo) y después (azul) frente al paper (×)",
             fontsize=13, fontweight="bold", y=0.96)
fig.savefig("figures/fig_correcciones_fuzzificacion.png", dpi=125, bbox_inches="tight")
print("guardado: figures/fig_correcciones_fuzzificacion.png")
