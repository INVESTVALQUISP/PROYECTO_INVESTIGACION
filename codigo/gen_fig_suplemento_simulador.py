"""
gen_fig_suplemento_simulador.py
================================================================================
Figuras del simulador interactivo para el material suplementario del articulo de la mejora
(articulo/suplemento.tex): cada apartado de la pantalla en una figura aparte, dibujado con el
MISMO codigo de la ventana (intersection_view.IntersectionView y sim_engine.StepSim), en el
mismo instante y con las mismas llegadas que la captura de la ventana (captura_ventana_suplemento.py).

Escenario: 720/2160 veh/h, semilla 1, duracion 3600 s (los valores por defecto de la ventana).

Con FLC-O (t = 118 s, el verde E-W SIGUE; y t = 139 s, FLC-O CAMBIA de fase):
  fig_sup_calle.png            la calle: cruce, autos, semaforos de tres luces, colas y encabezado
  fig_sup_entradas.png         entradas G, R y V sobre sus conjuntos difusos
  fig_sup_salida.png           salida u en t = 118 s (sigue)   fig_sup_salida_cambia.png  en t = 139 s (cambia)
  fig_sup_fuerza.png           fuerza de las 27 reglas en t = 118 s
  fig_sup_fuerza_cambia.png    fuerza de las 27 reglas en t = 139 s
  fig_sup_traza.png            retardo medio d_m en el tiempo, con la curva del controlador de 1977 (mismas llegadas)
  fig_sup_explicacion.png      texto «¿Que decidio el controlador y por que?» en t = 118 s
  fig_sup_registro.png         registro «Decisiones y regla que dispara» hasta t = 139 s
Con Pappis y Mamdani (1977), t = 118 s (intervencion de 47 s, dispara R2, e* = 4 s):
  fig_sup_p_reglas.png         las 5 reglas de la intervencion con su activacion y la que dispara
  fig_sup_p_grados.png         grado de cada extension posible, umbral 0.5 y extension elegida
  fig_sup_p_disparos.png       disparos acumulados de las 25 reglas
  fig_sup_p_traza.png          retardo medio d_m con extensiones y cortes, y la curva de FLC-O (mismas llegadas)
  fig_sup_p_explicacion.png    texto explicativo de la decision
  fig_sup_p_registro.png       registro de decisiones
Diagramas de bloques (lazo de control completo):
  fig_sup_bloques_flco.png     FLC-O: detectores, entradas G/R/V, fuzzificacion, 27 reglas, salida u y decision
  fig_sup_bloques_pappis.png   Pappis y Mamdani (1977): sensores, fuzzificacion, 25 reglas min-max y decision
Ademas escribe articulo/sup_simulador_datos.tex con las cifras de esos instantes (macros \\Sim...).

Uso:  python codigo/gen_fig_suplemento_simulador.py
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import textwrap
from types import SimpleNamespace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.transforms import Bbox

import sim_engine as se
from intersection_view import IntersectionView
from simulador_gui import decision_line, NOMBRES

OUT = "articulo/figures"
NS, EW, SEED, DUR = 720, 2160, 1, 3600
T_A = 118          # instante principal (FLC-O sigue; Pappis decide en la intervencion de 47 s)
T_B = 139          # FLC-O cambia de fase
CALIBRADA = dict(a_mode="crossing", q_mode="current", predicted_q=False)   # lectura de A y Q del articulo (Sec. IV-B)
PAD = 0.06         # pulgadas alrededor de cada apartado
DPI = 250


def cfg(ctrl):
    return se.SimConfig(lam_ns=NS / 3600.0, lam_ew=EW / 3600.0, seed=SEED, duration=DUR, controller=ctrl, **CALIBRADA)


def guardar_eje(fig, rend, ax, nombre, extra=()):
    """Guarda un apartado (un eje y, opcionalmente, otros ejes que van con el) en su propio PNG."""
    bbs = [a.get_tightbbox(rend) for a in (ax,) + tuple(extra)]
    bb = Bbox.union(bbs).transformed(fig.dpi_scale_trans.inverted())
    bb = Bbox.from_extents(max(bb.x0, 0) - PAD, bb.y0 - PAD, bb.x1 + PAD, bb.y1 + PAD)
    otros = [a for a in fig.axes if a is not ax and a not in extra and a.get_visible()]
    for a in otros:                      # los apartados vecinos no se cuelan en el recorte
        a.set_visible(False)
    fig.savefig(f"{OUT}/{nombre}.png", dpi=DPI, bbox_inches=bb)
    for a in otros:
        a.set_visible(True)
    print("guardado", nombre, f"{bb.width:.2f} x {bb.height:.2f} in")


def texto_png(titulo, texto, nombre, ancho=4.6, mono=False, envolver=70):
    """Dibuja un cuadro de texto de la ventana (explicacion o registro) como figura; el recuadro se ajusta al texto."""
    lineas = []
    for parr in texto.split("\n"):
        lineas += textwrap.wrap(parr, envolver) if not mono else [parr]
    fig, ax = plt.subplots(figsize=(ancho, 0.2 * (len(lineas) + 2.0)))
    ax.axis("off")
    ax.text(0, 1, titulo, fontsize=8.6, fontweight="bold", va="top", color="#2c3e50", transform=ax.transAxes)
    ax.text(0.01, 0.80, "\n".join(lineas), family="monospace" if mono else None, fontsize=7.4, va="top",
            linespacing=1.4, transform=ax.transAxes,
            bbox=dict(boxstyle="square,pad=0.5", fc="white" if mono else "#fffdf0", ec="#b0b7bf", lw=0.8))
    fig.savefig(f"{OUT}/{nombre}.png", dpi=DPI, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    print("guardado", nombre, len(lineas), "lineas")


def correr(ctrl, paradas):
    """Simula con la vista de la ventana hasta cada instante de 'paradas' y llama paradas[t](view, sim, st)."""
    c = cfg(ctrl)
    otro = "pappis" if ctrl == "flco" else "flco"
    sim, ref = se.StepSim(c), se.StepSim(cfg(otro))
    fig = plt.figure(figsize=(14.6, 8.2), dpi=100)
    view = IntersectionView(fig, rules=c.rules, flco=c.flco, max_green=getattr(c, "max_green", 57))
    view.reset()
    if ctrl == "flco":
        view.sub.set_text(f"controlador: FLC-O ({c.flco_model}) · N-S {NS} veh/h · E-W {EW} veh/h · semilla {SEED}")
    else:
        view.sub.set_text(f"reglas: paper · umbral 0.50 · N-S {NS} veh/h · E-W {EW} veh/h · lectura calibrada · semilla {SEED}")
    view.set_reference(NOMBRES[otro] + ", mismas llegadas")
    t_fin = max(paradas)
    st = None
    while st is None or st.t < t_fin:
        st = sim.step()
        view.advance(st, ref_dm=ref.step().dm)
        for _ in range(3):              # como la ventana: los autos se mueven en sub-cuadros de 1/3 s
            view.draw_frame(1 / 3)
        if st.t in paradas:
            view.draw_frame(0.0)
            fig.canvas.draw()
            paradas[st.t](fig, fig.canvas.get_renderer(), view, sim, st)
    plt.close(fig)
    return sim, ref


datos = {}


# ------------------------------------------------------------------ FLC-O
def flco_a(fig, rend, view, sim, st):
    d = st.decision
    datos.update(SimT=st.t, SimVerde="E-W" if st.phase == 1 else "N-S", SimV=d.elapsed, SimG=f"{d.G:.1f}",
                 SimR=f"{d.R:.1f}", SimU=f"{d.u:+.2f}", SimQns=st.q_ns, SimQew=st.q_ew, SimDm=f"{st.dm:.2f}",
                 SimQg=d.q_green, SimQr=d.q_red, SimModelo=sim.cfg.flco_model.replace("_", r"\_"))
    guardar_eje(fig, rend, view.ax_rules, "fig_sup_entradas", extra=tuple(view._fl_insets))
    guardar_eje(fig, rend, view.ax_grade, "fig_sup_salida")
    guardar_eje(fig, rend, view.ax_fire, "fig_sup_fuerza")
    texto_png("¿Qué decidió el controlador y por qué?",
              se.explain_flco(d, st.phase, sim.flco, sim.flco.gmin, sim.cfg.max_green), "fig_sup_explicacion")
    # la calle: el encabezado va sobre el cruce para no tapar los autos de la cola (igual que en la replica)
    pos, va, bbox = view.hdr.get_position(), view.hdr.get_va(), view.hdr.get_bbox_patch()
    view.hdr.set_position((50, 102.0))
    view.hdr.set_va("bottom")
    fig.canvas.draw()
    guardar_eje(fig, rend, view.ax, "fig_sup_calle")
    view.hdr.set_position(pos)
    view.hdr.set_va(va)
    fig.canvas.draw()


def flco_b(fig, rend, view, sim, st):
    d = st.decision
    datos.update(SimTb=st.t, SimVb=d.elapsed, SimGb=f"{d.G:.1f}", SimRb=f"{d.R:.1f}", SimUb=f"{d.u:+.2f}")
    guardar_eje(fig, rend, view.ax_grade, "fig_sup_salida_cambia")
    guardar_eje(fig, rend, view.ax_fire, "fig_sup_fuerza_cambia")
    view.axq.set_xlim(0, 150)            # en la ventana el eje se duplica al pasar de 120 s; aqui se recorta para leerla mejor
    fig.canvas.draw()
    guardar_eje(fig, rend, view.axq, "fig_sup_traza")
    lineas = [decision_line(SimpleNamespace(t=t, phase=ph, decision=dd)) for t, ph, dd in sim.decisions
              if getattr(dd, "kind", "") == "flco" and dd.event]
    datos.update(SimNCambios=len(lineas))
    texto_png("Decisiones y regla que dispara", "\n".join(lineas[-14:]), "fig_sup_registro", ancho=3.6, mono=True)


sim_f, ref_f = correr("flco", {T_A: flco_a, T_B: flco_b})
datos.update(SimDmFin=f"{sim_f.dm:.2f}", SimDmRefFin=f"{ref_f.dm:.2f}")


# ------------------------------------------------------------------ Pappis y Mamdani (1977)
def pappis_a(fig, rend, view, sim, st):
    d = st.decision
    datos.update(SimPInt=d.intervention, SimPEst=d.e_star, SimPGrado=f"{d.grade_max:.2f}",
                 SimPRegla=",".join(f"R{i + 1}" for i in d.winners), SimPV=d.elapsed)
    guardar_eje(fig, rend, view.ax_rules, "fig_sup_p_reglas")
    guardar_eje(fig, rend, view.ax_grade, "fig_sup_p_grados")
    guardar_eje(fig, rend, view.ax_fire, "fig_sup_p_disparos")
    guardar_eje(fig, rend, view.axq, "fig_sup_p_traza")
    texto_png("¿Qué decidió el controlador y por qué?", se.explain_decision(d, st.phase, st.t, sim.cfg.threshold),
              "fig_sup_p_explicacion", envolver=84, ancho=5.4)
    lineas = [decision_line(SimpleNamespace(t=t, phase=ph, decision=dd)) for t, ph, dd in sim.decisions]
    datos.update(SimPNDec=len(lineas))
    texto_png("Decisiones y regla que dispara", "\n".join(lineas[-14:]), "fig_sup_p_registro", ancho=3.6, mono=True)


correr("pappis", {T_A: pappis_a})

# ------------------------------------------------------------------ diagramas de bloques
OR, GR, BL, VI = "#c2410c", "#2f855a", "#2563eb", "#6d28d9"


def bloque(ax, x0, y0, x1, y1, txt, fc, ec, fs=6.4):
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0.2,rounding_size=1", fc=fc, ec=ec, lw=1.1))
    ax.text((x0 + x1) / 2, (y0 + y1) / 2, txt, ha="center", va="center", fontsize=fs, color="#1f2937", linespacing=1.3)


def flecha(ax, x0, y0, x1, y1, col="#333", lw=0.9, ls="-"):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="->", color=col, lw=lw, ls=ls))


def diagrama(nombre, titulo, bloques, salida, semaforo, medidas, ancho=7.16):
    fig, ax = plt.subplots(figsize=(ancho, 2.75))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 42)
    ax.axis("off")
    n = len(bloques)
    x_fin = 77
    w = (x_fin - 3 - 1.6 * (n - 1)) / n
    ax.add_patch(FancyBboxPatch((1, 17), x_fin - 1 + 1, 23, boxstyle="round,pad=0.2,rounding_size=1", fc="none", ec=OR, lw=1, ls="--"))
    ax.text(2.5, 38.3, titulo, fontsize=6.3, color=OR, fontweight="bold", va="center")
    xs = [3 + k * (w + 1.6) for k in range(n)]
    for x, txt in zip(xs, bloques):
        bloque(ax, x, 19.5, x + w, 35, txt, "#ffedd5", OR, 5.6)
    for x in xs[1:]:
        flecha(ax, x - 1.6, 27.2, x, 27.2)
    bloque(ax, 81, 19.5, 99, 35, semaforo, "#dcfce7", GR, 5.8)
    flecha(ax, xs[-1] + w, 27.2, 81, 27.2, GR, 1.6)
    ax.text(79.2, 30.4, salida, fontsize=6.2, color=GR, ha="center", fontweight="bold")
    bloque(ax, 20, 1, 66, 12, "Intersección: llegadas de Bernoulli, colas FIFO,\ndescarga a 1 veh/s, tiempo perdido de 5 s por cambio", "#dbeafe", BL, 6.0)
    bloque(ax, 72, 1, 99, 12, "Retardo medio\n$d_m = D\\,/\\,N$, $D=\\sum_n (Q_{1,n}+Q_{2,n})$", "#e5e7eb", "#4b5563", 5.9)
    flecha(ax, 66, 6.5, 72, 6.5)
    ax.plot([90, 90, 43], [19.5, 15.5, 15.5], color=GR, lw=1.2)
    flecha(ax, 43, 15.5, 43, 12.2, GR, 1.2)
    ax.text(70, 13.9, "fase verde / roja", fontsize=5.8, color=GR, va="center")
    ax.plot([22, 11], [12, 12], color=VI, lw=1, ls="--")
    flecha(ax, 11, 12, 11, 19.5, VI, 1, "--")
    ax.text(12.3, 15.6, medidas, fontsize=5.6, color=VI, va="center")
    fig.tight_layout(pad=0.3)
    fig.savefig(f"{OUT}/{nombre}.png", dpi=300)
    plt.close(fig)
    print("guardado", nombre)


diagrama("fig_sup_bloques_flco", "CONTROLADOR FLC-O (decide cada segundo de verde)",
         ["Detectores\ncolas $Q_g$, $Q_r$ y\nllegadas de los\npróximos 10 s",
          "Entradas (5)\n$G=Q_g+\\sum\\omega_k W_g$\n$R=Q_r+\\sum\\rho_k W_r$\n$V$ = verde transcurrido",
          "Fuzzificación (6)\nRuspini: bajo,\nmedio, alto\n(3 nudos por variable)",
          "Inferencia (7)\n27 reglas\nfuerza = producto\nde pertenencias",
          "Salida (8)\n$u=\\sum w\\,c\\,/\\sum w$\ncambiar si $u>0$\n($V\\geq3$ s; o $V=90$ s)"],
         "u", "Semáforo\ncambia de fase o\nsigue en verde\n(ámbar 3 s + rojo 2 s)", "medidas $Q_g$, $Q_r$, llegadas, $V$")
diagrama("fig_sup_bloques_pappis", "CONTROLADOR DE PAPPIS Y MAMDANI (decide a los 7, 17, 27, 37 y 47 s de verde)",
         ["Sensores\n$T$, $A$, $Q$\n(Sec. IV-B)", "Fuzzificación\nTablas II–VI\ndel original",
          "Inferencia\n25 reglas\nmín–máx", "Decisión (4)\nmáximo y\numbral 0.5"],
         "e*", "Semáforo\nextiende el verde\ne* = 0…10 s\n(0: cambia de fase)", "medidas $A$, $Q$, $T$")

with open("articulo/sup_simulador_datos.tex", "w", encoding="utf-8") as f:
    f.write("% Generado por codigo/gen_fig_suplemento_simulador.py: cifras de los instantes que muestran las figuras del simulador\n")
    for k, v in datos.items():
        f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
print("escrito articulo/sup_simulador_datos.tex:", datos)
