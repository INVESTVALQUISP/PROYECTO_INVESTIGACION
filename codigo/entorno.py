"""
entorno.py
================================================================================
Registra el entorno de ejecucion de los resultados: versiones de Python y NumPy, generador pseudoaleatorio y su mapa de
semillas, equipo (CPU, SO), tiempo de ejecucion de una simulacion de 7200 s por controlador y costo por decision del
controlador difuso. Salida: resultados/entorno.json     Uso:  python codigo/entorno.py
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import json
import os
import platform
import sys
import time

import numpy as np

import fuzzy_logic as fl
import traffic_model as tm


def cpu():
    try:
        for line in open("/proc/cpuinfo"):
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "desconocido"


def mejor(fn, n=3):
    best = 1e9
    for _ in range(n):
        t0 = time.perf_counter()
        fn()
        best = min(best, time.perf_counter() - t0)
    return best


def main():
    rng = np.random.default_rng(0)
    l1, l2 = 720 / 3600, 2160 / 3600
    t = {
        "ciclo_fijo": mejor(lambda: tm.simulate_fixed_cycle(l1, l2, 0, 7200)),
        "actuado": mejor(lambda: tm.simulate_actuated(l1, l2, 0, 7200)),
        "difuso": mejor(lambda: tm.simulate_fuzzy(l1, l2, 0, 7200, **tm.CALIBRADA)),
    }
    wg = [1, 0, 1, 1, 0, 1, 1, 0, 0, 1]
    n = 2000
    t0 = time.perf_counter()
    for _ in range(n):
        fl.fuzzy_decision(wg, wg, 5, fl.RULES[17], a_mode="crossing", q_mode="current", q_green=4)
    por_decision = (time.perf_counter() - t0) / n
    out = dict(
        python=sys.version.split()[0], implementacion=platform.python_implementation(), numpy=np.__version__,
        generador=type(rng.bit_generator).__name__ + " (np.random.default_rng)",
        semillas="ciclo fijo y difuso: semilla k = 0..19 en la replica k (numeros aleatorios comunes); llegadas: rng.random(N) < tasa por segundo",
        so=platform.platform(), cpu=cpu(), nucleos=os.cpu_count(),
        segundos_por_simulacion_7200s=t, segundos_por_decision_difuso=por_decision,
        complejidad_por_decision="O(R·|E|) = O(5 reglas x 10 extensiones) = O(1)")
    json.dump(out, open("resultados/entorno.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
