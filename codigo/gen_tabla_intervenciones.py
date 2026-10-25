"""
gen_tabla_intervenciones.py
================================================================================
Decisiones por intervencion de una simulacion (720/2160 veh/h, 1800 s, semilla 1), a partir de
muestras/disparos_reglas.csv (generado por informe_disparos.py). Salida: articulo_ieee/tabla_intervenciones.tex
Uso:  python codigo/gen_tabla_intervenciones.py
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import collections
import csv

rows = list(csv.DictReader(open("muestras/disparos_reglas.csv", encoding="utf-8-sig")))
dec = {}
for r in rows:
    dec.setdefault((r["t"], r["brazo_verde"]), []).append(r)
by = collections.defaultdict(lambda: dict(n=0, cut=0, e10=0, r5=0))
for rs in dec.values():
    i = int(rs[0]["intervencion"])
    e = int(float(rs[0]["e_star"]))
    d = by[i]
    d["n"] += 1
    d["cut"] += e == 0
    d["e10"] += e == 10
    d["r5"] += any(r["regla"].endswith("R5") and r["dispara"] == "1" for r in rs)
lines = [f"{i}  & {d['n']} & {d['cut']} & {d['e10']} & {d['r5']} \\\\" for i, d in sorted(by.items())]
tot = {k: sum(d[k] for d in by.values()) for k in ("n", "cut", "e10", "r5")}
tex = (r"""\begin{table}[!t]
\caption{Decisiones por intervención en la simulación de la Fig.~\ref{fig:disparos} (cortes: $e^*{=}0$)}
\label{tab:intervenciones}
\centering
\footnotesize
\begin{tabular}{rrrrr}
\hline
Interv. (s) & Decis. & Cortes & $e^*{=}10$ & R5 dispara \\
\hline
""" + "\n".join(lines) + f"""
\\hline
Total & {tot['n']} & {tot['cut']} & {tot['e10']} & {tot['r5']} \\\\
\\hline
\\end{{tabular}}
\\fuente{{conteo propio sobre \\texttt{{muestras/disparos\\_reglas.csv}} (\\texttt{{informe\\_disparos.py}}: 720/2160\\,veh/h, 1800\\,s, semilla 1, lectura calibrada). Una decisión es una intervención del controlador; $e^*$ se obtiene con \\eqref{{eq:decision}}.}}
\\end{{table}}
""")
open("articulo_ieee/tabla_intervenciones.tex", "w", encoding="utf-8").write(tex)
print(tot)
