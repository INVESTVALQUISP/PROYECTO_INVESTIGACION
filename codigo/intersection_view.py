"""
intersection_view.py
================================================================================
Capa de renderizado del simulador interactivo. Dibuja (matplotlib) la
interseccion vista desde arriba, estilo Fig. 1/2 del paper:

  * carretera N-S (vertical) y E-W (horizontal), con carriles, marcas de
    centro, lineas de parada y flechas de sentido;
  * vehiculos: azules = brazo N-S, naranjas = brazo E-W. Un vehiculo se
    forma en cola detras de la linea de parada (p<0), cruza la interseccion
    cuando descarga (0<=p<=12) y sale del plano (p>13);
  * semaforos de tres luces: verde con derecho de paso; durante el tiempo perdido
    (5 s por cambio de fase = 10 s por ciclo, pag. 2 del paper) el brazo saliente
    muestra AMBAR 3 s y luego ambos brazos quedan en ROJO 2 s;
  * movimiento continuo: los vehiculos entran por el borde, avanzan en la cola
    cuando sale el de adelante, aceleran al cruzar y salen del plano (se dibujan
    varios sub-cuadros por segundo simulado; la animacion usa blitting);
  * trazas en vivo de d_m(t) con las decisiones del controlador (triangulo
    verde = extension elegida, cuadrado rojo = corte del verde);
  * PANEL DE REGLAS (columna derecha): las 5 reglas de la intervencion en curso con
    su activacion y la regla que DISPARA (decide la extension), el vector de grados
    grade(e) con el umbral 0.5 y los disparos acumulados de las 25 reglas.

La vista es agnostica del backend: recibe un Figure y se dibuja sobre el
canvas que el llamador elija (TkAgg en la GUI, Agg para exportar video).

Convenciones geometricas (plano 0..100 x 0..100):
  * carril N->S (baja): centro x=47.5, linea de parada y=57.5  -> y = 57.5-p
  * carril E->W (izq.): centro y=52.5, linea de parada x=57.5  -> x = 57.5-p
"""
import numpy as np
import matplotlib
from matplotlib.patches import Rectangle, Circle

import fuzzy_logic as fl

# --- paleta y constantes visuales ------------------------------------------
ROAD = "#4d4d52"
LANE = "#f2f2f2"
BLUE = "#1f6fd6"      # brazo N-S
ORANGE = "#e8833a"    # brazo E-W
GREEN_L = "#2ecc71"
RED_L = "#e74c3c"
TXT = "#34495e"

STOP_Y = 57.5         # linea de parada del carril N->S
STOP_X = 57.5         # linea de parada del carril E->W
# --- vehiculos ------------------------------------------------------------
# (nombre, largo, ancho) en unidades del plano; la calzada tiene 5 unidades por carril
CAR_TYPES = (("sedán", 4.4, 2.2), ("SUV", 4.9, 2.4), ("compacto", 3.9, 2.1), ("camioneta", 5.3, 2.4))
STOP_LINE_GAP = 1.4   # distancia del paragolpes delantero a la linea de parada cuando esta detenido
GAP_DEFAULT = 2.2     # separacion entre autos detenidos (paragolpes a paragolpes); se puede cambiar en la ventana
GAP_HARD_MIN = 0.8    # separacion minima absoluta: ningun auto se acerca mas que esto al de adelante
QVIS_MAX = 6          # referencia de autos visibles en cola (el numero real depende del largo de cada auto)
QSPAN = 40.0          # unidades de plano disponibles para la cola
SPACING = 6.0         # separacion media entre centros (solo para estimar la longitud de la cola)

# --- cinematica de los vehiculos (unidades de plano por segundo simulado) ----
SPAWN_P = -47.0       # p donde "entra" un vehiculo (justo fuera del plano)
P_OUT = 62.0          # p a partir del cual el vehiculo que cruzo sale del plano
V_APPROACH = 12.0     # velocidad de aproximacion / avance en la cola
V_MAX = 15.0          # velocidad maxima al cruzar
ACCEL = 16.0          # aceleracion al cruzar la linea de parada
ACCEL_Q = 9.0         # aceleracion al avanzar en la cola
DECEL = 14.0          # frenado comodo al acercarse al auto de adelante o a la linea

BODY_COLORS = {"ns": ("#1f6fd6", "#2a9d8f", "#264e86", "#4a90e2", "#5c6bc0", "#1b8bb5"),
               "ew": ("#e8833a", "#e76f51", "#f4a261", "#d9822b", "#c0392b", "#e0a526")}

AMBER_L = "#f5b82e"
AMBER_S = 3           # segundos de ambar (paper: ambar de 3 s) dentro de los 5 s de tiempo perdido


_INT_COLORS = {7: "#2b6cb0", 17: "#2f855a", 27: "#c05621", 37: "#6b46c1", 47: "#b83280"}


def plt_color(k):
    return _INT_COLORS.get(k, "#555555")


class IntersectionView:
    """Vista animada de la interseccion. Uso:

        view = IntersectionView(fig)
        state = sim.step()
        while not state.done:
            view.step_render(state)       # avanza 1 s y redibuja
            fig.canvas.draw()
    """

    def __init__(self, fig, rules=None, panels=True):
        self.fig = fig
        self.panels = panels
        self.rules = rules if rules is not None else fl.RULES
        self.threshold = 0.5                  # umbral que se dibuja (lo fija la ventana)
        self.disabled = frozenset()           # reglas apagadas: {(intervencion, indice)}
        if panels:
            gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 0.42], hspace=0.10,
                                  left=0.04, right=0.585, top=0.965, bottom=0.085)
        else:
            gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 0.42], hspace=0.10,
                                  left=0.055, right=0.985, top=0.965, bottom=0.09)
        self.ax = fig.add_subplot(gs[0])
        self.axq = fig.add_subplot(gs[1])
        self._build_scene()
        self._build_trace()
        if panels:
            gr = fig.add_gridspec(3, 1, height_ratios=[0.37, 0.24, 0.39], hspace=0.42,
                                  left=0.665, right=0.985, top=0.945, bottom=0.065)
            self.ax_rules = fig.add_subplot(gr[0])
            self.ax_grade = fig.add_subplot(gr[1])
            self.ax_fire = fig.add_subplot(gr[2])
            self._build_rule_panels()
        self._bg = None
        self._need_full = True
        self._build_pool()
        fig.canvas.mpl_connect("draw_event", self._on_draw)
        self._animated_extra()

    # ------------------------------------------------------------------
    # personalizacion (se aplica en vivo)
    # ------------------------------------------------------------------
    def refresh(self):
        """Redibuja todo (fondo + artistas animados); sirve tras un cambio de opciones con la simulacion en pausa."""
        self._need_full = True
        self._full_draw()
        self.draw_frame(0.0)

    def set_threshold(self, thr):
        self.threshold = float(thr)
        if self.panels and getattr(self, "_last", None) is not None:
            d = self._last
            self._draw_rules(d, self.rules[d.intervention], d.intervention)
            self._draw_grade(d)
            self.refresh()

    def set_disabled(self, disabled):
        """Reglas apagadas (se muestran en gris y no aportan a la decision)."""
        self.disabled = frozenset(disabled)
        if self.panels:
            d = getattr(self, "_last", None)
            if d is not None:
                self._draw_rules(d, self.rules[d.intervention], d.intervention)
            self.refresh()

    def set_car_options(self, gap=None, mix=None):
        """gap: separacion entre autos detenidos (unidades); mix: True = tipos de auto variados."""
        if gap is not None:
            self.gap = float(gap)
        if mix is not None:
            self.mix = bool(mix)

    def set_detectors(self, show):
        for a in self._detectors:
            a.set_visible(bool(show))
        self.refresh()

    def set_panels(self, rules=True, grade=True, fire=True, trace=True):
        """Muestra u oculta cada apartado de la ventana (para explicar de a poco)."""
        if not self.panels:
            return
        for ax, flag in ((self.ax_rules, rules), (self.ax_grade, grade), (self.ax_fire, fire), (self.axq, trace)):
            ax.set_visible(bool(flag))
        for a in (self.ln_dm, self.sc_ext, self.sc_cut, self.dec_txt):
            a.set_visible(bool(trace))
        right = rules or grade or fire
        if not hasattr(self, "_pos0"):
            self._pos0 = (self.ax.get_position().frozen(), self.axq.get_position().frozen())
        if right:
            self.ax.set_position(self._pos0[0])
            self.axq.set_position(self._pos0[1])
        else:                                   # sin paneles a la derecha, la calle usa todo el ancho
            p0, q0 = self._pos0
            self.ax.set_position([0.04, p0.y0, 0.945, p0.height])
            self.axq.set_position([0.04, q0.y0, 0.945, q0.height])
        self.refresh()

    def set_rules(self, rules):
        """Cambia el conjunto de reglas mostrado (p. ej. al reiniciar con otra config)."""
        self.rules = rules
        if self.panels:
            self._build_rule_panels()

    # ------------------------------------------------------------------
    # escena
    # ------------------------------------------------------------------
    def _build_scene(self):
        ax = self.ax
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_facecolor("#eef0f2")

        # calzada
        ax.add_patch(Rectangle((45, 0), 10, 100, fc=ROAD, ec="none", zorder=1))
        ax.add_patch(Rectangle((0, 45), 100, 10, fc=ROAD, ec="none", zorder=1))
        # marcas de carril (punteadas), sin entrar en la caja de la isla
        for y0, y1 in ((0, 45), (55, 100)):
            ax.plot([50, 50], [y0, y1], color=LANE, lw=1.6,
                    linestyle=(0, (6, 7)), alpha=0.85, zorder=2)
        for x0, x1 in ((0, 45), (55, 100)):
            ax.plot([x0, x1], [50, 50], color=LANE, lw=1.6,
                    linestyle=(0, (6, 7)), alpha=0.85, zorder=2)
        # lineas de parada
        ax.add_patch(Rectangle((45.1, STOP_Y), 4.8, 0.8, fc="white",
                               ec="none", zorder=3))
        ax.add_patch(Rectangle((STOP_X, 50.1), 0.8, 4.8, fc="white",
                               ec="none", zorder=3))
        # barras de cola (se redimensionan en vivo, detras de los autos)
        self.bar_ns = Rectangle((45.3, STOP_Y), 4.4, 0.0, fc=BLUE,
                                alpha=0.18, ec="none", zorder=2)
        self.bar_ew = Rectangle((STOP_X, 50.3), 0.0, 4.4, fc=ORANGE,
                                alpha=0.18, ec="none", zorder=2)
        ax.add_patch(self.bar_ns)
        ax.add_patch(self.bar_ew)
        # flechas de sentido
        ax.annotate("", xy=(47.5, 76), xytext=(47.5, 88),
                    arrowprops=dict(arrowstyle="-|>", color="white",
                                    lw=2.6, mutation_scale=16), zorder=3)
        ax.annotate("", xy=(76, 52.5), xytext=(88, 52.5),
                    arrowprops=dict(arrowstyle="-|>", color="white",
                                    lw=2.6, mutation_scale=16), zorder=3)
        # rumbos (fuera de la calzada)
        for x, y, s, ha, va in ((43.4, 93.0, "N", "right", "top"),
                                (43.4, 2.5, "S", "right", "bottom"),
                                (3.0, 43.6, "O", "left", "top"),
                                (97.0, 43.6, "E", "right", "top")):
            ax.text(x, y, s, ha=ha, va=va, fontsize=11,
                    color=TXT, fontweight="bold", zorder=4)
        # detectores del paper (pag. 709): ven las llegadas de los proximos 10 s; capa opcional
        self._detectors = []
        for (x, y, w, h, tx, ty, rot) in ((45.25, STOP_Y + 29.4, 4.5, 1.2, 44.6, STOP_Y + 30.0, 0),
                                          (STOP_X + 29.4, 50.25, 1.2, 4.5, STOP_X + 30.0, 56.0, 0)):
            rect = Rectangle((x, y), w, h, fc="#f1c40f", ec="#9a7d0a", lw=0.8, alpha=0.9, zorder=4)
            lab_ = ax.text(tx, ty, "detector", fontsize=7, color="#7d6608", ha="right" if rot == 0 and tx < 50 else "center",
                           va="center", zorder=4)
            rect.set_visible(False)
            lab_.set_visible(False)
            ax.add_patch(rect)
            self._detectors += [rect, lab_]
        # semaforos de tres luces (rojo / ambar / verde)
        self._lamps = {}
        self._build_head("ns", 40.3, 58.8, vertical=True)
        self._build_head("ew", 58.8, 41.6, vertical=False)
        ax.text(38.7, 60.2, "N-S", ha="right", va="center", fontsize=8, color=TXT, zorder=4)
        ax.text(66.4, 38.9, "E-W", ha="left", va="center", fontsize=8, color=TXT, zorder=4)
        # textos en vivo
        self.hdr = ax.text(50, 100.0, "", ha="center", va="top",
                           fontsize=11.5, color=TXT, zorder=7,
                           bbox=dict(fc="white", ec="none", alpha=0.85,
                                     pad=2.0))
        self.sub = ax.text(0.4, -0.6, "", ha="left", va="top",
                           fontsize=8.5, color="#7f8c8d", zorder=7,
                           bbox=dict(fc="white", ec="none", alpha=0.7,
                                     pad=1.5))
        self.lab_ns = ax.text(38.7, 65.5, "", ha="right", va="center",
                              fontsize=9.5, color=BLUE, fontweight="bold",
                              zorder=7)
        self.lab_ew = ax.text(58.8, 36.4, "", ha="left", va="top",
                              fontsize=9.5, color=ORANGE, fontweight="bold",
                              zorder=7)
        self._cars = []

    def _build_head(self, arm, x0, y0, vertical):
        """Caja de semaforo con tres lamparas (orden rojo, ambar, verde)."""
        ax = self.ax
        w, h = (3.6, 10.4) if vertical else (10.4, 3.6)
        ax.add_patch(matplotlib.patches.FancyBboxPatch(
            (x0, y0), w, h, boxstyle="round,pad=0.15,rounding_size=0.9",
            fc="#1b1b1b", ec="#0e0e0e", lw=0.8, zorder=5))
        lamps = []
        for k in range(3):
            if vertical:
                c = (x0 + w / 2, y0 + h - 1.75 - 3.45 * k)
            else:
                c = (x0 + 1.75 + 3.45 * k, y0 + h / 2)
            lamp = Circle(c, 1.25, fc="#333333", ec="none", zorder=6)
            ax.add_patch(lamp)
            lamps.append(lamp)
        self._lamps[arm] = lamps

    _OFF = ("#4a2626", "#4f4522", "#1f4a2f")
    _ON = (RED_L, AMBER_L, GREEN_L)

    def _set_lamps(self, arm, which):
        """which: 0 rojo, 1 ambar, 2 verde."""
        for k, lamp in enumerate(self._lamps[arm]):
            lamp.set_facecolor(self._ON[k] if k == which else self._OFF[k])

    def _light_state(self, st):
        """(luz N-S, luz E-W) segun el estado: 0 rojo, 1 ambar, 2 verde."""
        if st.in_transition:
            out = st.phase                       # brazo que tenia el verde
            idx = getattr(st, "trans_index", 0)
            amber = idx < AMBER_S
            ns = (1 if amber else 0) if out == 0 else 0
            ew = (1 if amber else 0) if out == 1 else 0
            return ns, ew
        return (2, 0) if st.phase == 0 else (0, 2)

    # ------------------------------------------------------------------
    # traza de retardo
    # ------------------------------------------------------------------
    def _build_trace(self):
        ax = self.axq
        ax.set_facecolor("#fbfcfd")
        ax.grid(True, lw=0.5, color="#d5dbe0", alpha=0.8)
        ax.set_xlabel("tiempo (s)", fontsize=10)
        ax.set_ylabel("$d_m$ (s/veh)", fontsize=10)
        (self.ln_dm,) = ax.plot([], [], color="#2c3e50", lw=1.5)
        self.sc_ext = ax.scatter([], [], marker="^", s=22, color=GREEN_L,
                                 edgecolor="none", zorder=5,
                                 label="extensión e*")
        self.sc_cut = ax.scatter([], [], marker="s", s=16, color=RED_L,
                                 edgecolor="none", zorder=5,
                                 label="corte del verde")
        self.dec_txt = ax.text(0.012, 0.90, "", transform=ax.transAxes,
                               fontsize=9.5, color=TXT, va="top")
        ax.legend(loc="upper right", fontsize=8.5, framealpha=0.9)
        self._tt = []
        self._dd = []
        self._xt = []
        self._xd = []
        self._ct = []
        self._cd = []
        self._xmax = 60.0                  # los limites cambian a saltos (evita redibujar todo)
        self._ymax = 6.0
        ax.set_xlim(0, self._xmax)
        ax.set_ylim(0, self._ymax)

    # ------------------------------------------------------------------
    # panel de reglas / disparos
    # ------------------------------------------------------------------
    def _rule_keys(self):
        return [(k, i) for k in sorted(self.rules) for i in range(len(self.rules[k]))]

    @staticmethod
    def _rule_short(r):
        T, A, Q, E = r
        return f"T={T} · A=mt({A}) · Q={'any' if Q == 'any' else 'lt(' + Q + ')'} → E={E}"

    def _build_rule_panels(self):
        """Dibuja los tres paneles de la columna derecha en su estado inicial."""
        keys = self._rule_keys()
        self._fire = {k: 0 for k in keys}      # disparos decisivos
        self._act = {k: 0 for k in keys}       # decisiones en que la regla tuvo grado > 0
        self._last = None
        self._draw_rules(None, self.rules[sorted(self.rules)[0]], sorted(self.rules)[0])
        self._draw_grade(None)
        self._draw_fire()

    def _draw_rules(self, d, rules, k):
        ax = self.ax_rules
        ax.clear()
        ax.set_xlim(0, 1)
        ax.set_ylim(0, len(rules) + 1.35)
        ax.axis("off")
        ttl = f"Reglas de la intervención de {k} s"
        if d is None:
            ttl += "  (aún sin decisión)"
        ax.text(0.0, len(rules) + 1.2, ttl, fontsize=10, fontweight="bold", color=TXT, va="center")
        if d is not None:
            ax.text(0.0, len(rules) + 0.62,
                    f"entradas: Q (rojo)={d.q_red} · cola verde={d.q_green} · A(10 s)={d.beta[-1]}",
                    fontsize=7.4, color="#7f8c8d", va="center")
        bx0, bw = 0.69, 0.255
        ax.text(bx0 + bw / 2, len(rules) + 0.62, "activación", fontsize=7, color="#7f8c8d",
                ha="center", va="center")
        for i, r in enumerate(rules):
            y = len(rules) - 1 - i + 0.1
            win = d is not None and i in d.winners
            act = d.activation[i] if d is not None else 0.0
            off = (k, i) in self.disabled
            if win:
                ax.add_patch(Rectangle((-0.01, y - 0.4), 1.02, 0.8, fc="#d9f5e3", ec=GREEN_L, lw=1.2, zorder=0))
            ax.text(0.0, y, f"R{i + 1}", fontsize=8, fontweight="bold", color="#aab7c4" if off else TXT, va="center")
            ax.text(0.05, y, self._rule_short(r) + ("  (apagada)" if off else ""), fontsize=6.6, va="center",
                    color="#aab7c4" if off else ("#0b6b35" if win else TXT),
                    fontweight="bold" if win else "normal", style="italic" if off else "normal")
            ax.add_patch(Rectangle((bx0, y - 0.2), bw, 0.4, fc="#ecf0f1", ec="none"))
            col = GREEN_L if win else ("#3b82c4" if act >= self.threshold else "#aab7c4")
            ax.add_patch(Rectangle((bx0, y - 0.2), bw * act, 0.4, fc=col, ec="none"))
            ax.text(bx0 + bw + 0.005, y, f"{act:.2f}" + (" ★" if win else ""), fontsize=7.2,
                    va="center", ha="left", color="#0b6b35" if win else TXT)
        ax.plot([bx0 + bw * self.threshold] * 2, [-0.35, len(rules) - 0.45], color=RED_L, lw=0.8, ls="--")
        ax.text(bx0 + bw * self.threshold, -0.5, f"umbral {self.threshold:.2f}", fontsize=6.3, color=RED_L,
                ha="center", va="top")

    def _draw_grade(self, d):
        ax = self.ax_grade
        ax.clear()
        e = np.arange(1, 11)
        g = d.grades if d is not None else np.zeros(10)
        cols = ["#aab7c4"] * 10
        if d is not None and d.e_star > 0:
            cols[d.e_star - 1] = GREEN_L
        elif d is not None:
            cols = ["#e8a09a"] * 10
        ax.bar(e, g, color=cols, edgecolor="#5d6d7e", lw=0.5)
        ax.axhline(self.threshold, color=RED_L, lw=1.0, ls="--")
        ax.set_xticks(e)
        ax.set_ylim(0, 1.12)
        ax.set_xlim(0.3, 10.7)
        ax.tick_params(labelsize=7.5)
        ax.set_xlabel("extensión candidata e (s)", fontsize=8)
        ax.set_ylabel("grade(e)", fontsize=8)
        ax.grid(True, axis="y", lw=0.4, color="#d5dbe0")
        if d is None:
            ttl = "Vector de grados (inferencia mín–máx)"
        elif d.e_star > 0:
            ttl = f"Decisión: e* = {d.e_star} s (grado {d.grade_max:.2f} ≥ {self.threshold:.2f})"
        else:
            ttl = f"Decisión: CORTE del verde (grado máx. {d.grade_max:.2f} < {self.threshold:.2f})"
        ax.set_title(ttl, fontsize=9.5, fontweight="bold", color=TXT, loc="left")

    def _draw_fire(self):
        ax = self.ax_fire
        ax.clear()
        keys = self._rule_keys()
        n = len(keys)
        ys = np.arange(n)[::-1]
        act = np.array([self._act[k] for k in keys], dtype=float)
        fire = np.array([self._fire[k] for k in keys], dtype=float)
        colors = [plt_color(k[0]) for k in keys]
        ax.barh(ys, act, color=colors, alpha=0.25, height=0.8, edgecolor="none")
        ax.barh(ys, fire, color=colors, alpha=1.0, height=0.55, edgecolor="none")
        ax.set_yticks(ys)
        ax.set_yticklabels([f"{k} s · R{i + 1}" for k, i in keys], fontsize=5.8)
        ax.tick_params(axis="x", labelsize=7)
        ax.set_ylim(-0.7, n - 0.3)
        top = max(1.0, act.max() if n else 1.0, fire.max() if n else 1.0)
        ax.set_xlim(0, top * 1.12)
        for j, (k, i) in enumerate(keys):
            if i == 0 and j > 0:
                ax.axhline(ys[j] + 0.5, color="#95a5a6", lw=0.5)
            f = self._fire[(k, i)]
            if f:
                ax.text(f + top * 0.01, ys[j], str(f), fontsize=5.4, va="center", color=TXT)
        ax.grid(True, axis="x", lw=0.4, color="#d5dbe0")
        tot = int(fire.sum())
        ax.set_title(f"Disparos acumulados por regla (oscuro) y activaciones (claro) · total {tot}",
                     fontsize=8.6, fontweight="bold", color=TXT, loc="left")

    def _update_rules(self, d, st):
        if not self.panels:
            return
        for i, a in enumerate(d.activation):
            if a > 0:
                self._act[(d.intervention, i)] += 1
        for i in d.winners:
            self._fire[(d.intervention, i)] += 1
        self._last = d
        self._draw_rules(d, self.rules[d.intervention], d.intervention)
        self._draw_grade(d)
        self._draw_fire()

    # ------------------------------------------------------------------
    # dinámica: autos con movimiento continuo
    # ------------------------------------------------------------------
    def _build_pool(self):
        """Pool de autos reutilizables. Cada auto se dibuja con 6 piezas (carroceria, techo,
        vidrios, ruedas, faros y luces de freno) definidas en coordenadas unitarias y escaladas
        al largo y ancho de cada tipo de auto."""
        from matplotlib.patches import FancyBboxPatch, PathPatch
        from matplotlib.path import Path

        def rects(spec):
            verts, codes = [], []
            for (x, y, w, h) in spec:
                verts += [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
                codes += [Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY]
            return Path(verts, codes)

        wheels = rects([(-0.36, -0.57, 0.20, 0.13), (0.20, -0.57, 0.20, 0.13),
                        (-0.36, 0.44, 0.20, 0.13), (0.20, 0.44, 0.20, 0.13)])
        head = rects([(0.46, -0.36, 0.05, 0.18), (0.46, 0.18, 0.05, 0.18)])
        tail = rects([(-0.51, -0.36, 0.05, 0.18), (-0.51, 0.18, 0.05, 0.18)])
        self._pool = {"ns": [], "ew": []}
        for arm in ("ns", "ew"):
            for k in range(46):
                parts = dict(
                    body=FancyBboxPatch((-0.5, -0.5), 1.0, 1.0, boxstyle="round,pad=0,rounding_size=0.2",
                                        fc=BODY_COLORS[arm][0], ec="#1d2733", lw=0.6, zorder=8),
                    glass=FancyBboxPatch((-0.22, -0.40), 0.52, 0.80, boxstyle="round,pad=0,rounding_size=0.12",
                                         fc="#26323f", ec="none", zorder=9),
                    roof=FancyBboxPatch((-0.13, -0.31), 0.30, 0.62, boxstyle="round,pad=0,rounding_size=0.10",
                                        fc=BODY_COLORS[arm][0], ec="none", zorder=10),
                    wheels=PathPatch(wheels, fc="#111111", ec="none", zorder=7),
                    head=PathPatch(head, fc="#fff3b0", ec="none", zorder=11),
                    tail=PathPatch(tail, fc="#8e1f18", ec="none", zorder=11))
                for a in parts.values():
                    a.set_visible(False)
                    a.set_animated(True)
                    self.ax.add_patch(a)
                self._pool[arm].append(parts)
        self._queue = {"ns": [], "ew": []}     # autos en cola (cabecera primero)
        self._cross = {"ns": [], "ew": []}     # autos que ya cruzaron la linea de parada
        self._next_id = 0
        self._model_q = {"ns": 0, "ew": 0}
        self.gap = GAP_DEFAULT                 # separacion entre autos detenidos (editable)
        self.mix = True                        # True: tipos de auto variados; False: solo sedanes

    @staticmethod
    def _mix_color(c, k):
        """Aclara (k>0) u oscurece (k<0) un color hex."""
        c = c.lstrip("#")
        rgb = [int(c[i:i + 2], 16) for i in (0, 2, 4)]
        rgb = [int(v + (255 - v) * k) if k > 0 else int(v * (1 + k)) for v in rgb]
        return "#%02x%02x%02x" % tuple(max(0, min(255, v)) for v in rgb)

    def _new_car(self, arm, p):
        cid = self._next_id
        self._next_id += 1
        kind = CAR_TYPES[(cid * 7 + (3 if arm == "ew" else 0)) % len(CAR_TYPES)] if self.mix else CAR_TYPES[0]
        return {"id": cid, "p": p, "v": V_APPROACH, "L": kind[1], "W": kind[2],
                "color": BODY_COLORS[arm][(cid * 5) % len(BODY_COLORS[arm])], "brake": False}

    def _advance_cars(self, st):
        """Aplica al modelo visual los eventos de este segundo (llegadas y descargas)."""
        for arm, arrived, discharged in (("ns", st.arrived_ns, st.discharge_ns),
                                         ("ew", st.arrived_ew, st.discharge_ew)):
            if arrived:
                car = self._new_car(arm, SPAWN_P)
                q = self._queue[arm]
                rear = q[-1] if q else (self._cross[arm][-1] if self._cross[arm] else None)
                if rear is not None:       # nunca nace encima del auto de atras (en cola o ya cruzando)
                    car["p"] = min(SPAWN_P, rear["p"] - (rear["L"] + car["L"]) / 2 - GAP_HARD_MIN - 0.5)
                q.append(car)
            if discharged and self._queue[arm]:
                car = self._queue[arm].pop(0)
                car["v"] = max(car["v"], 1.5)
                car["brake"] = False
                self._cross[arm].append(car)

    def _move_cars(self, dt):
        """Avanza dt segundos simulados. Cada auto frena de forma comoda hasta quedar a 'gap' del
        auto de adelante (o a la linea de parada) y nunca se acerca a menos de GAP_HARD_MIN."""
        if dt <= 0:
            return
        for arm in ("ns", "ew"):
            # autos que ya cruzaron: aceleran, sin acercarse al de adelante
            ahead = None
            for car in self._cross[arm]:
                car["v"] = min(V_MAX, car["v"] + ACCEL * dt)
                newp = car["p"] + car["v"] * dt
                if ahead is not None:
                    newp = min(newp, ahead["p"] - (ahead["L"] + car["L"]) / 2 - GAP_HARD_MIN)
                car["p"] = max(car["p"], newp)
                ahead = car
            self._cross[arm] = [c for c in self._cross[arm] if c["p"] < P_OUT]
            # autos en cola: seguimiento con frenado
            lead = self._cross[arm][-1] if self._cross[arm] else None     # el que acaba de cruzar
            prev = None
            for car in self._queue[arm]:
                p, v, L = car["p"], car["v"], car["L"]
                if prev is None:
                    target = -(L / 2 + STOP_LINE_GAP)
                else:
                    target = prev["p"] - (prev["L"] + L) / 2 - self.gap
                limit = None
                ahead = prev if prev is not None else lead
                if ahead is not None:
                    limit = ahead["p"] - (ahead["L"] + L) / 2 - GAP_HARD_MIN
                    if prev is None:
                        target = min(target, limit)
                dist = max(0.0, target - p)
                v_allowed = min(V_APPROACH, (2.0 * DECEL * dist) ** 0.5)
                v_new = min(v_allowed, v + ACCEL_Q * dt)
                newp = min(p + v_new * dt, max(p, target))
                if limit is not None:
                    newp = min(newp, limit)
                newp = max(newp, p) if (limit is None or p <= limit) else limit
                car["brake"] = (v_new < v - 0.3) or (v_new < 0.4)
                car["v"] = max(0.0, (newp - p) / dt)
                car["p"] = newp
                prev = car

    def _place_cars(self):
        """Asigna los autos a las piezas del pool: posicion, orientacion, tamano y colores."""
        from matplotlib.transforms import Affine2D
        data = self.ax.transData
        for arm in ("ns", "ew"):
            pool = self._pool[arm]
            j = 0
            theta = -np.pi / 2 if arm == "ns" else np.pi          # N-S baja (-y); E-W va hacia la izquierda (-x)
            for car in self._queue[arm] + self._cross[arm]:
                p = car["p"]
                if p < SPAWN_P - 6 or p > P_OUT:
                    continue
                if j >= len(pool):
                    break
                parts = pool[j]
                j += 1
                if arm == "ns":
                    cx, cy = 47.5, STOP_Y - p
                else:
                    cx, cy = STOP_X - p, 52.5
                tr = Affine2D().scale(car["L"], car["W"]).rotate(theta).translate(cx, cy) + data
                for k, a in parts.items():
                    a.set_transform(tr)
                    a.set_visible(True)
                parts["body"].set_facecolor(car["color"])
                parts["roof"].set_facecolor(self._mix_color(car["color"], 0.28))
                parts["tail"].set_facecolor("#ff3b30" if car["brake"] else "#8e1f18")
            for parts in pool[j:]:
                for a in parts.values():
                    a.set_visible(False)

    def _queue_extent(self, arm):
        """Longitud (unidades) que ocupa la cola real del modelo en la calle y cuantos autos no caben en el dibujo."""
        pos, shown = STOP_LINE_GAP, 0
        n = self._model_q[arm]
        for i in range(n):
            L = self._queue[arm][i]["L"] if i < len(self._queue[arm]) else 4.2
            if pos + L > QSPAN + 6:
                break
            pos += L + self.gap
            shown += 1
        return min(pos, QSPAN), n - shown

    def _animated_extra(self):
        """Marca como animados los artistas que cambian en cada segundo (ya no se dibujan
        en el redibujo completo: se pintan por blitting y el fondo solo cambia en decisiones)."""
        self._anim_static = [self.bar_ns, self.bar_ew, self.ln_dm, self.sc_ext, self.sc_cut,
                             self.hdr, self.lab_ns, self.lab_ew]
        for arm in ("ns", "ew"):
            self._anim_static += self._lamps[arm]
        for a in self._anim_static:
            a.set_animated(True)

    def _animated(self):
        """Artistas que cambian en cada sub-cuadro (se dibujan por blitting)."""
        arts = []
        for arm in ("ns", "ew"):
            for parts in self._pool[arm]:
                arts += list(parts.values())
        return arts + list(self._anim_static)          # autos debajo; barras, textos y luces encima

    def _on_draw(self, event):
        self._bg = self.fig.canvas.copy_from_bbox(self.fig.bbox)

    def _full_draw(self):
        self.fig.canvas.draw()          # dispara _on_draw -> guarda el fondo

    def draw_frame(self, dt=1.0):
        """Un sub-cuadro: mueve los autos dt s simulados y repinta solo lo animado."""
        self._move_cars(dt)
        self._place_cars()
        canvas = self.fig.canvas
        if self._bg is None:
            self._full_draw()
            return
        canvas.restore_region(self._bg)
        for a in self._animated():
            if a.get_visible():
                a.axes.draw_artist(a)
        canvas.blit(self.fig.bbox)

    def _update_trace(self, st):
        self._tt.append(st.t)
        self._dd.append(st.dm)
        if len(self._tt) > 6000:                     # decimar si crece
            self._tt = self._tt[::2] + [self._tt[-1]]
            self._dd = self._dd[::2] + [self._dd[-1]]
        d = st.decision
        if d is not None:
            if d.cut:
                self._ct.append(st.t)
                self._cd.append(st.dm)
            else:
                self._xt.append(st.t)
                self._xd.append(st.dm)
        self.ln_dm.set_data(self._tt, self._dd)
        self.sc_ext.set_offsets(np.c_[self._xt, self._xd])
        self.sc_cut.set_offsets(np.c_[self._ct, self._cd])
        changed = False
        while st.t > self._xmax:
            self._xmax *= 2
            changed = True
        hi = max(max(self._dd) if self._dd else 5.0, 5.0) * 1.15
        while hi > self._ymax:
            self._ymax *= 1.6
            changed = True
        if changed:
            self.axq.set_xlim(0, self._xmax)
            self.axq.set_ylim(0, self._ymax)
            self._need_full = True
        if d is not None:
            who = "N-S" if st.phase == 0 else "E-W"
            if d.cut:
                self.dec_txt.set_text(
                    f"última decisión: t={st.t} s · verde {who} "
                    f"{d.elapsed} s → CORTE (grado {d.grade_max:.2f} < umbral)")
            else:
                rid = ", ".join(f"{d.intervention}s-R{i + 1}" for i in d.winners)
                self.dec_txt.set_text(
                    f"última decisión: t={st.t} s · verde {who} "
                    f"{d.elapsed} s → e*={d.e_star} s (grado {d.grade_max:.2f}) · dispara {rid}")

    def _phase_label(self, st):
        if st.in_transition:
            idx = getattr(st, "trans_index", 0)
            return ("ámbar (tiempo perdido)" if idx < AMBER_S
                    else "todo rojo (despeje)")
        arm = "N-S" if st.phase == 0 else "E-W"
        return f"verde {arm} (segundo {st.green_elapsed})"

    # ------------------------------------------------------------------
    def advance(self, st):
        """Aplica el estado de un segundo simulado (sin dibujar los autos).
        Actualiza semaforos, textos, traza y paneles; redibuja el fondo solo si
        hace falta (decision del controlador, cambio de ejes o primer cuadro)."""
        self._need_full = self._bg is None
        self._advance_cars(st)
        ns, ew = self._light_state(st)
        self._set_lamps("ns", ns)
        self._set_lamps("ew", ew)
        mm, ss = divmod(st.t, 60)
        self.hdr.set_text(
            f"t = {mm:02d}:{ss:02d}   ·   {self._phase_label(st)}   ·   "
            f"cola N-S: {st.q_ns}   ·   cola E-W: {st.q_ew}   ·   "
            f"d_m = {st.dm:.2f} s/veh")
        self._model_q = {"ns": st.q_ns, "ew": st.q_ew}
        ext_ns, hid_ns = self._queue_extent("ns")
        ext_ew, hid_ew = self._queue_extent("ew")
        self.lab_ns.set_text(f"N-S: {st.q_ns} veh" + (f" (+{hid_ns})" if hid_ns > 0 else ""))
        self.lab_ew.set_text(f"E-W: {st.q_ew} veh" + (f" (+{hid_ew})" if hid_ew > 0 else ""))
        self.bar_ns.set_height(ext_ns)
        self.bar_ew.set_width(ext_ew)
        self._update_trace(st)
        if st.decision is not None:
            self._update_rules(st.decision, st)
            self._need_full = True
        if self._need_full:
            self._full_draw()          # los autos son artistas animados: no se dibujan aqui

    def step_render(self, st, sub=1, on_frame=None, u=1.0):
        """Avanza 1 s simulado y lo dibuja en 'sub' sub-cuadros (movimiento suave).
        on_frame() se llama tras cada sub-cuadro (p. ej. para capturar video)."""
        self.advance(st)
        for _ in range(max(1, sub)):
            self.draw_frame(1.0 / max(1, sub))
            if on_frame is not None:
                on_frame()

    # ------------------------------------------------------------------
    def reset(self):
        """Vuelve al estado inicial (t=0, sin autos ni traza)."""
        for arm in ("ns", "ew"):
            self._queue[arm] = []
            self._cross[arm] = []
            for parts in self._pool[arm]:
                for a_ in parts.values():
                    a_.set_visible(False)
        self._model_q = {"ns": 0, "ew": 0}
        self._next_id = 0
        self._tt.clear(); self._dd.clear()
        self._xt.clear(); self._xd.clear()
        self._ct.clear(); self._cd.clear()
        self.bar_ns.set_height(0)
        self.bar_ew.set_width(0)
        self.ln_dm.set_data([], [])
        self.sc_ext.set_offsets(np.empty((0, 2)))
        self.sc_cut.set_offsets(np.empty((0, 2)))
        self.dec_txt.set_text("")
        self._set_lamps("ns", 2)
        self._set_lamps("ew", 0)
        self.hdr.set_text("t = 00:00   ·   listo")
        self.lab_ns.set_text("N-S: 0 veh")
        self.lab_ew.set_text("E-W: 0 veh")
        self._xmax, self._ymax = 60.0, 6.0
        self.axq.set_xlim(0, self._xmax)
        self.axq.set_ylim(0, self._ymax)
        if self.panels:
            self._build_rule_panels()
        self._full_draw()
