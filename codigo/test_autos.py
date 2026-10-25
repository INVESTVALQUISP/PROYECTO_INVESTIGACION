"""
test_autos.py
================================================================================
Comprueba las funciones didacticas del simulador:
  1. los autos dibujados nunca se acercan menos de GAP_HARD_MIN al de adelante (ni se superponen),
     con distintas separaciones y tipos de auto, y su numero coincide con la cola del modelo;
  2. apagar reglas: sin apagar nada el resultado no cambia; con todas apagadas el controlador siempre corta;
     apagar R5 empeora el retardo (cada regla aporta);
  3. «Agregar autos a mano» suma exactamente los autos pedidos;
  4. la explicacion de cada decision menciona la extension elegida y las reglas que deciden.
Uso:  python test_autos.py
"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import sim_engine as se
from intersection_view import IntersectionView, GAP_HARD_MIN

fails = 0


def check(name, ok, detail=""):
    global fails
    print(f"  [{'OK' if ok else 'FALLO'}] {name} {detail}")
    fails += 0 if ok else 1


print("Autos: separacion y cola dibujada")
for ns, ew, seed, gap, mix in ((720, 2160, 1, 2.2, True), (1440, 1440, 3, 0.8, True),
                               (360, 2520, 2, 5.0, False), (1080, 1800, 4, 2.2, True)):
    sim = se.StepSim(se.SimConfig(lam_ns=ns / 3600, lam_ew=ew / 3600, seed=seed, duration=3600))
    fig = plt.figure(figsize=(6, 4))
    view = IntersectionView(fig, rules=sim.cfg.rules, panels=False)
    view.reset()
    view.set_car_options(gap=gap, mix=mix)
    worst, mism = 1e9, 0
    for _ in range(900):
        st = sim.step()
        view._advance_cars(st)
        view._model_q = {"ns": st.q_ns, "ew": st.q_ew}
        mism += (len(view._queue["ns"]) != st.q_ns) or (len(view._queue["ew"]) != st.q_ew)
        for _k in range(3):
            view._move_cars(1 / 3)
            for arm in ("ns", "ew"):
                lane = view._cross[arm] + view._queue[arm]
                for a, b in zip(lane, lane[1:]):
                    worst = min(worst, (a["p"] - b["p"]) - (a["L"] + b["L"]) / 2)
    plt.close(fig)
    check(f"{ns}/{ew}, separacion {gap}: hueco minimo {worst:.2f} >= {GAP_HARD_MIN}", worst >= GAP_HARD_MIN - 1e-9)
    check("autos dibujados == cola del modelo en cada segundo", mism == 0)

print("Reglas apagadas")
base = se.StepSim(se.SimConfig(seed=1, duration=900)).run_all()
same = se.StepSim(se.SimConfig(seed=1, duration=900, disabled=frozenset())).run_all()
check("sin apagar nada el retardo no cambia", abs(base - same) < 1e-12)
none = se.StepSim(se.SimConfig(seed=1, duration=900,
                               disabled=frozenset((k, i) for k in (7, 17, 27, 37, 47) for i in range(5))))
none.run_all()
check("con las 25 reglas apagadas el controlador siempre corta",
      all(d.cut and not d.winners for _, _, d in none.decisions) and len(none.decisions) > 0)
no_r5 = se.StepSim(se.SimConfig(seed=1, duration=900, disabled=frozenset((k, 4) for k in (7, 17, 27, 37, 47)))).run_all()
check(f"apagar R5 empeora el retardo ({base:.1f} -> {no_r5:.1f} s/veh)", no_r5 > base)

print("Agregar autos a mano")
s1 = se.StepSim(se.SimConfig(seed=1, duration=300))
s2 = se.StepSim(se.SimConfig(seed=1, duration=300))
s2.inject(0, 5)
s2.inject(1, 3)
for _ in range(120):
    s1.step()
    s2.step()
extra = s2.sim.total_arrivals - s1.sim.total_arrivals
check(f"se agregan exactamente 8 autos (diferencia {extra})", extra == 8 and s2.pending == {0: 0, 1: 0})

print("Explicacion de cada decision")
bad = 0
for t, ph, d in s1.decisions:
    txt = se.explain_decision(d, ph, t)
    ok = (f"{d.e_star} s" in txt) if not d.cut else ("CORTA" in txt)
    bad += not ok
check(f"{len(s1.decisions)} decisiones explicadas con su extension o su corte", bad == 0 and len(s1.decisions) > 0)

print(f"\n{'TODO OK' if fails == 0 else str(fails) + ' FALLOS'}")
sys.exit(1 if fails else 0)
