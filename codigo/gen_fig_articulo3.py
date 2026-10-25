"""
gen_fig_articulo3.py
================================================================================
Figura de incertidumbre estadistica del articulo: error relativo (replica - paper) en
cada caudal con su IC 95 %, para el ciclo fijo y el controlador difuso.
Requiere resultados/analisis_estadistico.json (python codigo/analisis_estadistico.py).
Salida: articulo_ieee/figures/fig_incertidumbre.png
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

est = json.load(open("resultados/analisis_estadistico.json"))
rows = est["rows"]
x = np.arange(len(rows))
fig, ax = plt.subplots(figsize=(3.45, 2.7))
for key, color, off, lab in (("fixed", "#7f8c8d", -0.17, "Ciclo fijo"), ("fuzzy", "#c0392b", 0.17, "Difuso")):
    m = np.array([100 * (r[key]["mean"] - r[key]["paper"]) / r[key]["paper"] for r in rows])
    lo = np.array([100 * (r[key]["lo"] - r[key]["paper"]) / r[key]["paper"] for r in rows])
    hi = np.array([100 * (r[key]["hi"] - r[key]["paper"]) / r[key]["paper"] for r in rows])
    ax.errorbar(x + off, m, yerr=[m - lo, hi - m], fmt="o", ms=3, lw=1, capsize=1.5, color=color, label=lab)
    ax.axhline(est["sesgo_" + ("fijo" if key == "fixed" else "difuso")]["mean_pct"], color=color, lw=0.7, ls=":")
ax.axhline(0, color="k", lw=0.8)
ax.set_xticks(x)
ax.set_xticklabels([f"{r['ns']}/{r['ew']}" for r in rows], rotation=70, fontsize=5.5, ha="right")
ax.set_ylabel("réplica − publicado (%)", fontsize=7)
ax.tick_params(axis="y", labelsize=7)
ax.legend(fontsize=6.5, loc="lower left", frameon=False)
ax.set_title("Error relativo con IC 95 % (líneas punteadas: sesgo medio)", fontsize=6.5)
ax.grid(alpha=0.25)
fig.tight_layout(pad=0.3)
fig.savefig("articulo_ieee/figures/fig_incertidumbre.png", dpi=300)
print("guardado articulo_ieee/figures/fig_incertidumbre.png")
