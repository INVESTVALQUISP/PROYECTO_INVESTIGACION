"""
test_paper_tables.py
================================================================================
Verifica el codigo contra lo IMPRESO en el paper (paper_data.py, transcrito de la
imagen del original):
  * Tablas V y VI (operadores mt y lt aplicados a las Tablas III y IV)
  * Las 25 reglas del Apendice (5 intervenciones x 5 reglas)
  * El ejemplo de las pags. 7-8: Tabla VII (cada regla y la fila agregada)
  * Estructura temporal: verde efectivo maximo 57 s
Uso:  python test_paper_tables.py
"""
import sys

import numpy as np

import fuzzy_logic as fl
import paper_data as pdta
import traffic_model as tm

fails = 0


def check(name, ok, detail=""):
    global fails
    print(f"  [{'OK' if ok else 'FALLO'}] {name} {detail}")
    fails += 0 if ok else 1


print("Tablas II, III y IV (conjuntos base)")
for name, mine, ref in (("II", fl.MU_TIME, pdta.TABLE_II), ("III", fl.MU_ARR, pdta.TABLE_III),
                        ("IV", fl.MU_QUEUE, pdta.TABLE_IV)):
    check(f"Tabla {name}", all(np.allclose(mine[k], ref[k]) for k in ref) and set(mine) == set(ref))

print("Tabla V  mt(A) sobre la Tabla III")
for label, row in pdta.TABLE_V.items():
    got = [fl.mt_arr(label, a) for a in range(1, 11)]
    check(f"mt({label})", np.allclose(got, row, atol=1e-9))

print("Tabla VI lt(A) sobre la Tabla IV (q = 4..32)")
for label, row in pdta.TABLE_VI.items():
    got = [fl.lt_queue(label, q) for q in range(4, 33)]
    check(f"lt({label})", np.allclose(got, row, atol=1e-9))

print("Apendice: 25 reglas = 5 intervenciones x 5 reglas")
check("5 intervenciones", sorted(fl.RULES) == [7, 17, 27, 37, 47])
check("5 reglas por intervencion", all(len(v) == 5 for v in fl.RULES.values()))
# Cada intervencion: T = veryshort, short, medium, long, verylong con E = T
check("T = E en todas las reglas", all(r[0] == r[3] for v in fl.RULES.values() for r in v))
check("1.a regla siempre veryshort/none/any",
      all(v[0] == ("veryshort", "none", "any", "veryshort") for v in fl.RULES.values()))
EXPECTED_Q = {   # etiquetas de Q de las reglas 2..5 de cada intervencion (Apendice, pags. 715-716)
    7:  ["verysmall", "verysmall", "verysmall", "verysmall"],
    17: ["verysmall", "verysmall", "verysmall", "small"],
    27: ["verysmall", "verysmall", "verysmall", "small"],
    37: ["smallplus", "smallplus", "medium", "long"],
    47: ["long", "long", "verylong", "verylong"],
}
EXPECTED_A = {
    7:  ["afew", "few", "medium", "many"],
    17: ["afew", "few", "medium", "many"],
    27: ["afew", "few", "medium", "many"],
    37: ["afew", "medium", "many", "toomany"],
    47: ["afew", "medium", "toomany", "toomany"],
}
for k in (7, 17, 27, 37, 47):
    check(f"intervencion {k}: A", [r[1] for r in fl.RULES[k][1:]] == EXPECTED_A[k])
    check(f"intervencion {k}: Q", [r[2] for r in fl.RULES[k][1:]] == EXPECTED_Q[k])

print("Ejemplo de las pags. 7-8 (2.a intervencion, Tabla VII)")
x, xp, Q = pdta.EXAMPLE_X, pdta.EXAMPLE_XP, pdta.EXAMPLE_Q
beta, betap = np.cumsum(x), Q + np.cumsum(xp)
check("beta  = (0 1 1 2 3 4 5 5 5 6)", list(beta) == pdta.EXAMPLE_BETA)
check("beta' = (5 6 6 6 7 7 7 8 8 8)", list(betap) == pdta.EXAMPLE_BETA_P)
per_rule = fl.fuzzy_decision_per_rule(x, xp, Q, fl.RULES[17], a_mode="arrivals", q_mode="predicted")
for i, key in enumerate(("R1", "R2", "R3", "R4", "R5")):
    check(f"Tabla VII fila {key}", np.allclose(per_rule[i, 1:], pdta.EXAMPLE_ROW_VII[key]))
grade = fl.fuzzy_decision(x, xp, Q, fl.RULES[17], a_mode="arrivals", q_mode="predicted")
check("Tabla VII fila 'Fuzzy Algorithm'", np.allclose(grade[1:], pdta.EXAMPLE_ROW_VII["algoritmo"]))
check("extension elegida = 10 s", fl.decide_extension(grade) == 10)
check("regla de empate: maxima extension", fl.decide_extension(np.array([0, .5, 0, 0, 0, 0, 0, 0, 0, .5, 0])) == 9)
check("si todo < 0.5 no hay extension", fl.decide_extension(np.array([0, .4, .3, 0, 0, 0, 0, 0, 0, 0, 0])) == 0)

print("Estructura temporal")
arr = np.ones((2, 400), dtype=int)       # saturado: siempre extiende al maximo
s = tm.Sim(arr[0], arr[1])
t_end = s.run_green_fuzzy(0, 0, 400, mode="literal", predicted_q=False, queue_source="total",
                          ruleset={k: [("verylong", "toomany", "any", "verylong")] * 1 for k in fl.INTERVENTIONS})
check("verde efectivo maximo = 57 s (47 + 10)", t_end == 57, f"(obtenido {t_end} s)")
s = tm.Sim(arr[0], arr[1])
t_end = s.run_green_fuzzy(0, 0, 400, ruleset={k: [("veryshort", "none", "any", "veryshort")] for k in fl.INTERVENTIONS},
                          threshold=2.0)    # nunca extiende: primera intervencion corta
check("verde efectivo minimo = 7 s (corte en la 1.a intervencion)", t_end == 7, f"(obtenido {t_end} s)")

print(f"\n{'TODO OK' if fails == 0 else str(fails) + ' FALLOS'}")
sys.exit(1 if fails else 0)
