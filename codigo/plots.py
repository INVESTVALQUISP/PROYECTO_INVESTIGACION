"""
plots.py
================================================================================
Genera las figuras del paper de Pappis & Mamdani (1977):

  Fig. 2 : Funciones de pertenencia borrosa definidas sobre el TIEMPO
           (reproduce la Fig. 2 del paper).
  Fig. 3 : Funciones de pertenencia agregadas del algoritmo difuso
           (intervencion 2 / 17 s, ejemplo trabajado de la pags. 7).
  Fig. 4 : Tabla VIII: retardo del controlador difuso (simulado) frente al
           ciclo fijo simulado y a los valores publicados.

Requiere matplotlib:  pip install matplotlib
El backend es 'Agg' (headless), asi que funciona en VS Code sin ventana grafica;
las imagenes se guardan en la carpeta 'figures/'.
"""

import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import os
import numpy as np
import fuzzy_logic as fl
import paper_data as pdta


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


# ---------------------------------------------------------------------------
# Fig. 2 - Funciones de pertenencia sobre el TIEMPO
# ---------------------------------------------------------------------------
def plot_membership_time(outdir="figures"):
    plt = _plt()
    os.makedirs(outdir, exist_ok=True)
    t = np.arange(1, 11)
    fig, ax = plt.subplots(figsize=(7, 4))
    for label, mu in fl.MU_TIME.items():
        ax.plot(t, mu, marker="o", label=label)
    ax.set_xticks(t)
    ax.set_xlabel("Tiempo / extension (s)")
    ax.set_ylabel("Grado de pertenencia $\\mu$")
    ax.set_title("Fig. 2 - Conjuntos borrosos sobre TIEMPO (Pappis & Mamdani 1977)")
    ax.legend(title="etiqueta")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    path = os.path.join(outdir, "fig2_time_membership.png")
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Bonus: funciones de pertenencia sobre ARRIBOS y COLAS (Tablas III y IV)
# ---------------------------------------------------------------------------
def plot_membership_arrivals(outdir="figures"):
    plt = _plt()
    os.makedirs(outdir, exist_ok=True)
    a = np.arange(1, 11)
    fig, ax = plt.subplots(figsize=(7, 4))
    for label, mu in fl.MU_ARR.items():
        ax.plot(a, mu, marker="o", label=label)
    ax.set_xticks(a)
    ax.set_xlabel("Arribos (veh en 10 s)")
    ax.set_ylabel("Grado de pertenencia $\\mu$")
    ax.set_title("Funciones de pertenencia sobre ARRIBOS (Tabla III)")
    ax.legend(ncol=2)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    path = os.path.join(outdir, "fig_membership_arrivals.png")
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def plot_membership_queues(outdir="figures"):
    plt = _plt()
    os.makedirs(outdir, exist_ok=True)
    q = np.arange(4, 33)
    fig, ax = plt.subplots(figsize=(8, 4))
    for label, mu in fl.MU_QUEUE.items():
        ax.plot(q, mu, label=label)
    ax.set_xlabel("Cola (veh)")
    ax.set_ylabel("Grado de pertenencia $\\mu$")
    ax.set_title("Funciones de pertenencia sobre COLAS (Tabla IV)")
    ax.legend(ncol=3)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    path = os.path.join(outdir, "fig_membership_queues.png")
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Fig. 3 - Funciones de pertenencia agregadas del algoritmo difuso
#          (intervencion 2 / 17 s, ejemplo trabajado de la pags. 7)
# ---------------------------------------------------------------------------
def plot_decision_curve(outdir="figures"):
    plt = _plt()
    os.makedirs(outdir, exist_ok=True)
    # Ejemplo del paper (pag. 7): brazo N-S con derecho de paso, cola E-W = 5.
    x = [0, 1, 0, 1, 1, 1, 1, 0, 0, 1]   # arribos N-S (cruzan el punto critico)
    xp = [0, 1, 0, 0, 1, 0, 0, 1, 0, 0]  # arribos E-W (se suman a la cola)
    q_cross = 5
    rules = fl.RULES[17]
    per_rule = fl.fuzzy_decision_per_rule(x, xp, q_cross, rules,
                                          a_mode="arrivals", q_mode="predicted")
    agg = per_rule.max(axis=0)

    e = np.arange(1, 11)
    fig, ax = plt.subplots(figsize=(7, 4))
    styles = ["-", "--", ":", "-.", (0, (3, 1, 1, 1)), (0, (5, 2))]
    for r, (T, A, Q, E) in enumerate(rules):
        ax.plot(e, per_rule[r, 1:11], linestyle=styles[r % len(styles)],
                alpha=0.55, label=f"{T} / {A} / {Q}")
    ax.plot(e, agg[1:11], color="k", marker="o", linewidth=2.5,
            label="ALGORITMO (agregado)")
    ax.axhline(0.5, color="red", linestyle="--", alpha=0.6,
               label="umbral 0.5")
    ax.set_xticks(e)
    ax.set_xlabel("Extension del verde e (s)")
    ax.set_ylabel("Grado de confianza")
    ax.set_title("Fig. 3 - Algoritmo difuso agregado (intervencion 2, 17 s)\n"
                 "Ejemplo del paper: seleccion e* = 10 s")
    ax.set_ylim(-0.02, 1.25)
    ax.legend(fontsize=7.5, loc="upper left", ncol=2)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    path = os.path.join(outdir, "fig3_decision_curve.png")
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Fig. 4 - Tabla VIII: replica vs. paper
# ---------------------------------------------------------------------------
def plot_delay_comparison(rows, outdir="figures", name="calibrada",
                          fname="fig4_delay_comparison.png"):
    """rows: lista de dicts (ns, ew, fixed, fuzzy) de resultados/resultados_oficiales.json."""
    plt = _plt()
    os.makedirs(outdir, exist_ok=True)
    labels = [f"{r['ns']}/{r['ew']}" for r in rows]
    fixed = [r["fixed"] for r in rows]
    fuzzy = [r["fuzzy"] for r in rows]
    paper_fz = [pdta.TABLE_VIII[(r["ns"], r["ew"])][1] for r in rows]
    paper_fx = [pdta.TABLE_VIII[(r["ns"], r["ew"])][0] for r in rows]

    x = np.arange(len(labels))
    w = 0.27
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(x - w, fixed, w, label="Ciclo fijo optimo (simulado)", color="#4C72B0")
    ax.bar(x, fuzzy, w, label=f"Difuso (simulado, lectura {name})", color="#DD8452")
    ax.bar(x + w, paper_fz, w, label="Difuso (paper, Tabla VIII)", color="#55A868")
    ax.plot(x, paper_fx, "k_", markersize=14, label="Vehiculo-actuado (paper)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_xlabel("Caudal N-S / E-W (veh/h)")
    ax.set_ylabel("Retardo medio por vehiculo (s)")
    ax.set_title("Fig. 4 - Tabla VIII: replica vs. paper (20 replicas x 7200 s)")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    ax.set_ylim(0, max(max(fixed), max(fuzzy), max(paper_fx)) * 1.1)
    fig.tight_layout()
    path = os.path.join(outdir, fname)
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
def plot_all(results_json="resultados/resultados_oficiales.json", outdir="figures"):
    """Genera las figuras. La Fig. 4 usa los resultados oficiales guardados."""
    import json
    paths = [
        plot_membership_time(outdir),
        plot_membership_arrivals(outdir),
        plot_membership_queues(outdir),
        plot_decision_curve(outdir),
    ]
    if os.path.exists(results_json):
        res = json.load(open(results_json))
        paths.append(plot_delay_comparison(res["table_VIII"]["calibrada"], outdir, "calibrada"))
        if "literal" in res["table_VIII"]:
            paths.append(plot_delay_comparison(res["table_VIII"]["literal"], outdir, "literal",
                                               "fig4b_delay_comparison_literal.png"))
    return paths


if __name__ == "__main__":
    for p in plot_all():
        print("guardado:", p)
