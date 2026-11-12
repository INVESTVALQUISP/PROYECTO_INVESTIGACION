"""
gen_revision_observaciones.py
================================================================================
Escribe en articulo/ las piezas del documento «Revision de las observaciones» (articulo/revision_observaciones.tex), a partir de
la fuente unica codigo/observaciones_revision.py y de las cifras y etiquetas del manuscrito compilado:
  revision_obs_tabla.tex      tabla de las 21 observaciones con su veredicto, la razon y la accion
  revision_obs_resumen.tex    macros con los conteos por veredicto
  revision_obs_noprocede.tex  lista de las observaciones que no tienen sentido o no son verificables (para destacarlas)
Requiere haber compilado articulo/main.tex y articulo/suplemento.tex (main.aux, suplemento.aux, numeros.tex).
Uso:  python gen_revision_observaciones.py
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
from collections import Counter

import etiquetas_articulo as ea
from observaciones_revision import OBS, PROCEDE, EN_PARTE, NO_PROCEDE, NO_VERIFICABLE, clase

OUT = "articulo"
COLOR = {PROCEDE: "okverde", EN_PARTE: "okamarillo", NO_PROCEDE: "okrojo", NO_VERIFICABLE: "okgris"}


def t(txt):
    """Texto plano -> LaTeX con las cifras como macros."""
    return ea.resolver(ea.tex_escape(txt), "tex")


def donde(claves):
    return "; ".join(ea.ref(c) for c in claves) if claves else "sin cambios"


def main():
    filas = []
    for oid, tipo, texto, ubic, ver, razon, accion, claves in OBS:
        cl = clase(oid, tipo)[0]
        etq = tipo if tipo != "Otra" else cl.lower() + ", clasif. propia"
        cel_obs = f"\\textbf{{{oid}}}\\ ({t(etq)}): {t(texto)}\\par\\smallskip{{\\itshape Ubicaci\\'on citada: {t(ubic)}}}"
        cel_ver = f"\\cellcolor{{{COLOR[ver]}}}\\textbf{{{t(ver)}}}"
        cel_acc = f"{t(accion)}\\par\\smallskip{{\\itshape Queda en: {t(donde(claves))}}}"
        filas.append(f"{cel_obs} & {cel_ver} & {t(razon)} & {cel_acc} \\\\\n\\midrule")
    cab = ("\\begingroup\\footnotesize\\setlength{\\tabcolsep}{4pt}\n\\begin{longtable}{@{}p{7.4cm}p{2.1cm}p{8.4cm}p{7.3cm}@{}}\n"
           "\\caption{Evaluaci\\'on de cada observaci\\'on recibida}\\label{tab:evaluacion}\\\\\n\\toprule\n"
           "Observaci\\'on recibida & Veredicto & Evaluaci\\'on (raz\\'on y evidencia) & Qu\\'e se hizo en el manuscrito \\\\\n\\midrule\n\\endfirsthead\n"
           "\\toprule\nObservaci\\'on recibida & Veredicto & Evaluaci\\'on (raz\\'on y evidencia) & Qu\\'e se hizo en el manuscrito \\\\\n\\midrule\n\\endhead\n")
    pie = "\\bottomrule\n\\end{longtable}\n\\endgroup\n"
    open(f"{OUT}/revision_obs_tabla.tex", "w", encoding="utf-8").write(cab + "\n".join(filas) + "\n" + pie)
    c = Counter(o[4] for o in OBS)
    M = ["% Generado por gen_revision_observaciones.py (no editar a mano)",
         f"\\newcommand{{\\RevN}}{{{len(OBS)}}}", f"\\newcommand{{\\RevNProcede}}{{{c[PROCEDE]}}}", f"\\newcommand{{\\RevNParte}}{{{c[EN_PARTE]}}}",
         f"\\newcommand{{\\RevNNo}}{{{c[NO_PROCEDE]}}}", f"\\newcommand{{\\RevNNoVer}}{{{c[NO_VERIFICABLE]}}}",
         f"\\newcommand{{\\RevNLevantadas}}{{{c[PROCEDE] + c[EN_PARTE]}}}"]
    open(f"{OUT}/revision_obs_resumen.tex", "w", encoding="utf-8").write("\n".join(M) + "\n")
    items = []
    for oid, tipo, texto, ubic, ver, razon, accion, claves in OBS:
        if ver in (NO_PROCEDE, NO_VERIFICABLE):
            corto = t(texto if len(texto) < 170 else texto[:167].rsplit(" ", 1)[0] + "…")
            items.append(f"\\item \\textbf{{{oid} ({t(ver)}).}} {corto} \\emph{{Por qu\\'e no tiene sentido:}} {t(razon)}")
    open(f"{OUT}/revision_obs_noprocede.tex", "w", encoding="utf-8").write("\\begin{itemize}\n" + "\n".join(items) + "\n\\end{itemize}\n")
    print("escritas las piezas de la revision:", dict(c))


if __name__ == "__main__":
    main()
