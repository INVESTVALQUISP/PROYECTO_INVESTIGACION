"""
gen_suplemento_etiquetas.py
================================================================================
El material suplementario (articulo_replica/suplemento.tex) incluye tablas que citan ecuaciones y
secciones del articulo principal. Este script lee articulo_replica/main.aux (generado al compilar
main.tex) y escribe articulo_replica/suplemento_etiquetas.tex con el numero de cada etiqueta, para
que el suplemento se compile solo, sin depender de main.aux.

Uso:  (1) compilar main.tex   (2) python codigo/gen_suplemento_etiquetas.py   (3) compilar suplemento.tex
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import re

aux = open("articulo_replica/main.aux", encoding="utf-8").read()
pat = re.compile(r"\\newlabel\{([^}]+)\}\{\{(.*?)\}\{\d+\}")
lines = ["% generado por codigo/gen_suplemento_etiquetas.py a partir de main.aux; no editar a mano"]
n = 0
for key, num in pat.findall(aux):
    num = re.sub(r"\\mbox\s*\{([^}]*)\}", r"\1", num)
    lines.append(f"\\expandafter\\def\\csname lbl@{key}\\endcsname{{{num}}}")
    n += 1
open("articulo_replica/suplemento_etiquetas.tex", "w", encoding="utf-8").write("\n".join(lines) + "\n")
print(f"{n} etiquetas escritas en articulo_replica/suplemento_etiquetas.tex")
