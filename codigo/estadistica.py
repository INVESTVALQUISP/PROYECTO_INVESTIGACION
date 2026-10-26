"""
estadistica.py
================================================================================
Estadistica sin scipy (solo math y numpy) para los experimentos del proyecto:

  * ic95(x)                   : media, desviacion estandar de la muestra (n-1), IC 95 % (t de Student)
  * wilcoxon(x, y)            : prueba de rangos con signo para datos pareados (exacta si no hay empates y n <= 25;
                                aproximacion normal con correccion por empates y de continuidad en los demas casos)
  * friedman(M)               : prueba de Friedman (bloques en filas, tratamientos en columnas), con correccion por empates
  * holm(p)                   : correccion de Holm-Bonferroni de una lista de p-valores
  * t_sf2, t_ppf975, chi2_sf  : funciones de distribucion auxiliares

Verificado en test_estadistica.py con valores conocidos.
"""
import math

import numpy as np


# ---------------------------------------------------------------- distribuciones
def _betacf(a, b, x):
    tiny, qab, qap, qam = 1e-300, a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
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
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def t_sf2(t, df):
    """P(|T| > |t|) con df grados de libertad (dos colas)."""
    return _betai(df / 2.0, 0.5, df / (df + t * t))


def t_ppf975(df):
    """Cuantil 0.975 de la t de Student (biseccion)."""
    lo, hi = 0.0, 100.0
    for _ in range(80):
        mid = (lo + hi) / 2.0
        if t_sf2(mid, df) > 0.05:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def chi2_sf(x, df):
    """P(chi2_df > x) = Q(df/2, x/2), gamma incompleta regularizada superior."""
    if x <= 0:
        return 1.0
    a, xx = df / 2.0, x / 2.0
    if xx < a + 1.0:                       # serie
        ap, s, term = a, 1.0 / a, 1.0 / a
        for _ in range(500):
            ap += 1.0
            term *= xx / ap
            s += term
            if abs(term) < abs(s) * 1e-15:
                break
        return max(0.0, 1.0 - s * math.exp(-xx + a * math.log(xx) - math.lgamma(a)))
    b = xx + 1.0 - a                       # fraccion continua (Lentz)
    c, d = 1.0 / 1e-300, 1.0 / b
    h = d
    for i in range(1, 500):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        d = d if abs(d) > 1e-300 else 1e-300
        c = b + an / c
        c = c if abs(c) > 1e-300 else 1e-300
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < 1e-15:
            break
    return h * math.exp(-xx + a * math.log(xx) - math.lgamma(a))


# ---------------------------------------------------------------- resumen
def ic95(x):
    """(media, desviacion estandar de la muestra, limite inferior, limite superior del IC 95 %)."""
    x = np.asarray(x, float)
    m = float(x.mean())
    sd = float(x.std(ddof=1)) if len(x) > 1 else 0.0
    h = t_ppf975(len(x) - 1) * sd / math.sqrt(len(x)) if len(x) > 1 else 0.0
    return m, sd, m - h, m + h


# ---------------------------------------------------------------- pruebas no parametricas
def _rank_avg(a):
    """Rangos 1..n con empates promediados."""
    a = np.asarray(a, float)
    order = np.argsort(a, kind="mergesort")
    ranks = np.empty(len(a))
    i = 0
    while i < len(a):
        j = i
        while j + 1 < len(a) and a[order[j + 1]] == a[order[i]]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return ranks


def wilcoxon(x, y):
    """Prueba de rangos con signo (dos colas) para muestras pareadas x, y.

    Devuelve dict(n, W_plus, W_minus, p, metodo). Los pares con diferencia 0 se descartan."""
    d = np.asarray(x, float) - np.asarray(y, float)
    d = d[d != 0]
    n = len(d)
    if n == 0:
        return dict(n=0, W_plus=0.0, W_minus=0.0, p=1.0, metodo="sin diferencias")
    r = _rank_avg(np.abs(d))
    wp = float(r[d > 0].sum())
    wm = float(r[d < 0].sum())
    w = min(wp, wm)
    ties = len(np.unique(np.abs(d))) < n
    if not ties and n <= 25:               # distribucion exacta por conteo de subconjuntos
        total = n * (n + 1) // 2
        cnt = np.zeros(total + 1)
        cnt[0] = 1
        for k in range(1, n + 1):
            cnt[k:] = cnt[k:] + cnt[:total + 1 - k].copy()
        p = min(1.0, 2.0 * cnt[:int(round(w)) + 1].sum() / 2.0 ** n)
        return dict(n=n, W_plus=wp, W_minus=wm, p=float(p), metodo="exacta")
    mu = n * (n + 1) / 4.0
    _, counts = np.unique(np.abs(d), return_counts=True)
    var = n * (n + 1) * (2 * n + 1) / 24.0 - (counts ** 3 - counts).sum() / 48.0
    z = (abs(w - mu) - 0.5) / math.sqrt(var) if var > 0 else 0.0
    p = math.erfc(max(z, 0.0) / math.sqrt(2.0))
    return dict(n=n, W_plus=wp, W_minus=wm, p=float(min(1.0, p)), metodo="normal")


def friedman(M):
    """Prueba de Friedman. M: matriz (bloques x tratamientos). Devuelve dict(chi2, df, p, rangos_medios)."""
    M = np.asarray(M, float)
    n, k = M.shape
    R = np.vstack([_rank_avg(row) for row in M])
    Rj = R.sum(axis=0)
    # correccion por empates
    t_corr = 0.0
    for row in M:
        _, c = np.unique(row, return_counts=True)
        t_corr += (c ** 3 - c).sum()
    q = 12.0 * (Rj ** 2).sum() / (n * k * (k + 1)) - 3.0 * n * (k + 1)
    q /= 1.0 - t_corr / (n * k * (k ** 2 - 1))
    return dict(chi2=float(q), df=k - 1, p=float(chi2_sf(q, k - 1)), rangos_medios=(Rj / n).tolist())


def holm(p):
    """p-valores ajustados por Holm-Bonferroni (mismo orden que la entrada)."""
    p = np.asarray(p, float)
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    run = 0.0
    for rank, idx in enumerate(order):
        run = max(run, (m - rank) * p[idx])
        adj[idx] = min(1.0, run)
    return adj.tolist()
