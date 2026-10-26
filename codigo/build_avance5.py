"""
build_avance5.py
================================================================================
Genera 'avance5_validacion_replica.pdf': quinto avance (espanol). Confirma la
VALIDACION de la replica frente al paper ORIGINAL (version en ingles), con
enfasis en las CURVAS DE FUZZIFICACION.

Lee: resultados/resultados_oficiales.json, resultados/fidelity_audit.json, paper_data.py, fuzzy_logic.py
y las figuras de figures/. Ejecuta test_paper_tables.py para contar comprobaciones.

Uso:  python build_avance5.py
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import json
import re
import os
import subprocess
_COD = os.path.dirname(os.path.abspath(__file__))
import sys

import numpy as np
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Frame, Image, PageBreak, PageTemplate,
                                Paragraph, Preformatted, Spacer, Table, TableStyle)

import fuzzy_logic as fl
import paper_data as pdta
import traffic_model as tm

OUT = ("docs" if os.path.isdir("docs") else "entregas") + "/avance5_validacion_replica.pdf"
res = json.load(open("resultados/resultados_oficiales.json"))
aud = json.load(open("resultados/fidelity_audit.json"))
CAL, LIT = res["table_VIII"]["calibrada"], res["table_VIII"]["literal"]
T1 = res["table_I"]

# las graficas de las curvas de fuzzificacion se regeneran SIEMPRE antes de armar el PDF
for gen in ("gen_fig_fuzzificacion.py", "gen_fig_lt_explicacion.py", "gen_fig_validacion.py", "gen_fig_correcciones.py"):
    subprocess.run([sys.executable, os.path.join(_COD, gen)], check=True, capture_output=True)

# comprobaciones automaticas (se recalculan al construir el PDF)
tp = subprocess.run([sys.executable, os.path.join(_COD, "test_paper_tables.py")], capture_output=True, text=True)
N_OK, N_FAIL = tp.stdout.count("[OK]"), tp.stdout.count("[FALLO]")
te = subprocess.run([sys.executable, os.path.join(_COD, "test_sim_engine.py")], capture_output=True, text=True)
ENG = re.search(r"(\d+)/(\d+) equivalencias", te.stdout).groups()


# ---------------------------------------------------------------------------
def png_size(path):
    with open(path, "rb") as f:
        d = f.read(33)
    return int.from_bytes(d[16:20], "big"), int.from_bytes(d[20:24], "big")


ss = getSampleStyleSheet()
NAVY, BLUE = colors.HexColor("#1a2b4a"), colors.HexColor("#274270")
ST = {
    "title": ParagraphStyle("t", parent=ss["Title"], fontSize=20, leading=25, textColor=NAVY, alignment=TA_CENTER),
    "sub": ParagraphStyle("st", parent=ss["Normal"], fontSize=10.5, leading=14, textColor=colors.HexColor("#33415c"), alignment=TA_CENTER),
    "h1": ParagraphStyle("h1", parent=ss["Heading1"], fontSize=14, leading=18, textColor=NAVY, spaceBefore=12, spaceAfter=6),
    "h2": ParagraphStyle("h2", parent=ss["Heading2"], fontSize=11.5, leading=15, textColor=BLUE, spaceBefore=9, spaceAfter=4),
    "body": ParagraphStyle("b", parent=ss["Normal"], fontSize=9.5, leading=14, alignment=TA_JUSTIFY, spaceAfter=6),
    "cap": ParagraphStyle("cap", parent=ss["Normal"], fontSize=8, leading=11, alignment=TA_CENTER,
                          textColor=colors.HexColor("#555"), spaceBefore=3, spaceAfter=10),
    "code": ParagraphStyle("code", fontName="Courier", fontSize=7, leading=9),
    "mono": ParagraphStyle("mono", parent=ss["Normal"], fontName="Courier", fontSize=8.5, leading=12,
                           backColor=colors.HexColor("#f2f4f8"), borderPadding=6, leftIndent=6, rightIndent=6, spaceAfter=8),
    "note": ParagraphStyle("note", parent=ss["Normal"], fontSize=9, leading=13, alignment=TA_JUSTIFY,
                           backColor=colors.HexColor("#fff6dd"), borderPadding=6, leftIndent=6, rightIndent=6,
                           borderColor=colors.HexColor("#e3c46a"), borderWidth=0.6, spaceBefore=4, spaceAfter=10),
}
ST["bullet"] = ParagraphStyle("bl", parent=ST["body"], leftIndent=12, bulletIndent=4)


def P(text, style="body"):
    return Paragraph(text, ST[style])


def bullets(items):
    return [Paragraph(t, ST["bullet"], bulletText="•") for t in items]


def fig(path, caption, width=150 * mm):
    w, h = png_size(path)
    img = Image(path, width=width, height=width * h / w)
    img.hAlign = "CENTER"
    return [img, P(caption, "cap")]


def code(text, title=None):
    out = [P(title, "h2")] if title else []
    return out + [Preformatted(text, ST["code"]), Spacer(1, 6)]


def table(header, rows, widths, font=7.5, hl=()):
    cell = ParagraphStyle("cell", parent=ss["Normal"], fontSize=font, leading=font + 2, alignment=0)

    def wrap(v):
        return Paragraph(v, cell) if isinstance(v, str) and len(v) > 22 else v
    rows = [[wrap(v) for v in r] for r in rows]
    t = Table([header] + rows, colWidths=widths, repeatRows=1)
    style = [("FONT", (0, 0), (-1, 0), "Helvetica-Bold", font), ("FONT", (0, 1), (-1, -1), "Helvetica", font),
             ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
             ("ALIGN", (1, 0), (-1, -1), "CENTER"), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c0cc")),
             ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef1f6")]),
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 2),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]
    for r in hl:
        style.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#fdeecd")))
    t.setStyle(TableStyle(style))
    return t


def on_page(c, doc):
    c.saveState()
    c.setFont("Helvetica", 7.5)
    c.setFillColor(colors.HexColor("#7a8699"))
    if doc.page > 1:
        c.drawString(18 * mm, A4[1] - 12 * mm, "Avance 5 — Validación de la réplica frente al paper original (Pappis & Mamdani, 1977)")
        c.setStrokeColor(colors.HexColor("#c9d2e0"))
        c.line(18 * mm, A4[1] - 13.5 * mm, A4[0] - 18 * mm, A4[1] - 13.5 * mm)
    c.drawRightString(A4[0] - 18 * mm, 12 * mm, f"Página {doc.page}")
    c.restoreState()


doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm,
                      bottomMargin=16 * mm, title="Avance 5: validación de la réplica de Pappis & Mamdani (1977)")
doc.addPageTemplates([PageTemplate(id="all", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height)],
                                   onPage=on_page)])
S = []
W = doc.width

# ===========================================================================
# Encabezado y resumen
# ===========================================================================
S += [P("Avance 5 — Validación de la réplica frente al paper original", "title"),
      P("Pappis &amp; Mamdani (1977), <i>A Fuzzy Logic Controller for a Traffic Junction</i>, IEEE Trans. SMC-7(10), 707–716.<br/>"
        "Referencia única: la versión <b>original en inglés</b>, leída sobre la imagen de cada página · 14 de octubre de 2026", "sub"),
      Spacer(1, 8)]

S.append(P("0. Resumen de la validación", "h1"))
S.append(P(
    "Este avance confirma, elemento por elemento, que la réplica en Python coincide con lo que publica el paper original, "
    "y señala con honestidad lo que <b>no</b> se puede confirmar. Las "
    "<b>curvas de fuzzificación</b> ocupan la Sección 2 y se validan punto por punto contra las tablas impresas."))
e_sim = np.mean([abs(r["sim"] - pdta.TABLE_I[(r["ns"], r["ew"])][0]) / pdta.TABLE_I[(r["ns"], r["ew"])][0] for r in T1]) * 100
e_for = np.mean([abs(r["formula"] - pdta.TABLE_I[(r["ns"], r["ew"])][1]) / pdta.TABLE_I[(r["ns"], r["ew"])][1] for r in T1]) * 100
errs = [abs(r["fuzzy"] - pdta.TABLE_VIII[(r["ns"], r["ew"])][1]) / pdta.TABLE_VIII[(r["ns"], r["ew"])][1] * 100 for r in CAL]
wins = sum(r["fuzzy"] < r["fixed"] for r in CAL)
lit_wins = sum(r["fuzzy"] < r["fixed"] for r in LIT)
hdr = ["Elemento del paper", "Cómo se verificó", "Resultado"]
rows = [
    ["Tablas II, III, IV (conjuntos base)", "Valor a valor contra la imagen (paper_data.py)", "exacto"],
    ["Tablas V y VI (operadores mt y lt)", "Valor a valor; curvas con marcadores del paper", "exacto (diferencia máx. 0.000)"],
    ["Apéndice: 25 reglas (5 × 5)", "Transcritas de la imagen de las págs. 715–716", "exacto (se corrigió la versión previa)"],
    ["Ejemplo de las págs. 7–8 (Tabla VII)", "Cada regla y la fila «Fuzzy Algorithm»", "exacto; e* = 10 s"],
    ["Intervenciones 7, 17, 27, 37, 47 s; verde ≤ 57 s", "Prueba de estructura temporal", "exacto"],
    ["Tabla I (modelo, ciclo fijo de Webster)", "20 réplicas × 7200 s; fórmula de Webster", f"error medio {e_sim:.1f} % (sim.) / {e_for:.1f} % (fórmula)"],
    ["Tabla VIII (difuso vs. ciclo fijo), lectura calibrada", "20 réplicas × 7200 s", f"{wins}/16 celdas mejoran; error medio {np.mean(errs):.1f} %, máx. {np.max(errs):.1f} %"],
    ["Tabla VIII, lectura literal", "ídem", f"solo {lit_wins}/16 celdas mejoran; inestable en flujos altos"],
]
S.append(table(hdr, rows, [58 * mm, 62 * mm, 54 * mm], font=7.8, hl=(7, 8)))
S.append(P(f"Tabla 0.1 — Resumen de la validación. Comprobaciones automáticas: {N_OK} correctas y {N_FAIL} fallidas "
           f"(<font face='Courier'>test_paper_tables.py</font>); equivalencia del motor del simulador: {ENG[0]}/{ENG[1]}.", "cap"))
S.append(P(
    "<b>Conclusión.</b> Todo lo que el paper <i>especifica</i> (conjuntos, operadores, reglas, ejemplo, tiempos, modelo y Tabla I) "
    "queda reproducido exactamente o dentro de la variabilidad estadística. Lo que el paper <i>no especifica</i> es cómo su "
    "programa medía las entradas A y Q en la simulación; con la lectura literal la Tabla VIII no se reproduce, y con la lectura "
    "calibrada sí (Sección 6). Esa lectura es una <b>inferencia por falta de datos</b> en el paper, no una cita (Secciones 6 y 7).", "note"))

S += fig("figures/fig_fuzzificacion.png",
         "Figura 0.1 — Curvas de fuzzificación del controlador (Tablas II, V, IV y VI). Se explican y validan en la Sección 2.", width=W * 0.92)

# ===========================================================================
# 1. Método de validación
# ===========================================================================
S.append(P("1. Fuente de verdad y método de validación", "h1"))
S += bullets([
    "<b>Fuente única:</b> el PDF original en inglés.",
    "<b>Se lee la imagen, no el texto extraído.</b> El texto extraído del PDF mezcla las dos columnas de la pág. 716 y desordena "
    "las reglas del Apéndice; la versión anterior del código heredó ese error. Todos los valores de <font face='Courier'>paper_data.py</font> "
    "se transcribieron de las imágenes de las tablas.",
    "<b>Pruebas automáticas</b> (<font face='Courier'>test_paper_tables.py</font>): comparan el código con lo impreso para las Tablas II–VII, "
    "las 25 reglas, el ejemplo trabajado y la estructura temporal.",
    "<b>Protocolo estadístico:</b> 20 réplicas × 7200 s por combinación de caudal, 16 combinaciones, semilla base 0 "
    "(el difuso usa base + 100000). El paper solo dice «many runs» y 7200 s por corrida.",
])
S.append(P("1.1 Todas las correcciones hechas", "h2"))
S.append(P("Cada fila indica qué se encontró al contrastar el código con el paper original, cómo estaba y cómo quedó. "
           "Las dos primeras afectan directamente a las curvas de fuzzificación y se muestran en la Figura 1.1."))
hdr = ["#", "Elemento (paper)", "Antes (incorrecto)", "Ahora (verificado)", "Efecto"]
rows = [
    ["1", "Operador mt (pág. 4, Tabla V)", "Para a &lt; x0 devolvía μ<sub>A</sub>(a), p. ej. mt(many)(3) = 0.5.", "0 para a &lt; x0; coincide con las 60 celdas de la Tabla V.", "Las reglas daban confianza a pocos arribos."],
    ["2", "Conjunto «verylong» de colas (Tabla IV)", "Pico en q = 29.", "Pico en q = 28 (picos 8, 12, …, 28); también corrige lt(verylong), Tabla VI.", "Reglas de 37 y 47 s con umbrales desplazados."],
    ["3", "Reglas de las intervenciones de 27, 37 y 47 s (Apéndice, pág. 716)", "24 reglas (5+5+7+5+2) copiadas del texto OCR, que mezcla las dos columnas.", "25 reglas, 5 por intervención, leídas de la imagen del original.", "Cambia el comportamiento en verdes largos."],
    ["4", "Momento de intervención (pág. 3)", "Decidía tras 8 s de verde; verde máximo 58 s.", "Decide tras 7 s; verde = 7 + Σe* ≤ 57 s.", "Verde mínimo y máximo como en el paper."],
    ["5", "Procesamiento del segundo final del verde difuso", "Se reprocesaba y se contaban dos veces sus arribos (6–12 % más vehículos).", "Cada segundo se procesa una sola vez.", "Difuso y ciclo fijo comparables."],
    ["6", "Verdes del ciclo fijo (ecs. 8–10)", "Verdes fraccionarios (p. ej. 8.1 s).", "Segundos enteros (el modelo avanza en pasos de 1 s).", "Tabla I más cercana."],
    ["7", "Tabla I, columna «Formula» (pág. 3)", "Se imprimía una fórmula incorrecta.", "Fórmula de Webster completa ponderada por flujo.", "Error medio 0.8 %."],
    ["8", "Entradas A y Q (ejemplo de las págs. 7–8)", "Una sola lectura, sin documentar.", "Dos lecturas explícitas (literal y calibrada) y auditoría de 8 variantes.", "Se sabe qué se infiere y qué no."],
    ["9", "Material derivado", "PDFs, re-afinado y baselines calculados con las reglas erróneas.", "Archivados en _extras_pospuestos/; simuladores y pruebas actualizados.", "Sin cifras obsoletas en circulación."],
]
S.append(table(hdr, rows, [7 * mm, 38 * mm, 48 * mm, 48 * mm, 33 * mm], font=7.2))
S.append(P("Tabla 1.1 — Correcciones respecto de la versión anterior. Las cifras de los avances 1–4 quedan <b>superadas</b> por este avance.", "cap"))
S += fig("figures/fig_correcciones_fuzzificacion.png",
         "Figura 1.1 — Curvas antes (rojo, discontinuo) y después (azul) de las correcciones 1 y 2, frente a los valores impresos en el paper (×).", width=W)

# ===========================================================================
# 2. CURVAS DE FUZZIFICACION
# ===========================================================================
S.append(PageBreak())
S.append(P("2. Curvas de fuzzificación", "h1"))
S.append(P(
    "La <b>fuzzificación</b> traduce cada medida numérica (<i>crisp</i>) a <b>grados de pertenencia</b> entre 0 y 1 de términos "
    "lingüísticos. El controlador no razona con «4 vehículos» sino con «tiene grado 0.9 de <i>a few</i> y 0.5 de <i>medium</i>». "
    "Hay tres variables de entrada y una de salida:"))
hdr = ["Variable", "Símbolo", "Universo (discreto)", "Qué mide"]
rows = [
    ["Tiempo / extensión", "T (salida E)", "t = 1 … 10 s", "Extensión candidata del verde; E usa los mismos conjuntos que T"],
    ["Arribos", "A", "a = 1 … 10 veh", "Vehículos que cruzarán el punto crítico en los próximos t s (pads de detección)"],
    ["Cola", "Q", "q = 4 … 32 veh", "Vehículos en cola en el brazo en rojo"],
]
S.append(table(hdr, rows, [38 * mm, 24 * mm, 32 * mm, 80 * mm], font=8))
S.append(P("Tabla 2.1 — Variables difusas. Todos los universos son discretos: por eso las curvas se grafican con marcadores.", "cap"))

S.append(P("2.1 Conjuntos base (Tablas II, III y IV del paper)", "h2"))
hdr = ["Conjunto"] + [str(t) for t in range(1, 11)]
S.append(table(hdr, [[n] + [f"{v:g}" if v else "" for v in fl.MU_TIME[n]] for n in ("veryshort", "short", "medium", "long", "verylong")],
               [26 * mm] + [14.8 * mm] * 10, font=8))
S.append(P("Tabla 2.2 — Tiempo / extensión (Tabla II), t en segundos. Triángulos de pico 1, 3, 5, 7 y 9 s (verylong vale 1 en 9 y 10 s).", "cap"))
S.append(table(hdr, [[n] + [f"{v:g}" if v else "" for v in fl.MU_ARR[n]] for n in ("none", "afew", "few", "medium", "many", "toomany")],
               [26 * mm] + [14.8 * mm] * 10, font=8))
S.append(P("Tabla 2.3 — Arribos (Tabla III), a en vehículos. «none» tiene su máximo (0.5) en a = 1; «toomany» en a = 5.", "cap"))
qs = list(range(4, 33, 2))
hdr = ["Conjunto"] + [str(q) for q in qs]
S.append(table(hdr, [[n] + [f"{fl.MU_QUEUE[n][q - 4]:g}" if fl.MU_QUEUE[n][q - 4] else "" for q in qs]
                     for n in ("verysmall", "small", "smallplus", "medium", "long", "verylong")],
               [24 * mm] + [10.0 * mm] * 15, font=7.5))
S.append(P("Tabla 2.4 — Colas (Tabla IV), q en vehículos (se muestran los q pares; el código tiene los 29 valores). "
           "Seis «lomas» de 7 puntos con picos en q = 8, 12, 16, 20, 24 y 28.", "cap"))

S.append(P("2.2 Operadores «more than» (mt) y «less than» (lt) — pág. 4 del paper", "h2"))
S.append(P(
    "Las reglas no usan los conjuntos base: usan versiones monótonas. Si <i>x</i><sub>0</sub> es el valor donde A alcanza su máximo:"))
S.append(P("mt(A)(x) = 0 para x ≤ x0 ;  1 − μA(x) para x &gt; x0<br/>lt(A)(x) = 1 − μA(x) para x &lt; x0 ;  0 para x ≥ x0", "mono"))
S.append(P(
    "<b>mt(x) = «al menos x»</b>: crece con la cantidad observada. <b>lt(x) = «menos que x»</b>: decrece. En todas las reglas la entrada A "
    "va con <i>mt</i> y la entrada Q con <i>lt</i> (o con «any», que vale 1 siempre). Los resultados son las Tablas V y VI, "
    "que el código reproduce sin diferencia (Sección 2.4). <i>Detalle de la Tabla V:</i> para «none» y a = 1 el paper imprime 0.5 "
    "(es 1 − 0.5), es decir que en x<sub>0</sub> aplica 1 − μ cuando el máximo es menor que 1; el código sigue la tabla impresa."))
S.append(table(["Conjunto"] + [str(a) for a in range(1, 11)],
               [[f"mt({n})"] + [f"{fl.mt_arr(n, a):g}" if fl.mt_arr(n, a) else "" for a in range(1, 11)] for n in pdta.TABLE_V],
               [26 * mm] + [14.8 * mm] * 10, font=8))
S.append(P("Tabla 2.5 — mt sobre arribos (Tabla V).", "cap"))
S.append(table(["Conjunto"] + [str(q) for q in qs],
               [[f"lt({n})"] + [f"{fl.lt_queue(n, q):g}" if fl.lt_queue(n, q) else "" for q in qs] for n in pdta.TABLE_VI],
               [24 * mm] + [10.0 * mm] * 15, font=7.5))
S.append(P("Tabla 2.6 — lt sobre colas (Tabla VI). Cada conjunto es un «umbral difuso»: vale 1 hasta unos 4 vehículos antes del pico, "
           "baja 0.5 → 0.3 → 0.1 y se anula en el pico.", "cap"))

S.append(PageBreak())
S.append(P("2.3 Las curvas de fuzzificación", "h2"))
S.append(P("La figura traza los cuatro bloques desde el mismo código que usa la simulación (<font face='Courier'>fuzzy_logic.py</font>):"))
S += fig("figures/fig_fuzzificacion.png",
         "Figura 2.1 — Curvas de fuzzificación. (a) tiempo/extensión (Tabla II); (b) arribos con mt (Tabla V); (c) colas (Tabla IV); (d) colas con lt (Tabla VI).",
         width=W)
S += bullets([
    "<b>(a) Tiempo T y extensión E:</b> cinco triángulos desplazados 2 s. En t = 3 s «short» vale 1 y «veryshort» ya vale 0; los solapes de 0.5 "
    "dan una transición suave. La salida E usa estos mismos conjuntos.",
    "<b>(b) Arribos con mt:</b> curvas crecientes. mt(none) ya vale 0.5 con un solo vehículo; mt(toomany) solo empieza a contar desde a = 6. "
    "A mayor número de arribos previstos, más reglas de extensión larga se activan.",
    "<b>(c) Colas:</b> seis lomas de ancho 7 con picos en 8, 12, 16, 20, 24 y 28. Una cola de 12 es «small» con grado 1.",
    "<b>(d) Colas con lt:</b> el espejo decreciente. lt(verysmall) cae a 0 en q = 8, lt(small) en 12, … lt(verylong) en 28: cuanto más corta la cola "
    "del brazo en rojo, más se permite extender el verde.",
])

S.append(P("2.4 Validación de las curvas contra los valores impresos", "h2"))
S.append(P(
    "Sobre cada curva se superponen los valores impresos en el paper (marcadores <b>×</b>, transcritos de la imagen). En los cuatro paneles "
    "la diferencia máxima es <b>0.000</b>: las curvas del código son exactamente las del paper (Tablas II, IV, V y VI; la III se verifica en las pruebas)."))
S += fig("figures/fig_validacion_fuzzificacion.png",
         "Figura 2.2 — Código (líneas) vs. paper (×). Los marcadores coinciden con las curvas en todos los puntos.", width=W)

S.append(P("2.5 Fuzzificación de un caso concreto", "h2"))
S.append(P(
    "Para entender qué entra a las reglas, se fuzzifica una situación: la extensión candidata es t = 8 s, se prevén a = 4 vehículos y la cola del "
    "brazo en rojo es q = 6. Cada círculo es un grado de pertenencia que luego combinan los operadores min/max."))
S += fig("figures/fig_ejemplo_fuzzificacion.png",
         "Figura 2.3 — Fuzzificación de t = 8 s, a = 4 veh, q = 6 veh.", width=W)
g_t = {n: fl.MU_TIME[n][7] for n in fl.MU_TIME}
g_a = {n: fl.mt_arr(n, 4) for n in pdta.TABLE_V}
g_q = {n: fl.lt_queue(n, 6) for n in pdta.TABLE_VI}
S.append(table(["Entrada", "Grados no nulos"],
               [["T = 8 s", ", ".join(f"{n}: {v:g}" for n, v in g_t.items() if v)],
                ["A = 4 veh (mt)", ", ".join(f"mt({n}): {v:g}" for n, v in g_a.items() if v)],
                ["Q = 6 veh (lt)", ", ".join(f"lt({n}): {v:g}" for n, v in g_q.items() if v)]],
               [34 * mm, 140 * mm], font=8))
S.append(P("Tabla 2.7 — Grados del caso. Por ejemplo, la regla «T = long, A = mt(medium), Q = lt(verysmall), E = long» aportaría "
           "min(0.5, 0.5, 0.3, 0.5) = 0.3.", "cap"))

S.append(CondPageBreak(95 * mm))
S.append(P("2.6 Cómo se lee el operador lt", "h2"))
S += fig("figures/fig_lt_explicacion.png",
         "Figura 2.4 — (a) construcción de lt(medium) a partir del conjunto base; (b) las seis curvas lt.", width=W)
S += code(open(os.path.join(_COD, "fuzzy_logic.py"), encoding="utf-8").read().split("MU_TIME = {")[1].split("def mu_time")[0].join(["MU_TIME = {", ""]).rstrip(),
          "Código de la fuzzificación (fuzzy_logic.py)")

# ===========================================================================
# 3. Reglas
# ===========================================================================
S.append(PageBreak())
S.append(P("3. Las 25 reglas del Apéndice", "h1"))
S.append(P(
    "El conocimiento del controlador son 25 reglas «si T … y A = mt(·) y Q = lt(·) entonces E …», agrupadas en 5 intervenciones de 5 reglas "
    "(págs. 6, 715–716). Se encadenan con «else» (= max). Tabla transcrita de la <b>imagen</b> del Apéndice:"))
hdr = ["Intervención", "T", "A (mt)", "Q (lt)", "E"]
rows = []
for k in fl.INTERVENTIONS:
    for i, (T, A, Q, E) in enumerate(fl.RULES[k]):
        rows.append([f"{k} s" if i == 0 else "", T, A, Q, E])
S.append(table(hdr, rows, [28 * mm, 32 * mm, 32 * mm, 32 * mm, 32 * mm], font=7.8,
               hl=tuple(range(11, 26))))
S.append(P("Tabla 3.1 — Las 25 reglas. Resaltadas las intervenciones de 27, 37 y 47 s, cuya transcripción previa era errónea.", "cap"))
S += bullets([
    "<b>Estructura diagonal:</b> en todas las reglas T = E; la primera de cada intervención es siempre «veryshort / none / any».",
    "<b>Cola cada vez más permisiva:</b> los umbrales de Q suben con el tiempo de verde (verysmall → small → smallplus/medium → long/verylong): "
    "tras más tiempo de verde la cola del brazo en rojo es naturalmente mayor.",
    "<b>Reglas de 27 s:</b> son iguales a las de 17 s. Las que antes se atribuían a 27 s (smallplus, medium, long) pertenecen a la intervención de 37 s.",
    "<b>Reglas trial-and-error:</b> el paper (pág. 8) dice que se obtuvieron por prueba y error; no son óptimas universales.",
])

# ===========================================================================
# 4. Inferencia y ejemplo
# ===========================================================================
S.append(P("4. Inferencia, decisión y ejemplo trabajado", "h1"))
S.append(P(
    "Para cada extensión candidata e = 1…10 s (con T = e) cada regla aporta min(μ<sub>T</sub>(e), μ<sub>mt(A)</sub>(β<sub>e</sub>), "
    "μ<sub>lt(Q)</sub>(q<sub>e</sub>), μ<sub>E</sub>(e)) y las reglas se unen con <b>max</b> (inferencia min–max de Mamdani). "
    "<b>Defuzzificación (no es centroide):</b> se elige el e de mayor grado; si todos son menores que 0.5 no hay extensión y se cambia de fase; "
    "si el máximo se repite, se toma la <b>mayor</b> extensión empatada (pág. 8)."))
S.append(CondPageBreak(75 * mm))
S.append(P("4.1 Ejemplo de las págs. 7–8 (2.ª intervención, 17 s)", "h2"))
S.append(P(
    "Datos: arribos N–S x = (0 1 0 1 1 1 1 0 0 1) → β = (0 1 1 2 3 4 5 5 5 6); arribos E–W x′ = (0 1 0 0 1 0 0 1 0 0) con cola Q = 5 → "
    "β′ = (5 6 6 6 7 7 7 8 8 8). Tabla VII del paper y resultado del código:"))
per = fl.fuzzy_decision_per_rule(pdta.EXAMPLE_X, pdta.EXAMPLE_XP, pdta.EXAMPLE_Q, fl.RULES[17], a_mode="arrivals", q_mode="predicted")
agg = fl.fuzzy_decision(pdta.EXAMPLE_X, pdta.EXAMPLE_XP, pdta.EXAMPLE_Q, fl.RULES[17], a_mode="arrivals", q_mode="predicted")
rows = []
for i, key in enumerate(("R1", "R2", "R3", "R4", "R5")):
    T_, A_, Q_, E_ = fl.RULES[17][i]
    ok = np.allclose(per[i, 1:], pdta.EXAMPLE_ROW_VII[key])
    rows.append([f"{T_}/mt({A_})/{'any' if Q_ == 'any' else 'lt(' + Q_ + ')'}"] + [f"{v:g}" if v else "0" for v in per[i, 1:]] + ["OK" if ok else "NO"])
rows.append(["Fuzzy Algorithm (max)"] + [f"{v:g}" if v else "0" for v in agg[1:]] +
            ["OK" if np.allclose(agg[1:], pdta.EXAMPLE_ROW_VII["algoritmo"]) else "NO"])
S.append(table(["Regla"] + [str(e) for e in range(1, 11)] + ["= paper"], rows, [54 * mm] + [9.2 * mm] * 10 + [14 * mm], font=7.3, hl=(6,)))
S.append(P("Tabla 4.1 — Cada fila coincide con la Tabla VII del paper (columnas e = 1…10 s). El máximo es 0.8 en e = 10 s, que es la extensión elegida.", "cap"))
S += fig("figures/fig3_decision_curve.png", "Figura 4.1 — Contribución de cada regla y curva agregada (umbral 0.5).", width=125 * mm)

# ===========================================================================
# 5. Modelo y Tabla I
# ===========================================================================
S.append(PageBreak())
S.append(P("5. Modelo de la intersección y Tabla I", "h1"))
S += bullets([
    "Dos calles unidireccionales, un carril, sin giros; flujo de saturación 3600 veh/h = 1 veh/s; tiempo perdido de 10 s por ciclo (5 s por cambio de fase).",
    "Llegadas Bernoulli por segundo; retardo medio d<sub>m</sub> = retardo total / vehículos totales (pág. 2).",
    "Controlador: intervenciones a los 7, 17, 27, 37 y 47 s del verde; si e* = 10 se vuelve a intervenir 10 s después; si e* &lt; 10 el verde termina tras e* s; "
    "verde efectivo = 7 + Σe* ≤ 57 s.",
    "Ciclo fijo óptimo (Webster): C<sub>0</sub> = (1.5L + 5)/(1 − Y), g<sub>i</sub> = (y<sub>i</sub>/Y)(C<sub>0</sub> − L). La columna «vehicle-actuated» de la "
    "Tabla VIII repite la columna «Model» de la Tabla I, por lo que la línea base de comparación es este ciclo fijo simulado.",
])
hdr = ["N–S", "E–W", "Sim.", "Paper (Model)", "err %", "Fórmula", "Paper (Formula)", "err %"]
rows = []
for r in T1:
    pm, pf = pdta.TABLE_I[(r["ns"], r["ew"])]
    rows.append([r["ns"], r["ew"], f"{r['sim']:.2f}", pm, f"{100 * (r['sim'] - pm) / pm:+.1f}", f"{r['formula']:.2f}", pf, f"{100 * (r['formula'] - pf) / pf:+.1f}"])
S.append(table(hdr, rows, [16 * mm, 16 * mm, 20 * mm, 26 * mm, 18 * mm, 22 * mm, 28 * mm, 18 * mm], font=7.6))
S.append(P(f"Tabla 5.1 — Tabla I: simulación (20 × 7200 s) y fórmula de Webster contra el paper. Error medio {e_sim:.1f} % (simulación) y {e_for:.1f} % (fórmula). "
           "Mayor desviación: 360/2160 (−7.9 %), porque el verde de 8.1 s se redondea a 8 s.", "cap"))
S.append(P("La fórmula usada es d = C(1−λ)²/(2(1−λX)) + X²/(2q(1−X)) − 0.65(C/q²)<super>1/3</super>X<super>2+5λ</super>, evaluada en cada brazo con los ajustes óptimos y ponderada por el flujo; "
           "reproduce la columna «Formula» con diferencias menores a 0.1 s salvo 360/2520. Esto valida a la vez el modelo y las ecuaciones (8)–(10) del paper."))

# ===========================================================================
# 6. Tabla VIII
# ===========================================================================
S.append(P("6. Tabla VIII: controlador difuso frente a la línea base", "h1"))
S.append(P(
    "El paper no detalla cómo su programa obtenía A y Q a partir del estado de la simulación. El ejemplo de la Tabla VII usa «β = arribos acumulados» y "
    "«β′ = Q + arribos del brazo en rojo», pero no dice cuánto vale Q cuando la simulación avanza ni cómo cuentan en A los vehículos que ya "
    "esperan en el brazo en verde. Se dejaron dos lecturas, sin tocar las reglas:"))
S += bullets([
    "<b>Literal:</b> A = arribos acumulados; Q = cola total del brazo en rojo evaluada en β′ (exactamente el ejemplo).",
    "<b>Calibrada:</b> A = vehículos que realmente cruzan en e s (limitados por 1 veh/s, lo que incluye la cola del verde); "
    "Q = vehículos llegados al brazo en rojo <i>desde el inicio del verde actual</i>, en su valor actual.",
])
hdr = ["N–S", "E–W", "Fijo sim.", "Fijo paper", "Difuso sim.", "Difuso paper", "err %", "Mejora sim.", "Mejora paper"]
rows = []
for r in CAL:
    pf, pz = pdta.TABLE_VIII[(r["ns"], r["ew"])]
    rows.append([r["ns"], r["ew"], f"{r['fixed']:.2f}", pf, f"{r['fuzzy']:.2f}", pz, f"{100 * (r['fuzzy'] - pz) / pz:+.1f}",
                 f"{r['improvement']:+.0f} %", f"{100 * (pf - pz) / pf:+.0f} %"])
S.append(table(hdr, rows, [15 * mm, 15 * mm, 21 * mm, 21 * mm, 22 * mm, 23 * mm, 16 * mm, 21 * mm, 22 * mm], font=7.6))
S.append(P(f"Tabla 6.1 — Tabla VIII con la lectura calibrada (20 × 7200 s). El difuso mejora al ciclo fijo en {wins}/16 celdas (paper: 16/16); error medio "
           f"{np.mean(errs):.1f} %, máximo {np.max(errs):.1f} %. Las celdas pesadas (1080/1800 y 1440/1440) quedan a ±2 %.", "cap"))
S += fig("figures/fig4_delay_comparison.png", "Figura 6.1 — Retardo medio: réplica vs. paper.", width=W)
S += fig("figures/fig_validacion_tablas.png", "Figura 6.2 — Réplica vs. paper en las Tablas I y VIII (la diagonal es la coincidencia exacta). "
         "A la derecha, la lectura literal en escala logarítmica.", width=W)

S.append(P("6.1 Auditoría de las lecturas posibles", "h2"))
S.append(P(f"Se probaron las 8 combinaciones razonables ({aud['reps']} réplicas × {aud['duration']} s, reglas fijas) y se midió el error frente a la Tabla VIII:"))
na = {"arrivals": "arribos acumulados", "crossing": "cruces (limit. saturación)"}
nq = {"predicted": "predicha β′", "current": "actual"}
ns_ = {"total": "total", "green_arrivals": "desde inicio del verde"}
rows, hl = [], []
for i, v in enumerate(aud["variants"]):
    tag = ""
    if (v["a_mode"], v["q_mode"], v["queue_source"]) == ("crossing", "current", "green_arrivals"):
        tag, hl = " (calibrada)", [i + 1]
    if (v["a_mode"], v["q_mode"], v["queue_source"]) == ("arrivals", "predicted", "total"):
        tag = " (literal)"
    rows.append([na[v["a_mode"]], nq[v["q_mode"]], ns_[v["queue_source"]], f"{v['mean_err']:.1f} %", f"{v['max_err']:.1f} %", f"{v['wins']}/16{tag}"])
S.append(table(["A", "Q evaluada en", "Cola Q", "Error medio", "Máximo", "Mejor que el fijo"], rows,
               [38 * mm, 28 * mm, 38 * mm, 22 * mm, 22 * mm, 30 * mm], font=7.6, hl=tuple(hl)))
S.append(P("Tabla 6.2 — Solo una lectura reproduce la Tabla VIII en todo el rango.", "cap"))
S.append(P(
    "<b>Por qué falla la lectura literal.</b> Con la cola total real del brazo en rojo, las reglas de 7, 17 y 27 s solo extienden si esa cola es de unos 5 vehículos o menos "
    "(lt(verysmall)); en cuanto el flujo sube, la cola supera ese valor, el verde se corta a ~9 s y la capacidad no alcanza: el sistema se satura. "
    "<b>Advertencia:</b> la lectura calibrada se eligió por reproducir los resultados, no porque el texto la indique, y es sensible (contar la cola completa "
    "o los 2 vehículos llegados en el tiempo perdido ya la vuelve inestable).", "note"))

# ===========================================================================
# 7. Conclusiones
# ===========================================================================
S.append(P("7. Información que el paper no contiene", "h1"))
S.append(P(
    "La réplica se construyó con una única fuente: el paper original. Estos son los datos que no están en él y cómo se resolvieron; "
    "en las tres primeras filas, la solución adoptada es una <b>inferencia o suposición</b> y no una cita."))
hdr = ["Dato ausente", "Qué dice el paper", "Cómo se resolvió en la réplica"]
rows = [
    ["Cómo el programa obtenía A y Q en cada intervención", "El ejemplo (págs. 7–8) da vectores ya calculados: β = arribos acumulados, β′ = Q + arribos del brazo en rojo.", "Dos lecturas explícitas; la calibrada se infiere por ser la única de 8 que reproduce la Tabla VIII."],
    ["Velocidades de los vehículos y distancia de los detectores", "Cada vehículo se registra con N = l/v − 1.5 s (pág. 3), sin dar l ni la distribución de v.", "No se modela; se usan directamente los arribos por segundo como cruces del punto crítico."],
    ["Valores fuera de los universos impresos", "Colas de 4 a 32 y arribos de 1 a 10.", "lt(·)(q) = 1 para q &lt; 4; mt(·)(0) = 0."],
    ["Número de réplicas, semillas y generador aleatorio", "«Many runs»; 7200 s por corrida; ICL-1900.", "20 réplicas × 7200 s, semilla base 0."],
    ["Condiciones iniciales", "No se mencionan.", "Cola vacía, empieza la fase N–S, sin periodo de calentamiento."],
    ["Reparto del tiempo perdido (10 s por ciclo)", "Ámbar de 3 s; el verde efectivo termina a mitad del ámbar.", "5 s sin descarga en cada cambio de fase; los arribos de ese tiempo se acumulan en la cola."],
]
S.append(table(hdr, rows, [48 * mm, 62 * mm, 64 * mm], font=7.4))
S.append(P("Tabla 7.1 — Información ausente en el paper y decisión tomada en la réplica.", "cap"))
S.append(P("7.1 ¿Llegadas aleatorias o fijas?", "h2"))
arr = json.load(open("resultados/llegadas_fijas_vs_aleatorias.json"))
S.append(P(
    "El paper describe las llegadas como aleatorias (pág. 2): en cada segundo se genera un número pseudoaleatorio y se compara con la tasa media. "
    "Lo único fijo en el modelo es la descarga de la cola, a 1 veh/s durante el verde (flujo de saturación). Una entrada de 1 veh/s por brazo equivaldría a "
    "3600 veh/h, mientras que las Tablas I y VIII usan entre 360 y 2520 veh/h. Aun así, se comprobó la alternativa de llegadas fijas "
    f"(un vehículo cada 1/λ s, con desfase aleatorio; {arr['reps']} réplicas × {arr['duration']} s):"))
hdr = ["Modelo de llegadas", "Error medio, Tabla I", "Error medio, Tabla VIII"]
rows = [["Aleatorias (Bernoulli por segundo)", f"{arr['err_table_I']['bernoulli']:.1f} %", f"{arr['err_table_VIII']['bernoulli']:.1f} %"],
        ["Fijas (un vehículo cada 1/λ s)", f"{arr['err_table_I']['fijas']:.1f} %", f"{arr['err_table_VIII']['fijas']:.1f} %"]]
S.append(table(hdr, rows, [60 * mm, 55 * mm, 59 * mm], font=8))
sel = [r for r in arr["rows"] if (r["ns"], r["ew"]) in ((360, 2520), (720, 2160), (1440, 1440))]
S.append(P("Tabla 7.2 — Ciclo fijo (Tabla I) y difuso con lectura calibrada (Tabla VIII). Con llegadas fijas el ciclo fijo queda sistemáticamente por debajo de la Tabla I (p. ej. 360/2520: "
           + ", ".join(f"{r['fixed_fijas']:.1f} s con llegadas fijas frente a {r['fixed_bernoulli']:.1f} s con aleatorias, paper {pdta.TABLE_I[(r['ns'], r['ew'])][0]}"
                       for r in sel[:1]) + "). La Tabla I respalda las llegadas aleatorias; la Tabla VIII no distingue entre ambos modelos.", "cap"))

S.append(P("8. Conclusiones de la validación", "h1"))
S.append(P("<b>Confirmado con la réplica:</b>"))
S += bullets([
    "Fuzzificación: Tablas II–VI y curvas exactas (diferencia 0.000).",
    "Las 25 reglas del Apéndice y la inferencia min–max con defuzzificación por máximo, umbral 0.5 y desempate a la mayor extensión.",
    "El ejemplo trabajado (Tabla VII completa, e* = 10 s) y la estructura temporal (7, 17, 27, 37, 47 s; verde ≤ 57 s).",
    f"El modelo de la intersección: Tabla I con error medio {e_sim:.1f} % y fórmula de Webster {e_for:.1f} %.",
    f"La conclusión cualitativa del paper: el difuso supera al ciclo fijo en {wins}/16 combinaciones, con mejoras de 14 % a 30 % (paper: 10 % a 24 %).",
])
S.append(P("<b>No confirmado / abierto:</b>"))
S += bullets([
    "Cómo medía el programa original A y Q (Secciones 6 y 7): la lectura calibrada es una inferencia por falta de datos.",
    "El difuso simulado queda 10 %–20 % por debajo del publicado en caudales medios (p. ej. 1080/1080: 9.62 vs. 12.0).",
    "No hay código ni generador aleatorio de 1977: la comparación es estadística, no dígito a dígito. Tampoco se conoce el número de réplicas.",
])
S.append(P("Referencia", "h2"))
S.append(P("C. P. Pappis y E. H. Mamdani, «A Fuzzy Logic Controller for a Traffic Junction», <i>IEEE Trans. Syst., Man, Cybern.</i>, vol. SMC-7, no. 10, pp. 707–716, oct. 1977 (versión original en inglés)."))

doc.build(S)
print("generado:", OUT)
