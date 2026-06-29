# Extending τ³-bench into Food Delivery
## A tau-bench domain-extension design study

Technical and operational design for the first domain in a portfolio that compounds across two-sided marketplaces.

Prasad Subrahmanya · April 2026

---

## Headline

A τ³-shaped Food Delivery domain in **16 weeks** that ships ~3,200 RL-ready trajectories, with infrastructure that lands domain 2 in 8 weeks at ~50% reuse and rises to ~65% reuse from domain 3 onward.

---

## Key conclusions

1. **The brief points to v1; the production target is τ³-bench.** The repository linked in the case description (`sierra-research/tau-bench`) is officially deprecated. Its README opens with: "⚠️ This repository contains outdated versions ... Please use τ³-bench." The current `sierra-research/tau2-bench` repo ships τ²- and τ³-features, including a Gymnasium RL interface (`uv sync --extra gym`), compositional task generation, dual-control (Dec-POMDP), and 75+ task fixes from the SABER paper (Cuadron et al., ICLR 2026). We extend τ³-bench.

2. **Food Delivery is structurally harder than retail, airline, or manufacturing** along eight axes: multi-party communications (4 actors versus 2), real-time temporal state, stochastic transitions (driver assignment, restaurant prep), two-sided marketplace constraints, partial-fulfilment recovery paths, hard safety constraints (allergens), and monetary identity invariants (refunds, credits, replacements, payouts). Each requires **new env, tool, or reward primitives** that base τ³-bench does not provide.

3. **Base τ³-bench reward is strict 0/1, fine for eval, wrong shape for RL.** The actual implementation in `tau_bench/envs/base.py` is a SHA-256 hash of JSON state versus ground-truth replay, plus an optional output substring check. We layer four upgrades: (a) **equivalence-class hashing** (so stochastic driver assignment does not break reward), (b) **safety-gate hard rules** (hard-zero on allergen violation), (c) **monetary identity invariant** (refunds + credits + replacement value must equal the disputed amount), and (d) **dense process reward** for RL training (per-checkpoint partial credit). AReaL-SEA validated this style of verifier-based shaping on tau²-bench, lifting Pass^1 from baseline to 75% retail and 98% telecom (arXiv 2601.22607).

4. **3,200 RL-ready trajectories at v1.** Twelve capability buckets (MECE), 200 hand-crafted seed tasks for the high-priority buckets, 3,000 compositionally generated and verified tasks, all bucket-stratified and difficulty-annotated for curriculum RL. We follow the published ~50% pass-rate calibration target for Tau-style RL-gyms. Volume anchors: the Manufacturing extension released 50 tasks; SWE-bench Verified ships 500; GAIA ships 466; Mind2Web 2 ships 130 at 1,000+ human-hours; MUA-RL trained against 165 tau-bench tasks.

5. **Org: 4 FTE core plus a tiered contractor pyramid (~85 active at peak).** Tiers calibrated to public labeling-platform rate cards: T1 ($120/hr, 4 ex-DoorDash/Uber-Eats ops experts), T2 ($80/hr, 4 senior SWE/data engineers), T3 ($30/hr, ~50 trajectory writers), T4 ($15/hr, ~25 reviewers). Guiding principle: do not scale internal headcount linearly with workload.

6. **Reuse compounds.** ~50% of v1 infrastructure is reusable on domain 2; ~65% by domain 3 once abstractions stabilise. Reusable: compositional task generator, user-simulator framework, behavioural-fraud telemetry, grader regression suite, reward-overrides DSL, hiring-funnel templates, two-sided-marketplace VRN pattern, curriculum/difficulty annotation.

7. **Two original moves**, called out as proposals: (i) the **Virtual Restaurant Network** , a persistent two-sided marketplace simulator (50 fictional restaurants, 80 drivers, 200 customers) whose schema (supplier × courier × consumer × pricing engine) generalises to ride-share, healthcare scheduling, marketplace, field service; (ii) **difficulty-annotated curriculum splits** so the consuming lab can train curriculum-RL out of the box.

---

## Repo structure

```
agent-eval-domain-extension/
├── README.md                         <- this file
├── METHODOLOGY.md                    <- analytical framework, sources, assumptions
├── output/
│   └── food-delivery-domain.pdf      <- printable deck (12 slides)
├── slides/
│   ├── slides.html                   <- HTML deck source
│   └── render_pdf.js                 <- Puppeteer renderer (optional)
├── artifacts/
│   ├── 01_decision_tree.md           <- 12 capability buckets, L1+L2
│   ├── 02_domain_spec.md             <- τ³-bench-shaped Food Delivery domain spec
│   ├── 03_sample_tools.py            <- 6 example tool implementations
│   ├── 04_sample_tasks.json          <- 3 full sample tasks
│   ├── 05_reward_design.md           <- reward upgrades (equiv-class, safety, monetary, dense)
│   ├── 06_cost_model.md              <- FTE, throughput, hiring-funnel math
│   └── 07_phased_plan.md             <- 16-week plan, weekly slices from W4
├── build.sh                          <- regenerate the PDF (uses headless Chrome)
└── package.json                      <- only if you regenerate via Puppeteer
```

## Reading order

If you have 5 minutes: open `output/food-delivery-domain.pdf` and read the deck.

If you have 20 minutes: deck, then `METHODOLOGY.md`, then `artifacts/01_decision_tree.md` and `artifacts/05_reward_design.md`.

If you have 60 minutes: read everything; the artifacts/ folder is where the depth lives.

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

- I do not invent names or numbers I cannot defend. Every quantitative claim is either tied to a cited public source or labelled as a model assumption (rate cards anchored to public labeling-platform ranges; task volumes anchored to public benchmarks).
- The two original proposals (Virtual Restaurant Network, curriculum splits) are framed as proposals rather than commitments. They are small and concrete by design.
- The deck does not lean on marketing language. "Reliability is not the same problem as intelligence" is a published industry frame and shows up once.
