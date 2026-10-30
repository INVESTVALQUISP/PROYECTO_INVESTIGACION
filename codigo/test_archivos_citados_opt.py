"""
test_archivos_citados_opt.py
================================================================================
Reproducibilidad del paquete: todo script, archivo de resultados (JSON/CSV) y fuente LaTeX que el articulo
(main.tex), el material suplementario (suplemento.tex) y los README citan debe EXISTIR en el proyecto.
  1. cada \\texttt{archivo.py|json|csv|tex|md} citado se encuentra en codigo/, resultados/, articulo_replica/ o la raiz;
  2. cada \\input{...} y \\includegraphics{...} apunta a un archivo existente;
  3. cada tabla_*.tex del articulo se usa (no hay fuentes LaTeX obsoletas);
  4. cada script de codigo/ citado por el articulo se puede importar o compilar (py_compile).
Uso:  python test_archivos_citados_opt.py
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import glob
import os
import py_compile
import re
import sys

fails = 0


def check(name, ok, detail=""):
    global fails
    print(f"  [{'OK' if ok else 'FALLO'}] {name} {detail}")
    fails += 0 if ok else 1


ART = "articulo"
docs = {n: open(os.path.join(ART, n), encoding="utf-8").read() for n in ("main.tex", "suplemento.tex")}
BUSCAR = ["codigo", "resultados", ART, "docs", "."]


def existe(nombre):
    base = os.path.basename(nombre)
    for d in BUSCAR:
        if os.path.exists(os.path.join(d, nombre)) or os.path.exists(os.path.join(d, base)):
            return True
    return False


print("Archivos citados con \\texttt{...}")
citados = set()
tablas = {os.path.basename(f): open(f, encoding="utf-8").read() for f in glob.glob(os.path.join(ART, "tabla_*.tex"))}
for tex in list(docs.values()) + list(tablas.values()):
    for m in re.finditer(r"\\texttt\{([^}]*)\}", tex):
        t = m.group(1).replace("\\_", "_")
        for tok in re.findall(r"[\w./-]+\.(?:py|json|csv|tex|md|txt)\b", t):
            citados.add(tok)
faltan = sorted(c for c in citados if not existe(c))
check(f"{len(citados)} archivos citados en main.tex, suplemento.tex y tabla_*.tex", not faltan, f"faltan: {faltan}" if faltan else "")

print("\\input e \\includegraphics")
rotos = []
n_ent = 0
for nombre, tex in docs.items():
    for m in re.finditer(r"\\input\{([^}]+)\}", tex):
        n_ent += 1
        f = m.group(1)
        if not os.path.exists(os.path.join(ART, f if f.endswith(".tex") else f + ".tex")):
            rotos.append((nombre, f))
    for m in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", tex):
        n_ent += 1
        if not os.path.exists(os.path.join(ART, "figures", m.group(1))):
            rotos.append((nombre, m.group(1)))
check(f"{n_ent} entradas \\input/\\includegraphics resueltas", not rotos, f"rotas: {rotos}" if rotos else "")

print("Fuentes LaTeX obsoletas")
usadas = {os.path.basename(m.group(1)) + ".tex" if not m.group(1).endswith(".tex") else os.path.basename(m.group(1))
          for tex in docs.values() for m in re.finditer(r"\\input\{([^}]+)\}", tex)}
sueltas = sorted(os.path.basename(f) for f in glob.glob(os.path.join(ART, "tabla_*.tex")) if os.path.basename(f) not in usadas)
check("todas las tabla_*.tex se usan en main.tex o suplemento.tex", not sueltas, f"sin usar: {sueltas}" if sueltas else "")

print("Los scripts citados compilan")
malos = []
for c in sorted(citados):
    if c.endswith(".py"):
        for d in ("codigo", "."):
            ruta = os.path.join(d, os.path.basename(c))
            if os.path.exists(ruta):
                try:
                    py_compile.compile(ruta, doraise=True)
                except py_compile.PyCompileError as e:
                    malos.append((c, str(e)[:80]))
                break
check("py_compile de cada script .py citado", not malos, f"{malos}" if malos else "")

print("Archivos que el articulo exige expresamente")
for f in ("codigo/verificar_formulas.py", "resultados/verificacion_formulas.json", "codigo/gen_tabla_180.py", "resultados/reglas_180.csv",
          "codigo/ejecutar_pruebas.py", "resultados/entorno.json", "resultados/efecto_borde.json", "resultados/comparadores.json"):
    check(f, os.path.exists(f))

print()
if fails:
    print(f"FALLARON {fails} comprobaciones")
    sys.exit(1)
print("TODO OK")
