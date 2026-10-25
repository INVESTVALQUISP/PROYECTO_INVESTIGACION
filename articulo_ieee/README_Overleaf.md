# Artículo IEEE — Réplica para el docente (24 páginas)

Réplica y validación del controlador de lógica difusa de Pappis y Mamdani (1977).
Plantilla IEEEtran (journal), texto en español con abstract en inglés.

## Compilar en Overleaf
1. Overleaf → New Project → Upload Project → subir `articulo_ieee_overleaf_v9.zip`.
2. Menu → Main document: `main.tex`; compilador: **pdfLaTeX** (TeX Live 2023 o superior).
3. Compilar (BibTeX corre solo). Resultado esperado: 24 páginas, sin errores.

## Contenido
- `main.tex` — I Introducción, II Estado del arte, III Fundamentos, IV Modelo y réplica,
  V Metodología, VI Resultados, VII Discusión, VIII Conclusiones, Disponibilidad del código.
- `referencias.bib` — 37 referencias (todas citadas).
- `tabla_*.tex` — tablas generadas desde los resultados (`gen_tablas_latex.py`; `gen_tabla_180.py` genera el anexo con las 180 reglas, `gen_tabla_intervenciones.py` la tabla de decisiones por intervención y `resultados/reglas_180.csv`), incluida `tabla_estadistica.tex` (IC 95 %).
- `figures/` — figuras (`gen_fig_articulo.py`, `gen_fig_articulo2.py`, `gen_fig_articulo3.py`, `gen_fig_articulo4.py`: un archivo por apartado del simulador). La captura de la ventana (`fig_simulador.png`) es una captura de pantalla del simulador en t = 118 s (720/2160 veh/h, semilla 1).
- `articulo_replica_para_docente.pdf` — vista previa compilada.

## Pendientes antes de enviar
- Autores: Raul Nolberto Quispe Saya y Kevin Luis Valero Ccacya (Escuela Profesional de Ingeniería Electrónica, Universidad Nacional de San Agustín de Arequipa). Verificar la redacción de la afiliación con el docente.
- Verificar cada referencia contra su DOI/editorial.
- La lectura «calibrada» de las entradas A y Q es una inferencia por falta de datos (así se declara en el texto).

## Origen de fórmulas y datos (observación del docente)
- Sección IV del artículo («Desarrollo matemático de las fórmulas»): de dónde sale cada fórmula (página del artículo original), su deducción paso a paso, qué es empírico o inferido y una verificación numérica independiente (`codigo/verificar_formulas.py` → `resultados/verificacion_formulas.json`).
- Cada tabla lleva una nota «Fuente:» (macro `\fuente{}` en `main.tex`) con la tabla del artículo original, la fórmula o el script de donde salen sus datos.
- Apéndice A: las 180 reglas en una sola tabla larga (`longtable`, a una columna, para que no se superponga con las referencias).
