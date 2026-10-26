"""
gen_fig_simulador_compuesto.py
================================================================================
Figura unica del simulador para el articulo: la captura de la ventana completa
(muestras/captura_simulador_gui.png) con los seis apartados rotulados (a) a (f).
Reemplaza a las Figs. 7 a 13 de la version anterior (la captura y sus seis recortes);
los seis apartados por separado quedan en el material suplementario.
Salida: articulo_ieee/figures/fig_simulador.png
Uso:  python codigo/gen_fig_simulador_compuesto.py
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.image as mpimg

IMG = "muestras/captura_simulador_gui.png"
OUT = "articulo_ieee/figures/fig_simulador.png"
img = mpimg.imread(IMG)
h, w = img.shape[:2]
fig = plt.figure(figsize=(7.16, 7.16 * h / w))
ax = fig.add_axes([0, 0, 1, 1])
ax.imshow(img); ax.axis("off")

# (letra, x0, y0, x1, y1) en pixeles de la captura
PANELES = [("a", 165, 185, 620, 632),    # la calle
           ("b", 825, 172, 1240, 402),   # panel de reglas
           ("c", 825, 428, 1240, 610),   # vector de grados
           ("d", 825, 628, 1240, 868),   # disparos acumulados
           ("e", 5, 640, 745, 878),      # traza del retardo
           ("f", 1262, 622, 1596, 892)]  # registro de decisiones
for L, x0, y0, x1, y1 in PANELES:
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec="#c53030", lw=1.1, ls="--"))
    # la letra va en una esquina libre (derecha) para no tapar los titulos de los paneles
    xt, yt, va = (x1 - 4, y1 - 4, "bottom") if L == "e" else (x1 - 4, y0 + 4, "top")
    ax.text(xt, yt, f"({L})", ha="right", va=va, fontsize=8.5, fontweight="bold", color="white",
            bbox=dict(boxstyle="round,pad=0.18", fc="#c53030", ec="none"))
fig.savefig(OUT, dpi=round(w / 7.16))
print("guardado", OUT, (w, h))
