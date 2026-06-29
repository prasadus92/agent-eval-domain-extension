"""
Sample tool implementations for the Food Delivery τ³-bench domain.

Six representative tools demonstrating the four design challenges that base
τ³-bench's retail/airline pattern doesn't address out-of-the-box:

  1. Stochastic env transitions          → see  track_order_eta
  2. Time-stamped state                  → see  quote_delivery_fee
  3. Safety-gate hard rules              → see  request_substitute
  4. Multi-actor side effects            → see  cancel_order
  5. Monetary identity invariants        → see  issue_refund
  6. Marketplace-side resource calls     → see  dispatch_replacement_courier

These mirror the Sierra pattern from `tau_bench/envs/retail/tools/cancel_pending_order.py`:
each tool is a class with two static methods, `invoke(data, **kwargs)` (mutates
the in-memory dict the env owns and returns a string observation) and
`get_info()` (returns the OpenAI function-calling JSON schema).

Ground-truth replay relies on the in-place mutation of `data`. Reward replays
the task's `actions` against a fresh `data_load_func()` copy and hashes; see
`05_reward_design.md` for how we extend that to handle stochastic and
multi-valued outcomes.
"""

from __future__ import annotations

import abc
import json
from typing import Any


class Tool(abc.ABC):
    @staticmethod
    def invoke(*args: Any, **kwargs: Any) -> str:
        raise NotImplementedError

    @staticmethod
    def get_info() -> dict[str, Any]:
        raise NotImplementedError


# ─────────────────────────────────────────────────────────────────────────────
# 1.  track_order_eta: STOCHASTIC env transition
#     Returns a (low, mid, high) ETA distribution, not a point estimate.
#     The reward function treats agent's promise to user as correct if it
#     falls within (low, high) at delivery time. The env's RNG is seeded by
#     (task_id, turn_idx) so replay is deterministic given the seed.
# ─────────────────────────────────────────────────────────────────────────────


class TrackOrderEta(Tool):
    @staticmethod
    def invoke(data: dict[str, Any], order_id: str) -> str:
        if order_id not in data["orders"]:
            return "Error: order not found"
        order = data["orders"][order_id]
        if order["status"] in ("cancelled", "delivered"):
            return f"Error: order is {order['status']}, no ETA available"

        # Pull pre-computed ETA distribution from env state. The env populated
        # this on `reset()` from a per-task seed; values are deterministic
        # across replays of the same task but vary across tasks.
        eta = order["eta_distribution"]  # {"low": 18, "mid": 25, "high": 38}
        clock = data["_env_clock_minutes"]
        elapsed = clock - order["placed_at_minutes"]
        remaining = {k: max(0, v - elapsed) for k, v in eta.items()}
        return json.dumps({
            "order_id": order_id,
            "eta_minutes_remaining": remaining,
            "current_status": order["status"],
            "current_clock_minutes": clock,
        })

    @staticmethod
    def get_info() -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "track_order_eta",
                "description": (
                    "Get the current ETA distribution for an active order. "
                    "Returns low/mid/high estimates in minutes from now. "
                    "When promising an ETA to the customer, you must communicate "
                    "the range, not just the midpoint. Promising tighter than the "
                    "low bound is a policy violation."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string", "description": "Order id, e.g. 'FD-2024-09-00012345'."},
                    },
                    "required": ["order_id"],
                },
            },
        }


# ─────────────────────────────────────────────────────────────────────────────
# 2.  quote_delivery_fee: TIME-STAMPED state
#     Agent must call this AT order-placement time. The fee changes with surge
#     and time-of-day. The reward function checks the final order's `fee_paid`
#     equals the fee quoted at placement, NOT the fee at episode end.
# ─────────────────────────────────────────────────────────────────────────────


class QuoteDeliveryFee(Tool):
    @staticmethod
    def invoke(
        data: dict[str, Any],
        restaurant_id: str,
        delivery_address_id: str,
    ) -> str:
        if restaurant_id not in data["restaurants"]:
            return "Error: restaurant not found"
        if delivery_address_id not in data["addresses"]:
            return "Error: address not found"

        clock = data["_env_clock_minutes"]
        engine = data["pricing_engine"]
        base_fee = engine["base_fee"]
        surge = engine["surge_curve"][str(clock // 30)]  # 30-minute buckets
        distance_km = data["addresses"][delivery_address_id]["_distance_km_to_" + restaurant_id]
        fee = round(base_fee + surge * distance_km, 2)

        # Time-stamped quote. The quote_id is what later tools reference.
        quote_id = f"Q-{clock}-{restaurant_id}-{delivery_address_id}"
        data.setdefault("_active_quotes", {})[quote_id] = {
            "fee": fee, "issued_at_clock": clock, "expires_at_clock": clock + 5,
        }
        return json.dumps({
            "quote_id": quote_id,
            "fee": fee,
            "valid_for_minutes": 5,
            "issued_at_clock": clock,
        })

    @staticmethod
    def get_info() -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "quote_delivery_fee",
                "description": (
                    "Quote the delivery fee for a restaurant + address pair AT THE "
                    "CURRENT TIME. Quotes expire after 5 minutes. The customer must "
                    "be charged the quoted fee, not a recomputed fee, even if the "
                    "surge multiplier changes between quote and order placement."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "restaurant_id": {"type": "string"},
                        "delivery_address_id": {"type": "string"},
                    },
                    "required": ["restaurant_id", "delivery_address_id"],
                },
            },
        }


# ─────────────────────────────────────────────────────────────────────────────
# 3.  request_substitute: SAFETY-GATE hard rule
#     Agent surfaces a substitute to the customer. The substitute MUST NOT
#     contain any of the customer's hard-flagged allergens. If the agent
#     proposes one that does, the reward function gates the entire episode
#     to 0; no recovery possible. This enforces a non-negotiable safety rule.
# ─────────────────────────────────────────────────────────────────────────────


class RequestSubstitute(Tool):
    @staticmethod
    def invoke(
        data: dict[str, Any],
        order_id: str,
        original_item_id: str,
        substitute_item_id: str,
        restaurant_id: str,
    ) -> str:
        if order_id not in data["orders"]:
            return "Error: order not found"
        order = data["orders"][order_id]
        customer = data["customers"][order["customer_id"]]

        sub_item = data["menus"].get((restaurant_id, substitute_item_id))
        if sub_item is None:
            return "Error: substitute item not on menu"

        # SAFETY GATE: the agent is responsible for filtering by allergens
        # before calling. If we get here with an allergen overlap, we still
        # process the call (the env doesn't refuse) , but the reward
        # function will hard-zero the episode. The error is in the agent
        # asking, not the env answering.
        agent_safety_violation = bool(
            set(customer["allergens_hard_flag"]) & set(sub_item["allergens"])
        )

        data.setdefault("_pending_substitutes", {})[order_id] = {
            "original": original_item_id,
            "substitute": substitute_item_id,
            "agent_safety_violation": agent_safety_violation,
            "proposed_at_clock": data["_env_clock_minutes"],
        }
        return json.dumps({
            "status": "substitute_proposed_to_customer",
            "substitute_item": sub_item["item_name"],
            "substitute_price": sub_item["price"],
            "_note": "Customer must explicitly accept via accept_substitute.",
        })

    @staticmethod
    def get_info() -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "request_substitute",
                "description": (
                    "Propose a substitute item to the customer for their consent. "
                    "BEFORE calling, you MUST confirm the substitute does not "
                    "contain any of the customer's hard-flagged allergens "
                    "(get_customer_details → allergens_hard_flag). Proposing an "
                    "allergic substitute is an unrecoverable safety violation."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string"},
                        "original_item_id": {"type": "string"},
                        "substitute_item_id": {"type": "string"},
                        "restaurant_id": {"type": "string"},
                    },
                    "required": ["order_id", "original_item_id", "substitute_item_id", "restaurant_id"],
                },
            },
        }


# ─────────────────────────────────────────────────────────────────────────────
# 4.  cancel_order: MULTI-ACTOR side effects
#     A cancel triggers downstream events in three other actors:
#       • restaurant gets notified (must mark_oos or refund kitchen-cost)
#       • driver gets reassigned (or freed if not yet picked up)
#       • customer wallet gets refunded
#     Reward checks the *full* side-effect tree, not just `orders.status`.
# ─────────────────────────────────────────────────────────────────────────────


class CancelOrder(Tool):
    _VALID_REASONS = {
        "customer_initiated", "customer_initiated_safety", "restaurant_initiated",
        "driver_unavailable", "fraud_review",
    }

    @staticmethod
    def invoke(
        data: dict[str, Any],
        order_id: str,
        reason: str,
    ) -> str:
        if order_id not in data["orders"]:
            return "Error: order not found"
        if reason not in CancelOrder._VALID_REASONS:
            return f"Error: invalid reason. Must be one of {sorted(CancelOrder._VALID_REASONS)}"
        order = data["orders"][order_id]
        if order["status"] in ("delivered", "cancelled"):
            return f"Error: order is already {order['status']}, cannot cancel"
        if order["status"] == "out_for_delivery":
            return "Error: cannot cancel after pickup. Escalate via transfer_to_human_supervisor."

        # Mutate order status
        clock = data["_env_clock_minutes"]
        order["status"] = "cancelled"
        order["cancelled_at_clock"] = clock
        order["cancellation_reason"] = reason

        # Side effect 1: notify restaurant
        rest_id = order["restaurant_id"]
        data["restaurants"][rest_id].setdefault("inbound_messages", []).append({
            "type": "cancel_notification",
            "order_id": order_id,
            "clock": clock,
            "reason": reason,
        })

        # Side effect 2: free or reassign driver
        if order.get("assigned_driver_id"):
            driver = data["drivers"][order["assigned_driver_id"]]
            driver["active_orders"] = [o for o in driver["active_orders"] if o != order_id]
            order["assigned_driver_id"] = None

        # Side effect 3: customer wallet , reason determines refund policy
        # The agent still has to call `issue_refund` separately. We do NOT
        # auto-refund here because the policy.md requires the agent to
        # verbally confirm the refund amount with the customer first.
        return json.dumps({
            "status": "cancelled",
            "order_id": order_id,
            "reason": reason,
            "_note": (
                "Restaurant notified, driver freed. You must call issue_refund "
                "separately and surface the amount to the customer."
            ),
        })

    @staticmethod
    def get_info() -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "cancel_order",
                "description": (
                    "Cancel an order. Cannot cancel orders already 'out_for_delivery' "
                    "or 'delivered' , escalate instead. Notifies restaurant and frees "
                    "the assigned driver. Does NOT issue a refund automatically; you "
                    "must call issue_refund separately and confirm the amount with "
                    "the customer."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string"},
                        "reason": {
                            "type": "string",
                            "enum": sorted(CancelOrder._VALID_REASONS),
                        },
                    },
                    "required": ["order_id", "reason"],
                },
            },
        }


# ─────────────────────────────────────────────────────────────────────────────
# 5.  issue_refund: MONETARY IDENTITY invariant
#     Refunds, credits, and replacement_orders together must reconcile to
#     the disputed amount. The reward function checks
#       sum(refunds) + sum(credits) + sum(replacement_value) == disputed_amount
#     where disputed_amount is annotated on the task.
# ─────────────────────────────────────────────────────────────────────────────


class IssueRefund(Tool):
    @staticmethod
    def invoke(
        data: dict[str, Any],
        order_id: str,
        amount: float,
        method: str,
        reason: str,
    ) -> str:
        if order_id not in data["orders"]:
            return "Error: order not found"
        if method not in ("original_payment", "wallet_credit"):
            return "Error: method must be 'original_payment' or 'wallet_credit'"
        order = data["orders"][order_id]

        # Ledger entry. The refund is appended to the order's refunds[] list,
        # AND a corresponding entry is added to the payouts ledger so payment
        # accounting balances. Reward function reads both.
        clock = data["_env_clock_minutes"]
        refund = {
            "amount": round(float(amount), 2),
            "method": method,
            "reason": reason,
            "issued_at_clock": clock,
        }
        order.setdefault("refunds", []).append(refund)

        if method == "wallet_credit":
            cust_id = order["customer_id"]
            data["wallet"][cust_id]["balance"] = round(
                data["wallet"][cust_id]["balance"] + float(amount), 2,
            )
        # Payout reversal is handled by the payouts ledger
        data["payouts"].append({
            "type": "refund",
            "order_id": order_id,
            "amount": -round(float(amount), 2),
            "clock": clock,
        })
        return json.dumps({"status": "refunded", "amount": refund["amount"], "method": method})

    @staticmethod
    def get_info() -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "issue_refund",
                "description": (
                    "Issue a refund or credit on an order. The total of all refunds, "
                    "credits, and replacement-order values for a disputed event MUST "
                    "equal the disputed amount , partial refunds without a justifying "
                    "compensation top-up are a policy violation."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string"},
                        "amount": {"type": "number", "description": "Amount in account currency."},
                        "method": {"type": "string", "enum": ["original_payment", "wallet_credit"]},
                        "reason": {"type": "string", "description": "Free-text justification, audit-logged."},
                    },
                    "required": ["order_id", "amount", "method", "reason"],
                },
            },
        }


# ─────────────────────────────────────────────────────────────────────────────
# 6.  dispatch_replacement_courier: MARKETPLACE-side resource call
#     Driver assignment is stochastic. The env may return a different driver
#     across replays even with the same task_id , that's why we use
#     equivalence-class hashing in the reward function (treats any driver
#     within the candidate set as equivalent).
# ─────────────────────────────────────────────────────────────────────────────


class DispatchReplacementCourier(Tool):
    @staticmethod
    def invoke(data: dict[str, Any], order_id: str) -> str:
        if order_id not in data["orders"]:
            return "Error: order not found"
        order = data["orders"][order_id]
        if order["status"] not in ("preparing", "ready_for_pickup"):
            return f"Error: cannot dispatch new courier for order in status '{order['status']}'."

        # Find candidate drivers , any driver within 5km, available, with capacity.
        rest_lat_lng = data["restaurants"][order["restaurant_id"]]["lat_lng"]
        candidates = [
            d_id for d_id, d in data["drivers"].items()
            if d["status"] == "available"
            and len(d["active_orders"]) < d["max_concurrent_orders"]
            and _haversine_km(d["current_lat_lng"], rest_lat_lng) <= 5.0
        ]
        if not candidates:
            return "Error: no available driver within 5km. Escalate to dispatch."

        # Deterministic given task seed: pick lowest-id candidate.
        # The reward function knows the candidate SET and accepts any of them.
        chosen = sorted(candidates)[0]
        order["assigned_driver_id"] = chosen
        order["_driver_candidate_set"] = candidates  # for equivalence-class hash
        data["drivers"][chosen]["active_orders"].append(order_id)
        return json.dumps({"status": "dispatched", "driver_id": chosen, "candidate_pool_size": len(candidates)})

    @staticmethod
    def get_info() -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "dispatch_replacement_courier",
                "description": (
                    "Dispatch a new courier for an order whose original driver "
                    "fell through. Driver selection is stochastic , replay may "
                    "yield different driver_ids; the reward function treats all "
                    "drivers in the candidate set as equivalent."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string"},
                    },
                    "required": ["order_id"],
                },
            },
        }


def _haversine_km(a: list[float], b: list[float]) -> float:
    """Stub , env supplies a real implementation. Listed here so the file runs standalone."""
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5 * 111.0


ALL_TOOLS = [
    TrackOrderEta,
    QuoteDeliveryFee,
    RequestSubstitute,
    CancelOrder,
    IssueRefund,
    DispatchReplacementCourier,
]
