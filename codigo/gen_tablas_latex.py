"""
gen_tablas_latex.py
================================================================================
Genera articulo_replica/tabla_*.tex (un archivo por tabla) con las tablas del articulo a partir de los JSON del proyecto
(resultados_oficiales, analisis_estadistico, comparadores, fidelity_audit, llegadas_fijas_vs_aleatorias, ablacion_reglas,
efecto_borde, disparos_agregados, verificacion_formulas) y de fuzzy_logic.py (reglas), para que los numeros del texto y de
las tablas no se desincronicen.
Uso:  python codigo/gen_tablas_latex.py
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
cmp_ = json.load(open("resultados/comparadores.json"))
brd = json.load(open("resultados/efecto_borde.json"))
dsp = json.load(open("resultados/disparos_agregados.json"))
ent = json.load(open("resultados/entorno.json"))
out = {}          # nombre de archivo -> contenido


def f(x, nd=2):
    return f"{x:.{nd}f}"


def pm(m, lo, hi, nd=2):
    """media ± semiancho del IC."""
    return f"{m:.{nd}f}\\,$\\pm$\\,{(hi - lo) / 2:.{nd}f}"


def pval(p):
    if p < 0.001:
        return "$<0.001$"
    return f"{p:.3f}"


# ---------------- Tabla VII: ejemplo ----------------
per = fl.fuzzy_decision_per_rule(pdta.EXAMPLE_X, pdta.EXAMPLE_XP, pdta.EXAMPLE_Q, fl.RULES[17], a_mode="arrivals", q_mode="predicted")[:, 1:]
agg = per.max(axis=0)
fmt = lambda v: "0" if abs(v) < 1e-12 else f"{v:g}"
rows = []
for i, nm in enumerate(["R1 very short", "R2 short", "R3 medium", "R4 long", "R5 very long"]):
    rows.append(f"{nm} & " + " & ".join(fmt(v) for v in per[i]) + r" \\")
rows.append(r"\midrule")
rows.append("Algoritmo & " + " & ".join(r"\textbf{" + fmt(v) + "}" for v in agg) + r" \\")
out["tabla_VII"] = (r"""\begin{table}[!t]
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
out["tabla_reglas"] = (r"""\begin{table*}[!t]
\caption{Desglose de las 25 reglas del Apéndice del artículo original: cada columna es una intervención y cada caja una regla, con sus condiciones sobre $T$, $A$ y $Q$ y su conclusión $E=T$. R5 es la que más extiende el verde.}
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


# ---------------- Tabla I (validacion del modelo) + ajustes de Webster y efecto del redondeo ----------------
wd = {}
for w, r in zip(cmp_["webster"], cmp_["rows"]):
    a_, b_ = r["fijo"], r["fijo_sin_red"]
    dif = 100 * (b_["mean"] - a_["mean"]) / a_["mean"]
    star = "$^{*}$" if r["tests"]["fijo_sin_red_vs_fijo"]["p_holm"] < 0.05 else ""
    marca = r"\textbf{" if abs(w["Ceff"] - w["C0"]) > 0.5 else "{"
    wd[(w["ns"], w["ew"])] = (f"{w['C0']:.1f} & {marca}{w['Ceff']}" + "}" + f" & {w['g1']:.2f}/{w['g2']:.2f} & {w['r1']}/{w['r2']}",
                              f"{b_['mean']:.2f} & {dif:+.1f}{star}")
n_ceff = sum(abs(w["Ceff"] - w["C0"]) > 0.5 for w in cmp_["webster"])
n_sig = sum(r["tests"]["fijo_sin_red_vs_fijo"]["p_holm"] < 0.05 for r in cmp_["rows"])
rows = []
e1, e2 = [], []
for r in res["table_I"]:
    pm_, pf_ = pdta.TABLE_I[(r["ns"], r["ew"])]
    e1.append(abs(r["sim"] - pm_) / pm_ * 100)
    e2.append(abs(r["formula"] - pf_) / pf_ * 100)
    w1, w2 = wd[(r["ns"], r["ew"])]
    rows.append(f"{r['ns']}/{r['ew']} & {w1} & {f(r['sim'])} & {pm_} & {100 * (r['sim'] - pm_) / pm_:+.1f} & {f(r['formula'])} & {pf_} & {100 * (r['formula'] - pf_) / pf_:+.1f} & {w2} \\\\")
E_I_SIM, E_I_FORM = float(np.mean(e1)), float(np.mean(e2))
out["tabla_I"] = (r"""\begin{table*}[!t]
\caption{Validación del modelo (Tabla I del original) y ajustes de Webster: ciclo óptimo $C_0$, ciclo efectivo $C_{\mathrm{ef}}=g_1'+g_2'+10$ (en negrita, los """ + f"{n_ceff}" + r""" flujos con $C_{\mathrm{ef}}\ne C_0$), verdes sin redondear ($g_i$) y redondeados ($g_i'$); retardo medio (s/veh) del ciclo fijo con verdes redondeados (Sim.), con la fórmula de Webster (Fórm.) y con verdes sin redondear; $^{*}$: diferencia significativa (Wilcoxon pareado, Holm). """ + f"{res['reps']} réplicas de {res['duration']}" + r"""\,s.}
\label{tab:tablaI}
\centering
\scriptsize
\setlength{\tabcolsep}{3pt}
\begin{tabular}{@{}lrrcrrrrrrrrr@{}}
\toprule
 & \multicolumn{4}{c}{Ajustes de Webster} & \multicolumn{6}{c}{Retardo con verdes redondeados} & \multicolumn{2}{c}{Sin redondear} \\
\cmidrule(lr){2-5}\cmidrule(lr){6-11}\cmidrule(lr){12-13}
N--S/E--W & $C_0$ & $C_{\mathrm{ef}}$ & $g_1/g_2$ & $g_1'/g_2'$ & Sim. & Pub. & Err.\,\% & Fórm. & Pub. & Err.\,\% & $d_m$ & Dif.\,\% \\
\midrule
""" + "\n".join(rows) + r"""
\midrule
\multicolumn{7}{@{}l}{Error relativo medio (valor absoluto, \%)} & """ + f"{E_I_SIM:.1f}" + r""" & & & """ + f"{E_I_FORM:.1f}" + r""" & & \\
\bottomrule
\end{tabular}
\fuente{Tabla~I del artículo original (p.~708) para las columnas «Pub.»; simulación propia con \eqref{eq:colaR}--\eqref{eq:dm} (\texttt{run\_experiments.py}, \texttt{comparadores.py}); fórmula propia de \eqref{eq:retardo-webster} con los ajustes de \eqref{eq:webster} (\texttt{traffic\_model.webster\_optimum}). Err.\,$=100(\text{réplica}-\text{pub.})/\text{pub.}$}
\end{table*}
""")

# ---------------- Tabla VIII ampliada: difuso, fijo, IC, comparador actuado ----------------
rows = []
errs = []
n_better_act = n_worse_act = n_ns_act = 0
for r, c in zip(est["rows"], cmp_["rows"]):
    pf_, pz_ = pdta.TABLE_VIII[(r["ns"], r["ew"])]
    fx, fz, rd = r["fixed"], r["fuzzy"], r["reduction"]
    errs.append(abs(fz["mean"] - pz_) / pz_ * 100)
    act = c["actuado"]
    dact = 100 * (fz["mean"] - act["mean"]) / act["mean"]
    tt = c["tests"]["difuso_vs_actuado"]
    sig = tt["p_holm"] < 0.05
    n_better_act += sig and dact < 0
    n_worse_act += sig and dact > 0
    n_ns_act += not sig
    rows.append(f"{r['ns']}/{r['ew']} & {pm(fx['mean'], fx['lo'], fx['hi'])} & {pf_} & {pm(fz['mean'], fz['lo'], fz['hi'])} & {pz_} & "
                f"{100 * (fz['mean'] - pz_) / pz_:+.1f} & {rd['pct']:.1f} & {100 * (pf_ - pz_) / pf_:.1f} & {f(act['mean'])} & {dact:+.1f}{'$^{*}$' if sig else ''} \\\\")
sf, sz = est["sesgo_fijo"], est["sesgo_difuso"]
ms = cmp_["resumen"]["medias"]
out["tabla_VIII"] = (r"""\begin{table*}[!t]
\caption{Difuso frente al ciclo fijo (Tabla VIII del original) y a un controlador actuado por detector (comparador adicional); """ + f"{est['reps']} réplicas de {est['duration']}" + r"""\,s con números aleatorios comunes. Retardo medio (s/veh) $\pm$ semiancho del IC 95\,\%. «Mej.»: reducción del difuso respecto del fijo (\%), con la réplica y con los retardos impresos; «Dif. vs act.»: diferencia relativa del difuso respecto del actuado; $^{*}$: significativa (Wilcoxon pareado, Holm, $p<0.05$).}
\label{tab:tabla8}
\centering
\footnotesize
\setlength{\tabcolsep}{3.2pt}
\begin{tabular}{@{}lrrrrrrrrr@{}}
\toprule
 & \multicolumn{2}{c}{Ciclo fijo} & \multicolumn{3}{c}{Difuso (25 reglas, calibrada)} & \multicolumn{2}{c}{Mej.\,(\%)} & Accionado & Dif. vs \\
\cmidrule(lr){2-3}\cmidrule(lr){4-6}\cmidrule(lr){7-8}
N--S/E--W & Réplica & Pub. & Réplica & Pub. & Err.\,\% & Réplica & Pub. & (s/veh) & act.\,\% \\
\midrule
""" + "\n".join(rows) + r"""
\midrule
\multicolumn{5}{@{}l}{Mejora al ciclo fijo: 16/16 (Holm $p\le$ """ + f"{est['p_holm_max']:.1e}" + r""")} & """ + f"{np.mean(errs):.1f}" + r""" (media) & \multicolumn{4}{l}{error máx. """ + f"{np.max(errs):.1f}" + r"""\,\%} \\
\multicolumn{5}{@{}l}{Medias de los 16 flujos (s/veh): fijo / difuso / accionado} & \multicolumn{5}{l}{""" + f"{ms['fijo']:.2f} / {ms['difuso']:.2f} / {ms['actuado']:.2f}" + r"""} \\
\bottomrule
\end{tabular}
\fuente{columnas «Pub.»: Tabla~VIII del artículo original (p.~715); «Mej. pub.» recalculada con sus retardos (el artículo imprime +21\,\% en 720/720; recalculado, 23.7\,\%). Réplica: \texttt{analisis\_estadistico.py} y \texttt{comparadores.py}; IC con la distribución $t$ de Student, $n_r=20$. El comparador accionado (extensión por hueco de 3\,s, verde de 7 a 57\,s) no es parte del artículo original.}
\end{table*}
""")

# ---------------- Auditoria de las 8 lecturas ----------------
na = {"arrivals": "arribos", "crossing": "cruces"}; nq = {"predicted": "predicha", "current": "actual"}
ns_ = {"total": "total", "green_arrivals": "desde el verde"}
rows = []
for v in aud["variants"]:
    mark = r" (calibrada)" if (v["a_mode"], v["q_mode"], v["queue_source"]) == ("crossing", "current", "green_arrivals") else (
        r" (literal)" if (v["a_mode"], v["q_mode"], v["queue_source"]) == ("arrivals", "predicted", "total") else "")
    rows.append(f"{na[v['a_mode']]} & {nq[v['q_mode']]} & {ns_[v['queue_source']]} & {v['mean_err']:.1f}\\,$\\pm$\\,{v['err_rep_sd']:.1f} & {v['max_err']:.0f} & {v['wins']}/16 ({v['wins_sig']}){mark} \\\\")
out["tabla_auditoria"] = (r"""\begin{table}[!t]
\caption{Auditoría de las ocho lecturas de las entradas del controlador (25 reglas fijas; """ + f"{aud['reps']} réplicas de {aud['duration']}" + r"""\,s con números aleatorios comunes). Error relativo frente a la Tabla VIII del original: el de los retardos medios de las réplicas (medio entre los 16 flujos, y máximo) $\pm$ la desviación estándar entre réplicas del error por réplica; entre paréntesis, flujos con mejora significativa sobre el fijo (Wilcoxon pareado, Holm).}
\label{tab:auditoria}
\centering
\scriptsize
\setlength{\tabcolsep}{2.2pt}
\begin{tabular}{@{}lllrrr@{}}
\toprule
$A$ & $Q$ evaluada & Cola $Q$ & Medio\,\% & Máx.\,\% & Mejor que fijo \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\fuente{simulaciones propias (\texttt{fidelity\_audit.py}) comparadas con la Tabla~VIII del artículo original (p.~715).}
\end{table}
""")

# ---------------- llegadas aleatorias vs fijas ----------------
w1, w8 = arr["wilcoxon_celdas"]["tabla_I"]["p"], arr["wilcoxon_celdas"]["tabla_VIII"]["p"]
tI, t8 = arr["tabla_I"], arr["tabla_VIII"]
out["tabla_llegadas"] = (r"""\begin{table}[!t]
\caption{Llegadas aleatorias frente a llegadas fijas (un vehículo cada $1/\lambda$ segundos con desfase aleatorio): error relativo medio de los retardos medios respecto del artículo $\pm$ desviación estándar entre réplicas del error por réplica (""" + f"{arr['reps']} réplicas de {arr['duration']}" + r"""\,s). $p$: prueba de Wilcoxon pareada entre los errores de las 16 celdas.}
\label{tab:llegadas}
\centering
\footnotesize
\begin{tabular}{@{}lcc@{}}
\toprule
Modelo de llegadas & Tabla I (\%) & Tabla VIII (\%) \\
\midrule
Aleatorias (Bernoulli por segundo) & """ + f"{tI['bernoulli']['media']:.1f}\\,$\\pm$\\,{tI['bernoulli']['sd']:.1f} & {t8['bernoulli']['media']:.1f}\\,$\\pm$\\,{t8['bernoulli']['sd']:.1f}" + r""" \\
Fijas & """ + f"{tI['fijas']['media']:.1f}\\,$\\pm$\\,{tI['fijas']['sd']:.1f} & {t8['fijas']['media']:.1f}\\,$\\pm$\\,{t8['fijas']['sd']:.1f}" + r""" \\
$p$ (Wilcoxon) & """ + f"{pval(w1)} & {pval(w8)}" + r""" \\
\bottomrule
\end{tabular}
\fuente{simulaciones propias (\texttt{arrival\_model\_check.py}) comparadas con las Tablas~I y~VIII del artículo original (pp.~708 y~715).}
\end{table}
""")

# ---------------- ablacion de reglas ----------------
rows = []
base = abl["variants"][0]["dm_rep_mean"]
for v in abl["variants"]:
    if v["key"] == "A":
        ext = "--- & ---"
    else:
        ext = f"{100 * (v['dm_rep_mean'] - base) / base:+.1f} & {pval(v['wilcoxon_vs_A_p_holm'])}"
    rows.append(f"{v['key']} & {v['name'].replace('Paper:', 'Original:')} & {v['n_rules']} & {v['dm_rep_mean']:.2f}\\,$\\pm$\\,{v['dm_rep_sd']:.2f} & {ext} & {v['wins']}/16 \\\\")
fr = abl["friedman"]
out["tabla_ablacion"] = (r"""\begin{table}[!t]
\caption{Reducción de reglas (lectura calibrada; """ + f"{abl['reps']} réplicas de {abl['duration']}" + r"""\,s con números aleatorios comunes). $d_m$: retardo medio de los 16 flujos por réplica (media $\pm$ desviación estándar). «Dif.»: respecto de las 25 reglas; $p$: Wilcoxon pareado con Holm. «Mej. fijo»: flujos en que mejora al ciclo fijo. Friedman entre las 6 variantes: $\chi^2_5=""" + f"{fr['chi2']:.1f}" + r"""$, $p<0.001$.}
\label{tab:ablacion}
\centering
\scriptsize
\setlength{\tabcolsep}{1.6pt}
\begin{tabular}{@{}cp{0.27\columnwidth}rrrrr@{}}
\toprule
 & Reglas conservadas & N.º & $d_m$ (s) & Dif.\,\% & $p$ & Mej. fijo \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\fuente{simulaciones propias (\texttt{ablacion\_reglas.py}) con subconjuntos de las reglas del Apéndice del artículo original (pp.~715 y~716); línea base: ciclo fijo de la Tabla~I.}
\end{table}
""")

# ---------------- efecto de borde ----------------
rs = brd["resumen"]
out["tabla_borde"] = (r"""\begin{table}[!t]
\caption{Efecto de borde del horizonte: aumento relativo del retardo medio al sumar la espera residual de los vehículos que siguen en cola en $t=H$ (""" + f"{brd['reps']} réplicas de {brd['duration']}" + r"""\,s, 16 flujos).}
\label{tab:borde}
\centering
\footnotesize
\begin{tabular}{@{}lrr@{}}
\toprule
Controlador & Media (\%) & Máximo (\%) \\
\midrule
Ciclo fijo & """ + f"{rs['fijo']['media_pct']:.2f} & {rs['fijo']['max_pct']:.2f}" + r""" \\
Difuso, lectura calibrada & """ + f"{rs['calibrada']['media_pct']:.2f} & {rs['calibrada']['max_pct']:.2f}" + r""" \\
Difuso, lectura literal (saturada) & """ + f"{rs['literal']['media_pct']:.1f} & {rs['literal']['max_pct']:.1f}" + r""" \\
\bottomrule
\end{tabular}
\fuente{simulaciones propias (\texttt{efecto\_borde.py}) con las mismas llegadas, con y sin \texttt{Sim.residual\_delay}.}
\end{table}
""")

# ---------------- activacion y disparo agregados ----------------
rows = []
for fl_ in dsp["flujos"]:
    d, c, e = fl_["decisiones_por_replica"], fl_["cortes"], fl_["e10"]
    disp = " & ".join(f"{100 * m:.1f}\\,$\\pm$\\,{100 * s:.1f}" for m, s in zip(fl_["dispara"]["mean"], fl_["dispara"]["sd"]))
    rows.append(f"{fl_['ns']}/{fl_['ew']} & {d['mean']:.0f} & {100 * c['mean']:.1f}\\,$\\pm$\\,{100 * c['sd']:.1f} & {100 * e['mean']:.1f}\\,$\\pm$\\,{100 * e['sd']:.1f} & {disp} \\\\")
out["tabla_disparos"] = (r"""\begin{table*}[!t]
\caption{Activación y disparo de las reglas agregados sobre """ + f"{dsp['reps']} réplicas de {dsp['duration']}" + r"""\,s en cuatro regímenes de tráfico (media $\pm$ desviación estándar entre réplicas). «Decisiones»: por réplica; «cortes»: fracción de decisiones con $e^*=0$; «$e^*=10$»: fracción con extensión máxima; R1 a R5: porcentaje de las extensiones en que la regla R$i$ (de cualquier intervención) dispara.}
\label{tab:disparos}
\centering
\footnotesize
\setlength{\tabcolsep}{4pt}
\begin{tabular}{@{}lrrrrrrrr@{}}
\toprule
N--S/E--W & Decisiones & Cortes (\%) & $e^*=10$ (\%) & R1 & R2 & R3 & R4 & R5 \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\fuente{simulaciones propias (\texttt{informe\_agregado.py}, \texttt{resultados/disparos\_agregados.json}), lectura calibrada y 25 reglas del Apéndice del artículo original (pp.~715 y~716).}
\end{table*}
""")

# ---------------- verificacion numerica de las deducciones ----------------
v = ver
out["tabla_verificacion"] = (r"""\begin{table}[!t]
\caption{Verificación numérica de las deducciones de las Secciones~\ref{sec:modelo} y~\ref{sec:controlador}: cada fórmula se compara con un cálculo independiente.}
\label{tab:verificacion}
\centering
\scriptsize
\setlength{\tabcolsep}{2.4pt}
\begin{tabular}{@{}p{0.34\columnwidth}p{0.33\columnwidth}p{0.24\columnwidth}@{}}
\toprule
Fórmula & Cálculo independiente & Resultado \\
\midrule
\eqref{eq:retardoR}, \eqref{eq:retardoG}: $D=\sum_n$ colas & suma de esperas individuales (FIFO), """ + f"{v['colas']['casos']}" + r""" escenarios & dif. máx. """ + f"{v['colas']['max_dif']:.0f}" + r""" \\
Simulador: $\sum_n$ colas & espera de los que salieron $+$ residual (""" + f"{v['sim_real']['casos']}" + r""" corridas) & dif. máx. """ + f"{v['sim_real']['max_dif']:.0f}" + r""" \\
Primer término de \eqref{eq:retardo-webster} & área de la cola de un modelo fluido & error """ + f"{100 * v['uniforme']['max_err_rel']:.3f}" + r"""\,\% \\
Segundo término de \eqref{eq:retardo-webster} & cola M/D/1 simulada (Lindley) & error """ + f"{100 * v['md1']['max_err_rel']:.1f}" + r"""\,\% (ruido) \\
Reparto $g_i$ de \eqref{eq:webster} & igualdad $X_1=X_2$ & dif. $<10^{-15}$ \\
Ciclo $C_0$ de \eqref{eq:webster} & mínimo numérico de Webster & retardo $\le$ """ + f"{100 * v['ciclo']['max_exceso_retardo']:.1f}" + r"""\,\% sobre el mínimo \\
\eqref{eq:lt}, \eqref{eq:mt}: $\max=1-\mu_A$, $\min=0$ & """ + f"{v['mtlt']['puntos']}" + r""" puntos de 12 conjuntos & """ + f"{v['mtlt']['fallos_propiedad']}" + r""" fallos \\
Regla composicional exacta & """ + f"{v['singleton']['casos']}" + r""" relaciones aleatorias & dif. máx. """ + f"{v['singleton']['max_dif']:.0f}" + r""" \\
Conteos & $5\cdot6\cdot6$; $5\cdot5$; $7+5\cdot10$ & """ + f"{v['conteos']['producto']}; {v['conteos']['reglas']}; {v['conteos']['verde_max']}" + r""" \\
\bottomrule
\end{tabular}
\fuente{\texttt{verificar\_formulas.py} (semilla 2026); caudales de la Tabla~VIII para la comparación de $C_0$.}
\end{table}
""")

for n, t in out.items():
    open(f"articulo_replica/{n}.tex", "w", encoding="utf-8").write(t)
print("tablas:", ", ".join(out))
print(f"Tabla I: error {E_I_SIM:.2f} / {E_I_FORM:.2f} | Tabla VIII: error medio {np.mean(errs):.2f}, max {np.max(errs):.2f} | difuso vs accionado: mejor {n_better_act}, peor {n_worse_act}, n.s. {n_ns_act}")
print(f"redondeo: {n_ceff} flujos con Ceff != C0; {n_sig} con diferencia significativa")
