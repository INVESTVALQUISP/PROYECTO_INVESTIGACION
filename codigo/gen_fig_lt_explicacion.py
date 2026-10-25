"""
gen_fig_lt_explicacion.py
Figura auxiliar para explicar el panel (d) de fig_fuzzificacion.png
(conjuntos lt(...) sobre la cola).
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import fuzzy_logic as fl

Q = np.arange(4, 33)
EST = dict(linewidth=1.8, markersize=4.5, marker="o", markevery=1)

fig, axs = plt.subplots(1, 2, figsize=(13, 4.8))

# ---------------- Panel (a): el mecanismo con un solo conjunto ------------
ax = axs[0]
base = [fl.MU_QUEUE["medium"][q - 4] for q in Q]
lt = [fl.lt_queue("medium", q) for q in Q]
ax.plot(Q, base, color="#2b6cb0", **EST, label="medium (conjunto base, Tabla IV)")
ax.plot(Q, lt, color="#c53030", **EST, label="lt(medium) = «cola menor que mediana»")
ax.axvline(12, color="#555", linestyle="--", linewidth=1)
ax.annotate("cola = 12 veh\nlt(medium) = 1\n(mediana está lejos: la cola\nsí es 'menor que mediana')",
            xy=(12, 1), xytext=(13.2, 0.62), fontsize=8.5,
            arrowprops=dict(arrowstyle="->", color="#555"),
            bbox=dict(boxstyle="round,pad=0.3", fc="#fffbe6", ec="#d9c98a"))
ax.text(20, 0.55, "x0 = pico\n(= 20)", fontsize=8, ha="center", color="#c53030")
ax.set_title("(a) Cómo se construye lt: 1 − μ a la IZQUIERDA del pico, 0 a la derecha",
             fontsize=10)
ax.set_xlabel("q (veh) — cola del brazo en rojo")
ax.set_ylabel("grado de pertenencia μ")
ax.set_ylim(-0.06, 1.15)
ax.grid(True, lw=0.5, color="#d5dbe0")
ax.tick_params(labelsize=9)
ax.legend(fontsize=8.5, loc="upper left")

# ---------------- Panel (b): las seis curvas (el panel d original) --------
ax = axs[1]
colors = plt.cm.tab10
for i, name in enumerate(("verysmall", "small", "smallplus", "medium", "long", "verylong")):
    vals = [fl.lt_queue(name, q) for q in Q]
    lw = 2.2 if name == "medium" else 1.2
    ax.plot(Q, vals, color=colors(i), linewidth=lw,
            marker="o", markersize=3.5, markevery=1,
            alpha=1.0 if name == "medium" else 0.45,
            label=f"lt({name})")
ax.set_title("(b) Las seis curvas del panel (d) — cada una es un\n«umbral difuso» a una altura distinta",
             fontsize=10)
ax.set_xlabel("q (veh) — cola del brazo en rojo")
ax.set_ylabel("grado de pertenencia μ")
ax.set_ylim(-0.06, 1.15)
ax.grid(True, lw=0.5, color="#d5dbe0")
ax.tick_params(labelsize=9)
ax.legend(fontsize=8, loc="lower left", ncol=1)

fig.suptitle("Explicación del panel (d): colas con operador «less than» (Tabla VI)",
             fontsize=12, fontweight="bold")
fig.tight_layout(rect=(0, 0, 1, 0.95))
fig.savefig("figures/fig_lt_explicacion.png", dpi=140)
print("guardado: figures/fig_lt_explicacion.png")
