"""
web_sim.py
================================================================================
Simulador de la interseccion en la WEB (mismo motor y misma vista que la GUI
Tkinter). Muestra la animacion de la interseccion + la traza de d_m(t) + el
registro de decisiones, con controles de flujos, semilla, duracion, reglas,
umbral, modo y velocidad.

Ejecutar (Windows o Linux):
    pip install flask
    python web_sim.py
    → abrir http://localhost:8000

Notas:
  * Cada "tick" HTTP avanza EXACTAMENTE 1 segundo de simulacion (modelo pull:
    el navegador solicita el siguiente cuadro; la velocidad se controla con el
    intervalo entre solicitudes).
  * La vista se renderiza con matplotlib (backend Agg) y viaja a JPG.
  * Reproduce exactamente la logica ya validada (test_sim_engine.py).
"""
import _raiz  # noqa: F401  (cwd = carpeta del proyecto)
import base64
import io
import threading

import numpy as np
from flask import Flask, jsonify, request
from PIL import Image

import matplotlib
matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg

import sim_engine as se
from intersection_view import IntersectionView

app = Flask(__name__)
LOCK = threading.Lock()
S = {"sim": None, "view": None, "canvas": None, "fig": None, "log": []}


# ---------------------------------------------------------------------------
def _build(ns, ew, dur, seed, rules, thr, mode):
    if S["fig"] is not None:
        plt.close(S["fig"])
    cfg = se.SimConfig(lam_ns=ns / 3600.0, lam_ew=ew / 3600.0, seed=seed,
                       duration=dur, ruleset=rules, threshold=thr, mode=mode)
    sim = se.StepSim(cfg)
    fig = plt.figure(figsize=(16.0, 9.2), dpi=80)       # 1280x736 px
    canvas = FigureCanvasAgg(fig)
    view = IntersectionView(fig, rules=cfg.rules)
    view.reset()
    view.sub.set_text(
        f"reglas: {rules} · umbral {thr:.2f} · N-S {ns} veh/h · "
        f"E-W {ew} veh/h · lectura {'calibrada' if mode == 'capacity' else 'literal'} · semilla {seed}")
    S.update(sim=sim, view=view, canvas=canvas, fig=fig)
    S["log"] = []


def _frame_b64():
    w, h = S["canvas"].get_width_height()
    img = np.asarray(S["canvas"].buffer_rgba()).reshape(h, w, 4)
    buf = io.BytesIO()
    Image.fromarray(img[:, :, :3]).save(buf, "JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def _payload(st, frames=None):
    line = None
    d = st.decision
    if d is not None:
        arm = "N-S" if st.phase == 0 else "E-W"
        if d.cut:
            line = f"t={st.t:4d} {arm} v{d.elapsed:2d}s > CORTE (g={d.grade_max:.2f})"
        else:
            ids = ",".join(f"R{i + 1}" for i in d.winners)
            line = f"t={st.t:4d} {arm} v{d.elapsed:2d}s > e*={d.e_star:2d} [{d.intervention}s {ids}]"
        S["log"].append(line)
        del S["log"][:-200]
    return {
        "frame": frames[-1] if frames else _frame_b64(),
        "frames": frames or [],
        "t": st.t,
        "done": st.done,
        "dm": round(st.dm, 3),
        "q_ns": st.q_ns,
        "q_ew": st.q_ew,
        "phase": st.phase,
        "in_transition": st.in_transition,
        "decision": line,
        "duration": S["sim"].cfg.duration,
    }


# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return PAGE


def _params():
    a = request.args
    return (int(a.get("ns", 720)), int(a.get("ew", 2160)),
            int(a.get("dur", 3600)), int(a.get("seed", 1)),
            a.get("rules", "paper"), float(a.get("thr", 0.5)),
            a.get("mode", "capacity"))


SUB = 3          # sub-cuadros por segundo simulado (movimiento suave)


def _step():
    """Avanza 1 s de simulacion y devuelve (estado, lista de cuadros JPEG en base64)."""
    st = S["sim"].step()
    frames = []
    S["view"].step_render(st, sub=SUB, on_frame=lambda: frames.append(_frame_b64()))
    return st, frames


@app.route("/api/start")
def api_start():
    with LOCK:
        ns, ew, dur, seed, rules, thr, mode = _params()
        _build(ns, ew, dur, seed, rules, thr, mode)
        st, fr = _step()
        return jsonify(_payload(st, fr))


@app.route("/api/tick")
def api_tick():
    with LOCK:
        if S["sim"] is None or S["sim"].done:
            return jsonify({"error": "no hay simulacion activa"}), 400
        st, fr = _step()
        return jsonify(_payload(st, fr))


@app.route("/api/reset")
def api_reset():
    with LOCK:
        ns, ew, dur, seed, rules, thr, mode = _params()
        _build(ns, ew, dur, seed, rules, thr, mode)
        return jsonify({"frame": _frame_b64(), "t": 0, "done": False,
                        "dm": 0.0, "q_ns": 0, "q_ew": 0, "phase": 0,
                        "in_transition": False, "decision": None,
                        "duration": dur})


@app.route("/api/state")
def api_state():
    with LOCK:
        if S["sim"] is None:
            return jsonify({"exists": False})
        sim = S["sim"]
        return jsonify({"exists": True, "done": sim.done, "t": sim.t,
                        "duration": sim.cfg.duration,
                        "dm": round(sim.dm, 3),
                        "q_ns": len(sim.sim.q_ns), "q_ew": len(sim.sim.q_ew),
                        "frame": _frame_b64()})


@app.route("/api/disparos.csv")
def api_csv():
    """Descarga los disparos de reglas de la simulacion en curso (CSV)."""
    import csv
    from flask import Response
    with LOCK:
        sim = S["sim"]
        rows = sim.firing_rows() if sim is not None else []
    buf = io.StringIO()
    if rows:
        wr = csv.DictWriter(buf, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)
    return Response("\ufeff" + buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=disparos_reglas.csv"})


# ---------------------------------------------------------------------------
PAGE = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Simulador · semáforo inteligente difuso (Pappis &amp; Mamdani 1977)</title>
<style>
  body { margin:0; font-family:"Segoe UI", Arial, sans-serif; background:#eef0f2; color:#34495e; }
  header { background:#2c3e50; color:#fff; padding:10px 18px; font-size:15px; }
  header small { color:#bdc3c7; font-weight:normal; }
  .wrap { display:flex; gap:12px; padding:12px; align-items:flex-start; }
  .panel { width:300px; min-width:300px; background:#fff; border-radius:10px;
           box-shadow:0 1px 4px rgba(0,0,0,.12); padding:14px; }
  .scene { flex:1; background:#fff; border-radius:10px; box-shadow:0 1px 4px rgba(0,0,0,.12);
           padding:8px; }
  .scene img { width:100%; height:auto; border-radius:6px; display:block; }
  label { font-size:12.5px; display:block; margin-top:8px; }
  input[type=number], select { width:100%; box-sizing:border-box; padding:4px 6px;
           border:1px solid #cfd8dc; border-radius:6px; font-size:13px; }
  .row { display:flex; gap:8px; }
  .row > div { flex:1; }
  .btns { display:flex; gap:6px; margin-top:12px; }
  .btns button { flex:1; padding:7px 0; border:0; border-radius:7px; font-size:13.5px;
           cursor:pointer; background:#1f6fd6; color:#fff; }
  .btns button:disabled { background:#b0bec5; cursor:default; }
  #b_pause { background:#e67e22; } #b_step { background:#16a085; } #b_reset { background:#7f8c8d; }
  #status { margin-top:10px; font-size:13px; font-family:Consolas, monospace;
            background:#f8f9fa; border-radius:6px; padding:6px 8px; }
  #log { height:260px; overflow-y:auto; margin-top:10px; border:1px solid #e0e0e0;
         border-radius:6px; padding:6px 8px; font-family:Consolas, monospace;
         font-size:11px; background:#fff; white-space:pre; }
  .ttl { font-size:12px; text-transform:uppercase; letter-spacing:.4px;
         color:#7f8c8d; margin-top:12px; }
  .note { font-size:11.5px; color:#95a5a6; margin-top:8px; }
</style>
</head>
<body>
<header>Simulador · <b>semáforo inteligente difuso</b> (Pappis &amp; Mamdani 1977)
 <small>— réplica paso a paso (1 s por tick) de la simulación validada</small></header>
<div class="wrap">
  <div class="panel">
    <div class="row">
      <div><label>Flujo N–S (veh/h)</label><input type="number" id="ns" value="720" min="60" max="3600" step="60"></div>
      <div><label>Flujo E–W (veh/h)</label><input type="number" id="ew" value="2160" min="60" max="3600" step="60"></div>
    </div>
    <div class="row">
      <div><label>Duración (s)</label><input type="number" id="dur" value="3600" min="300" max="14400" step="300"></div>
      <div><label>Semilla</label><input type="number" id="seed" value="1" min="0" max="99999"></div>
    </div>
    <div class="row">
      <div><label>Reglas</label>
        <select id="rules">
          <option value="paper">originales (paper)</option>
        </select></div>
      <div><label>Umbral</label><input type="number" id="thr" value="0.50" min="0.30" max="0.90" step="0.05"></div>
    </div>
    <div class="row">
      <div><label>Modo</label>
        <select id="mode">
          <option value="capacity">calibrada (Tabla VIII)</option>
          <option value="literal">literal (ejemplo pág. 7)</option>
        </select></div>
      <div><label>Velocidad (fps)</label><input type="number" id="fps" value="10" min="5" max="30"></div>
    </div>
    <div class="btns">
      <button id="b_start">▶ Iniciar</button>
      <button id="b_pause" disabled>⏸ Pausa</button>
      <button id="b_step">⏭ Paso</button>
      <button id="b_reset">↺ Reiniciar</button>
    </div>
    <div id="status">Listo. Elija parámetros y pulse Iniciar.</div>
    <div class="ttl">Decisiones y regla que dispara (★ en el panel)</div>
    <div id="log"></div>
    <div class="note"><a href="/api/disparos.csv">Descargar disparos de reglas (CSV)</a></div>
    <div class="note">Los cambios de parámetros se aplican al pulsar Iniciar o Reiniciar.</div>
  </div>
  <div class="scene"><img id="frame" alt="intersección"></div>
</div>
<script>
const $ = id => document.getElementById(id);
let running = false, timer = null, built = false;

function params() {
  return "ns=" + $("ns").value + "&ew=" + $("ew").value +
         "&dur=" + $("dur").value + "&seed=" + $("seed").value +
         "&rules=" + $("rules").value + "&thr=" + $("thr").value +
         "&mode=" + $("mode").value;
}

function showStatus(st) {
  const mm = String(Math.floor(st.t / 60)).padStart(2, "0");
  const ss = String(st.t % 60).padStart(2, "0");
  $("status").textContent = st.done
    ? "Final: d_m = " + st.dm + " s/veh en " + st.t + " s"
    : "t = " + mm + ":" + ss + "   ·   d_m = " + st.dm + " s/veh   ·   cola N-S: " +
      st.q_ns + "   ·   cola E-W: " + st.q_ew;
}
function addLog(line) {
  if (!line) return;
  const el = $("log");
  el.textContent += line + "\\n";
  el.scrollTop = el.scrollHeight;
}
function draw(st) {
  const fr = (st.frames && st.frames.length) ? st.frames : [st.frame];
  const ms = 1000 / Math.max(1, +$("fps").value || 10) / fr.length;
  fr.forEach((f, i) => setTimeout(() => { $("frame").src = "data:image/jpeg;base64," + f; }, i * ms));
  showStatus(st);
  if (st.decision) addLog(st.decision);
  if (st.done) addLog("--- final: d_m = " + st.dm + " s/veh ---");
}
function setButtons() {
  $("b_start").disabled = running;
  $("b_pause").disabled = !running;
}
async function loop() {
  if (!running) return;
  try {
    const r = await fetch("/api/tick");
    if (!r.ok) throw 0;
    const st = await r.json();
    draw(st);
    if (st.done) { running = false; setButtons(); return; }
  } catch (e) {
    running = false; setButtons();
    $("status").textContent = "Error de conexión con el servidor.";
    return;
  }
  timer = setTimeout(loop, 1000 / Math.max(1, +$("fps").value || 10));
}
$("b_start").onclick = async () => {
  if (running) return;
  $("log").textContent = "";
  const r = await fetch("/api/start?" + params());
  const st = await r.json();
  built = true;
  draw(st);
  if (!st.done) { running = true; setButtons(); loop(); }
};
$("b_pause").onclick = () => {
  running = !running;
  $("b_pause").textContent = running ? "⏸ Pausa" : "▶ Continuar";
  setButtons();
  if (running) loop();
};
$("b_step").onclick = async () => {
  if (running) $("b_pause").onclick();
  let url = "/api/tick";
  if (!built) { url = "/api/start?" + params(); built = true; $("log").textContent = ""; }
  const r = await fetch(url);
  if (r.ok) draw(await r.json());
};
$("b_reset").onclick = async () => {
  running = false; setButtons();
  $("b_pause").textContent = "⏸ Pausa";
  const r = await fetch("/api/reset?" + params());
  const st = await r.json();
  built = true;
  $("log").textContent = "";
  draw(st);
  $("status").textContent = "Simulación lista (" + st.duration + " s). Pulse Iniciar o Paso.";
};
// si la pagina se recarga con una simulacion previa, la muestra
(async () => {
  try {
    const st = await (await fetch("/api/state")).json();
    if (st.exists) {
      built = true;
      $("frame").src = "data:image/jpeg;base64," + st.frame;
      showStatus(st);
      if (!st.done) {
        $("b_pause").disabled = false;
        $("b_pause").textContent = "▶ Continuar";
      }
    }
  } catch (e) {}
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)
