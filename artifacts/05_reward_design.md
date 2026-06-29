# Reward Design, Four Upgrades over Base τ³-bench

> The single most opinionated technical claim in this proposal. The base τ³-bench reward (read directly from `tau_bench/envs/base.py`) is strict 0/1, fine for eval, poor for RL training. We propose four upgrades. Each is small, concrete, and back-compatible with the existing `RewardResult` interface.

---

## 0. Base τ³-bench reward (what we're starting from)

From `tau_bench/envs/base.py::Env.calculate_reward`:

```python
def calculate_reward(self) -> RewardResult:
    data_hash = self.get_data_hash()           # hash of agent's final DB state
    reward = 1.0
    actions = [a for a in self.task.actions if a.name != RESPOND_ACTION_NAME]

    self.data = self.data_load_func()           # fresh DB
    for action in self.task.actions:            # replay GT actions
        if action.name not in self.terminate_tools:
            self.step(action)
    gt_data_hash = self.get_data_hash()

    info = RewardActionInfo(
        r_actions=data_hash == gt_data_hash, gt_data_hash=gt_data_hash)
    if not info.r_actions:
        reward = 0.0

    if len(self.task.outputs) > 0:              # output substring check
        # ... 0.0 if any expected output not present in some agent reply
        ...
    return RewardResult(reward=reward, info=info, actions=actions)
```

Two predicates, AND-ed:
- DB-state SHA-256 of agent's run == DB-state SHA-256 of ground-truth replay
- Each `task.outputs` string appears (case-insensitive, comma-stripped) in some agent reply

Reward ∈ {0.0, 1.0}. No partial credit. No safety constraints. No tolerance for stochastic/equivalent outcomes.

This is fine for eval (where you want strict pass/fail). It is the wrong shape for RL training, where you want denser signal and where equivalent-but-not-identical good outcomes should still be rewarded.

---

## 1. Equivalence-class hashing (for stochastic outcomes)

**Problem.** Driver assignment is stochastic. Across replays of the same task seed, different drivers may be assigned (any driver in a valid candidate pool is a correct answer). Strict DB-hash equality breaks: agent's `assigned_driver_id="drv_jose_h_31"` and GT's `"drv_li_w_44"` produce different hashes, so reward = 0 even though both are correct.

**Fix.** Replace `get_data_hash()` with `get_data_hash_canonical()`, which projects out fields listed in the task's `equivalence_class` override before hashing:

```python
def get_data_hash_canonical(self) -> str:
    canonical = copy.deepcopy(self.data)
    for ovr in self.task.reward_overrides.get("equivalence_class", []):
        # Replace the field with the (sorted) candidate set
        path, candidate_path = ovr["field_path"], ovr["candidate_set_path"]
        candidates = _resolve_path(canonical, candidate_path)
        # If the agent's chosen value is in the set, canonicalize to the set itself
        if _resolve_path(canonical, path) in candidates:
            _set_path(canonical, path, sorted(candidates))
    return consistent_hash(to_hashable(canonical))
```

**Used in**: bucket 5 (driver coordination), bucket 6 (restaurant coordination), bucket 10 (multi-stop sequencing, the order in which couriers visit drop-offs has multiple valid solutions).

**Cost**: ~10 lines of code in the env. Per-task overhead in the task JSON is one `equivalence_class` field.

---

## 2. Safety-gate hard rules (for non-negotiable constraints)

**Problem.** Allergens are not a soft preference. If the agent proposes a substitute containing the customer's hard-flagged allergen, *no amount of subsequent good behavior recovers that*. Base reward has no concept of irrecoverable violations, a brilliant 10-step trajectory ending in a successful order is rewarded the same regardless of whether the agent suggested a peanut substitute to a peanut-allergic customer along the way.

**Fix.** Apply a pre-check that hard-zeros the reward if any safety constraint was violated at any point in the trajectory:

```python
def _safety_gate_passed(self) -> bool:
    gates = self.task.reward_overrides.get("safety_gate") or []
    for gate in gates:
        # Each gate is a predicate over the trajectory's tool calls
        if _gate_violated(gate, self.actions, self.data):
            return False
    return True
```

Example gate:
```json
{
  "hard_zero_if": "any tool call uses substitute_item_id with allergen 'peanut' for this customer"
}
```

In `calculate_reward`, gate runs first; if False, reward = 0.0 unconditionally.

**Used in**: bucket 9 (allergens, ~30 tasks), bucket 12 (fraud handling, agent must never authorize action against a flagged-fraud customer without escalation), bucket 7 (compensation cap, agent must never exceed authorized credit threshold).

**Cost**: ~30 lines of code for the gate predicate language. A small, declarative DSL for "tool X with arg Y matching pattern Z."

---

## 3. Monetary-identity invariant (for refunds and replacements)

**Problem.** A refund scenario can be resolved many valid ways: full refund to original payment; full refund as wallet credit; partial refund + apology credit; replacement order; partial refund + replacement of remaining items. Strict DB equality says only the one ledger pattern in the GT is correct. We want to accept any pattern that satisfies the monetary identity:

> sum(refunds) + sum(credits) + sum(replacement_order_value) == disputed_amount

**Fix.** When `task.reward_overrides.monetary_identity.disputed_amount` is set, the reward function reconstructs the ledger from the agent's trajectory and checks the identity:

```python
def _monetary_identity_holds(self) -> bool:
    inv = self.task.reward_overrides.get("monetary_identity")
    if inv is None: return True
    order_id = self.task.order_id
    refunded = sum(r["amount"] for r in self.data["orders"][order_id].get("refunds", []))
    credited = sum(c["amount"] for c in self.data["orders"][order_id].get("credits", []))
    rep_val  = sum(_replacement_value(self, r_id)
                   for r_id in self.data["orders"][order_id].get("replacements", []))
    total = refunded + credited + rep_val
    return abs(total - inv["disputed_amount"]) <= inv.get("tolerance", 0.01)
```

If `inv.hard_zero_if_above` is also set (compensation cap), the reward also hard-zeros if the total *exceeds* the cap. This is what makes bucket 7 ("Can your AI say no?") trainable, the agent learns "satisfies-disputed-amount AND does-not-exceed-cap" via a single reward signal.

**Used in**: buckets 3, 7, 8, 11.

**Cost**: ~25 lines + the `disputed_amount` annotation per affected task.

---

## 4. Dense process reward (for RL training)

**Problem.** Sparse 0/1 reward at episode end is a hard credit-assignment problem. RL training is dramatically more sample-efficient with dense intermediate rewards. The base τ³-bench reward only fires once per episode.

**Fix.** Each task ships with a `process_reward_checkpoints` list, small declarative predicates over the trajectory, each with a weight. The reward function returns BOTH the outcome reward AND the process reward, structured so the consuming lab can choose:

```python
@dataclass
class ShapedRewardResult(RewardResult):
    outcome_reward: float       # 0.0 or 1.0, the original reward
    process_reward: float       # sum of checkpoint weights satisfied
    safety_passed: bool         # did all safety gates pass?
    monetary_identity_holds: bool
    breakdown: list[CheckpointResult]   # per-checkpoint detail for diagnostics
```

The consuming lab trains on whatever combination they want:
- `r = outcome_reward` (matches base τ³ exactly)
- `r = outcome_reward + 0.3 * process_reward`
- `r = outcome_reward * safety_passed * monetary_identity_holds`
- Any custom function

Sample checkpoints from `04_sample_tasks.json` task 1:
```json
[
  {"step": "fetched customer allergen profile before substitution", "weight": 0.15},
  {"step": "filtered substitutes by allergen", "weight": 0.15},
  {"step": "explicit customer confirmation captured", "weight": 0.10}
]
```

The DSL for "step satisfied" is the same one used for safety gates: tool-call patterns over the trajectory.

**Cost**: ~15 lines per task to author the checkpoints (T1 work, on the hand-crafted seed; for compositional generation, checkpoints are templated by atomic action type so cost is amortized).

**Net result**: every shipped task carries 3-7 process checkpoints. Across 3,200 tasks, ~16,000 dense reward signals, a hundredfold density increase over outcome-only.

---

## How these compose

Final reward shape:

```python
def calculate_reward_shaped(self) -> ShapedRewardResult:
    # 1. Safety gate, hard zero if violated
    safety_passed = self._safety_gate_passed()
    if not safety_passed:
        return ShapedRewardResult(
            reward=0.0, outcome_reward=0.0, process_reward=0.0,
            safety_passed=False, ...
        )

    # 2. Outcome reward, original DB-hash + output-substring check
    #    BUT using equivalence-class canonical hashing
    outcome = 1.0 if self.get_data_hash_canonical() == self._gt_canonical_hash() else 0.0

    # 3. Monetary identity, modifies outcome (hard-zero if violated)
    money_ok = self._monetary_identity_holds()
    if not money_ok:
        outcome = 0.0

    # 4. Process reward, sum of checkpoint weights satisfied
    process = self._process_reward_score()

    return ShapedRewardResult(
        reward=outcome + 0.3 * process,    # default; the lab overrides this
        outcome_reward=outcome,
        process_reward=process,
        safety_passed=safety_passed,
        monetary_identity_holds=money_ok,
        breakdown=self._checkpoint_breakdown(),
    )
```

Backwards-compatible: if no `reward_overrides` are present (i.e. tasks shipped from base retail/airline/banking), `safety_passed=True`, `monetary_identity_holds=True`, `process=0.0`, `outcome` reduces to the canonical hash check (which collapses to original hash check when there are no equivalence classes). Existing leaderboards still work.

---

## Quality assurance: the grader regression suite

The grader IS the bottleneck, if it scores trajectories incorrectly, all the data is poison. We build a suite of:

- **100 known-good trajectories** (PASS expected)
- **100 known-bad trajectories** (FAIL expected, with specific failure mode tagged)
- **50 known-edge trajectories** (subtle pass/fail boundary cases)

The suite runs:
- On every grader code change → CI gate
- On every reward-override schema change
- Weekly against a 1% sample of newly-graded tasks (LLM-judge audit comparing grader verdict to a separate LLM's verdict)

If the grader passes a known-bad trajectory or fails a known-good one, we don't ship. This is the difference between "the data is good" and "we know the data is good."

---

## Cost summary

| Upgrade | LOC | Per-task annotation cost | Engineering weeks |
|---|---|---|---|
| Equivalence-class hashing | ~10 | trivial (1 field) | 0.5 |
| Safety-gate gates | ~30 (DSL) | ~3 min (T1 work) | 1.0 |
| Monetary-identity invariant | ~25 | ~2 min (T3 work, since it's just an amount) | 0.5 |
| Process reward checkpoints | ~50 (DSL + scoring) | ~7 min (T3 work) per task | 1.5 |
| Grader regression suite | ~100 | one-off | 1.5 (T2 work) |
| **Total** | **~215** | **~12 min/task amortized** | **~5 weeks of T2 + T1 time** |

This is the work that makes our data RL-ready, and it's the work that competitors who only wrap base τ³-bench will not have done.
