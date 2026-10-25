"""
analisis_estadistico.py
================================================================================
Incertidumbre estadistica de la replica (mismo protocolo oficial: 20 replicas x 7200 s,
semillas 0.. para el ciclo fijo y 100000.. para el difuso, lectura CALIBRADA).

Guarda los retardos de CADA replica y calcula:
  * media, desviacion y IC 95 % (t de Student) de cada celda;
  * si el valor impreso en el paper cae dentro del IC 95 % de la replica;
  * mejora del difuso sobre el fijo con IC 95 % (Welch) y p-valor;
  * sesgo medio replica - paper (IC 95 % entre celdas) y prueba de signos.

Uso:  python codigo/analisis_estadistico.py        (~3 min con 4 nucleos)
Salida: resultados/analisis_estadistico.json
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import json
import math
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

import paper_data as pdta
import traffic_model as tm

REPS, DUR = 20, 7200


# ---- distribucion t de Student sin scipy (beta incompleta regularizada, Lentz) ----
def _betacf(a, b, x):
    tiny, qab, qap, qam = 1e-300, a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d; d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c; c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d; d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c; c = c if abs(c) > tiny else tiny
        de = d * c
        h *= de
        if abs(de - 1.0) < 1e-14:
            break
    return h


def _betai(a, b, x):
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                  + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def t_sf2(t, df):
    """P(|T| > |t|) con df grados de libertad (dos colas)."""
    return _betai(df / 2.0, 0.5, df / (df + t * t))


def t_ppf975(df):
    """Cuantil 0.975 de la t de Student (biseccion sobre t_sf2 = 0.05)."""
    lo, hi = 0.0, 100.0
    for _ in range(80):
        mid = (lo + hi) / 2.0
        if t_sf2(mid, df) > 0.05:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def binom_two_sided(k, n):
    """Prueba de signos exacta (p = 0.5), dos colas."""
    pk = [math.comb(n, i) / 2 ** n for i in range(n + 1)]
    return min(1.0, sum(q for q in pk if q <= pk[k] + 1e-15))


def _fixed(args):
    ns, ew = args
    return [tm.simulate_fixed_cycle(ns / 3600.0, ew / 3600.0, k, duration=DUR) for k in range(REPS)]


def _fuzzy(args):
    ns, ew = args
    return [tm.simulate_fuzzy(ns / 3600.0, ew / 3600.0, 100000 + k, duration=DUR, **tm.CALIBRADA)
            for k in range(REPS)]


def ci(x):
    x = np.asarray(x, float)
    m, s = x.mean(), x.std(ddof=1)
    h = t_ppf975(len(x) - 1) * s / math.sqrt(len(x))
    return float(m), float(s), float(m - h), float(m + h)


def main():
    combos = tm.COMBINATIONS
    with ProcessPoolExecutor() as ex:
        fx = list(ex.map(_fixed, combos))
        fz = list(ex.map(_fuzzy, combos))
    rows = []
    for (ns, ew), a, b in zip(combos, fx, fz):
        ma, sa, la, ha = ci(a)
        mb, sb, lb, hb = ci(b)
        pf, pz = pdta.TABLE_VIII[(ns, ew)]
        diff = ma - mb
        se = math.sqrt(sa ** 2 / REPS + sb ** 2 / REPS)
        dfw = se ** 4 / ((sa ** 2 / REPS) ** 2 / (REPS - 1) + (sb ** 2 / REPS) ** 2 / (REPS - 1))
        h = t_ppf975(dfw) * se
        p = t_sf2(diff / se, dfw)
        rows.append(dict(
            ns=ns, ew=ew, fixed=dict(mean=ma, sd=sa, lo=la, hi=ha, paper=pf, paper_in_ci=bool(la <= pf <= ha)),
            fuzzy=dict(mean=mb, sd=sb, lo=lb, hi=hb, paper=pz, paper_in_ci=bool(lb <= pz <= hb)),
            reduction=dict(abs=diff, lo=diff - h, hi=diff + h, pct=100 * diff / ma, p=float(p)),
            values_fixed=a, values_fuzzy=b))
    err_f = np.array([100 * (r["fixed"]["mean"] - r["fixed"]["paper"]) / r["fixed"]["paper"] for r in rows])
    err_z = np.array([100 * (r["fuzzy"]["mean"] - r["fuzzy"]["paper"]) / r["fuzzy"]["paper"] for r in rows])

    def bias(e):
        m, s, lo, hi = ci(e)
        neg = int((e < 0).sum())
        return dict(mean_pct=m, sd=s, lo=lo, hi=hi, n_negativos=neg, n=len(e),
                    p_signos=binom_two_sided(neg, len(e)),
                    p_t=t_sf2(float(e.mean() / (e.std(ddof=1) / math.sqrt(len(e)))), len(e) - 1))

    out = dict(reps=REPS, duration=DUR, rows=rows, sesgo_fijo=bias(err_f), sesgo_difuso=bias(err_z),
               n_paper_en_ci_fijo=sum(r["fixed"]["paper_in_ci"] for r in rows),
               n_paper_en_ci_difuso=sum(r["fuzzy"]["paper_in_ci"] for r in rows),
               n_mejora_signif=sum(r["reduction"]["p"] < 0.05 and r["reduction"]["abs"] > 0 for r in rows))
    os.makedirs("resultados", exist_ok=True)
    json.dump(out, open("resultados/analisis_estadistico.json", "w"), indent=1)
    print(f"{'N-S':>5} {'E-W':>5} | fijo [IC95] (paper) | difuso [IC95] (paper) | mejora % p")
    for r in rows:
        f, z, d = r["fixed"], r["fuzzy"], r["reduction"]
        print(f"{r['ns']:5d} {r['ew']:5d} | {f['mean']:6.2f} [{f['lo']:6.2f},{f['hi']:6.2f}] ({f['paper']:5.1f}){'*' if f['paper_in_ci'] else ' '}"
              f" | {z['mean']:6.2f} [{z['lo']:6.2f},{z['hi']:6.2f}] ({z['paper']:5.1f}){'*' if z['paper_in_ci'] else ' '}"
              f" | {d['pct']:5.1f} p={d['p']:.1e}")
    print("\nPaper dentro del IC95 (*): fijo", out["n_paper_en_ci_fijo"], "/16 | difuso", out["n_paper_en_ci_difuso"], "/16")
    print("Mejora significativa (p<0.05):", out["n_mejora_signif"], "/16")
    print("Sesgo replica-paper fijo  :", {k: round(v, 3) if isinstance(v, float) else v for k, v in out["sesgo_fijo"].items()})
    print("Sesgo replica-paper difuso:", {k: round(v, 3) if isinstance(v, float) else v for k, v in out["sesgo_difuso"].items()})


if __name__ == "__main__":
    main()
