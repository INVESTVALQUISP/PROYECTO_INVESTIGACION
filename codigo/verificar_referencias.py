"""Comprueba cada DOI de articulo_ieee/referencias.bib contra la API pública de Crossref.

Para cada entrada con DOI compara título, primer autor, año, volumen y páginas con lo que
registra el editor. Requiere conexión a internet; usa solo la biblioteca estándar.

    python verificar_referencias.py                 # revisa todas las entradas con DOI
    python verificar_referencias.py Ali2021 Mei2024 # revisa solo esas claves

Un DOI que Crossref no encuentra (HTTP 404) o cuyo título no coincide debe corregirse o
eliminarse de referencias.bib; en estilo IEEE el DOI es opcional.
"""
import json
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BIB = Path(__file__).resolve().parent.parent / "articulo_ieee" / "referencias.bib"
DOI_RE = re.compile(r"(10\.\d{4,9}/[^\s{}]+)")


def leer_bib(ruta):
    """Devuelve {clave: {campo: valor}} con un analizador mínimo de BibTeX."""
    texto = Path(ruta).read_text(encoding="utf-8")
    entradas = {}
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,(.*?)\n\}", texto, re.S):
        campos = {}
        for c in re.finditer(r"(\w+)\s*=\s*\{((?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*)\}", m.group(3)):
            campos[c.group(1).lower()] = c.group(2)
        entradas[m.group(2)] = campos
    return entradas


def doi_de(campos):
    for clave in ("doi", "note"):
        m = DOI_RE.search(campos.get(clave, ""))
        if m:
            return m.group(1)
    return None


def normalizar(s):
    s = re.sub(r"\\[`'^\"~=.]\{?\\?(\w)\}?", r"\1", s)  # acentos LaTeX
    s = re.sub(r"\\[a-zA-Z]+\s*", " ", s).replace("{", "").replace("}", "")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^a-z0-9 ]+", " ", s).split()


def similitud(a, b):
    ta, tb = set(normalizar(a)), set(normalizar(b))
    return len(ta & tb) / max(1, len(ta | tb))


def consultar(doi):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    req = urllib.request.Request(url, headers={"User-Agent": "verificar_referencias/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["message"]


def comparar(campos, msg):
    """Lista de (campo, valor en el .bib, valor en Crossref, coincide)."""
    titulo = " ".join(msg.get("title", [""]))
    autores = msg.get("author", [])
    apellido = normalizar(autores[0].get("family", ""))[:1] if autores else []
    primer_autor_bib = normalizar(campos.get("author", "").split(" and ")[0])[-1:]
    fecha = (msg.get("issued") or msg.get("published") or {}).get("date-parts", [[None]])[0][0]
    filas = [
        ("título", campos.get("title", ""), titulo, similitud(campos.get("title", ""), titulo) >= 0.7),
        ("primer autor", " ".join(primer_autor_bib), " ".join(apellido), primer_autor_bib == apellido),
    ]
    if "year" in campos:
        filas.append(("año", campos["year"], str(fecha), campos["year"].strip() == str(fecha)))
    if "volume" in campos and msg.get("volume"):
        filas.append(("volumen", campos["volume"], msg["volume"], campos["volume"].strip() == msg["volume"]))
    if "pages" in campos and msg.get("page"):
        p_bib = re.sub(r"[-–—]+", "-", campos["pages"]).strip()
        p_cr = re.sub(r"[-–—]+", "-", msg["page"]).strip()
        filas.append(("páginas", p_bib, p_cr, p_bib == p_cr))
    return filas


def main(claves):
    entradas = leer_bib(BIB)
    con_doi = {k: doi_de(v) for k, v in entradas.items() if doi_de(v)}
    if claves:
        con_doi = {k: v for k, v in con_doi.items() if k in claves}
    print(f"{len(entradas)} entradas en el .bib; {len(con_doi)} con DOI a verificar\n")
    problemas = 0
    for clave, doi in con_doi.items():
        try:
            msg = consultar(doi)
        except urllib.error.HTTPError as e:
            estado = "NO EXISTE en Crossref" if e.code == 404 else f"error HTTP {e.code}"
            print(f"[REVISAR] {clave}  {doi}  -> {estado}")
            problemas += 1
            continue
        except Exception as e:  # sin red, DNS, tiempo de espera
            print(f"[SIN RED] {clave}  {doi}  -> {type(e).__name__}: {e}")
            problemas += 1
            continue
        filas = comparar(entradas[clave], msg)
        mal = [f for f in filas if not f[3]]
        print(f"[{'OK' if not mal else 'REVISAR'}] {clave}  {doi}")
        for campo, bib, cr, ok in filas:
            if not ok or "-v" in sys.argv:
                print(f"      {campo}: .bib = {bib!r}  |  Crossref = {cr!r}")
        problemas += bool(mal)
    print(f"\n{len(con_doi) - problemas} de {len(con_doi)} verificados sin diferencias")
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main([a for a in sys.argv[1:] if not a.startswith("-")]))
