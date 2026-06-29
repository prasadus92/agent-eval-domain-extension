# Cost Model, FTE × Throughput × Margin

> **All numbers are model assumptions, clearly labeled.** They are calibrated against publicly known industry rates and published industry stats for large labeling platforms. Anything a real operator knows internally that contradicts these should override them.

---

## Per-task fully-loaded cost (hand-crafted)

| Component | Hours/task | $/hour | $/task |
|---|---|---|---|
| T3 trajectory writer (author + run + check) | 0.80 | $30 | $24.00 |
| T1 expert review (sampled, 30% of tasks) | 0.15 | $120 | $18.00 |
| T4 fraud / paste-detection / telemetry triage | 0.10 | $15 | $1.50 |
| T2 grader regression-suite cost amortized | 0.05 | $80 | $4.00 |
| Tooling, infra, LLM grader runs, storage | n/a |, | $5.00 |
| **Total per hand-crafted task** | | | **~$52.50** |

## Per-task fully-loaded cost (compositionally generated + verified)

| Component | Hours/task | $/hour | $/task |
|---|---|---|---|
| Compositional generator runtime (LLM compose + verify) | 0.05 | n/a | $4.00 |
| T4 reviewer pass (sanity, persona consistency, replay) | 0.10 | $15 | $1.50 |
| T3 fix-up on rejected tasks (30% rejection rate, 15 min each) | 0.075 amortized | $30 | $2.25 |
| T1 spot-check (5% sample) | 0.0075 | $120 | $0.90 |
| Tooling / infra | n/a |, | $3.00 |
| **Total per generated-and-verified task** | | | **~$11.65** |

(Generation rejection rate of ~30% is conservative; some tasks fail the auto-replay verification and need T3 cleanup.)

---

## v1 program P&L

### Inputs
- Hand-crafted seed tasks: **200**
- Compositionally generated + verified tasks: **3,000**
- Program length: **16 weeks**
- Core-team FTE allocation: **4 people × 4 months × $200K/yr = $267K**
- Tier 1 expert pool (4 people, ~50% allocation × 16 wk × $120/hr × 30 hr/wk): **~$115K**
- Tier 2 engineering pool (4 people × 16 wk × $80/hr × 30 hr/wk): **~$153K**
- Tier 3 trajectory authors (50 peak, ramping; not all FTE, see throughput model below): cost is captured per-task above
- Tier 4 reviewers: cost is captured per-task above
- Tooling, LLM API, infra, hiring funnel, vetting: **$60K**

### Direct task costs
- 200 hand-crafted × $52.50 = **$10,500**
- 3,000 generated × $11.65 = **$34,950**

### Total v1 cost
| Bucket | Amount |
|---|---|
| Core-team FTE | $267,000 |
| T1 domain experts | $115,000 |
| T2 engineering | $153,000 |
| Direct task costs (T3 + T4 + infra-per-task) | $45,450 |
| Tooling, infra, hiring funnel, vetting | $60,000 |
| **Total v1 cost** | **~$640,000** |

(Earlier mental model was $520K, refining here with the actual cost line items adds ~$120K. The T3 author labor moves out of FTE assumption and into per-task; T2 engineering becomes a separate line. This is the more honest number.)

### Pricing target
- **Price target: $900K-$1.0M** for v1 dataset + grader infrastructure + RL-shaped rewards + curriculum splits
- **Gross margin: ~30-35%**

This is a thinner margin than I'd want for a steady-state program. v1 is margin-light by design; the team is building infrastructure that pays back across later domains. See domain-2 economics below.

---

## Domain 2 P&L (food-delivery → ride-share, hotel, healthcare scheduling, etc.)

What's reusable from v1 (60-70% of code, 100% of methodology):
- Compositional task generator (parameterize for new atomic action types)
- User simulator framework (the 3-persona structure)
- Behavioral telemetry / fraud pipeline
- Grader regression suite tooling
- Reward overrides DSL (safety gate, monetary identity, equivalence class, process checkpoints)
- Hiring funnel (T1-T4 templates, work-sample tests, calibration sessions)
- Cost dashboard, weekly margin tracking
- Two-sided-marketplace VRN pattern (where applicable)
- Curriculum-difficulty annotation schema

What's new per-domain:
- `data_model.py` (schemas)
- `tools.py` (domain-specific tools)
- `policy.md` (~30 pages of domain rules)
- ~150 hand-crafted seed tasks (lower than v1's 200 because we're starting from a working pattern)
- T1 domain experts (different vertical)

### Domain 2 costs

| Bucket | Amount |
|---|---|
| Core-team FTE (8 weeks × 4 people × $200K/yr) | $123,000 |
| T1 new domain experts (4 people × 8 wk × $120/hr × 30 hr) | $58,000 |
| T2 engineering (1 person × 8 wk, small adapter work only) | $19,000 |
| Direct task costs (150 × $52.50 + 2,500 × $11.65) | $37,000 |
| Tooling, infra | $15,000 |
| **Total domain 2 cost** | **~$252,000** |

| Pricing target | $600,000-$700,000 |
| Gross margin | **~58-65%** |

The compounding works. By domain 4 the margin is in the 65-70% range.

---

## Throughput model

### Hand-crafted task throughput

A T3 trajectory writer averages 1 task / hour for difficulty-2 tasks (most common) and 0.5 tasks / hour for difficulty-4 (multi-step recovery). With a 50-author pool working ~30 hours/week:

- Mixed-difficulty average: 0.75 tasks / author / hour
- 50 authors × 30 hours × 0.75 = ~1,125 tasks / week

We don't need that throughput on hand-crafted tasks (200 total over 16 weeks = 12.5/week avg). The pool is sized for the **generated-task verification** pass, which IS the throughput bottleneck:

### Generated-task verification throughput

T4 reviewers verify generated tasks at ~6 minutes / task (10 / hour, but with quality dips above that). 25 reviewers × 30 hours × 10 = 7,500 verifications / week, comfortable headroom over our 200 / week target rate during the W9-W12 generation phase.

### The actual bottleneck

Bottleneck is **T1 expert review** for the hand-crafted seed tasks. 4 T1 experts × 30 hours × 6 reviews/hour (15 min each, sampled at 30% × 200 hand-crafted = 60 reviews) = trivially completable. T1 capacity is consumed by:
- Policy.md authoring (~10 person-days)
- Decision-tree gap analysis (W1-W2, ~20 person-days)
- Bucket-by-bucket QA (continuous)
- Final QA pass before delivery (W15-W16)

T1 is a strategic bottleneck, they design what's right; they don't execute.

---

## Margin protection mechanics

A common failure mode to avoid: "with a negative margin it's easier to deliver fast." Here's how we don't fall into that trap.

1. **Per-bucket $/task tracking, weekly.** Dashboard shows actual hours-per-task by bucket. If a bucket exceeds 1.5x the budget, we either kill the bucket or restructure (move from hand-crafted to generated where possible).

2. **Tier-routing gate.** Every task type has a routing rule: "T3 author, T4 review, T1 sample only." If a writer flags a task as needing T1 design help, that triggers a routing review, not an automatic escalation. T1 hours are budgeted weekly.

3. **Compositional generator yield monitoring.** Generation rejection rate started at 30% but can drift. If it climbs above 40%, generator is paused for tuning rather than absorbing more T3 fix-up labor.

4. **Hard cost cap per bucket per week.** If a bucket consumes more than its budget two weeks running, the bucket goes to a kill/restructure decision in the weekly review.

5. **No bonus on volume; bonus on grader-pass-rate.** T3 writers earn a bonus tied to "% of your tasks that the grader passes on first replay attempt." This decouples bonus from speed, you can't game it by writing many bad tasks fast.

---

## Hiring funnel cost

Filling the T3 pool (50 trajectory writers) is a known operational risk. Funnel:

| Stage | Yield | Cost / candidate |
|---|---|---|
| Sourced (labeling platforms + outbound + Upwork-tier platforms) | 100% | $5 (sourcer time) |
| AI-administered work-sample test (write 3 trajectories, auto-graded) | 30% pass | $0 (auto) |
| Human pair-review on first 5 paid tasks | 60% retain | $80 (1 hr × $80 reviewer rate) |
| Calibration over 2-week onboarding | 70% retain | covered by per-task labor budget |

End-to-end conversion: ~12.5%. To fill 50 seats, we source ~400 candidates. Cost: ~$5,000 sourcing + ~$10,000 in pair-review hours = $15,000 total. Already included in the $60K tooling/infra line above.

T1 experts are headhunted directly (4 people, 4-week sourcing window). Cost ~$10,000 in recruiter or fee.

---

## Sensitivity analysis

If our assumptions are off by 25% in either direction:

| Variable | -25% | Base | +25% |
|---|---|---|---|
| T3 hourly rate | $22.50 | $30 | $37.50 |
| Hand-crafted hours per task | 0.6 | 0.8 | 1.0 |
| Compositional rejection rate | 22% | 30% | 38% |
| **v1 total cost** | **~$555K** | **~$640K** | **~$735K** |
| **v1 margin at $950K price** | **42%** | **33%** | **23%** |

Below 25% margin we'd want to renegotiate or descope. The hand-crafted task volume is the most flexible variable, we can ship 150 hand-crafted + 2,800 generated and protect margin if the generator is high-quality.

---

## Pricing benchmark

Public datapoints used to anchor the $900K-$1.0M target:
- Scale AI's published "Donovan" product pricing for vertical datasets in the seven figures
- Surge AI's published pricing tiers (referenced anecdotally in industry; data costs ~$20/task for general annotation, much higher for expert work)
- industry positioning of dataset-extension as "frontier-lab" pricing, implies six-to-seven figures
- Tau-bench's value as a known benchmark gives the consuming lab a "we know what we're getting" frame, which de-risks pricing premium

If the lab pushes back, we can offer:
- Outcome-only reward variant (drop the dense reward shaping) for ~$650K
- Smaller v1 (1,500 tasks) for ~$500K, paid as a pilot, with full v1 expansion contracted upon successful pilot eval

We do NOT discount the methodology infrastructure (grader regression, fraud pipeline), those are what make the second domain cheap. Those costs stay.
