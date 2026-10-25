"""
verificar_formulas.py
================================================================================
Verificacion numerica de las deducciones del articulo (Seccion "Desarrollo matematico de las
formulas"). Cada comprobacion compara el resultado de la formula con un calculo independiente:

  1. Cola y retardo (ec. colaR-retardoG): suma de colas por segundo  ==  suma de esperas individuales
     de cada vehiculo (simulacion FIFO con vehiculos explicitos).
  2. Primer termino de Webster: formula  ==  area de la cola de un modelo fluido (dt = 1 ms).
  3. Segundo termino de Webster: formula  ==  cola M/D/1 simulada (recursion de Lindley).
  4. Ciclo y verdes: g_i = (y_i/Y)(C0 - L) iguala los grados de saturacion y C0 queda cerca del
     minimo numerico del retardo de Webster.
  5. Operadores mt / lt: max = 1 - mu, min = 0 (salvo en el modo x0) y comparacion con las Tablas V y VI.
  6. Entrada exacta: la regla composicional con un conjunto unitario devuelve la fila de la relacion.
  7. Conteos: 5 x 6 x 6 = 180, 25 reglas y verde maximo de 57 s.

Salida: resultados/verificacion_formulas.json     Uso:  python codigo/verificar_formulas.py
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import json
import math

import numpy as np

import fuzzy_logic as fl

rng = np.random.default_rng(2026)
out = {}


# ------------------------------------------------------------------ 1. cola y retardo
def check_colas(n_cases=1000):
    worst = 0
    for _ in range(n_cases):
        R, G = int(rng.integers(5, 30)), int(rng.integers(5, 40))
        p = float(rng.uniform(0.05, 0.9))
        QG = int(rng.integers(0, 6))
        q = (rng.random(R + G) < p).astype(int)
        # formulas del articulo
        QR = QG + q[:R].sum()
        DR = sum(QG + q[:n].sum() for n in range(1, R + 1))
        DG = sum(max(QR + q[R:R + n].sum() - n, 0) for n in range(1, G + 1))
        D_formula = DR + DG
        # simulacion FIFO con vehiculos explicitos (s = 1 veh/s)
        fila = [1] * QG                      # los QG vehiculos iniciales ya estan en cola al terminar el segundo 1
        esperas = 0
        for n in range(1, R + G + 1):
            fila += [n] * int(q[n - 1])      # llegadas del segundo n
            if n > R and fila:               # en verde sale un vehiculo por segundo
                esperas += n - fila.pop(0)
        esperas += sum((R + G) - t + 1 for t in fila)    # los que siguen en cola al final (segundos t..R+G)
        worst = max(worst, abs(D_formula - esperas))
    return dict(casos=n_cases, max_dif=float(worst))


# ------------------------------------------------------------------ 2. termino uniforme
def check_uniforme():
    casos, worst = [], 0.0
    for C, lam, q in ((60, 0.5, 0.2), (90, 0.4, 0.25), (45, 0.6, 0.4), (120, 0.3, 0.15), (30, 0.5, 0.1)):
        s, dt = 1.0, 1e-3
        r = C * (1 - lam)
        Q, area, t = 0.0, 0.0, 0.0
        while t < C:
            Q = Q + q * dt if t < r else max(Q + (q - s) * dt, 0.0)
            area += Q * dt
            t += dt
        d_sim = area / (q * C)
        X = q / (lam * s)
        d_for = C * (1 - lam) ** 2 / (2 * (1 - lam * X))
        err = abs(d_sim - d_for) / d_for
        worst = max(worst, err)
        casos.append(dict(C=C, lam=lam, q=q, formula=d_for, simulado=d_sim))
    return dict(casos=len(casos), max_err_rel=float(worst), detalle=casos)


# ------------------------------------------------------------------ 3. M/D/1
def check_md1(n=1_500_000):
    res, worst = [], 0.0
    for X in (0.3, 0.6, 0.8):
        c = 0.5                      # capacidad (veh/s)
        q = X * c
        A = rng.exponential(1 / q, n)
        W, acc = 0.0, 0.0
        S = 1 / c
        for a in A:                  # recursion de Lindley
            acc += W
            W = max(W + S - a, 0.0)
        w_sim = acc / n
        w_for = X ** 2 / (2 * q * (1 - X))
        err = abs(w_sim - w_for) / w_for
        worst = max(worst, err)
        res.append(dict(X=X, formula=w_for, simulado=w_sim))
    return dict(casos=len(res), max_err_rel=float(worst), detalle=res)


# ------------------------------------------------------------------ 4. ciclo y verdes
def webster_d(C, g, q, s=1.0):
    lam = g / C
    X = q / (lam * s)
    return (C * (1 - lam) ** 2 / (2 * (1 - lam * X)) + X ** 2 / (2 * q * (1 - X))
            - 0.65 * (C / q ** 2) ** (1 / 3) * X ** (2 + 5 * lam))


def check_ciclo():
    L, s = 10.0, 1.0
    filas, max_dX, max_gap = [], 0.0, 0.0
    for ns, ew in ((360, 360), (720, 1080), (1080, 1440), (1440, 1440)):
        q1, q2 = ns / 3600, ew / 3600
        y1, y2 = q1 / s, q2 / s
        Y = y1 + y2
        C0 = (1.5 * L + 5) / (1 - Y)
        g1, g2 = y1 / Y * (C0 - L), y2 / Y * (C0 - L)
        X1, X2 = q1 / (g1 / C0 * s), q2 / (g2 / C0 * s)
        max_dX = max(max_dX, abs(X1 - X2))

        def total(C):
            g1c, g2c = y1 / Y * (C - L), y2 / Y * (C - L)
            return (q1 * webster_d(C, g1c, q1) + q2 * webster_d(C, g2c, q2)) / (q1 + q2)
        Cs = np.arange(L / (1 - Y) + 0.5, 400, 0.25)
        vals = [total(C) for C in Cs]
        Cn = float(Cs[int(np.argmin(vals))])
        gap = (total(C0) - min(vals)) / min(vals)
        max_gap = max(max_gap, gap)
        filas.append(dict(ns=ns, ew=ew, C0=C0, C_numerico=Cn, X=X1, Cmin=L / (1 - Y),
                          retardo_C0=total(C0), retardo_min=float(min(vals))))
    return dict(casos=len(filas), max_dif_X=float(max_dX), max_exceso_retardo=float(max_gap), detalle=filas)


# ------------------------------------------------------------------ 5. mt / lt
def check_mtlt():
    pts, bad_prop, dif_mt, dif_lt = 0, 0, 0, 0
    for name, f in fl.MU_ARR.items():
        f = np.array(f, float)
        x0 = int(np.argmax(f)) + 1
        for x in range(1, 11):
            mu = f[x - 1]
            lt = (1 - mu) if x < x0 else 0.0
            mt = (1 - mu) if x > x0 else 0.0
            pts += 1
            if x != x0 and (abs(max(lt, mt) - (1 - mu)) > 1e-12):
                bad_prop += 1
            if min(lt, mt) != 0:
                bad_prop += 1
            if abs(fl.mt_arr(name, x) - mt) > 1e-12:
                dif_mt += 1                  # solo debe ocurrir en x0 (valor impreso 1 - mu(x0))
    for name, f in fl.MU_QUEUE.items():
        f = np.array(f, float)
        x0 = int(np.argmax(f)) + 4
        for x in range(4, 33):
            mu = f[x - 4]
            lt = (1 - mu) if x < x0 else 0.0
            mt = (1 - mu) if x > x0 else 0.0
            pts += 1
            if x != x0 and (abs(max(lt, mt) - (1 - mu)) > 1e-12):
                bad_prop += 1
            if min(lt, mt) != 0:
                bad_prop += 1
            if abs(fl.lt_queue(name, x) - lt) > 1e-12:
                dif_lt += 1
    return dict(puntos=pts, fallos_propiedad=bad_prop, dif_mt_codigo_vs_definicion=dif_mt,
                dif_lt_codigo_vs_definicion=dif_lt, conjuntos_llegadas=len(fl.MU_ARR), conjuntos_colas=len(fl.MU_QUEUE))


# ------------------------------------------------------------------ 6. entrada exacta
def check_singleton(n=200):
    worst = 0.0
    for _ in range(n):
        R = rng.random((10, 10))
        x0 = int(rng.integers(0, 10))
        A = np.zeros(10)
        A[x0] = 1.0
        comp = np.max(np.minimum(R, A[:, None]), axis=0)     # max_x min{R(x,y), A(x)}
        worst = max(worst, float(np.max(np.abs(comp - R[x0]))))
    return dict(casos=n, max_dif=worst)


# ------------------------------------------------------------------ 7. conteos
def check_conteos():
    n_rules = sum(len(v) for v in fl.RULES.values())
    verde = 7 + 5 * 10
    return dict(T=len(fl.MU_TIME), A=len(fl.MU_ARR), Q=len(fl.MU_QUEUE),
                producto=len(fl.MU_TIME) * len(fl.MU_ARR) * len(fl.MU_QUEUE), reglas=n_rules,
                verde_max=verde, verde_max_alt=max(fl.INTERVENTIONS) + 10)


if __name__ == "__main__":
    out["colas"] = check_colas()
    out["uniforme"] = check_uniforme()
    out["md1"] = check_md1()
    out["ciclo"] = check_ciclo()
    out["mtlt"] = check_mtlt()
    out["singleton"] = check_singleton()
    out["conteos"] = check_conteos()
    json.dump(out, open("resultados/verificacion_formulas.json", "w"), indent=1)
    for k, v in out.items():
        print(k, {a: b for a, b in v.items() if a != "detalle"})
