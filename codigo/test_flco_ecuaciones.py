"""
test_flco_ecuaciones.py
================================================================================
Comprueba que FLC-O se puede reconstruir SOLO con lo que dice el suplemento (articulo/suplemento.tex, Seccion «FLC-O
completo»): las ecuaciones y los 42 parametros impresos con 6 decimales (articulo/tabla_s_parametros.tex).
  1. los valores de la tabla del suplemento coinciden con el vector theta del modelo elegido (resultados/opt/);
  2. una implementacion INDEPENDIENTE, escrita solo con las ecuaciones del suplemento (sin opt_flc2.py), da la misma
     salida u que FuzzyOpt en 500 puntos (G, R, V) al azar, incluidos puntos por debajo de k1 y por encima de k3;
  3. las pertenencias suman 1 en todo punto (particion de Ruspini);
  4. las entradas G y R del suplemento coinciden con FuzzyOpt.entradas dentro del simulador vectorizado;
  5. el ejemplo numerico del suplemento (tabla_s_ejemplo.tex) coincide con la implementacion independiente.
Uso:  python test_flco_ecuaciones.py
"""
import json
import re
import sys

import numpy as np

import opt_flc2
from sim_batch import BatchSim, make_arrivals

fails = 0


def check(name, ok, detail=""):
    global fails
    print(f"  [{'OK' if ok else 'FALLO'}] {name} {detail}")
    fails += 0 if ok else 1


def num(txt):
    return float(txt.replace("$-$", "-").replace("$", "").strip())


# ---------------------------------------------------------------- lectura de la tabla del suplemento
fin = json.load(open("resultados/opt/modelos_finales.json"))
nombre = fin["flc"]
modelo = json.load(open(f"resultados/opt/{nombre}.json"))
tex = open("articulo/tabla_s_parametros.tex", encoding="utf-8").read()
filas = [l for l in tex.splitlines() if l.endswith("\\\\") and "&" in l and "Par" not in l]
th_tabla = np.zeros(42)
for r, l in enumerate(filas):
    c = [x.strip().rstrip("\\").strip() for x in l.split("&")]
    for k in range(3):
        th_tabla[k * 14 + r] = num(c[2 * k + 1])

print("Parametros del suplemento")
check("la tabla tiene los 42 parametros", len(filas) == 14 and np.all(np.isfinite(th_tabla)), f"({len(filas)} filas)")
th = np.array(modelo["theta"], dtype=float)
check("los valores de la tabla (6 decimales) son los del modelo elegido", np.abs(th_tabla - th).max() < 5.1e-7,
      f"(diferencia maxima {np.abs(th_tabla - th).max():.1e})")


# ---------------------------------------------------------------- implementacion independiente (solo las ecuaciones del suplemento)
def sat(z):
    return min(1.0, max(0.0, z))


def mu(x, k):
    k1, k2, k3 = k
    bajo = sat((k2 - x) / (k2 - k1))
    alto = sat((x - k2) / (k3 - k2))
    return (bajo, 1.0 - bajo - alto, alto)


def nudos(p):
    k1 = abs(p[0])
    k2 = k1 + abs(p[1]) + 0.05
    return (k1, k2, k2 + abs(p[2]) + 0.05)


def salida_u(G, R, V, t):
    kG, kR, kV = nudos(t[0:3]), nudos(t[3:6]), nudos(t[6:9])
    c = t[9:36]
    mg, mr, mv = mu(G, kG), mu(R, kR), mu(V, kV)
    num_, den = 0.0, 0.0
    for i in range(3):
        for j in range(3):
            for k in range(3):
                w = mg[i] * mr[j] * mv[k]
                num_ += w * c[i * 9 + j * 3 + k]
                den += w
    return num_ / (den + 1e-9)


print("Ecuaciones del suplemento frente a opt_flc2.FuzzyOpt")
ctrl = opt_flc2.FuzzyOpt(th_tabla, True, modelo["gmin"])
rng = np.random.default_rng(0)
G = np.concatenate([rng.uniform(0, 12, 450), [0, 0.0004, 1.1, 4.7, 4.8, 50]])
R = np.concatenate([rng.uniform(0, 40, 450), [0, 0.2, 8.0, 20.7, 21, 100]])
V = np.concatenate([rng.uniform(0, 95, 450), [0, 6.5, 23.5, 54.5, 54.6, 90]])
u_ind = np.array([salida_u(g, r, v, th_tabla) for g, r, v in zip(G, R, V)])
u_cod = ctrl.score(G, R, V)
check("u coincide en 500 puntos (incluidos los extremos fuera de [k1, k3])", np.abs(u_ind - u_cod).max() < 1e-9,
      f"(diferencia maxima {np.abs(u_ind - u_cod).max():.1e})")
check("el codigo con la tabla de 6 decimales da casi lo mismo que con theta exacto",
      np.abs(opt_flc2.FuzzyOpt(th, True, modelo["gmin"]).score(G, R, V) - u_cod).max() < 1e-4)
k_ = nudos(th_tabla[0:3])
check("las tres pertenencias suman 1 en todo punto", all(abs(sum(mu(x, k_)) - 1.0) < 1e-12 for x in np.linspace(-1, 60, 200)))
check("por debajo de k1 valen (1, 0, 0) y por encima de k3, (0, 0, 1)", mu(0.0, k_) == (1.0, 0.0, 0.0) and mu(k_[2] + 5, k_) == (0.0, 0.0, 1.0))

print("Entradas G y R del suplemento frente a FuzzyOpt.entradas")
arr = make_arrivals([720 / 3600.0], [2160 / 3600.0], [3], 400)
muestras = []


class Sonda:
    """Controlador que nunca cambia la fase y, en t = 50, 120 y 300, compara G y R del suplemento con FuzzyOpt.entradas."""

    def stop(self, sim, t, green):
        if t in (50, 120, 300):
            a = sim.arr
            ns = sim.phase[0] == 0
            qg, qr = (sim.q_ns[0], sim.q_ew[0]) if ns else (sim.q_ew[0], sim.q_ns[0])
            arg, arr_r = (a.arr_ns[0], a.arr_ew[0]) if ns else (a.arr_ew[0], a.arr_ns[0])
            Gs = qg + sum(w * arg[t:t + l].sum() for w, l in zip(ctrl.alfa, (2, 5, 10)))
            Rs = qr + sum(w * arr_r[t:t + l].sum() for w, l in zip(ctrl.beta, (3, 6, 10)))
            Gc, Rc, Vc = ctrl.entradas(sim, t)
            muestras.append((abs(Gs - Gc[0]), abs(Rs - Rc[0]), abs((t - sim.tstart[0]) - Vc[0])))
        return np.zeros(1, dtype=bool)


BatchSim(arr, max_green=None).run(Sonda())
check("G, R y V del suplemento = FuzzyOpt.entradas en 3 instantes", len(muestras) == 3 and np.abs(np.array(muestras)).max() < 1e-9)

print("Ejemplo numerico del suplemento")
ej = open("articulo/tabla_s_ejemplo.tex", encoding="utf-8").read()
m = re.search(r"u=([+-]?\d+\.\d+)\$", ej)
u_ej = salida_u(2.0, 5.0, 10.0, th_tabla)
check("la u del ejemplo impreso coincide con la implementacion independiente", m is not None and abs(float(m.group(1)) - u_ej) < 6e-5,
      f"(impreso {m.group(1) if m else '?'}, calculado {u_ej:+.4f})")

print("TODO OK" if fails == 0 else f"{fails} FALLOS")
sys.exit(1 if fails else 0)
