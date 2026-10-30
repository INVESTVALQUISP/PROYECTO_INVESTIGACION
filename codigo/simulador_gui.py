"""
simulador_gui.py
================================================================================
Simulador INTERACTIVO de la interseccion (calle, autos y semaforos) con dos controladores:

  * FLC-O: el controlador difuso optimizado del articulo de mejora (27 reglas, decide cada segundo);
  * Pappis & Mamdani (1977): el controlador original (25 reglas, interviene a los 7, 17, 27, 37 y 47 s de verde).

Reproduce paso a paso (1 s por tick) el mismo modelo ya validado (traffic_model.simulate_fuzzy y sim_batch), pero con
interfaz grafica: se eligen el controlador, los flujos, la semilla, la duracion y la velocidad, y se observa la
animacion de la interseccion + la traza de d_m(t) (con la curva del OTRO controlador sobre las mismas llegadas) + el
registro de decisiones + el panel del controlador (entradas, salida y fuerza de cada regla).

Uso interactivo (necesita un entorno grafico, p.ej. Windows):
    python simulador_gui.py                          # FLC-O (el controlador mejorado)
    python simulador_gui.py --controlador pappis     # el controlador de 1977

Uso en video (sin interfaz; exporta MP4 o GIF para las diapositivas):
    python simulador_gui.py --video animacion.mp4 --ns 720 --ew 2160 --seed 1 --seconds 90 --fps 10
    python simulador_gui.py --video animacion.mp4 --controlador pappis

Dependencias: numpy, matplotlib, imageio (+ imageio-ffmpeg para MP4).
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import argparse
import os
import sys
import time

import numpy as np

import sim_engine as se


def decision_line(st):
    """Linea corta de registro: tiempo, brazo, segundo de verde, e* y regla(s) que disparan."""
    d = st.decision
    arm = "N-S" if st.phase == 0 else "E-W"
    if getattr(d, "kind", "") == "flco":
        return f"t={st.t:4d} {arm} v{d.elapsed:2d}s > CAMBIA u={d.u:+.2f}" + (" [verde máx.]" if d.forced else "")
    if d.cut:
        return f"t={st.t:4d} {arm} v{d.elapsed:2d}s > CORTE (g={d.grade_max:.2f})"
    ids = ",".join(f"R{i + 1}" for i in d.winners)
    return f"t={st.t:4d} {arm} v{d.elapsed:2d}s > e*={d.e_star:2d} [{d.intervention}s {ids}]"


def write_firings_csv(sim, path):
    """Guarda en CSV todas las decisiones y la activacion / disparo de cada regla."""
    import csv
    rows = sim.firing_rows()
    if not rows:
        return None
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return path


# ===========================================================================
# Modo video (headless)
# ===========================================================================
def render_video(path, ns, ew, rules, seed, seconds, fps, threshold, mode, csv_path=None, sub=3,
                 controller="flco", reference=True):
    import matplotlib
    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from intersection_view import IntersectionView

    cfg = se.SimConfig(lam_ns=ns / 3600.0, lam_ew=ew / 3600.0, seed=seed,
                       duration=seconds, ruleset=rules, threshold=threshold,
                       mode=mode, controller=controller)
    sim = se.StepSim(cfg)
    ref = None
    if reference:                                  # el otro controlador, sobre las mismas llegadas
        ref = se.StepSim(se.SimConfig(lam_ns=ns / 3600.0, lam_ew=ew / 3600.0, seed=seed, duration=seconds,
                                      ruleset=rules, threshold=threshold, mode=mode,
                                      controller="pappis" if controller == "flco" else "flco"))

    fig = plt.figure(figsize=(16.0, 9.2), dpi=100)    # 1600x920 px
    canvas = FigureCanvasAgg(fig)
    view = IntersectionView(fig, rules=cfg.rules, flco=cfg.flco, max_green=getattr(cfg, "max_green", 57))
    if controller == "flco":
        view.sub.set_text(f"controlador: FLC-O ({cfg.flco_model}) · N-S {ns} veh/h · E-W {ew} veh/h · semilla {seed}")
    else:
        view.sub.set_text(
            f"reglas: {rules} · umbral {threshold:.2f} · N-S {ns} veh/h · "
            f"E-W {ew} veh/h · lectura {'calibrada' if mode == 'capacity' else 'literal'} · semilla {seed}")
    view.reset()
    if ref is not None:
        view.set_reference(NOMBRES[ref.cfg.controller] + ", mismas llegadas")

    # -- escritor de video (MP4 con imageio-ffmpeg; si no, GIF con PIL) --
    writer = None
    gif_frames = None
    ext = os.path.splitext(path)[1].lower()
    if ext == ".gif":
        gif_frames = []
    else:
        try:
            import imageio
            writer = imageio.get_writer(path, fps=fps, codec="libx264",
                                        quality=8, pixelformat="yuv420p")
        except Exception as e:                       # noqa: BLE001
            print(f"[aviso] no se pudo crear el escritor MP4 ({e}); "
                  f"se guardara un GIF en {os.path.splitext(path)[0]}.gif")
            path = os.path.splitext(path)[0] + ".gif"
            gif_frames = []

    total = seconds
    frames_per_s = max(1, int(sub))

    def grab():
        w, h = canvas.get_width_height()
        frame = np.asarray(canvas.buffer_rgba()).reshape(h, w, 4)[:, :, :3]
        if writer is not None:
            writer.append_data(frame)
        else:
            from PIL import Image
            if (total * frames_per_s) <= 3600 or len(gif_frames) % 2 == 0:
                gif_frames.append(Image.fromarray(frame.copy()))

    for n in range(total):
        st = sim.step()
        view.advance(st, ref_dm=None if ref is None else ref.step().dm)
        for _ in range(frames_per_s):                           # 'sub' cuadros por segundo simulado
            view.draw_frame(1.0 / frames_per_s)
            grab()
        if (n + 1) % max(1, total // 10) == 0:
            print(f"  ... {100 * (n + 1) // total}%")

    if writer is not None:
        writer.close()
    else:
        from PIL import Image
        dur = 1000.0 / fps * (2 if total * frames_per_s > 3600 else 1)
        gif_frames[0].save(path, save_all=True, append_images=gif_frames[1:],
                           duration=int(dur), loop=0, optimize=False)
    print(f"video listo: {path}  (d_m final = {sim.dm:.3f} s/veh)")
    if csv_path:
        if write_firings_csv(sim, csv_path):
            print(f"disparos de reglas guardados en: {csv_path}")
    return path


# ===========================================================================
# Modo interactivo (Tkinter)
# ===========================================================================
NOMBRES = {"flco": "FLC-O (mejorado)", "pappis": "Pappis y Mamdani (1977)"}
CLAVES = {v: k for k, v in NOMBRES.items()}

PRESETS = {
    "Del artículo: 720 / 2160": (720, 2160),
    "Poco tráfico: 360 / 360": (360, 360),
    "Tráfico medio: 720 / 1080": (720, 1080),
    "Calle principal: 1080 / 1800": (1080, 1800),
    "Muy cargado: 1440 / 1440": (1440, 1440),
    "Muy asimétrico: 360 / 2520": (360, 2520),
    "Personalizado": None,
}

AYUDA = """CÓMO USAR EL SIMULADOR

BOTONES (columna derecha)
  ▶ Iniciar / ⏸ Pausa / ▶ Continuar: arranca, detiene y reanuda la simulación.
  ⏭ Paso: avanza 1 segundo simulado (útil para explicar con calma).
  ↺ Reiniciar: vuelve a t = 0 con los parámetros elegidos.
  Agregar autos a mano: suma autos a un brazo (entran de a uno por segundo) para ver cómo reacciona el controlador.
  ¿Qué decidió el controlador y por qué?: explicación en palabras simples de cada decisión.

1 · ESCENARIO
  Escenario: caudales de ejemplo. Flujo N-S / E-W: vehículos por hora que llegan a cada calle.
  Duración y semilla: la semilla fija las llegadas aleatorias (misma semilla = misma corrida).
  Velocidad: segundos simulados por segundo real. Se puede bajar a 1 para ir muy lento.

2 · CONTROLADOR
  Controlador: FLC-O (el controlador difuso mejorado del artículo) o Pappis y Mamdani (1977). Al cambiarlo, la simulación se
  reinicia con los mismos flujos y la misma semilla, así que las llegadas de autos son idénticas y la comparación es justa.
  Mostrar d_m del otro controlador: dibuja en la traza, punteada, la curva del controlador que NO se está viendo, sobre las
  mismas llegadas. Es la comparación en vivo: la curva continua es el controlador elegido.
  Solo con Pappis y Mamdani (1977):
    Umbral de decisión: grado mínimo (0.5 en el paper) para aceptar una extensión del verde.
    Lectura de A y Q: «calibrada» reproduce la Tabla VIII del paper; «literal» sigue el ejemplo tal cual.
    Encender / apagar reglas: quita reglas de las 25 para ver cuánto aporta cada una (se aplica en vivo).
  FLC-O no tiene umbral: cada segundo calcula una salida u y cambia de fase si u > 0 (después del verde mínimo de 3 s).

3 · VISTA DIDÁCTICA
  Apartados visibles: oculta reglas, grados, disparos o la traza de d_m para explicar de a poco.
  Pausar en cada decisión: la simulación se detiene cada vez que el controlador decide.
  Explicar cada decisión: muestra el texto explicativo.
  Mostrar detectores: marca dónde estarían los detectores que ven las llegadas de los próximos 10 s.
  Separación entre autos: distancia entre autos detenidos (nunca se tocan). Tipos de auto: variados o solo sedán.

LA PANTALLA
  Calle: autos azules = N-S, naranjas = E-W. Luces rojas de freno cuando el auto frena.
  Con Pappis y Mamdani (1977):
    Reglas de la intervención: las 5 reglas vigentes con su activación; ★ = la que decide.
    Decisión: grado de cada extensión posible (1 a 10 s) y el umbral. Disparos: cuántas veces actuó cada regla.
    Traza: retardo medio d_m en el tiempo (triángulo verde = extensión, cuadrado rojo = corte).
  Con FLC-O (cada segundo):
    Entradas (casilla «Reglas»): G = cola en verde + llegadas previstas, R = cola en rojo + llegadas previstas, V = segundos de
    verde, cada una sobre sus conjuntos difusos aprendidos (bajo, medio, alto); la línea roja es el valor actual.
    Salida (casilla «Grados»): u; si u > 0 se cambia de fase. Fuerza de las 27 reglas (casilla «Disparos»): rojo = la regla
    empuja a cambiar, azul = a seguir.
    Traza: d_m en el tiempo; cada cuadrado rojo es un cambio de fase.
  d_m cuenta solo los vehículos que ya salieron (convención del original). El artículo usa además la espera residual al final;
  al terminar, la ventana muestra las dos cifras.
"""


def run_gui(test_hook=None, controlador="flco"):
    """Abre la ventana. 'test_hook(app, root)' (solo para pruebas automaticas) reemplaza al mainloop.
    controlador: "flco" (FLC-O, el mejorado) o "pappis" (Pappis y Mamdani, 1977) al abrir."""
    import matplotlib
    try:
        matplotlib.use("TkAgg")
    except Exception:                                 # noqa: BLE001
        pass
    import tkinter as tk
    from tkinter import ttk
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from intersection_view import IntersectionView

    class App:
        def __init__(self, root):
            self.root = root
            root.title("Simulador · semáforo difuso: FLC-O frente a Pappis y Mamdani (1977)")
            root.configure(bg="#f4f5f7")
            # ventana adaptada a la pantalla (en pantallas chicas los botones quedaban fuera)
            w = min(1620, root.winfo_screenwidth() - 40)
            h = min(900, root.winfo_screenheight() - 80)
            root.geometry(f"{w}x{h}+10+10")
            root.minsize(900, 560)
            root.bind("<F11>", lambda e: root.attributes("-fullscreen", not root.attributes("-fullscreen")))

            # ---------- variables ----------
            self.v_ns = tk.IntVar(value=720)
            self.v_ew = tk.IntVar(value=2160)
            self.v_dur = tk.IntVar(value=3600)
            self.v_seed = tk.IntVar(value=1)
            self.v_thr = tk.DoubleVar(value=0.50)
            self.v_fps = tk.IntVar(value=10)
            self.v_rules = tk.StringVar(value="paper")
            self.v_mode = tk.StringVar(value="capacity")
            self.v_ctrl = tk.StringVar(value=NOMBRES[controlador])
            self.v_ref = tk.BooleanVar(value=True)
            self.v_preset = tk.StringVar(value="Del artículo: 720 / 2160")
            self.v_pause_dec = tk.BooleanVar(value=False)
            self.v_explain = tk.BooleanVar(value=True)
            self.v_p_rules = tk.BooleanVar(value=True)
            self.v_p_grade = tk.BooleanVar(value=True)
            self.v_p_fire = tk.BooleanVar(value=True)
            self.v_p_trace = tk.BooleanVar(value=True)
            self.v_detect = tk.BooleanVar(value=False)
            self.v_gap = tk.DoubleVar(value=2.2)
            self.v_mix = tk.StringVar(value="Variados")
            self.disabled = set()             # reglas apagadas: {(intervencion, indice)}
            self._pause_req = False

            # ---------- panel superior con pestañas ----------
            nb = ttk.Notebook(root)
            nb.pack(side=tk.TOP, fill=tk.X, padx=8, pady=(6, 0))

            def lab(parent, txt, row, col, **kw):
                ttk.Label(parent, text=txt).grid(row=row, column=col, sticky="e", padx=(10, 2), pady=2, **kw)

            # --- pestaña 1: escenario ---
            t1 = ttk.Frame(nb, padding=6)
            nb.add(t1, text=" 1 · Escenario ")
            lab(t1, "Escenario:", 0, 0)
            cb = ttk.Combobox(t1, textvariable=self.v_preset, values=list(PRESETS), width=28, state="readonly")
            cb.grid(row=0, column=1, columnspan=3, sticky="w")
            cb.bind("<<ComboboxSelected>>", lambda e: self._on_preset())
            lab(t1, "Flujo N-S (veh/h):", 1, 0)
            ttk.Spinbox(t1, from_=60, to=3600, increment=60, width=6, textvariable=self.v_ns,
                        command=self._custom_preset).grid(row=1, column=1, sticky="w")
            lab(t1, "Flujo E-W (veh/h):", 1, 2)
            ttk.Spinbox(t1, from_=60, to=3600, increment=60, width=6, textvariable=self.v_ew,
                        command=self._custom_preset).grid(row=1, column=3, sticky="w")
            lab(t1, "Duración (s):", 0, 4)
            ttk.Spinbox(t1, from_=300, to=14400, increment=300, width=7,
                        textvariable=self.v_dur).grid(row=0, column=5, sticky="w")
            lab(t1, "Semilla:", 1, 4)
            ttk.Spinbox(t1, from_=0, to=99999, width=7, textvariable=self.v_seed).grid(row=1, column=5, sticky="w")
            lab(t1, "Velocidad (s simulados por s):", 0, 6)
            ttk.Spinbox(t1, from_=1, to=30, width=5, textvariable=self.v_fps).grid(row=0, column=7, sticky="w")
            ttk.Label(t1, text="Flujos, duración y semilla se aplican al pulsar Reiniciar; la velocidad, en vivo.",
                      foreground="#7f8c8d").grid(row=1, column=6, columnspan=4, sticky="w", padx=10)

            # --- pestaña 2: controlador ---
            t2 = ttk.Frame(nb, padding=6)
            nb.add(t2, text=" 2 · Controlador ")
            lab(t2, "Controlador:", 0, 0)
            cbc = ttk.Combobox(t2, textvariable=self.v_ctrl, values=list(NOMBRES.values()), width=26, state="readonly")
            cbc.grid(row=0, column=1, columnspan=2, sticky="w")
            cbc.bind("<<ComboboxSelected>>", lambda e: self._on_ctrl())
            ttk.Checkbutton(t2, text="Mostrar d_m del otro controlador (mismas llegadas)", variable=self.v_ref,
                            command=self._apply_ref).grid(row=0, column=3, columnspan=4, sticky="w", padx=10)
            self.w_1977 = []                                  # controles que solo valen para Pappis y Mamdani
            lab(t2, "Umbral de decisión:", 1, 0)
            sp = ttk.Spinbox(t2, from_=0.30, to=0.90, increment=0.05, width=6, textvariable=self.v_thr,
                             command=self._apply_threshold)
            sp.grid(row=1, column=1, sticky="w")
            fm = ttk.LabelFrame(t2, text="Lectura de A y Q", padding=4)
            fm.grid(row=1, column=2, columnspan=2, sticky="w", padx=10)
            r1 = ttk.Radiobutton(fm, text="calibrada", value="capacity", variable=self.v_mode)
            r1.pack(side=tk.LEFT, padx=4)
            r2 = ttk.Radiobutton(fm, text="literal", value="literal", variable=self.v_mode)
            r2.pack(side=tk.LEFT, padx=4)
            fr = ttk.LabelFrame(t2, text="Reglas del controlador", padding=4)
            fr.grid(row=1, column=4, columnspan=3, sticky="w", padx=10)
            r3 = ttk.Radiobutton(fr, text="originales (paper)", value="paper", variable=self.v_rules,
                                 command=self._on_rules)
            r3.pack(side=tk.LEFT, padx=4)
            self.lab_rules = ttk.Label(fr, text="25 de 25 activas")
            self.lab_rules.pack(side=tk.LEFT, padx=6)
            b_rules = ttk.Button(fr, text="Encender / apagar reglas…", command=self.open_rules_editor)
            b_rules.pack(side=tk.LEFT, padx=4)
            self.w_1977 = [sp, r1, r2, r3, b_rules]
            self.lab_ctrl = ttk.Label(t2, text="", foreground="#7f8c8d", wraplength=1100, justify="left")
            self.lab_ctrl.grid(row=2, column=0, columnspan=8, sticky="w", padx=10, pady=(4, 0))

            # --- pestaña 3: vista didáctica ---
            t3 = ttk.Frame(nb, padding=6)
            nb.add(t3, text=" 3 · Vista didáctica ")
            f_pan = ttk.LabelFrame(t3, text="Apartados visibles", padding=4)
            f_pan.grid(row=0, column=0, rowspan=2, sticky="nw", padx=6)
            self.cb_panels = []
            for k, (txt, var) in enumerate((("Reglas", self.v_p_rules), ("Grados", self.v_p_grade),
                                            ("Disparos", self.v_p_fire), ("Traza d_m", self.v_p_trace))):
                cbp = ttk.Checkbutton(f_pan, text=txt, variable=var, command=self._apply_panels)
                cbp.grid(row=k // 2, column=k % 2, sticky="w", padx=4)
                self.cb_panels.append(cbp)
            f_cls = ttk.LabelFrame(t3, text="Para explicar", padding=4)
            f_cls.grid(row=0, column=1, rowspan=2, sticky="nw", padx=6)
            ttk.Checkbutton(f_cls, text="Pausar en cada decisión", variable=self.v_pause_dec).grid(
                row=0, column=0, sticky="w")
            ttk.Checkbutton(f_cls, text="Explicar cada decisión", variable=self.v_explain,
                            command=self._apply_explain).grid(row=1, column=0, sticky="w")
            ttk.Checkbutton(f_cls, text="Mostrar detectores", variable=self.v_detect,
                            command=self._apply_view_opts).grid(row=2, column=0, sticky="w")
            f_car = ttk.LabelFrame(t3, text="Autos", padding=4)
            f_car.grid(row=0, column=2, rowspan=2, sticky="nw", padx=6)
            ttk.Label(f_car, text="Separación entre autos:").grid(row=0, column=0, sticky="w")
            ttk.Scale(f_car, from_=0.8, to=5.0, variable=self.v_gap, length=140,
                      command=lambda v: self._apply_view_opts()).grid(row=0, column=1, padx=4)
            self.lab_gap = ttk.Label(f_car, text="2.2")
            self.lab_gap.grid(row=0, column=2)
            ttk.Label(f_car, text="Tipos de auto:").grid(row=1, column=0, sticky="w", pady=(4, 0))
            cbm = ttk.Combobox(f_car, textvariable=self.v_mix, values=("Variados", "Solo sedán"), width=12,
                               state="readonly")
            cbm.grid(row=1, column=1, sticky="w", padx=4, pady=(4, 0))
            cbm.bind("<<ComboboxSelected>>", lambda e: self._apply_view_opts())
            ttk.Button(t3, text="? Ayuda", command=self.open_help).grid(row=0, column=3, sticky="ne", padx=12)

            # ---------- figura (escena + traza) ----------
            self.fig = plt.figure(figsize=(14.6, 8.4), dpi=90)
            self.canvas = FigureCanvasTkAgg(self.fig, master=root)
            self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            # ---------- columna de controles ----------
            side = ttk.Frame(root, width=330)
            # se empaqueta ANTES que la figura: si la ventana es chica, la figura se
            # achica y los botones (Iniciar, Pausa...) siempre quedan visibles
            side.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 8), pady=8, before=self.canvas.get_tk_widget())
            side.pack_propagate(False)

            btns = ttk.Frame(side)
            btns.pack(fill=tk.X)
            for c in (0, 1):
                btns.columnconfigure(c, weight=1, uniform="b")
            self.b_start = ttk.Button(btns, text="▶ Iniciar", command=self.start)
            self.b_start.grid(row=0, column=0, sticky="ew", padx=2, pady=2)
            self.b_pause = ttk.Button(btns, text="⏸ Pausa", state=tk.DISABLED, command=self.toggle_pause)
            self.b_pause.grid(row=0, column=1, sticky="ew", padx=2, pady=2)
            self.b_step = ttk.Button(btns, text="⏭ Paso", command=self.step1)
            self.b_step.grid(row=1, column=0, sticky="ew", padx=2, pady=2)
            ttk.Button(btns, text="↺ Reiniciar", command=self.reset).grid(row=1, column=1, sticky="ew", padx=2, pady=2)

            self.prog = ttk.Progressbar(side, maximum=1000)
            self.prog.pack(fill=tk.X, pady=(8, 2))
            self.status = ttk.Label(side, text="Listo. Elija parámetros y pulse Iniciar.", anchor="w",
                                    foreground="#34495e", wraplength=315)
            self.status.pack(fill=tk.X)

            fa = ttk.LabelFrame(side, text="Agregar autos a mano", padding=4)
            fa.pack(fill=tk.X, pady=(6, 0))
            for c in range(4):
                fa.columnconfigure(c, weight=1, uniform="a")
            for c, (txt, arm, n) in enumerate((("N-S +1", 0, 1), ("N-S +5", 0, 5), ("E-W +1", 1, 1), ("E-W +5", 1, 5))):
                ttk.Button(fa, text=txt, width=7, command=lambda a=arm, k=n: self.inject(a, k)).grid(
                    row=0, column=c, padx=1)

            fs = ttk.Frame(side)
            fs.pack(fill=tk.X, pady=(6, 0))
            fs.columnconfigure(0, weight=1, uniform="s")
            fs.columnconfigure(1, weight=1, uniform="s")
            ttk.Button(fs, text="Guardar disparos (CSV)", command=self.save_csv).grid(row=0, column=0, sticky="ew", padx=1)
            ttk.Button(fs, text="Guardar imagen (PNG)", command=self.save_png).grid(row=0, column=1, sticky="ew", padx=1)

            ttk.Label(side, text="¿Qué decidió el controlador y por qué?", foreground="#34495e").pack(anchor="w", pady=(8, 2))
            self.explain = tk.Text(side, height=13, wrap="word", font=("TkDefaultFont", 9), bg="#fffdf2",
                                   relief="flat", padx=6, pady=4)
            self.explain.pack(fill=tk.X)
            self.explain.insert("1.0", "Aquí aparecerá, en palabras simples, la explicación de cada decisión "
                                       "del controlador (cada 10 s de verde).")
            self.explain.config(state=tk.DISABLED)

            ttk.Label(side, text="Decisiones y regla que dispara", foreground="#34495e").pack(anchor="w", pady=(8, 2))
            logf = ttk.Frame(side)
            logf.pack(fill=tk.BOTH, expand=True)
            self.log = tk.Listbox(logf, font=("Consolas", 8), width=44, relief="flat", bg="#ffffff", height=4)
            sb = ttk.Scrollbar(logf, orient=tk.VERTICAL, command=self.log.yview)
            self.log.configure(yscrollcommand=sb.set)
            self.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            sb.pack(side=tk.RIGHT, fill=tk.Y)

            self.sim = None
            self.ref = None                   # el otro controlador sobre las mismas llegadas (curva punteada)
            self.view = None
            self.after_id = None
            self.running = False
            self._set_ctrl_ui()

        # -------------------------------------------------------------
        def _on_rules(self):
            # umbral por defecto de cada conjunto (el usuario puede editarlo)
            self.v_thr.set(0.50)

        def _ref_label(self):
            otro = "pappis" if self._ctrl() == "flco" else "flco"
            return NOMBRES[otro] + ", mismas llegadas"

        def _ctrl(self):
            return CLAVES[self.v_ctrl.get()]

        def _cfg(self, controller=None):
            return se.SimConfig(
                lam_ns=self.v_ns.get() / 3600.0, lam_ew=self.v_ew.get() / 3600.0,
                seed=self.v_seed.get(), duration=self.v_dur.get(),
                ruleset=self.v_rules.get(), threshold=self.v_thr.get(),
                mode=self.v_mode.get(), disabled=frozenset(self.disabled),
                controller=controller or self._ctrl(),
                # lectura explicita de A y Q (ver traffic_model.CALIBRADA / LITERAL)
                **(dict(a_mode="crossing", q_mode="current", predicted_q=False) if self.v_mode.get() == "capacity"
                   else dict(a_mode="arrivals", q_mode="predicted", predicted_q=True)))

        def _set_ctrl_ui(self):
            """Activa o desactiva los controles segun el controlador y renombra los apartados de la columna derecha."""
            flco = self._ctrl() == "flco"
            for w in self.w_1977:
                w.config(state="disabled" if flco else "normal")
            names = (("Entradas", "Salida u", "Fuerza de reglas", "Traza d_m") if flco
                     else ("Reglas", "Grados", "Disparos", "Traza d_m"))
            for w, txt in zip(self.cb_panels, names):
                w.config(text=txt)
            self.lab_ctrl.config(text=(
                "FLC-O: 27 reglas con 3 entradas (G, R, V) aprendidas con CMA-ES; decide cada segundo y cambia de fase si u > 0 "
                "(verde mínimo 3 s, máximo 90 s). No tiene umbral ni las 25 reglas de 1977, por eso esos controles están apagados."
                if flco else
                "Pappis y Mamdani (1977): 25 reglas; interviene a los 7, 17, 27, 37 y 47 s de verde. El umbral y las reglas "
                "se cambian en vivo; la lectura de A y Q, al pulsar Reiniciar. Apagar reglas muestra cuánto aporta cada una."))

        def _on_ctrl(self):
            self._set_ctrl_ui()
            self.reset()

        def _apply_ref(self):
            if self.view is not None:
                self.view.set_reference(self._ref_label() if self.v_ref.get() else "")

        # ---------- personalizacion didactica ----------
        def _on_preset(self):
            v = PRESETS.get(self.v_preset.get())
            if v is not None:
                self.v_ns.set(v[0])
                self.v_ew.set(v[1])

        def _custom_preset(self):
            self.v_preset.set("Personalizado")

        def _apply_threshold(self):
            try:
                thr = float(self.v_thr.get())
            except Exception:                         # noqa: BLE001
                return
            if self.sim is not None:
                self.sim.cfg.threshold = thr
            if self.view is not None:
                self.view.set_threshold(thr)

        def _apply_view_opts(self):
            self.v_gap_val = float(self.v_gap.get())
            self.lab_gap.config(text=f"{self.v_gap_val:.1f}")
            if self.view is not None:
                self.view.set_car_options(gap=self.v_gap_val, mix=(self.v_mix.get() == "Variados"))
                self.view.set_detectors(self.v_detect.get())

        def _apply_panels(self):
            if self.view is not None:
                self.view.set_panels(rules=self.v_p_rules.get(), grade=self.v_p_grade.get(),
                                     fire=self.v_p_fire.get(), trace=self.v_p_trace.get())

        def _set_explain(self, text):
            self.explain.config(state=tk.NORMAL)
            self.explain.delete("1.0", tk.END)
            self.explain.insert("1.0", text)
            self.explain.config(state=tk.DISABLED)

        def _apply_explain(self):
            if not self.v_explain.get():
                self._set_explain("(Explicación desactivada. Marque «Explicar cada decisión» para verla.)")
            elif self.sim is not None and self.sim.flco is not None and self.sim.last_decision is not None:
                self._set_explain(self._explain_flco(self.sim.last_decision, self.sim.phase))
            elif self.sim is not None and self.sim.decisions:
                t, ph, d = self.sim.decisions[-1]
                self._set_explain(se.explain_decision(d, ph, t, self.sim.cfg.threshold))

        def _explain_flco(self, d, phase):
            return se.explain_flco(d, phase, self.sim.flco, self.sim.flco.gmin, self.sim.cfg.max_green)

        def _update_rules_label(self):
            n = 25 - len(self.disabled)
            self.lab_rules.config(text=f"{n} de 25 activas")

        def _apply_disabled(self):
            self._update_rules_label()
            if self.sim is not None:
                self.sim.cfg.disabled = frozenset(self.disabled)
            if self.view is not None:
                self.view.set_disabled(self.disabled)

        def open_rules_editor(self):
            import fuzzy_logic as fl
            win = tk.Toplevel(self.root)
            win.title("Encender / apagar reglas")
            win.transient(self.root)
            ttk.Label(win, text="Marque las reglas que el controlador puede usar. Una regla apagada no aporta a la decisión "
                                "(se aplica en vivo).", padding=6).grid(row=0, column=0, columnspan=5, sticky="w")
            vars_ = {}
            rules = se.load_ruleset(self.v_rules.get())

            def toggle(k, i):
                if vars_[(k, i)].get():
                    self.disabled.discard((k, i))
                else:
                    self.disabled.add((k, i))
                self._apply_disabled()

            for c, k in enumerate(fl.INTERVENTIONS):
                f = ttk.LabelFrame(win, text=f"Intervención de {k} s", padding=4)
                f.grid(row=1, column=c, sticky="n", padx=4, pady=4)
                for i, r in enumerate(rules[k]):
                    v = tk.BooleanVar(value=(k, i) not in self.disabled)
                    vars_[(k, i)] = v
                    T, A, Q, E = r
                    txt = f"R{i + 1}  T={T}\n     A=mt({A})\n     Q={'any' if Q == 'any' else 'lt(' + Q + ')'}"
                    ttk.Checkbutton(f, text=txt, variable=v, command=lambda kk=k, ii=i: toggle(kk, ii)).pack(anchor="w", pady=2)

            def preset(keep):
                for (k, i), v in vars_.items():
                    on = keep(i)
                    v.set(on)
                    (self.disabled.discard if on else self.disabled.add)((k, i))
                self._apply_disabled()

            bar = ttk.Frame(win, padding=6)
            bar.grid(row=2, column=0, columnspan=5, sticky="w")
            for txt, keep in (("Todas (25)", lambda i: True), ("Solo extremas R1 y R5 (10)", lambda i: i in (0, 4)),
                              ("Solo R1, R3 y R5 (15)", lambda i: i in (0, 2, 4)), ("Sin R5", lambda i: i != 4),
                              ("Solo R5 (5)", lambda i: i == 4)):
                ttk.Button(bar, text=txt, command=lambda kp=keep: preset(kp)).pack(side=tk.LEFT, padx=3)
            ttk.Button(bar, text="Cerrar", command=win.destroy).pack(side=tk.LEFT, padx=12)

        def open_help(self):
            win = tk.Toplevel(self.root)
            win.title("Ayuda del simulador")
            txt = tk.Text(win, width=100, height=34, wrap="word", font=("TkDefaultFont", 10), padx=8, pady=6)
            txt.insert("1.0", AYUDA)
            txt.config(state=tk.DISABLED)
            txt.pack(fill=tk.BOTH, expand=True)
            ttk.Button(win, text="Cerrar", command=win.destroy).pack(pady=4)

        def inject(self, arm, n):
            if self.sim is None or self.sim.done:
                self._build()
            self.sim.inject(arm, n)
            if self.ref is not None:
                self.ref.inject(arm, n)            # el otro controlador recibe los mismos autos
            self.status.config(text=f"Se agregan {n} auto(s) al brazo {'N-S' if arm == 0 else 'E-W'} "
                                    f"(entran de a uno por segundo).")

        def _build(self):
            cfg = self._cfg()
            self.sim = se.StepSim(cfg)
            otro = "pappis" if cfg.controller == "flco" else "flco"
            self.ref = se.StepSim(self._cfg(otro))              # el otro controlador, mismas llegadas
            if self.view is not None and (self.view.flco is None) != (cfg.flco is None):
                # cambia el tipo de panel de la derecha: se rehace la figura
                self.fig.canvas.mpl_disconnect(self.view._draw_cid)
                self.fig.clf()
                self.view = None
            if self.view is None:
                self.view = IntersectionView(self.fig, rules=cfg.rules, flco=cfg.flco, max_green=getattr(cfg, "max_green", 57))
            else:
                self.view.set_rules(cfg.rules)
            self.view.reset()
            self.view.set_threshold(self.v_thr.get())
            self.view.set_disabled(self.disabled)
            if cfg.controller == "flco":
                self.view.sub.set_text(
                    f"controlador: FLC-O ({cfg.flco_model}) · N-S {self.v_ns.get()} veh/h · "
                    f"E-W {self.v_ew.get()} veh/h · semilla {self.v_seed.get()}")
            else:
                self.view.sub.set_text(
                    f"reglas: {self.v_rules.get()} · umbral {self.v_thr.get():.2f}"
                    f" · N-S {self.v_ns.get()} veh/h · E-W {self.v_ew.get()} veh/h"
                    f" · lectura {'calibrada' if self.v_mode.get() == 'capacity' else 'literal'} · semilla {self.v_seed.get()}")
            self.view.set_reference(self._ref_label() if self.v_ref.get() else "")
            self.log.delete(0, tk.END)
            self.prog["value"] = 0
            self._apply_view_opts()
            self._apply_panels()
            self._set_explain(("Aquí aparecerá, en palabras simples, qué mira FLC-O y qué decide en cada segundo de verde."
                               if cfg.controller == "flco" else
                               "Aquí aparecerá, en palabras simples, la explicación de cada decisión del "
                               "controlador (cada 10 s de verde).") if self.v_explain.get() else
                              "(Explicación desactivada. Marque «Explicar cada decisión» para verla.)")
            self.status.config(text=f"Simulación lista: {self.v_dur.get()} s. "
                                    "Pulse Iniciar o Paso.")

        # -------------------------------------------------------------
        def _nsub(self):
            """Sub-cuadros por segundo simulado (movimiento suave): ~24 cuadros/s en pantalla."""
            return max(1, min(6, round(24 / max(1, self.v_fps.get()))))

        def _advance(self, st):
            """Pasa el segundo st a la vista y avanza tambien al otro controlador (curva punteada de la traza)."""
            rd = None
            if self.ref is not None and not self.ref.done:
                rd = self.ref.step().dm
            self.view.advance(st, ref_dm=rd)

        def _final_text(self, st):
            if self.sim.flco is not None:
                otro = f" · de 1977: {self.ref.dm:.3f}" if self.ref is not None else ""
            else:
                otro = f" · FLC-O: {self.ref.dm:.3f}" if self.ref is not None else ""
            res = f"{self.sim.dm_residual:.3f}" + (f" frente a {self.ref.dm_residual:.3f}" if self.ref is not None else "")
            return (f"Final: d_m = {st.dm:.3f} s/veh{otro} (convención del original, solo vehículos servidos). "
                    f"Con la espera residual del artículo: {res}.")

        def _after_state(self, st):
            d = st.decision
            if d is not None and getattr(d, "kind", "") == "flco":
                if d.event:
                    self.log.insert(tk.END, decision_line(st))
                    self.log.see(tk.END)
                    if self.v_pause_dec.get() and self.running:
                        self._pause_req = True
                if self.v_explain.get():
                    self._set_explain(self._explain_flco(d, st.phase))
            elif d is not None:
                self.log.insert(tk.END, decision_line(st))
                self.log.see(tk.END)
                if self.v_explain.get():
                    self._set_explain(se.explain_decision(st.decision, st.phase, st.t, self.sim.cfg.threshold))
                if self.v_pause_dec.get() and self.running:
                    self._pause_req = True
            self.prog["value"] = 1000 * st.t // max(1, self.sim.cfg.duration)
            mm, ss = divmod(st.t, 60)
            self.status.config(text=f"t = {mm:02d}:{ss:02d}  ·  d_m = {st.dm:.2f} s/veh")

        def _tick(self):
            if not self.running:
                return
            st = self.sim.step()
            self._advance(st)
            self._after_state(st)
            self._sub(0, self._nsub(), st)

        def _sub(self, j, sub, st):
            if not self.running:
                return
            self.view.draw_frame(1.0 / sub)
            # ritmo compensado: descuenta lo que tardo en dibujar para sostener los ticks/s pedidos
            self._due += 1.0 / (max(1, self.v_fps.get()) * sub)
            now = time.perf_counter()
            if self._due < now - 0.5:
                self._due = now
            delay = max(1, int((self._due - now) * 1000))
            if j + 1 < sub:
                self.after_id = self.root.after(delay, lambda: self._sub(j + 1, sub, st))
                return
            if st.done:
                self.running = False
                self.b_pause.config(state=tk.DISABLED, text="⏸ Pausa")
                self.b_start.config(state=tk.NORMAL)
                self.status.config(text=self._final_text(st))
                self.log.insert(tk.END, f"--- final: d_m = {st.dm:.3f} s/veh ---")
                self.log.see(tk.END)
                return
            if self._pause_req:                 # «Pausar en cada decisión»
                self._pause_req = False
                self.pause()
                self.status.config(text=f"Pausa en la decisión de t = {st.t} s. Pulse Continuar para seguir "
                                        f"o Paso para avanzar de a 1 s.")
                return
            self.after_id = self.root.after(delay, self._tick)

        # -------------------------------------------------------------
        def toggle_pause(self):
            if self.running:
                self.pause()
            else:
                self.start()

        def start(self):
            if self.running:
                return
            if self.sim is None or self.sim.done:
                self._build()
            self.running = True
            self._due = time.perf_counter()
            self.b_pause.config(state=tk.NORMAL, text="⏸ Pausa")
            self.b_start.config(state=tk.DISABLED)
            self.after_id = self.root.after(0, self._tick)

        def pause(self):
            if not self.running:
                return
            self.running = False
            if self.after_id is not None:
                self.root.after_cancel(self.after_id)
                self.after_id = None
            self.b_pause.config(text="▶ Continuar")
            self.b_start.config(state=tk.DISABLED)
            self.status.config(text="En pausa. Pulse Continuar o Paso.")

        def step1(self):
            if self.running:
                self.pause()
            if self.sim is None or self.sim.done:
                self._build()
            st = self.sim.step()
            self._advance(st)
            self._after_state(st)
            for _ in range(3):
                self.view.draw_frame(1.0 / 3)
                self.root.update_idletasks()
            if st.done:
                self.status.config(text=self._final_text(st))
                self.log.insert(tk.END, f"--- final: d_m = {st.dm:.3f} s/veh ---")
                self.log.see(tk.END)

        def save_csv(self):
            from tkinter import filedialog, messagebox
            if self.sim is None or not self.sim.decisions:
                messagebox.showinfo("Disparos", "Aún no hay decisiones que guardar.")
                return
            path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="disparos_reglas.csv",
                                                filetypes=[("CSV", "*.csv")])
            if path:
                write_firings_csv(self.sim, path)
                self.status.config(text=f"Disparos guardados: {os.path.basename(path)}")

        def save_png(self):
            from tkinter import filedialog
            path = filedialog.asksaveasfilename(defaultextension=".png", initialfile="simulacion.png",
                                                filetypes=[("PNG", "*.png")])
            if path:
                self.fig.savefig(path, dpi=130)
                self.status.config(text=f"Imagen guardada: {os.path.basename(path)}")

        def reset(self):
            self.running = False
            if self.after_id is not None:
                self.root.after_cancel(self.after_id)
                self.after_id = None
            self._build()
            self.b_pause.config(state=tk.DISABLED, text="⏸ Pausa")
            self.b_start.config(state=tk.NORMAL)

    root = tk.Tk()
    app = App(root)
    if test_hook is not None:
        test_hook(app, root)
        return
    root.mainloop()


# ===========================================================================
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Simulador interactivo del semáforo difuso: FLC-O (mejorado) "
                                 "y Pappis & Mamdani (1977)")
    ap.add_argument("--video", metavar="SALIDA.mp4",
                    help="modo sin interfaz: exporta el video a SALIDA")
    ap.add_argument("--controlador", choices=["flco", "pappis"], default="flco",
                    help="flco = FLC-O (el controlador mejorado, por defecto); pappis = Pappis y Mamdani (1977)")
    ap.add_argument("--sin-referencia", action="store_true",
                    help="con --video: no dibuja la curva d_m del otro controlador")
    ap.add_argument("--ns", type=int, default=720, help="flujo N-S (veh/h)")
    ap.add_argument("--ew", type=int, default=2160, help="flujo E-W (veh/h)")
    ap.add_argument("--rules", choices=["paper"], default="paper",
                    help="conjunto de reglas")
    ap.add_argument("--seed", type=int, default=1, help="semilla")
    ap.add_argument("--seconds", type=int, default=90,
                    help="duración de la simulación (s)")
    ap.add_argument("--fps", type=int, default=30, help="cuadros por segundo del video")
    ap.add_argument("--sub", type=int, default=3,
                    help="sub-cuadros por segundo simulado (movimiento suave; con --fps 30 y --sub 3 el video va a 10x)")
    ap.add_argument("--threshold", type=float, default=None,
                    help="umbral de decisión (paper: 0.5)")
    ap.add_argument("--mode", choices=["capacity", "literal"],
                    default="capacity", help="capacity = lectura calibrada; literal = ejemplo pág. 7")
    ap.add_argument("--csv", metavar="DISPAROS.csv", default=None,
                    help="con --video: guarda también los disparos de reglas en CSV")
    args = ap.parse_args()

    if args.video:
        thr = args.threshold
        if thr is None:
            thr = 0.50
        render_video(args.video, args.ns, args.ew, args.rules, args.seed,
                     args.seconds, args.fps, thr, args.mode, args.csv, args.sub,
                     controller=args.controlador, reference=not args.sin_referencia)
    else:
        run_gui(controlador=args.controlador)
