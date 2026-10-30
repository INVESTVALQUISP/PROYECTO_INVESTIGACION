"""
test_sim_flco.py
================================================================================
Pruebas del simulador INTERACTIVO con FLC-O (sim_engine.StepSim con controller="flco" e intersection_view con flco):
  1. el motor paso a paso da, en 6 escenarios (uno saturado), el mismo retardo con espera residual, el mismo retardo
     "solo servidos" y el mismo numero de cambios de fase que el simulador por lotes (sim_batch + opt_flc2.FuzzyOpt);
  2. respeta el verde minimo y el verde maximo del modelo (en escenarios donde el maximo se alcanza);
  3. los autos agregados a mano entran uno por segundo y se cuentan;
  4. las fuerzas de las 27 reglas suman 1 y la salida u es su promedio ponderado de los consecuentes;
  5. la vista dibuja FLC-O: barras de fuerza, salida u, cambios de fase en la traza, curva del controlador de
     referencia sobre las mismas llegadas y apartados que se pueden ocultar;
  6. la explicacion en palabras y el CSV (27 filas por cambio de fase);
  7. el controlador de 1977 sigue sin paneles de FLC-O y una configuracion invalida da error;
  8. la API del simulador web con FLC-O (si flask esta instalado).
Con --gui prueba ademas la ventana Tk (necesita pantalla; ejecutar_pruebas.py no lo usa).
Uso:  python test_sim_flco.py [--gui]
"""
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg

import sim_engine as se
from intersection_view import IntersectionView
from sim_batch import BatchSim, make_arrivals

fails = 0


def check(name, ok, detail=""):
    global fails
    print(f"  [{'OK' if ok else 'FALLO'}] {name} {detail}")
    fails += 0 if ok else 1


def cfg_flco(ns, ew, seed, dur, **kw):
    return se.SimConfig(lam_ns=ns / 3600.0, lam_ew=ew / 3600.0, seed=seed, duration=dur, controller="flco", **kw)


print("Motor paso a paso con FLC-O == simulador por lotes")
for seed, ns, ew, dur in [(3, 720, 2160, 1200), (1, 360, 360, 900), (7, 1440, 1440, 1500), (2, 360, 2520, 1000),
                          (5, 1080, 1800, 1300), (11, 1800, 1800, 1800)]:
    cfg = cfg_flco(ns, ew, seed, dur)
    sim = se.StepSim(cfg)
    sim.run_all()
    r = BatchSim(make_arrivals(ns / 3600.0, ew / 3600.0, [seed], dur), max_green=cfg.max_green).run(cfg.flco)
    ok = (sim.sim.total_delay + sim.sim.residual_delay(dur) == int(r["D"][0])
          and abs(sim.dm - float(r["delay_served"][0])) < 1e-12 and len(sim.decisions) == int(r["n_switch"][0]))
    check(f"N-S {ns} / E-W {ew}, semilla {seed}, {dur} s", ok,
          f"(D = {int(r['D'][0])}, {int(r['n_switch'][0])} cambios, d_m = {sim.dm:.3f})")

print("Verde minimo y maximo")
for ns, ew in ((3000, 60), (60, 3000)):
    cfg = cfg_flco(ns, ew, 4, 900)
    sim = se.StepSim(cfg)
    sim.run_all()
    el = [d.elapsed for _, _, d in sim.decisions]
    forzados = sum(d.forced for _, _, d in sim.decisions)
    check(f"N-S {ns} / E-W {ew}: todos los verdes entre {cfg.flco.gmin} y {cfg.max_green} s y alguno llega al maximo",
          min(el) >= cfg.flco.gmin and max(el) <= cfg.max_green and forzados > 0,
          f"(de {min(el)} a {max(el)} s, {forzados} por verde maximo)")

print("Autos agregados a mano")
cfg = cfg_flco(360, 360, 1, 200)
base = se.StepSim(cfg)
base.run_all()
sim = se.StepSim(cfg_flco(360, 360, 1, 200))
sim.inject(1, 7)
sim.run_all()
check("7 autos agregados al brazo E-W suman 7 llegadas", sim.sim.total_arrivals == base.sim.total_arrivals + 7,
      f"({base.sim.total_arrivals} -> {sim.sim.total_arrivals})")

print("Fuerza de las reglas y salida u")
sim = se.StepSim(cfg_flco(720, 2160, 3, 300))
ds = []
while not sim.done:
    st = sim.step()
    ds.append(st.decision)
ds = [d for d in ds if d is not None]
c = sim.flco.c
check("las 27 fuerzas suman 1 en cada segundo de verde", all(abs(d.weights.sum() - 1.0) < 1e-6 and len(d.weights) == 27 for d in ds),
      f"({len(ds)} decisiones)")
check("u = suma de fuerza x consecuente", all(abs(d.u - float(d.weights @ c)) < 1e-6 for d in ds))
check("cambia de fase solo si u > 0 (o por verde maximo) y despues del verde minimo",
      all((d.switch == ((not d.locked) and d.u > 0 or d.forced)) for d in ds))

print("Vista de FLC-O")
cfg = cfg_flco(720, 2160, 3, 200)
sim = se.StepSim(cfg)
ref = se.StepSim(se.SimConfig(lam_ns=720 / 3600.0, lam_ew=2160 / 3600.0, seed=3, duration=200))
fig = plt.figure(figsize=(16.0, 9.2), dpi=60)
canvas = FigureCanvasAgg(fig)
view = IntersectionView(fig, rules=cfg.rules, flco=cfg.flco, max_green=cfg.max_green)
view.reset()
view.set_reference("Pappis y Mamdani (1977), mismas llegadas")
n_sw, ultimo = 0, None
for _ in range(60):
    st = sim.step()
    view.advance(st, ref_dm=ref.step().dm)
    view.draw_frame(1.0)
    n_sw += 1 if (st.decision is not None and st.decision.switch) else 0
    ultimo = st.decision if st.decision is not None else ultimo
check("27 barras de fuerza y la ultima coincide con la decision", len(view._fl_bars) == 27 and np.allclose(
    [b.get_width() for b in view._fl_bars], ultimo.weights))
check("la barra de la salida u mide u", abs(view._fl_ubar.get_width() - ultimo.u) < 1e-12)
check("la traza marca un cuadrado por cambio de fase y ningun triangulo", len(view._ct) == n_sw and len(view._xt) == 0,
      f"({n_sw} cambios en 60 s)")
check("la curva de referencia tiene un punto por segundo y su ultimo valor es el del otro controlador",
      len(view._rd) == 60 and abs(view._rd[-1] - ref.dm) < 1e-12 and view.ln_ref.get_visible())
view.set_panels(rules=False, grade=False, fire=False, trace=True)
check("ocultar los apartados oculta tambien las barras y los marcadores animados",
      not any(a.get_visible() for k in ("rules", "grade", "fire") for a in view._fl_grp[k]))
view.set_panels(rules=True, grade=True, fire=True, trace=True)
check("mostrarlos de nuevo los restaura", all(a.get_visible() for a in view._fl_grp["rules"] + view._fl_grp["grade"]))
view.reset()
check("reiniciar deja la traza vacia y las barras en blanco", len(view._tt) == 0 and len(view._rd) == 0
      and all(b.get_width() == 0 for b in view._fl_bars))
plt.close(fig)

print("Explicacion y CSV")
sw = [(t, ph, d) for t, ph, d in sim.decisions]
txt = se.explain_flco(sim.last_decision, sim.phase, sim.flco, sim.flco.gmin, sim.cfg.max_green)
check("la explicacion nombra G, R, V, las reglas que mas pesan y la salida u", all(k in txt for k in ("G (demanda", "R (presión", "V =", "Reglas que más pesan", "u =")))
rows = sim.firing_rows()
check("el CSV tiene 27 filas por cada cambio de fase", len(rows) == 27 * len(sw) and len(sw) > 0, f"({len(sw)} cambios, {len(rows)} filas)")

print("Controlador de 1977 y configuraciones invalidas")
sim77 = se.StepSim(se.SimConfig(lam_ns=720 / 3600.0, lam_ew=2160 / 3600.0, seed=3, duration=120))
fig = plt.figure(figsize=(16.0, 9.2), dpi=60)
canvas = FigureCanvasAgg(fig)
v77 = IntersectionView(fig, rules=sim77.cfg.rules)
check("la vista del controlador de 1977 no tiene paneles de FLC-O", v77.flco is None and not hasattr(v77, "_fl_bars"))
plt.close(fig)
try:
    se.SimConfig(controller="otro")
    ok = False
except ValueError:
    ok = True
check("un controlador desconocido da error", ok)
try:
    se.cargar_flco("mlp_v3_g3")
    ok = False
except ValueError:
    ok = True
check("un modelo que no es FLC-O da error", ok)

print("Simulador web con FLC-O")
try:
    import web_sim
except ImportError:
    print("  (omitida: flask no esta instalado)")
else:
    cl = web_sim.app.test_client()
    r = cl.get("/api/start?ns=720&ew=2160&dur=30&seed=1&ctrl=flco&ref=1").get_json()
    n = 1
    while not r["done"]:
        r = cl.get("/api/tick").get_json()
        n += 1
    check("30 ticks con FLC-O y el otro controlador de referencia", n == 30 and r["ctrl"] == "flco" and r["ref_dm"] is not None
          and r["dm_res"] is not None and r["ref_dm_res"] is not None and len(r["frame"]) > 1000)
    r = cl.get("/api/start?ns=720&ew=2160&dur=30&seed=1&ctrl=pappis&ref=0").get_json()
    check("con ctrl=pappis y sin referencia", r["ctrl"] == "pappis" and r["ref_dm"] is None)
    check("la pagina se sirve", cl.get("/").status_code == 200 and b"FLC-O" in cl.get("/").data)

if "--gui" in sys.argv:
    print("Ventana Tk")
    import simulador_gui
    out = {}

    def hook(app, root):
        app.v_dur.set(60)
        app.reset()
        for _ in range(60):
            app.step1()
        out["flco"] = (app.sim.cfg.controller, app.sim.t, app.ref is not None, app.log.size())
        app.v_ctrl.set(simulador_gui.NOMBRES["pappis"])
        app._on_ctrl()
        for _ in range(20):
            app.step1()
        out["pappis"] = (app.sim.cfg.controller, app.sim.t, app.view.flco is None)
        root.destroy()

    simulador_gui.run_gui(test_hook=hook, controlador="flco")
    check("la ventana arranca con FLC-O, corre 60 s y registra cambios de fase",
          out["flco"][0] == "flco" and out["flco"][2] and out["flco"][3] > 0, f"{out['flco']}")
    check("cambiar a Pappis y Mamdani rehace la vista y reinicia", out["pappis"][0] == "pappis" and out["pappis"][2], f"{out['pappis']}")

print("TODO OK" if fails == 0 else f"{fails} FALLOS")
sys.exit(1 if fails else 0)
