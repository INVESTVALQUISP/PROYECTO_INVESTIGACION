"""
gen_tablas_opt.py
================================================================================
Lee resultados/opt/evaluacion_final.json y resultados/opt/modelos_finales.json y escribe en articulo_opt/:
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

import opt_flc2
from opt_nombres import ETIQUETA, clave, finales

OUT = "articulo_opt"
SETS = {"oficial": "Of", "no_vistos": "Nv", "variable": "Va", "saturado": "Sa"}
CTRL = {"fijo": "Fijo", "actuado": "Act", "actuado_af": "ActAf", "maxpressure": "Max", "pappis": "Pap",
        "afinado_pappis": "PapAf", "mdp": "Mdp", "flc": "Flc", "flc_causal": "FlcC", "mlp": "Mlp", "mlp_causal": "MlpC"}


def f(x, n=2):
    return f"{x:.{n}f}"


def pct(x, n=1):
    return f"{x:+.{n}f}".replace("-", "$-$")


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
            L.append(f"\\newcommand{{\\Red{rn}}}{{{100 * (base['pappis'] - base[r]) / base['pappis']:.1f}}}")
    for s, sn in SETS.items():
        if "flc" in med[s] and "pappis" in med[s]:
            L.append(f"\\newcommand{{\\RedPap{sn}}}{{{100 * (med[s]['pappis'] - med[s]['flc']) / med[s]['pappis']:.1f}}}")
        if "flc" in med[s] and "actuado_af" in med[s]:
            L.append(f"\\newcommand{{\\RedActAf{sn}}}{{{100 * (med[s]['actuado_af'] - med[s]['flc']) / med[s]['actuado_af']:.1f}}}")
    comp = of["comparaciones"]
    for r, rn in (("pappis", "Pap"), ("actuado_af", "ActAf"), ("actuado", "Act"), ("fijo", "Fijo"), ("mdp", "Mdp"), ("afinado_pappis", "PapAf")):
        k = f"{key['flc']}__vs__{key[r]}"
        if k in comp:
            c = comp[k]
            L.append(f"\\newcommand{{\\ParMedia{rn}}}{{{c['mejora_media_pct']:.1f}}}")
            L.append(f"\\newcommand{{\\ParMejor{rn}}}{{{c['mejor_signif']}}}")
            L.append(f"\\newcommand{{\\ParPeor{rn}}}{{{c['peor_signif']}}}")
            L.append(f"\\newcommand{{\\ParMin{rn}}}{{{min(c['mejora_por_par']):.1f}}}")
            L.append(f"\\newcommand{{\\ParMax{rn}}}{{{max(c['mejora_por_par']):.1f}}}")
    if os.path.exists("resultados/opt/mdp_oficial.json"):
        mdp = json.load(open("resultados/opt/mdp_oficial.json"))
        dif = max(abs(x["dp_sim"] - x["dp_analitico"]) / x["dp_analitico"] * 100 for x in mdp)
        L.append(f"\\newcommand{{\\PdMaxDif}}{{{dif:.1f}}}")
    open(f"{OUT}/numeros.tex", "w").write("\n".join(L) + "\n")

    # ---------------- tabla_oficial.tex
    cols = ["fijo", "actuado_af", "pappis", "flc", "mdp"]
    kc = f"{key['flc']}__vs__{key['pappis']}"
    rows = []
    for i, (a, b) in enumerate(pares):
        vals = [of["por_par"][key[r]][i]["media"] for r in cols]
        gan = comp[kc]["mejora_por_par"][i]
        sig = "$^{*}$" if comp[kc]["p_holm"][i] < 0.05 else ""
        mejor = int(np.argmin(vals[:4]))
        cells = [(f"\\textbf{{{f(v)}}}" if j == mejor else f(v)) for j, v in enumerate(vals[:4])]
        rows.append(f"{int(a)} / {int(b)} & " + " & ".join(cells) + f" & {pct(gan)}{sig} & {f(vals[4])} \\\\")
    mv = [np.mean([of["por_par"][key[r]][i]["media"] for i in range(len(pares))]) for r in cols]
    rows.append("\\midrule")
    rows.append("Media & " + " & ".join(f(v) for v in mv[:4]) + f" & {pct(comp[kc]['mejora_media_pct'])} & {f(mv[4])} \\\\")
    T = ["\\begin{table}[t]", "\\centering", "\\caption{Retardo medio por veh\\'iculo (s) en los 16 pares de caudales de la Tabla VIII del art\\'iculo original, "
         "con 20 r\\'eplicas de 7200 s y n\\'umeros aleatorios comunes. Se cuenta la espera de todos los veh\\'iculos hasta el horizonte. "
         "$\\Delta$: mejora de FLC-O frente a Pappis y Mamdani (\\%); $^{*}$: significativa (Wilcoxon pareado, Holm, 0.05). "
         "En negrita, el menor de las cuatro primeras columnas.}", "\\label{tab:oficial}", "\\scriptsize", "\\setlength{\\tabcolsep}{2.6pt}",
         "\\begin{tabular}{@{}lrrrrrr@{}}", "\\toprule",
         "N-S / E-W (veh/h) & Webster & Actuado af. & Pappis & FLC-O & $\\Delta$ (\\%) & \\'Optimo$^{\\dagger}$ \\\\", "\\midrule"] + rows + \
        ["\\bottomrule", "\\end{tabular}",
         "\\fuente{simulaci\\'on del autor (resultados/opt/evaluacion\\_final.json); $^{\\dagger}$ cota por programaci\\'on din\\'amica que conoce los caudales y no ve llegadas futuras (Sec.~\\ref{sec:pd}).}",
         "\\end{table}"]
    open(f"{OUT}/tabla_oficial.tex", "w").write("\n".join(T) + "\n")

    # ---------------- tabla_conjuntos.tex
    orden = ["fijo", "actuado", "actuado_af", "maxpressure", "pappis", "afinado_pappis", "flc", "mdp", "mlp"]
    R = []
    for r in orden:
        if r not in med["oficial"]:
            continue
        cells = []
        for s in SETS:
            v = med[s].get(r)
            cells.append("--" if v is None else f(v, 1))
        R.append(f"{ETIQUETA[r]} & " + " & ".join(cells) + " \\\\")
    T = ["\\begin{table}[t]", "\\centering", "\\caption{Retardo medio (s/veh) en los conjuntos de prueba. Oficial: Tabla VIII, 16 pares $\\times$ 20 r\\'eplicas. "
         "No vistos: 64 pares sorteados con otras semillas. Variable: demanda por tramos de 600 s con factor de 0.4 a 1.6. "
         "Saturado: suma de caudales de 3000 a 3300 veh/h. Todos con 7200 s.}", "\\label{tab:conjuntos}", "\\scriptsize",
         "\\begin{tabular}{@{}lrrrr@{}}", "\\toprule", "Controlador & Oficial & No vistos & Variable & Saturado \\\\", "\\midrule"] + R + \
        ["\\bottomrule", "\\end{tabular}",
         "\\fuente{simulaci\\'on del autor (resultados/opt/evaluacion\\_final.json). El \\'optimo no se calcula en el conjunto saturado (la cola truncada de la programaci\\'on din\\'amica no es fiable all\\'i).}",
         "\\end{table}"]
    open(f"{OUT}/tabla_conjuntos.tex", "w").write("\n".join(T) + "\n")

    # ---------------- tabla_comparaciones.tex
    R = []
    for r in ("pappis", "afinado_pappis", "fijo", "actuado", "actuado_af", "mdp"):
        k = f"{key['flc']}__vs__{key[r]}"
        if k in comp:
            c = comp[k]
            R.append(f"{ETIQUETA[r]} & {pct(c['mejora_media_pct'])} & {pct(min(c['mejora_por_par']))} a {pct(max(c['mejora_por_par']))} & "
                     f"{c['mejor_signif']} & {c['peor_signif']} \\\\")
    T = ["\\begin{table}[t]", "\\centering", "\\caption{FLC-O frente a cada referencia en la Tabla VIII: mejora media del retardo por par de caudales (\\%), "
         "intervalo de las 16 mejoras y n\\'umero de pares (de 16) en que es significativamente mejor o peor "
         "(Wilcoxon pareado sobre 20 r\\'eplicas, correcci\\'on de Holm, 0.05).}", "\\label{tab:comparaciones}", "\\scriptsize",
         "\\begin{tabular}{@{}lrrrr@{}}", "\\toprule", "Referencia & Mejora media & Intervalo & Mejor & Peor \\\\", "\\midrule"] + R + \
        ["\\bottomrule", "\\end{tabular}", "\\fuente{simulaci\\'on del autor; Wilcoxon exacto o con aproximaci\\'on normal seg\\'un empates (estadistica.py).}", "\\end{table}"]
    open(f"{OUT}/tabla_comparaciones.tex", "w").write("\n".join(T) + "\n")

    # ---------------- tabla_ablacion.tex (filas definidas en modelos_finales.json)
    abl = fin.get("ablacion", [])
    R = []
    for etiqueta, modelo, npar, nota in abl:
        if modelo not in of["delay"]:
            continue
        o = float(np.mean(of["delay"][modelo]))
        nv = float(np.mean(d["no_vistos"]["delay"][modelo])) if modelo in d["no_vistos"]["delay"] else float("nan")
        va = float(np.mean(d["variable"]["delay"][modelo])) if modelo in d["variable"]["delay"] else float("nan")
        R.append(f"{etiqueta} & {npar} & {nota} & {f(o)} & {f(nv, 1)} & {f(va, 1)} \\\\")
    if R:
        T = ["\\begin{table}[t]", "\\centering", "\\caption{Variantes de FLC-O y controladores aprendidos. Retardo medio (s/veh) en la Tabla VIII, "
             "en caudales no vistos y con demanda variable. $g_{\\min}$: verde m\\'inimo.}", "\\label{tab:ablacion}", "\\scriptsize",
             "\\setlength{\\tabcolsep}{2.4pt}", "\\begin{tabular}{@{}lrlrrr@{}}", "\\toprule",
             "Variante & Par. & Informaci\\'on & Oficial & No vistos & Variable \\\\", "\\midrule"] + R + \
            ["\\bottomrule", "\\end{tabular}", "\\fuente{simulaci\\'on del autor; par.: n\\'umero de par\\'ametros entrenados.}", "\\end{table}"]
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
        kk = lambda k: ", ".join(f"{x:.1f}" for x in k)
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
    # (a) todos los pares: media, sd, IC95 y p de Holm de FLC-O frente a Pappis y al actuado afinado
    kp = f"{key['flc']}__vs__{key['pappis']}"
    ka = f"{key['flc']}__vs__{key['actuado_af']}"
    R = []
    for i, (a_, b_) in enumerate(pares):
        pp, aa, ff = of["por_par"][key["pappis"]][i], of["por_par"][key["actuado_af"]][i], of["por_par"][key["flc"]][i]
        R.append(f"{int(a_)}/{int(b_)} & {f(pp['media'])} $\\pm$ {f(pp['sd'])} & {f(aa['media'])} $\\pm$ {f(aa['sd'])} & "
                 f"{f(ff['media'])} $\\pm$ {f(ff['sd'])} & [{f(ff['ic_lo'])}, {f(ff['ic_hi'])}] & "
                 f"{pct(comp[kp]['mejora_por_par'][i])} & {comp[kp]['p_holm'][i]:.1e} & {pct(comp[ka]['mejora_por_par'][i])} & {comp[ka]['p_holm'][i]:.1e} \\\\")
    T = ["\\begin{table*}[!t]", "\\centering", "\\caption{Conjunto oficial: media $\\pm$ desviaci\\'on est\\'andar muestral (20 r\\'eplicas, $n-1$) del retardo (s/veh), "
         "IC de 95\\,\\% de FLC-O y mejora de FLC-O frente a Pappis y Mamdani y frente al actuado afinado con su $p$ de Wilcoxon corregido por Holm.}",
         "\\label{tab:spares}", "\\scriptsize", "\\begin{tabular}{@{}lrrrrrrrr@{}}", "\\toprule",
         "N-S/E-W & Pappis y Mamdani & Actuado afinado & FLC-O & IC 95\\,\\% FLC-O & $\\Delta_P$ (\\%) & $p_P$ & $\\Delta_A$ (\\%) & $p_A$ \\\\", "\\midrule"] + R + \
        ["\\bottomrule", "\\end{tabular}", "\\fuente{simulaci\\'on del autor (resultados/opt/evaluacion\\_final.json); $\\Delta$: reducci\\'on relativa del retardo medio del par.}", "\\end{table*}"]
    open(f"{OUT}/tabla_s_pares.tex", "w").write("\n".join(T) + "\n")

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
    print("escrito en", OUT)


if __name__ == "__main__":
    main()
