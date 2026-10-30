"""
gen_fig_articulo4.py
================================================================================
Figuras del simulador para el articulo, cada apartado en una figura aparte, todas del
MISMO instante de la simulacion (720/2160 veh/h, semilla 1, t = 118 s), mas el cuadro
completo. Salida: articulo_replica/figures/

  fig_sim_calle.png      la calle: cruce, vehiculos, semaforos de tres luces y colas
  fig_sim_reglas.png     panel de reglas de la intervencion con su activacion y la regla que dispara
  fig_sim_decision.png   vector de grados grade(e), umbral 0.5 y extension elegida
  fig_sim_disparos.png   disparos acumulados (oscuro) y activaciones (claro) de las 25 reglas
  fig_sim_traza.png      retardo medio d_m en el tiempo, con extensiones y cortes
  fig_sim_registro.png   registro de decisiones (tiempo, brazo, e*, regla que dispara)
  fig_simulador_cuadro.png  cuadro completo de las figuras de matplotlib (sin la barra de controles)
La captura de la ventana (con la barra de controles) se hace con captura_ventana.py.
Uso:  python codigo/gen_fig_articulo4.py
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
from types import SimpleNamespace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox

import sim_engine as se
from intersection_view import IntersectionView
from simulador_gui import decision_line

OUT = "articulo_replica/figures"
T_STOP = 119          # pasos simulados (t = 118 s: la ultima decision es e* = 4 s por la regla R2 de 47 s)

cfg = se.SimConfig(lam_ns=720 / 3600, lam_ew=2160 / 3600, seed=1, duration=3600)   # misma duracion que la ventana (la duracion cambia las llegadas)
sim = se.StepSim(cfg)
fig = plt.figure(figsize=(14.6, 8.2), dpi=100)
view = IntersectionView(fig, rules=cfg.rules)
view.reset()
view.sub.set_text("N-S 720 veh/h · E-W 2160 veh/h · lectura calibrada · semilla 1")
for n in range(T_STOP):
    st = sim.step()
    view.advance(st)
    if n >= T_STOP - 3:
        for _ in range(3):
            view.draw_frame(1 / 3)
view.draw_frame(0.0)
fig.canvas.draw()
rend = fig.canvas.get_renderer()
print(f"t = {st.t} s, ultima decision: {decision_line(st) if st.decision else '-'}")

fig.savefig(f"{OUT}/fig_simulador_cuadro.png", dpi=150)
# en la figura de la calle el encabezado va sobre el cruce, para que no tape a los autos de la cola
view.hdr.set_position((50, 102.0))
view.hdr.set_va("bottom")
view.hdr.set_bbox(dict(fc="none", ec="none"))
fig.canvas.draw()
PAD = 0.06   # pulgadas
for name, ax in (("calle", view.ax), ("reglas", view.ax_rules), ("decision", view.ax_grade),
                 ("disparos", view.ax_fire), ("traza", view.axq)):
    bb = ax.get_tightbbox(rend).transformed(fig.dpi_scale_trans.inverted())
    bb = Bbox.from_extents(max(bb.x0, 0) - PAD, bb.y0 - PAD, bb.x1 + PAD, bb.y1 + PAD)
    fig.savefig(f"{OUT}/fig_sim_{name}.png", dpi=250, bbox_inches=bb)
    print("guardado", name, f"{bb.width:.2f} x {bb.height:.2f} in")
plt.close(fig)

# ---- registro de decisiones (equivale al cuadro de texto de la ventana) ----
lines = []
for t, phase, d in sim.decisions:
    lines.append(decision_line(SimpleNamespace(t=t, phase=phase, decision=d)))
shown = lines[-14:]
fig, ax = plt.subplots(figsize=(4.4, 0.19 * (len(shown) + 2.2)))
ax.axis("off")
ax.text(0, 1, "Decisiones y regla que dispara", fontsize=8.6, fontweight="bold", va="top", color="#2c3e50",
        transform=ax.transAxes)
ax.text(0, 0.90, "\n".join(shown), family="monospace", fontsize=7.6, va="top", linespacing=1.45,
        transform=ax.transAxes)
fig.savefig(f"{OUT}/fig_sim_registro.png", dpi=250, bbox_inches="tight", pad_inches=0.05)
print(len(lines), "decisiones en total;", len(shown), "en el registro")
