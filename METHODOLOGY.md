# Methodology

How this design study was approached: what was read, what was assumed, and what was left out.

---

## 1. Framing

The design study answers a concrete question: how would you extend the Tau benchmark into a new domain — Food Delivery — for RL training rather than eval-only use, and what are the main challenges, timeline, and resources? Four signals shaped the work:

1. **Operational challenges of data production at scale.** One row per challenge, each mapped to a specific operational mechanic (see `07_phased_plan.md` and the challenge table below).
2. **First of several domains.** The infrastructure is designed so a second domain reuses most of the v1 tooling.
3. **Data required for RL.** This determines the RL-gym shape: dense reward, ~50% pass-rate calibration, and train/dev/test/curriculum splits.
4. **Bounded scope.** The study is dense rather than exhaustive; each artifact does one job.

---

## 2. Sources

### Sierra Research (the chassis)
- [`sierra-research/tau-bench`](https://github.com/sierra-research/tau-bench): original repo; README redirects to τ³-bench
- [`sierra-research/tau2-bench`](https://github.com/sierra-research/tau2-bench): the τ²/τ³ repo (rebranded as τ³ when banking, voice, and gym arrived)
- [τ-bench paper, arXiv 2406.12045](https://arxiv.org/abs/2406.12045): Yao, Shinn, Razavi, Narasimhan, NeurIPS 2024
- [τ²-bench paper, arXiv 2506.07982](https://arxiv.org/abs/2506.07982): dual-control plus compositional generation (Barres et al., 2025)
- Source files read directly:
  - `tau_bench/types.py` (Action, Task Pydantic models)
  - `tau_bench/envs/base.py` (the reward implementation)
  - `tau_bench/envs/user.py` (5 user-simulator strategies plus the system prompt)
  - `tau_bench/envs/retail/tasks_test.py` (canonical task example)
  - `tau_bench/envs/retail/tools/__init__.py` (16 retail tools)
  - `tau_bench/envs/airline/tools/__init__.py` (14 airline tools)
  - `tau_bench/envs/retail/tools/cancel_pending_order.py` (concrete tool implementation)
  - `tau_bench/envs/retail/wiki.md` (the policy pattern)
  - τ³-bench `src/tau2/domains/README.md` (domain contract)
  - τ³-bench `src/tau2/gym/README.md` (Gymnasium interface)

### Published RL-gym / data-production practice
Drawn from publicly described practice around tau-bench-style data production (no proprietary sources):
- Domain-extension shape: per-domain DBs, tools, and policies; a small (~50-task) initial release per domain, with domains like Manufacturing, E-commerce, Hotel, Insurance, Digital Wallet, and Consulting progressing across the field.
- RL-gym calibration: a ~50% pass-rate target, a 4-type environment taxonomy, and "high-fidelity trajectories and graded eval signals".
- Agentic-eval failure taxonomy: tool execution / data grounding / reasoning; full-trajectory evaluation; weekly evaluation sprints.
- Framing principles widely cited in the space: "policy-aware agents", "cascading consequences", and "reliability is not the same problem as intelligence".

### Adjacent benchmark landscape
- [SABER paper (Cuadron et al., ICLR 2026)](https://openreview.net/forum?id=En2z9dckgP): the source of the 75+ task fixes τ³ incorporated
- [τ²-Bench-Verified (Amazon AGI)](https://github.com/amazon-agi/tau2-bench-verified): third-party verification track
- [MUA-RL paper, arXiv 2508.18669](https://arxiv.org/abs/2508.18669): trained on 165 tau-bench tasks (115 retail + 50 airline) lifting retail Pass^1 to 67%
- [AReaL-SEA / EigenData paper, arXiv 2601.22607](https://arxiv.org/abs/2601.22607): per-instance verifiers lifted Pass^1 from baseline to 75% retail and 98% telecom on tau²-bench
- [SWE-bench Verified](https://www.swebench.com/) (500 tasks; top frontier models ~80-94% Pass^1)
- [AgentBench (arXiv 2308.03688)](https://arxiv.org/abs/2308.03688) (8 environments, 29 LLMs)
- [Mind2Web 2](https://github.com/OSU-NLP-Group/Mind2Web-2) (130 long-horizon tasks, 1,000+ human-hours)
- [GAIA (arXiv 2311.12983)](https://arxiv.org/abs/2311.12983) (466 questions; humans 92% vs GPT-4 plugins 15%)
- [WebArena](https://github.com/web-arena-x/webarena) (812 tasks)
- [OSWorld](https://os-world.github.io/) (369 tasks; humans 72% vs best model 12%)

---

## 3. Assumptions and where they come from

| Assumption | Source / rationale | Sensitivity |
|---|---|---|
| Small core team plus a tiered contractor pool | Guiding principle: do not scale internal headcount linearly with workload | Team size does not change the strategy |
| 200 hand-crafted plus 3,000 generated tasks at v1 | Calibrated against MUA-RL (165 tau-bench training tasks lifting Pass^1 to 67%); per-bucket density of 250-400 trajectories at ~50% pass | Could ship 150 plus 2,500 if generator yield is lower |
| Generator yield ~70% | Conservative against τ²-bench compositional generator design (atomic-action triples plus assertion functions); falsifiable in W9-10 | Below 60% triggers retune |
| 16-week timeline | Calibrated against published weekly evaluation-sprint cadence and the implied Manufacturing-extension complexity | Stretches to 20 weeks if voice modality enters scope |
| ~50% average pass-rate target | The established practice of domain-specific calibration targeting ~50% pass rates for Tau-style RL gyms | This is the established bar |
| 50% reuse to domain 2, ~65% from domain 3 | Honest about abstraction costs; first reuse pass surfaces gaps; second domain stabilises them | Higher reuse on closely-related verticals (ride-share) than distant ones |

These are assumptions, not commitments.

---

## 4. Decisions and trade-offs

A few choices someone could push back on, with the reasoning.

**No consumer named.** The design reads the same regardless of which trainer or lab consumes the data, so no specific one is assumed.

**Two original proposals, framed as proposals.** The Virtual Restaurant Network and difficulty-annotated curriculum splits are original to this study. Neither sits in any vendor's stack today, and both are small enough to defend in detail. Scaling this kind of data production is still an open problem across the field, which leaves room for original thinking. The proposals are kept modest rather than ambitious.

**Code references check out against the actual repo.** Every Pydantic snippet, every reward-function quote, every tool count comes from reading the source. A reviewer cross-checking against the GitHub repo will find the same lines.

**Responsible-AI is embedded in the build.** Allergen safety gates, monetary-identity invariants, fraud detection, and paste detection live in the data and reward design (`05_reward_design.md`). The standard responsible-AI primitives (data privacy, bias mitigation, model monitoring, HITL) show up as concrete code rather than a standalone section.

---

## 5. Open questions to resolve in week 1

1. Which buckets are highest priority for the target model? The hypothesis is the six high-priority buckets (3, 4, 5, 6, 7, 9); the actual probe-set Pass^1 confirms or re-orders.
2. Pass^k target. Different reliability bars imply different task volumes and difficulty calibrations.
3. Voice modality in scope or text-only v1? Voice adds 2-3 weeks.
4. Is grader output for these trajectories available? Access closes the feedback loop in days rather than weeks.
5. Compositional generator compute budget. Generation runs ~40K LLM calls including verification.
6. Dual-control depth. Multi-actor user-simulator (3 personas) is in the base spec; adding a 4th actor (dispatch operator) is incremental.
7. Geographic and regulatory variance. Food delivery in the US, EU, and India differ on dietary norms, refund laws, and tipping. Scope to one geography for v1.

---

## 6. Operational challenges of data production at scale

| Challenge | Operational mechanic |
|---|---|
| Throughput cliff at scale | Compositional generator carries the volume; hand-crafted tasks seed the high-priority buckets only |
| Behavioural telemetry, paste detection | Fraud pipeline flags anomalous authoring patterns |
| Group fraud detection (do not punish individuals) | Flag, gather evidence, then ban as a cluster rather than one-off |
| Quality not volume | Author bonus tied to grader pass-rate, not task count |
| Weekly delivery cadence | Every week from W4 ships a gradeable slice; review checkpoints throughout |
| Independent QA | Triple-check pipeline (author, review, replay verification) |
| Spec translation | Product owns translating research intent into written task specs |

---

## 7. Additional technical notes

### 7.1 Statistical power for Pass^k measurement

Pass^k is computed by running each task k times and asking "did all k succeed?" For a headline Pass^4 number to have a ±2% confidence interval, you need ~200 tasks per bucket × 4 reps = 800 rollouts per bucket. Across 12 buckets that is ~10K rollouts per leaderboard run.

This is why "first runnable in W4 with 50 tasks" is integration-shaped, not measurement-shaped. The first usable Pass^k number per bucket comes around W8, once each priority bucket has ~30 to 50 tasks shipped. The phased plan phrases the W4 milestone as "first integratable slice" for that reason.

### 7.2 Human-expert-API compounding

An MCP-based human-expert API (routing tasks to vetted domain experts on demand) gains capability from every τ-bench domain shipped. Each domain expands the verifiable behaviour-set such an API can route to.

- Food delivery adds: refund accounting, allergen-safety verification, real-time courier coordination as MCP-callable expert workflows.
- A second domain (say, Hotel) adds: booking modification, refund eligibility under change windows, group reservation handling.
- The dataset and the expert-verification capability cross-pollinate: the trajectories train models, the experts verify in production.

This is noted as a forward-looking, somewhat speculative direction rather than part of the v1 scope.
