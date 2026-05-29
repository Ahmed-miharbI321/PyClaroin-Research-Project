"""
Fully agentic PyClarion-style WCST implementation.

This is intentionally closer to the style of demos/introduction.ipynb in the
pyClarion repository:

1. Keyspace definition.
2. Agent construction through an Agent subclass.
3. Knowledge/state initialization.
4. Event processing in an external environment loop.

Unlike the earlier high-level implementation, the agent does not directly choose
"the hidden rule" from a hard-coded rule-choice class. It receives a stimulus
card, selects one of four target cards, receives correct/incorrect feedback, and
learns how to behave across trials.

Cognitive mapping:
- NACS/top level: explicit hypotheses over sorting rules.
- ACS/bottom level: reinforcement learner over rule-use policies.
- MS: confidence, uncertainty, frustration, and perseveration pressure.
- MCS-like monitor: learns the approximate set-shift criterion from experience.

The tester/environment knows the hidden rule. The agent does not.

Because pyClarion is evolving, this file keeps all PyClarion-dependent code in a
small number of places. The learning algorithm itself is ordinary Python state
inside the Agent, while activation passing and action selection are represented
as PyClarion Input/Choice events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import exp
import random
from typing import Any, Iterable, Mapping, NamedTuple

from pyClarion import Agent, Atom, Atoms, Choice, Input
from pyClarion.knowledge import Buses, Bus, BusFamily, DataFamily, Root


# ---------------------------------------------------------------------------
# 1) Keyspace definition
# ---------------------------------------------------------------------------

class Color(Atoms):
    red: Atom
    grn: Atom
    blu: Atom
    ylw: Atom


class Shape(Atoms):
    circ: Atom
    squr: Atom
    tria: Atom
    star: Atom


class Number(Atoms):
    one: Atom
    two: Atom
    three: Atom
    four: Atom


class Rule(Atoms):
    color: Atom
    shape: Atom
    number: Atom


class Target(Atoms):
    """The four selectable target cards in a WCST display."""
    t1: Atom
    t2: Atom
    t3: Atom
    t4: Atom


class Feedback(Atoms):
    correct: Atom
    incorrect: Atom


class Affect(Atoms):
    certain: Atom
    uncertain: Atom
    frustrated: Atom
    shifting: Atom


class Main(Buses):
    stimulus: Bus
    target: Bus
    feedback: Bus
    policy: Bus
    affect: Bus
    action: Bus


class WCSTBuses(BusFamily):
    main: Main


class WCSTData(DataFamily):
    color: Color
    shape: Shape
    number: Number
    rule: Rule
    target: Target
    feedback: Feedback
    affect: Affect


class WCSTRoot(Root):
    b: WCSTBuses
    d: WCSTData


# ---------------------------------------------------------------------------
# 2) Cards and WCST environment
# ---------------------------------------------------------------------------

class Card(NamedTuple):
    color: Atom
    shape: Atom
    number: Atom


def atom_tail(atom_or_key: Any) -> str:
    """Human-friendly fallback name for pyClarion Keys/atoms."""
    text = str(atom_or_key)
    return text.split(":")[-1].split(".")[-1].strip("')>")


def atom_name_in(atoms: Atoms, atom_or_key: Any) -> str:
    """Return the declared attribute name for an Atom/Key within an Atoms sort.

    In this PyClarion version, printing an Atom may only show
    ``<... Atom object at ...>``. The reliable names are the declared class
    attributes, e.g. ``Target.t4`` or ``Rule.color``. This helper maps values
    back through those declarations and also handles Keys such as
    ``Key('d:target:t4')`` returned by Choice.poll().
    """
    names = getattr(atoms.__class__, "__annotations__", {})
    key_name = atom_tail(atom_or_key)

    if key_name in names:
        return key_name

    for name in names:
        candidate = getattr(atoms, name)
        if atom_or_key == candidate:
            return name
        try:
            if atom_or_key == ~candidate:
                return name
        except TypeError:
            pass

    return key_name


@dataclass
class WCSTEnvironment:
    """External WCST tester.

    The environment exposes target cards and stimulus cards, but keeps the hidden
    rule private. It switches rule after a criterion number of consecutive correct
    responses, matching the standard WCST category-completion idea.
    """

    root: WCSTRoot
    switch_after_correct: int = 10
    rng: random.Random = field(default_factory=random.Random)

    hidden_rule: Atom = field(init=False)
    previous_rule: Atom | None = field(default=None, init=False)
    correct_streak: int = field(default=0, init=False)
    trial: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        d = self.root.d
        self.rules = [d.rule.color, d.rule.shape, d.rule.number]
        self.targets: dict[Atom, Card] = {
            d.target.t1: Card(d.color.red, d.shape.circ, d.number.one),
            d.target.t2: Card(d.color.grn, d.shape.squr, d.number.two),
            d.target.t3: Card(d.color.blu, d.shape.tria, d.number.three),
            d.target.t4: Card(d.color.ylw, d.shape.star, d.number.four),
        }
        self.hidden_rule = self.rng.choice(self.rules)

    def make_stimulus(self) -> Card:
        """Generate a card that has one matching target for each possible rule.

        This preserves the WCST ambiguity: before feedback, color/shape/number are
        all plausible bases for sorting.
        """
        target_values = list(self.targets.values())
        color_card = self.rng.choice(target_values)
        shape_card = self.rng.choice([c for c in target_values if c is not color_card])
        number_card = self.rng.choice([
            c for c in target_values if c is not color_card and c is not shape_card
        ])
        return Card(color_card.color, shape_card.shape, number_card.number)

    def target_matching(self, stimulus: Card, rule: Atom) -> Atom:
        for target_atom, card in self.targets.items():
            if rule == self.root.d.rule.color and card.color == stimulus.color:
                return target_atom
            if rule == self.root.d.rule.shape and card.shape == stimulus.shape:
                return target_atom
            if rule == self.root.d.rule.number and card.number == stimulus.number:
                return target_atom
        raise RuntimeError(f"No target matched {stimulus=} under {rule=}.")

    def score(self, stimulus: Card, chosen_target: Atom) -> Atom:
        self.trial += 1
        correct_target = self.target_matching(stimulus, self.hidden_rule)
        is_correct = chosen_target == correct_target

        if is_correct:
            self.correct_streak += 1
            fb = self.root.d.feedback.correct
            if self.correct_streak >= self.switch_after_correct:
                self._switch_rule()
            return fb

        return self.root.d.feedback.incorrect

    def _switch_rule(self) -> None:
        self.previous_rule = self.hidden_rule
        options = [r for r in self.rules if r != self.hidden_rule]
        self.hidden_rule = self.rng.choice(options)
        self.correct_streak = 0


# ---------------------------------------------------------------------------
# 3) Fully agentic PyClarion agent
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CognitiveState:
    """Small state abstraction used by the bottom-level RL learner."""

    last_feedback: str
    streak_bucket: str
    affect: str


class FullyAgenticWCSTAgent(Agent):
    """WCST agent with explicit hypotheses plus learned procedural control.

    The agent learns at two levels:

    1. Explicit NACS-like hypothesis adaptation. Feedback changes the posterior
       over color/shape/number as possible hidden rules.
    2. Implicit ACS-like reinforcement learning. Q-values learn which rule-using
       strategy tends to pay off in cognitive states such as uncertainty,
       frustration, or possible set-shift.

    The action emitted to the environment is not a rule label. It is a target-card
    choice. Rule hypotheses are internal causes of target-card actions.
    """

    root: WCSTRoot
    stimulus_in: Input
    feedback_in: Input
    policy_drive: Input
    affect_out: Input
    target_choice: Choice

    def __init__(
        self,
        name: str,
        root: WCSTRoot,
        *,
        rng: random.Random | None = None,
        alpha: float = 0.25,
        gamma: float = 0.20,
        temperature: float = 0.35,
        explicit_weight: float = 0.55,
        implicit_weight: float = 0.45,
        epsilon: float = 0.06,
        perseveration_bias: float = 0.10,
        frustration_threshold: int = 2,
        choice_sd: float = 0.04,
        choice_latency_factor: float = 0.0,
    ) -> None:
        super().__init__(name, root)
        self.root = root
        self.rng = rng or random.Random()

        d = root.d
        self.rules = [d.rule.color, d.rule.shape, d.rule.number]
        self.targets = [d.target.t1, d.target.t2, d.target.t3, d.target.t4]

        # NACS/top-level explicit posterior over hidden rules.
        self.posterior: dict[Atom, float] = {r: 1.0 / len(self.rules) for r in self.rules}

        # ACS/bottom-level learned procedural values: Q(state, internal-rule-use).
        self.q: dict[tuple[CognitiveState, Atom], float] = {}
        self.alpha = alpha
        self.gamma = gamma
        self.temperature = temperature
        self.explicit_weight = explicit_weight
        self.implicit_weight = implicit_weight
        self.epsilon = epsilon
        self.perseveration_bias = perseveration_bias
        self.frustration_threshold = frustration_threshold

        # Meta-cognitive/MCS-like statistics learned from experience.
        self.learned_shift_criterion: float | None = None
        self.correct_streak = 0
        self.incorrect_streak = 0
        self.last_feedback_name = "none"
        self.last_state: CognitiveState | None = None
        self.last_rule_strategy: Atom | None = None
        self.last_target: Atom | None = None
        self.last_stimulus: Card | None = None
        self.last_rule_to_target: dict[Atom, Atom] = {}

        with self:
            # These are demo-style process definitions: external data enters via
            # Input processes, and ACS action selection is represented by Choice.
            self.stimulus_in = Input(f"{name}.stimulus_in", root.d)
            self.feedback_in = Input(f"{name}.feedback_in", root.d.feedback)
            self.policy_drive = Input(f"{name}.policy_drive", root.d.target)
            self.affect_out = Input(f"{name}.affect_out", root.d.affect)

            self.target_choice = Choice(
                f"{name}.target_choice",
                root.d,
                root.d,
                root.d.target,
                sd=choice_sd,
                f=choice_latency_factor,
            )
            self.target_choice.input = self.policy_drive.main

    # ----- Agent/environment interface -------------------------------------

    def initialize(self) -> None:
        self._send_affect()
        self._run_events()

    def perceive(self, stimulus: Card, env: WCSTEnvironment) -> None:
        """Receive a new card and prepare target-action drives."""
        self.last_stimulus = stimulus
        self.last_rule_to_target = {r: env.target_matching(stimulus, r) for r in self.rules}

        # The current PyClarion Input parser accepts atoms from a single declared
        # sort/keyspace, but it does not accept `Sort ** Atom` expressions. The
        # stimulus contains three different feature sorts, so we keep the card as
        # Python agent state and convert it into target drives below. This is still
        # agentic: the PyClarion Choice process receives the learned policy drive,
        # while the environment never reveals the hidden rule.

        self._send_policy_drive()
        self.system.schedule(self.target_choice.trigger())
        self._run_events()

    def act(self) -> Atom:
        """Select one of the four target cards."""
        polled = self.target_choice.poll()
        if not polled:
            self.system.schedule(self.target_choice.trigger())
            self._run_events()
            polled = self.target_choice.poll()

        selected = next(iter(polled.values())) if isinstance(polled, Mapping) else polled
        target = self._key_to_atom(selected, self.root.d.target)
        self.last_target = target
        self.last_state = self._state()
        self.last_rule_strategy = self._infer_rule_strategy_from_target(target)
        return target

    def observe(self, feedback_atom: Atom) -> None:
        """Learn from feedback and prepare for the next trial."""
        reward = 1.0 if feedback_atom == self.root.d.feedback.correct else -1.0
        self.system.schedule(self.feedback_in.send({feedback_atom: 1.0}))

        self._update_explicit_posterior(feedback_atom)
        self._update_implicit_q(reward)
        self._update_meta_monitor(feedback_atom)
        self._send_affect()
        self.last_feedback_name = atom_tail(feedback_atom)
        self._run_events()

    # ----- Learning ---------------------------------------------------------

    def _update_explicit_posterior(self, feedback_atom: Atom) -> None:
        if self.last_rule_strategy is None:
            return

        correct = feedback_atom == self.root.d.feedback.correct

        if correct:
            # The chosen rule explains the observed success.
            self.posterior = {
                r: 1.0 if r == self.last_rule_strategy else 0.0 for r in self.rules
            }
            return

        was_certain = self.posterior.get(self.last_rule_strategy, 0.0) >= 0.98
        if was_certain:
            # If certainty is violated, interpret this as possible set shift.
            remaining = [r for r in self.rules if r != self.last_rule_strategy]
            self.posterior = {
                r: 0.0 if r == self.last_rule_strategy else 1.0 / len(remaining)
                for r in self.rules
            }
            return

        # Otherwise eliminate only the failed hypothesis and renormalize.
        self.posterior[self.last_rule_strategy] = 0.0
        total = sum(self.posterior.values())
        if total <= 0.0:
            self.posterior = {r: 1.0 / len(self.rules) for r in self.rules}
        else:
            self.posterior = {r: v / total for r, v in self.posterior.items()}

    def _update_implicit_q(self, reward: float) -> None:
        if self.last_state is None or self.last_rule_strategy is None:
            return

        key = (self.last_state, self.last_rule_strategy)
        old = self.q.get(key, 0.0)
        next_state = self._state()
        bootstrap = max(self.q.get((next_state, r), 0.0) for r in self.rules)
        self.q[key] = old + self.alpha * (reward + self.gamma * bootstrap - old)

    def _update_meta_monitor(self, feedback_atom: Atom) -> None:
        correct = feedback_atom == self.root.d.feedback.correct
        if correct:
            self.correct_streak += 1
            self.incorrect_streak = 0
            return

        # An error after a run of successes is evidence about the task's shift
        # criterion. This is learned online instead of being given to the agent.
        if self.correct_streak >= 2:
            if self.learned_shift_criterion is None:
                self.learned_shift_criterion = float(self.correct_streak)
            else:
                self.learned_shift_criterion = (
                    0.80 * self.learned_shift_criterion + 0.20 * self.correct_streak
                )

        self.correct_streak = 0
        self.incorrect_streak += 1

    # ----- Drive construction ---------------------------------------------

    def _send_policy_drive(self) -> None:
        explicit = self._explicit_target_drive()
        implicit = self._implicit_target_drive()

        drive = {t: 0.0 for t in self.targets}
        for t in self.targets:
            drive[t] = self.explicit_weight * explicit.get(t, 0.0)
            drive[t] += self.implicit_weight * implicit.get(t, 0.0)

        # Exploration: small uniform target pressure.
        for t in self.targets:
            drive[t] = (1.0 - self.epsilon) * drive[t] + self.epsilon / len(self.targets)

        # MS/frustration: repeated errors create a mild tendency to repeat the
        # last response, allowing perseverative errors to emerge rather than be
        # directly scripted.
        if self.incorrect_streak >= self.frustration_threshold and self.last_target is not None:
            try:
                last_target = self._key_to_atom(self.last_target, self.root.d.target)
            except KeyError:
                last_target = None
            if last_target is not None:
                drive[last_target] = drive.get(last_target, 0.0) + self.perseveration_bias

        drive = self._normalize(drive)
        self.system.schedule(self.policy_drive.send(drive))

    def _explicit_target_drive(self) -> dict[Atom, float]:
        drive = {t: 0.0 for t in self.targets}
        for rule_atom, p in self.posterior.items():
            target = self.last_rule_to_target.get(rule_atom)
            if target is not None:
                drive[target] += p
        return self._normalize(drive)

    def _implicit_target_drive(self) -> dict[Atom, float]:
        state = self._state()
        rule_probs = self._softmax({r: self.q.get((state, r), 0.0) for r in self.rules})
        drive = {t: 0.0 for t in self.targets}
        for rule_atom, p in rule_probs.items():
            target = self.last_rule_to_target.get(rule_atom)
            if target is not None:
                drive[target] += p
        return self._normalize(drive)

    def _infer_rule_strategy_from_target(self, target: Atom) -> Atom:
        # A target usually corresponds to exactly one internal rule strategy for
        # the generated stimulus. If ambiguity happens, choose the strongest
        # posterior/Q-supported explanation.
        candidates = [r for r, t in self.last_rule_to_target.items() if t == target]
        if not candidates:
            return self.rng.choice(self.rules)
        if len(candidates) == 1:
            return candidates[0]
        state = self._state()
        return max(candidates, key=lambda r: self.posterior.get(r, 0.0) + self.q.get((state, r), 0.0))

    # ----- State, affect, and utility --------------------------------------

    def _state(self) -> CognitiveState:
        if self.correct_streak == 0:
            streak_bucket = "none"
        elif self.learned_shift_criterion is not None and self.correct_streak >= self.learned_shift_criterion - 1:
            streak_bucket = "near_shift"
        elif self.correct_streak >= 3:
            streak_bucket = "stable"
        else:
            streak_bucket = "early"
        return CognitiveState(self.last_feedback_name, streak_bucket, atom_tail(self.current_affect()))

    def current_affect(self) -> Atom:
        d = self.root.d
        if self.incorrect_streak >= self.frustration_threshold:
            return d.affect.frustrated
        if self.learned_shift_criterion is not None and self.correct_streak >= self.learned_shift_criterion - 1:
            return d.affect.shifting
        if max(self.posterior.values()) >= 0.98:
            return d.affect.certain
        return d.affect.uncertain

    def _send_affect(self) -> None:
        self.system.schedule(self.affect_out.send({self.current_affect(): 1.0}))

    def _run_events(self) -> None:
        # The introduction notebook uses `for event in agent.run(): ...`; keeping
        # this helper makes every perception/action/feedback cycle process all
        # scheduled events before the Python environment continues.
        for _event in self.run():
            pass

    def _softmax(self, values: dict[Atom, float]) -> dict[Atom, float]:
        temp = max(self.temperature, 1e-6)
        m = max(values.values()) if values else 0.0
        exps = {k: exp((v - m) / temp) for k, v in values.items()}
        return self._normalize(exps)

    @staticmethod
    def _normalize(values: dict[Atom, float]) -> dict[Atom, float]:
        clipped = {k: max(0.0, float(v)) for k, v in values.items()}
        total = sum(clipped.values())
        if total <= 0.0:
            n = len(clipped) or 1
            return {k: 1.0 / n for k in clipped}
        return {k: v / total for k, v in clipped.items()}

    @staticmethod
    def _key_to_atom(key: Any, atoms: Atoms) -> Atom:
        """Robustly translate a pyClarion Key/string/Atom to an Atom."""
        names = getattr(atoms.__class__, "__annotations__", {})
        key_name = atom_tail(key)

        # Choice.poll() often returns Key('d:target:t4'), whose useful part is
        # the final declared attribute name. Map that directly first.
        if key_name in names:
            return getattr(atoms, key_name)

        for name in names:
            atom = getattr(atoms, name)
            if key == atom:
                return atom
            try:
                if key == ~atom:
                    return atom
            except TypeError:
                pass

        # Fallback for Atoms implementations that are iterable but do not expose
        # class annotations in the expected way.
        for atom in atoms:
            if key == atom:
                return atom
            try:
                if key == ~atom:
                    return atom
            except TypeError:
                pass

        raise KeyError(f"Could not map selected key {key!r} to an Atom in {atoms!r}")


# ---------------------------------------------------------------------------
# 4) Experiment runner
# ---------------------------------------------------------------------------

@dataclass
class TrialRecord:
    trial: int
    stimulus: tuple[str, str, str]
    hidden_rule: str
    chosen_target: str
    inferred_rule_strategy: str
    feedback: str
    affect: str
    posterior: dict[str, float]
    learned_shift_criterion: float | None
    perseverative_error: bool


def run_wcst(
    *,
    n_trials: int = 128,
    switch_after_correct: int = 10,
    seed: int = 13,
    verbose: bool = True,
) -> tuple[list[TrialRecord], dict[str, Any]]:
    rng = random.Random(seed)
    root = WCSTRoot()
    env = WCSTEnvironment(root, switch_after_correct=switch_after_correct, rng=rng)
    agent = FullyAgenticWCSTAgent("agent", root, rng=rng)
    agent.initialize()

    records: list[TrialRecord] = []
    correct_count = 0
    error_count = 0
    perseverative_errors = 0

    for i in range(1, n_trials + 1):
        stimulus = env.make_stimulus()
        hidden_before = env.hidden_rule
        previous_rule = env.previous_rule

        agent.perceive(stimulus, env)
        chosen_target = agent.act()
        chosen_strategy = agent.last_rule_strategy
        fb = env.score(stimulus, chosen_target)

        is_error = fb == root.d.feedback.incorrect
        is_persev = bool(is_error and previous_rule is not None and chosen_strategy == previous_rule)
        correct_count += int(not is_error)
        error_count += int(is_error)
        perseverative_errors += int(is_persev)

        agent.observe(fb)

        rec = TrialRecord(
            trial=i,
            stimulus=(atom_name_in(root.d.color, stimulus.color), atom_name_in(root.d.shape, stimulus.shape), atom_name_in(root.d.number, stimulus.number)),
            hidden_rule=atom_name_in(root.d.rule, hidden_before),
            chosen_target=atom_name_in(root.d.target, chosen_target),
            inferred_rule_strategy=atom_name_in(root.d.rule, chosen_strategy),
            feedback=atom_name_in(root.d.feedback, fb),
            affect=atom_name_in(root.d.affect, agent.current_affect()),
            posterior={atom_name_in(root.d.rule, k): round(v, 3) for k, v in agent.posterior.items()},
            learned_shift_criterion=(
                None if agent.learned_shift_criterion is None else round(agent.learned_shift_criterion, 2)
            ),
            perseverative_error=is_persev,
        )
        records.append(rec)

        if verbose:
            print(
                f"Trial {i:03d} | hidden={rec.hidden_rule:<6} "
                f"target={rec.chosen_target:<2} strategy={rec.inferred_rule_strategy:<6} "
                f"fb={rec.feedback:<9} affect={rec.affect:<10} "
                f"posterior={rec.posterior} shift≈{rec.learned_shift_criterion}"
                + (" PERSEV" if rec.perseverative_error else "")
            )

    metrics = {
        "trials": n_trials,
        "correct": correct_count,
        "errors": error_count,
        "perseverative_errors": perseverative_errors,
        "learned_shift_criterion": (
            None if agent.learned_shift_criterion is None else round(agent.learned_shift_criterion, 2)
        ),
        "q_values_learned": len(agent.q),
    }
    return records, metrics


if __name__ == "__main__":
    _, metrics = run_wcst(n_trials=128, switch_after_correct=10, seed=13, verbose=True)
    print("-" * 88)
    print(metrics)
