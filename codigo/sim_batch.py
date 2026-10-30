"""
sim_batch.py
================================================================================
Simulador por LOTES de la interseccion aislada de dos fases: simula R escenarios a la vez con NumPy
(un escenario = un par de caudales + una semilla). Es la misma dinamica que traffic_model.py:

  * dos brazos de un carril, flujo de saturacion de 1 veh/s, tiempo perdido de 5 s por cambio de fase;
  * llegadas Bernoulli (un numero aleatorio por segundo), generadas con numpy.random.default_rng(semilla),
    primero el brazo N-S y despues el E-W (como _make_arrivals), de modo que los numeros aleatorios son
    identicos a los del simulador de referencia;
  * la descarga es de 1 vehiculo por segundo en el brazo con verde.

Retardo. La espera total de todos los vehiculos hasta el horizonte H es la suma por segundo de las colas,
    D = sum_{t=0}^{H-1} (Q_NS,t + Q_EW,t)     (colas al final de cada segundo, tras llegadas y descarga),
que coincide con total_delay + residual_delay de traffic_model.Sim. Con ella la simulacion no necesita las
listas FIFO: solo mantiene las longitudes de cola. El retardo medio es D / (llegadas en [0, H)).
La convencion del articulo original (solo vehiculos ya servidos, sin el residuo) se obtiene aparte
(retardo_servidos) para poder comparar.

Un controlador implementa (todos opcionales):
  on_green_start(sim, idx)   -> (n,) duracion del verde, o None si el verde lo decide otro metodo
  decide(sim, ctx)           -> (n,) extension e* en s (0 = cortar el verde) en las epocas de decision
  stop(sim, t, idx)          -> (n,) bool: terminar el verde ahora (control por detector, cada segundo)
Las epocas de decision son el_verde = gmin + k*delta (k >= 0) mientras el_verde < max_verde.

Uso:
    arr = make_arrivals(lam_ns, lam_ew, seeds, 7200)
    res = BatchSim(arr).run(PappisFuzzy())
    res["delay"]            # retardo medio por vehiculo (con residuo), forma (R,)
"""
import numpy as np

INF = 10 ** 9


class Arrivals:
    """Llegadas de R escenarios: arr_ns, arr_ew (R, N) con N = H + 60, y sus sumas acumuladas."""

    def __init__(self, arr_ns, arr_ew, duration, lam_ns=None, lam_ew=None, seeds=None):
        self.arr_ns = arr_ns
        self.arr_ew = arr_ew
        self.H = int(duration)
        self.R, self.N = arr_ns.shape
        z = np.zeros((self.R, 1), dtype=np.int32)
        self.C_ns = np.concatenate([z, np.cumsum(arr_ns, axis=1, dtype=np.int32)], axis=1)   # C[:, t] = llegadas en [0, t)
        self.C_ew = np.concatenate([z, np.cumsum(arr_ew, axis=1, dtype=np.int32)], axis=1)
        self.lam_ns, self.lam_ew, self.seeds = lam_ns, lam_ew, seeds
        self.n_arrivals = (self.C_ns[:, self.H] + self.C_ew[:, self.H]).astype(np.int64)

    def subset(self, idx):
        idx = np.asarray(idx)
        return Arrivals(self.arr_ns[idx], self.arr_ew[idx], self.H,
                        None if self.lam_ns is None else np.asarray(self.lam_ns)[idx],
                        None if self.lam_ew is None else np.asarray(self.lam_ew)[idx],
                        None if self.seeds is None else np.asarray(self.seeds)[idx])


def make_arrivals(lam_ns, lam_ew, seeds, duration, profile=None):
    """Llegadas Bernoulli. lam_* en veh/s, escalares o arreglos (R,). Con profile (R, N) o (N,) la tasa se
    multiplica segundo a segundo (demanda variable en el tiempo); sin profile coincide con _make_arrivals."""
    seeds = np.atleast_1d(np.asarray(seeds, dtype=np.int64))
    R = len(seeds)
    lam_ns = np.broadcast_to(np.asarray(lam_ns, dtype=float), (R,)).copy()
    lam_ew = np.broadcast_to(np.asarray(lam_ew, dtype=float), (R,)).copy()
    N = int(duration) + 60
    arr_ns = np.empty((R, N), dtype=np.int8)
    arr_ew = np.empty((R, N), dtype=np.int8)
    prof = None
    if profile is not None:
        prof = np.broadcast_to(np.asarray(profile, dtype=float), (R, N))
    for i, s in enumerate(seeds):
        rng = np.random.default_rng(int(s))
        u_ns = rng.random(N)
        u_ew = rng.random(N)
        if prof is None:
            arr_ns[i] = u_ns < lam_ns[i]
            arr_ew[i] = u_ew < lam_ew[i]
        else:
            arr_ns[i] = u_ns < lam_ns[i] * prof[i]
            arr_ew[i] = u_ew < lam_ew[i] * prof[i]
    return Arrivals(arr_ns, arr_ew, duration, lam_ns, lam_ew, seeds)


class Context:
    """Lo que ve un controlador en una epoca de decision para los escenarios idx (los que estan en verde)."""

    def __init__(self, sim, t, idx):
        a = sim.arr
        self.sim, self.t, self.idx = sim, t, idx
        self.phase = sim.phase[idx]
        self.tstart = sim.tstart[idx]
        self.el = t - self.tstart                       # s de verde transcurridos
        self._ns = self.phase == 0
        ns = self._ns
        self.q_g = np.where(ns, sim.q_ns[idx], sim.q_ew[idx])       # cola del brazo con verde
        self.q_r = np.where(ns, sim.q_ew[idx], sim.q_ns[idx])       # cola del brazo en rojo
        rows = idx[:, None]
        cols = t + np.arange(10)[None, :]
        wns, wew = a.arr_ns[rows, cols], a.arr_ew[rows, cols]
        self.wg = np.where(ns[:, None], wns, wew).astype(np.int32)  # llegadas de los proximos 10 s (verde)
        self.wr = np.where(ns[:, None], wew, wns).astype(np.int32)  # idem (rojo)
        self.red_since_green = self.cum(t, "r") - self.cum(self.tstart, "r")   # llegadas al rojo desde el inicio del verde

    def cum(self, tt, arm):
        """Llegadas acumuladas en [0, tt) del brazo 'g' (con verde) o 'r' (en rojo); tt escalar o (n,)."""
        a = self.sim.arr
        tt = np.broadcast_to(np.asarray(tt), self.idx.shape)
        c_ns, c_ew = a.C_ns[self.idx, tt], a.C_ew[self.idx, tt]
        if arm == "g":
            return np.where(self._ns, c_ns, c_ew)
        return np.where(self._ns, c_ew, c_ns)

    def past(self, k, arm="g"):
        """Llegadas en los ultimos k s (causal: solo lo ya ocurrido) en el brazo 'g' o 'r'."""
        return self.cum(self.t, arm) - self.cum(np.maximum(self.t - k, 0), arm)


class BatchSim:
    def __init__(self, arrivals, lost=5, gmin=7, delta=10, max_green=57):
        self.arr = arrivals
        self.lost, self.gmin, self.delta, self.max_green = lost, gmin, delta, max_green

    def run(self, ctrl, metrics=True, trace=False):
        a = self.arr
        R, H = a.R, a.H
        q_ns = np.zeros(R, dtype=np.int32)
        q_ew = np.zeros(R, dtype=np.int32)
        phase = np.zeros(R, dtype=np.int8)
        lost_mode = np.zeros(R, dtype=bool)
        lostc = np.zeros(R, dtype=np.int8)
        tstart = np.zeros(R, dtype=np.int32)
        gend = np.full(R, INF, dtype=np.int64)
        last_arr = np.zeros(R, dtype=np.int32)
        last_ns = np.full(R, -1000, dtype=np.int32)      # instante de la ultima llegada en cada brazo
        last_ew = np.full(R, -1000, dtype=np.int32)
        D_ns = np.zeros(R, dtype=np.int64)
        D_ew = np.zeros(R, dtype=np.int64)
        qmax_ns = np.zeros(R, dtype=np.int32)
        qmax_ew = np.zeros(R, dtype=np.int32)
        n_switch = np.zeros(R, dtype=np.int32)
        green_time = np.zeros(R, dtype=np.int64)
        self.q_ns, self.q_ew, self.phase, self.tstart, self.last_arr = q_ns, q_ew, phase, tstart, last_arr
        self.last_ns, self.last_ew = last_ns, last_ew
        self.t = 0
        has_start = hasattr(ctrl, "on_green_start")
        has_dec = hasattr(ctrl, "decide")
        has_stop = hasattr(ctrl, "stop")
        if hasattr(ctrl, "reset"):
            ctrl.reset(self)
        if has_start:                                   # el primer verde (t = 0)
            g = ctrl.on_green_start(self, np.arange(R), 0)
            if g is not None:
                gend[:] = g
        allidx = np.arange(R)
        if trace:
            tr_q = np.zeros((R, H, 2), dtype=np.int16)
            tr_ph = np.zeros((R, H), dtype=np.int8)       # 0 / 1: brazo con verde; 2: tiempo perdido
        gmin, delta = self.gmin, self.delta
        mg = INF if self.max_green is None else self.max_green
        for t in range(H):
            self.t = t
            green = ~lost_mode
            # --- decisiones del controlador en los escenarios con verde ---
            el = t - tstart
            if has_dec:
                m = green & (el >= gmin) & (((el - gmin) % delta) == 0) & (el < mg)
                if m.any():
                    idx = allidx[m]
                    e = np.asarray(ctrl.decide(self, Context(self, t, idx)))
                    gend[idx] = t + e
            if has_stop:
                s = ctrl.stop(self, t, green)
                gend = np.where(s & green, np.minimum(gend, t), gend)
            gend = np.where(green & (el >= mg), np.minimum(gend, t), gend)
            ended = green & (t >= gend)
            if ended.any():
                lost_mode |= ended
                lostc[ended] = 0
                n_switch[ended] += 1
                green = ~lost_mode
            # --- un segundo: llegadas y descarga ---
            a_ns = a.arr_ns[:, t]
            a_ew = a.arr_ew[:, t]
            q_ns += a_ns
            q_ew += a_ew
            last_ns = np.where(a_ns > 0, t, last_ns)
            last_ew = np.where(a_ew > 0, t, last_ew)
            self.last_ns, self.last_ew = last_ns, last_ew
            g_ns = green & (phase == 0) & (q_ns > 0)
            g_ew = green & (phase == 1) & (q_ew > 0)
            q_ns -= g_ns
            q_ew -= g_ew
            D_ns += q_ns
            D_ew += q_ew
            if trace:
                tr_q[:, t, 0] = q_ns
                tr_q[:, t, 1] = q_ew
                tr_ph[:, t] = np.where(lost_mode, 2, phase)
            if metrics:
                np.maximum(qmax_ns, q_ns, out=qmax_ns)
                np.maximum(qmax_ew, q_ew, out=qmax_ew)
                green_time += green
            if has_stop:                                 # ultima llegada en el brazo con verde (control por hueco)
                arr_g = np.where(phase == 0, a_ns, a_ew)
                last_arr = np.where(green & (arr_g > 0), t, last_arr)
                self.last_arr = last_arr
            # --- fin del tiempo perdido: empieza el verde de la otra fase ---
            if lost_mode.any():
                lostc[lost_mode] += 1                    # los que acaban de terminar el verde ya pierden este segundo
                done = lost_mode & (lostc >= self.lost)
                if done.any():
                    lost_mode[done] = False
                    phase[done] ^= 1
                    tstart[done] = t + 1
                    gend[done] = INF
                    last_arr[done] = t + 1
                    self.last_arr = last_arr
                    if has_start:
                        idx = allidx[done]
                        g = ctrl.on_green_start(self, idx, t + 1)
                        if g is not None:
                            gend[idx] = g
        D = D_ns + D_ew
        out = dict(D=D, D_ns=D_ns, D_ew=D_ew, n=a.n_arrivals,
                   delay=D / a.n_arrivals, qmax_ns=qmax_ns, qmax_ew=qmax_ew,
                   n_switch=n_switch, green_frac=green_time / H, q_final_ns=q_ns.copy(), q_final_ew=q_ew.copy())
        out["delay_ns"] = D_ns / np.maximum(1, a.C_ns[:, H])
        out["delay_ew"] = D_ew / np.maximum(1, a.C_ew[:, H])
        out["delay_served"] = self._served_delay(out)
        if trace:
            out["trace_q"], out["trace_phase"] = tr_q, tr_ph
        return out

    def _served_delay(self, out):
        """Convencion del articulo original: solo la espera de los vehiculos que ya salieron (sin el residuo)."""
        a = self.arr
        H = a.H
        res = np.zeros(a.R, dtype=np.int64)
        for i in range(a.R):
            for arr, qf in ((a.arr_ns[i, :H], out["q_final_ns"][i]), (a.arr_ew[i, :H], out["q_final_ew"][i])):
                if qf > 0:
                    pos = np.flatnonzero(arr)[-int(qf):]
                    res[i] += int((H - pos).sum())
        return (out["D"] - res) / a.n_arrivals
