# Food Delivery Domain, τ³-bench Spec

> Drop-in `food_delivery` domain for `sierra-research/tau2-bench` (the τ³-bench repo). This is the technical contract we ship.

---

## File contract (matches τ³-bench `domains/README.md`)

```
src/tau2/domains/food_delivery/
├── __init__.py
├── data_model.py        # subclass of DB
├── tools.py             # subclass of ToolKitBase (agent-facing)
├── environment.py       # get_environment(), get_tasks(), get_tasks_split()
├── utils.py             # data path helpers
├── user_data_model.py   # OPTIONAL, dual-control state for customer/driver/restaurant
└── user_tools.py        # OPTIONAL, tools for the user-side simulators

data/tau2/domains/food_delivery/
├── tasks.json           # ~3,200 tasks
├── split_tasks.json     # base / train / dev / test (must include "base")
├── db.json              # initial DB state (50 restaurants, 80 drivers, 200 customers, …)
├── policy.md            # the wiki, agent policy, ~30 pages
├── user_db.json         # OPTIONAL, per-role user DB
└── tasks_voice.json     # OPTIONAL, voice variants for τ³ voice modality
```

Plus one line of registration in `registry.py`:

```python
registry.register_domain(get_environment, "food_delivery")
registry.register_tasks(get_tasks, "food_delivery", get_task_splits=get_tasks_split)
```

---

## Data model, 11 tables

(retail has 3 tables; airline has 3; manufacturing has 9. Food delivery is structurally larger.)

### Core entities

| Table | Key | Notable fields |
|---|---|---|
| `customers` | customer_id | name, address, payment_methods[], dietary_constraints[], allergens_hard_flag[], dispute_history, loyalty_tier |
| `restaurants` | restaurant_id | name, address, cuisine, operating_hours, current_queue_minutes, closed_until, oos_items[], reliability_score |
| `menus` | (restaurant_id, item_id) | item_name, price, prep_time_minutes, allergens[], dietary_tags[], availability_status |
| `drivers` | driver_id | name, vehicle_type, current_lat_lng, working_hours, reliability_score, active_orders[] |
| `orders` | order_id | customer_id, restaurant_id, items[], status, placed_at, eta_at, delivered_at, total, refunds[], credits[] |
| `addresses` | address_id | line1, city, geocode, validation_status, delivery_notes |

### Marketplace dynamics

| Table | Purpose |
|---|---|
| `pricing_engine` | Surge multipliers, fee tables, time-of-day pricing rules |
| `promotions` | Promo codes with eligibility predicates (first-order, geo-fence, min-cart, expiration) |
| `wallet` | Customer credit balances, expiration, redemption history |
| `payouts` | Restaurant + driver payout ledger |
| `replacement_orders` | Linked replacement orders (orig_order_id → replacement_order_id) |

### State storage

Plain JSON loaded into Python dicts on `env.reset()` (matches τ³-bench's pattern in `tau_bench/envs/retail/data/__init__.py`). No SQLite, no ORM. This is the existing pattern; we don't deviate.

---

## Tool surface, 24 agent tools + 12 user tools

(retail has 16 agent tools; airline has 14; manufacturing has 17. Food delivery's 24 is 50% larger than retail and calibrated to the 12-bucket capability surface; the breakdown is 13 read tools, 7 write tools, 4 escalation tools.)

### Agent tools (24)

**Read tools (13, no DB mutation):**

| Tool | Purpose |
|---|---|
| `find_customer_by_phone_or_email` | Identify the user |
| `get_customer_details` | Profile, dietary flags, dispute history |
| `get_order_details` | Current state of an order |
| `list_orders_for_customer` | Recent order history |
| `get_restaurant_details` | Hours, capacity, reliability |
| `search_menu_items` | With optional `exclude_allergens=[]` filter |
| `get_driver_details` | Driver location, ETA, reliability |
| `track_order_eta` | Real-time ETA (returns distribution, not point estimate) |
| `quote_delivery_fee` | Time-stamped fee quote (pricing_engine snapshot) |
| `check_promo_eligibility` | Returns boolean + reason if rejected |
| `check_restaurant_capacity` | Capacity at a given timestamp |
| `validate_address` | Geocoding + delivery zone check |
| `Think` | Chain-of-thought scratch (shared across τ³ domains) |

**Write tools (7, DB mutation):**

| Tool | Purpose | Confirmation required? |
|---|---|---|
| `place_order` | Create order, charge customer, dispatch | Yes, surface order summary |
| `modify_order` | Add/remove items, change address pre-pickup, apply promo | Yes |
| `cancel_order` | With reason enum {customer_initiated, restaurant_initiated, driver_unavailable} | Yes |
| `issue_refund_or_credit` | Refund to original payment OR wallet credit (single tool, mode arg) | **Yes, monetary action** |
| `request_and_confirm_substitute` | Two-stage: surface substitute, capture consent, apply | Yes on confirm |
| `dispatch_replacement_courier` | Assign new driver to existing order | Yes |
| `notify_party` | Push message to restaurant or driver (party arg) | No |

**Escalation (4):**

| Tool | Purpose |
|---|---|
| `flag_account_for_fraud_review` | Non-terminal flag; the human reviews async |
| `transfer_to_human_supervisor` | Terminate episode; reward depends on whether escalation was warranted |
| `transfer_to_dispatch` | Specific to driver/restaurant operational issues |
| `transfer_to_safety_team` | Specific to allergen/safety incidents |

Total: 13 + 7 + 4 = 24 agent tools. Calibrated to 50% larger than retail's 16, not the 30 a naive count would produce; tools that share state mutation patterns are merged with mode arguments rather than split.

### User tools (dual-control, τ²-bench pattern)

The user side has THREE simulator personas, each with their own tools:

**Customer (4 tools):**
- `provide_information_to_agent`, `accept_substitute`, `refuse_substitute`, `terminate_conversation`

**Driver (4 tools):**
- `update_location`, `mark_pickup`, `mark_delivered`, `report_issue` (e.g. customer absent, address wrong)

**Restaurant (4 tools):**
- `mark_order_received`, `mark_prep_started`, `mark_oos_during_prep`, `mark_ready_for_pickup`

This is the multi-actor extension of τ²-bench's two-actor dual-control. Each role has its own LLM persona simulator with its own observation/action space, but they all act on the same shared env state, Dec-POMDP, generalized to N actors.

---

## Policy wiki (`policy.md`), outline

~30 pages, sections roughly mirroring the 12 buckets:

1. Identity verification (when required, how to handle failures)
2. Order-placement rules (eligibility, validation, pricing transparency)
3. Modification rules (windows, what's reversible)
4. Cancellation matrix (state × initiator × eligibility)
5. Substitution policy (consent flow, allergen safety)
6. Driver coordination protocols
7. Restaurant coordination protocols
8. Compensation matrix (severity × customer tier × authorization level)
9. Allergen safety protocol (hard rules, agent NEVER overrides)
10. Group/scheduled order rules
11. Promo/loyalty/surge rules (eligibility, stacking)
12. Fraud handling (escalation triggers, do-not-engage scenarios)
13. Confirmation rules (when explicit yes/no is required), copied from retail wiki pattern
14. Escalation rules (when to transfer to human, mandatory escalations)

The wiki is the agent's system prompt. It is also what the agent must follow under pressure, bucket 7 specifically tests whether the agent caves on it.

---

## Reward design (see `05_reward_design.md` for full)

Base τ³-bench reward (binary 0/1 from DB-state-hash equality + output substring) is **insufficient** for food delivery because:

1. Multiple valid action orderings (driver A or driver B both valid) → DB-hash equality is too strict → use **equivalence-class hashing**
2. Allergen safety is a hard rule independent of DB state → add **safety-gate reward** (hard-zero on violation)
3. Refunds + credits + replacements + payouts must sum to disputed amount, but ledger entries can be in any order → add **monetary identity invariant** check
4. RL training needs dense per-checkpoint signal, not sparse end-of-episode → add **process reward**

These are described in `05_reward_design.md`.

---

## Compositional task generator, design

(extends τ²-bench's compositional generator pattern.)

**Atomic components:**
- 12 buckets × ~6 L2 sub-buckets = 72 atomic action types
- 4 customer personas (cooperative, adversarial, pressured, abusive)
- 3 difficulty levels (1, 3, 5)
- 8 environmental contexts (restaurant_busy, driver_shortage, surge, allergen_present, holiday, weather_event, address_ambiguous, payment_issue)

**Generator output**: a Task instance with:
- Random combination of (atomic, persona, difficulty, context)
- Generated `instruction` string via LLM with persona prompt
- Generated ground-truth `actions` from atomic action templates
- Generated `outputs` substring assertions where applicable
- Embedded difficulty + bucket annotations

**Verification step**: generated tasks are NOT auto-shipped. Each is verified by:
1. Auto-replay of ground-truth actions on the env, must produce the expected DB delta
2. T4 reviewer pass (5 minutes/task average), sanity check the instruction, persona consistency, action sequence

**Yield**: ~70% of generated tasks pass verification. Generate 4,500 to ship 3,000.

---

## Splits

`split_tasks.json`:

```json
{
  "base":   ["task_0001", ...],   // ~600, eval, matches retail/airline pattern
  "train":  ["task_0601", ...],   // ~2,400, RL training
  "dev":    ["task_3001", ...],   // ~300, held out for hyperparameter tuning
  "test":   ["task_3301", ...],   // ~300, final eval
  "curriculum_easy":   ["task_…"],
  "curriculum_medium": ["task_…"],
  "curriculum_hard":   ["task_…"]
}
```

Splits are stratified by `(bucket, difficulty)`, every split is balanced across the 12 capability buckets and 5 difficulty levels.

---

## What this domain teaches us about domains 2..N

After shipping food delivery, the patterns that **transfer**:

1. The 11-table data model has 6 marketplace-specific tables (`pricing_engine`, `promotions`, `wallet`, `payouts`, `replacement_orders`) → **reusable for any two-sided marketplace**
2. The 3-persona user-simulator pattern (customer + supplier + intermediary) → reusable for ride-share, healthcare scheduling, B2B procurement, field service
3. The 4-tier reward design (equiv-class + safety + monetary + dense) → reusable wherever stochastic, safety-relevant, or financial domains apply
4. The compositional generator's (atomic × persona × difficulty × context) framing → reusable as-is

We will explicitly extract these as a `tau_bench_marketplace_kit` after shipping food delivery, so domain 2 starts from this scaffold. Estimated reuse: 60-70% of code; 100% of methodology.
