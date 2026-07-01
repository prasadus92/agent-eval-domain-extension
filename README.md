# Extending τ³-bench into Food Delivery

A design study for adding a Food Delivery domain to [τ³-bench](https://github.com/sierra-research/tau2-bench), shaped for RL training rather than eval-only use.

The goal: a τ³-shaped Food Delivery domain that ships ~3,200 RL-ready trajectories, with infrastructure that is largely reusable when a second marketplace domain (ride-share, hotel, healthcare scheduling) follows.

---

## Key conclusions

1. **Target τ³-bench, not the deprecated original.** The `sierra-research/tau-bench` repo is officially deprecated; its README redirects to τ³-bench. The current `sierra-research/tau2-bench` repo ships τ²/τ³ features including a Gymnasium RL interface (`uv sync --extra gym`), compositional task generation, dual-control (Dec-POMDP), and the 75+ task fixes from the SABER paper (Cuadron et al., ICLR 2026). This study extends τ³-bench.

2. **Food Delivery is structurally harder than retail, airline, or manufacturing** along eight axes: multi-party communications (4 actors versus 2), real-time temporal state, stochastic transitions (driver assignment, restaurant prep), two-sided marketplace constraints, partial-fulfilment recovery paths, hard safety constraints (allergens), and monetary identity invariants (refunds, credits, replacements, payouts). Each requires **new env, tool, or reward primitives** that base τ³-bench does not provide.

3. **Base τ³-bench reward is strict 0/1 — fine for eval, wrong shape for RL.** The implementation in `tau_bench/envs/base.py` is a SHA-256 hash of JSON state versus ground-truth replay, plus an optional output substring check. This study layers four upgrades: (a) **equivalence-class hashing** so stochastic driver assignment does not break reward, (b) **safety-gate hard rules** that hard-zero on an allergen violation, (c) a **monetary identity invariant** (refunds + credits + replacement value must equal the disputed amount), and (d) **dense process reward** for RL training (per-checkpoint partial credit). AReaL-SEA validated this style of verifier-based shaping on tau²-bench, lifting Pass^1 to 75% retail and 98% telecom (arXiv 2601.22607).

4. **~3,200 RL-ready trajectories at v1.** Twelve capability buckets (MECE), 200 hand-crafted seed tasks for the high-priority buckets, and ~3,000 compositionally generated and verified tasks, all bucket-stratified and difficulty-annotated for curriculum RL. The design follows the published ~50% pass-rate calibration target for Tau-style RL gyms. Volume anchors: the Manufacturing extension released 50 tasks; SWE-bench Verified ships 500; GAIA ships 466; Mind2Web 2 ships 130 at 1,000+ human-hours; MUA-RL trained against 165 tau-bench tasks.

5. **Reuse compounds across domains.** Roughly half of the v1 infrastructure is reusable on a second domain, rising once the abstractions stabilise. Reusable pieces: the compositional task generator, the user-simulator framework, the behavioural-fraud telemetry, the grader regression suite, the reward-overrides DSL, the two-sided-marketplace simulator pattern, and the curriculum/difficulty annotation.

6. **Two original proposals**, framed as proposals: (i) the **Virtual Restaurant Network**, a persistent two-sided marketplace simulator (50 fictional restaurants, 80 drivers, 200 customers) whose schema (supplier × courier × consumer × pricing engine) generalises to ride-share, healthcare scheduling, marketplace, and field service; (ii) **difficulty-annotated curriculum splits** so a consuming trainer can run curriculum RL out of the box.

---

## Repo structure

```
agent-eval-domain-extension/
├── README.md                         <- this file
├── METHODOLOGY.md                    <- analytical framework, sources, assumptions
└── artifacts/
    ├── 01_decision_tree.md           <- 12 capability buckets, L1 + L2
    ├── 02_domain_spec.md             <- τ³-bench-shaped Food Delivery domain spec
    ├── 03_sample_tools.py            <- 6 example tool implementations
    ├── 04_sample_tasks.json          <- 3 full sample tasks
    ├── 05_reward_design.md           <- reward upgrades (equiv-class, safety, monetary, dense)
    └── 07_phased_plan.md             <- 16-week phased plan, weekly slices from W4
```

## Reading order

Start with `METHODOLOGY.md` for the framework and sources, then `artifacts/01_decision_tree.md` and `artifacts/05_reward_design.md` — that is where the technical depth lives. `artifacts/02_domain_spec.md` and `artifacts/03_sample_tools.py` give the concrete τ³-bench domain contract.

---

## Sources

This work is grounded in:

- **Sierra Research repos**: [`sierra-research/tau-bench`](https://github.com/sierra-research/tau-bench), [`sierra-research/tau2-bench`](https://github.com/sierra-research/tau2-bench)
- **Sierra papers**: [τ-bench (arXiv 2406.12045)](https://arxiv.org/abs/2406.12045), [τ²-bench (arXiv 2506.07982)](https://arxiv.org/abs/2506.07982)
- **Sierra blog**: [Benchmarking AI Agents](https://sierra.ai/blog/benchmarking-ai-agents), [τ³-bench launch](https://sierra.ai/blog/bench-advancing-agent-benchmarking-to-knowledge-and-voice)
- **Public RL with tau-bench**: [MUA-RL (arXiv 2508.18669)](https://arxiv.org/abs/2508.18669), [AReaL-SEA / EigenData (arXiv 2601.22607)](https://arxiv.org/abs/2601.22607)
- **Adjacent benchmarks**: [SWE-bench Verified](https://www.swebench.com/), [AgentBench (arXiv 2308.03688)](https://arxiv.org/abs/2308.03688), [Mind2Web 2](https://github.com/OSU-NLP-Group/Mind2Web-2), [GAIA (arXiv 2311.12983)](https://arxiv.org/abs/2311.12983), [WebArena](https://github.com/web-arena-x/webarena), [OSWorld](https://os-world.github.io/)
- **τ²-Bench-Verified (Amazon AGI)**: [github.com/amazon-agi/tau2-bench-verified](https://github.com/amazon-agi/tau2-bench-verified)

---

## A note on a few choices

- Every quantitative claim is either tied to a cited public source or labelled as a model assumption (task volumes anchored to public benchmarks; timeline anchored to published evaluation-sprint cadence). Nothing here asserts anything proprietary.
- The two original proposals (Virtual Restaurant Network, curriculum splits) are framed as proposals rather than commitments. They are small and concrete by design.
- Every code reference — Pydantic snippet, reward function quote, tool count — is read directly from the τ³-bench source and cross-checks against the public repo.
