"""LAB 2 - Yonlendirici + uzman ajanlar. 5 bosluk (TODO) doldurulacak.

Her TODO satirini LAB.md'deki kodla DEGISTIRIN (satirin tamamini).
Takilirsaniz: lab2_router_solution/agent.py cozumun kendisidir.
"""
from google.adk.agents import Agent

from shared.agents import SPECIALIST_INSTRUCTIONS  # uzman talimatlari hazir
from shared.config import get_model
from shared.mock_backend import (cancel_subscription, get_invoice, handoff_to_human,
                                 issue_refund, reset_modem, run_line_diagnostics,
                                 verify_customer)

MODEL = get_model()

# --- Uzmanlar. 'description' alanini YONLENDIRICI okur: dogru yonlendirme buna baglidir ---
billing_agent = Agent(
    name="billing_agent",
    model=MODEL,
    description="",  # TODO: REPLACE_BILLING_DESCRIPTION
    instruction=SPECIALIST_INSTRUCTIONS["billing_agent"],
    tools=[verify_customer, get_invoice, issue_refund, handoff_to_human],
    disallow_transfer_to_peers=True,
)

tech_agent = Agent(
    name="tech_agent",
    model=MODEL,
    description="",  # TODO: REPLACE_TECH_DESCRIPTION
    instruction=SPECIALIST_INSTRUCTIONS["tech_agent"],
    tools=[verify_customer, run_line_diagnostics, reset_modem, handoff_to_human],
    disallow_transfer_to_peers=True,
)

cancel_agent = Agent(
    name="cancel_agent",
    model=MODEL,
    description="",  # TODO: REPLACE_CANCEL_DESCRIPTION
    instruction=SPECIALIST_INSTRUCTIONS["cancel_agent"],
    tools=[verify_customer, cancel_subscription, handoff_to_human],
    disallow_transfer_to_peers=True,
)

# --- Yonlendirici ---
root_agent = Agent(
    name="router",
    model=MODEL,
    description="Front-line call router for Nimbus Telecom.",
    instruction="TODO: REPLACE_ROUTER_INSTRUCTION",
    tools=[handoff_to_human],
    sub_agents=[],  # TODO: REPLACE_SUBAGENTS
)
