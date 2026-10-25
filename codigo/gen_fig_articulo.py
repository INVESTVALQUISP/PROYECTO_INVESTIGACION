"""
gen_fig_articulo.py
================================================================================
Figuras del articulo IEEE, dibujadas al ANCHO FINAL (7.16 in = ancho de pagina a dos
columnas) para que el texto quede legible (>= 6 pt) sin escalar:
  fig_timeline.png, fig_taxonomia.png, fig_bloques.png, fig_fuzzificacion_ieee.png
Salida: articulo_ieee/figures/
Uso:  python gen_fig_articulo.py
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

import fuzzy_logic as fl

OUT = "articulo_ieee/figures"
W = 7.16
plt.rcParams.update({"font.size": 7, "axes.titlesize": 7.5, "axes.labelsize": 7, "xtick.labelsize": 6.5,
                     "ytick.labelsize": 6.5, "legend.fontsize": 6.3})
BL, OR, GR = "#2b6cb0", "#c05621", "#2f855a"


def box(ax, x0, y0, x1, y1, text, fc, ec, fs=6.8, bold=False, lw=1.0):
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0.25,rounding_size=0.8", fc=fc, ec=ec, lw=lw))
    ax.text((x0 + x1) / 2, (y0 + y1) / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal")


# ------------------------------------------------------------------ timeline
events = [(1958, "Webster:\nciclo fijo óptimo", "t"), (1963, "Miller", "t"), (1965, "Zadeh:\nconjuntos difusos", "f"),
          (1969, "TRANSYT", "t"), (1971, "Allsop", "t"), (1975, "Mamdani y Assilian:\nprimer control difuso", "f"),
          (1977, "Pappis y Mamdani:\nsemáforo difuso", "f"), (1982, "SCOOT y SCATS", "t"),
          (1999, "Trabia et al.", "f"), (2000, "Niittymäki\ny Pursula", "f"), (2001, "Bingham\n(neurodifuso)", "a"),
          (2003, "Abdulhai et al.\n(Q-learning)", "a"), (2005, "Murat y\nGedizlioglu", "f"),
          (2015, "Mnih et al.\n(DQN)", "a"), (2016, "Genders\ny Razavi", "a"), (2018, "IntelliLight", "a"), (2020, "Chu et al.", "a")]
col = {"t": BL, "f": OR, "a": GR}
LV = {1958: 1.0, 1963: -1.0, 1965: 2.1, 1969: -1.0, 1971: 1.0, 1975: -2.1, 1977: 2.1, 1982: -1.0,
      1999: 1.0, 2000: -1.0, 2001: 2.3, 2003: -2.3, 2005: 1.0, 2015: -1.0, 2016: 1.0, 2018: -2.2, 2020: 2.3}
fig, ax = plt.subplots(figsize=(W, 3.0))
ax.axhline(0, color="#444", lw=1.2)
for yr, lab, cat in events:
    lv = LV[yr]
    ax.plot([yr, yr], [0, lv * 0.82], color=col[cat], lw=0.8)
    ax.plot(yr, 0, "o", color=col[cat], ms=4)
    ax.text(yr, lv, f"{yr}\n{lab}", ha="center", va="bottom" if lv > 0 else "top", fontsize=5.6, color=col[cat],
            bbox=dict(boxstyle="round,pad=0.18", fc="white", ec=col[cat], lw=0.5))
ax.set_ylim(-3.9, 3.9); ax.set_xlim(1952, 2025); ax.axis("off")
for c, t in (("t", "Ingeniería de tránsito"), ("f", "Lógica difusa"), ("a", "Aprendizaje (RL / neurodifuso)")):
    ax.plot([], [], "o", color=col[c], label=t, ms=4)
ax.legend(loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.03))
fig.tight_layout(pad=0.3)
fig.savefig(f"{OUT}/fig_timeline.png", dpi=300); plt.close(fig)

# ------------------------------------------------------------------ taxonomia
fig, ax = plt.subplots(figsize=(W, 3.1))
ax.set_xlim(0, 100); ax.set_ylim(0, 64); ax.axis("off")


def link(xa, ya, xb, yb):
    ym = (ya + yb) / 2
    ax.plot([xa, xa, xb, xb], [ya, ym, ym, yb], color="#555", lw=0.8)


box(ax, 32, 55, 68, 62, "Control de señales de una intersección", "#e8edf5", "#1a2b4a", 7.6, True)
box(ax, 1, 43, 19, 50, "Tiempo fijo", "#dbeafe", BL, 7, True)
box(ax, 21, 43, 39, 50, "Actuado por\nvehículo", "#dbeafe", BL, 7, True)
box(ax, 41, 43, 59, 50, "Adaptativo en\ntiempo real", "#dbeafe", BL, 7, True)
box(ax, 61, 43, 99, 50, "Inteligencia computacional", "#ffedd5", OR, 7.2, True)
for xc in (10, 30, 50, 80):
    link(50, 55, xc, 50)
box(ax, 1, 20, 19, 40, "Webster (1958)\nMiller (1963)\nAllsop (1971)\nTRANSYT (1969)", "white", BL, 6.3)
box(ax, 21, 20, 39, 40, "Extensión del verde\ncon detectores\n(línea base de\nPappis y Mamdani)", "white", BL, 6.3)
box(ax, 41, 20, 59, 40, "SCOOT, SCATS\nRHODES (2001)\nrevisión de\nPapageorgiou (2003)", "white", BL, 6.3)
for xa in (10, 30, 50):
    ax.plot([xa, xa], [43, 40], color="#555", lw=0.8)
box(ax, 61, 33, 79, 40, "Lógica difusa", "#ffedd5", OR, 6.8, True)
box(ax, 81, 33, 99, 40, "Neurodifuso y RL", "#dcfce7", GR, 6.8, True)
link(80, 43, 70, 40); link(80, 43, 90, 40)
box(ax, 61, 12, 79, 30, "Pappis–Mamdani (1977)\nTrabia (1999)\nNiittymäki (2000)\nMurat (2005)", "white", OR, 6.0)
box(ax, 81, 12, 99, 30, "Bingham (2001)\nAbdulhai (2003)\nGenders (2016)\nIntelliLight (2018)\nChu (2020)", "white", GR, 6.0)
for xa in (70, 90):
    ax.plot([xa, xa], [33, 30], color="#555", lw=0.8)
ax.text(30, 8, "La réplica de este trabajo se ubica en la rama de lógica difusa\n(Pappis y Mamdani, 1977) y se contrasta con el ciclo fijo óptimo.",
        ha="center", va="center", fontsize=6.3, style="italic", color="#333")
fig.tight_layout(pad=0.3)
fig.savefig(f"{OUT}/fig_taxonomia.png", dpi=300); plt.close(fig)

# ------------------------------------------------------------------ bloques
fig, ax = plt.subplots(figsize=(W, 2.5))
ax.set_xlim(0, 100); ax.set_ylim(0, 40); ax.axis("off")
ax.add_patch(FancyBboxPatch((1, 17), 76, 21, boxstyle="round,pad=0.2,rounding_size=1", fc="none", ec=OR, lw=1, ls="--"))
ax.text(2.5, 36, "CONTROLADOR DIFUSO", fontsize=6.3, color=OR, fontweight="bold", va="center")
items = [(3, "Sensores (pads)", "T, A, Q"), (21, "Fuzzificación", "Tablas II–VI"), (39, "Inferencia", "25 reglas, mín–máx"), (57, "Decisión", "máx. y umbral 0.5")]
for x, t, sub in items:
    box(ax, x, 20, x + 16, 33, f"{t}\n{sub}", "#ffedd5", OR, 6.2)
for x in (19, 37, 55):
    ax.annotate("", xy=(x + 2, 26.5), xytext=(x, 26.5), arrowprops=dict(arrowstyle="->", color="#333", lw=0.9))
box(ax, 81, 20, 99, 33, "Semáforo\n(fase verde / roja)\ne* = 0…10 s", "#dcfce7", GR, 6.2)
ax.annotate("", xy=(81, 26.5), xytext=(73, 26.5), arrowprops=dict(arrowstyle="->", color=GR, lw=1.6))
ax.text(77, 29.5, "e*", fontsize=6.5, color=GR, ha="center", fontweight="bold")
box(ax, 20, 1, 66, 12, "Intersección: llegadas Bernoulli, colas FIFO,\ndescarga a 1 veh/s, tiempo perdido L = 10 s/ciclo", "#dbeafe", BL, 6.0)
box(ax, 72, 1, 99, 12, "Retardo medio\n$d_m = D\\,/\\sum q_n$", "#e5e7eb", "#4b5563", 6.2)
ax.annotate("", xy=(72, 6.5), xytext=(66, 6.5), arrowprops=dict(arrowstyle="->", color="#333", lw=0.9))
# el semaforo gobierna la fase de la interseccion
ax.plot([90, 90, 43], [20, 15.5, 15.5], color=GR, lw=1.2)
ax.annotate("", xy=(43, 12.2), xytext=(43, 15.5), arrowprops=dict(arrowstyle="->", color=GR, lw=1.2))
ax.text(72, 13.6, "fase verde / roja", fontsize=5.8, color=GR, va="center")
# medidas de la interseccion hacia los sensores
ax.plot([22, 11], [12, 12], color="#6d28d9", lw=1, ls="--")
ax.annotate("", xy=(11, 20), xytext=(11, 12), arrowprops=dict(arrowstyle="->", color="#6d28d9", lw=1, ls="--"))
ax.text(12.5, 15.5, "medidas $A$, $Q$, $T$", fontsize=5.8, color="#6d28d9", va="center")
fig.tight_layout(pad=0.3)
fig.savefig(f"{OUT}/fig_bloques.png", dpi=300); plt.close(fig)

# ------------------------------------------------------------------ fuzzificacion
T = np.arange(1, 11); Q = np.arange(4, 33)
fig, axs = plt.subplots(2, 2, figsize=(W, 4.9))


def sets(ax, xs, items, title, xl, loc_ncol=3):
    for i, (n, v) in enumerate(items):
        ax.plot(xs, v, color=plt.cm.tab10(i), lw=1.1, marker="o", ms=2.6, label=n)
    ax.set_title(title); ax.set_xlabel(xl); ax.set_ylabel("grado de pertenencia $\\mu$")
    ax.set_ylim(-0.05, 1.5); ax.set_yticks([0, .2, .4, .6, .8, 1.0]); ax.grid(True, lw=0.3, color="#d5dbe0")
    ax.legend(loc="upper center", ncol=loc_ncol, frameon=False, handlelength=1.4, columnspacing=0.9)


sets(axs[0, 0], T, list(fl.MU_TIME.items()), "(a) Tiempo $T$ y extensión $E$ (Tabla II)", "$t$ (s)")
sets(axs[0, 1], T, [(f"mt({b})", [fl.mt_arr(b, a) for a in T]) for b in ("none", "afew", "few", "medium", "many", "toomany")],
     "(b) Arribos con «más que» (Tabla V)", "$a$ (veh)")
sets(axs[1, 0], Q, list(fl.MU_QUEUE.items()), "(c) Cola $Q$ (Tabla IV)", "$q$ (veh)")
sets(axs[1, 1], Q, [(f"lt({b})", [fl.lt_queue(b, q) for q in Q]) for b in ("verysmall", "small", "smallplus", "medium", "long", "verylong")],
     "(d) Cola con «menos que» (Tabla VI)", "$q$ (veh)")
fig.tight_layout(pad=0.4)
fig.savefig(f"{OUT}/fig_fuzzificacion_ieee.png", dpi=300); plt.close(fig)
print("guardadas: fig_timeline, fig_taxonomia, fig_bloques, fig_fuzzificacion_ieee")
