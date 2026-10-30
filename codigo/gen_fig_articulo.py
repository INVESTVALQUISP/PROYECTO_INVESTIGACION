"""
gen_fig_articulo.py
================================================================================
Figuras del articulo IEEE, dibujadas al ANCHO FINAL (7.16 in = ancho de pagina a dos
columnas) para que el texto quede legible (>= 6 pt) sin escalar:
  fig_timeline.png, fig_taxonomia.png, fig_bloques.png, fig_fuzzificacion_ieee.png
Salida: articulo_replica/figures/
Uso:  python gen_fig_articulo.py
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

import fuzzy_logic as fl

OUT = "articulo_replica/figures"
W = 7.16
plt.rcParams.update({"font.size": 7, "axes.titlesize": 7.5, "axes.labelsize": 7, "xtick.labelsize": 6.5,
                     "ytick.labelsize": 6.5, "legend.fontsize": 6.3})
BL, OR, GR = "#2b6cb0", "#c05621", "#2f855a"


def box(ax, x0, y0, x1, y1, text, fc, ec, fs=6.8, bold=False, lw=1.0):
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0.25,rounding_size=0.8", fc=fc, ec=ec, lw=lw))
    ax.text((x0 + x1) / 2, (y0 + y1) / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal")


# ------------------------------------------------------------------ cronologia (por linea de trabajo)
# Se dibuja al TAMANO FINAL de impresion (7.16 in de ancho) con texto de 6 a 6.5 pt, legible sin escalar.
ERAS = [("1958 a 1982", 0), ("1999 a 2005", 1), ("2015 a 2020", 2), ("2021 a 2026", 3)]
LANES = [
    ("Ingeniería de tránsito", BL, "#dbeafe",
     [["1958 Webster: ciclo fijo óptimo", "1963 Miller", "1969 TRANSYT", "1971 Allsop", "1982 SCOOT y SCATS"], ["2001 RHODES"], [], []]),
    ("Lógica difusa", OR, "#ffedd5",
     [["1965 Zadeh: conjuntos difusos", "1975 Mamdani y Assilian", "1977 Pappis y Mamdani"],
      ["1999 Trabia et al.", "2000 Niittymäki y Pursula", "2005 Murat y Gedizlioglu"], [],
      ["2021 Ali; Jiang; Vuong (ANFIS)", "2026 Shaheen et al. (tipo 2)"]]),
    ("Aprendizaje y bancos de prueba", GR, "#dcfce7",
     [[], ["2001 Bingham (neurodifuso)", "2003 Abdulhai et al. (Q-learning)"],
      ["2015 Mnih et al. (DQN)", "2016 Genders y Razavi", "2018 IntelliLight", "2020 Chu et al."],
      ["2021 Ault (RESCO)", "2022 Noaeen et al. (revisión)", "2024 Mei et al. (LibSignal)", "2025 Vlasceanu; Michailidis"]]),
]
LH = 0.092                         # pulgadas por linea de 6 pt
x_lab, x_era0, w_era = 0.05, 1.2, 1.46
hts = [max(1, max(len(c) for c in L[3])) * LH + 0.1 for L in LANES]
H = 0.26 + sum(hts) + 0.05
fig, ax = plt.subplots(figsize=(W, H))
ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
y = H - 0.05
for lab, i in ERAS:                                    # encabezados de epoca
    ax.add_patch(plt.Rectangle((x_era0 + i * w_era, y - 0.2), w_era - 0.04, 0.2, fc="#e8edf5", ec="#1a2b4a", lw=0.6))
    ax.text(x_era0 + i * w_era + (w_era - 0.04) / 2, y - 0.1, lab, ha="center", va="center", fontsize=6.5, fontweight="bold")
ax.annotate("", xy=(W - 0.03, y - 0.1), xytext=(x_era0 + 4 * w_era - 0.03, y - 0.1), arrowprops=dict(arrowstyle="->", lw=0.8, color="#1a2b4a"))
y -= 0.26
for (nombre, col, fc, celdas), h in zip(LANES, hts):
    ax.add_patch(plt.Rectangle((x_lab, y - h), x_era0 - 0.1, h, fc=fc, ec=col, lw=0.8))
    ax.text(x_lab + (x_era0 - 0.1) / 2, y - h / 2, nombre.replace(" y bancos", "\ny bancos").replace("Ingeniería de ", "Ingeniería\nde "), ha="center", va="center",
            fontsize=6.3, fontweight="bold", color=col)
    for i, items in enumerate(celdas):
        ax.add_patch(plt.Rectangle((x_era0 + i * w_era, y - h), w_era - 0.04, h, fc="white", ec=col, lw=0.6))
        for k, t in enumerate(items):
            ax.text(x_era0 + i * w_era + 0.04, y - 0.05 - k * LH, t, ha="left", va="top", fontsize=6, color="#222")
    y -= h + 0.0
fig.subplots_adjust(0, 0, 1, 1)
fig.savefig(f"{OUT}/fig_timeline.png", dpi=300); plt.close(fig)

# ------------------------------------------------------------------ taxonomia (arbol de tres niveles)
COLS = [("Tiempo fijo", BL, "#dbeafe", ["Webster (1958)", "Miller (1963)", "Allsop (1971)", "TRANSYT (1969)"]),
        ("Actuado por vehículo", BL, "#dbeafe", ["Extensión del verde con", "detectores; línea base de", "Pappis y Mamdani"]),
        ("Adaptativo en tiempo real", BL, "#dbeafe", ["SCOOT, SCATS (1982)", "RHODES (2001)", "Papageorgiou (2003)"]),
        ("Lógica difusa", OR, "#ffedd5", ["Pappis y Mamdani (1977)", "Trabia (1999)", "Niittymäki y Pursula (2000)", "Murat (2005)", "Ali; Jiang (2021)", "Shaheen (2026)"]),
        ("Neurodifuso y RL", GR, "#dcfce7", ["Bingham (2001)", "Abdulhai (2003)", "Genders (2016)", "IntelliLight (2018)", "Chu (2020)", "Vuong (2021)", "Vlasceanu (2025)"]),
        ("Revisiones y bancos", GR, "#dcfce7", ["Noaeen (2022)", "Michailidis (2025)", "Ault, RESCO (2021)", "Mei, LibSignal (2024)"])]
nL = max(len(c[3]) for c in COLS)
H = 0.3 + 0.27 + 0.34 + nL * LH + 0.12 + 0.12
fig, ax = plt.subplots(figsize=(W, H))
ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
cw, gap, x0 = 1.13, 0.05, 0.05
xs = [x0 + i * (cw + gap) for i in range(6)]
yR = H - 0.26
ax.add_patch(FancyBboxPatch((W / 2 - 1.5, yR), 3.0, 0.22, boxstyle="round,pad=0.01,rounding_size=0.04", fc="#e8edf5", ec="#1a2b4a", lw=1.0))
ax.text(W / 2, yR + 0.11, "Control de señales de una intersección aislada", ha="center", va="center", fontsize=7, fontweight="bold")
yG = yR - 0.30
grupos = [("Ingeniería de tránsito", 0, 2, BL, "#dbeafe"), ("Inteligencia computacional", 3, 5, OR, "#ffedd5")]
for nombre, i0, i1, col, fc in grupos:
    xa, xb = xs[i0], xs[i1] + cw
    ax.add_patch(FancyBboxPatch((xa, yG), xb - xa, 0.2, boxstyle="round,pad=0.01,rounding_size=0.04", fc=fc, ec=col, lw=1.0))
    ax.text((xa + xb) / 2, yG + 0.1, nombre, ha="center", va="center", fontsize=6.8, fontweight="bold", color=col)
    xm = (xa + xb) / 2
    ax.plot([W / 2, W / 2, xm, xm], [yR, yR - 0.04, yR - 0.04, yG + 0.2], color="#555", lw=0.8)
yC = yG - 0.3
for (nombre, col, fc, items), x in zip(COLS, xs):
    ax.add_patch(FancyBboxPatch((x, yC), cw, 0.24, boxstyle="round,pad=0.01,rounding_size=0.04", fc=fc, ec=col, lw=1.4 if nombre == "Lógica difusa" else 0.9))
    ax.text(x + cw / 2, yC + 0.12, nombre, ha="center", va="center", fontsize=6.3, fontweight="bold", color=col)
    ax.plot([x + cw / 2] * 2, [yC + 0.24, yG], color="#555", lw=0.6)
    ax.add_patch(plt.Rectangle((x, yC - 0.06 - nL * LH - 0.04), cw, nL * LH + 0.06 + 0.0, fc="white", ec=col, lw=0.6))
    for k, t in enumerate(items):
        ax.text(x + 0.04, yC - 0.07 - k * LH, t, ha="left", va="top", fontsize=6, color="#222")
fig.subplots_adjust(0, 0, 1, 1)
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
