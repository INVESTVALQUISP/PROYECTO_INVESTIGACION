"""
gen_tablas_opt.py
================================================================================
Lee resultados/opt/evaluacion_final.json y resultados/opt/modelos_finales.json y escribe en articulo/:
  numeros.tex          macros con las cifras del texto (\\DelayOfFlc = retardo medio oficial de FLC-O, etc.)
  tabla_oficial.tex    retardo por par de caudales de la Tabla VIII (referencias, FLC-O y optimo)
  tabla_conjuntos.tex  retardo medio en los cuatro conjuntos de prueba
  tabla_comparaciones.tex  mejora de FLC-O frente a cada referencia, con Wilcoxon + Holm
  tabla_ablacion.tex   variantes de FLC-O y controladores aprendidos
  tabla_reglas_flc.tex     base de reglas de FLC-O (27 consecuentes) y nudos de las funciones de pertenencia
Todas las cifras del articulo salen de aqui, no se escriben a mano.
Uso:  python gen_tablas_opt.py
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import json
import os

import numpy as np

import estadistica as est
import opt_flc2
from opt_nombres import ETIQUETA, clave, finales

OUT = "articulo"
SETS = {"oficial": "Of", "no_vistos": "Nv", "variable": "Va", "saturado": "Sa"}
CTRL = {"fijo": "Fijo", "actuado": "Act", "actuado_af": "ActAf", "actuado_vista": "ActV", "maxpressure": "Max", "pappis": "Pap",
        "afinado_pappis": "PapAf", "mdp": "Mdp", "flc": "Flc", "flc_causal": "FlcC", "mlp": "Mlp", "mlp_causal": "MlpC"}


def f(x, n=2):
    return f"{x:.{n}f}"


def neg(txt):
    return txt.replace("-", "$-$")


def red(a, b):
    """Reduccion relativa de b respecto de a, en %, con signo tipografico."""
    return neg(f"{100 * (a - b) / a:.1f}")


def pct(x, n=1):
    return f"{x:+.{n}f}".replace("-", "$-$")


def p_txt(p):
    return "$<\\!0.001$" if p < 0.001 else f"{p:.2f}"


# variantes de la ablacion entrenadas con 3 semillas de CMA-ES (semilla 0 = el nombre base; 1 y 2 = _s1 y _s2)
GRUPOS_SEMILLAS = {"Fijos": "flcs_v3_g3", "Reglas": "flcs4_v3_g3", "GSiete": "flcopt_g7", "GCinco": "flcopt_g5",
                   "GCuatro": "flcopt_g4", "GTres": "flcopt_g3"}


def semillas_de(base, disponibles):
    return [m for m in (base, base + "_s1", base + "_s2") if m in disponibles]


def main():
    os.makedirs(OUT, exist_ok=True)
    d = json.load(open("resultados/opt/evaluacion_final.json"))
    fin = finales()
    key = {r: clave(r, fin) for r in CTRL}
    key["afinado_pappis"] = fin.get("afinado", "afinado_pappis")
    of = d["oficial"]
    pares = np.array(of["flujos"])[::20]
    med = {s: {r: float(np.mean(d[s]["delay"][key[r]])) for r in CTRL if key[r] in d[s]["delay"]} for s in SETS}

    # ---------------- numeros.tex
    L = ["% Generado por gen_tablas_opt.py (no editar a mano)"]
    for s, sn in SETS.items():
        for r, rn in CTRL.items():
            if r in med[s]:
                L.append(f"\\newcommand{{\\Delay{sn}{rn}}}{{{med[s][r]:.2f}}}")
    base = med["oficial"]
    for r, rn in CTRL.items():
        if r in base and r != "pappis":
            L.append("\\newcommand{\\Red" + rn + "}{" + red(base["pappis"], base[r]) + "}")
    for s, sn in SETS.items():
        if "flc" in med[s] and "pappis" in med[s]:
            L.append("\\newcommand{\\RedPap" + sn + "}{" + red(med[s]["pappis"], med[s]["flc"]) + "}")
        if "flc" in med[s] and "actuado_af" in med[s]:
            L.append("\\newcommand{\\RedActAf" + sn + "}{" + red(med[s]["actuado_af"], med[s]["flc"]) + "}")
        if "flc" in med[s] and "actuado_vista" in med[s]:
            L.append("\\newcommand{\\RedActV" + sn + "}{" + red(med[s]["actuado_vista"], med[s]["flc"]) + "}")
        if "actuado_vista" in med[s] and "pappis" in med[s]:
            L.append("\\newcommand{\\RedVistaPap" + sn + "}{" + red(med[s]["pappis"], med[s]["actuado_vista"]) + "}")   # el actuado con vista frente a Pappis
        if "actuado_vista" in med[s] and "actuado_af" in med[s]:
            L.append("\\newcommand{\\RedVistaAf" + sn + "}{" + red(med[s]["actuado_af"], med[s]["actuado_vista"]) + "}")  # solo por la informacion
    comp = of["comparaciones"]
    for r, rn in (("pappis", "Pap"), ("actuado_af", "ActAf"), ("actuado_vista", "ActV"), ("actuado", "Act"), ("fijo", "Fijo"), ("mdp", "Mdp"), ("afinado_pappis", "PapAf")):
        k = f"{key['flc']}__vs__{key[r]}"
        if k in comp:
            c = comp[k]
            L.append(f"\\newcommand{{\\ParMedia{rn}}}{{{c['mejora_media_pct']:.1f}}}")
            L.append(f"\\newcommand{{\\ParMejor{rn}}}{{{c['mejor_signif']}}}")
            L.append(f"\\newcommand{{\\ParPeor{rn}}}{{{c['peor_signif']}}}")
            L.append(f"\\newcommand{{\\ParMin{rn}}}{{{min(c['mejora_por_par']):.1f}}}")
            L.append(f"\\newcommand{{\\ParMax{rn}}}{{{max(c['mejora_por_par']):.1f}}}")
    # macros de las variantes de la ablacion y de las semillas: \\Delay{Of,Nv,Va,Sa}<Id> y reduccion frente al actuado afinado \\RedAct<Id>
    ids = {"flcs_v3_g3": "Fijos", "flcs4_v3_g3": "Reglas", "flcopt_g7": "GSiete", "flcopt_g5": "GCinco",
           "flcopt_g4": "GCuatro", "flcopt_g3": "SemCero", "flcopt_g3_s1": "SemUno", "flcopt_g3_s2": "SemDos",
           "lineal_causal_v3_g3": "LinC"}
    for modelo_, id_ in ids.items():
        for sn_, nom_ in SETS.items():
            if modelo_ in d[sn_]["delay"]:
                v_ = float(np.mean(d[sn_]["delay"][modelo_]))
                L.append(f"\\newcommand{{\\Delay{nom_}{id_}}}{{{v_:.2f}}}")
        if modelo_ in d["oficial"]["delay"]:
            v_ = float(np.mean(d["oficial"]["delay"][modelo_]))
            L.append("\\newcommand{\\RedAct" + id_ + "}{" + red(base["actuado_af"], v_) + "}")
            L.append("\\newcommand{\\RedPap" + id_ + "}{" + red(base["pappis"], v_) + "}")
    for r, rn in CTRL.items():       # reduccion frente al actuado afinado en el conjunto oficial
        if r in base and r != "actuado_af":
            L.append("\\newcommand{\\RedAct" + rn + "}{" + red(base["actuado_af"], base[r]) + "}")
    for sn_, nom_ in (("oficial", "Of"), ("saturado", "Sa")):
        x_ = np.array(d[sn_]["delay"][key["pappis"]]); y_ = np.array(d[sn_]["delay_servidos"][key["pappis"]])
        rel_ = (x_ - y_) / x_ * 100
        L.append(f"\\newcommand{{\\ResDif{nom_}}}{{{rel_.mean():.1f}}}")
        L.append(f"\\newcommand{{\\ResDif{nom_}Max}}{{{rel_.max():.1f}}}")
    for sn_, nom_ in (("no_vistos", "Nv"), ("variable", "Va"), ("saturado", "Sa")):        # FLC-O frente a cada referencia, por escenario
        L.append(f"\\newcommand{{\\EscN{nom_}}}{{{len(d[sn_]['flujos'])}}}")
        for r_, rn_ in (("pappis", "Pap"), ("actuado_af", "ActAf"), ("actuado_vista", "ActV")):
            c_ = d[sn_].get("comparaciones_escenario", {}).get(f"{key['flc']}__vs__{key[r_]}")
            if c_:
                pre_ = "\\newcommand{\\Esc" + rn_ + nom_
                L.append(pre_ + "Red}{" + neg("%.1f" % c_["mejora_media_escenario_pct"]) + "}")
                L.append(pre_ + "Lo}{" + neg("%.1f" % c_["ic_lo"]) + "}")
                L.append(pre_ + "Hi}{" + neg("%.1f" % c_["ic_hi"]) + "}")
                L.append(pre_ + "P}{" + p_txt(c_["p_wilcoxon"]) + "}")
                L.append(pre_ + "Mejor}{" + str(c_["mejor"]) + "}")
                L.append(pre_ + "Peor}{" + str(c_["peor"]) + "}")
    # variantes de la ablacion con varias semillas de entrenamiento: media y desviacion estandar entre semillas
    for id_, base_ in GRUPOS_SEMILLAS.items():
        ms = semillas_de(base_, of["delay"])
        for sn_, nom_ in SETS.items():
            vals = [float(np.mean(d[sn_]["delay"][m_])) for m_ in ms if m_ in d[sn_]["delay"]]
            if vals:
                L.append(f"\\newcommand{{\\Med{nom_}{id_}}}{{{np.mean(vals):.2f}}}")
                L.append(f"\\newcommand{{\\Sd{nom_}{id_}}}{{{(np.std(vals, ddof=1) if len(vals) > 1 else 0.0):.2f}}}")
        L.append(f"\\newcommand{{\\NSem{id_}}}{{{len(ms)}}}")
        vo_ = [float(np.mean(d["oficial"]["delay"][m_])) for m_ in ms]
        L.append("\\newcommand{\\RedPapMed" + id_ + "}{" + red(base["pappis"], float(np.mean(vo_))) + "}")        # reduccion frente a Pappis de la media de semillas
        L.append("\\newcommand{\\RedActAfMed" + id_ + "}{" + red(base["actuado_af"], float(np.mean(vo_))) + "}")
        L.append("\\newcommand{\\RedActVMed" + id_ + "}{" + red(base["actuado_vista"], float(np.mean(vo_))) + "}")
    if os.path.exists("resultados/opt/mdp_oficial.json"):
        mdp = json.load(open("resultados/opt/mdp_oficial.json"))
        dif = max(abs(x["dp_sim"] - x["dp_analitico"]) / x["dp_analitico"] * 100 for x in mdp)
        L.append(f"\\newcommand{{\\PdMaxDif}}{{{dif:.1f}}}")
    open(f"{OUT}/numeros.tex", "w").write("\n".join(L) + "\n")

    # ---------------- tabla_oficial.tex (Tabla 4): media +- desviacion estandar de las 20 replicas de cada controlador
    cols = ["fijo", "actuado_af", "actuado_vista", "pappis", "flc", "mdp"]
    cols = [r for r in cols if key[r] in of["por_par"]]
    kc = f"{key['flc']}__vs__{key['pappis']}"
    kv = f"{key['flc']}__vs__{key['actuado_vista']}"
    tiene_v = "actuado_vista" in cols
    rows = []
    for i, (a, b) in enumerate(pares):
        cel = {}
        for r in cols:
            e = of["por_par"][key[r]][i]
            cel[r] = (e["media"], e["sd"])
        mejor = min((r for r in cols if r != "mdp"), key=lambda r: cel[r][0])
        txt = []
        for r in cols:
            m_, sd_ = cel[r]
            c = f"{f(m_)} $\\pm$ {f(sd_)}" if r != "mdp" else f(m_)
            txt.append(f"\\textbf{{{c}}}" if r == mejor else c)
        sigp = "$^{*}$" if comp[kc]["p_holm"][i] < 0.05 else ""
        colv = ""
        if tiene_v:
            sigv = "$^{*}$" if comp[kv]["p_holm"][i] < 0.05 else ""
            colv = f" & {pct(comp[kv]['mejora_por_par'][i])}{sigv}"
        antes = [t for r, t in zip(cols, txt) if r != "mdp"]
        rows.append(f"{int(a)} / {int(b)} & " + " & ".join(antes) + f" & {pct(comp[kc]['mejora_por_par'][i])}{sigp}{colv} & {txt[-1]} \\\\")
    mv = {r: np.mean([of["por_par"][key[r]][i]["media"] for i in range(len(pares))]) for r in cols}
    rows.append("\\midrule")
    fila_m = "Media de los 16 pares & " + " & ".join(f(mv[r]) for r in cols if r != "mdp") + f" & {pct(comp[kc]['mejora_media_pct'])}"
    if tiene_v:
        fila_m += f" & {pct(comp[kv]['mejora_media_pct'])}"
    rows.append(fila_m + f" & {f(mv['mdp'])} \\\\")
    cab = "N-S / E-W (veh/h) & Webster & Actuado af. & Actuado af. + vista & Pappis reconst. & FLC-O & $\\Delta_P$ (\\%) & " + ("$\\Delta_V$ (\\%) & " if tiene_v else "") + "\\'Optimo$^{\\dagger}$ \\\\"
    esp = "@{}l" + "r" * (len(cols) - 1 + 1 + (2 if tiene_v else 1)) + "@{}"
    T = ["\\begin{table*}[!t]", "\\centering", "\\caption{Retardo medio por veh\\'iculo (s) $\\pm$ desviaci\\'on est\\'andar muestral ($n-1$) de las 20 r\\'eplicas, en los 16 pares de caudales "
         "de la Tabla VIII del art\\'iculo original (7200 s, n\\'umeros aleatorios comunes). Se cuenta la espera de todos los veh\\'iculos hasta el horizonte. "
         "``Pappis reconst.'': controlador de 1977 reconstruido (Sec.~\\ref{sec:lecturas}). ``Actuado af. + vista'': actuado afinado con la misma vista adelante de 10 s que FLC-O. "
         "$\\Delta_P$ y $\\Delta_V$: mejora de FLC-O (\\%) frente a Pappis reconst. y frente al actuado af. + vista; $^{*}$: significativa (Wilcoxon pareado, Holm, 0.05). "
         "En negrita, el menor retardo medio entre los controladores realizables.}", "\\label{tab:oficial}", "\\scriptsize", "\\setlength{\\tabcolsep}{3pt}",
         "\\begin{tabular}{" + esp + "}", "\\toprule", cab, "\\midrule"] + rows + \
        ["\\bottomrule", "\\end{tabular}",
         "\\fuente{simulaci\\'on del autor (resultados/opt/evaluacion\\_final.json); $^{\\dagger}$ cota por programaci\\'on din\\'amica que conoce los caudales y no ve llegadas futuras (Sec.~\\ref{sec:pd}); es determinista, sin dispersi\\'on.}",
         "\\end{table*}"]
    open(f"{OUT}/tabla_oficial.tex", "w").write("\n".join(T) + "\n")

    # ---------------- tabla_conjuntos.tex (Tabla 6): media +- semiancho del IC 95 % y comparaciones pareadas de FLC-O
    orden = ["fijo", "actuado", "actuado_af", "actuado_vista", "maxpressure", "pappis", "afinado_pappis", "flc", "mdp", "mlp"]

    def estadistico(s, modelo):
        """(media, semiancho del IC 95 %) de modelo en el conjunto s: unidad de analisis = el par (oficial: media de 20 replicas) o el escenario."""
        if s == "oficial":
            m_, sd_, lo_, hi_ = est.ic95([e["media"] for e in of["por_par"][modelo]])
        else:
            e_ = d[s]["resumen"][modelo]
            m_, lo_, hi_ = e_["media"], e_["ic_lo"], e_["ic_hi"]
        return m_, (hi_ - lo_) / 2

    def comparacion(s, a, b):
        """FLC-O (a) frente a la referencia b: reduccion media por unidad (%), IC 95 %, p de Wilcoxon pareado."""
        if s == "oficial":
            x = np.array([e["media"] for e in of["por_par"][a]])
            y = np.array([e["media"] for e in of["por_par"][b]])
            rel = (y - x) / y * 100.0
            m_, sd_, lo_, hi_ = est.ic95(rel)
            return m_, lo_, hi_, est.wilcoxon(x, y)["p"]
        c_ = d[s]["comparaciones_escenario"][f"{a}__vs__{b}"]
        return c_["mejora_media_escenario_pct"], c_["ic_lo"], c_["ic_hi"], c_["p_wilcoxon"]

    R = []
    for r in orden:
        if r not in med["oficial"]:
            continue
        cells = []
        for s in SETS:
            if key[r] not in (of["por_par"] if s == "oficial" else d[s].get("resumen", {})):
                cells.append("--")
                continue
            m_, h_ = estadistico(s, key[r])
            cells.append(f"{f(m_, 1)} $\\pm$ {f(h_, 1)}")
        R.append(f"{ETIQUETA[r]} & " + " & ".join(cells) + " \\\\")
    R.append("\\midrule")
    R.append("\\multicolumn{5}{l}{Reducci\\'on media de FLC-O por unidad (\\%) [IC 95\\,\\%], $p$ de Wilcoxon pareado} \\\\")
    for r in ("pappis", "actuado_af", "actuado_vista"):
        if r not in med["oficial"]:
            continue
        cells = []
        for s in SETS:
            m_, lo_, hi_, p_ = comparacion(s, key["flc"], key[r])
            cells.append(f"{neg(f(m_, 1))} [{neg(f(lo_, 1))}, {neg(f(hi_, 1))}], $p$ {p_txt(p_) if p_ < 0.001 else '= ' + p_txt(p_)}")
        R.append(f"\\quad frente a {ETIQUETA[r]} & " + " & ".join(cells) + " \\\\")
    nsc = {s: len(d[s]["flujos"]) for s in SETS}
    T = ["\\begin{table*}[!t]", "\\centering", "\\caption{Retardo medio (s/veh) $\\pm$ semiancho del IC de 95\\,\\% en los cuatro conjuntos de prueba (todos de 7200 s), y reducci\\'on de FLC-O por unidad frente a tres referencias. "
         f"Unidad de an\\'alisis y semillas de las llegadas: Oficial, los 16 pares de la Tabla VIII, cada uno con la media de 20 r\\'eplicas (semillas 0 a 19); "
         f"No vistos, {nsc['no_vistos']} escenarios con caudales sorteados (semillas 500000 a {500000 + nsc['no_vistos'] - 1}); "
         f"Variable, {nsc['variable']} escenarios con demanda por tramos de 600 s y factor de 0.4 a 1.6 (semillas 300000 a {300000 + nsc['variable'] - 1}); "
         f"Saturado, {nsc['saturado']} escenarios con suma de caudales de 3000 a 3300 veh/h (semillas 400000 a {400000 + nsc['saturado'] - 1}). "
         "Cada escenario es un par de caudales con una r\\'eplica; los controladores ven las mismas llegadas.}", "\\label{tab:conjuntos}", "\\scriptsize",
         "\\setlength{\\tabcolsep}{3pt}", "\\begin{tabular}{@{}lllll@{}}", "\\toprule",
         f"Controlador & Oficial ($n={nsc['oficial'] // 20}$ pares) & No vistos ($n={nsc['no_vistos']}$) & Variable ($n={nsc['variable']}$) & Saturado ($n={nsc['saturado']}$) \\\\", "\\midrule"] + R + \
        ["\\bottomrule", "\\end{tabular}",
         "\\fuente{simulaci\\'on del autor (resultados/opt/evaluacion\\_final.json). El \\'optimo no se calcula en el conjunto saturado (la cola truncada de la programaci\\'on din\\'amica no es fiable all\\'i) y es determinista (sin IC).}",
         "\\end{table*}"]
    open(f"{OUT}/tabla_conjuntos.tex", "w").write("\n".join(T) + "\n")

    # ---------------- tabla_comparaciones.tex (Tabla 5): rango y IC 95 % de las 16 mejoras por par
    R = []
    for r in ("pappis", "afinado_pappis", "fijo", "actuado", "actuado_af", "actuado_vista", "mdp"):
        k = f"{key['flc']}__vs__{key[r]}"
        if k in comp:
            c = comp[k]
            m_, sd_, lo_, hi_ = est.ic95(c["mejora_por_par"])
            R.append(f"{ETIQUETA[r]} & {pct(c['mejora_media_pct'])} & [{pct(lo_)}, {pct(hi_)}] & {pct(min(c['mejora_por_par']))} a {pct(max(c['mejora_por_par']))} & "
                     f"{c['mejor_signif']} & {c['peor_signif']} \\\\")
    T = ["\\begin{table}[t]", "\\centering", "\\caption{FLC-O frente a cada referencia en la Tabla VIII. Mejora media del retardo por par de caudales (\\%); "
         "IC de 95\\,\\% de esa media (t de Student sobre las 16 mejoras por par); rango (m\\'inimo a m\\'aximo) de las 16 mejoras, que no es un intervalo de confianza; "
         "y n\\'umero de pares (de 16) en que FLC-O es significativamente mejor o peor (Wilcoxon pareado sobre 20 r\\'eplicas, correcci\\'on de Holm, 0.05).}",
         "\\label{tab:comparaciones}", "\\scriptsize", "\\setlength{\\tabcolsep}{2.6pt}",
         "\\begin{tabular}{@{}lrrrrr@{}}", "\\toprule", "Referencia & Media & IC 95\\,\\% & Rango & Mejor & Peor \\\\", "\\midrule"] + R + \
        ["\\bottomrule", "\\end{tabular}", "\\fuente{simulaci\\'on del autor; Wilcoxon exacto o con aproximaci\\'on normal seg\\'un empates (estadistica.py).}", "\\end{table}"]
    open(f"{OUT}/tabla_comparaciones.tex", "w").write("\n".join(T) + "\n")

    # ---------------- tabla_ablacion.tex (Tabla 7): filas con 3 semillas de entrenamiento -> media +- desviacion estandar entre semillas
    abl = fin.get("ablacion", [])
    R = []
    for etiqueta, modelo, npar, nota in abl:
        if modelo not in of["delay"]:
            continue
        grupo = semillas_de(modelo, of["delay"]) if modelo in GRUPOS_SEMILLAS.values() else [modelo]
        if "propuesto" in etiqueta:
            grupo = [modelo]

        def celda(s, dec):
            v = [float(np.mean(d[s]["delay"][m_])) for m_ in grupo if m_ in d[s]["delay"]]
            if not v:
                return "--"
            return f"{np.mean(v):.{dec}f}" + (f" $\\pm$ {np.std(v, ddof=1):.{dec}f}" if len(v) > 1 else "")
        etq = etiqueta.replace("(mejor de 3 semillas)", "(semilla elegida)")
        R.append(f"{etq} & {npar} & {nota} & {len(grupo)} & {celda('oficial', 2)} & {celda('no_vistos', 2)} & {celda('variable', 2)} \\\\")
    if R:
        T = ["\\begin{table*}[!t]", "\\centering", "\\caption{Variantes de FLC-O y controladores aprendidos, entrenados con las mismas condiciones. Retardo medio (s/veh) en la Tabla VIII, "
             "en caudales no vistos y con demanda variable. Con 3 semillas de entrenamiento (columna $n$), media $\\pm$ desviaci\\'on est\\'andar muestral ($n-1$) entre semillas; "
             "con $n=1$, un solo entrenamiento (exploratorio, sin incertidumbre). $g_{\\min}$: verde m\\'inimo.}", "\\label{tab:ablacion}", "\\scriptsize",
             "\\setlength{\\tabcolsep}{2.4pt}", "\\begin{tabular}{@{}lrlrrrr@{}}", "\\toprule",
             "Variante & Par. & Informaci\\'on & $n$ & Oficial & No vistos & Variable \\\\", "\\midrule"] + R + \
            ["\\bottomrule", "\\end{tabular}", "\\fuente{simulaci\\'on del autor; par.: n\\'umero de par\\'ametros entrenados; las semillas cambian solo la semilla de CMA-ES, con los mismos escenarios de entrenamiento.}", "\\end{table*}"]
        open(f"{OUT}/tabla_ablacion.tex", "w").write("\n".join(T) + "\n")

    # ---------------- tabla_reglas_flc.tex (FLC-O elegido)
    nom = fin.get("flc")
    if nom and os.path.exists(f"resultados/opt/{nom}.json"):
        m = json.load(open(f"resultados/opt/{nom}.json"))
        ctrl = opt_flc2.FuzzyOpt(np.array(m["theta"]), True, m["gmin"]) if m.get("modelo") == "flcopt" else opt_flc2.FuzzySegundo(np.array(m["theta"]), True, m["gmin"])
        etq = ["bajo", "medio", "alto"]
        R = []
        for i in range(3):
            for j in range(3):
                cs = [ctrl.c[i * 9 + j * 3 + k] for k in range(3)]
                R.append(f"{etq[i]} & {etq[j]} & " + " & ".join(f"{c:+.2f}".replace("-", "$-$") for c in cs) + " \\\\")
        kk = lambda k: ", ".join(f"{x:.3f}" for x in k)
        extra = ""
        if hasattr(ctrl, "alfa"):
            extra = (f" Pesos aprendidos de la vista adelante: verde ({', '.join(f'{w:.2f}' for w in ctrl.alfa)}) para 2, 5 y 10 s; "
                     f"rojo ({', '.join(f'{w:.2f}' for w in ctrl.beta)}) para 3, 6 y 10 s.")
        T = ["\\begin{table}[t]", "\\centering", "\\caption{Base de reglas de FLC-O: consecuente num\\'erico $c_{ijk}$ de cada regla "
             "(positivo: cambiar la fase; negativo: seguir en verde) seg\\'un la demanda en verde $G$, la presi\\'on en rojo $R$ y el verde transcurrido $V$. "
             f"Nudos $(k_1,k_2,k_3)$: $G$ ({kk(ctrl.kG)}), $R$ ({kk(ctrl.kR)}), $V$ ({kk(ctrl.kE)}).{extra}}}", "\\label{tab:reglasflc}", "\\scriptsize",
             "\\begin{tabular}{@{}llrrr@{}}", "\\toprule", "$G$ & $R$ & $V$ bajo & $V$ medio & $V$ alto \\\\", "\\midrule"] + R + \
            ["\\bottomrule", "\\end{tabular}", f"\\fuente{{modelo entrenado {nom.replace('_', chr(92) + '_')} (resultados/opt/{nom.replace('_', chr(92) + '_')}.json).}}", "\\end{table}"]
        open(f"{OUT}/tabla_reglas_flc.tex", "w").write("\n".join(T) + "\n")

    # ---------------- tablas del suplemento
    # (a) todos los pares: media, sd, IC95 y p de Holm de FLC-O frente a Pappis, al actuado afinado y al actuado con vista adelante
    kp = f"{key['flc']}__vs__{key['pappis']}"
    ka = f"{key['flc']}__vs__{key['actuado_af']}"
    kv = f"{key['flc']}__vs__{key['actuado_vista']}"
    R1, R2 = [], []
    for i, (a_, b_) in enumerate(pares):
        pp, aa, vv, ff = (of["por_par"][key[r_]][i] for r_ in ("pappis", "actuado_af", "actuado_vista", "flc"))
        R1.append(f"{int(a_)}/{int(b_)} & {f(pp['media'])} $\\pm$ {f(pp['sd'])} & {f(aa['media'])} $\\pm$ {f(aa['sd'])} & {f(vv['media'])} $\\pm$ {f(vv['sd'])} & "
                  f"{f(ff['media'])} $\\pm$ {f(ff['sd'])} & [{f(ff['ic_lo'])}, {f(ff['ic_hi'])}] \\\\")
        R2.append(f"{int(a_)}/{int(b_)} & {pct(comp[kp]['mejora_por_par'][i])} & {p_txt(comp[kp]['p_holm'][i])} & {pct(comp[ka]['mejora_por_par'][i])} & {p_txt(comp[ka]['p_holm'][i])} & "
                  f"{pct(comp[kv]['mejora_por_par'][i])} & {p_txt(comp[kv]['p_holm'][i])} \\\\")
    T = ["\\begin{table*}[!t]", "\\centering", "\\caption{Conjunto oficial, todos los pares. Arriba: media $\\pm$ desviaci\\'on est\\'andar muestral (20 r\\'eplicas, $n-1$) del retardo (s/veh) de Pappis y Mamdani reconstruido, "
         "del actuado afinado, del actuado afinado con vista adelante y de FLC-O, e IC de 95\\,\\% de FLC-O. Abajo: mejora de FLC-O frente a Pappis reconst. ($\\Delta_P$), al actuado afinado ($\\Delta_A$) y al actuado afinado con vista adelante ($\\Delta_V$), "
         "con el $p$ de Wilcoxon pareado corregido por Holm.}",
         "\\label{tab:spares}", "\\scriptsize", "\\setlength{\\tabcolsep}{4pt}", "\\begin{tabular}{@{}lrrrrr@{}}", "\\toprule",
         "N-S/E-W & Pappis reconst. & Actuado af. & Actuado af. + vista & FLC-O & IC 95\\,\\% FLC-O \\\\", "\\midrule"] + R1 + \
        ["\\bottomrule", "\\end{tabular}", "", "\\vspace{6pt}", "", "\\begin{tabular}{@{}lrrrrrr@{}}", "\\toprule",
         "N-S/E-W & $\\Delta_P$ (\\%) & $p_P$ & $\\Delta_A$ (\\%) & $p_A$ & $\\Delta_V$ (\\%) & $p_V$ \\\\", "\\midrule"] + R2 + \
        ["\\bottomrule", "\\end{tabular}", "\\fuente{simulaci\\'on del autor (resultados/opt/evaluacion\\_final.json); $\\Delta$: reducci\\'on relativa del retardo medio del par.}", "\\end{table*}"]
    open(f"{OUT}/tabla_s_pares.tex", "w").write("\n".join(T) + "\n")

    # (a2) los 42 parametros completos de FLC-O y un ejemplo numerico (para reconstruirlo sin leer el codigo)
    nom_ = fin.get("flc")
    if nom_ and os.path.exists(f"resultados/opt/{nom_}.json"):
        m_ = json.load(open(f"resultados/opt/{nom_}.json"))
        th_ = np.array(m_["theta"], dtype=float)
        etq_ = ["bajo", "medio", "alto"]
        nombres = ([f"$p_{{{k + 1}}}^{{G}}$" for k in range(3)] + [f"$p_{{{k + 1}}}^{{R}}$" for k in range(3)] + [f"$p_{{{k + 1}}}^{{V}}$" for k in range(3)] +
                   ["$c_{\\text{" + etq_[i // 9] + "},\\text{" + etq_[(i // 3) % 3] + "},\\text{" + etq_[i % 3] + "}}$" for i in range(27)] +
                   [f"$\\omega_{{{k + 1}}}$" for k in range(3)] + [f"$\\rho_{{{k + 1}}}$" for k in range(3)])
        celdas = [(nombres[k], th_[k]) for k in range(42)]
        filas = []
        for r_ in range(14):
            fila = []
            for c_ in range(3):
                nm, v = celdas[c_ * 14 + r_]
                fila.append(f"{nm} & {neg(f'{v:.6f}')}")
            filas.append(" & ".join(fila) + " \\\\")
        T = ["\\begin{table*}[!t]", "\\centering", "\\caption{Los 42 par\\'ametros de FLC-O (vector $\\theta$ de resultados/opt/" + nom_.replace("_", "\\_") + ".json). Nudos de cada variable: "
             "$k_1=|p_1|$, $k_2=k_1+|p_2|+0.05$, $k_3=k_2+|p_3|+0.05$; pesos de la vista adelante: $\\omega_k$ y $\\rho_k$ entran en valor absoluto; $c_{G,R,V}$ es el consecuente de la regla con esos conjuntos de $G$, $R$ y $V$.}",
             "\\label{tab:sparametros}", "\\scriptsize", "\\renewcommand{\\arraystretch}{1.3}", "\\begin{tabular}{@{}lrlrlr@{}}", "\\toprule", "Par\\'ametro & Valor & Par\\'ametro & Valor & Par\\'ametro & Valor \\\\", "\\midrule"] + filas + \
            ["\\bottomrule", "\\end{tabular}", "\\fuente{modelo entrenado " + nom_.replace("_", "\\_") + " (resultados/opt/" + nom_.replace("_", "\\_") + ".json); $\\theta$ con 6 decimales.}", "\\end{table*}"]
        open(f"{OUT}/tabla_s_parametros.tex", "w").write("\n".join(T) + "\n")
        # ejemplo: G = 2.0, R = 5.0, V = 10 s
        ctl = opt_flc2.FuzzyOpt(th_, True, m_["gmin"])
        ent = {"G": (2.0, ctl.kG), "R": (5.0, ctl.kR), "V": (10.0, ctl.kE)}
        mu = {k: opt_flc2.ruspini(np.array([v]), kn)[0] for k, (v, kn) in ent.items()}
        w_ = (mu["G"][:, None, None] * mu["R"][None, :, None] * mu["V"][None, None, :]).reshape(27)
        u_ = float((w_ @ ctl.c) / (w_.sum() + 1e-9))
        filas = [f"{k} = {ent[k][0]:g} & {f(mu[k][0], 4)} & {f(mu[k][1], 4)} & {f(mu[k][2], 4)} \\\\" for k in ("G", "R", "V")]
        T = ["\\begin{table}[t]", "\\centering", "\\caption{Ejemplo num\\'erico para comprobar una implementaci\\'on de FLC-O: pertenencias de $G=2$, $R=5$ y $V=10$\\,s "
             f"con los nudos de la Tabla~\\ref{{tab:sparametros}}; la salida resulta $u={u_:+.4f}$ ({'cambiar' if u_ > 0 else 'seguir en verde'}).}}",
             "\\label{tab:sejemplo}", "\\scriptsize", "\\begin{tabular}{@{}lrrr@{}}", "\\toprule", "Entrada & bajo & medio & alto \\\\", "\\midrule"] + filas + \
            ["\\bottomrule", "\\end{tabular}", "\\fuente{c\\'alculo con las Ecs. del art\\'iculo (opt\\_flc2.py).}", "\\end{table}"]
        open(f"{OUT}/tabla_s_ejemplo.tex", "w").write("\n".join(T) + "\n")

    # (b) programacion dinamica: analitico frente a simulado
    if os.path.exists("resultados/opt/mdp_oficial.json"):
        mdp = json.load(open("resultados/opt/mdp_oficial.json"))
        R = [f"{x['ns']}/{x['ew']} & {f(x['dp_analitico'])} & {f(x['dp_sim'])} & {pct(100 * (x['dp_sim'] - x['dp_analitico']) / x['dp_analitico'])} \\\\" for x in mdp]
        T = ["\\begin{table}[t]", "\\centering", "\\caption{Cota \\'optima por programaci\\'on din\\'amica: retardo que predice (ley de Little) y retardo medido "
             "al simular su pol\\'itica durante 7200\\,s con 20 r\\'eplicas (s/veh).}", "\\label{tab:smdp}", "\\scriptsize",
             "\\begin{tabular}{@{}lrrr@{}}", "\\toprule", "N-S/E-W & Predicho & Simulado & Dif.\\ (\\%) \\\\", "\\midrule"] + R + \
            ["\\bottomrule", "\\end{tabular}", "\\fuente{opt\\_mdp.py y simulaci\\'on del autor (resultados/opt/mdp\\_oficial.json).}", "\\end{table}"]
        open(f"{OUT}/tabla_s_mdp.tex", "w").write("\n".join(T) + "\n")

    # (c) sensibilidad a la semilla de entrenamiento
    sem = fin.get("semillas", [])
    R = []
    for etiqueta, modelo in sem:
        if modelo in of["delay"]:
            o = float(np.mean(of["delay"][modelo]))
            nv = float(np.mean(d["no_vistos"]["delay"][modelo])) if modelo in d["no_vistos"]["delay"] else float("nan")
            va = float(np.mean(d["variable"]["delay"][modelo])) if modelo in d["variable"]["delay"] else float("nan")
            sa = float(np.mean(d["saturado"]["delay"][modelo])) if modelo in d["saturado"]["delay"] else float("nan")
            R.append(f"{etiqueta} & {f(o)} & {f(nv, 1)} & {f(va, 1)} & {f(sa, 1)} \\\\")
    if R:
        T = ["\\begin{table}[t]", "\\centering", "\\caption{Sensibilidad de FLC-O a la semilla de entrenamiento de CMA-ES: retardo medio (s/veh) "
             "en los cuatro conjuntos de prueba.}", "\\label{tab:ssemillas}", "\\scriptsize", "\\begin{tabular}{@{}lrrrr@{}}", "\\toprule",
             "Entrenamiento & Oficial & No vistos & Variable & Saturado \\\\", "\\midrule"] + R + \
            ["\\bottomrule", "\\end{tabular}", "\\fuente{simulaci\\'on del autor; cada fila es un entrenamiento independiente con otra semilla de CMA-ES y los mismos escenarios.}", "\\end{table}"]
        open(f"{OUT}/tabla_s_semillas.tex", "w").write("\n".join(T) + "\n")
    # (d) las ocho lecturas de A y Q frente a la Tabla VIII del original (resultados/fidelity_audit.json)
    if os.path.exists("resultados/fidelity_audit.json"):
        au = json.load(open("resultados/fidelity_audit.json"))
        nomA = {"arrivals": "arribos acumulados", "crossing": "cruces (m\\'ax.\\ 1 veh/s)"}
        nomQ = {"predicted": "prevista $\\beta'_e$", "current": "actual"}
        nomS = {"total": "toda la cola", "green_arrivals": "llegados desde el inicio del verde"}
        R = []
        for v in au["variants"]:
            fila = (f"{nomA[v['a_mode']]} & {nomQ[v['q_mode']]} & {nomS[v['queue_source']]} & {f(v['mean_err'], 1)} & {f(v['max_err'], 1)} & {v['wins']}/16 \\\\")
            if v["a_mode"] == "crossing" and v["q_mode"] == "current" and v["queue_source"] == "green_arrivals":
                fila = "\\textbf{" + fila.replace(" & ", "} & \\textbf{").replace(" \\\\", "} \\\\")
            R.append(fila)
        T = ["\\begin{table*}[t]", "\\centering", "\\caption{Las ocho lecturas de $A$ y $Q$ con las 25 reglas del Ap\\'endice fijas: error relativo medio y m\\'aximo del retardo "
             "frente a los impresos en la Tabla VIII del original (20 r\\'eplicas de 7200\\,s, n\\'umeros aleatorios comunes) y pares de caudales en que el difuso queda por debajo del ciclo fijo. En negrita, la lectura adoptada.}",
             "\\label{tab:slecturas}", "\\scriptsize", "\\begin{tabular}{@{}lllrrr@{}}", "\\toprule",
             "$A$ & $Q$ evaluada en & Cola $Q$ & Error medio (\\%) & Error m\\'aximo (\\%) & Mejor que el fijo \\\\", "\\midrule"] + R + \
            ["\\bottomrule", "\\end{tabular}", "\\fuente{codigo/fidelity\\_audit.py y resultados/fidelity\\_audit.json.}", "\\end{table*}"]
        open(f"{OUT}/tabla_s_lecturas.tex", "w").write("\n".join(T) + "\n")
    print("escrito en", OUT)


if __name__ == "__main__":
    main()
