# Controlador de semáforos con lógica difusa: réplica de Pappis y Mamdani (1977) y su optimización

Réplica, validación, simulador gráfico y —en la rama `optimizacion`— mejora del controlador de semáforos con lógica difusa de

> C. P. Pappis y E. H. Mamdani, «A Fuzzy Logic Controller for a Traffic Junction»,
> *IEEE Trans. Syst., Man, Cybern.*, vol. SMC-7, no. 10, pp. 707–717, oct. 1977.

El controlador decide, cada 10 s de verde, cuánto extender la luz verde de una intersección aislada de dos calles unidireccionales.
**Usa las 25 reglas exactas del artículo original** (5 por cada intervención, a los 7, 17, 27, 37 y 47 s), leídas de la imagen de
las páginas del original y verificadas por pruebas automáticas.

> **Autores:** Raul Nolberto Quispe Saya y Kevin Luis Valero Ccacya
> Escuela Profesional de Ingeniería Electrónica, Universidad Nacional de San Agustín de Arequipa.

## Qué contiene

| Carpeta | Contenido |
|---|---|
| `codigo/` | Modelo de tráfico, controlador difuso (25 reglas), simulador paso a paso, simulador gráfico y web, pruebas y generadores de figuras y tablas. |
| `resultados/` | Resultados de la réplica en JSON (Tablas I y VIII, auditoría, estadística, verificación de fórmulas) y las 180 reglas en `reglas_180.csv`; en `resultados/opt/`, los modelos entrenados y la evaluación final de la optimización. |
| `articulo_ieee/` | Artículo de la réplica en formato IEEE (IEEEtran) listo para compilar en Overleaf, con su PDF. |
| `articulo_opt/` | Artículo (9 páginas) y suplemento (3 páginas) de la versión de optimización, con sus PDF, tablas y figuras. |
| `figures/`, `muestras/` | Figuras, captura de la ventana, video de ejemplo y CSV de disparos de reglas. |
| `docs/` | Guía técnica (`README_TECNICO.md`), guía de VS Code y el PDF del avance 5. |
| `notebooks/` | Cuaderno Jupyter con las verificaciones. |
| `.vscode/` | Configuraciones de F5 y tareas para ejecutar todo desde Visual Studio Code. |
| `referencia/` | Cita del artículo original (el PDF no se incluye: pertenece a IEEE). |
| `archivo/` | Material histórico, no vigente: el primer controlador del proyecto (16 reglas, centroide) y un módulo anterior a las correcciones. |

## Resultados

Con las 25 reglas, 20 réplicas de 7200 s por combinación de flujos y números aleatorios comunes (la réplica *k* usa la semilla *k* en todos los controladores):

- **Verificación contra lo impreso:** conjuntos difusos, operadores «más que» y «menos que», las 25 reglas y el ejemplo trabajado del
  artículo coinciden con el original (diferencia 0.000).
- **Tabla I** (modelo de ciclo fijo con ajustes de Webster): error relativo medio de 2.1 % (simulación) y 0.8 % (fórmula).
- **Tabla VIII** (difuso frente a ciclo fijo): el difuso mejora al ciclo fijo en **16 de 16** combinaciones de flujo (Wilcoxon exacto pareado
  con corrección de Holm, p ≤ 3.1·10⁻⁵), con un error medio de 9.2 % y máximo de 18.6 % respecto de los retardos publicados. El retardo del
  difuso queda en promedio 8.6 % por debajo del publicado (IC 95 % de −12.0 a −5.3); esa discrepancia se documenta y no se explica.
- **Comparadores que no son del paper** (`comparadores.py`): frente a un controlador actuado por detector (hueco de 3 s, verde de 7 a 57 s) el
  difuso es mejor en 10 flujos (caudales bajos y medios), peor en 5 (caudales altos, hasta +29 %) e indistinguible en 1; en promedio de los
  16 flujos son equivalentes (10.93 frente a 10.88 s/veh). La defuzzificación por centroide degrada el sistema (230.9 s) y todos los
  subconjuntos reducidos de reglas son significativamente peores que las 25 reglas (con 15 reglas, +1.6 %).
- **Inferencia por falta de datos:** el artículo no dice cómo se miden los arribos *A* y la cola *Q* en la simulación. De ocho lecturas
  probadas, solo una («calibrada») reproduce la Tabla VIII; se presenta como una inferencia, no como una cita del original.

## Versión de optimización (rama `optimizacion`)

Además de replicar el controlador de 1977, esta rama busca un sistema difuso mejor. **FLC-O** es un controlador difuso de 27 reglas y 42
parámetros que decide cada segundo si cambiar de fase; sus parámetros se entrenan con CMA-ES sobre caudales sorteados y se prueban en
conjuntos que no se usaron para entrenar, con una medida del retardo que cuenta toda la espera hasta el final del horizonte. El manuscrito
es `articulo_opt/main.tex` y su suplemento, `articulo_opt/suplemento.tex`.

Retardo medio en s/veh (FLC-O con la vista adelante de 10 s que supone el modelo original):

| Conjunto de prueba | Pappis y Mamdani | Actuado afinado | FLC-O | FLC-O frente a Pappis | FLC-O frente al actuado afinado |
|---|---|---|---|---|---|
| Oficial (16 pares de la Tabla VIII × 20 réplicas) | 10.95 | 9.63 | 7.91 | −27.8 % | −17.8 % |
| 64 caudales no vistos | 10.40 | 9.17 | 7.40 | −28.8 % | −19.3 % |
| Demanda variable | 8.65 | 8.07 | 6.07 | −29.8 % | −24.7 % |
| Cerca de la saturación | 105.87 | 24.13 | 24.29 | −77.1 % | +0.7 % (empate) |

En el conjunto oficial FLC-O es significativamente mejor que los dos en los 16 pares (Wilcoxon pareado con Holm). **Límites:** la mejora
depende de la vista adelante (sin ella, el difuso causal queda 3.5 % peor que el actuado afinado y la mejor variante causal, 1.7 % mejor);
cerca de la saturación hay empate, no mejora; todo es simulación de una intersección aislada; el mejor resultado usa un verde mínimo de 3 s
(con 5 s, 8.21; con 7 s, 8.60). El detalle está en la sección 9 de `docs/README_TECNICO.md` y en el artículo.

```bash
python codigo/simulador_opt.py                    # compara Pappis y Mamdani con FLC-O sobre las mismas llegadas (ventana)
python codigo/opt_evaluacion_final.py             # evaluación completa en los cuatro conjuntos de prueba (varios minutos)
python codigo/gen_tablas_opt.py                   # regenera tablas y cifras del artículo de optimización
python codigo/opt_entrenar_modelo.py --modelo flcopt --gmin 3 --max-green 90 --suma-max 3300 --ref actuado_af --out resultados/opt/mi_modelo.json
```

## Instalación

Se necesita Python 3.10 o superior (el simulador de ventana usa Tkinter).

```bash
# Linux / macOS (en Ubuntu: sudo apt install python3-venv python3-tk)
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

```powershell
# Windows (PowerShell)
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Cómo usarlo

```bash
python codigo/ejecutar_pruebas.py      # resumen de validación: pruebas y tablas (segundos)
python codigo/simulador_gui.py         # simulador gráfico con calle, reglas y disparos
python codigo/web_sim.py               # simulador web en http://localhost:8000
python codigo/informe_disparos.py      # CSV y PNG de qué reglas disparan
python codigo/run_experiments.py       # Tablas I y VIII oficiales (unos 2 min)
python codigo/comparadores.py          # actuado por detector, centroide y ciclo fijo sin redondeo
```

Los scripts se pueden ejecutar desde cualquier carpeta. En Visual Studio Code, abra la carpeta y use **Ejecutar y depurar (F5)**;
`docs/README_VSCODE.md` explica el paso a paso.

### El simulador

La ventana muestra la calle con autos que respetan la distancia entre sí, semáforos de tres luces y, para cada decisión, las cinco reglas
de la intervención con su activación, la regla que dispara (★), el vector de grados y los disparos acumulados de las 25 reglas. Tiene
opciones para explicar: escenarios predefinidos, encender y apagar reglas, pausar en cada decisión, explicación de cada decisión en
palabras simples, agregar autos a mano y ocultar o mostrar apartados.

![Simulador](muestras/captura_simulador_gui.png)

### Artículo

`articulo_ieee/` contiene el manuscrito (`main.tex`, 15 páginas, con su PDF), el material suplementario (`suplemento.tex`: lista literal de
las 180 reglas y los apartados del simulador por separado), `referencias.bib`, las tablas y las figuras. En Overleaf: suba la carpeta como
proyecto, deje `main.tex` como documento principal y compile con pdfLaTeX. Las tablas y figuras se regeneran con los scripts
`codigo/gen_tablas_latex.py`, `gen_tabla_180.py` y `gen_fig_*.py`. Las versiones exactas de Python y NumPy de los resultados están en
`requirements-resultados.txt`.

## Pruebas

`python codigo/ejecutar_pruebas.py` corre 165 comprobaciones automáticas (132 de la réplica y 33 de la optimización):

| Prueba | Qué verifica |
|---|---|
| `test_paper_tables.py` (42) | Conjuntos, operadores, las 25 reglas, ejemplo de la Tabla VII y estructura temporal frente a lo impreso. |
| `test_sim_engine.py` (10) | El simulador paso a paso da el mismo resultado que la simulación por lotes. |
| `test_disparos.py` (22) | El panel de reglas y disparos muestra lo que calcula el controlador. |
| `test_autos.py` (13) | Los autos nunca se superponen, apagar reglas afecta el resultado, y las explicaciones coinciden con las decisiones. |
| `test_parametros.py` (14) | Las lecturas de las entradas A y Q son explícitas y ningún parámetro se ignora; `mt`/`lt` coinciden con la Tabla V; la contabilidad del retardo. |
| `test_estadistica.py` (10) | Wilcoxon, Friedman, Holm, t de Student y χ² contra valores conocidos. |
| `verificar_formulas.py` (9) | Las deducciones del artículo contra cálculos independientes. |
| `test_archivos_citados.py` (12) | Todo script, JSON, CSV y fuente LaTeX citado por el artículo existe y compila. |
| `test_sim_batch.py` (10) | El simulador vectorizado reproduce exactamente al de referencia (6 controladores, 2 convenciones de retardo). |
| `test_opt.py` (11) | CMA-ES, partición de Ruspini, programación dinámica, FLC-O y Pappis afinado. |
| `test_archivos_citados_opt.py` (12) | Todo archivo citado por el artículo y el suplemento de optimización existe. |
| `verificar_referencias.py` | Comprueba cada DOI de `referencias.bib` contra Crossref (requiere internet; no cuenta entre las comprobaciones). |

Con `--rapido` recalcula además una Tabla VIII reducida (unos 20 s).

## Más documentación

- `docs/README_TECNICO.md`: detalle técnico, decisiones y correcciones de la transcripción.
- `docs/README_VSCODE.md`: uso desde Visual Studio Code y personalización del simulador.
- `docs/avance5_validacion_replica.pdf`: informe de validación con las curvas de fuzzificación.
