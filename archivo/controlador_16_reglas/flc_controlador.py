"""
Controlador de Lógica Difusa (FLC) tipo Mamdani para extensión
del tiempo de verde semafórico.

Entradas:
    - Longitud de Cola (Q)
    - Tasa de Llegada (A)

Salida:
    - Extensión del Verde (E)
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# ============================================================
# 0. Carpeta de resultados
# ============================================================
# Se crea "resultados" en el mismo directorio donde está este código.
DIRECTORIO_CODIGO = os.path.dirname(os.path.abspath(__file__))
CARPETA_RESULTADOS = os.path.join(DIRECTORIO_CODIGO, "resultados")

os.makedirs(CARPETA_RESULTADOS, exist_ok=True)

# ============================================================
# 1. Universos de discurso
# ============================================================
Q = ctrl.Antecedent(
    np.arange(0, 31, 1),
    'cola'
)  # 0-30 vehículos

A = ctrl.Antecedent(
    np.arange(0, 15.5, 0.5),
    'llegada'
)  # 0-15 veh/min

E = ctrl.Consequent(
    np.arange(0, 26, 1),
    'extension'
)  # 0-25 segundos


# ============================================================
# 2. Funciones de membresía
# ============================================================

# --- Longitud de cola ---
Q['corta'] = fuzz.trapmf(
    Q.universe, [0, 0, 3, 7]
)

Q['media'] = fuzz.trimf(
    Q.universe, [4, 9, 14]
)

Q['larga'] = fuzz.trimf(
    Q.universe, [11, 17, 23]
)

Q['muy_larga'] = fuzz.trapmf(
    Q.universe, [18, 24, 30, 30]
)


# --- Tasa de llegada ---
A['baja'] = fuzz.trapmf(
    A.universe, [0, 0, 1.5, 4]
)

A['moderada'] = fuzz.trimf(
    A.universe, [2, 5, 8]
)

A['alta'] = fuzz.trimf(
    A.universe, [6, 9.5, 13]
)

A['muy_alta'] = fuzz.trapmf(
    A.universe, [10, 13, 15, 15]
)


# --- Extensión del verde ---
E['muy_corta'] = fuzz.trimf(
    E.universe, [0, 0, 4]
)

E['corta'] = fuzz.trimf(
    E.universe, [2, 6, 10]
)

E['media'] = fuzz.trimf(
    E.universe, [8, 12.5, 17]
)

E['larga'] = fuzz.trimf(
    E.universe, [15, 19, 23]
)

E['muy_larga'] = fuzz.trimf(
    E.universe, [20, 25, 25]
)

E.defuzzify_method = 'centroid'


# ============================================================
# 3. Base de reglas
#    16 reglas: combinatoria completa 4x4
# ============================================================
reglas = [
    ctrl.Rule(Q['corta'] & A['baja'], E['muy_corta']),
    ctrl.Rule(Q['corta'] & A['moderada'], E['corta']),
    ctrl.Rule(Q['corta'] & A['alta'], E['media']),
    ctrl.Rule(Q['corta'] & A['muy_alta'], E['media']),

    ctrl.Rule(Q['media'] & A['baja'], E['corta']),
    ctrl.Rule(Q['media'] & A['moderada'], E['media']),
    ctrl.Rule(Q['media'] & A['alta'], E['larga']),
    ctrl.Rule(Q['media'] & A['muy_alta'], E['larga']),

    ctrl.Rule(Q['larga'] & A['baja'], E['media']),
    ctrl.Rule(Q['larga'] & A['moderada'], E['larga']),
    ctrl.Rule(Q['larga'] & A['alta'], E['muy_larga']),
    ctrl.Rule(Q['larga'] & A['muy_alta'], E['muy_larga']),

    ctrl.Rule(Q['muy_larga'] & A['baja'], E['larga']),
    ctrl.Rule(Q['muy_larga'] & A['moderada'], E['muy_larga']),
    ctrl.Rule(Q['muy_larga'] & A['alta'], E['muy_larga']),
    ctrl.Rule(Q['muy_larga'] & A['muy_alta'], E['muy_larga']),
]

sistema_control = ctrl.ControlSystem(reglas)
simulador = ctrl.ControlSystemSimulation(sistema_control)


# ============================================================
# 4. Función para calcular la extensión
# ============================================================
def calcular_extension(
    cola_actual: float,
    tasa_llegada: float
) -> float:
    """
    Devuelve la extensión de verde (segundos) para una
    cola y tasa de llegada dadas.
    """

    simulador.input['cola'] = cola_actual
    simulador.input['llegada'] = tasa_llegada

    simulador.compute()

    return simulador.output['extension']


# ============================================================
# 5. Guardar funciones de membresía
# ============================================================
def guardar_funciones_membresia():
    """Guarda las gráficas de las funciones de membresía."""

    # --------------------------------------------------------
    # Gráfica de Longitud de Cola
    # --------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 6))

    for nombre in Q.terms:
        ax.plot(
            Q.universe,
            Q[nombre].mf,
            linewidth=2,
            label=nombre.replace('_', ' ').title()
        )

    ax.set_title(
        'Funciones de Membresía - Longitud de Cola',
        fontsize=14,
        fontweight='bold'
    )
    ax.set_xlabel('Longitud de Cola (vehículos)')
    ax.set_ylabel('Grado de Membresía')
    ax.set_ylim(-0.05, 1.05)
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()

    ruta = os.path.join(
        CARPETA_RESULTADOS,
        'funciones_membresia_cola.png'
    )

    fig.savefig(ruta, dpi=300, bbox_inches='tight')
    plt.close(fig)

    print(f"Gráfica guardada: {ruta}")


    # --------------------------------------------------------
    # Gráfica de Tasa de Llegada
    # --------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 6))

    for nombre in A.terms:
        ax.plot(
            A.universe,
            A[nombre].mf,
            linewidth=2,
            label=nombre.replace('_', ' ').title()
        )

    ax.set_title(
        'Funciones de Membresía - Tasa de Llegada',
        fontsize=14,
        fontweight='bold'
    )
    ax.set_xlabel('Tasa de Llegada (vehículos/minuto)')
    ax.set_ylabel('Grado de Membresía')
    ax.set_ylim(-0.05, 1.05)
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()

    ruta = os.path.join(
        CARPETA_RESULTADOS,
        'funciones_membresia_llegada.png'
    )

    fig.savefig(ruta, dpi=300, bbox_inches='tight')
    plt.close(fig)

    print(f"Gráfica guardada: {ruta}")


    # --------------------------------------------------------
    # Gráfica de Extensión del Verde
    # --------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 6))

    for nombre in E.terms:
        ax.plot(
            E.universe,
            E[nombre].mf,
            linewidth=2,
            label=nombre.replace('_', ' ').title()
        )

    ax.set_title(
        'Funciones de Membresía - Extensión del Verde',
        fontsize=14,
        fontweight='bold'
    )
    ax.set_xlabel('Extensión del Verde (segundos)')
    ax.set_ylabel('Grado de Membresía')
    ax.set_ylim(-0.05, 1.05)
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()

    ruta = os.path.join(
        CARPETA_RESULTADOS,
        'funciones_membresia_extension.png'
    )

    fig.savefig(ruta, dpi=300, bbox_inches='tight')
    plt.close(fig)

    print(f"Gráfica guardada: {ruta}")


# ============================================================
# 6. Prueba rápida al ejecutar este archivo directamente
# ============================================================
if __name__ == "__main__":

    casos_prueba = [
        (2, 1),    # cola corta, llegada baja
        (10, 6),   # cola media, llegada moderada
        (20, 11),  # cola larga, llegada alta
        (28, 14),  # cola muy larga, llegada muy alta
    ]

    print("\n" + "=" * 65)
    print("CONTROLADOR DE LÓGICA DIFUSA - FLC MAMDANI")
    print("=" * 65)

    print(
        f"{'Cola (veh)':>12}"
        f"{'Llegada (veh/min)':>20}"
        f"{'Extensión (s)':>15}"
    )

    print("-" * 50)

    for cola, llegada in casos_prueba:

        ext = calcular_extension(
            cola,
            llegada
        )

        print(
            f"{cola:>12}"
            f"{llegada:>20}"
            f"{ext:>15.2f}"
        )

    print("=" * 65)

    # Guardar las gráficas
    print("\nGuardando funciones de membresía...")
    guardar_funciones_membresia()

    print("\nProceso terminado.")
    print(f"Resultados disponibles en:")
    print(CARPETA_RESULTADOS)
