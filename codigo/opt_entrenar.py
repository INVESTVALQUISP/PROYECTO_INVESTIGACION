"""
opt_entrenar.py
================================================================================
Escenarios y funciones de evaluacion comunes a los experimentos de optimizacion.

Protocolo (para evitar sobreajuste a lo que luego se reporta):
  * ENTRENAMIENTO: caudales sorteados al azar (no son los de la Tabla VIII) y semillas 100000+.
  * VALIDACION:    caudales sorteados distintos y semillas 200000+ (eleccion del mejor entrenamiento).
  * PRUEBA:        los 16 pares de caudales de la Tabla VIII del paper con las semillas 0..19 (las mismas
                   20 replicas y los mismos numeros aleatorios comunes que usa el resto del articulo),
                   y conjuntos adicionales (caudales no vistos, demanda variable, sobresaturacion).
El objetivo es el retardo medio por vehiculo CON residuo (toda la espera hasta el horizonte), normalizado por el
del controlador de referencia en el mismo escenario para que todos los niveles de demanda pesen igual.
"""
import numpy as np

import traffic_model as tm
from sim_batch import make_arrivals, BatchSim
from opt_controladores import FixedCycle, Actuated, PappisFuzzy

H_ENTRENA = 3600
H_PRUEBA = 7200
SEMILLA_ENTRENA = 100000
SEMILLA_VALIDA = 200000


def caudales_aleatorios(n, rng, suma_min=540, suma_max=3000, q_min=180):
    """n pares (veh/h) con q_min <= cada brazo y suma entre suma_min y suma_max (y < 3600 = saturacion)."""
    out = []
    while len(out) < n:
        a, b = rng.uniform(q_min, suma_max - q_min, size=2)
        if suma_min <= a + b <= suma_max:
            out.append((a, b))
    return np.array(out)


def construir(flujos_vh, semillas, H, perfil=None):
    flujos_vh = np.asarray(flujos_vh, dtype=float)
    return make_arrivals(flujos_vh[:, 0] / 3600.0, flujos_vh[:, 1] / 3600.0, semillas, H, profile=perfil)


def escenarios_entrenamiento(n=64, H=H_ENTRENA, seed=1, semilla0=SEMILLA_ENTRENA):
    rng = np.random.default_rng(seed)
    fl = caudales_aleatorios(n, rng)
    return fl, construir(fl, semilla0 + np.arange(n), H)


def escenarios_validacion(n=64, H=H_PRUEBA, seed=2, semilla0=SEMILLA_VALIDA):
    rng = np.random.default_rng(seed)
    fl = caudales_aleatorios(n, rng)
    return fl, construir(fl, semilla0 + np.arange(n), H)


def escenarios_oficiales(reps=20, H=H_PRUEBA):
    """Los 16 pares de la Tabla VIII x semillas 0..reps-1. Devuelve (flujos (R,2), arrivals)."""
    fl = np.array([c for c in tm.COMBINATIONS for _ in range(reps)], dtype=float)
    sem = np.array([s for _ in tm.COMBINATIONS for s in range(reps)])
    return fl, construir(fl, sem, H)


def correr_referencias(arr, flujos_vh, max_verde=57):
    """Retardo medio con residuo de los tres controladores de referencia en los escenarios de arr."""
    ln, le = flujos_vh[:, 0] / 3600.0, flujos_vh[:, 1] / 3600.0
    return {
        "fijo": BatchSim(arr, max_green=None).run(FixedCycle(ln, le)),
        "actuado": BatchSim(arr, max_green=max_verde).run(Actuated(7, 3)),
        "Pappis": BatchSim(arr).run(PappisFuzzy()),
    }
