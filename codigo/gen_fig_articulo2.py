"""
gen_fig_articulo2.py
================================================================================
Figuras de resultados del articulo IEEE (segundo avance), al ancho final de pagina
(7.16 in a dos columnas, 3.45 in una columna). Salida: articulo_ieee/figures/

  fig_validacion_curvas.png  curvas del codigo vs valores impresos (Tablas II, IV, V, VI)
  fig_tabla7.png             ejemplo de las pags. 7-8: aporte de cada regla y agregado
  fig_tabla8.png             Tabla VIII: replica vs paper (16 caudales)
  fig_dispersion.png         replica vs paper: Tabla I, Tabla VIII calibrada y literal
  fig_auditoria.png          error de las 8 lecturas de A y Q
  fig_disparos.png           disparos por regla y decisiones en una simulacion
  (fig_sim_*.png y el cuadro del simulador: ver gen_fig_articulo4.py)
Uso:  python gen_fig_articulo2.py
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import csv
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import fuzzy_logic as fl
import paper_data as pdta
import sim_engine as se
import traffic_model as tm
from intersection_view import IntersectionView

OUT = "articulo_ieee/figures"
W, C = 7.16, 3.45
plt.rcParams.update({"font.size": 7, "axes.titlesize": 7.5, "axes.labelsize": 7, "xtick.labelsize": 6.5,
                     "ytick.labelsize": 6.5, "legend.fontsize": 6.3, "axes.linewidth": 0.6})
BL, OR, GR, RD, PU = "#2b6cb0", "#c05621", "#2f855a", "#c53030", "#6b46c1"
INT_COL = {7: "#2b6cb0", 17: "#2f855a", 27: "#c05621", 37: "#6b46c1", 47: "#b83280"}
res = json.load(open("resultados/resultados_oficiales.json"))
cal, lit = res["table_VIII"]["calibrada"], res["table_VIII"]["literal"]

# ---------------------------------------------------------------- 1. curvas vs paper
T, Q = np.arange(1, 11), np.arange(4, 33)
fig, axs = plt.subplots(2, 2, figsize=(W, 4.3))


def panel(ax, xs, items, ref, title, xl):
    worst = 0.0
    for i, (n, v) in enumerate(items):
        ax.plot(xs, v, color=plt.cm.tab10(i), lw=1.0, marker="o", ms=2.3, label=n)
        r = ref[n if n in ref else n.split("(")[-1].rstrip(")")]
        ax.plot(xs, r, "kx", ms=4.5, mew=0.8)
        worst = max(worst, float(np.max(np.abs(np.array(v) - np.array(r)))))
    ax.plot([], [], "kx", ms=4.5, mew=0.8, label="impreso")
    ax.set_title(f"{title}\nmáx |código − paper| = {worst:.3f}")
    ax.set_xlabel(xl); ax.set_ylabel("grado $\\mu$")
    ax.set_ylim(-0.05, 1.55); ax.set_yticks([0, .5, 1.0]); ax.grid(True, lw=0.3, color="#d5dbe0")
    ax.legend(loc="upper center", ncol=4, frameon=False, handlelength=1.2, columnspacing=0.7)


panel(axs[0, 0], T, list(fl.MU_TIME.items()), pdta.TABLE_II, "(a) Tiempo / extensión (Tabla II)", "$t$ (s)")
panel(axs[0, 1], T, [(f"mt({b})", [fl.mt_arr(b, a) for a in T]) for b in pdta.TABLE_V], pdta.TABLE_V, "(b) «Más que» (Tabla V)", "$a$ (veh)")
panel(axs[1, 0], Q, list(fl.MU_QUEUE.items()), pdta.TABLE_IV, "(c) Colas (Tabla IV)", "$q$ (veh)")
panel(axs[1, 1], Q, [(f"lt({b})", [fl.lt_queue(b, q) for q in Q]) for b in pdta.TABLE_VI], pdta.TABLE_VI, "(d) «Menos que» (Tabla VI)", "$q$ (veh)")
fig.tight_layout(pad=0.4)
fig.savefig(f"{OUT}/fig_validacion_curvas.png", dpi=300); plt.close(fig)

# ---------------------------------------------------------------- 2. ejemplo Tabla VII
per = fl.fuzzy_decision_per_rule(pdta.EXAMPLE_X, pdta.EXAMPLE_XP, pdta.EXAMPLE_Q, fl.RULES[17],
                                 a_mode="arrivals", q_mode="predicted")[:, 1:]
agg = per.max(axis=0)
fig, ax = plt.subplots(figsize=(C, 2.5))
e = np.arange(1, 11)
names = ["R1 veryshort", "R2 short", "R3 medium", "R4 long", "R5 verylong"]
for i in range(5):
    ax.plot(e, per[i], lw=0.8, marker="o", ms=2, alpha=0.8, label=names[i])
ax.plot(e, agg, "k-", lw=1.8, marker="s", ms=3.2, label="algoritmo (máx.)")
ax.axhline(0.5, color=RD, ls="--", lw=0.8)
ax.annotate("$e^*=10$ s", xy=(10, agg[-1]), xytext=(7.6, 0.93), fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.6))
ax.set_xticks(e); ax.set_ylim(-0.03, 1.05); ax.set_xlabel("extensión candidata $e$ (s)"); ax.set_ylabel("grado de confianza")
ax.grid(True, lw=0.3, color="#d5dbe0"); ax.legend(ncol=2, loc="upper left", frameon=False, fontsize=5.8)
fig.tight_layout(pad=0.3); fig.savefig(f"{OUT}/fig_tabla7.png", dpi=300); plt.close(fig)

# ---------------------------------------------------------------- 3. Tabla VIII
labels = [f"{r['ns']}/{r['ew']}" for r in cal]
x = np.arange(16); w = 0.27
fig, ax = plt.subplots(figsize=(W, 2.7))
ax.bar(x - w, [r["fixed"] for r in cal], w, color=BL, label="ciclo fijo óptimo (réplica)")
ax.bar(x, [r["fuzzy"] for r in cal], w, color=OR, label="difuso (réplica, lectura calibrada)")
ax.bar(x + w, [pdta.TABLE_VIII[(r["ns"], r["ew"])][1] for r in cal], w, color=GR, label="difuso (paper, Tabla VIII)")
ax.plot(x, [pdta.TABLE_VIII[(r["ns"], r["ew"])][0] for r in cal], "k_", ms=9, mew=1.2, label="vehículo-actuado (paper)")
ax.set_xticks(x); ax.set_xticklabels(labels, rotation=45, ha="right")
ax.set_xlabel("caudal N–S / E–W (veh/h)"); ax.set_ylabel("retardo medio $d_m$ (s/veh)")
ax.grid(True, axis="y", lw=0.3, color="#d5dbe0"); ax.legend(loc="upper left", frameon=False, ncol=1)
fig.tight_layout(pad=0.3); fig.savefig(f"{OUT}/fig_tabla8.png", dpi=300); plt.close(fig)

# ---------------------------------------------------------------- 4. dispersion
fig, axs = plt.subplots(1, 3, figsize=(W, 2.5))


def scat(ax, px, py, lim, label, color, log=False):
    ax.scatter(px, py, s=9, color=color, label=label, edgecolors="none")
    lo, hi = lim
    ax.plot([lo, hi], [lo, hi], "k-", lw=0.7)
    if not log:
        ax.fill_between([lo, hi], [0.9 * lo, 0.9 * hi], [1.1 * lo, 1.1 * hi], color="#cfd8e6", alpha=0.6, lw=0)
    ax.set_xlim(lo, hi); ax.set_ylim(lo, hi); ax.set_aspect("equal"); ax.grid(True, lw=0.3, color="#d5dbe0")
    ax.set_xlabel("paper (s/veh)"); ax.set_ylabel("réplica (s/veh)")


t1 = res["table_I"]
p1 = [pdta.TABLE_I[(r["ns"], r["ew"])] for r in t1]
scat(axs[0], [a for a, b in p1], [r["sim"] for r in t1], (5, 33), "simulación", BL)
axs[0].scatter([b for a, b in p1], [r["formula"] for r in t1], s=11, facecolors="none", edgecolors=OR, linewidths=0.7, label="fórmula")
axs[0].set_title("(a) Tabla I"); axs[0].legend(loc="upper left", frameon=False)
pz = [pdta.TABLE_VIII[(r["ns"], r["ew"])][1] for r in cal]
scat(axs[1], pz, [r["fuzzy"] for r in cal], (4, 26), "calibrada", GR); axs[1].set_title("(b) Tabla VIII, calibrada")
scat(axs[2], pz, [r["fuzzy"] for r in lit], (3, 900), "literal", RD, log=True)
axs[2].set_xscale("log"); axs[2].set_yscale("log"); axs[2].set_title("(c) Tabla VIII, literal (log)")
fig.tight_layout(pad=0.3); fig.savefig(f"{OUT}/fig_dispersion.png", dpi=300); plt.close(fig)

# ---------------------------------------------------------------- 5. auditoria de lecturas
aud = json.load(open("resultados/fidelity_audit.json"))["variants"]
ab = {"arrivals": "arr", "crossing": "cruce", "predicted": "pred", "current": "act", "total": "total", "green_arrivals": "verde"}
labs = [f"{ab[v['a_mode']]} / {ab[v['q_mode']]} / {ab[v['queue_source']]}" for v in aud]
vals = [v["mean_err"] for v in aud]
order = np.argsort(vals)[::-1]
fig, ax = plt.subplots(figsize=(C, 2.6))
cols = [GR if (aud[i]["a_mode"], aud[i]["q_mode"], aud[i]["queue_source"]) == ("crossing", "current", "green_arrivals") else
        (RD if (aud[i]["a_mode"], aud[i]["q_mode"], aud[i]["queue_source"]) == ("arrivals", "predicted", "total") else "#8fa3b8") for i in order]
ax.barh(range(8), [vals[i] for i in order], color=cols)
ax.set_yticks(range(8)); ax.set_yticklabels([labs[i] for i in order], fontsize=6.2)
ax.set_xscale("log"); ax.set_xlabel("error medio frente a la Tabla VIII (%)")
for j, i in enumerate(order):
    ax.text(vals[i] * 1.07, j, f"{vals[i]:.1f}", va="center", fontsize=6)
ax.set_xlim(5, 1500); ax.grid(True, axis="x", lw=0.3, color="#d5dbe0")
ax.text(0.99, 0.02, "A / Q evaluada / cola Q", transform=ax.transAxes, ha="right", fontsize=5.8, color="#555")
fig.tight_layout(pad=0.3); fig.savefig(f"{OUT}/fig_auditoria.png", dpi=300); plt.close(fig)

# ---------------------------------------------------------------- 6. disparos (simulacion 720/2160, 1800 s)
rows = list(csv.DictReader(open("muestras/disparos_reglas.csv", encoding="utf-8-sig")))
rules = []
for r in rows:
    if r["regla"] not in [x[0] for x in rules]:
        rules.append((r["regla"], int(r["intervencion"])))
fire = {k: 0 for k, _ in rules}; act = {k: 0 for k, _ in rules}
estar = {}
for r in rows:
    fire[r["regla"]] += int(r["dispara"]); act[r["regla"]] += float(r["activacion"]) > 0
    estar[r["t"]] = int(r["e_star"])
fig, axs = plt.subplots(1, 2, figsize=(W, 3.2), gridspec_kw=dict(width_ratios=[1.45, 1]))
ax = axs[0]
ys = np.arange(len(rules))[::-1]
ax.barh(ys, [act[k] for k, _ in rules], color=[INT_COL[i] for _, i in rules], alpha=0.28, height=0.8)
ax.barh(ys, [fire[k] for k, _ in rules], color=[INT_COL[i] for _, i in rules], height=0.55)
ax.set_yticks(ys); ax.set_yticklabels([k.replace("s-", " s · ") for k, _ in rules], fontsize=5.4)
for j, (k, i) in enumerate(rules):
    if fire[k]:
        ax.text(fire[k] + 0.4, ys[j], str(fire[k]), va="center", fontsize=5.4)
ax.set_xlabel("decisiones"); ax.set_title("(a) Activaciones (claro) y disparos (oscuro)")
ax.grid(True, axis="x", lw=0.3, color="#d5dbe0")
ax = axs[1]
vals = np.array(list(estar.values()))
cnt = [int((vals == v).sum()) for v in range(0, 11)]
ax.bar(range(0, 11), cnt, color=["#c53030"] + ["#2b6cb0"] * 10)
ax.set_xticks(range(0, 11)); ax.set_xticklabels(["corte"] + [str(i) for i in range(1, 11)], fontsize=5.6)
ax.set_xlabel("extensión elegida $e^*$ (s)"); ax.set_ylabel("decisiones"); ax.set_title(f"(b) {len(vals)} decisiones")
ax.grid(True, axis="y", lw=0.3, color="#d5dbe0")
fig.tight_layout(pad=0.3); fig.savefig(f"{OUT}/fig_disparos.png", dpi=300); plt.close(fig)

# ---------------------------------------------------------------- 7. (el cuadro y los apartados del simulador los genera gen_fig_articulo4.py)

# ---------------------------------------------------------------- 8. linea de tiempo de una fase
from matplotlib.patches import Rectangle
fig, ax = plt.subplots(figsize=(W, 1.55))
ax.set_xlim(-1, 72); ax.set_ylim(-1.7, 3.3); ax.axis("off")
ax.add_patch(Rectangle((0, 0), 7, 1, fc="#bcd4ee", ec="k", lw=0.5))
ax.text(3.5, 0.5, "7 s\nmínimo", ha="center", va="center", fontsize=5.6)
for k, t0 in enumerate([7, 17, 27, 37, 47]):
    ax.add_patch(Rectangle((t0, 0), 10, 1, fc="#d9f5e3" if k % 2 == 0 else "#bfe8cf", ec="k", lw=0.5))
    ax.text(t0 + 5, 0.5, "$e^*\\leq 10$ s", ha="center", va="center", fontsize=5.8)
    ax.plot([t0, t0], [1, 1.9], color=INT_COL[[7, 17, 27, 37, 47][k]], lw=1.0)
    ax.text(t0, 2.05, f"intervención\n{t0} s", ha="center", va="bottom", fontsize=5.8, color=INT_COL[t0])
ax.add_patch(Rectangle((57, 0), 3, 1, fc="#f5b82e", ec="k", lw=0.5)); ax.text(58.5, 0.5, "ámbar", ha="center", va="center", fontsize=5.2)
ax.add_patch(Rectangle((60, 0), 2, 1, fc="#e74c3c", ec="k", lw=0.5)); ax.text(61, 0.5, "rojo", ha="center", va="center", fontsize=5.2, color="w")
ax.annotate("", xy=(0, -0.55), xytext=(57, -0.55), arrowprops=dict(arrowstyle="<->", lw=0.7))
ax.text(28.5, -0.95, "verde efectivo: $7+\\sum e^*\\leq 57$ s", ha="center", fontsize=6.3)
ax.annotate("", xy=(57, -0.55), xytext=(62, -0.55), arrowprops=dict(arrowstyle="<->", lw=0.7, color="#555"))
ax.text(66.5, -0.95, "tiempo perdido\n(5 s por cambio)", ha="center", va="center", fontsize=5.6, color="#555")
fig.tight_layout(pad=0.2); fig.savefig(f"{OUT}/fig_fase.png", dpi=300); plt.close(fig)

# ---------------------------------------------------------------- 9. mejora porcentual
lab = [f"{r['ns']}/{r['ew']}" for r in cal]
mej_r = [r["improvement"] for r in cal]
mej_p = [100 * (pdta.TABLE_VIII[(r["ns"], r["ew"])][0] - pdta.TABLE_VIII[(r["ns"], r["ew"])][1]) / pdta.TABLE_VIII[(r["ns"], r["ew"])][0] for r in cal]
fig, ax = plt.subplots(figsize=(C, 2.5))
x = np.arange(16)
ax.bar(x - 0.2, mej_r, 0.4, color=OR, label="réplica")
ax.bar(x + 0.2, mej_p, 0.4, color=GR, label="artículo")
ax.set_xticks(x); ax.set_xticklabels(lab, rotation=60, ha="right", fontsize=5.4)
ax.set_ylabel("mejora sobre el ciclo fijo (%)"); ax.grid(True, axis="y", lw=0.3, color="#d5dbe0")
ax.legend(frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, 1.12))
fig.tight_layout(pad=0.3); fig.savefig(f"{OUT}/fig_mejora.png", dpi=300); plt.close(fig)
print("figuras generadas en", OUT)
