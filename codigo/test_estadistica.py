"""
test_estadistica.py: verifica estadistica.py con valores conocidos (sin scipy).
Uso:  python test_estadistica.py
"""
import sys

import estadistica as es

fails = 0


def check(name, ok, detail=""):
    global fails
    print(f"  [{'OK' if ok else 'FALLO'}] {name} {detail}")
    fails += 0 if ok else 1


close = lambda a, b, tol=1e-6: abs(a - b) < tol
check("t de Student: cuantil 0.975 con 19 g.l. = 2.093", close(es.t_ppf975(19), 2.093024, 1e-5))
check("chi2: P(chi2_1 > 3.841459) = 0.05", close(es.chi2_sf(3.841458820694124, 1), 0.05, 1e-9))
check("chi2: P(chi2_2 > 5.991465) = 0.05", close(es.chi2_sf(5.991464547107979, 2), 0.05, 1e-9))
check("chi2: P(chi2_2 > 10) = exp(-5)", close(es.chi2_sf(10, 2), 0.006737947, 1e-8))
check("chi2: P(chi2_5 > 11.0705) = 0.05", close(es.chi2_sf(11.070497693516351, 5), 0.05, 1e-7))
w = es.wilcoxon([1, 2, 3, 4, 5, 6], [0, 0, 0, 0, 0, 0])
check("Wilcoxon exacto, n = 6 todos positivos: p = 2/64", close(w["p"], 2 / 64) and w["metodo"] == "exacta", f"(p = {w['p']:.5f})")
d = [6, 8, 14, 16, 23, 24, 28, 29, 41, -48, 49, 56, 60, -67, 75]            # ejemplo clasico de Wilcoxon (1945)
w = es.wilcoxon(d, [0] * 15)
check("Wilcoxon, ejemplo clasico n = 15: W = 24 y p = 0.04126", close(min(w["W_plus"], w["W_minus"]), 24) and close(w["p"], 0.041259765625, 1e-9),
      f"(W = {min(w['W_plus'], w['W_minus']):.0f}, p = {w['p']:.5f})")
f = es.friedman([[1, 2, 3]] * 5)
check("Friedman: 5 bloques con el mismo orden de 3 tratamientos: chi2 = 10, p = exp(-5)", close(f["chi2"], 10) and close(f["p"], 0.006737947, 1e-8))
check("Holm: [0.01, 0.04, 0.03] -> [0.03, 0.06, 0.06]", all(close(a, b) for a, b in zip(es.holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])))
m, sd, lo, hi = es.ic95([1, 2, 3, 4, 5])
check("IC 95 %: media 3, sd muestral 1.5811, IC [1.037, 4.963]", close(m, 3) and close(sd, 1.5811388, 1e-6) and close(lo, 1.036757, 1e-4))
print(f"\n{'TODO OK' if fails == 0 else str(fails) + ' FALLOS'}")
sys.exit(1 if fails else 0)
