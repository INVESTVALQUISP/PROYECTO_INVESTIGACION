"""
gen_cuadro_observaciones.py
================================================================================
Genera el «Cuadro de observaciones levantadas» (entregas/Cuadro_Observaciones_Levantadas.docx) de la revision del 07-11-2026,
desde la fuente unica codigo/observaciones_revision.py. Las ubicaciones (seccion, ecuacion, tabla, figura y pagina) se leen del
manuscrito compilado (articulo/main.aux y suplemento.aux) y las cifras de articulo/numeros.tex.
Requiere python-docx y haber compilado articulo/main.tex y articulo/suplemento.tex.
Uso:  python gen_cuadro_observaciones.py
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import os
import subprocess
from collections import Counter

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

import etiquetas_articulo as ea
from observaciones_revision import OBS, PROCEDE, EN_PARTE, NO_PROCEDE, NO_VERIFICABLE

OUT = "entregas/Cuadro_Observaciones_Levantadas.docx"
TITULOS = {
    "O1": "Asimetría de información: el actuado no tiene vista adelante",
    "O2": "Ecuaciones exactas de las funciones de pertenencia de FLC-O",
    "O3": "Tablas 6 y 7 sin n, semillas ni dispersión; ablación con una semilla",
    "O4": "Comparación contra una reconstrucción calibrada, sin etiqueta consistente",
    "O5": "Tabla 4 y Fig. 3(a) sin dispersión para todos los controladores",
    "O6": "«CONTROLDORES» en el pie de la Tabla 3",
    "O7": "Pie de la Fig. 3: banda solo de FLC-O",
    "O8": "Pie de la Tabla 6: réplicas y semillas",
    "O9": "Sec. IX: «reconstruido» en la primera mención del 27.8 %",
    "O10": "Resumen: calificar el 17.8 % con vista adelante",
    "O11": "Referencias [25] Vuong y [26] Shaheen",
    "O12": "CPU exacta y tiempo del «entrenamiento de 20 minutos»",
    "O13": "Tabla 5: significado del intervalo",
    "O14": "Tabla S2: unidades de los errores",
    "O15": "Justificación, Sec. 7: «venta» por «ventana»",
    "O16": "Novedad incremental: declarar el alcance empírico",
    "O17": "Notación: G, R, V, Q_G, Q_V, u, c_ijk",
    "O18": "Empate cerca de la saturación sin prueba de significancia",
    "O19": "Repositorio no verificable externamente",
    "O20": "Tabla 3: sin ecuaciones de pertenencia",
    "O21": "Arreglo propuesto con «FLC-O causal (1.7 %)»",
}
ESTADO = {PROCEDE: "Levantada", EN_PARTE: "Levantada en parte", NO_PROCEDE: "No procede (no se modificó)", NO_VERIFICABLE: "No verificable por el revisor"}
COLOR = {PROCEDE: "D6F0D6", EN_PARTE: "FFF2B8", NO_PROCEDE: "F9CCC7", NO_VERIFICABLE: "DCE0EB"}


def sombrear(celda, color):
    tcPr = celda._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tcPr.append(shd)


def escribir(celda, texto, negrita=False, tam=7.5, color=None):
    celda.text = ""
    p = celda.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run(texto)
    r.font.size = Pt(tam)
    r.bold = negrita
    if color:
        r.font.color.rgb = RGBColor.from_string(color)


def repetir_encabezado(fila):
    trPr = fila._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def fijar_anchos(tabla, anchos):
    lay = OxmlElement("w:tblLayout")
    lay.set(qn("w:type"), "fixed")
    tabla._tbl.tblPr.append(lay)
    for fila in tabla.rows:
        for i, c in enumerate(fila.cells):
            c.width = anchos[i]


def tabla(doc, cabecera, filas, anchos, colores=None):
    tb = doc.add_table(rows=1, cols=len(cabecera))
    tb.style = "Table Grid"
    tb.autofit = False
    tb.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, tx in enumerate(cabecera):
        escribir(tb.rows[0].cells[i], tx, True, 8, "FFFFFF")
        sombrear(tb.rows[0].cells[i], "1F3864")
    repetir_encabezado(tb.rows[0])
    for k, fila in enumerate(filas):
        c = tb.add_row().cells
        for i, tx in enumerate(fila):
            escribir(c[i], tx, negrita=(i in (0, 3)), tam=7.5)
        if colores:
            sombrear(c[3], colores[k])
    fijar_anchos(tb, anchos)
    return tb


def main():
    c = Counter(o[4] for o in OBS)
    doc = Document()
    sec = doc.sections[0]
    sec.orientation = WD_ORIENT.LANDSCAPE
    sec.page_width, sec.page_height = Cm(29.7), Cm(21.0)
    sec.left_margin = sec.right_margin = Cm(1.2)
    sec.top_margin = sec.bottom_margin = Cm(1.3)
    st = doc.styles["Normal"]
    st.font.name = "Calibri"
    st.font.size = Pt(9)
    for txt, tam, neg in (("Cuadro de observaciones levantadas", 16, True),
                          ("Revisión del 07-11-2026 del artículo «Mejora de un controlador de semáforos de lógica difusa para una intersección aislada: optimización del controlador de Pappis y Mamdani (1977)»", 10, False),
                          ("Raul Nolberto Quispe Saya y Kevin Luis Valero Ccacya — Escuela Profesional de Ingeniería Electrónica, UNSA", 9, False)):
        p = doc.add_paragraph()
        r = p.add_run(txt)
        r.bold = neg
        r.font.size = Pt(tam)
    p = doc.add_paragraph(
        f"Se extrajeron {len(OBS)} observaciones distintas del documento recibido: {c[PROCEDE]} proceden y se levantaron, {c[EN_PARTE]} proceden en parte (se levantó lo que tiene fondo), "
        f"{c[NO_PROCEDE]} no proceden y no se modificó nada por ellas, y {c[NO_VERIFICABLE]} no es verificable por el revisor. Las que no proceden están resaltadas en rojo; la razón de cada una "
        "está en el documento «Revisión de las observaciones». Las ubicaciones se leen del manuscrito compilado (articulo/main.pdf y articulo/suplemento.pdf).")
    for r in p.runs:
        r.font.size = Pt(9)
    p = doc.add_paragraph()
    r = p.add_run("Cambio de cifras que conviene conocer (observación O1)")
    r.bold = True
    r.font.size = Pt(10)
    cifras = [
        ("Ventaja de FLC-O sobre el actuado afinado (sin vista adelante), conjunto oficial", "17.8 %", ea.valor("RedActAfOf") + " % (se conserva, rotulada «sin vista adelante»)"),
        ("Ventaja de FLC-O sobre el actuado afinado CON la misma vista adelante, conjunto oficial", "no se había medido", ea.valor("RedActVOf") + f" % (significativa en {ea.valor('ParMejorActV')} de 16 pares, {ea.valor('ParPeorActV')} peor)"),
        ("Ventaja de FLC-O sobre el controlador de 1977 reconstruido (misma información)", ea.valor("RedFlc") + " %", ea.valor("RedFlc") + " % (no cambia)"),
        ("Ventaja del actuado con vista adelante sobre el controlador de 1977 reconstruido", "no se había medido", ea.valor("RedVistaPapOf") + " %"),
    ]
    tabla(doc, ["Cifra", "Antes de la revisión", "Después"], cifras, [Cm(14.0), Cm(4.5), Cm(8.0)])
    doc.add_paragraph()
    p = doc.add_paragraph()
    r = p.add_run("Cuadro de observaciones")
    r.bold = True
    r.font.size = Pt(10)
    filas, colores = [], []
    for oid, tipo, texto, ubic, ver, razon, accion, claves in OBS:
        donde = "; ".join(ea.ref(k) for k in claves) if claves else "—"
        if ver == NO_PROCEDE:
            que = "No se modificó el manuscrito. " + ea.resolver(razon, "txt")
        elif ver == NO_VERIFICABLE:
            que = ea.resolver(accion, "txt") + " (" + ea.resolver(razon, "txt") + ")"
        else:
            que = ea.resolver(accion, "txt")
        filas.append((f"{oid}\n{tipo}", TITULOS[oid] + f"\nUbicación citada: {ubic}", "", ESTADO[ver], que, donde))
        colores.append(COLOR[ver])
    filas = [(a, b, "", e, q, d) for (a, b, _, e, q, d) in filas]
    # 5 columnas visibles: N.º, observacion, estado, que se hizo, donde queda
    visibles = [(a, b, e, q, d) for (a, b, _, e, q, d) in filas]
    tb = tabla(doc, ["N.º", "Observación y ubicación citada", "Estado", "Qué se hizo", "Dónde queda"], visibles, [Cm(1.5), Cm(6.0), Cm(2.7), Cm(10.8), Cm(5.7)])
    for k, fila in enumerate(tb.rows[1:]):
        sombrear(fila.cells[2], colores[k])
    cp = doc.core_properties
    cp.author = "Raul Nolberto Quispe Saya; Kevin Luis Valero Ccacya"
    cp.last_modified_by = cp.author
    cp.title = "Cuadro de observaciones levantadas"
    cp.comments = ""
    os.makedirs("entregas", exist_ok=True)
    doc.save(OUT)
    print("guardado", OUT, dict(c))


if __name__ == "__main__":
    main()
