"""
gen_justificacion.py
================================================================================
Genera las cifras y la tabla del documento articulo/justificacion.tex (por que se eligio FLC-O) a partir de los
resultados guardados, de modo que nada del documento se escribe a mano:
  articulo/justificacion_datos.tex  macros con las cifras (\\J...)
  articulo/tabla_j_modelos.tex      tabla de candidatos: parametros, J de entrenamiento y de validacion, retardo en los
                                    cuatro conjuntos de prueba
Calcula aqui, con los escenarios de VALIDACION (semillas 200000+), el valor de J de cada candidato (21 s), y la
comparacion pareada FLC-O frente a la politica neuronal en el conjunto oficial (Wilcoxon + Holm).
Requiere haber corrido opt_evaluacion_final.py (resultados/opt/evaluacion_final.json).
Uso:  python gen_justificacion.py
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import opt_flc2
from opt_entrenar import escenarios_validacion, actuado_afinado
from opt_evaluacion_final import cargar_modelos, construir_modelo
from opt_evaluar import comparar

OUT = "articulo"
SETS = ("oficial", "no_vistos", "variable", "saturado")
M = {}                      # macros


def neg(txt):
    return txt.replace("-", "$-$")


def f2(x):
    return neg(f"{x:.2f}")


def f1(x):
    return neg(f"{x:.1f}")


def f3(x):
    return neg(f"{x:.3f}")


def macro(nombre, valor):
    M[nombre] = valor


def main():
    ev = json.load(open("resultados/opt/evaluacion_final.json"))
    fin = json.load(open("resultados/opt/modelos_finales.json"))
    media = {s: {n: float(np.mean(v)) for n, v in ev[s]["delay"].items()} for s in SETS}

    # ---------------------------------------------------------------- J de validacion de cada candidato
    fl, arr = escenarios_validacion(64, suma_max=3300)
    ref = actuado_afinado(arr)["delay"]
    todos = cargar_modelos()
    nombres = ["afinado_v3", "flcs_v3_g3", "flcs4_v3_g3", "flcopt_g3", "flcopt_g3_s1", "flcopt_g3_s2", "flcopt_g4", "flcopt_g5",
               "flcopt_g7", "mlp_v3_g3", "flcs_causal_v3_g3", "lineal_causal_v3_g3", "mlp_causal_v3_g3"]
    jval, jtr, npar = {}, {}, {}
    for n in nombres:
        mk, ctrl = construir_modelo(todos[n])
        r = mk(arr).run(ctrl)
        jval[n] = float(np.mean(r["delay"] / ref))
        m = json.load(open(f"resultados/opt/{n}.json"))
        jtr[n] = float(m["fitness_train"])
        npar[n] = len(m["theta"])
    gens = len(json.load(open("resultados/opt/flcopt_g3_s2.json"))["historial"])

    # ---------------------------------------------------------------- tabla de candidatos
    filas = [
        ("Actuado afinado (referencia)", "3", "no", None, None, "actuado_af"),
        ("Pappis y Mamdani (1977)", "0", "10 s", None, None, "pappis"),
        ("Pappis y Mamdani afinado (25 reglas)", str(npar["afinado_v3"]), "10 s", jtr["afinado_v3"], jval["afinado_v3"], "afinado_v3"),
        ("Difuso 27 reglas, horizontes fijos", str(npar["flcs_v3_g3"]), "10 s", jtr["flcs_v3_g3"], jval["flcs_v3_g3"], "flcs_v3_g3"),
        ("Difuso 81 reglas con hueco", str(npar["flcs4_v3_g3"]), "10 s", jtr["flcs4_v3_g3"], jval["flcs4_v3_g3"], "flcs4_v3_g3"),
        ("FLC-O, $g_{\\min}=7$\\,s", "42", "10 s", jtr["flcopt_g7"], jval["flcopt_g7"], "flcopt_g7"),
        ("FLC-O, $g_{\\min}=5$\\,s", "42", "10 s", jtr["flcopt_g5"], jval["flcopt_g5"], "flcopt_g5"),
        ("FLC-O, $g_{\\min}=4$\\,s", "42", "10 s", jtr["flcopt_g4"], jval["flcopt_g4"], "flcopt_g4"),
        ("FLC-O, $g_{\\min}=3$\\,s, semilla 0", "42", "10 s", jtr["flcopt_g3"], jval["flcopt_g3"], "flcopt_g3"),
        ("FLC-O, $g_{\\min}=3$\\,s, semilla 1", "42", "10 s", jtr["flcopt_g3_s1"], jval["flcopt_g3_s1"], "flcopt_g3_s1"),
        ("\\textbf{FLC-O, $g_{\\min}=3$\\,s, semilla 2 (elegido)}", "42", "10 s", jtr["flcopt_g3_s2"], jval["flcopt_g3_s2"], "flcopt_g3_s2"),
        ("Política neuronal", str(npar["mlp_v3_g3"]), "10 s", jtr["mlp_v3_g3"], jval["mlp_v3_g3"], "mlp_v3_g3"),
        ("Difuso 27 reglas, causal", str(npar["flcs_causal_v3_g3"]), "no", jtr["flcs_causal_v3_g3"], jval["flcs_causal_v3_g3"], "flcs_causal_v3_g3"),
        ("Política lineal causal", str(npar["lineal_causal_v3_g3"]), "no", jtr["lineal_causal_v3_g3"], jval["lineal_causal_v3_g3"], "lineal_causal_v3_g3"),
        ("Política neuronal causal", str(npar["mlp_causal_v3_g3"]), "no", jtr["mlp_causal_v3_g3"], jval["mlp_causal_v3_g3"], "mlp_causal_v3_g3"),
    ]
    L = ["% Generado por gen_justificacion.py (no editar a mano)",
         "\\begin{table*}[t]", "\\centering",
         "\\caption{Candidatos entrenados con las mismas condiciones: $J$ de entrenamiento (3600\\,s, 64 escenarios) y de validación "
         "(7200\\,s, 64 escenarios distintos; 1 es igual al actuado afinado, menos es mejor) y retardo medio en los cuatro conjuntos de prueba (s/veh)}",
         "\\label{tab:jmodelos}", "\\footnotesize", "\\setlength{\\tabcolsep}{3.5pt}",
         "\\begin{tabular}{@{}p{5.3cm}rcrrrrrr@{}}", "\\toprule",
         "Candidato & Par. & Vista & $J$ entr. & $J$ val. & Oficial & No vistos & Variable & Saturado \\\\", "\\midrule"]
    for nom, p, vista, jt, jv, clave in filas:
        d = [f2(media[s][clave]) for s in SETS]
        a = "--" if jt is None else f3(jt)
        b = "1" if clave == "actuado_af" else ("--" if jv is None else f3(jv))
        L.append(f"{nom} & {p} & {vista} & {a} & {b} & " + " & ".join(d) + " \\\\")
        if clave in ("pappis", "afinado_v3", "flcs4_v3_g3", "flcopt_g3_s2", "mlp_v3_g3"):
            L.append("\\midrule")
    L += ["\\bottomrule", "\\end{tabular}",
          "\\fuente{\\texttt{resultados/opt/evaluacion\\_final.json} (prueba), \\texttt{codigo/opt\\_validar.py} (validación) y "
          "campo \\texttt{fitness\\_train} de cada modelo de \\texttt{resultados/opt/} (entrenamiento); tabla generada por "
          "\\texttt{codigo/gen\\_justificacion.py}.}", "\\end{table*}"]
    open(f"{OUT}/tabla_j_modelos.tex", "w", encoding="utf-8").write("\n".join(L) + "\n")

    # ---------------------------------------------------------------- macros
    macro("JGens", str(gens))
    lam = 4 + int(3 * np.log(42))
    macro("JLambda", str(lam))
    macro("JMu", str(lam // 2))
    macro("JNEval", f"{gens * lam * 64:,}".replace(",", "\\,"))
    horas = gens * lam * 64 * (3600 / 7200) * 0.230 / 3600
    macro("JHorasRef", f1(horas))
    for k, n in (("Flc", "flcopt_g3_s2"), ("FlcCero", "flcopt_g3"), ("FlcUno", "flcopt_g3_s1"), ("Mlp", "mlp_v3_g3"),
                 ("GCuatro", "flcopt_g4"), ("GCinco", "flcopt_g5"), ("GSiete", "flcopt_g7"), ("FlcsFijos", "flcs_v3_g3"),
                 ("FlcsGap", "flcs4_v3_g3"), ("PapAf", "afinado_v3"), ("MlpC", "mlp_causal_v3_g3"), ("LinC", "lineal_causal_v3_g3"),
                 ("FlcC", "flcs_causal_v3_g3")):
        macro("JVal" + k, f3(jval[n]))
        macro("JTr" + k, f3(jtr[n]))
    macro("JBrecha", f1(100 * (jval["flcopt_g3_s2"] - jtr["flcopt_g3_s2"]) / jtr["flcopt_g3_s2"]))
    # razon de medias retardo(FLC-O) / retardo(actuado afinado) en cada conjunto de prueba
    for k, s in (("Of", "oficial"), ("Nv", "no_vistos"), ("Va", "variable"), ("Sa", "saturado")):
        macro("JRaz" + k, f3(media[s]["flcopt_g3_s2"] / media[s]["actuado_af"]))
    # semillas de entrenamiento
    sem = [media["oficial"][n] for n in ("flcopt_g3", "flcopt_g3_s1", "flcopt_g3_s2")]
    pap = media["oficial"]["pappis"]
    macro("JSemCero", f2(sem[0]))
    macro("JSemUno", f2(sem[1]))
    macro("JRedMlpSem", f1(100 * (1 - np.mean(sem) / media["oficial"]["mlp_v3_g3"])))
    macro("JSemMedia", f2(float(np.mean(sem))))
    r_act = json.load(open("resultados/opt/actuado_afinado.json"))["mejor"]["ratio"]
    macro("JActAfRatio", f3(r_act))
    macro("JActAfMejora", f1(100 * (1 - r_act)))
    macro("JSemPeor", f2(max(sem)))
    macro("JSemMejor", f2(min(sem)))
    macro("JRedSemMedia", f1(100 * (1 - np.mean(sem) / pap)))
    macro("JRedSemPeor", f1(100 * (1 - max(sem) / pap)))
    macro("JSemRango", f2(max(sem) - min(sem)))
    # convencion del retardo: con espera residual (articulo) frente a solo vehiculos servidos (replica anterior)
    for k, s in (("Of", "oficial"), ("Sa", "saturado")):
        for c, n in (("Pap", "pappis"), ("Flc", "flcopt_g3_s2")):
            macro(f"J{c}Res{k}", f2(media[s][n]))
            macro(f"J{c}Serv{k}", f2(float(np.mean(ev[s]["delay_servidos"][n]))))
    pr, ps = media["saturado"]["pappis"], float(np.mean(ev["saturado"]["delay_servidos"]["pappis"]))
    macro("JOcultoSa", f1(100 * (pr - ps) / pr))
    # cuanto aporta la vista adelante
    macro("JGanaVista", f1(100 * (media["oficial"]["mlp_causal_v3_g3"] - media["oficial"]["flcopt_g3_s2"]) / media["oficial"]["mlp_causal_v3_g3"]))
    # FLC-O frente a la politica neuronal, conjunto oficial, por par y con Holm
    c = comparar(np.asarray(ev["oficial"]["delay"]["flcopt_g3_s2"]), np.asarray(ev["oficial"]["delay"]["mlp_v3_g3"]))
    macro("JFlcMlpMejor", str(c["mejor_signif"]))
    macro("JFlcMlpPeor", str(c["peor_signif"]))
    macro("JFlcMlpMedia", f1(c["mejora_media_pct"]))
    # forma aprendida de FLC-O
    th = np.array(json.load(open("resultados/opt/flcopt_g3_s2.json"))["theta"])
    ctrl = opt_flc2.FuzzyOpt(th, True, 3)
    a, b = ctrl.alfa, ctrl.beta
    for i, v in enumerate(a):
        macro("JAlfa" + "ABC"[i], f2(v))
    for i, v in enumerate(b):
        macro("JBeta" + "ABC"[i], f2(v))
    macro("JWgA", f2(a.sum()))              # peso efectivo por vehiculo que llega en los 2 primeros s (verde)
    macro("JWgB", f2(a[1] + a[2]))          # s 3 a 5
    macro("JWgC", f2(a[2]))                 # s 6 a 10
    macro("JWrA", f2(b.sum()))              # s 1 a 3 (rojo)
    macro("JWrB", f2(b[1] + b[2]))          # s 4 a 6
    macro("JWrC", f2(b[2]))                 # s 7 a 10
    for nom, k in (("G", ctrl.kG), ("R", ctrl.kR), ("V", ctrl.kE)):
        for i, v in enumerate(k):
            macro(f"JK{nom}" + "ABC"[i], f2(float(v)))
    macro("JNPos", str(int((ctrl.c > 0).sum())))
    macro("JNNeg", str(int((ctrl.c <= 0).sum())))
    macro("JCMin", f2(float(ctrl.c.min())))
    macro("JCMax", f2(float(ctrl.c.max())))

    L = ["% Generado por gen_justificacion.py (no editar a mano)"]
    L += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in M.items()]
    open(f"{OUT}/justificacion_datos.tex", "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("escritos", f"{OUT}/justificacion_datos.tex", f"({len(M)} macros) y", f"{OUT}/tabla_j_modelos.tex")
    print("validacion:", {k: round(v, 4) for k, v in sorted(jval.items(), key=lambda kv: kv[1])})
    print("FLC-O frente a la red neuronal (oficial):", c["mejor_signif"], "mejor,", c["peor_signif"], "peor,", f"{c['mejora_media_pct']:.1f} % medio")


if __name__ == "__main__":
    main()
