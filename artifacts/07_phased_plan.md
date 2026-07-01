# 16-Week Phased Plan

> A guiding principle: weekly delivery, not big-bang. The first shippable slice is in **week 4**, not week 16. Every week from W4 onward we ship something the consuming lab can grade.

---

## Phase 0, Scope & gap analysis (W1-W2)

| Week | Deliverable | Owner |
|---|---|---|
| W1 | Decision tree v1 (12 buckets × ~6 L2 each), agreed with the consuming lab | PD + T1 lead |
| W1 | 50-task probe set authored (rapid, intentionally rough) | T1 + T3 (5 authors) |
| W1 | Consuming-lab model run against τ³ retail base + our probe set | T2 lead |
| W2 | Bucket-by-bucket reward gap analysis | PD + T2 lead |
| W2 | Target buckets + hand-crafted vs generated allocation | PD |
| W2 | policy.md v1 outline | T1 lead |
| W2 | Hiring funnel kicked off (T3 + T4 sourcing) | Process Mgr |
| W2 | **Review checkpoint**: gap analysis readout, target buckets agreed | PD |

**Exit criteria**: the consuming lab signed off on which buckets we're investing in. Hiring funnel running. T2 has a clear technical scope.

---

## Phase 1, Domain skeleton (W3-W4)

| Week | Deliverable | Owner |
|---|---|---|
| W3 | data_model.py: 11 tables, schemas designed | T2 lead |
| W3 | tools.py: first 12 of 24 agent tools coded + tested | T2 (3 SWEs) |
| W3 | environment.py + utils.py: env wires up | T2 lead |
| W3 | policy.md v1 written (first 6 buckets covered) | T1 lead |
| W3 | First 25 hand-crafted tasks authored on the highest-priority buckets | T3 (5 authors) |
| W4 | Remaining 12 agent tools coded + tested | T2 |
| W4 | First 50 hand-crafted tasks total, T1-reviewed | T1 + T3 |
| W4 | DB-state generator producing 50 restaurants × 80 drivers × 200 customers | T2 |
| W4 | grader regression suite v0 (50 trajectories) | T2 + QA lead |
| W4 | **Review checkpoint #1: first slice delivered**, 50 tasks, runnable end-to-end | PD |

**Exit criteria**: the consuming lab can `tau2 run --domain food_delivery --num-tasks 50`. Bucket coverage: 4 of 12 highest-priority. Grader regression suite passing.

---

## Phase 2, Bucket coverage (W5-W8)

| Week | Deliverable | Owner |
|---|---|---|
| W5 | user_data_model.py + user_tools.py (3 personas) | T2 |
| W5 | First user-side simulators (customer + driver + restaurant) running | T2 + T1 |
| W5 | +25 hand-crafted tasks (cumulative 75) | T3 (15 authors active) |
| W5 | **Review checkpoint #2: weekly delivery** | |
| W6 | Decision tree refined based on first-slice consuming-lab feedback | PD |
| W6 | +30 hand-crafted tasks across all 12 buckets (cumulative 105) | T3 |
| W6 | safety_gate DSL + first 10 safety-gated tasks | T2 + T1 |
| W6 | **Review checkpoint #3** | |
| W7 | monetary_identity invariant implemented + tested | T2 |
| W7 | +40 hand-crafted (cumulative 145) | T3 |
| W7 | **Review checkpoint #4** | |
| W8 | All 24 agent tools production-quality | T2 |
| W8 | All 12 user tools (4 per persona) | T2 |
| W8 | +55 hand-crafted (cumulative 200, TARGET HIT) | T3 |
| W8 | grader regression suite v1 (full 250-trajectory bank) | QA lead |
| W8 | **Review checkpoint #5: bucket coverage complete** | PD |

**Exit criteria**: 200 hand-crafted tasks across all 12 buckets, all reward overrides functional, user-sim 3-persona working, full tool surface.

---

## Phase 3, Compositional generator + scale (W9-W12)

| Week | Deliverable | Owner |
|---|---|---|
| W9 | Compositional task generator v1: 72 atomic action types × 4 personas × 3 difficulty levels × 8 contexts wiring | T2 lead + 1 SWE |
| W9 | First 200 generated tasks → verification → ~140 retained | T4 (10 reviewers) |
| W9 | T3 author count ramped to 50 (final size) | Process Mgr |
| W9 | T4 reviewer count ramped to 25 (final size) | Process Mgr |
| W9 | **Review checkpoint #6** | |
| W10 | Generator yield tuning (target 70% pass rate) | T2 |
| W10 | +800 generated → ~560 retained (cumulative 700 generated) | T4 |
| W10 | **Review checkpoint #7** | |
| W11 | +1,000 generated → ~700 retained (cumulative 1,400) | T4 |
| W11 | Process reward checkpoints attached to all generated tasks | T2 + T3 |
| W11 | **Review checkpoint #8** | |
| W12 | +1,000 generated → ~700 retained (cumulative 2,100) | T4 |
| W12 | Behavioral telemetry / fraud pipeline live | T2 + QA lead |
| W12 | **Review checkpoint #9: 2,300 total tasks shipped** | PD |

**Exit criteria**: 200 hand-crafted + 2,100 generated = 2,300 tasks. Telemetry detecting AI-paste, mouse-anomaly, keystroke-pace anomalies. Generator yield stable at 70%.

---

## Phase 4, Reward calibration & QA (W13-W14)

| Week | Deliverable | Owner |
|---|---|---|
| W13 | +700 generated tasks (cumulative 3,000) | T4 |
| W13 | Difficulty calibration on 1,000 samples, recalibrate weights to hit ~50% Pass^1 average | T1 + T2 |
| W13 | Process reward checkpoint review on all hand-crafted | T1 |
| W13 | **Review checkpoint #10** | |
| W14 | Curriculum split scoring | T2 |
| W14 | LLM-judge audit of 1% sample (32 tasks), disagreement cases reviewed | T1 + QA lead |
| W14 | grader regression suite v2 with 350 trajectories | QA lead |
| W14 | **Review checkpoint #11** | |

**Exit criteria**: difficulty calibrated, curriculum splits ready, all rewards reproducible, audit clean.

---

## Phase 5, Freeze, ship, retrospect (W15-W16)

| Week | Deliverable | Owner |
|---|---|---|
| W15 | Final QA pass on 100% of hand-crafted + 5% sample of generated | T1 + QA lead |
| W15 | Splits frozen: base / train / dev / test + curriculum_easy/medium/hard | T2 |
| W15 | Submission package prepared (data + grader + docs) | PD + T2 |
| W15 | Internal LLM-grader run for triple-check | QA lead |
| W15 | **Review checkpoint #12: pre-freeze review** | |
| W16 | Consuming-lab signoff on freeze | PD |
| W16 | Final v1 handoff, leaderboard submission, dataset delivery, docs | PD + T2 |
| W16 | **Review checkpoint #13: handoff** | |
| W16 | Internal retrospective + playbook extraction kickoff | PD |

**Exit criteria**: v1 delivered, signed off by the consuming lab, leaderboard entry submitted to taubench.com, retrospective scheduled.

---

## Phase 6+, Continuous expansion + Domain 2 starter (W17+)

Two parallel tracks:
- **Track A**, Continuous food-delivery expansion: add buckets identified via post-v1 model evals; expand task volume on under-served buckets; voice modality if requested.
- **Track B**, Domain 2 starter: extract reusable infra from food-delivery, set up the next domain's skeleton. Estimated 8 weeks to v1 of domain 2.

Track B uses the same FTE pool with new T1 experts contracted-in for the new vertical. T2 engineering needs only 1 person for adapter work because the infra is reusable.

---

## Risk gates, what we revisit at each phase

| Phase exit | Re-evaluate | If off-target, what we do |
|---|---|---|
| W2 | Hiring funnel velocity | If T3 sourcing is below 50/week, extend funnel into W3 + start T1 sourcing earlier |
| W4 | First-slice feedback | If different buckets should be prioritized, swap and re-plan the remaining weeks |
| W8 | Hand-crafted authoring rate | If we're behind 200, ship 150 + 3,200 generated instead |
| W12 | Generator yield | If yield <60%, pause generation, retune. If >75%, increase target volume |
| W14 | Calibration | If average pass-rate is <30% or >70%, recalibrate difficulty weights |
| W16 | Final handoff | If signoff slips, freeze scope while resolving rather than adding new work |

The plan is opinionated about **what's fixed and what's flexible**. Quality bar and weekly cadence are fixed. Volume target is flexible. The timeline is the anchor; task volume flexes to protect the quality bar.

---

## Communication cadence

| With | Frequency | Format |
|---|---|---|
| Consuming-lab researcher | Weekly | Slice review call (30 min) + async dataset diff |
| Consuming-lab technical contact | Bi-weekly | Status doc, quality KPIs |
| Program sponsor | Weekly | 1:1 status, escalations, progress tracker |
| Core team | Daily standup | 15 min |
| T1/T2/T3/T4 contractor leads | Weekly per tier | 30 min calibration call |
| All-hands (program team) | Bi-weekly | 45 min, covers KPI review, blocker escalation |

This is the cadence that makes "weekly slices" actually work. The structure forces alignment loops to happen at the right granularity.
