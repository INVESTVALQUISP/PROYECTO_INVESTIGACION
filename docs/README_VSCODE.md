# Avance de la simulación — cómo correrlo y presentarlo en Visual Studio Code

Muestra que el sistema funciona: **las 25 reglas usadas, cuáles se activan y cuáles DISPARAN
en cada decisión**, todo sobre una simulación gráfica de la calle con el modelo de
Pappis y Mamdani (1977).

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
├── docs/            guías y PDF del avance 5
├── archivo/         material histórico (no usar)
├── .vscode/         ejecutar/depurar con F5 y tareas
└── salidas/         (se crea al ejecutar) CSV, PNG, MP4 y resumen de pruebas
```

Los scripts se pueden ejecutar desde cualquier carpeta: `codigo/_raiz.py` fija la carpeta del
proyecto como directorio de trabajo. Los nombres de archivo de las tablas siguientes están en `codigo/`.

## Personalización didáctica del simulador (ventana)

La parte superior de la ventana tiene tres pestañas y la columna derecha tiene los controles de uso:

| Dónde | Qué permite |
|---|---|
| **1 · Escenario** | Escenarios predefinidos (poco tráfico, medio, cargado, asimétrico…) o flujos propios, duración, semilla y velocidad (desde 1 s simulado por segundo). |
| **2 · Controlador** | Umbral de decisión (en vivo), lectura de A y Q y **Encender / apagar reglas**: quita cualquiera de las 25 reglas y se ve al instante cuánto aporta (apagar R5 sube el retardo de ~17 a ~68 s/veh en una corrida de prueba). |
| **3 · Vista didáctica** | Ocultar/mostrar reglas, grados, disparos y traza de d_m; **pausar en cada decisión**; explicación en palabras simples de cada decisión; mostrar los detectores; separación entre autos y tipos de auto. Botón **? Ayuda** con la explicación de cada control. |
| Columna derecha | **Agregar autos a mano** (N-S/E-W, +1 o +5) para ver cómo reacciona el controlador; cuadro «¿Qué decidió el controlador y por qué?»; registro de decisiones. |

Los autos ahora son vehículos con carrocería, vidrios, ruedas, faros y luces de freno (que se encienden al frenar), de cuatro tipos
(sedán, SUV, compacto, camioneta). Frenan de forma suave y **nunca se tocan**: `test_autos.py` comprueba en miles de cuadros que el
hueco entre un auto y el de adelante nunca baja de 0.8 unidades, con separaciones de 0.8 a 5.

## 1. Preparar VS Code (una sola vez)
1. Instala Python 3.10 o superior (https://www.python.org/downloads/) marcando **Add Python to PATH**
   (en Windows ya incluye Tkinter, que usa el simulador de ventana).
2. VS Code → **Archivo → Abrir carpeta…** → elige la carpeta `raíz del repositorio/`. Instala la extensión
   **Python** si VS Code lo pide.
3. Terminal integrada (`Ctrl+Ñ` o *Terminal → Nueva terminal*):
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. `Ctrl+Shift+P` → **Python: Select Interpreter** → elige el de `.venv`.

## 2. Ejecutar con un clic
Abre **Ejecutar y depurar** (`Ctrl+Shift+D`), elige una configuración en la lista y pulsa **F5**
(vienen ya definidas en `.vscode/launch.json`):

| Configuración | Qué hace |
|---|---|
| **1. Pruebas de validación (resumen)** | Corre las 3 baterías de pruebas (Tablas II–VI, 25 reglas, ejemplo de la pág. 7, motor del simulador, panel de disparos) y muestra las Tablas I y VIII. Guarda `salidas/pruebas.txt`. |
| **2. Simulador gráfico: calle + reglas + disparos** | Ventana con la intersección animada y el panel de reglas. |
| **3. Simulador web** | Lo mismo en el navegador: abre http://localhost:8000 (en VS Code: *Simple Browser*). |
| **4. Informe de reglas y disparos** | Sin ventana: deja `salidas/disparos_reglas.csv`, `resumen_disparos.csv` e `informe_disparos.png`. |
| **5. Video MP4 de la simulación** | `salidas/simulacion.mp4` (+ CSV de disparos), 30 cuadros/s con movimiento suave. |
| **6. Tablas I y VIII oficiales** | Recalcula los resultados completos (~2 min). |

También por terminal: `python codigo/ejecutar_pruebas.py`, `python codigo/simulador_gui.py`, `python codigo/web_sim.py`,
`python codigo/informe_disparos.py --ns 1080 --ew 1800 --seconds 3600 --seed 4`.

## 3. Qué se ve en el simulador (ventana o web)
**Izquierda:** la calle (N–S en azul, E–W en naranja) con vehículos que **entran por el borde, avanzan en la cola
cuando sale el de adelante, aceleran al cruzar y salen de la pantalla**; semáforos de tres luces
(verde → **ámbar 3 s** → rojo) y la traza del retardo medio d<sub>m</sub>(t).
**Derecha (lo pedido):**
1. **Reglas de la intervención** (7, 17, 27, 37 o 47 s): las 5 reglas con su texto del paper y una
   barra de **activación** (0 a 1). La regla que **dispara** queda en verde con ★.
2. **Vector grade(e)**: el grado de cada extensión candidata (1 a 10 s), el umbral 0.5 y la decisión
   (`e* = …` o **CORTE** del verde).
3. **Disparos acumulados** de las 25 reglas (barra oscura) y sus activaciones (barra clara).

**Definiciones.** *Activación* de una regla = máximo sobre e de mín(μ<sub>T</sub>, μ<sub>mt(A)</sub>,
μ<sub>lt(Q)</sub>, μ<sub>E</sub>). *Disparo* = la regla cuya contribución en e\* iguala el grado máximo,
es decir, la que gana la decisión; si todo el vector es menor que 0.5 el verde se corta y no hay regla
ganadora. Botones: **Iniciar / Pausa / Paso (avanza 1 s) / Reiniciar**, **Guardar disparos (CSV)**,
**Guardar imagen (PNG)**. En la web: enlace *Descargar disparos de reglas (CSV)*.

**Sobre el ámbar.** El modelo del paper no tiene una fase ámbar propia: usa *verde efectivo* y un tiempo
perdido de 10 s por ciclo (5 s por cambio de fase), y menciona un ámbar de 3 s. Por eso el simulador muestra
esos 5 s como **3 s de ámbar (brazo saliente) + 2 s de todo rojo**. Es solo una representación visual: en el
modelo numérico no cruzan vehículos durante esos 5 s (así se cuenta el tiempo perdido), por lo que los
resultados no cambian.

**Fluidez.** Cada segundo simulado se dibuja en varios sub-cuadros (~24 por segundo en pantalla). Si la
animación va lenta en tu equipo, baja la «Velocidad (fps)» de la ventana.

## 4. Guion sugerido para la presentación (≈ 6 min)
1. **Pruebas (configuración 1):** «todo lo impreso en el paper coincide con el código»: 42 comprobaciones,
   ejemplo de las págs. 7–8 y Tablas I y VIII.
2. **Simulador (configuración 2):** arrancar con 720/2160 veh/h; pausar en una decisión y mostrar el panel:
   entradas, reglas activadas, regla que dispara, e\*.
3. **Paso a paso:** con *Paso* mostrar un CORTE (todo < 0.5) y una extensión de 10 s.
4. **Disparos acumulados:** casi siempre dispara la regla de extensión larga (*verylong*); las intermedias
   casi no deciden (coincide con el experimento de reducción de reglas).
5. **Informe (configuración 4):** CSV + figura con las 25 reglas y las decisiones en el tiempo.
6. Cambiar a **1440/1440** o a la lectura **literal** y comentar la diferencia (Avance 5, Sección 6).

## 5. Problemas frecuentes
* *«No module named …»*: activa el entorno (`.venv\Scripts\activate`) y repite `pip install -r requirements.txt`.
* *No se abre la ventana (Linux/macOS):* instala Tkinter (`sudo apt install python3-tk`) o usa la versión web.
* *No exporta MP4:* instala `imageio-ffmpeg`; si no, el script guarda un GIF.
* La carpeta `muestras/` trae un ejemplo ya generado (video, informe, CSV y captura de la ventana).

## 6. Optimización: comparar el controlador de 1977 con FLC-O

La versión de optimización agrega un controlador difuso nuevo (FLC-O, 27 reglas, 42 parámetros entrenados con CMA-ES) y herramientas
para compararlo con el de Pappis y Mamdani sobre **las mismas llegadas de vehículos**. Estas configuraciones de **F5** ya vienen en `.vscode/launch.json`:

| Configuración | Qué hace |
|---|---|
| **7. Comparar Pappis y Mamdani con FLC-O (ventana)** | Abre una figura con las colas de los dos brazos y la fase de cada controlador, y muestra en la terminal el retardo medio, la cola máxima y los cambios de fase de cada uno. |
| **8. Animación GIF** | Guarda `salidas/comparacion.gif` (colas como barras y semáforos de los dos controladores) y `salidas/comparacion.png`. |
| **9. Evaluación de optimización (rápida)** | Evalúa todos los controladores con 5 réplicas de 3600 s (unos minutos) y escribe `resultados/opt/evaluacion_final_rapido.json`. |

Por terminal:

```bash
python codigo/simulador_opt.py                                        # escenario del artículo (720 / 2160 veh/h), abre una ventana
python codigo/simulador_opt.py --ns 1080 --ew 1800 --seed 5 --seconds 1200
python codigo/simulador_opt.py --gif salidas/comparacion.gif --guardar salidas/comparacion.png --sin-ventana
python codigo/opt_evaluacion_final.py                                 # evaluación completa (conjuntos oficial, no vistos, variable y saturado)
python codigo/gen_tablas_opt.py && python codigo/gen_fig_opt.py       # regenera tablas, cifras y figuras del artículo de optimización
```

Entrenar un controlador (unos 15 minutos con 4 núcleos; los puntos de control se guardan en `*.parcial` y se retoman con `--resume`):

```bash
python codigo/opt_entrenar_modelo.py --modelo flcopt --gmin 5 --max-green 90 --suma-max 3300 --ref actuado_af --gens 150 --out resultados/opt/mi_modelo.json
```

En Windows se usan los mismos comandos con `python` dentro del entorno virtual (`.venv\Scripts\Activate.ps1`).
