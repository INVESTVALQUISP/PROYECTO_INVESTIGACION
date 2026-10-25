# Réplica del *Fuzzy Logic Controller for a Traffic Junction* (Pappis & Mamdani, 1977)

> C. P. Pappis y E. H. Mamdani, *A Fuzzy Logic Controller for a Traffic Junction*,
> IEEE Trans. Syst., Man, Cybern., vol. SMC-7, no. 10, pp. 707–716, 1977.

**Alcance actual:** replicar el paper original lo más fielmente posible, para poder
entenderlo y reproducirlo. No se propone ningún cambio al método (reglas, conjuntos,
operadores, regla de decisión): los controladores alternativos y el re-afinado de reglas
hechos antes no forman parte de este repositorio (se calcularon con reglas mal transcritas y quedaron descartados).

**Fuente de verdad:** únicamente el paper **original en inglés** (PDF `01 pappis1977`, págs. 707–716),
leído sobre la **imagen** de cada página. La traducción al español (hecha por una IA) **no se usa**
como referencia: contiene errores verificados, p. ej. las reglas de las intervenciones de 27 s
(le asigna `long/mt(many)/lt(medium)` y `verylong/mt(too many)/lt(long)`, que en el original son
de la de 37 s) y de 37 s. Todos los valores de `paper_data.py` y las 25 reglas salen del original.

---

## Estructura de carpetas

```
raíz del repositorio/
├── codigo/          todo el código Python (modelo, controlador, simulador, pruebas, generadores)
├── resultados/      JSON de resultados (Tablas I y VIII, auditoría, llegadas, reducción de reglas)
├── figures/         figuras generadas por plots.py y gen_fig_*.py
├── muestras/        ejemplos listos para mostrar (video, CSV de disparos, captura del simulador)
├── articulo_ieee/   artículo IEEE para Overleaf (main.tex, tablas, figuras, PDF)
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
| Tabla VIII (difuso vs. línea base), lectura **calibrada** | ⚠️ 16/16 celdas mejoran al ciclo fijo; error medio 9.3 %, máximo 19.8 % |
| Tabla VIII, lectura **literal** (A y Q tal como en el ejemplo) | ❌ inestable desde 360/1440 (§5) |

**El punto que sigue abierto** es cómo obtenía el programa original las entradas A y Q a partir
del estado de la simulación: el paper no lo dice y las lecturas literales no reproducen su
Tabla VIII (§5). Es la principal limitación de la réplica (§5 y §7).

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
| `articulo_ieee/` (+ `articulo_ieee_overleaf_v9.zip`) | Artículo IEEE (IEEEtran), segundo avance, 15 págs., para Overleaf (`articulo_replica_para_docente.pdf` = vista previa). Figuras: `gen_fig_articulo.py`, `gen_fig_articulo2.py`, `gen_fig_articulo3.py`, `gen_fig_articulo4.py` (figuras del simulador, una por apartado); estadística (IC 95 %): `analisis_estadistico.py` → `resultados/analisis_estadistico.json`; tablas: `gen_tablas_latex.py`, `verificar_formulas.py` (comprobación numérica de las deducciones), `gen_tabla_intervenciones.py` (decisiones por intervención), `gen_tabla_180.py` (las 180 reglas escritas una por una, con las 25 del autor en verde → `resultados/reglas_180.csv`); reducción de reglas: `ablacion_reglas.py` → `resultados/ablacion_reglas.json`; chequeo: `check_latex.py`. |
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
| 3 | **Reglas de las intervenciones 27, 37 y 47 s.** La transcripción anterior (7 reglas en la de 27 s, 2 en la de 47 s, 24 en total) venía del texto OCR, que mezcla las dos columnas de la pág. 716; la traducción al español tenía además otros errores en las intervenciones de 27 y 37 s. Con la **imagen** del original: 5 reglas por intervención, 25 en total (como dice el texto de la pág. 6). | Cambia por completo el comportamiento del controlador en verdes largos. |
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
frente a la Tabla VIII (10 réplicas × 7200 s):

| A | Q evaluada en | cola Q | error medio | máximo | mejor que el fijo |
|---|---|---|--:|--:|--:|
| arribos acumulados | predicha β′ | total | 631.0 % | 2622.5 % | 5/16 (≈ `LITERAL`) |
| arribos acumulados | predicha β′ | desde inicio del verde | 323.1 % | 1869.0 % | 6/16 |
| arribos acumulados | actual | total | 566.6 % | 2609.7 % | 5/16 |
| arribos acumulados | actual | desde inicio del verde | 227.6 % | 1184.9 % | 6/16 |
| cruces (limit. por saturación) | predicha β′ | total | 421.0 % | 2403.6 % | 11/16 |
| cruces (limit. por saturación) | predicha β′ | desde inicio del verde | 175.4 % | 1161.9 % | 11/16 |
| cruces (limit. por saturación) | actual | total | 374.1 % | 2362.4 % | 12/16 |
| cruces (limit. por saturación) | actual | desde inicio del verde | 9.3 % | 19.3 % | 16/16 ◀ `CALIBRADA` |

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

## 6. Resultados oficiales (20 réplicas × 7200 s, lectura calibrada)

**Tabla I** (ciclo fijo; error medio 2.1 % simulación, 0.8 % fórmula; mayor desviación 360/2160: −7.9 %).

**Tabla VIII** (retardo medio en s/veh):

| N–S | E–W | fijo (sim.) | fijo (paper) | **difuso (sim.)** | difuso (paper) | error | mejora sim. | mejora paper |
|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 360 | 360 | 7.29 | 7.2 | **5.63** | 5.7 | -1.2 % | +23 % | +21 % |
| 360 | 720 | 7.48 | 7.4 | **5.97** | 6.1 | -2.1 % | +20 % | +18 % |
| 360 | 1080 | 7.76 | 7.9 | **6.30** | 6.6 | -4.5 % | +19 % | +16 % |
| 360 | 1440 | 8.24 | 8.4 | **6.72** | 7.3 | -7.9 % | +18 % | +13 % |
| 360 | 1800 | 9.19 | 9.3 | **7.36** | 8.4 | -12.3 % | +20 % | +10 % |
| 360 | 2160 | 11.33 | 12.3 | **8.68** | 10.0 | -13.2 % | +23 % | +19 % |
| 360 | 2520 | 16.17 | 15.8 | **12.17** | 13.6 | -10.5 % | +25 % | +14 % |
| 720 | 720 | 9.36 | 9.7 | **6.55** | 7.4 | -11.5 % | +30 % | +24 % |
| 720 | 1080 | 10.63 | 10.8 | **7.52** | 8.8 | -14.6 % | +29 % | +19 % |
| 720 | 1440 | 12.49 | 12.7 | **9.16** | 10.9 | -16.0 % | +27 % | +14 % |
| 720 | 1800 | 15.35 | 15.9 | **12.10** | 14.1 | -14.2 % | +21 % | +11 % |
| 720 | 2160 | 21.21 | 21.8 | **17.49** | 18.5 | -5.5 % | +18 % | +15 % |
| 1080 | 1080 | 13.53 | 13.6 | **9.62** | 12.0 | -19.8 % | +29 % | +12 % |
| 1080 | 1440 | 17.77 | 17.9 | **13.63** | 15.4 | -11.5 % | +23 % | +14 % |
| 1080 | 1800 | 25.54 | 25.8 | **22.04** | 21.6 | +2.0 % | +14 % | +16 % |
| 1440 | 1440 | 26.86 | 27.3 | **23.18** | 22.9 | +1.2 % | +14 % | +16 % |

Mejora respecto del ciclo fijo en **16/16** celdas (paper: 16/16). Error relativo frente al
paper: medio 9.3 %, máximo 19.8 % (1080/1080). Las celdas pesadas (1080/1800 y 1440/1440)
quedan a ±2 %. El difuso simulado es sistemáticamente algo más bajo que el publicado
en caudales medios; esa diferencia no se corrigió con ningún ajuste de reglas.

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
