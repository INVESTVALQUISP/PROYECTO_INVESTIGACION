"""Validacion de equivalencia: StepSim.run_all() == simulate_fuzzy().

El motor por pasos (sim_engine, que alimenta el simulador GUI/web) debe devolver
exactamente el mismo d_m que la simulacion por lotes (traffic_model), para las dos
lecturas del controlador y para varios caudales/semillas.
"""
import sys

import sim_engine as se
import traffic_model as tm

CASES = [(360, 720, 1, 7200), (720, 1440, 2, 7200), (1440, 1440, 3, 3600),
         (360, 2520, 7, 3600), (720, 720, 11, 1800)]


def main():
    failures = total = 0
    for name, cfg_kw in (("calibrada", tm.CALIBRADA), ("literal", tm.LITERAL)):
        for (ns, ew, seed, dur) in CASES:
            total += 1
            ref = tm.simulate_fuzzy(ns / 3600.0, ew / 3600.0, seed, dur, **cfg_kw)
            cfg = se.SimConfig(lam_ns=ns / 3600.0, lam_ew=ew / 3600.0, seed=seed,
                               duration=dur, **cfg_kw)
            got = se.StepSim(cfg).run_all()
            ok = abs(got - ref) < 1e-9
            print(f"{name:9s} {ns}/{ew} seed={seed:2d} dur={dur:5d} "
                  f"ref={ref:9.4f} step={got:9.4f} {'OK' if ok else 'FALLO'}")
            failures += not ok
    print(f"\n{total - failures}/{total} equivalencias correctas")
    return failures


if __name__ == "__main__":
    sys.exit(main())
