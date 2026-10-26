"""
sim_engine.py
================================================================================
Motor de simulacion PASO A PASO (1 segundo por tick) para el simulador
interactivo. Reproduce EXACTAMENTE la logica de traffic_model.simulate_fuzzy
(mismas llegadas, mismas colas, mismas decisiones), pero expone el estado de
cada segundo para animarlo.

Uso tipico:
    cfg = SimConfig(lam_ns=720/3600, lam_ew=2160/3600, seed=1, duration=3600)
    sim = StepSim(cfg)
    while not sim.done:
        state = sim.step()      # avanza 1 s y devuelve el estado
        ... dibujar(state) ...
"""
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

import fuzzy_logic as fl
from traffic_model import Sim, _make_arrivals, LOST, INTERVENTIONS


def load_ruleset(name: str) -> dict:
    """'paper' -> las 25 reglas del Apendice del paper (unico conjunto vigente).

    El re-afinado previo ('tuned') se hizo sobre una transcripcion incorrecta de
    las reglas y quedo archivado en _extras_pospuestos/; no se ofrece aqui.
    """
    if name == "paper":
        return fl.RULES
    raise ValueError(f"ruleset desconocido o archivado: {name}")


@dataclass
class SimConfig:
    lam_ns: float = 720 / 3600.0        # veh/s
    lam_ew: float = 2160 / 3600.0       # veh/s
    seed: int = 1
    duration: int = 3600                # s
    ruleset: str = "paper"              # "paper" | "tuned"
    threshold: float = 0.5
    mode: str = "capacity"              # "capacity" | "literal"  (ver traffic_model)
    predicted_q: Optional[bool] = None  # None: valor por defecto del modo (capacity -> False, literal -> True); si se da, SIEMPRE se respeta
    queue_source: Optional[str] = None  # None: "total" si mode="literal", si no "green_arrivals"
    a_mode: Optional[str] = None        # "crossing" | "arrivals" (None: segun mode)
    q_mode: Optional[str] = None        # "current" | "predicted" (None: segun mode)
    lost: float = LOST                  # s por cambio de fase
    disabled: frozenset = frozenset()   # {(intervencion, indice 0..4)} de reglas apagadas (uso didactico)

    def __post_init__(self):
        self.rules = load_ruleset(self.ruleset)
        # Se resuelven y se GUARDAN los parametros de la lectura (ninguno queda implicito ni se ignora):
        # SimConfig() queda explicitamente CALIBRADA (crossing / current / predicted_q=False / green_arrivals).
        self.a_mode, self.q_mode = fl._resolve_modes(self.mode, self.predicted_q, self.a_mode, self.q_mode)
        self.predicted_q = (self.q_mode == "predicted")
        if self.queue_source is None:
            self.queue_source = "total" if self.mode == "literal" else "green_arrivals"


def rule_text(rule) -> str:
    """Texto de una regla (T, A, Q, E) tal como se escribe en el paper."""
    T, A, Q, E = rule
    q = "any" if Q == "any" else f"lt({Q})"
    return f"si T={T} y A=mt({A}) y Q={q} entonces E={E}"


_LABEL_ES = {"veryshort": "muy corta", "short": "corta", "medium": "media", "long": "larga", "verylong": "muy larga"}


def explain_decision(d, phase, t, threshold=0.5):
    """Explicacion en lenguaje claro de una decision del controlador (para clases y presentaciones)."""
    who = "N-S" if phase == 0 else "E-W"
    other = "E-W" if phase == 0 else "N-S"
    L = [f"t = {t} s · El brazo {who} lleva {d.elapsed} s en verde y el controlador decide cuánto "
         f"extenderlo (intervención de {d.intervention} s)."]
    L.append(f"Mira tres datos: cola del brazo en rojo ({other}) Q = {d.q_red} veh; cola del brazo en verde "
             f"({who}) = {d.q_green} veh; llegadas esperadas en los próximos 10 s: A = {d.beta[-1]} veh.")
    act = [(i, a) for i, a in enumerate(d.activation) if a > 0]
    if act:
        txt = ", ".join(f"R{i + 1} ({_LABEL_ES.get(d.rules[i][3], d.rules[i][3])}) con {a:.2f}" for i, a in act)
        rest = " Las demás no se activan." if len(act) < len(d.rules) else ""
        L.append(f"Reglas que se activan: {txt}.{rest}")
    else:
        L.append("Ninguna regla se activa con estos datos.")
    if d.cut:
        L.append(f"El mayor grado es {d.grade_max:.2f}, menor que el umbral {threshold:.2f}: no hay extensión "
                 f"que se pueda justificar, así que se CORTA el verde y cambia la fase.")
    else:
        names = ", ".join(f"R{i + 1}" for i in d.winners)
        L.append(f"Decide {names}: su grado {d.grade_max:.2f} alcanza el umbral {threshold:.2f}. "
                 f"Se extiende el verde {d.e_star} s."
                 + (" Como es el máximo (10 s), el controlador volverá a decidir en 10 s." if d.e_star == 10
                    else " Como es menos de 10 s, el verde termina cuando se cumpla ese tiempo."))
    return "\n".join(L)


@dataclass
class Decision:
    """Decision del controlador en una intervencion, con el detalle de las reglas.

    Terminologia (inferencia min-max de Mamdani):
      * activacion de una regla r = max sobre e de min(mu_T(e), mu_mt(A)(a_e), mu_lt(Q)(q_e), mu_E(e))
      * DISPARO decisivo = regla cuya contribucion en e* iguala el grado maximo
        (la regla que "gana" la decision); puede haber empates.
    """
    elapsed: int          # seg. de verde transcurrido (7, 17, 27, 37, 47)
    e_star: int           # extension elegida (0 = cortar)
    grade_max: float      # maximo del vector de grados
    cut: bool             # True si se corto el verde
    intervention: int = 0                 # 7, 17, 27, 37 o 47
    rules: tuple = ()                     # las 5 reglas de la intervencion
    grades: Optional[np.ndarray] = None   # grade(e = 1..10)
    per_rule: Optional[np.ndarray] = None # (n_reglas, 10): aporte de cada regla por e
    activation: tuple = ()                # activacion maxima de cada regla
    winners: tuple = ()                   # indices de las reglas que disparan (deciden e*)
    q_red: int = 0                        # cola del brazo en rojo (entrada Q)
    q_green: int = 0                      # cola del brazo en verde
    beta: tuple = ()                      # A evaluada para e = 1..10
    qv: tuple = ()                        # Q evaluada para e = 1..10


@dataclass
class StepState:
    t: int
    phase: int                # 0 = N-S en verde, 1 = E-W en verde
    in_transition: bool       # True durante el tiempo perdido (todo rojo)
    green_elapsed: int        # segundos de verde transcurridos
    q_ns: int
    q_ew: int
    arrived_ns: bool
    arrived_ew: bool
    discharge_ns: bool
    discharge_ew: bool
    dm: float                 # retardo medio actual (s/veh)
    decision: Optional[Decision] = None
    done: bool = False
    trans_index: int = -1     # 0..4: segundo de tiempo perdido que acaba de procesarse (-1 si no es transicion)


class StepSim:
    def __init__(self, cfg: SimConfig):
        self.cfg = cfg
        self.arr_ns, self.arr_ew = _make_arrivals(cfg.lam_ns, cfg.lam_ew,
                                                  cfg.seed, cfg.duration)
        self.sim = Sim(self.arr_ns, self.arr_ew, lost=cfg.lost)
        self.t = 0
        self.phase = 0
        self.green_start = 0
        self.ii = 0
        self.green_end = None
        self.in_transition = False
        self.trans_remaining = 0
        self.done = False
        self.decisions = []         # (t, fase, Decision) de toda la corrida
        self.pending = {0: 0, 1: 0}  # autos agregados a mano (0 = N-S, 1 = E-W) que entraran en los proximos segundos

    # ------------------------------------------------------------------
    def inject(self, arm: int, n: int = 1):
        """Agrega n autos a mano al brazo arm (0 = N-S, 1 = E-W). Entran uno por segundo
        (el modelo admite a lo sumo una llegada por segundo y brazo), en los proximos segundos libres."""
        self.pending[arm] += max(0, int(n))

    def _apply_pending(self, t):
        for arm, arr in ((0, self.arr_ns), (1, self.arr_ew)):
            if self.pending[arm] > 0 and not arr[t]:
                arr[t] = 1
                self.pending[arm] -= 1

    # ------------------------------------------------------------------
    @property
    def dm(self) -> float:
        if self.sim.total_arrivals == 0:
            return 0.0
        return self.sim.total_delay / self.sim.total_arrivals

    def step(self) -> StepState:
        """Avanza 1 segundo y devuelve el estado (despues de procesarlo).

        Misma logica que traffic_model.Sim.run_green_fuzzy / transition: la
        intervencion ocurre al INICIO del segundo t (tras t - green_start s de
        verde); cada segundo se procesa una sola vez.
        """
        t = self.t
        self._apply_pending(t)
        decision = None
        green_elapsed = 0

        if not self.in_transition:
            # -- intervencion del controlador difuso --
            if self.ii < len(INTERVENTIONS) and t == self.green_start + INTERVENTIONS[self.ii]:
                wg, wc, qc, qg = self.sim.fuzzy_inputs(self.phase, self.green_start, t,
                                                       self.cfg.queue_source)
                grade = fl.fuzzy_decision(wg, wc, qc, self.cfg.rules[INTERVENTIONS[self.ii]],
                                          predicted_q=self.cfg.predicted_q,
                                          q_green=qg, mode=self.cfg.mode,
                                          a_mode=self.cfg.a_mode, q_mode=self.cfg.q_mode)
                rules_k = self.cfg.rules[INTERVENTIONS[self.ii]]
                per_rule = fl.fuzzy_decision_per_rule(
                    wg, wc, qc, rules_k, predicted_q=self.cfg.predicted_q, q_green=qg,
                    mode=self.cfg.mode, a_mode=self.cfg.a_mode, q_mode=self.cfg.q_mode)[:, 1:]
                off = [i for i in range(len(rules_k)) if (INTERVENTIONS[self.ii], i) in self.cfg.disabled]
                if off:                           # reglas apagadas: no aportan nada al maximo
                    per_rule = per_rule.copy()
                    per_rule[off, :] = 0.0
                    grade = np.concatenate(([0.0], per_rule.max(axis=0)))
                e_star = fl.decide_extension(grade, self.cfg.threshold)
                a_mode, q_mode = fl._resolve_modes(self.cfg.mode, self.cfg.predicted_q,
                                                   self.cfg.a_mode, self.cfg.q_mode)
                beta, qv = fl._beta_and_q(wg, wc, qc, qg, a_mode, q_mode)
                winners = ()
                if e_star > 0:
                    gmax = grade[e_star]
                    winners = tuple(int(i) for i in np.flatnonzero(per_rule[:, e_star - 1] >= gmax - 1e-12))
                decision = Decision(
                    elapsed=t - self.green_start, e_star=e_star,
                    grade_max=float(grade[1:].max()), cut=e_star == 0,
                    intervention=INTERVENTIONS[self.ii], rules=tuple(rules_k),
                    grades=np.array(grade[1:]), per_rule=per_rule,
                    activation=tuple(float(x) for x in per_rule.max(axis=1)),
                    winners=winners, q_red=int(qc), q_green=int(qg),
                    beta=tuple(int(x) for x in beta), qv=tuple(int(x) for x in qv))
                self.decisions.append((t, self.phase, decision))
                self.green_end = t + e_star
                self.ii += 1
            # -- fin de la fase verde: este mismo segundo ya es tiempo perdido --
            if self.green_end is not None and t >= self.green_end:
                self.in_transition = True
                self.trans_remaining = int(self.cfg.lost)

        arr_ns = bool(self.arr_ns[t])
        arr_ew = bool(self.arr_ew[t])
        d_ns = d_ew = False
        trans_index = -1
        if self.in_transition:
            trans_index = int(self.cfg.lost) - self.trans_remaining
            self.sim.tick(t, None)
            self.trans_remaining -= 1
            if self.trans_remaining <= 0:
                self.in_transition = False
                self.phase = 1 - self.phase
                self.green_start = t + 1
                self.ii = 0
                self.green_end = None
        else:
            # en tick() el arribo se procesa ANTES de la descarga: un auto que llega a una cola
            # vacia del brazo en verde cruza en el mismo segundo
            q = self.sim.q_ns if self.phase == 0 else self.sim.q_ew
            green_arrival = arr_ns if self.phase == 0 else arr_ew
            discharged = (len(q) + (1 if green_arrival else 0)) > 0
            d_ns = discharged and self.phase == 0
            d_ew = discharged and self.phase == 1
            self.sim.tick(t, self.phase)
            green_elapsed = t - self.green_start
        self.t = t + 1
        self.done = self.t >= self.cfg.duration

        return StepState(
            t=t, phase=self.phase, in_transition=self.in_transition,
            green_elapsed=green_elapsed,
            q_ns=len(self.sim.q_ns), q_ew=len(self.sim.q_ew),
            arrived_ns=arr_ns,
            arrived_ew=arr_ew,
            discharge_ns=d_ns, discharge_ew=d_ew,
            dm=self.dm, decision=decision, done=self.done, trans_index=trans_index,
        )

    def run_all(self) -> float:
        """Corre hasta el final y devuelve d_m (para validacion)."""
        while not self.done:
            self.step()
        return self.dm

    # ------------------------------------------------------------------
    def firing_rows(self):
        """Una fila por (decision, regla) con activacion y disparo; sirve para CSV y reportes."""
        rows = []
        for t, phase, d in self.decisions:
            for i, r in enumerate(d.rules):
                rows.append(dict(
                    t=t, brazo_verde="N-S" if phase == 0 else "E-W", intervencion=d.intervention,
                    regla=f"{d.intervention}s-R{i + 1}", texto=rule_text(r),
                    activacion=round(d.activation[i], 3), dispara=int(i in d.winners),
                    e_star=d.e_star, grado_max=round(d.grade_max, 3),
                    q_rojo=d.q_red, q_verde=d.q_green))
        return rows
