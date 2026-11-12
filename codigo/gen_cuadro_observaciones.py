"""
gen_cuadro_observaciones.py
================================================================================
Genera el «Cuadro de observaciones levantadas» (documento Word escrito desde cero, una observacion tras otra:
observacion y ubicacion citada, estado, que se hizo y donde queda; sin tablas) (entregas/Cuadro_Observaciones_Levantadas.docx) de la revision del 07-11-2026,
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


COLOR_TXT = {PROCEDE: "1E7B34", EN_PARTE: "8A6D00", NO_PROCEDE: "C0392B", NO_VERIFICABLE: "34495E"}


def parrafo(doc, texto="", negrita=False, tam=10.5, color=None, antes=0, despues=4, sangria=None):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before, pf.space_after = Pt(antes), Pt(despues)
    if sangria is not None:
        pf.left_indent = Cm(sangria)
    if texto:
        r = p.add_run(texto)
        r.bold = negrita
        r.font.size = Pt(tam)
        if color:
            r.font.color.rgb = RGBColor.from_string(color)
    return p


def linea(doc):
    """Separador horizontal (borde inferior de un parrafo vacio)."""
    p = parrafo(doc, despues=6)
    pPr = p._p.get_or_add_pPr()
    bdr = OxmlElement("w:pBdr")
    bot = OxmlElement("w:bottom")
    for k, v in (("w:val", "single"), ("w:sz", "6"), ("w:space", "1"), ("w:color", "1F3864")):
        bot.set(qn(k), v)
    bdr.append(bot)
    pPr.append(bdr)


def rotulo(doc, texto):
    parrafo(doc, texto, negrita=True, tam=10.5, color="1F3864", antes=6, despues=2)


def bloque(doc, n, titulo, cuerpo_obs, ubic, estado, color_estado, que, donde, etiqueta="OBSERVACIÓN"):
    h = doc.add_heading(f"{etiqueta} {n}", level=2)
    h.paragraph_format.space_before = Pt(14)
    linea(doc)
    rotulo(doc, "Observación y ubicación citada")
    parrafo(doc, titulo, negrita=True, sangria=0.5, despues=2)
    if cuerpo_obs:
        parrafo(doc, cuerpo_obs, sangria=0.5, despues=2)
    if ubic:
        parrafo(doc, "Ubicación citada por el revisor: " + ubic, sangria=0.5, tam=10, color="555555")
    p = parrafo(doc, antes=6, despues=2)
    r = p.add_run("ESTADO: ")
    r.bold = True
    r.font.size = Pt(10.5)
    r.font.color.rgb = RGBColor.from_string("1F3864")
    r = p.add_run(estado)
    r.bold = True
    r.font.size = Pt(10.5)
    r.font.color.rgb = RGBColor.from_string(color_estado)
    rotulo(doc, "Qué se hizo")
    parrafo(doc, que, sangria=0.5)
    rotulo(doc, "Dónde queda")
    parrafo(doc, donde, sangria=0.5)


def main():
    c = Counter(o[4] for o in OBS)
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.2)
    sec.top_margin = sec.bottom_margin = Cm(2.0)
    st = doc.styles["Normal"]
    st.font.name = "Calibri"
    st.font.size = Pt(10.5)
    for nombre in ("Heading 1", "Heading 2"):
        hs = doc.styles[nombre]
        hs.font.name = "Calibri"
        hs.font.color.rgb = RGBColor.from_string("1F3864")

    t = doc.add_heading("Cuadro de observaciones levantadas", level=1)
    t.paragraph_format.space_after = Pt(4)
    parrafo(doc, "Revisión del 07-11-2026 del artículo «Mejora de un controlador de semáforos de lógica difusa para una intersección "
                 "aislada: optimización del controlador de Pappis y Mamdani (1977)»", tam=11)
    parrafo(doc, "Raul Nolberto Quispe Saya y Kevin Luis Valero Ccacya — Escuela Profesional de Ingeniería Electrónica, "
                 "Universidad Nacional de San Agustín de Arequipa", tam=10, color="555555", despues=10)
    parrafo(doc, f"Se extrajeron {len(OBS)} observaciones distintas del documento recibido: {c[PROCEDE]} proceden y se levantaron, "
                 f"{c[EN_PARTE]} proceden en parte (se levantó lo que tiene fondo), {c[NO_PROCEDE]} no proceden y no se modificó nada por "
                 f"ellas, y {c[NO_VERIFICABLE]} no es verificable por el revisor. Cada observación se presenta abajo con la misma estructura: "
                 "la observación y su ubicación citada, su estado, qué se hizo y dónde queda en el manuscrito compilado (articulo/main.pdf y "
                 "articulo/suplemento.pdf). La razón detallada de las que no proceden está en el documento «Revisión de las observaciones».")
    rotulo(doc, "Cambio de cifras que conviene conocer (observación 1)")
    for txt in (
        f"Ventaja de FLC-O sobre el actuado afinado sin vista adelante (conjunto oficial): 17.8 % antes; {ea.valor('RedActAfOf')} % después "
        "(se conserva, rotulada «sin vista adelante»).",
        f"Ventaja de FLC-O sobre un actuado afinado con la misma vista adelante: no se había medido; ahora {ea.valor('RedActVOf')} % "
        f"(significativa en {ea.valor('ParMejorActV')} de 16 pares, peor en {ea.valor('ParPeorActV')}).",
        f"Ventaja de FLC-O sobre el controlador de 1977 reconstruido (misma información): {ea.valor('RedFlc')} %, no cambia.",
        f"Ventaja del actuado con vista adelante sobre el controlador de 1977 reconstruido: {ea.valor('RedVistaPapOf')} %.",
    ):
        p = doc.add_paragraph(txt, style="List Bullet")
        p.paragraph_format.space_after = Pt(2)

    for n, (oid, tipo, texto, ubic, ver, razon, accion, claves) in enumerate(OBS, start=1):
        donde = "; ".join(ea.ref(k) for k in claves) if claves else "—"
        if ver == NO_PROCEDE:
            que = "No se modificó el manuscrito. " + ea.resolver(razon, "txt")
            donde = "No aplica (no hay cambio en el manuscrito)." + (" Referencia: " + donde if claves else "")
        elif ver == NO_VERIFICABLE:
            que = ea.resolver(accion, "txt") + " (" + ea.resolver(razon, "txt") + ")"
        else:
            que = ea.resolver(accion, "txt")
        bloque(doc, n, f"{TITULOS[oid]} ({oid}, observación {tipo.lower()})", ea.resolver(texto, "txt"), ubic,
               ESTADO[ver], COLOR_TXT[ver], que, donde)

    # ---- pedidos del ingeniero (rondas anteriores) que no caben en el articulo y van en el material suplementario
    doc.add_page_break()
    doc.add_heading("Pedidos del ingeniero que van en el material suplementario", level=1)
    parrafo(doc, "Además de las observaciones de esta revisión, el material suplementario reúne lo que el ingeniero pidió en las "
                 "revisiones anteriores y no entra en el artículo por espacio.")
    R = ea.ref
    pedidos = [
        ("Las figuras de «la calle»",
         "Figura de la calle del simulador, con la explicación de cada elemento: autos por brazo, semáforos de tres luces, línea de parada, "
         "franja y etiqueta de cola, encabezado y pie.", f"{R('S:fig:s-calle')}; {R('S:sec:s-sim-b')}"),
        ("Las figuras que salen en el simulador, cada apartado en una figura aparte para que se puedan ver",
         "Cada apartado de la ventana en su propia figura, dibujado con el código de la ventana a mayor resolución, con FLC-O (entradas, salida u "
         "en dos segundos, fuerza de las 27 reglas, traza, botones, explicación y registro) y con el controlador de 1977 (reglas de la intervención, "
         "grados, disparos, traza, explicación, registro y editor de reglas). Cada figura tiene su texto explicativo.",
         f"{R('S:sec:s-sim')}; {R('S:fig:s-entradas')} a {R('S:fig:s-editor')}"),
        ("Esas figuras, aparte de la captura de la simulación",
         "La captura completa de la ventana (con FLC-O y con el de 1977) va aparte, con los nueve apartados rotulados de (a) a (i), y remite a la "
         "figura de cada uno; las tres pestañas de configuración tienen también su figura.",
         f"{R('S:fig:s-ventana-flco')}; {R('S:fig:s-ventana-pappis')}; {R('S:fig:s-pestana1')} a {R('S:fig:s-pestana3')}"),
        ("Las reglas en un cuadro vertical (tipo desglose de reglas)",
         "Las 25 reglas de Pappis y Mamdani en cuadro vertical, una caja por regla; las 27 de FLC-O desglosadas una por fila, en forma «si … entonces».",
         f"{R('S:tab:sreglas25')}; {R('S:tab:sreglas27')}"),
        ("Las 180 reglas enteras, con las 25 que usa el autor marcadas en verde y con check",
         "Lista literal de las 180 combinaciones T × A × Q, una por fila, con las usadas en verde y ✓ y las demás con ×, y en qué intervención se usa cada una.",
         R('S:tab:s180')),
        ("Las gráficas de las pertenencias, tal como estaban", "Sin cambios.", R('fig:fuzzificacion')),
        ("Diagrama del sistema de control",
         "Diagramas de bloques de los dos controladores, con la ecuación del artículo que implementa cada bloque.",
         f"{R('S:fig:s-bloques-pappis')}; {R('S:fig:s-bloques-flco')}"),
    ]
    for n, (pedido, que, donde) in enumerate(pedidos, start=1):
        bloque(doc, n, pedido, "", "", "Atendido", COLOR_TXT[PROCEDE], que, donde, etiqueta="PEDIDO")

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
