"""
opt_nombres.py
================================================================================
Nombres cortos y etiquetas de los controladores en las tablas y figuras del articulo, y los modelos elegidos como
"finales" (resultados/opt/modelos_finales.json: rol -> nombre del modelo entrenado).
"""
import json
import os

ETIQUETA = {
    "fijo": "Ciclo fijo (Webster)",
    "actuado": "Actuado (hueco 3 s)",
    "actuado_af": "Actuado afinado",
    "maxpressure": "Presión máxima",
    "pappis": "Pappis y Mamdani",
    "afinado_pappis": "Pappis y Mamdani afinado",
    "mdp": "Óptimo (PD, caudales conocidos)",
    "flc": "FLC-O (propuesto)",
    "flc_causal": "FLC-O causal",
    "mlp": "Política neuronal (referencia)",
    "mlp_causal": "Política neuronal causal",
}

# orden de las columnas en las tablas
ORDEN_REFERENCIAS = ["fijo", "actuado", "actuado_af", "pappis"]


def finales(ruta="resultados/opt/modelos_finales.json"):
    """{rol: nombre del modelo entrenado}; roles: flc, flc_causal, mlp, mlp_causal, afinado."""
    if os.path.exists(ruta):
        return json.load(open(ruta))
    return {}


def clave(rol, fin=None):
    """Nombre bajo el que aparece el controlador en evaluacion_final.json."""
    fin = fin if fin is not None else finales()
    if rol in ("fijo", "actuado", "actuado_af", "maxpressure", "pappis", "mdp"):
        return rol
    return fin.get({"afinado_pappis": "afinado"}.get(rol, rol), rol)
