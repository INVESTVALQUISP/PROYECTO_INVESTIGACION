"""
etiquetas_articulo.py
================================================================================
Lee las etiquetas del manuscrito (articulo/main.aux) y del suplemento (articulo/suplemento.aux) y las cifras de articulo/numeros.tex,
para que los documentos de revision citen la seccion, tabla o figura y la pagina TAL COMO QUEDARON en el PDF compilado.
"""
import re

import _raiz  # noqa: F401  (cwd = carpeta del proyecto)


def leer_etiquetas(ruta):
    L = {}
    for m in re.finditer(r"\\newlabel\{([^}]+)\}\{\{(?:\\mbox\s*\{)?([^}]+?)\}?\}\{(\d+)\}", open(ruta, encoding="utf-8").read()):
        L[m.group(1)] = (m.group(2), int(m.group(3)))
    return L


def leer_numeros(ruta="articulo/numeros.tex"):
    return {m.group(1): m.group(2) for m in re.finditer(r"\\newcommand\{\\(\w+)\}\{([^}]*)\}", open(ruta, encoding="utf-8").read())}


L = leer_etiquetas("articulo/main.aux")
LS = leer_etiquetas("articulo/suplemento.aux")
N = leer_numeros()
# la seccion de disponibilidad es una seccion sin numero: su etiqueta hereda el de la anterior, asi que se cita por nombre
SIN_NUMERO = {"sec:disp": "Disponibilidad del código"}


def ref(clave):
    """'Sec. IV-B (p. 3)', 'Ec. (5) (p. 4)', 'Tabla 4 (p. 8)', 'Tabla S2 del suplemento (p. 2)'."""
    if clave.startswith("S:"):
        c = clave[2:]
        num, pag = LS[c]
        return (f"Tabla {num} del suplemento (p. {pag})" if c.startswith("tab:") else f"Sec. {num} del suplemento (p. {pag})")
    num, pag = L[clave]
    if clave in SIN_NUMERO:
        return f"«{SIN_NUMERO[clave]}» (p. {pag})"
    if clave.startswith("sec:"):
        return f"Sec. {num} (p. {pag})"
    if clave.startswith("eq:"):
        return f"Ec. ({num}) (p. {pag})"
    if clave.startswith("tab:"):
        return f"Tabla {num} (p. {pag})"
    return f"Fig. {num} (p. {pag})"


def valor(nombre):
    """Cifra de numeros.tex en texto plano (menos tipografico, '<0.001')."""
    v = N[nombre]
    return v.replace("$-$", "−").replace("$<\\!0.001$", "<0.001")


def resolver(txt, formato):
    """Sustituye @@Macro@@ por la cifra (formato 'txt') o por la macro de LaTeX (formato 'tex')."""
    if formato == "tex":
        return re.sub(r"@@(\w+)@@", lambda m: "\\" + m.group(1) + "{}", txt)
    return re.sub(r"@@(\w+)@@", lambda m: valor(m.group(1)), txt)


def tex_escape(txt):
    """Escapa lo necesario de un texto plano para LaTeX, respetando las marcas @@Macro@@ y el signo menos tipografico."""
    partes = re.split(r"(@@\w+@@)", txt)
    out = []
    for p in partes:
        if p.startswith("@@"):
            out.append(p)
            continue
        p = p.replace("\\", "\\textbackslash{}").replace("%", "\\%").replace("_", "\\_").replace("&", "\\&").replace("#", "\\#")
        p = p.replace("−", "$-$").replace("→", "$\\to$").replace("≥", "$\\ge$").replace("≤", "$\\le$")
        out.append(p)
    return "".join(out)
