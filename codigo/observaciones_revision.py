"""
observaciones_revision.py
================================================================================
Fuente unica de la revision del 07-11-2026 («Revision_Valero»): cada observacion recibida, su evaluacion (procede / procede
en parte / no procede / no verificable), la razon con la evidencia y lo que se hizo en el manuscrito. La usan
  gen_revision_observaciones.py   documento «Revision de las observaciones» (articulo/revision_observaciones.tex -> PDF)
  gen_cuadro_observaciones.py     documento «Cuadro de observaciones levantadas» (DOCX y PDF)
de modo que los dos documentos no se contradigan. Las ubicaciones («donde») se escriben como claves de etiquetas del
manuscrito (main.aux) o del suplemento (suplemento.aux, prefijo "S:") y los documentos las convierten en seccion/tabla y pagina.
"""

PROCEDE = "PROCEDE"
EN_PARTE = "PROCEDE EN PARTE"
NO_PROCEDE = "NO PROCEDE"
NO_VERIFICABLE = "NO VERIFICABLE"

# (id, tipo, texto de la observacion, ubicacion citada por el revisor, veredicto, razon y evidencia, accion en el manuscrito, donde)
OBS = [
    ("O1", "Mayor 1", "Asimetría de información: FLC-O usa 10 s de vista adelante y el actuado afinado no; la ventaja de @@RedActAfOf@@ % sobre el actuado es en parte una ventaja de información. "
     "Arreglo propuesto: agregar un actuado con vista adelante, o presentar la comparación sin vista adelante como la comparación justa y calificar el 17.8 %.",
     "Abstract; Sec. VIII-A; Tabla 4; Sec. IX; C3; Sec. 7", PROCEDE,
     "Es cierto y era la objeción más importante. Se implementó y afinó un actuado con la misma vista adelante (4 parámetros, mismos escenarios de entrenamiento y rango). "
     "Resultado: la ventaja de FLC-O sobre el actuado cae de @@RedActAfOf@@ % a @@RedActVOf@@ % en el conjunto oficial (significativa en @@ParMejorActV@@ de 16 pares, @@ParPeorActV@@ peor), a @@RedActVNv@@ % con caudales no vistos, a @@RedActVVa@@ % con demanda variable y a @@RedActVSa@@ % cerca de la saturación. "
     "Matiz que el revisor no vio: la comparación principal, con el controlador de 1977 reconstruido, ya tenía información igual (ese controlador también ve las llegadas de los próximos 10 s).",
     "Nuevo rival «actuado afinado con vista adelante» en el protocolo, en las Tablas 3 a 6, en la Fig. 3 y en el resumen; el @@RedActAfOf@@ % se califica como «sin vista adelante» y se reporta junto al @@RedActVOf@@ %. "
     "Se agrega, con honestidad, que el actuado con vista adelante ya mejora @@RedVistaPapOf@@ % al controlador de 1977.",
     ["sec:protocolo", "tab:controladores", "sec:res-oficial", "tab:oficial", "tab:comparaciones", "fig:retardo", "sec:res-otros", "tab:conjuntos", "sec:discusion", "S:sec:s-ref"]),
    ("O2", "Mayor 2", "Las ecuaciones exactas de las funciones de pertenencia de FLC-O (formas, hombros, comportamiento fuera del universo) no están en el manuscrito; "
     "la Fig. 2 y la lista de nudos no bastan para reconstruirlo sin el código.",
     "Fig. 2; Tabla 3; Justificación Sec. 7; C4, C5, C9; Parte 4B ítem 12", PROCEDE,
     "Era cierto: el texto describía la partición en palabras y daba los nudos con un decimal. Se verificó la corrección con una implementación independiente escrita solo con las ecuaciones nuevas.",
     "Se agregan las ecuaciones de las tres pertenencias, la parametrización de los nudos, el comportamiento fuera de [k1, k3]; los nudos y pesos con 3 decimales; en el suplemento, los 42 parámetros con 6 decimales y un ejemplo numérico. "
     "Nueva prueba test_flco_ecuaciones.py: la implementación independiente coincide con el código (diferencia 4e-16) y con la tabla impresa.",
     ["sec:flc", "eq:mf", "fig:difuso", "tab:reglasflc", "S:sec:s-flco", "S:tab:sparametros", "S:tab:sejemplo"]),
    ("O3", "Mayor 3", "Los conjuntos de prueba no oficiales (Tabla 6) y las filas de ablación (Tabla 7) carecen de número de réplicas y de dispersión; la ablación usa una sola semilla de entrenamiento. "
     "Arreglo: agregar n, semillas y SD/IC a las Tablas 6 y 7; estadística multi-semilla para verde mínimo, número de reglas y pesos de la vista adelante.",
     "Tablas 6 y 7; C5, C6; Sec. 7", PROCEDE,
     "Cierto. En la Tabla 6 cada escenario es un par de caudales con una réplica, pero eso no estaba dicho; y la ablación comparaba entrenamientos únicos, sin saber cuánto varía una semilla de otra.",
     "Tabla 6: n, semillas, media con IC 95 % y reducción por escenario con IC y prueba de Wilcoxon. Tabla 7: media y desviación entre 3 semillas de entrenamiento para verde mínimo (3, 4, 5 y 7 s), horizontes fijos y 81 reglas; "
     "las filas con una sola semilla se marcan como exploratorias (n = 1). Se entrenaron 10 modelos más para esto.",
     ["sec:res-otros", "tab:conjuntos", "sec:res-abl", "tab:ablacion", "S:tab:ssemillas"]),
    ("O4", "Mayor 4", "La comparación con Pappis y Mamdani es contra una reconstrucción calibrada, no contra la tabla impresa; el resumen y las etiquetas de las tablas no lo califican de forma consistente. "
     "Arreglo: etiquetar «reconstruido con A/Q calibradas» y dar el error de 9.2 % junto a la comparación principal.",
     "Sec. IV-B; Sec. IX; Tabla 4; Abstract", PROCEDE,
     "Cierto en la presentación: el manuscrito lo declaraba en la Sec. IV-B y en la Sec. IX, pero el resumen y las tablas decían «Pappis y Mamdani» a secas. "
     "Aclaración: las reglas, los conjuntos y los operadores son los impresos; solo las entradas A y Q son una definición de este trabajo.",
     "Se usa «Pappis y Mamdani reconstruido» en el resumen, el protocolo, las tablas y la discusión; el error de 9.2 % (máximo 18.6 %) acompaña la definición en el protocolo y en el resumen.",
     ["sec:lecturas", "sec:protocolo", "tab:controladores", "tab:oficial", "sec:discusion"]),
    ("O5", "Mayor 5", "La Tabla 4 solo da retardos medios; la Fig. 3(a) tiene banda de confianza solo para FLC-O. Arreglo: columnas de SD o IC 95 % en la Tabla 4 y bandas para todos los controladores.",
     "Tabla 4; Fig. 3; C7", PROCEDE,
     "Cierto en el texto principal. La dispersión por par ya estaba en el suplemento (Tabla S5) para tres controladores, pero no en la Tabla 4.",
     "Tabla 4: media ± desviación estándar de las 20 réplicas para cada controlador. Fig. 3(a): banda de IC 95 % para todos (la cota es determinista). Suplemento S5: se agrega el actuado con vista adelante.",
     ["tab:oficial", "fig:retardo", "S:tab:spares"]),
    ("O6", "Menor", "Pie de la Tabla 3: «CONTROLDORES» debe ser «CONTROLADORES».", "Tabla 3, pie", NO_PROCEDE,
     "No existe tal error. El fuente dice «Controladores comparados y la información que usan» y el texto extraído de nuestro PDF muestra «C ONTROLADORES COMPARADOS»: el título está en versalitas y la extracción de texto pierde letras. "
     "El propio revisor declara ruido de extracción en esas páginas.", "Ninguna (no hay defecto en el manuscrito).", ["tab:controladores"]),
    ("O7", "Menor", "Pie de la Fig. 3: aclarar que la banda es el IC 95 % solo de FLC-O; agregar IC para los otros o decirlo explícitamente.", "Fig. 3, pie", EN_PARTE,
     "El pie ya decía «la banda es el intervalo de confianza de 95 % de FLC-O». Se acepta la sugerencia de fondo (bandas para todos).", "Bandas para todos los controladores y pie reescrito (ver O5).", ["fig:retardo"]),
    ("O8", "Menor", "Pie de la Tabla 6: indicar número de réplicas y semillas de cada conjunto de prueba.", "Tabla 6, pie", PROCEDE,
     "Cierto: faltaba.", "El pie y los encabezados dan el número de unidades (16 pares, 64, 64 y 32 escenarios) y las semillas de cada conjunto.", ["tab:conjuntos", "sec:protocolo"]),
    ("O9", "Menor", "Sec. IX: «Pappis y Mamdani» debe ser «Pappis y Mamdani reconstruido» en la primera mención del 27.8 %.", "Sec. IX", PROCEDE,
     "Cierto (ver O4).", "Cambiado en la discusión, las conclusiones y el resumen.", ["sec:discusion", "sec:conclusiones"]),
    ("O10", "Menor", "Resumen: calificar el 17.8 % sobre el actuado como «con vista adelante de 10 s».", "Abstract", PROCEDE,
     "Cierto, y la revisión de fondo (O1) muestra que es la parte más sensible del resultado.", "El resumen en los dos idiomas separa «actuado sin vista adelante: @@RedActAfOf@@ %» de «actuado con la misma vista adelante: @@RedActVOf@@ %».", ["sec:res-oficial"]),
    ("O11", "Menor", "Sec. IV-B: revisar la consistencia de las referencias [25] «Vuong et al. (ANFIS)» y [26] «Shaheen et al.» con la lista de referencias.", "Sec. IV-B", EN_PARTE,
     "Se verificaron ambas contra Crossref (título, autores, revista, volumen, páginas, año): son consistentes. La ubicación citada es errónea: las dos citas están en la Sec. II (estado del arte), no en la IV-B. "
     "Solo faltaba el número de artículo de Shaheen et al.", "Se completa la entrada de Shaheen et al. (número 15273).", ["sec:sota"]),
    ("O12", "Menor", "Sec. V-A: indicar el modelo exacto de CPU y el tiempo de ejecución de la afirmación del «entrenamiento de 20 minutos»; la tabla de reproducibilidad marca el hardware como incompleto.",
     "Sec. V-A; Parte 4B ítem 7", EN_PARTE,
     "El dato de hardware sí faltaba. Pero no existe una afirmación de 20 minutos en ningún documento: el manuscrito decía 15 y el tiempo medido es 787 s (13 min). "
     "Además, el tiempo de entrenamiento está en la Sec. VI-D, no en la V-A (que trata del simulador). El «hardware» de este renglón de la plantilla es solo la computadora de las simulaciones: el estudio no tiene equipos físicos, instrumentación ni programas de PLC.",
     "Se agrega el procesador (Intel Xeon a 2.10 GHz, 4 vCPU, 15 GB) en las Sec. V-A y VI-D y en la disponibilidad, y el tiempo medido (13 min, 787 s). Se declara además que es el único equipo del estudio, que es solo de simulación (introducción, «Alcance»).", ["sec:vectorizado", "sec:entrena", "sec:disp", "sec:intro"]),
    ("O13", "Menor", "Tabla 5: aclarar si el intervalo es sobre las 16 mejoras por par o un IC de la media.", "Tabla 5", PROCEDE,
     "Era el rango (mínimo a máximo) de las 16 mejoras, no un intervalo de confianza; el rótulo «Intervalo» confundía.", "Columna renombrada «Rango», se agrega «IC 95 %» de la media y el pie lo explica.", ["tab:comparaciones"]),
    ("O14", "Menor", "Tabla S2 del suplemento: agregar unidades a las columnas «Error medio» y «Error máximo».", "Suplemento, Tabla S2", NO_PROCEDE,
     "Las unidades ya están: los encabezados dicen «Error medio ( %)» y «Error máximo ( %)».", "Ninguna.", ["S:tab:slecturas"]),
    ("O15", "Menor", "Justificación, Sec. 7: reemplazar «venta» por «ventana».", "Justificación, Sec. 7", NO_PROCEDE,
     "No aparece «venta» en el texto: el fuente y el PDF dicen «ventana». El revisor declara ruido de extracción en la página 10 de ese documento.", "Ninguna.", []),
    ("O16", "Otra", "Novedad incremental: el resumen y la introducción deben declarar que es un estudio empírico de optimización y comparación, no un nuevo paradigma de control.", "C2; Scorecard; Sec. 1", PROCEDE,
     "Es una calificación razonable de lo que el trabajo aporta.", "Se declara en el resumen (dos idiomas) y en la introducción: contribución empírica, no una nueva teoría de control.", ["sec:intro"]),
    ("O17", "Otra", "Notación: definir G, R, V, Q_G, Q_V, u y c_ijk en la tabla de notación antes de su primer uso.", "Sec. 8; Sec. VI", EN_PARTE,
     "G, R, V, u y c_ijk ya estaban en la Tabla 1, antes de la Sec. VI. «Q_G» no existe como símbolo aparte: en la Sec. IV-B era la misma cola que Q_g. Sí faltaban Q_V, a_e, q_e, los nudos k_i y las pertenencias.",
     "Se unifica Q_G como Q_g y se agregan Q_V, a_e, q_e, k1-k3 y las pertenencias a la Tabla 1.", ["tab:notacion", "sec:lecturas"]),
    ("O18", "Otra", "El «empate» cerca de la saturación (@@DelaySaFlc@@ frente a @@DelaySaActAf@@ s/veh) se reporta sin prueba de significancia.", "Sec. 7; Tabla 6; C-tabla de evidencia", PROCEDE,
     "Cierto. Con la prueba pareada por escenario no hay diferencia significativa (p = @@EscActAfSaP@@; reducción media por escenario de @@EscActAfSaRed@@ %, IC 95 % de @@EscActAfSaLo@@ % a @@EscActAfSaHi@@ %). Un p alto no demuestra equivalencia y así se dice.",
     "Se reporta el IC y el p de Wilcoxon en la Tabla 6 y en la Sec. VIII-B, con la salvedad.", ["sec:res-otros", "tab:conjuntos"]),
    ("O19", "Otra", "El repositorio no se pudo verificar externamente (sin acceso web); estado «UNVERIFIABLE».", "Etapa 0; C9; Parte 4B ítems 10 y 11", NO_VERIFICABLE,
     "Es una limitación del entorno del revisor, no un defecto del manuscrito. Se comprobó que el repositorio es público (responde sin credenciales) y que un clon limpio de main pasa todas las pruebas y compila el artículo.",
     "Para facilitar la verificación se agrega al manuscrito el commit con el que se generaron los resultados y el entorno exacto.", ["sec:disp"]),
    ("O20", "Otra", "Tabla 3: «no hay ecuaciones explícitas de las pertenencias»; la lista de nudos de la Tabla 3 no basta para reconstruir.", "Sec. 8 (Tabla 3)", NO_PROCEDE,
     "Referencia cruzada errónea: la Tabla 3 es la de controladores comparados; los nudos están en el pie de la Tabla 2. La sustancia (ecuaciones exactas) es válida y se atiende en O2.",
     "Ninguna adicional a O2.", ["tab:reglasflc"]),
    ("O21", "Otra", "Arreglo propuesto en C3: «hacer de la comparación con FLC-O causal (mejora de @@RedActMlpC@@ % sobre el actuado) la comparación justa principal».", "C3; Sec. 5, punto 1", NO_PROCEDE,
     "Error factual del revisor. El @@RedActMlpC@@ % es de la política neuronal causal; FLC-O causal cambia el retardo en @@RedActFlcC@@ % respecto del actuado afinado, es decir, es peor (@@DelayOfFlcC@@ contra @@DelayOfActAf@@ s/veh). "
     "Además, la comparación causal no es la principal para el resultado de 27.8 %, pues el controlador de 1977 sí tiene vista adelante. La alternativa que el revisor ofrece (actuado con vista adelante) sí se hizo (O1).",
     "Se mantiene la comparación sin vista adelante tal como estaba (@@RedActMlpC@@ % la política neuronal; @@RedActFlcC@@ % el difuso causal) y se agrega la comparación con información igualada.", ["sec:res-abl"]),
]

# ---------------------------------------------------------------- clase de cada observacion: mayor o menor
# La revision enumera 5 observaciones mayores (seccion 5, «Major Issues»: O1-O5) y 10 menores (seccion 6, «Minor Issues»: O6-O15).
# O16-O21 salen de otras secciones, donde el revisor no las pone en ninguna de las dos listas; se clasifican aqui segun la
# severidad que el propio revisor les da en esa seccion, y el documento lo dice.
BASE_CLASE = {
    "O16": ("Mayor", "no está en las listas de mayores ni menores de la revisión; sale de la sección C2, donde el revisor le asigna severidad «Important»"),
    "O17": ("Menor", "no está en las listas de mayores ni menores de la revisión; sale de la sección 8 (figuras, tablas y notación), cuyo arreglo el revisor califica de «menor»"),
    "O18": ("Mayor", "no está en las listas de mayores ni menores de la revisión; sale de la sección 7 (calidad de los datos) y es parte de la estadística de la Tabla 6 que pide la observación mayor 3"),
    "O19": ("Mayor", "no está en las listas de mayores ni menores de la revisión; sale de la sección C9 (reproducibilidad), donde el revisor le asigna severidad «Important»"),
    "O20": ("Menor", "no está en las listas de mayores ni menores de la revisión; sale de la sección 8 (figuras, tablas y notación), cuyo arreglo el revisor califica de «menor»"),
    "O21": ("Mayor", "no está en las listas de mayores ni menores de la revisión; es parte del arreglo propuesto en la observación mayor 1 y en la sección C3 (severidad «Important»)"),
}


def clase(oid, tipo):
    """('Mayor' | 'Menor', explicacion de donde sale la clasificacion)."""
    if tipo.startswith("Mayor"):
        return "Mayor", f"observación mayor {tipo.split()[1]} de la revisión, en su sección 5 «Major Issues»"
    if tipo == "Menor":
        return "Menor", "lista de observaciones menores de la revisión, en su sección 6 «Minor Issues»"
    return BASE_CLASE[oid][0], "clasificación propia: " + BASE_CLASE[oid][1]
