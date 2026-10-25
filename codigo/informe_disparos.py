"""
informe_disparos.py
================================================================================
Corre la simulacion (sin ventana) y deja como resultado, en la carpeta salidas/:

  disparos_reglas.csv     una fila por (decision, regla): activacion y si DISPARA
  resumen_disparos.csv    por regla: veces activada y veces que disparo
  informe_disparos.png    figura de una pagina: reglas usadas, disparos acumulados,
                          linea de tiempo de las decisiones y retardo d_m(t)

Definiciones (inferencia min-max de Mamdani, pag. 6 del paper):
  * ACTIVACION de una regla = max sobre e de min(mu_T(e), mu_mt(A), mu_lt(Q), mu_E(e)).
  * DISPARO = la regla cuya contribucion en la extension elegida e* iguala el grado
    maximo, es decir, la que "gana" la decision. Un corte del verde (todo < 0.5)
    no tiene regla ganadora.

Uso:
  python informe_disparos.py                              # 720/2160 veh/h, 1800 s
  python informe_disparos.py --ns 1080 --ew 1800 --seconds 3600 --seed 4
  python informe_disparos.py --mode literal               # lectura literal del ejemplo
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import argparse
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import sim_engine as se

COLORS = {7: "#2b6cb0", 17: "#2f855a", 27: "#c05621", 37: "#6b46c1", 47: "#b83280"}


def run(ns, ew, seconds, seed, mode):
    cfg = se.SimConfig(lam_ns=ns / 3600.0, lam_ew=ew / 3600.0, seed=seed, duration=seconds, mode=mode)
    sim = se.StepSim(cfg)
    dm_t = []
    while not sim.done:
        st = sim.step()
        dm_t.append(st.dm)
    return cfg, sim, np.array(dm_t)


def summarize(cfg, sim):
    counts = {}
    for k in sorted(cfg.rules):
        for i, r in enumerate(cfg.rules[k]):
            counts[(k, i)] = dict(regla=f"{k}s-R{i + 1}", texto=se.rule_text(r), activaciones=0, disparos=0)
    for _, _, d in sim.decisions:
        for i, a in enumerate(d.activation):
            if a > 0:
                counts[(d.intervention, i)]["activaciones"] += 1
        for i in d.winners:
            counts[(d.intervention, i)]["disparos"] += 1
    return counts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ns", type=int, default=720, help="flujo N-S (veh/h)")
    ap.add_argument("--ew", type=int, default=2160, help="flujo E-W (veh/h)")
    ap.add_argument("--seconds", type=int, default=1800)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--mode", choices=["capacity", "literal"], default="capacity",
                    help="capacity = lectura calibrada; literal = ejemplo pág. 7")
    ap.add_argument("--out", default="salidas")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    cfg, sim, dm_t = run(args.ns, args.ew, args.seconds, args.seed, args.mode)
    rows = sim.firing_rows()
    with open(os.path.join(args.out, "disparos_reglas.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    counts = summarize(cfg, sim)
    with open(os.path.join(args.out, "resumen_disparos.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["regla", "texto", "activaciones", "disparos"])
        w.writeheader(); w.writerows(counts.values())

    n_dec = len(sim.decisions)
    cuts = sum(d.cut for _, _, d in sim.decisions)
    print(f"Simulación: N-S {args.ns} / E-W {args.ew} veh/h, {args.seconds} s, semilla {args.seed}, "
          f"lectura {'calibrada' if args.mode == 'capacity' else 'literal'}")
    print(f"d_m final = {sim.dm:.2f} s/veh · decisiones = {n_dec} · cortes del verde = {cuts} · "
          f"extensiones = {n_dec - cuts}\n")
    print(f"{'regla':8s} {'activ.':>6s} {'disp.':>6s}  texto")
    for c in counts.values():
        print(f"{c['regla']:8s} {c['activaciones']:6d} {c['disparos']:6d}  {c['texto']}")

    # ---------------------------------------------------------------- figura
    fig = plt.figure(figsize=(15, 9.2))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.15, 1.0], hspace=0.34, wspace=0.22,
                          left=0.30, right=0.985, top=0.875, bottom=0.07)
    fig.suptitle(f"Reglas usadas y disparos de la simulación · N-S {args.ns} / E-W {args.ew} veh/h · "
                 f"{args.seconds} s · semilla {args.seed} · d_m = {sim.dm:.2f} s/veh",
                 fontsize=13, fontweight="bold", y=0.985)
    # (a) reglas + disparos
    ax = fig.add_subplot(gs[:, 0])
    keys = list(counts)
    ys = np.arange(len(keys))[::-1]
    act = np.array([counts[k]["activaciones"] for k in keys], float)
    fire = np.array([counts[k]["disparos"] for k in keys], float)
    col = [COLORS[k[0]] for k in keys]
    ax.barh(ys, act, color=col, alpha=0.25, height=0.8)
    ax.barh(ys, fire, color=col, height=0.55)
    ax.set_yticks(ys)
    ax.set_yticklabels([f"{counts[k]['regla']}  {counts[k]['texto'].replace('si ', '').replace(' entonces ', ' → ')}" for k in keys],
                       fontsize=6.6)
    for j, k in enumerate(keys):
        if k[1] == 0 and j:
            ax.axhline(ys[j] + 0.5, color="#95a5a6", lw=0.6)
        if fire[j]:
            ax.text(fire[j] + 0.3, ys[j], int(fire[j]), va="center", fontsize=7)
    ax.set_xlabel("número de decisiones")
    ax.set_title("(a) Las 25 reglas: activaciones (claro) y disparos (oscuro)", fontsize=10.5, loc="left")
    ax.grid(True, axis="x", lw=0.4, color="#d5dbe0")
    # (b) linea de tiempo de decisiones
    ax = fig.add_subplot(gs[0, 1])
    for t, ph, d in sim.decisions:
        if d.cut:
            ax.scatter(t, 0, marker="x", color="#e74c3c", s=26, zorder=3)
        else:
            w = d.winners[0] if d.winners else 0
            ax.scatter(t, d.e_star, color=COLORS[d.intervention], s=30, zorder=3)
    ax.set_ylabel("extensión elegida e* (s)  ·  × = corte")
    ax.set_xlabel("tiempo (s)")
    ax.set_yticks([0, 2, 4, 6, 8, 10])
    ax.set_title("(b) Decisiones en el tiempo (color = momento de intervención)", fontsize=10.5, loc="left", pad=24)
    for k, c in COLORS.items():
        ax.scatter([], [], color=c, label=f"{k} s")
    ax.legend(ncol=5, fontsize=7.5, loc="lower center", bbox_to_anchor=(0.5, 1.0), frameon=False, title=None)
    ax.grid(True, lw=0.4, color="#d5dbe0")
    # (c) d_m(t)
    ax = fig.add_subplot(gs[1, 1])
    ax.plot(np.arange(len(dm_t)), dm_t, color="#2c3e50", lw=1.3)
    ax.set_xlabel("tiempo (s)"); ax.set_ylabel("$d_m$ (s/veh)")
    ax.set_title("(c) Retardo medio acumulado", fontsize=10.5, loc="left")
    ax.grid(True, lw=0.4, color="#d5dbe0")
    path = os.path.join(args.out, "informe_disparos.png")
    fig.savefig(path, dpi=130)
    print(f"\nGuardado en {args.out}/: disparos_reglas.csv, resumen_disparos.csv, informe_disparos.png")


if __name__ == "__main__":
    main()
