# Réplica del controlador de lógica difusa de Pappis y Mamdani (1977)

Réplica, validación y simulador gráfico del controlador de semáforos con lógica difusa de

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
| `resultados/` | Resultados de la réplica en JSON (Tablas I y VIII, auditoría, estadística, verificación de fórmulas) y las 180 reglas en `reglas_180.csv`. |
| `articulo_ieee/` | Artículo en formato IEEE (IEEEtran) listo para compilar en Overleaf, con su PDF. |
| `figures/`, `muestras/` | Figuras, captura de la ventana, video de ejemplo y CSV de disparos de reglas. |
| `docs/` | Guía técnica (`README_TECNICO.md`), guía de VS Code y el PDF del avance 5. |
| `notebooks/` | Cuaderno Jupyter con las verificaciones. |
| `.vscode/` | Configuraciones de F5 y tareas para ejecutar todo desde Visual Studio Code. |
| `referencia/` | Cita del artículo original (el PDF no se incluye: pertenece a IEEE). |
| `archivo/` | Material histórico, no vigente: el primer controlador del proyecto (16 reglas, centroide) y un módulo anterior a las correcciones. |

## Resultados

Con las 25 reglas, 20 réplicas de 7200 s por combinación de flujos y la semilla base 0:

- **Verificación contra lo impreso:** conjuntos difusos, operadores «más que» y «menos que», las 25 reglas y el ejemplo trabajado del
  artículo coinciden con el original (diferencia 0.000).
- **Tabla I** (modelo de ciclo fijo con ajustes de Webster): error relativo medio de 2.1 % (simulación) y 0.8 % (fórmula).
- **Tabla VIII** (difuso frente a ciclo fijo): el difuso mejora al ciclo fijo en **16 de 16** combinaciones de flujo (p < 0.001 en todas),
  con un error medio de 9.3 % y máximo de 19.8 % respecto de los retardos publicados. El retardo del difuso queda en promedio 8.8 % por
  debajo del publicado; esa discrepancia se documenta en el artículo.
- **Inferencia por falta de datos:** el artículo no dice cómo se miden los arribos *A* y la cola *Q* en la simulación. De ocho lecturas
  probadas, solo una («calibrada») reproduce la Tabla VIII; se presenta como una inferencia, no como una cita del original.

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

`articulo_ieee/` contiene el manuscrito (`main.tex`, `referencias.bib`, tablas y figuras). En Overleaf: suba la carpeta como
proyecto, deje `main.tex` como documento principal y compile con pdfLaTeX. Las tablas y figuras se regeneran con los scripts
`codigo/gen_tablas_latex.py`, `gen_tabla_180.py` y `gen_fig_articulo*.py`.

## Pruebas

`python codigo/ejecutar_pruebas.py` corre 87 comprobaciones automáticas:

| Prueba | Qué verifica |
|---|---|
| `test_paper_tables.py` (42) | Conjuntos, operadores, las 25 reglas, ejemplo de la Tabla VII y estructura temporal frente a lo impreso. |
| `test_sim_engine.py` (10) | El simulador paso a paso da el mismo resultado que la simulación por lotes. |
| `test_disparos.py` (22) | El panel de reglas y disparos muestra lo que calcula el controlador. |
| `test_autos.py` (13) | Los autos nunca se superponen, apagar reglas afecta el resultado, y las explicaciones coinciden con las decisiones. |

`codigo/verificar_formulas.py` contrasta además las deducciones matemáticas del artículo con cálculos numéricos independientes.

## Más documentación

- `docs/README_TECNICO.md`: detalle técnico, decisiones y correcciones de la transcripción.
- `docs/README_VSCODE.md`: uso desde Visual Studio Code y personalización del simulador.
- `docs/avance5_validacion_replica.pdf`: informe de validación con las curvas de fuzzificación.
