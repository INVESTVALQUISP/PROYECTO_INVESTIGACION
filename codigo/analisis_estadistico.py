"""
analisis_estadistico.py
================================================================================
Incertidumbre estadistica de la replica (protocolo oficial: 20 replicas x 7200 s, lectura CALIBRADA) con
NUMEROS ALEATORIOS COMUNES: en la replica k (semilla k = 0..19) el ciclo fijo y el difuso ven las mismas llegadas,
por lo que la comparacion es PAREADA.

Para cada combinacion de caudal:
  * media, desviacion estandar de la muestra (n-1) e IC 95 % (t de Student) de cada controlador;
  * si el valor impreso en el paper cae dentro del IC 95 % de la replica;
  * reduccion del retardo del difuso sobre el fijo: media de las diferencias pareadas con IC 95 % (t pareada) y
    prueba de rangos con signo de Wilcoxon, con correccion de Holm entre los 16 flujos.
Entre celdas: sesgo medio replica - paper (IC 95 %, prueba t de una muestra y prueba de signos exacta).

Salida: resultados/analisis_estadistico.json      Uso:  python codigo/analisis_estadistico.py
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import json
import math
import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np

import estadistica as es
import paper_data as pdta
import traffic_model as tm

REPS, DUR = 20, 7200


def _fixed(args):
    ns, ew = args
    return [tm.simulate_fixed_cycle(ns / 3600.0, ew / 3600.0, k, duration=DUR) for k in range(REPS)]


def _fuzzy(args):
    ns, ew = args
    return [tm.simulate_fuzzy(ns / 3600.0, ew / 3600.0, k, duration=DUR, **tm.CALIBRADA) for k in range(REPS)]


def binom_two_sided(k, n):
    """Prueba de signos exacta (p = 0.5), dos colas."""
    pk = [math.comb(n, i) / 2 ** n for i in range(n + 1)]
    return min(1.0, sum(q for q in pk if q <= pk[k] + 1e-15))


def main():
    combos = tm.COMBINATIONS
    with ProcessPoolExecutor() as ex:
        fx = list(ex.map(_fixed, combos))
        fz = list(ex.map(_fuzzy, combos))
    rows = []
    for (ns, ew), a, b in zip(combos, fx, fz):
        ma, sa, la, ha = es.ic95(a)
        mb, sb, lb, hb = es.ic95(b)
        pf, pz = pdta.TABLE_VIII[(ns, ew)]
        d = np.asarray(a) - np.asarray(b)                       # diferencias pareadas (misma semilla)
        md, sd_d, lo_d, hi_d = es.ic95(d)
        w = es.wilcoxon(a, b)
        rows.append(dict(
            ns=ns, ew=ew, fixed=dict(mean=ma, sd=sa, lo=la, hi=ha, paper=pf, paper_in_ci=bool(la <= pf <= ha)),
            fuzzy=dict(mean=mb, sd=sb, lo=lb, hi=hb, paper=pz, paper_in_ci=bool(lb <= pz <= hb)),
            reduction=dict(abs=md, lo=lo_d, hi=hi_d, pct=100 * md / ma, p=w["p"], metodo=w["metodo"],
                           mejora_en_todas_las_replicas=bool((d > 0).all())),
            values_fixed=a, values_fuzzy=b))
    adj = es.holm([r["reduction"]["p"] for r in rows])
    for r, h in zip(rows, adj):
        r["reduction"]["p_holm"] = h
    err_f = np.array([100 * (r["fixed"]["mean"] - r["fixed"]["paper"]) / r["fixed"]["paper"] for r in rows])
    err_z = np.array([100 * (r["fuzzy"]["mean"] - r["fuzzy"]["paper"]) / r["fuzzy"]["paper"] for r in rows])

    def bias(e):
        m, s, lo, hi = es.ic95(e)
        neg = int((e < 0).sum())
        t = m / (s / math.sqrt(len(e)))
        return dict(mean_pct=m, sd=s, lo=lo, hi=hi, n_negativos=neg, n=len(e),
                    p_signos=binom_two_sided(neg, len(e)), p_t=es.t_sf2(t, len(e) - 1))

    out = dict(reps=REPS, duration=DUR, semillas="k = 0..19 para ambos controladores (CRN)", rows=rows,
               sesgo_fijo=bias(err_f), sesgo_difuso=bias(err_z),
               n_paper_en_ci_fijo=sum(r["fixed"]["paper_in_ci"] for r in rows),
               n_paper_en_ci_difuso=sum(r["fuzzy"]["paper_in_ci"] for r in rows),
               n_mejora_signif=sum(r["reduction"]["p_holm"] < 0.05 and r["reduction"]["abs"] > 0 for r in rows),
               n_mejora_todas_replicas=sum(r["reduction"]["mejora_en_todas_las_replicas"] for r in rows),
               p_holm_max=max(r["reduction"]["p_holm"] for r in rows))
    os.makedirs("resultados", exist_ok=True)
    json.dump(out, open("resultados/analisis_estadistico.json", "w"), indent=1)
    print(f"{'N-S':>5} {'E-W':>5} | fijo [IC95] (paper) | difuso [IC95] (paper) | mejora % p_Holm")
    for r in rows:
        f, z, d = r["fixed"], r["fuzzy"], r["reduction"]
        print(f"{r['ns']:5d} {r['ew']:5d} | {f['mean']:6.2f} [{f['lo']:6.2f},{f['hi']:6.2f}] ({f['paper']:5.1f}){'*' if f['paper_in_ci'] else ' '}"
              f" | {z['mean']:6.2f} [{z['lo']:6.2f},{z['hi']:6.2f}] ({z['paper']:5.1f}){'*' if z['paper_in_ci'] else ' '}"
              f" | {d['pct']:5.1f} p_Holm={d['p_holm']:.1e}")
    print("\nPaper dentro del IC95 (*): fijo", out["n_paper_en_ci_fijo"], "/16 | difuso", out["n_paper_en_ci_difuso"], "/16")
    print("Mejora significativa (Wilcoxon pareado, Holm p<0.05):", out["n_mejora_signif"], "/16 ; p_Holm max =", f"{out['p_holm_max']:.2e}",
          "; el difuso es mejor en las 20 replicas en", out["n_mejora_todas_replicas"], "/16")
    print("Sesgo replica-paper fijo  :", {k: round(v, 3) if isinstance(v, float) else v for k, v in out["sesgo_fijo"].items()})
    print("Sesgo replica-paper difuso:", {k: round(v, 3) if isinstance(v, float) else v for k, v in out["sesgo_difuso"].items()})


if __name__ == "__main__":
    main()
