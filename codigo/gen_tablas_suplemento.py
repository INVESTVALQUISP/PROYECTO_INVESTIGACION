"""
gen_tablas_suplemento.py
================================================================================
Tablas de reglas del material suplementario del articulo de la mejora (articulo/suplemento.tex):

  articulo/tabla_s_reglas25.tex   desglose vertical de las 25 reglas de Pappis y Mamdani (una columna por
                                  intervencion, una caja por regla), tal como las da el Apendice del original
  articulo/tabla_s_reglas27.tex   desglose de las 27 reglas de FLC-O, una por fila: SI G es ... Y R es ... Y V es ...
                                  ENTONCES c, con lo que la regla empuja a hacer (cambiar de fase o seguir en verde)
La lista de las 180 reglas T x A x Q (articulo/tabla_s_180.tex) la escribe gen_tabla_180.py.

Uso:  python codigo/gen_tablas_suplemento.py
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import json

import fuzzy_logic as fl

TXT = {"veryshort": "very short", "short": "short", "medium": "medium", "long": "long", "verylong": "very long",
       "none": "none", "afew": "a few", "few": "few", "many": "many", "toomany": "too many",
       "verysmall": "very small", "small": "small", "smallplus": "small plus"}


def caja(k, n):
    T, A, Q, E = fl.RULES[k][n]
    q = "any" if Q == "any" else f"lt({TXT[Q]})"
    return (r"\begin{tabular}[t]{@{}l@{}}\textbf{R" + str(n + 1) + r"} \\ \textbf{SI} $T$ = " + TXT[T]
            + r" \\ \textbf{Y} $A$ = mt(" + TXT[A] + r") \\ \textbf{Y} $Q$ = " + q
            + r" \\ \textbf{ENTONCES} $E$ = " + TXT[E] + r"\end{tabular}")


filas = [" & ".join(caja(k, n) for k in fl.INTERVENTIONS) + r" \\" + ("\n\\midrule" if n < 4 else "") for n in range(5)]
t25 = (r"""\begin{table}[H]
\caption{Desglose de las 25 reglas de Pappis y Mamdani (1977), la línea base que se mejora: cada columna es una intervención (segundo de verde en que el controlador decide) y cada caja una regla, con sus condiciones sobre el tiempo $T$, los arribos $A$ (operador «más que», mt) y la cola $Q$ (operador «menos que», lt), y su conclusión, la extensión $E=T$. R5 es la que más extiende el verde; R1 ($Q=$ any) es la que lo corta cuando no llegan autos.}
\label{tab:sreglas25}
\centering
\scriptsize
\setlength{\tabcolsep}{6pt}
\renewcommand{\arraystretch}{1.05}
\begin{tabular}{@{}ccccc@{}}
\toprule
7\,s & 17\,s & 27\,s & 37\,s & 47\,s \\
\midrule
""" + "\n".join(filas) + r"""
\bottomrule
\end{tabular}
\fuente{Apéndice del artículo original (pp.~715 y~716), transcrito sin cambios; las mismas reglas están en \texttt{codigo/fuzzy\_logic.py} (\texttt{RULES}).}
\end{table}
""")
open("articulo/tabla_s_reglas25.tex", "w", encoding="utf-8").write(t25)
print("guardado articulo/tabla_s_reglas25.tex")

# ---------------- las 27 reglas de FLC-O, una por fila ----------------
fin = json.load(open("resultados/opt/modelos_finales.json"))
nombre = fin["flc"]
theta = json.load(open(f"resultados/opt/{nombre}.json"))["theta"]
c = theta[9:36]
NOM = ("bajo", "medio", "alto")
filas = []
for i in range(27):
    g, r, v = NOM[i // 9], NOM[(i // 3) % 3], NOM[i % 3]
    ci = c[i]
    efecto = r"\textcolor{red!70!black}{cambiar de fase}" if ci > 0 else r"\textcolor{blue!70!black}{seguir en verde}"
    num = f"{ci:+.2f}".replace("-", "$-$")
    filas.append(f"{i + 1} & {g} & {r} & {v} & {num} & {efecto} \\\\" + ("\n\\midrule" if i % 9 == 8 and i < 26 else ""))
n_pos = sum(x > 0 for x in c)
t27 = (r"""\begin{table}[H]
\caption{Desglose de las 27 reglas de FLC-O, una por fila: «\textbf{SI} $G$ es $\mathcal{G}_i$ \textbf{Y} $R$ es $\mathcal{R}_j$ \textbf{Y} $V$ es $\mathcal{V}_k$ \textbf{ENTONCES} $c_{ijk}$». $G$: demanda en el brazo con verde; $R$: presión en el brazo en rojo; $V$: segundos de verde transcurridos. Un consecuente positivo empuja a cambiar de fase y uno negativo a seguir en verde; la decisión de cada segundo es el promedio de los consecuentes ponderado por la fuerza de cada regla (Ec.~(8) del artículo). """
       + f"{n_pos} de las 27 reglas empujan a cambiar." + r"""}
\label{tab:sreglas27}
\centering
\small
\setlength{\tabcolsep}{8pt}
\renewcommand{\arraystretch}{1.02}
\begin{tabular}{@{}rlllrl@{}}
\toprule
N.º & \textbf{SI} $G$ es & \textbf{Y} $R$ es & \textbf{Y} $V$ es & \textbf{ENTONCES} $c$ & la regla empuja a \\
\midrule
""" + "\n".join(filas) + r"""
\bottomrule
\end{tabular}
\fuente{modelo entrenado """ + nombre.replace("_", r"\_") + r""" (\texttt{resultados/opt/""" + nombre.replace("_", r"\_") + r""".json}); son los mismos consecuentes de la Tabla~2 del artículo, ordenados como regla por regla.}
\end{table}
""")
open("articulo/tabla_s_reglas27.tex", "w", encoding="utf-8").write(t27)
print("guardado articulo/tabla_s_reglas27.tex:", n_pos, "reglas con c > 0")
