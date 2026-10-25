"""
gen_tablas_latex.py
================================================================================
Genera articulo_ieee/tabla_*.tex (un archivo por tabla) con las tablas de resultados del articulo a partir
de los JSON del proyecto (resultados/resultados_oficiales.json, resultados/fidelity_audit.json,
resultados/llegadas_fijas_vs_aleatorias.json, resultados/ablacion_reglas.json, resultados/analisis_estadistico.json) y de fuzzy_logic.py (reglas),
para que los numeros del texto y de las tablas no se desincronicen.
Uso:  python gen_tablas_latex.py
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import json

import numpy as np

import fuzzy_logic as fl
import paper_data as pdta

res = json.load(open("resultados/resultados_oficiales.json"))
aud = json.load(open("resultados/fidelity_audit.json"))
arr = json.load(open("resultados/llegadas_fijas_vs_aleatorias.json"))
abl = json.load(open("resultados/ablacion_reglas.json"))
est = json.load(open("resultados/analisis_estadistico.json"))
ver = json.load(open("resultados/verificacion_formulas.json"))
out = []


def f(x, nd=2):
    return f"{x:.{nd}f}"


# ---------------- Tabla VII: ejemplo ----------------
per = fl.fuzzy_decision_per_rule(pdta.EXAMPLE_X, pdta.EXAMPLE_XP, pdta.EXAMPLE_Q, fl.RULES[17], a_mode="arrivals", q_mode="predicted")[:, 1:]
agg = per.max(axis=0)
fmt = lambda v: "0" if abs(v) < 1e-12 else f"{v:g}"
rows = []
for i, nm in enumerate(["R1 very short", "R2 short", "R3 medium", "R4 long", "R5 very long"]):
    rows.append(f"{nm} & " + " & ".join(fmt(v) for v in per[i]) + r" \\")
rows.append(r"\midrule")
rows.append("Algoritmo & " + " & ".join(r"\textbf{" + fmt(v) + "}" for v in agg) + r" \\")
out.append(r"""\begin{table}[!t]
\caption{Ejemplo del artículo original (17\,s): aporte de cada regla para cada extensión $e$ (s). Coincide con la Tabla~VII del artículo.}
\label{tab:tabla7}
\centering
\scriptsize
\setlength{\tabcolsep}{2.2pt}
\begin{tabular}{@{}l*{10}{c}@{}}
\toprule
 & 1 & 2 & 3 & 4 & 5 & 6 & 7 & 8 & 9 & 10 \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}
""")

# ---------------- Tabla de las 25 reglas (desglose vertical: una caja por regla) ----------------
lab = {"none": "none", "afew": "a few", "few": "few", "medium": "medium", "many": "many", "toomany": "too many",
       "verysmall": "very small", "small": "small", "smallplus": "small plus", "long": "long", "verylong": "very long"}
tl = {"veryshort": "very short", "short": "short", "medium": "medium", "long": "long", "verylong": "very long"}


def caja(k, n):
    T, A, Q, E = fl.RULES[k][n]
    q = "any" if Q == "any" else f"lt({lab[Q]})"
    return (r"\begin{tabular}[t]{@{}l@{}}\textbf{R" + str(n + 1) + r"} \\ \textbf{SI} $T$ = " + tl[T]
            + r" \\ \textbf{Y} $A$ = mt(" + lab[A] + r") \\ \textbf{Y} $Q$ = " + q
            + r" \\ \textbf{ENTONCES} $E$ = " + tl[E] + r"\end{tabular}")


rows = []
for n in range(5):
    rows.append(" & ".join(caja(k, n) for k in fl.INTERVENTIONS) + r" \\" + ("\n\\midrule" if n < 4 else ""))
out.append(r"""\begin{table*}[!t]
\caption{Desglose de las 25 reglas del Apéndice del artículo original: cada columna es una intervención (segundo del verde en que el controlador decide) y cada caja es una regla, con sus condiciones sobre el tiempo $T$, los arribos $A$ y la cola $Q$, y su conclusión $E$. En todas las reglas $E=T$. La regla R5 de cada intervención es la que más extiende el verde.}
\label{tab:reglas}
\centering
\scriptsize
\setlength{\tabcolsep}{7pt}
\renewcommand{\arraystretch}{1.05}
\begin{tabular}{@{}ccccc@{}}
\toprule
7\,s & 17\,s & 27\,s & 37\,s & 47\,s \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table*}
""")

# ---------------- Tabla I ----------------
rows = []
e1, e2 = [], []
for r in res["table_I"]:
    pm, pf = pdta.TABLE_I[(r["ns"], r["ew"])]
    e1.append(abs(r["sim"] - pm) / pm * 100); e2.append(abs(r["formula"] - pf) / pf * 100)
    rows.append(f"{r['ns']}/{r['ew']} & {f(r['sim'])} & {pm} & {100 * (r['sim'] - pm) / pm:+.1f} & {f(r['formula'])} & {pf} & {100 * (r['formula'] - pf) / pf:+.1f} \\\\")
out.append(r"""\begin{table}[!t]
\caption{Tabla I del artículo original: retardo medio (s/veh) del ciclo fijo con ajustes óptimos. Simulación (""" + f"{res['reps']} réplicas de {res['duration']}" + r"""\,s) y fórmula de Webster frente a los valores publicados.}
\label{tab:tablaI}
\centering
\scriptsize
\setlength{\tabcolsep}{2.6pt}
\begin{tabular}{@{}lrrrrrr@{}}
\toprule
N--S/E--W & Sim. & Paper & Err.\,\% & Fórm. & Paper & Err.\,\% \\
\midrule
""" + "\n".join(rows) + r"""
\midrule
\multicolumn{3}{@{}l}{Error relativo medio} & """ + f"{np.mean(e1):.1f}" + r""" & & & """ + f"{np.mean(e2):.1f}" + r""" \\
\bottomrule
\end{tabular}
\end{table}
""")

# ---------------- Tabla VIII ----------------
rows = []
errs = []
for r in res["table_VIII"]["calibrada"]:
    pf, pz = pdta.TABLE_VIII[(r["ns"], r["ew"])]
    lit = next(x for x in res["table_VIII"]["literal"] if (x["ns"], x["ew"]) == (r["ns"], r["ew"]))
    errs.append(abs(r["fuzzy"] - pz) / pz * 100)
    rows.append(f"{r['ns']}/{r['ew']} & {f(r['fixed'])} & {pf} & {f(r['fuzzy'])} & {pz} & {100 * (r['fuzzy'] - pz) / pz:+.1f} & {r['improvement']:+.0f} & {100 * (pf - pz) / pf:+.0f} & {f(lit['fuzzy'], 1)} \\\\")
wins = sum(r["fuzzy"] < r["fixed"] for r in res["table_VIII"]["calibrada"])
lwins = sum(r["fuzzy"] < r["fixed"] for r in res["table_VIII"]["literal"])
out.append(r"""\begin{table*}[!t]
\caption{Tabla VIII del artículo original: retardo medio (s/veh) del controlador difuso frente a la línea base de ciclo fijo óptimo (""" + f"{res['reps']} réplicas de {res['duration']}" + r"""\,s). «Calibrada» y «literal» son las dos lecturas de las entradas del controlador (Sección~\ref{sec:lecturas}).}
\label{tab:tabla8}
\centering
\footnotesize
\setlength{\tabcolsep}{4pt}
\begin{tabular}{@{}lrrrrrrrr@{}}
\toprule
 & \multicolumn{2}{c}{Línea base} & \multicolumn{3}{c}{Difuso, lectura calibrada} & \multicolumn{2}{c}{Mejora (\%)} & Difuso \\
\cmidrule(lr){2-3}\cmidrule(lr){4-6}\cmidrule(lr){7-8}
N--S/E--W & Réplica & Paper & Réplica & Paper & Err.\,\% & Réplica & Paper & literal \\
\midrule
""" + "\n".join(rows) + r"""
\midrule
\multicolumn{5}{@{}l}{Mejora al ciclo fijo: calibrada """ + f"{wins}/16, literal {lwins}/16" + r"""} & """ + f"{np.mean(errs):.1f}" + r""" (media) & \multicolumn{3}{l}{máx. """ + f"{np.max(errs):.1f}" + r"""} \\
\bottomrule
\end{tabular}
\end{table*}
""")

# ---------------- Tabla de auditoria ----------------
na = {"arrivals": "arribos", "crossing": "cruces"}; nq = {"predicted": "predicha", "current": "actual"}
ns_ = {"total": "total", "green_arrivals": "desde el verde"}
rows = []
for v in aud["variants"]:
    mark = r" (calibrada)" if (v["a_mode"], v["q_mode"], v["queue_source"]) == ("crossing", "current", "green_arrivals") else (
        r" (literal)" if (v["a_mode"], v["q_mode"], v["queue_source"]) == ("arrivals", "predicted", "total") else "")
    rows.append(f"{na[v['a_mode']]} & {nq[v['q_mode']]} & {ns_[v['queue_source']]} & {v['mean_err']:.1f} & {v['max_err']:.0f} & {v['wins']}/16{mark} \\\\")
out.append(r"""\begin{table}[!t]
\caption{Auditoría de las ocho lecturas de las entradas del controlador (reglas fijas; """ + f"{aud['reps']} réplicas de {aud['duration']}" + r"""\,s). Error relativo frente a la Tabla VIII del artículo.}
\label{tab:auditoria}
\centering
\scriptsize
\setlength{\tabcolsep}{2.4pt}
\begin{tabular}{@{}lllrrr@{}}
\toprule
$A$ & $Q$ evaluada & Cola $Q$ & Medio\,\% & Máx.\,\% & Mejor que fijo \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}
""")

# ---------------- llegadas aleatorias vs fijas ----------------
out.append(r"""\begin{table}[!t]
\caption{Llegadas aleatorias frente a llegadas fijas (un vehículo cada $1/\lambda$ segundos): error relativo medio respecto del artículo (""" + f"{arr['reps']} réplicas de {arr['duration']}" + r"""\,s).}
\label{tab:llegadas}
\centering
\footnotesize
\begin{tabular}{@{}lcc@{}}
\toprule
Modelo de llegadas & Tabla I (\%) & Tabla VIII (\%) \\
\midrule
Aleatorias (Bernoulli por segundo) & """ + f"{arr['err_table_I']['bernoulli']:.1f} & {arr['err_table_VIII']['bernoulli']:.1f}" + r""" \\
Fijas & """ + f"{arr['err_table_I']['fijas']:.1f} & {arr['err_table_VIII']['fijas']:.1f}" + r""" \\
\bottomrule
\end{tabular}
\end{table}
""")

# ---------------- ablacion de reglas ----------------
rows = []
for v in abl["variants"]:
    rows.append(f"{v['key']} & {v['name']} & {v['n_rules']} & {v['mean_dm']:.1f} & {v['wins']}/16 \\\\")
out.append(r"""\begin{table}[!t]
\caption{Experimento exploratorio de reducción de reglas (lectura calibrada; """ + f"{abl['reps']} réplicas de {abl['duration']}" + r"""\,s). $d_m$ medio sobre los 16 caudales.}
\label{tab:ablacion}
\centering
\scriptsize
\setlength{\tabcolsep}{2.4pt}
\begin{tabular}{@{}cp{0.5\columnwidth}rrr@{}}
\toprule
 & Reglas conservadas & N.º & $d_m$ (s) & Mejor que fijo \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}
""")
# ---------------- incertidumbre estadistica (IC 95 %) ----------------
rows = []
for r in est["rows"]:
    fx, fz, rd = r["fixed"], r["fuzzy"], r["reduction"]
    mk = lambda d: f"{d['mean']:.2f}\\,$\\pm$\\,{(d['hi'] - d['lo']) / 2:.2f}"
    dg = lambda d: "\\checkmark" if d["paper_in_ci"] else ""
    rows.append(f"{r['ns']}/{r['ew']} & {mk(fx)} & {fx['paper']:.1f} & {dg(fx)} & {mk(fz)} & {fz['paper']:.1f} & {dg(fz)} & {rd['pct']:.1f} \\\\")
sf, sz = est["sesgo_fijo"], est["sesgo_difuso"]
out.append(r"""\begin{table}[!t]
\caption{Incertidumbre estadística de la réplica (""" + f"{est['reps']} réplicas de {est['duration']}" + r"""\,s, lectura calibrada): retardo medio $\pm$ semiancho del IC al 95\,\%, valor publicado y marca ($\checkmark$) si el valor publicado cae dentro del intervalo. Mejora en \% sobre el ciclo fijo simulado; en las 16 combinaciones $p<0.001$ (Welch).}
\label{tab:estadistica}
\centering
\scriptsize
\setlength{\tabcolsep}{2.2pt}
\begin{tabular}{@{}lrrcrrcr@{}}
\toprule
 & \multicolumn{3}{c}{Ciclo fijo (s)} & \multicolumn{3}{c}{Difuso (s)} & \\
\cmidrule(lr){2-4}\cmidrule(lr){5-7}
N-S/E-W & Réplica & Pub. & En IC & Réplica & Pub. & En IC & Mej. \\
\midrule
""" + "\n".join(rows) + r"""
\midrule
\multicolumn{3}{@{}l}{Publicado dentro del IC} & """ + f"{est['n_paper_en_ci_fijo']}/16" + r""" & & & """ + f"{est['n_paper_en_ci_difuso']}/16" + r""" & \\
\multicolumn{3}{@{}l}{Sesgo medio réplica$-$publicado (\%)} & """ + f"{sf['mean_pct']:.1f}" + r""" & & & """ + f"{sz['mean_pct']:.1f}" + r""" & \\
\bottomrule
\end{tabular}
\end{table}
""")
# ---------------- verificacion numerica de las deducciones ----------------
v = ver
out.append(r"""\begin{table*}[!t]
\caption{Verificación numérica de las deducciones de la Sección~\ref{sec:formulas}: cada fórmula se compara con un cálculo independiente.}
\label{tab:verificacion}
\centering
\footnotesize
\setlength{\tabcolsep}{3pt}
\begin{tabular}{@{}p{0.2\textwidth}p{0.34\textwidth}p{0.17\textwidth}p{0.2\textwidth}@{}}
\toprule
Fórmula & Cálculo independiente con que se compara & Casos & Resultado \\
\midrule
\eqref{eq:retardoR}, \eqref{eq:retardoG}: $D=\sum_n$ colas & suma de las esperas individuales de cada vehículo (cola FIFO con vehículos explícitos) & """ + f"{v['colas']['casos']}" + r""" escenarios aleatorios & diferencia máxima """ + f"{v['colas']['max_dif']:.0f}" + r""" s$\cdot$veh \\
Término uniforme de \eqref{eq:retardo-webster} & área de la cola de un modelo fluido determinista (paso de 1\,ms) & """ + f"{v['uniforme']['casos']}" + r""" ciclos $(C,\lambda,q)$ & error relativo máximo """ + f"{100 * v['uniforme']['max_err_rel']:.3f}" + r"""\,\% \\
Término aleatorio de \eqref{eq:retardo-webster} & cola M/D/1 simulada con la recursión de Lindley ($1.5\cdot10^{6}$ clientes) & $X=0.3,\ 0.6,\ 0.8$ & error relativo máximo """ + f"{100 * v['md1']['max_err_rel']:.1f}" + r"""\,\% (ruido de la simulación) \\
Reparto $g_i=(y_i/Y)(C_0-L)$ de \eqref{eq:webster} & igualdad de los grados de saturación $X_1=X_2$ & """ + f"{v['ciclo']['casos']}" + r""" pares de caudales & diferencia máxima $<10^{-15}$ \\
Ciclo $C_0$ de \eqref{eq:webster} & mínimo numérico del retardo de Webster completo, con el mismo reparto de verdes & """ + f"{v['ciclo']['casos']}" + r""" pares de caudales & el retardo en $C_0$ excede al mínimo en """ + f"{100 * v['ciclo']['max_exceso_retardo']:.1f}" + r"""\,\% como máximo \\
\eqref{eq:lt}, \eqref{eq:mt}: $\max=1-\mu_A$ y $\min=0$ & valores de $\mu_A$ de las Tablas~III y~IV con $x\neq x_0$ & """ + f"{v['mtlt']['puntos']}" + r""" puntos de 12 conjuntos & """ + f"{v['mtlt']['fallos_propiedad']}" + r""" fallos \\
Regla composicional con entrada exacta & $\max_x\min\{R(x,y),A(x)\}$ frente a la fila $R(x_0,y)$ & """ + f"{v['singleton']['casos']}" + r""" relaciones aleatorias & diferencia máxima """ + f"{v['singleton']['max_dif']:.0f}" + r""" \\
Conteos & $5\cdot6\cdot6$; $5\cdot5$; $7+5\cdot10$ & 3 conteos & """ + f"{v['conteos']['producto']}; {v['conteos']['reglas']}; {v['conteos']['verde_max']}" + r""" \\
\bottomrule
\end{tabular}
\end{table*}
""")
names = ["tabla_VII", "tabla_reglas", "tabla_I", "tabla_VIII", "tabla_auditoria", "tabla_llegadas", "tabla_ablacion", "tabla_estadistica", "tabla_verificacion"]
FUENTE = {
    "tabla_VII": r"calculada con \eqref{eq:premisa} y \eqref{eq:decision} a partir de los conjuntos de las Tablas~II a~VI y de los vectores del ejemplo del artículo original (pp.~713 y~714); coincide con su Tabla~VII (p.~714). Código: \texttt{fuzzy\_logic.py}, \texttt{test\_paper\_tables.py}.",
    "tabla_reglas": r"Apéndice del artículo original (pp.~715 y~716), leído de la imagen de las páginas; verificado con \texttt{test\_paper\_tables.py}.",
    "tabla_I": r"columnas «Paper»: Tabla~I del artículo original (p.~708); «Sim.»: simulación propia con las ecuaciones \eqref{eq:colaR}--\eqref{eq:dm} (\texttt{run\_experiments.py}, \texttt{resultados/resultados\_oficiales.json}); «Fórm.»: evaluación de \eqref{eq:retardo-webster} con los ajustes de \eqref{eq:webster}. Err.\,$=100\,(\text{réplica}-\text{paper})/\text{paper}$.",
    "tabla_VIII": r"columnas «Paper»: Tabla~VIII del artículo original (p.~715); «Réplica»: simulación propia (\texttt{run\_experiments.py}, \texttt{resultados/resultados\_oficiales.json}). Mejora\,$=100\,(\text{fijo}-\text{difuso})/\text{fijo}$; la mejora «Paper» se recalcula con los retardos impresos y difiere de la columna impresa solo en 720/720 (+21 impreso; 23.7 recalculado). Err.\,$=100\,(\text{réplica}-\text{paper})/\text{paper}$.",
    "tabla_auditoria": r"simulaciones propias (\texttt{fidelity\_audit.py}, \texttt{resultados/fidelity\_audit.json}) comparadas con la Tabla~VIII del artículo original (p.~715).",
    "tabla_llegadas": r"simulaciones propias (\texttt{arrival\_model\_check.py}, \texttt{resultados/llegadas\_fijas\_vs\_aleatorias.json}) comparadas con las Tablas~I y~VIII del artículo original (pp.~708 y~715).",
    "tabla_ablacion": r"simulaciones propias (\texttt{ablacion\_reglas.py}, \texttt{resultados/ablacion\_reglas.json}) con subconjuntos de las reglas del Apéndice del artículo original (pp.~715 y~716); línea base: ciclo fijo de la Tabla~I.",
    "tabla_verificacion": r"\texttt{verificar\_formulas.py} (\texttt{resultados/verificacion\_formulas.json}); los casos aleatorios usan la semilla 2026. La comparación $C_0$ frente al mínimo numérico usa los caudales de la Tabla~VIII (360/360, 720/1080, 1080/1440 y 1440/1440).",
    "tabla_estadistica": r"\texttt{analisis\_estadistico.py} (\texttt{resultados/analisis\_estadistico.json}), con las 20 réplicas de cada celda; valores «Pub.»: Tabla~I (ciclo fijo, p.~708) y Tabla~VIII (difuso, p.~715) del artículo original. IC con la distribución $t$ de Student ($n=20$); mejora contrastada con la prueba de Welch.",
}
for n in list(FUENTE):
    i = names.index(n)
    t = out[i]
    j = t.rindex("\\end{tabular}") + len("\\end{tabular}")
    out[i] = t[:j] + "\n\\fuente{" + FUENTE[n] + "}" + t[j:]
for n, t in zip(names, out):
    open(f"articulo_ieee/{n}.tex", "w", encoding="utf-8").write(t)
print("tablas generadas: Tabla I error", round(np.mean(e1), 1), round(np.mean(e2), 1), "| Tabla VIII", round(np.mean(errs), 1), round(np.max(errs), 1), wins, lwins)
