"""
test_parametros.py
================================================================================
Comprueba que la configuracion de las lecturas de A y Q es EXPLICITA y que ningun parametro se ignora en silencio:
  1. traffic_model.CALIBRADA y LITERAL fijan a_mode, q_mode, predicted_q y queue_source;
  2. fuzzy_logic._resolve_modes respeta predicted_q siempre (tambien con mode = 'capacity');
  3. SimConfig y el simulador por lotes dan el mismo resultado con CALIBRADA y LITERAL;
  4. la definicion de mt / lt es la de la Tabla V impresa (mt(none)(1) = 0.5) y lt U mt = complemento en todo el universo.
Uso:  python test_parametros.py
"""
import sys

import numpy as np

import fuzzy_logic as fl
import sim_engine as se
import traffic_model as tm

fails = 0


def check(name, ok, detail=""):
    global fails
    print(f"  [{'OK' if ok else 'FALLO'}] {name} {detail}")
    fails += 0 if ok else 1


print("Configuracion explicita de las lecturas")
cal, lit = tm.CALIBRADA, tm.LITERAL
check("CALIBRADA = crossing / current / predicted_q=False / green_arrivals",
      (cal["a_mode"], cal["q_mode"], cal["predicted_q"], cal["queue_source"]) == ("crossing", "current", False, "green_arrivals"))
check("LITERAL = arrivals / predicted / predicted_q=True / total",
      (lit["a_mode"], lit["q_mode"], lit["predicted_q"], lit["queue_source"]) == ("arrivals", "predicted", True, "total"))
check("predicted_q=True se respeta con mode='capacity' (antes se ignoraba)", fl._resolve_modes("capacity", True, None, None) == ("crossing", "predicted"))
check("predicted_q=False se respeta con mode='literal'", fl._resolve_modes("literal", False, None, None) == ("arrivals", "current"))
check("sin predicted_q: capacity -> current y literal -> predicted",
      fl._resolve_modes("capacity", None, None, None)[1] == "current" and fl._resolve_modes("literal", None, None, None)[1] == "predicted")
check("a_mode y q_mode explicitos mandan sobre mode y predicted_q", fl._resolve_modes("literal", True, "crossing", "current") == ("crossing", "current"))
d = se.SimConfig()
check("SimConfig() queda explicitamente CALIBRADA (crossing / current / predicted_q=False / green_arrivals)",
      (d.a_mode, d.q_mode, d.predicted_q, d.queue_source) == ("crossing", "current", False, "green_arrivals"))
d = se.SimConfig(mode="literal")
check("SimConfig(mode='literal') queda explicitamente LITERAL (arrivals / predicted / True / total)",
      (d.a_mode, d.q_mode, d.predicted_q, d.queue_source) == ("arrivals", "predicted", True, "total"))
d = se.SimConfig(predicted_q=True)
check("SimConfig(predicted_q=True) con mode='capacity' conserva predicted_q=True y q_mode='predicted'",
      (d.predicted_q, d.q_mode) == (True, "predicted"))

print("Equivalencia entre motores")
for name, kw, mode in (("CALIBRADA", cal, "capacity"), ("LITERAL", lit, "literal")):
    dm_b = tm.simulate_fuzzy(720 / 3600, 2160 / 3600, 3, 1200, **kw)
    cfg = se.SimConfig(lam_ns=720 / 3600, lam_ew=2160 / 3600, seed=3, duration=1200, mode=mode,
                       a_mode=kw["a_mode"], q_mode=kw["q_mode"], predicted_q=kw["predicted_q"], queue_source=kw["queue_source"])
    check(f"{name}: motor paso a paso == simulacion por lotes", abs(se.StepSim(cfg).run_all() - dm_b) < 1e-9)

print("Operadores mt / lt (Tabla V impresa)")
check("mt(none)(1) = 0.5, como la Tabla V impresa", abs(fl.mt_arr("none", 1) - 0.5) < 1e-12)
ok = True
for name, f in fl.MU_ARR.items():
    x0 = int(np.argmax(f)) + 1
    for x in range(1, 11):
        mu = f[x - 1]
        lt = (1 - mu) if x < x0 else 0.0
        mt = fl.mt_arr(name, x)
        ok &= abs(max(lt, mt) - (1 - mu)) < 1e-12 and min(lt, mt) == 0
check("lt U mt = complemento y lt n mt = vacio en TODO el universo de los 6 conjuntos de arribos (incluido x0)", ok)

print("Contabilidad del retardo")
arr_ns, arr_ew = tm._make_arrivals(720 / 3600, 2160 / 3600, 1, 900)
sim = tm.Sim(arr_ns, arr_ew)
acc = [0]
orig = sim.tick


def tick(t, g):
    orig(t, g)
    acc[0] += len(sim.q_ns) + len(sim.q_ew)


sim.tick = tick
t, ph = 0, 0
while t < 900:
    t = sim.run_green_fuzzy(ph, t, 900, **cal)
    t = sim.transition(t, 900)
    ph = 1 - ph
check("suma por segundo de las colas == espera de los que salieron + espera residual", abs(acc[0] - (sim.total_delay + sim.residual_delay(900))) < 1e-9)

print(f"\n{'TODO OK' if fails == 0 else str(fails) + ' FALLOS'}")
sys.exit(1 if fails else 0)
