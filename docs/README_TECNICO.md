# Réplica del *Fuzzy Logic Controller for a Traffic Junction* (Pappis & Mamdani, 1977)

> C. P. Pappis y E. H. Mamdani, *A Fuzzy Logic Controller for a Traffic Junction*,
> IEEE Trans. Syst., Man, Cybern., vol. SMC-7, no. 10, pp. 707–716, 1977.

**Alcance de la réplica (secciones 1 a 8):** replicar el paper original lo más fielmente posible, para poder
entenderlo y reproducirlo. El trabajo del repositorio es ahora la mejora de ese controlador (sección 9); la réplica es su punto de partida. En la réplica no se propone ningún cambio al método (reglas, conjuntos,
operadores, regla de decisión): los controladores alternativos y el re-afinado de reglas
hechos antes no forman parte de este repositorio (se calcularon con reglas mal transcritas y quedaron descartados).

**Fuente de verdad:** únicamente el paper **original en inglés** (PDF `01 pappis1977`, págs. 707–716),
leído sobre la **imagen** de cada página. Todos los valores de `paper_data.py` y las 25 reglas salen del original.

---

## Estructura de carpetas

```
raíz del repositorio/
├── codigo/          todo el código Python (modelo, controlador, simulador, pruebas, generadores)
├── resultados/      JSON de resultados (Tablas I y VIII, auditoría, llegadas, reducción de reglas); opt/: modelos entrenados y evaluación final
├── figures/         figuras generadas por plots.py y gen_fig_*.py
├── muestras/        ejemplos listos para mostrar (video, CSV de disparos, captura del simulador)
├── articulo_replica/   artículo IEEE para Overleaf (main.tex, tablas, figuras, PDF)
├── articulo/    artículo y suplemento de la versión de optimización (main.tex, suplemento.tex, PDF)
├── referencia/      cita del paper original en inglés (el PDF no se incluye: es de IEEE)
├── notebooks/       cuaderno Jupyter
├── docs/            este documento, la guía de VS Code y el PDF del avance 5
├── archivo/         material histórico (controlador previo de 16 reglas y módulo previo a las correcciones; no usar)
├── .vscode/         ejecutar/depurar con F5 y tareas
└── salidas/         (se crea al ejecutar) CSV, PNG, MP4 y resumen de pruebas
```

Los scripts se pueden ejecutar desde cualquier carpeta: `codigo/_raiz.py` fija la carpeta del
proyecto como directorio de trabajo. Los nombres de archivo de las tablas siguientes están en `codigo/`.

## 1. Resumen del estado

| Qué se verifica | Estado |
|---|---|
| Tablas II–VI (conjuntos y operadores `mt`/`lt`) contra lo impreso | ✅ exacto (`test_paper_tables.py`) |
| Las **25 reglas del Apéndice** (5 intervenciones × 5) contra la imagen del original | ✅ exacto — **se corrigió un error grave, ver §4** |
| Ejemplo trabajado de las págs. 7–8 (Tabla VII, cada regla y la fila final, e\* = 10 s) | ✅ exacto |
| Estructura temporal: intervenciones a 7, 17, 27, 37, 47 s; verde efectivo ≤ 57 s | ✅ |
| Tabla I (modelo con ciclo fijo óptimo de Webster) | ✅ error medio 2.1 % (simulación) y 0.8 % (fórmula) |
| Tabla VIII (difuso vs. línea base), lectura **calibrada** | ⚠️ 16/16 celdas mejoran al ciclo fijo (Wilcoxon + Holm, p ≤ 3.1·10⁻⁵); error medio 9.2 %, máximo 18.6 % |
| Tabla VIII, lectura **literal** (A y Q tal como en el ejemplo) | ❌ inestable desde 360/1440 (§5) |

**El punto que sigue abierto** es cómo obtenía el programa original las entradas A y Q a partir
del estado de la simulación: el paper no lo dice y las lecturas literales no reproducen su
Tabla VIII (§5). Es la principal limitación de la réplica (§5 y §7).

---

### 1.1 Versión revisada (respuesta a la revisión «Avance 8»)

* Parámetros explícitos de las lecturas (`traffic_model.LITERAL` / `CALIBRADA`): ningún parámetro se ignora (`test_parametros.py`).
* Números aleatorios comunes (semilla *k* para todos los controladores), 20 réplicas en todas las tablas, desviación estándar muestral (n−1),
  pruebas exactas de Wilcoxon + Holm y Friedman (`estadistica.py`, `analisis_estadistico.py`).
* Comparadores que no son del paper: actuado por detector, difuso con centroide, ciclo fijo sin redondeo (`comparadores.py`).
* Efecto de borde del horizonte (`efecto_borde.py`), disparos agregados (`informe_agregado.py`), entorno y costo (`entorno.py`).
* `test_archivos_citados.py`: todo script, JSON, CSV y fuente LaTeX citado por el artículo existe y compila.
* `verificar_referencias.py`: comprueba cada DOI de `articulo_replica/referencias.bib` contra Crossref (título, primer autor, año, volumen, páginas); requiere internet y no forma parte de las comprobaciones.
* `python codigo/ejecutar_pruebas.py` corre 165 comprobaciones (132 de la réplica y 33 de la optimización); con `--rapido` recalcula además una Tabla VIII reducida.

---

## 2. Archivos

| Archivo | Qué hace |
|---|---|
| `paper_data.py` | Valores impresos del paper (Tablas I–VIII), transcritos de la **imagen** del original. |
| `fuzzy_logic.py` | Tablas II–IV, operadores `mt`/`lt`, las 25 reglas, inferencia min–max y decisión. `python codigo/fuzzy_logic.py` reproduce el ejemplo de la pág. 7. |
| `traffic_model.py` | Modelo de la intersección, ciclo fijo de Webster, fórmula de Webster, controlador difuso (`LITERAL`, `CALIBRADA`). |
| `run_experiments.py` | Tablas I y VIII con el protocolo oficial → `resultados/resultados_oficiales.json`. |
| `arrival_model_check.py` | Comprueba llegadas aleatorias vs. fijas contra la Tabla I → `resultados/llegadas_fijas_vs_aleatorias.json`. |
| `fidelity_audit.py` | Prueba las lecturas posibles de A y Q **sin tocar las reglas** → `resultados/fidelity_audit.json`. |
| `test_paper_tables.py` | 42 comprobaciones contra lo impreso en el paper. |
| `README_VSCODE.md`, `.vscode/`, `ejecutar_pruebas.py`, `informe_disparos.py`, `test_disparos.py`, `test_autos.py`, `muestras/` | **Avance de la simulación en VS Code:** 6 configuraciones F5, resumen de pruebas, panel de reglas y disparos, personalización didáctica (escenarios, reglas encendibles, explicación de cada decisión, autos a mano), informe CSV/PNG y ejemplos ya generados. |
| `sim_engine.py`, `test_sim_engine.py` | Motor paso a paso (1 s/tick) y su prueba de equivalencia con la simulación por lotes (10/10). |
| `intersection_view.py`, `simulador_gui.py`, `web_sim.py` | Simulador animado (Tkinter / navegador). |
| `plots.py`, `gen_fig_fuzzificacion.py`, `gen_fig_lt_explicacion.py`, `gen_fig_validacion.py`, `gen_fig_correcciones.py`, `diagrama_bloques.py` | Figuras (curvas de fuzzificación, validación contra lo impreso, Tablas I y VIII). |
| `build_avance5.py` → `avance5_validacion_replica.pdf` | **Avance 5**: validación de la réplica frente al paper original (14 págs., curvas de fuzzificación en la Sección 2). Reemplaza a los avances 1–4. |
| `articulo_replica/` (+ `articulo_ieee_overleaf_v11.zip`) | Artículo IEEE (IEEEtran), segundo avance, 15 págs., para Overleaf (`articulo_replica_para_docente.pdf` = vista previa). Figuras: `gen_fig_articulo.py`, `gen_fig_articulo2.py`, `gen_fig_articulo3.py`, `gen_fig_articulo4.py` (figuras del simulador, una por apartado); estadística (IC 95 %): `analisis_estadistico.py` → `resultados/analisis_estadistico.json`; tablas: `gen_tablas_latex.py`, `verificar_formulas.py` (comprobación numérica de las deducciones), `gen_tabla_intervenciones.py` (decisiones por intervención), `gen_tabla_180.py` (las 180 reglas escritas una por una, con las 25 del autor en verde → `resultados/reglas_180.csv`); reducción de reglas: `ablacion_reglas.py` → `resultados/ablacion_reglas.json`; chequeo: `check_latex.py`. |
| `referencia/LEEME.md` | Cita del paper original en inglés (única fuente de verdad); el PDF debe obtenerse de IEEE. |
| `notebooks/pappis_replica.ipynb` | Notebook para experimentar. |
| `archivo/` | Material histórico: el primer controlador del proyecto (16 reglas) y `old_fl.py`, el módulo anterior a las correcciones, que solo usa `gen_fig_correcciones.py` para mostrar qué se corrigió. |

---

## 3. Cómo ejecutar

```bash
pip install numpy matplotlib reportlab   # núcleo + PDF (flask para web_sim, imageio para video)
python codigo/test_paper_tables.py             # contra lo impreso: debe terminar en "TODO OK"
python codigo/test_sim_engine.py               # 10/10
python codigo/fuzzy_logic.py                   # ejemplo de la pág. 7
python codigo/run_experiments.py               # protocolo oficial, ~2 min  (--quick para probar)
python codigo/fidelity_audit.py                # auditoría de interpretaciones, ~25 min
python codigo/plots.py                         # figuras en figures/
python codigo/gen_fig_fuzzificacion.py && python codigo/gen_fig_validacion.py
python codigo/build_avance5.py                 # avance5_validacion_replica.pdf (requiere reportlab)
```

**Protocolo oficial:** 20 réplicas × 7200 s por combinación de caudal, 16 combinaciones, semilla
base 0 (el difuso usa base + 100000; fijo y difuso no comparten llegadas). El paper no
indica el número de réplicas ("many runs"), solo los 7200 s por corrida.

---

## 4. Qué viene del paper y cómo se implementó

### 4.1 Modelo (págs. 2–3)
* Dos calles unidireccionales, un carril, sin giros; flujo de saturación 3600 veh/h = 1 veh/s.
* Llegadas: cada segundo se compara un número pseudoaleatorio con la tasa media (Bernoulli).
* Tiempo perdido de 10 s por ciclo → 5 s sin descarga en cada cambio de fase.
* Retardo medio `d_m = D / Σ q_n`; cada vehículo acumula (instante de cruce − instante de llegada).
* Ciclo fijo: `C0 = (1.5 L + 5)/(1 − Y)`, `g_i = (y_i/Y)(C0 − L)`, redondeado a segundos enteros
  (el modelo avanza en unidades de 1 s). La columna "vehicle-actuated" de la Tabla VIII **repite**
  la columna "Model" de la Tabla I (pág. 3), por eso la línea base es el ciclo fijo simulado.
* La columna "Formula" de la Tabla I se reproduce con la fórmula de Webster
  `d = C(1−λ)²/(2(1−λX)) + X²/(2q(1−X)) − 0.65 (C/q²)^{1/3} X^{2+5λ}` ponderada por flujo
  (`traffic_model.webster_delay_formula`).

### 4.2 Controlador (págs. 3–8 y Apéndice)
* Intervenciones a los 7, 17, 27, 37 y 47 s del verde efectivo; en cada una se decide la
  extensión e\* ∈ 0..10 s. Si e\* = 10 se vuelve a intervenir 10 s después; si e\* < 10 el verde
  termina tras e\* s; si todo el vector es < 0.5 se cambia de fase de inmediato.
  Verde efectivo = 7 + Σ e\* ≤ 57 s.
* Cada regla `si T=… y A=mt(…) y Q=lt(…) entonces E=…` aporta
  `min(μ_T(e), μ_mt(A)(β_e), μ_lt(Q)(q_e), μ_E(e))` para cada e = 1..10 (T es la extensión
  candidata); las 5 reglas se unen con `max`. Se elige el e con mayor grado y, ante empate, **el
  mayor** e (pág. 8). No hay centroide.
* Supuestos fuera del universo impreso: `lt(·)(q) = 1` para q < 4 (cola menor que el primer
  elemento de la Tabla IV); `mt(·)(0) = 0`.

### 4.3 Registro de correcciones de fidelidad

| # | Corrección | Efecto |
|---|---|---|
| 1 | Operador `mt` (pág. 4, Tabla V): 0 para `a < x0`. | Octubre 2026 (previa). |
| 2 | Conjunto `verylong` de colas: pico en q = 28 (Tabla IV). | Octubre 2026 (previa). |
| 3 | **Reglas de las intervenciones 27, 37 y 47 s.** La transcripción anterior (7 reglas en la de 27 s, 2 en la de 47 s, 24 en total) venía del texto OCR, que mezcla las dos columnas de la pág. 716. Con la **imagen** del original: 5 reglas por intervención, 25 en total (como dice el texto de la pág. 6). | Cambia por completo el comportamiento del controlador en verdes largos. |
| 4 | **Temporización.** Se decidía tras 8 s de verde (y hasta 58 s en total); ahora tras exactamente 7 s y como máximo 57 s, como dice el paper. | Menos verde mínimo. |
| 5 | **Doble conteo de arribos.** Al terminar el verde difuso se reprocesaba el segundo final, contando dos veces sus arribos (entre 6 % y 12 % más vehículos que los generados, solo en el difuso). Ahora cada segundo se procesa una vez. | El difuso dejaba de ser comparable con el ciclo fijo. |
| 6 | Verdes del ciclo fijo en segundos enteros; Tabla I con fórmula de Webster real (antes se imprimía una fórmula incorrecta). | Tabla I más cercana al paper. |

---

## 5. Interpretaciones: lo que el paper no precisa

Las reglas, los conjuntos y los operadores son datos del paper. Lo que **no** está especificado
es cómo su programa calculaba, en cada intervención,

* **A** (vehículos que cruzan el punto crítico en e s), y
* **Q** (cola del brazo en rojo).

El ejemplo de las págs. 7–8 usa `β_e` = arribos acumulados en la ventana y `β'_e = Q + arribos
acumulados del brazo en rojo`. Pero es una ilustración con vectores dados; no dice qué valor
tiene Q cuando la simulación avanza (¿cola total?, ¿llegados en esta fase?), ni cómo cuentan
en A los vehículos que ya esperan en el brazo con verde.

`fidelity_audit.py` prueba las 8 combinaciones razonables, con las reglas fijas, y mide el error
frente a la Tabla VIII (20 réplicas × 7200 s, números aleatorios comunes; error medio ± desviación
estándar entre réplicas):

| A | Q evaluada en | cola Q | error medio | máximo | mejor que el fijo |
|---|---|---|--:|--:|--:|
| arribos acumulados | predicha β′ | total | 641.3 % ± 54.5 | 2620 % | 5/16 (≈ `LITERAL`) |
| arribos acumulados | predicha β′ | desde inicio del verde | 331.4 % ± 42.9 | 1897 % | 5/16 |
| arribos acumulados | actual | total | 569.1 % ± 43.9 | 2607 % | 5/16 |
| arribos acumulados | actual | desde inicio del verde | 218.9 % ± 29.0 | 1142 % | 5/16 |
| cruces (limit. por saturación) | predicha β′ | total | 418.1 % ± 47.2 | 2398 % | 11/16 |
| cruces (limit. por saturación) | predicha β′ | desde inicio del verde | 178.0 % ± 27.1 | 1141 % | 11/16 |
| cruces (limit. por saturación) | actual | total | 371.1 % ± 44.0 | 2341 % | 12/16 |
| cruces (limit. por saturación) | actual | desde inicio del verde | 9.2 % ± 1.5 | 19 % | 16/16 ◀ `CALIBRADA` |

Las dos lecturas que se dejan en el código:

* **`LITERAL`** — A = arribos acumulados; Q = cola total evaluada en `β'_e`. Es lo que dice el
  ejemplo, pero con colas totales reales el controlador solo extiende cuando el brazo en rojo
  tiene ≲ 5 vehículos (`lt(verysmall)`), así que en cuanto los flujos suben la fase verde se
  corta a ~9 s, la capacidad no alcanza y el sistema se satura.
* **`CALIBRADA`** — A = vehículos que realmente cruzan (limitados por 1 veh/s, lo que incluye la
  cola del verde); Q = vehículos llegados al brazo en rojo desde que empezó el verde actual,
  en su valor actual. **Se eligió por ser la única que reproduce la Tabla VIII en todo el
  rango**, no porque el texto del paper la indique.

> **Advertencia sobre la lectura calibrada.** Es una inferencia a partir de los resultados, no una
> cita del paper. Además es sensible: contar la cola completa, o añadir los ~2 vehículos
> llegados durante el tiempo perdido, ya la vuelve inestable. Debe presentarse
> como una inferencia por falta de datos.

---

## 6. Resultados oficiales (20 réplicas × 7200 s, números aleatorios comunes, lectura calibrada)

**Tabla I** (ciclo fijo; error medio 2.1 % simulación, 0.8 % fórmula; mayor desviación 360/2160: −7.9 %).

**Tabla VIII** (retardo medio en s/veh; la columna «mejora paper» se recalcula con los retardos impresos):

| N–S | E–W | fijo (sim.) | fijo (paper) | **difuso (sim.)** | difuso (paper) | error | mejora sim. | mejora paper |
|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 360 | 360 | 7.29 | 7.2 | **5.58** | 5.7 | -2.2 % | +23 % | +21 % |
| 360 | 720 | 7.48 | 7.4 | **5.96** | 6.1 | -2.2 % | +20 % | +18 % |
| 360 | 1080 | 7.76 | 7.9 | **6.25** | 6.6 | -5.4 % | +19 % | +16 % |
| 360 | 1440 | 8.24 | 8.4 | **6.69** | 7.3 | -8.4 % | +19 % | +13 % |
| 360 | 1800 | 9.19 | 9.3 | **7.39** | 8.4 | -12.0 % | +20 % | +10 % |
| 360 | 2160 | 11.33 | 12.3 | **8.69** | 10.0 | -13.1 % | +23 % | +19 % |
| 360 | 2520 | 16.17 | 15.8 | **12.00** | 13.6 | -11.7 % | +26 % | +14 % |
| 720 | 720 | 9.36 | 9.7 | **6.57** | 7.4 | -11.3 % | +30 % | +24 % |
| 720 | 1080 | 10.63 | 10.8 | **7.53** | 8.8 | -14.4 % | +29 % | +19 % |
| 720 | 1440 | 12.49 | 12.7 | **9.33** | 10.9 | -14.4 % | +25 % | +14 % |
| 720 | 1800 | 15.35 | 15.9 | **12.19** | 14.1 | -13.5 % | +21 % | +11 % |
| 720 | 2160 | 21.21 | 21.8 | **17.64** | 18.5 | -4.6 % | +17 % | +15 % |
| 1080 | 1080 | 13.53 | 13.6 | **9.76** | 12.0 | -18.6 % | +28 % | +12 % |
| 1080 | 1440 | 17.77 | 17.9 | **13.79** | 15.4 | -10.4 % | +22 % | +14 % |
| 1080 | 1800 | 25.54 | 25.8 | **22.34** | 21.6 | +3.4 % | +13 % | +16 % |
| 1440 | 1440 | 26.86 | 27.3 | **23.17** | 22.9 | +1.2 % | +14 % | +16 % |

Mejora respecto del ciclo fijo en **16/16** celdas (paper: 16/16; Wilcoxon exacto pareado con Holm, p ≤ 3.1·10⁻⁵). Error relativo frente al
paper: medio 9.2 %, máximo 18.6 % (1080/1080); sesgo medio del difuso −8.6 % (IC 95 % −12.0 a −5.3), del ciclo fijo −1.6 %.
Las celdas pesadas (1080/1800 y 1440/1440) quedan a ±3.4 %. El difuso simulado es sistemáticamente algo más bajo que el publicado
en caudales medios; esa diferencia no se corrigió con ningún ajuste de reglas.

**Comparadores que no son del paper** (`comparadores.py`, mismo protocolo): media de los 16 flujos fijo 13.76 s, difuso 10.93 s, **actuado por detector 10.88 s**, difuso con centroide 230.9 s. El difuso es mejor que el actuado en 10 flujos (caudales bajos y medios), peor en 5 (caudales altos, hasta +29 %) y no se distingue en 1; en promedio son indistinguibles (Wilcoxon sobre flujos, p = 0.50).

Figuras: `figures/fig4_delay_comparison.png` (calibrada) y `fig4b_delay_comparison_literal.png`.

---

## 7. Límites honestos

1. No se dispone del código ni del generador aleatorio de 1977; la réplica es estadística,
   no dígito a dígito.
2. La lectura calibrada de A y Q es una inferencia (§5).
3. El paper no da el número de réplicas ni cómo se discretiza el tiempo perdido; se usó 5 s + 5 s.
4. Tabla I: 360/2160 queda 8 % por debajo (verde de 8.1 s redondeado a 8 s).
5. Los PDFs, el informe LaTeX y los zips anteriores usan las reglas mal transcritas y **no deben
   citarse**; no se incluyen en este repositorio y habría que regenerarlos cuando se cierre la réplica.

## 8. Referencia

Pappis, C. P., & Mamdani, E. H. (1977). A Fuzzy Logic Controller for a Traffic Junction.
*IEEE Trans. Syst., Man, Cybern.*, 7(10), 707–716.

---

## 9. Mejora del controlador: optimización (FLC-O)

El objetivo del repositorio es mejorar el controlador de 1977 con un protocolo que separa entrenamiento, validación y prueba. Las secciones 1 a 8 describen la réplica de partida y no cambian. El manuscrito de la mejora es `articulo/main.tex` (9 páginas) con su suplemento `articulo/suplemento.tex` (3 páginas); las cifras de ambos salen de `resultados/opt/evaluacion_final.json`.

**Archivos (todos en `codigo/`):**

| Archivo | Qué hace |
|---|---|
| `sim_batch.py` | Simulador vectorizado: simula cientos de escenarios a la vez y da, escenario por escenario, exactamente el mismo retardo que `traffic_model.py` (`test_sim_batch.py`, diferencia 0 con 6 controladores y las dos convenciones de retardo). Unas 20 veces más rápido. |
| `opt_controladores.py`, `opt_flc.py`, `opt_flc2.py`, `opt_politicas.py` | Controladores: ciclo fijo de Webster, actuado por detector, presión máxima, Pappis y Mamdani (y su versión afinada), **FLC-O** (27 reglas, 42 parámetros) y la política neuronal de referencia. |
| `opt_es.py` | CMA-ES propio, con evaluación en paralelo y puntos de control. |
| `opt_mdp.py` | Política óptima por programación dinámica para caudales conocidos (sin ver las llegadas futuras), validada contra la simulación. |
| `opt_entrenar.py`, `opt_entrenar_modelo.py`, `opt_validar.py` | Escenarios de entrenamiento y validación, entrenamiento y selección con validación. |
| `opt_evaluacion_final.py`, `opt_evaluar.py` | Evaluación en cuatro conjuntos de prueba con Wilcoxon pareado y Holm → `resultados/opt/evaluacion_final.json`. |
| `gen_tablas_opt.py`, `gen_fig_opt.py`, `gen_matriz_opt.py` | Tablas, cifras del texto, figuras y matriz de respuesta de esta versión. |
| `simulador_opt.py` | Compara Pappis y Mamdani con FLC-O sobre las mismas llegadas (figura, GIF o ventana). |
| `test_sim_batch.py`, `test_opt.py`, `test_archivos_citados_opt.py` | 10 + 11 + 12 comprobaciones (en total, `ejecutar_pruebas.py` corre 165). |

**Resultados** (retardo medio en s/veh, incluye la espera residual al final del horizonte; FLC-O con vista adelante de 10 s, como supone el modelo original):

| Conjunto de prueba | Pappis y Mamdani | Actuado afinado | FLC-O | FLC-O frente a Pappis | FLC-O frente al actuado afinado |
|---|---|---|---|---|---|
| Oficial (16 pares de la Tabla VIII × 20 réplicas) | 10.95 | 9.63 | 7.91 | −27.8 % | −17.8 % |
| 64 caudales no vistos | 10.40 | 9.17 | 7.40 | −28.8 % | −19.3 % |
| Demanda variable | 8.65 | 8.07 | 6.07 | −29.8 % | −24.7 % |
| Cerca de la saturación | 105.87 | 24.13 | 24.29 | −77.1 % | +0.7 % (empate) |

En el conjunto oficial FLC-O es significativamente mejor que Pappis y Mamdani y que el actuado afinado en los 16 pares (Wilcoxon pareado con Holm) y no es peor en ninguno. La política óptima por programación dinámica con caudales conocidos da 9.35.

**Límites que el manuscrito declara:**

1. La mejora depende de la vista adelante de 10 s (llegadas de los próximos 10 s conocidas), que es un supuesto del modelo original. Sin ella, FLC-O causal da 9.97 (3.5 % peor que el actuado afinado) y la mejor variante causal, una política neuronal, da 9.46 (1.7 % mejor).
2. Cerca de la saturación FLC-O empata con el actuado afinado; no lo supera.
3. Todo es simulación de una intersección aislada con llegadas de Bernoulli; no hay datos de campo.
4. El mejor resultado usa un verde mínimo de 3 s; con 5 s da 8.21 y con 7 s da 8.60 en el conjunto oficial. Si 3 s no fuera admisible en la práctica, esas son las cifras que corresponden.
5. El retardo corregido (con espera residual) no es comparable con el de la Tabla VIII del original.

**Reproducir:** `python codigo/ejecutar_pruebas.py` (165 comprobaciones), `python codigo/opt_evaluacion_final.py` (evaluación completa), `python codigo/gen_tablas_opt.py && python codigo/gen_fig_opt.py` (tablas y figuras), `python codigo/simulador_opt.py` (comparación visual). Los modelos entrenados están en `resultados/opt/` (`modelos_finales.json` indica cuál es cuál). El paso a paso de las configuraciones F5 está en `README_VSCODE.md`.
