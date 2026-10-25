"""
test_disparos.py
================================================================================
Comprueba que el panel de REGLAS Y DISPAROS muestra lo mismo que calcula el
controlador, para las dos lecturas y varios caudales:
  1. el maximo de los aportes de las 5 reglas == vector grade(e) del controlador;
  2. e* coincide con la regla de decision (maximo, umbral 0.5, empate -> mayor e);
  3. las reglas que "disparan" son exactamente las que alcanzan el grado maximo en e*;
  4. un corte del verde no tiene regla ganadora y todo el vector es < 0.5;
  5. las decisiones ocurren a los 7, 17, 27, 37 y 47 s del verde (nunca despues de 57 s);
  6. el motor paso a paso no cambia el retardo respecto de la simulacion por lotes.
Uso:  python test_disparos.py
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


CASES = [(360, 720, 1), (720, 2160, 2), (1440, 1440, 3), (1080, 1800, 4)]
for mode in ("capacity", "literal"):
    print(f"lectura {'calibrada' if mode == 'capacity' else 'literal'}")
    n_dec = n_cut = 0
    bad = dict(agg=0, estar=0, win=0, cut=0, time=0)
    for ns, ew, seed in CASES:
        cfg = se.SimConfig(lam_ns=ns / 3600, lam_ew=ew / 3600, seed=seed, duration=1200, mode=mode)
        sim = se.StepSim(cfg)
        dm = sim.run_all()
        ref = tm.simulate_fuzzy(ns / 3600, ew / 3600, seed, 1200, mode=mode,
                                queue_source=cfg.queue_source)
        check(f"d_m igual a la simulacion por lotes ({ns}/{ew})", abs(dm - ref) < 1e-9)
        for t, ph, d in sim.decisions:
            n_dec += 1
            g = np.concatenate([[0.0], d.grades])
            bad["agg"] += not np.allclose(d.per_rule.max(axis=0), d.grades)
            bad["estar"] += fl.decide_extension(g, cfg.threshold) != d.e_star
            bad["time"] += d.elapsed not in fl.INTERVENTIONS
            if d.cut:
                n_cut += 1
                bad["cut"] += (len(d.winners) != 0) or (d.grades.max() >= cfg.threshold)
            else:
                ok = set(d.winners) == set(np.flatnonzero(d.per_rule[:, d.e_star - 1] >= d.grades[d.e_star - 1] - 1e-12))
                bad["win"] += not (ok and len(d.winners) >= 1)
    check(f"{n_dec} decisiones: max de reglas == grade(e)", bad["agg"] == 0)
    check("e* coincide con la regla de decision", bad["estar"] == 0)
    check("las reglas que disparan alcanzan el grado maximo en e*", bad["win"] == 0)
    check(f"{n_cut} cortes sin regla ganadora y con todo < 0.5", bad["cut"] == 0)
    check("decisiones solo a los 7, 17, 27, 37 y 47 s", bad["time"] == 0)

print("Animacion: la cola dibujada coincide con la cola del modelo")
for ns, ew, seed in CASES:
    sim = se.StepSim(se.SimConfig(lam_ns=ns / 3600, lam_ew=ew / 3600, seed=seed, duration=900))
    qv = {"ns": 0, "ew": 0}
    bad = 0
    while not sim.done:
        st = sim.step()
        qv["ns"] += int(st.arrived_ns) - int(st.discharge_ns)
        qv["ew"] += int(st.arrived_ew) - int(st.discharge_ew)
        bad += (qv["ns"] != st.q_ns) or (qv["ew"] != st.q_ew)
    check(f"autos dibujados == cola del modelo en cada segundo ({ns}/{ew})", bad == 0)

print(f"\n{'TODO OK' if fails == 0 else str(fails) + ' FALLOS'}")
sys.exit(1 if fails else 0)
