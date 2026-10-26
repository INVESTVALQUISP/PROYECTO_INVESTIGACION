# Artículo IEEE — Réplica del controlador difuso de Pappis y Mamdani (1977) — versión revisada (15 páginas)

Plantilla IEEEtran (journal), texto en español con abstract en inglés. Documentos:

| Archivo | Qué es |
|---|---|
| `main.tex` | Artículo principal (15 páginas con referencias). Documento principal en Overleaf. |
| `suplemento.tex` | Material suplementario (9 páginas): lista literal de las 180 reglas, los seis apartados del simulador por separado, figuras y tablas adicionales. Se compila aparte. |
| `referencias.bib` | 50 referencias (todas citadas), incluidas las de 2021–2026 (Ali, Jiang, Vuong, Dvorsky, Vlasceanu, Noaeen, Michailidis, Mei, Ault). |
| `tabla_*.tex` | Tablas generadas por programa desde `resultados/*.json` (`codigo/gen_tablas_latex.py`, `codigo/gen_tabla_180.py`). |
| `figures/` | Figuras (`codigo/gen_fig_articulo*.py`, `gen_fig_simulador_compuesto.py`). |
| `suplemento_etiquetas.tex` | Números de sección/ecuación de `main.tex` para el suplemento (lo genera `codigo/gen_suplemento_etiquetas.py`). |

## Compilar en Overleaf
1. Overleaf → New Project → Upload Project → subir `articulo_ieee_overleaf_v10.zip`.
2. Menú → Main document: `main.tex`; compilador **pdfLaTeX** (TeX Live 2023 o superior). Compilar (BibTeX corre solo).
   Resultado esperado: 15 páginas, sin errores.
3. Suplemento: en el menú, Main document → `suplemento.tex` y compilar (9 páginas). Si cambia `main.tex`, regenerar
   `suplemento_etiquetas.tex` con `python codigo/gen_suplemento_etiquetas.py` después de compilar `main.tex`.

## Convenciones (observaciones del revisor)
- Las ecuaciones se definen **una sola vez**, en orden: Sección III (modelo y línea base de Webster: Ecs. 1–7) y Sección IV
  (controlador: Ecs. 8–13). La Sección II no tiene ecuaciones. Cada fórmula dice de dónde sale (página del original,
  deducción o carácter empírico) donde se define; la verificación numérica está en la Sección VII-J y en
  `codigo/verificar_formulas.py` → `resultados/verificacion_formulas.json`.
- Notación: `\qbar` (q̄) es la tasa de llegada, α_n el indicador de llegada y `q` la longitud de la cola (Tabla 3).
- Las tablas propias se numeran con cifras arábigas (Tabla 8) y las del artículo original con romanas («Tabla VIII del original»).
- Separador decimal: punto en texto, ecuaciones, tablas y figuras (`es-nodecimaldot` en babel; sin él, babel-spanish convierte
  el punto de las ecuaciones en coma).
- Cada tabla lleva una nota «Fuente:» (macro `\fuente{}`).

## Pendientes antes de enviar
- Verificar cada referencia contra su DOI/editorial (las de 2021–2026 se tomaron de ficha y resumen, no del texto completo;
  el resumen de Niittymäki y Pursula (2000) no se pudo consultar y su fila de la Tabla 1 lo declara).
- La lectura «calibrada» de las entradas A y Q es una inferencia por falta de datos (así se declara en el texto).
- Autores y afiliación: Raul Nolberto Quispe Saya y Kevin Luis Valero Ccacya, Escuela Profesional de Ingeniería Electrónica,
  Universidad Nacional de San Agustín de Arequipa.
