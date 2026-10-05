"""LAB 1 - Tek ajan, 7 arac. Calisiyor... gibi gorunuyor. Bozacagiz.

Calistir (repo kokunden):   adk web .      sonra sol ustten "lab1_monolith" secin.
"""
from google.adk.agents import Agent

from shared.config import get_model
from shared.mock_backend import (cancel_subscription, get_invoice, handoff_to_human,
                                 issue_refund, reset_modem, run_line_diagnostics,
                                 verify_customer)

root_agent = Agent(
    name="support_agent",
    model=get_model(),
    description="Nimbus Telecom customer support agent.",
    instruction="""You are Nimbus Telecom's customer support agent.
You can help with billing, technical problems and cancellations using your tools.
Be brief and polite. If you cannot help, hand off to a human.""",
    tools=[verify_customer, get_invoice, issue_refund, run_line_diagnostics,
           reset_modem, cancel_subscription, handoff_to_human],
)
