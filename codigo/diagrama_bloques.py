"""
diagrama_bloques.py
================================================================================
Genera el diagrama de bloques del proceso de control difuso de Pappis & Mamdani
(1977): interseccion (planta), semaforo, sensores, controlador difuso y
evaluacion del retardo.

Salida:  figures/diagram_bloques.png  y  figures/diagram_bloques.svg
Uso:     python diagrama_bloques.py
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

# colores
C_CTRL_F, C_CTRL_E = "#ffedd5", "#c2410c"     # controlador difuso (naranja)
C_PL_F,   C_PL_E   = "#dbeafe", "#1d4ed8"     # planta (azul)
C_LU_F,   C_LU_E   = "#dcfce7", "#15803d"     # semaforo (verde)
C_EV_F,   C_EV_E   = "#e5e7eb", "#4b5563"     # evaluacion (gris)
C_FLOW   = "#334155"
C_MEAS   = "#7c3aed"
C_ACT    = "#16a34a"

fig, ax = plt.subplots(figsize=(16.5, 10.2))
ax.set_xlim(0, 100)
ax.set_ylim(0, 62)
ax.axis("off")


def block(x, y, w, h, title, lines, fc, ec, tsize=10, bsize=8):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.5,rounding_size=1.0",
                                fc=fc, ec=ec, lw=1.6, zorder=3))
    cx = x + w / 2
    ax.text(cx, y + h - 1.2, title, ha="center", va="top",
            fontsize=tsize, fontweight="bold", color="#111827", zorder=4)
    for i, ln in enumerate(lines):
        ax.text(cx, y + h - 3.4 - i * 1.95, ln, ha="center", va="top",
                fontsize=bsize, color="#1f2937", zorder=4)


def arrow(p0, p1, color=C_FLOW, lw=1.6, ls="-"):
    ax.annotate("", xy=p1, xytext=p0, zorder=2,
                arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                linestyle=ls, shrinkA=0, shrinkB=0))


def frame(x, y, w, h, ec, label, lc):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.3,rounding_size=1.2",
                                fc="none", ec=ec, lw=1.2, ls=(0, (6, 4)),
                                zorder=1))
    ax.text(x + 1.6, y + h - 1.3, label, ha="left", va="top",
            fontsize=10.5, fontweight="bold", color=lc, zorder=4)


# ------------------------------ titulo --------------------------------------
ax.text(50, 60.6, "Diagrama de bloques del proceso de control difuso",
        ha="center", va="top", fontsize=15.5, fontweight="bold", color="#111827")
ax.text(50, 58.6, "Fuzzy Logic Controller for a Traffic Junction  (Pappis & Mamdani, 1977)",
        ha="center", va="top", fontsize=10, color="#6b7280")

# --------------------- fila 1: controlador difuso ----------------------------
frame(3, 40, 94, 16.5, C_CTRL_E, "CONTROLADOR DIFUSO", C_CTRL_E)
block(6, 43, 20, 10.5, "Sensores (pads)",
      ["T: tiempo de la fase", "A: arribos del brazo en verde (10 s)",
       "Q: cola del brazo en rojo"], C_CTRL_F, C_CTRL_E)
block(30, 43, 19, 10.5, "Fuzzificaci\u00f3n",
      ["\u03bc_T(t) \u2014 Tabla II", "\u03bc_mt(A)(a) \u2014 Tablas III y V",
       "\u03bc_lt(Q)(q) \u2014 Tablas IV y VI"], C_CTRL_F, C_CTRL_E)
block(53, 43, 21, 10.5, "Inferencia (25 reglas)",
      ["SI T Y mt(A) Y lt(Q) ENT. E", "g_e = max_r  min( gT, gA, gQ, gE )",
       "para cada extensi\u00f3n e = 1\u202610 s"], C_CTRL_F, C_CTRL_E)
block(78, 43, 17, 10.5, "Decisi\u00f3n",
      ["max g_e < 0.5  \u2192  e* = 0", "(cambiar de fase)",
       "max g_e \u2265 0.5  \u2192  e* = argmax", "(extender 1\u201310 s)"], C_CTRL_F, C_CTRL_E)

arrow((26.4, 48.2), (29.6, 48.2))
arrow((49.4, 48.2), (52.6, 48.2))
arrow((74.4, 48.2), (77.6, 48.2))

# --------------------- fila 2: interseccion (planta) -------------------------
frame(3, 10, 94, 18, C_PL_E, "INTERSECCI\u00d3N  (planta: simulaci\u00f3n del tr\u00e1fico)", C_PL_E)
block(6, 13.5, 17, 11, "Arribos de veh\u00edculos",
      ["N\u2013S:  \u03bb\u2081 = q\u2081/3600 veh/s", "E\u2013W:  \u03bb\u2082 = q\u2082/3600 veh/s",
       "proceso Bernoulli (intervalo de 1 s)"], C_PL_F, C_PL_E)
block(28, 13.5, 17, 11, "Colas (FIFO)",
      ["Q\u2081 (N\u2013S)  y  Q\u2082 (E\u2013W)", "brazo en rojo: acumula",
       "brazo en verde: descarga"], C_PL_F, C_PL_E)
block(50, 13.5, 18, 11, "Descarga a saturaci\u00f3n",
      ["s = 3600 veh/h = 1 veh/s", "solo el brazo en verde",
       "D += tiempo de espera"], C_PL_F, C_PL_E)
block(73, 13.5, 21, 11, "Sem\u00e1foro (fase)",
      ["Fase 1: N-S verde / E-W rojo", "Fase 2: E-W verde / N-S rojo",
       "L = 10 s/ciclo", "verde m\u00e1ximo: 57 s (adaptativo)"], C_LU_F, C_LU_E)

arrow((23.4, 19), (27.6, 19))
arrow((45.4, 19), (49.6, 19))
arrow((72.6, 17.5), (68.6, 17.5))
ax.text(71.2, 18.15, "fase verde/rojo", ha="center", va="bottom",
        fontsize=7.5, color=C_FLOW, style="italic")

# --------------------- evaluacion -------------------------------------------
block(28, 1, 44, 6, "Evaluaci\u00f3n: retardo medio por veh\u00edculo",
      ["d_m = D / \u03a3 q_n    [s/veh]      \u2192     validaci\u00f3n (Tabla I) y resultado principal (Tabla VIII)"],
      C_EV_F, C_EV_E, tsize=9.5, bsize=8)
arrow((36, 13.1), (40, 7.4), lw=1.4)
ax.text(34.6, 9.3, "D  y  \u03a3 q_n", ha="right", va="center", fontsize=7.5,
        color=C_FLOW, style="italic")

ax.text(83.5, 11.2, "Intervenciones difusas a los 7, 17, 27, 37 y 47 s de cada verde",
        ha="center", va="center", fontsize=7.8, color=C_CTRL_E, style="italic")

# --------------------- senales verticales (pasillo y 28..40) -----------------
# A, Q : de arribos/colas a los sensores (medicion, punteada)
arrow((18, 28.4), (18, 42.4), color=C_MEAS, lw=1.6, ls="--")
ax.text(16.8, 35.6, "A (arribos)\nQ (cola)", ha="right", va="center",
        fontsize=8, color=C_MEAS)

# T : del semaforo a los sensores (codo ortogonal)
ax.plot([80, 80], [24.6, 34], color=C_MEAS, lw=1.6, ls="--", zorder=2)
ax.plot([80, 22], [34, 34], color=C_MEAS, lw=1.6, ls="--", zorder=2)
arrow((22, 34), (22, 42.4), color=C_MEAS, lw=1.6, ls="--")
ax.text(51, 35.2, "T (tiempo transcurrido de la fase)", ha="center", va="bottom",
        fontsize=8, color=C_MEAS)

# e* : de la decision al semaforo (accion de control, verde gruesa)
arrow((86.5, 42.4), (86.5, 24.6), color=C_ACT, lw=3.0)
ax.text(88.2, 33.8, "e*: extender el verde\no cambiar de fase (e* = 0)",
        ha="left", va="center", fontsize=8.5, color=C_ACT, fontweight="bold")

# --------------------- leyenda ------------------------------------------------
lx, ly = 4.5, 5.2
ax.plot([lx, lx + 4.5], [ly, ly], color=C_FLOW, lw=1.6)
ax.text(lx + 5.2, ly, "flujo (arribos, colas, descarga)", fontsize=8, va="center")
ax.plot([lx, lx + 4.5], [ly - 2.3, ly - 2.3], color=C_MEAS, lw=1.6, ls="--")
ax.text(lx + 5.2, ly - 2.3, "medici\u00f3n (sensores)", fontsize=8, va="center")
ax.plot([lx, lx + 4.5], [ly - 4.6, ly - 4.6], color=C_ACT, lw=3.0)
ax.text(lx + 5.2, ly - 4.6, "acci\u00f3n de control (e*)", fontsize=8, va="center")

plt.tight_layout()
fig.savefig("figures/diagram_bloques.png", dpi=200)
fig.savefig("figures/diagram_bloques.svg")
print("guardado: figures/diagram_bloques.png y .svg")
