# Methodology

How I approached this design study, what I read, what I assumed, and what I left out.

---

## 1. Reading the brief

> A frontier lab, a foundational-model producer, wants to build an extension of Tau benchmark into new domains. Take the example of a Food Delivery domain and come up with a draft project plan. What are the main challenges to be solved? How long will it take? What resources are needed? This project is complex. You will not reach the perfect solution. Limit the time you spend on it. Pay specific attention to operational challenges of the data production at scale. Assume this is the first of several domains the lab will want. Assume, that this is data required for RL.

Four signals shaped the deck:

1. "Operational challenges of data production at scale." Slide 11 covers this in depth, with one row per challenge mapped to a specific operational mechanic.
2. "First of several domains." The compounding-infrastructure framing on slides 10 and 12 lives here.
3. "Data required for RL." Determines the RL-gym shape, dense reward, ~50% pass-rate calibration, train/dev/test/curriculum splits.
4. "Limit the time you spend." Twelve slides, each doing one job.

---

## 2. Sources

### Sierra Research (the chassis)
- [`sierra-research/tau-bench`](https://github.com/sierra-research/tau-bench): original repo; README redirects to τ³-bench
- [`sierra-research/tau2-bench`](https://github.com/sierra-research/tau2-bench): the τ²/τ³ repo (rebranded as τ³ when banking and voice and gym arrived)
- [τ-bench paper, arXiv 2406.12045](https://arxiv.org/abs/2406.12045): Yao, Shinn, Razavi, Narasimhan, NeurIPS 2024
- [τ²-bench paper, arXiv 2506.07982](https://arxiv.org/abs/2506.07982): dual-control plus compositional generation (Barres et al., 2025)
- Source files I read directly:
  - `tau_bench/types.py` (Action, Task Pydantic models)
  - `tau_bench/envs/base.py` (the reward implementation)
  - `tau_bench/envs/user.py` (5 user simulator strategies plus the system prompt)
  - `tau_bench/envs/retail/tasks_test.py` (canonical task example)
  - `tau_bench/envs/retail/tools/__init__.py` (16 retail tools)
  - `tau_bench/envs/airline/tools/__init__.py` (14 airline tools)
  - `tau_bench/envs/retail/tools/cancel_pending_order.py` (concrete tool implementation)
  - `tau_bench/envs/retail/wiki.md` (the policy pattern)
  - τ³-bench `src/tau2/domains/README.md` (domain contract)
  - τ³-bench `src/tau2/gym/README.md` (Gymnasium interface)

### Published RL-gym / data-production practice
Drawn from publicly described industry practice around tau-bench-style data production (no proprietary sources):
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

### Competitive context
- Scale AI: Donovan, $300M+ DoD footprint
- Surge AI: ~$1.2B ARR (per Sacra Research and SiliconANGLE 2025 reporting), Anthropic RLHF customer (publicly stated)
- Mercor: $1B revenue, APEX-Agents 480-task benchmark, ~$95/hr average rate
- Invisible Technologies: $144M raised, $2B valuation, Cohere Command-A case study
- Public labeling-platform rate cards span roughly $30-$90+/hr (writers, ML, legal, STEM)

---

## 3. Assumptions and where they come from

| Assumption | Source / rationale | Sensitivity |
|---|---|---|
| 4 FTE core team | Guiding principle: do not scale internal headcount linearly with workload | Could be 3 or 5; does not change strategy |
| T1 = $120/hr, T2 = $80/hr, T3 = $30/hr, T4 = $15/hr | Anchored to public labeling-platform rate cards ($30-$90+/hr range) plus Mercor comparables (~$95/hr avg, up to $300/hr specialised) | ±30% variance possible by geography |
| 200 hand-crafted plus 3,000 generated tasks at v1 | Calibrated against MUA-RL (165 tau-bench training tasks lifting Pass^1 to 67%); per-bucket density of 250-400 trajectories at ~50% pass | Could ship 150 plus 2,500 if generator yield is lower |
| Generator yield ~70% | Conservative against τ²-bench compositional generator design (atomic-action triples plus assertion functions); falsifiable in W9-10 | Below 60% triggers retune |
| 16-week timeline | Calibrated against published weekly evaluation-sprint cadence and the implied Manufacturing-extension complexity | Stretches to 20 weeks if voice modality enters scope |
| ~50% average pass-rate target | the established practice of domain-specific calibration targeting ~50% pass rates for Tau-style RL-gyms | This is the established bar |
| 50% reuse to domain 2, ~65% from domain 3 | Honest about abstraction costs; first reuse pass surfaces gaps; second domain stabilises them | Higher reuse on closely-related verticals (ride-share) than distant ones |

These are assumptions, not commitments.

---

## 4. Decisions and trade-offs I made

A few choices in the deck that someone could push back on, with my reasoning.

**No consumer named.** The frontier lab consuming this data is left anonymous. The design reads the same regardless of which lab it is.

**Two original proposals, framed as proposals.** The Virtual Restaurant Network and difficulty-annotated curriculum splits are mine. Neither sits in any vendor's stack today, and both are small enough to defend in detail. Scaling this kind of data production is still an open problem across the field, which leaves room for original thinking. I kept the proposals modest rather than ambitious.

**Code references check out against the actual repo.** Every Pydantic snippet, every reward function quote, every tool count comes from reading the source. A reviewer cross-checking against the GitHub repo will find the same lines.

**Workforce tooling.** Workforce-platform mechanics (internal LLM-grader, tiered contractor sourcing) are described at the level of publicly known industry practice; nothing here asserts anything proprietary.

**Twelve slides, not thirty.** The brief asked for limited time spent. I read that as a quality signal more than a brevity one, so the deck is dense per slide rather than padded.

**Responsible-AI is embedded in the build, not a separate slide.** Allergen safety gates, monetary-identity invariants, fraud detection, and paste detection live in the data and reward design (slide 8 plus the `05_reward_design.md` artefact). A standalone "responsible AI" slide would feel performative; the standard responsible-AI primitives (data privacy, bias mitigation, model monitoring, HITL) show up as concrete code instead.

---

## 5. Open questions to resolve in week 1

These appear on slide 12 but are elaborated here:

1. Which buckets are highest priority for the consuming lab's specific model? My hypothesis is the six high-priority buckets (3, 4, 5, 6, 7, 9); the actual probe-set Pass^1 confirms or re-orders.
2. Pass^k target. Different reliability bars imply different task volumes and difficulty calibrations.
3. Voice modality in scope or text-only v1? Voice adds 2-3 weeks.
4. Will the consuming lab share grader output for our trajectories? Closes the feedback loop in days rather than weeks.
5. Compositional generator compute budget. Generation runs ~40K LLM calls (including verification), order of $10-15K in API costs.
6. Dual-control depth. Multi-actor user-simulator (3 personas) is in the base spec; adding a 4th actor (dispatch operator) is incremental.
7. Geographic and regulatory variance. Food delivery in the US, EU, India differ on dietary norms, refund laws, tipping. Scope to one geography v1.

---

## 6. Design emphases the deck addresses

| Emphasis | Where it appears |
|---|---|
| Decision tree of buckets | Slide 6 plus `01_decision_tree.md` |
| Reward gap per bucket, gap-driven investment | Slide 6 hypothesis chart plus W1-W2 plan |
| Tiered experts, expensive plus cheap | Slide 10 org pyramid plus per-task cost model |
| Virtual companies, monetised | Slide 12 Virtual Restaurant Network proposal |
| Throughput cliff at scale | Slide 11 row 1 (compositional generator mitigation) |
| Behavioural telemetry, paste detection | Slide 11 row 5 (fraud) |
| Group fraud detection (do not punish individuals) | Slide 11 row 5 explicitly: flag, gather, ban as cluster |
| Bonus tied to quality not volume | Slide 11 last row |
| Weekly delivery cadence | Slide 9 timeline plus 13 review checkpoints |
| Top labs send your data to competitors for QA | Slide 11 (triple-check pipeline) |
| Margin discipline | Slide 11 row 2 |
| Researchers cannot structure their problem | Slide 11 (PD owns translation, written specs) |

---

## 7. How to read this deliverable

- 5 minutes: open `output/food-delivery-domain.pdf` (or `slides/slides.html`)
- 20 minutes: deck, then this file, then `artifacts/01_decision_tree.md` and `artifacts/05_reward_design.md`
- 60 minutes: read everything in `artifacts/`; that is where the depth lives. The deck is the compression; the artefacts are the substance.

---

## 8. Talking points held back from the deck

These belong in dialogue rather than in a written brief. I would raise them when asked, or proactively in a live walkthrough.

### 8.1 Pricing posture

The deck does not commit a price; it is a technical and operational design, not a quote. I have a defensible three-tier pricing structure (outcome-only, RL-shaped, RL-shaped + domain-2 starter) anchored to public reference points: Scale AI contract data via Vendr, Labellerr's per-annotation rule of thumb scaled to multi-turn trajectories, and industry reporting on Surge's frontier-lab SOWs. Specific numbers are best discussed in live conversation, since they depend on the the lab's RL training objectives and reuse expectations across the next three to four domains.

### 8.2 Cross-functional and vendor-management posture

Running such a program asks for vendor / cloud / model-provider relationship management. My program-level posture:

- LLM API spend on the compositional generator and grader audits is the largest variable cost. I would negotiate batched pricing with the chosen provider (Anthropic or OpenAI) early in W1 against a forecast of ~40K calls per week at peak, and revisit at W8.
- Cloud spend (env hosting, telemetry storage, replay logs) is small but should be itemised separately so the lab sees what they are renting versus building.
- Model-provider relationship: pick one default for the user simulator and one for the grader-judge audit, and avoid mixing, because a mismatch between them creates spurious disagreement signal in the κ metric.

### 8.3 Data licensing and IP

Three questions I would clarify with the consuming lab and Sierra in W1:

- Who owns the dataset? Default in dataset-extension SOWs is consumer-owned with the producer having limited internal-improvement rights; I would push for the right to publish a redacted public subset (matches the "first agentic dataset on HuggingFace" angle).
- Is the dataset Sierra-licensable? τ³-bench is MIT-licensed; the Food Delivery extension follows the same license unless the lab specifies otherwise.
- Confidential vs publishable cuts: probably 80% confidential, 20% publishable subset. Same shape as the existing public Manufacturing release.

### 8.4 Statistical power for Pass^k measurement

Pass^k is computed by running each task k times and asking "did all k succeed?" For the headline number (Pass^4) to have ±2% confidence interval, you need ~200 tasks per bucket × 4 reps = 800 rollouts per bucket. Across 12 buckets that is ~10K rollouts per leaderboard run.

This is why "first runnable in W4 with 50 tasks" is integration-shaped, not measurement-shaped. The first usable Pass^k number per bucket comes around W8 once each priority bucket has ~30 to 50 tasks shipped. Worth being explicit about this in the live walkthrough; the deck phrases it as "first integratable slice" for that reason.

### 8.5 Human-expert-API compounding

An MCP-based human-expert API (the pattern of routing tasks to vetted domain experts on demand) gets a capability boost from every τ-bench domain shipped. Each domain expands the verifiable behaviour-set such an API can route to.

- Food delivery adds: refund accounting, allergen-safety verification, real-time courier coordination as MCP-callable expert workflows.
- Domain 2 (say, Hotel) adds: booking modification, refund eligibility under change windows, group reservation handling.
- The dataset and the workforce capability cross-pollinate: the trajectories train, the experts verify in production.

This angle is left out of the deck because it borders on speculative, but it is a strong strategic "and additionally" beat.
