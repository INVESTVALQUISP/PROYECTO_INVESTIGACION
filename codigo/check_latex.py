"""Chequeo estatico del proyecto LaTeX (no hay compilador en el sandbox):
llaves balanceadas, \\cite vs .bib, \\ref vs \\label, figuras existentes, entornos begin/end."""
import re, sys, os
d = sys.argv[1] if len(sys.argv) > 1 else "articulo_replica"
import glob
tex = open(f"{d}/main.tex", encoding="utf-8").read()
for extra in sorted(glob.glob(f"{d}/tabla_*.tex")):
    tex += "\n" + open(extra, encoding="utf-8").read()
bib = open(f"{d}/referencias.bib", encoding="utf-8").read()
code = re.sub(r"(?<!\\)%.*", "", tex)
ok = True
def rep(name, good, detail=""):
    global ok; ok &= good; print(("[OK] " if good else "[FALLO] ") + name, detail)
rep("llaves balanceadas", code.count("{") - code.count("\\{") == code.count("}") - code.count("\\}"), f"({code.count('{')} / {code.count('}')})")
keys = set(re.findall(r"@\w+\{([^,]+),", bib))
cited = set(k.strip() for m in re.findall(r"\\cite\{([^}]*)\}", code) for k in m.split(","))
rep("todas las citas existen en el .bib", cited <= keys, str(sorted(cited - keys)))
print("     entradas .bib no citadas:", sorted(keys - cited))
labels = set(re.findall(r"\\label\{([^}]*)\}", code)); refs = set(re.findall(r"\\(?:ref|eqref)\{([^}]*)\}", code))
rep("todas las referencias cruzadas tienen label", refs <= labels, str(sorted(refs - labels)))
figs = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", code)
rep("figuras existentes", all(os.path.exists(f"{d}/figures/{f}") for f in figs), str([f for f in figs if not os.path.exists(f"{d}/figures/{f}")]))
b = re.findall(r"\\begin\{(\w+\*?)\}", code); e = re.findall(r"\\end\{(\w+\*?)\}", code)
rep("begin/end balanceados", sorted(b) == sorted(e))
rep("entradas bib con llaves balanceadas", bib.count("{") == bib.count("}"))
words = len(re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})?", " ", code).split())
print("palabras aprox. del cuerpo:", words)
sys.exit(0 if ok else 1)
