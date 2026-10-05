"""Cozum tarafi icin ortak ajan kurucu. Lab 2'de siz bunlarin bir kismini kendiniz yazacaksiniz.

lab2_router_solution  -> build_router(guarded=False)
demo_guarded          -> build_router(guarded=True)
"""
from google.adk.agents import Agent

from shared import guards
from shared.config import get_model
from shared.mock_backend import (cancel_subscription, get_invoice, handoff_to_human,
                                 issue_refund, reset_modem, run_line_diagnostics,
                                 verify_customer)

# ---- Uzmanlarin TALIMATLARI (Lab 2'de hazir gelir) ----
SPECIALIST_INSTRUCTIONS = {
    "billing_agent": (
        "You are the billing specialist of Nimbus Telecom. You handle invoices, charges, "
        "payments and refunds. Ask for the customer id and PIN and call verify_customer "
        "before sharing or changing anything. Only call issue_refund after telling the "
        "customer the amount and reason. If you cannot resolve the issue, call handoff_to_human."),
    "tech_agent": (
        "You are the technical support specialist of Nimbus Telecom. Ask for the customer id and "
        "PIN and call verify_customer first. Then run run_line_diagnostics and, if it recommends "
        "it, offer reset_modem. If you cannot resolve the issue, call handoff_to_human."),
    "cancel_agent": (
        "You are the retention and cancellation specialist of Nimbus Telecom. Ask for the "
        "customer id and PIN and call verify_customer first. Ask once whether a plan change or "
        "discount would change their mind. Only call cancel_subscription after the customer "
        "clearly confirms. If you cannot resolve the issue, call handoff_to_human."),
}

# ---- Uzmanlarin ACIKLAMALARI: yonlendirici sadece bunu okuyarak karar verir ----
SPECIALIST_DESCRIPTIONS = {
    "billing_agent": "Handles invoices, unexpected charges, payments, late fees, payment "
                     "methods and refunds.",
    "tech_agent": "Handles internet, Wi-Fi, modem, router, mobile data and speed problems.",
    "cancel_agent": "Handles requests to cancel or terminate a subscription or close an account, "
                    "including early termination questions.",
}

# ---- Yonlendirici talimatinin iki surumu ----
ROUTER_V1 = """You are the front-line call router of Nimbus Telecom.
Read the customer's message and transfer to the right specialist:
billing_agent, tech_agent or cancel_agent.
If the customer asks for a human, call handoff_to_human.
Do not try to solve the problem yourself."""

ROUTER_V2 = ROUTER_V1 + """

Routing policy (apply in this order):
1. Explicit request for a person, legal threats, bereavement or safety concerns:
   call handoff_to_human with queue "escalation".
2. Explicit intent to cancel or leave, even if the reason is technical or price: cancel_agent.
   Questions about early termination fees also go to cancel_agent.
3. A service problem AND a request for money back: tech_agent first (diagnose before refunding).
4. Questions about charges, invoices, payments or fees: billing_agent.
5. Too vague to classify (e.g. "I need help"): do NOT transfer. Ask ONE short clarifying question."""


def _guard_kwargs(guarded: bool) -> dict:
    if not guarded:
        return {}
    return dict(
        before_tool_callback=guards.require_verified,
        on_tool_error_callback=guards.tool_error_fallback,
        before_model_callback=guards.start_timer,
        after_model_callback=[guards.log_usage, guards.mask_pii],
    )


def build_router(instruction: str = ROUTER_V2, guarded: bool = False) -> Agent:
    model = get_model()
    tools_by_agent = {
        "billing_agent": [verify_customer, get_invoice, issue_refund, handoff_to_human],
        "tech_agent": [verify_customer, run_line_diagnostics, reset_modem, handoff_to_human],
        "cancel_agent": [verify_customer, cancel_subscription, handoff_to_human],
    }
    specialists = [
        Agent(
            name=name,
            model=model,
            description=SPECIALIST_DESCRIPTIONS[name],
            instruction=SPECIALIST_INSTRUCTIONS[name],
            tools=tools,
            disallow_transfer_to_peers=True,   # uzmanlar birbirine ping-pong yapmasin
            **_guard_kwargs(guarded),
        )
        for name, tools in tools_by_agent.items()
    ]
    router_guards = {}
    if guarded:
        router_guards = dict(before_model_callback=guards.start_timer,
                             after_model_callback=[guards.log_usage, guards.mask_pii])
    return Agent(
        name="router",
        model=model,
        description="Front-line call router for Nimbus Telecom.",
        instruction=instruction,
        tools=[handoff_to_human],
        sub_agents=specialists,
        **router_guards,
    )
