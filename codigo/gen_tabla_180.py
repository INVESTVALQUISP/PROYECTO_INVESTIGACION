"""
gen_tabla_180.py
================================================================================
Las 180 reglas T x A x Q (5 x 6 x 6), escritas una por una, con las 25 reglas del autor
resaltadas en verde. Cada regla tiene la forma
    SI T = t  Y  A = mt(a)  Y  Q = lt(q)  ENTONCES  E = t
y el paper usa 25 de ellas: 5 reglas (R1..R5) en cada una de las 5 intervenciones
(7, 17, 27, 37 y 47 s). Para cada regla se indica en que intervenciones (y como R1..R5)
la usa el autor. La regla R1 del autor usa Q = "any" (sin condicion sobre la cola), por
eso cubre las seis reglas (Q = very small ... very long) de su fila en cada intervencion.

Salida:  resultados/reglas_180.csv   (una fila por regla)
         articulo_ieee/tabla_180.tex (una sola tabla larga con las 180 reglas)
Uso:  python codigo/gen_tabla_180.py
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import csv

import fuzzy_logic as fl

T_LAB = ["veryshort", "short", "medium", "long", "verylong"]
A_LAB = list(fl.MU_ARR)           # none, afew, few, medium, many, toomany
Q_LAB = list(fl.MU_QUEUE)         # verysmall, small, smallplus, medium, long, verylong
TXT = {"veryshort": "very short", "short": "short", "medium": "medium", "long": "long", "verylong": "very long",
       "none": "none", "afew": "a few", "few": "few", "many": "many", "toomany": "too many",
       "verysmall": "very small", "small": "small", "smallplus": "small plus"}
for k in ("medium", "long"):
    TXT.setdefault(k, k)

# (T, A, Q) -> {intervencion: (n.o de regla R1..R5, usa_any)}
used = {}
n_uses = 0
for k in fl.INTERVENTIONS:
    for n, (T, A, Q, E) in enumerate(fl.RULES[k], start=1):
        assert E == T
        n_uses += 1
        for q in (Q_LAB if Q == "any" else [Q]):
            used.setdefault((T, A, q), {})[k] = (n, Q == "any")
assert n_uses == 25

rows, idx = [], 0
for T in T_LAB:
    for A in A_LAB:
        for Q in Q_LAB:
            idx += 1
            u = used.get((T, A, Q), {})
            rows.append(dict(
                id=idx,
                regla=f"SI T={TXT[T]} Y A=mt({TXT[A]}) Y Q=lt({TXT[Q]}) ENTONCES E={TXT[T]}",
                usada_por_el_autor=int(bool(u)),
                **{f"interv_{k}s": (f"R{u[k][0]}" if k in u else "") for k in fl.INTERVENTIONS}))
with open("resultados/reglas_180.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
n_rows_used = sum(r["usada_por_el_autor"] for r in rows)
print(f"{len(rows)} reglas; {n_rows_used} filas resaltadas = las 25 reglas del autor "
      f"(R2-R5: 20 filas-intervencion; R1 con Q=any: 5 reglas x 6 colas)")


def fila(idx, T, A, Q):
    u = used.get((T, A, Q), {})
    e = TXT[T]
    regla = (f"\\textbf{{SI}} $T$ = {e} \\textbf{{Y}} $A$ = mt({TXT[A]}) "
             f"\\textbf{{Y}} $Q$ = lt({TXT[Q]}) \\textbf{{ENTONCES}} $E$ = {e}")
    cells = []
    for k in fl.INTERVENTIONS:
        if k in u:
            n, any_ = u[k]
            cells.append(f"\\cellcolor{{green!35}}R{n}" + ("*" if any_ else ""))
        else:
            cells.append("")
    mark = "\\textbf{\\checkmark}" if u else "$\\times$"
    row = f"{idx} & {regla} & " + " & ".join(cells) + f" & {mark} \\\\"
    return ("\\rowcolor{green!14}" + row) if u else row


body = []
idx0 = 0
for T in T_LAB:
    for A in A_LAB:
        for Q in Q_LAB:
            idx0 += 1
            body.append(fila(idx0, T, A, Q))
            if idx0 % 36 == 0 and idx0 < 180:
                body.append("\\midrule")

cab = r"\# & Regla & 7\,s & 17\,s & 27\,s & 37\,s & 47\,s & Usada \\"
tex = (r"""{\scriptsize
\setlength{\tabcolsep}{3pt}
\renewcommand{\arraystretch}{1.0}
\begin{longtable}{@{}r l ccccc c@{}}
\caption{Las 180 reglas del espacio $T\times A\times Q$ ($5\times6\times6$; cada una concluye $E=T$). Las que usa el autor están resaltadas en verde y marcadas con $\checkmark$; las demás, con $\times$. Las columnas de intervención indican con qué número de regla (R1 a R5) la usa cada intervención; R1* es la regla R1 del autor, que usa $Q=$ any (no condiciona la cola) y por eso cubre las seis reglas de su fila.}
\label{tab:180}\\
\toprule
""" + cab + r"""
\midrule
\endfirsthead
\toprule
""" + cab + r"""
\midrule
\endhead
\midrule
\multicolumn{8}{r}{\textit{continúa en la página siguiente}}\\
\endfoot
\bottomrule
\multicolumn{8}{@{}p{0.98\textwidth}@{}}{\vspace{2pt}\textit{Fuente:} etiquetas de $T$, $A$ y $Q$ de las Tablas~II a~IV del artículo original (p.~711), combinadas por la regla del producto ($5\times6\times6=180$); reglas resaltadas: Apéndice del artículo original (pp.~715 y~716). Código: \texttt{gen\_tabla\_180.py}; mismos datos en \texttt{resultados/reglas\_180.csv}.}\\
\endlastfoot
""" + "\n".join(body) + r"""
\end{longtable}
}
""")
open("articulo_ieee/tabla_180.tex", "w", encoding="utf-8").write(tex)
print("guardado articulo_ieee/tabla_180.tex y resultados/reglas_180.csv")
