"""
ejecutar_pruebas.py
================================================================================
Corre TODAS las pruebas de la replica y muestra un resumen para presentar que el
sistema funciona. Deja el texto en salidas/pruebas.txt.

  1. test_paper_tables.py : conjuntos, operadores, 25 reglas y ejemplo del paper
  2. test_sim_engine.py   : el simulador paso a paso == la simulacion por lotes
  3. test_disparos.py     : el panel de reglas/disparos muestra lo que calcula el controlador
  3b. test_autos.py       : autos con separacion segura, reglas apagadas, autos a mano y explicaciones
  3c. test_parametros.py, test_estadistica.py, verificar_formulas.py : parametros explicitos, estadistica y deducciones
  3c'. test_sim_batch.py : el simulador vectorizado (rama de optimizacion) reproduce exactamente al de referencia
  3c''. test_opt.py : componentes de la optimizacion (CMA-ES, programacion dinamica, FLC-O)
  3d. test_archivos_citados.py : todo archivo citado por el articulo existe (reproducibilidad del paquete)
  4. Resultados oficiales : Tabla I y Tabla VIII (leidos de resultados/resultados_oficiales.json)

Uso:
  python ejecutar_pruebas.py             # rapido (segundos)
  python ejecutar_pruebas.py --rapido    # ademas recalcula una Tabla VIII reducida (~20 s)
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import argparse
import json
import os
import re
import subprocess
import sys
import time

import numpy as np

import paper_data as pdta

OUT = "salidas"
lines = []


def say(text=""):
    print(text)
    lines.append(text)


def run_test(script, ok_regex, label):
    t0 = time.time()
    p = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), script)], capture_output=True, text=True)
    out = p.stdout
    n_ok = out.count("[OK]") or len(re.findall(r" OK\s*$", out, re.M))
    n_fail = out.count("[FALLO]") + len(re.findall(r"FALLO\s*$", out, re.M))
    m = re.search(ok_regex, out)
    extra = f" ({m.group(0)})" if m else ""
    status = "CORRECTO" if p.returncode == 0 else "FALLO"
    say(f"  {status:9s} {label:58s} {n_ok:3d} comprobaciones OK, {n_fail} fallidas{extra}  [{time.time() - t0:.1f} s]")
    if p.returncode != 0:
        say(out[-1500:])
    return p.returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rapido", action="store_true", help="recalcula una Tabla VIII reducida (3 x 1800 s)")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    say("=" * 100)
    say(" VALIDACION DE LA REPLICA — Pappis y Mamdani (1977), controlador difuso de semaforos")
    say("=" * 100)
    say("\n1) Pruebas automaticas")
    ok = True
    ok &= run_test("test_paper_tables.py", r"TODO OK", "Tablas II-VI, 25 reglas, ejemplo de la pag. 7 (Tabla VII), 57 s")
    ok &= run_test("test_sim_engine.py", r"\d+/\d+ equivalencias", "Simulador paso a paso == simulacion por lotes")
    ok &= run_test("test_disparos.py", r"TODO OK", "Panel de reglas y disparos == controlador")
    ok &= run_test("test_autos.py", r"TODO OK", "Autos sin superponerse, reglas apagadas, autos a mano, explicaciones")
    ok &= run_test("test_parametros.py", r"TODO OK", "Lecturas de A y Q explicitas, mt/lt = Tabla V, contabilidad del retardo")
    ok &= run_test("test_sim_batch.py", r"TODO OK", "Simulador vectorizado == simulador de referencia (exacto)")
    ok &= run_test("test_opt.py", r"TODO OK", "CMA-ES, particion de Ruspini, programacion dinamica, FLC-O y Pappis afinado")
    ok &= run_test("test_estadistica.py", r"TODO OK", "Wilcoxon, Friedman, Holm, t y chi2 (valores conocidos)")
    ok &= run_test("verificar_formulas.py", r"TODO OK", "Deducciones matematicas del articulo = calculos independientes")
    ok &= run_test("test_archivos_citados.py", r"TODO OK", "Todo script, JSON, CSV y fuente LaTeX citado existe y compila")
    ok &= run_test("test_archivos_citados_opt.py", r"TODO OK", "Idem para el articulo de optimizacion (articulo/)")

    say("\n2) Resultados oficiales (20 replicas x 7200 s, ver resultados/resultados_oficiales.json)")
    path = "resultados/resultados_oficiales.json"
    if os.path.exists(path):
        res = json.load(open(path))
        t1 = res["table_I"]
        e_sim = np.mean([abs(r["sim"] - pdta.TABLE_I[(r["ns"], r["ew"])][0]) / pdta.TABLE_I[(r["ns"], r["ew"])][0] for r in t1]) * 100
        e_for = np.mean([abs(r["formula"] - pdta.TABLE_I[(r["ns"], r["ew"])][1]) / pdta.TABLE_I[(r["ns"], r["ew"])][1] for r in t1]) * 100
        say(f"  Tabla I (modelo, ciclo fijo de Webster): error medio {e_sim:.1f} % (simulacion) y {e_for:.1f} % (formula)")
        say("\n  Tabla VIII (difuso vs ciclo fijo), retardo medio en s/veh")
        say(f"  {'N-S':>5} {'E-W':>5} | {'fijo':>6} | {'difuso':>7} {'paper':>6} {'err %':>7} | {'mejora':>7}")
        cal = res["table_VIII"]["calibrada"]
        wins = 0
        errs = []
        for r in cal:
            pz = pdta.TABLE_VIII[(r["ns"], r["ew"])][1]
            wins += r["fuzzy"] < r["fixed"]
            errs.append(abs(r["fuzzy"] - pz) / pz * 100)
            say(f"  {r['ns']:5d} {r['ew']:5d} | {r['fixed']:6.2f} | {r['fuzzy']:7.2f} {pz:6.1f} {100 * (r['fuzzy'] - pz) / pz:+7.1f} | {r['improvement']:+6.0f} %")
        say(f"\n  El difuso mejora al ciclo fijo en {wins}/16 combinaciones (paper: 16/16); "
            f"error medio frente al paper {np.mean(errs):.1f} %, maximo {np.max(errs):.1f} %.")
    else:
        say("  (falta resultados/resultados_oficiales.json: ejecute python run_experiments.py)")

    if args.rapido:
        import traffic_model as tm
        say("\n3) Tabla VIII reducida recalculada ahora (3 replicas x 1800 s; solo para mostrar que corre)")
        rows = tm.run_table(reps=3, duration=1800, base_seed=0, **tm.CALIBRADA)
        w = sum(r[3] < r[2] for r in rows)
        say(f"  {'N-S':>5} {'E-W':>5} | {'fijo':>6} {'difuso':>7}")
        for ns, ew, fx, fz, imp in rows:
            say(f"  {ns:5d} {ew:5d} | {fx:6.2f} {fz:7.2f}")
        say(f"  difuso mejor que fijo en {w}/16 combinaciones (corrida corta: hay mas ruido que en la oficial)")

    say("\n" + ("TODAS LAS PRUEBAS CORRECTAS" if ok else "HAY PRUEBAS FALLIDAS"))
    with open(os.path.join(OUT, "pruebas.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    say(f"(resumen guardado en {OUT}/pruebas.txt)")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
