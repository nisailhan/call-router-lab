"""Nimbus Telecom'un sahte arka ucu. Hepsi yerel Python fonksiyonu: kredi harcamaz.

ADK, her fonksiyonun adini, tip ipuclarini ve DOCSTRING'ini modele arac tanimi olarak gonderir.
Docstring'ler bu yuzden kod yorumu degil, modelin okudugu talimattir.
"""
import os

from google.adk.tools import ToolContext

CUSTOMERS = {
    "C-1001": {"name": "Ayse Demir", "pin": "4821", "plan": "Fiber 100",
               "balance_due": 249.90, "line": "ok"},
    "C-1002": {"name": "Mehmet Kaya", "pin": "7305", "plan": "Fiber 50",
               "balance_due": 0.0, "line": "modem_offline"},
    "C-1003": {"name": "John Smith", "pin": "1190", "plan": "Mobile 20GB",
               "balance_due": 89.00, "line": "ok"},
}


def verify_customer(customer_id: str, pin: str, tool_context: ToolContext) -> dict:
    """Verifies the customer's identity with their customer id and 4-digit PIN.
    Must succeed before any account-specific information is shared or changed.

    Args:
        customer_id: Customer id, for example "C-1001".
        pin: The customer's 4-digit PIN.
    """
    c = CUSTOMERS.get(customer_id)
    if not c or c["pin"] != pin:
        return {"status": "failed", "error": "Customer id or PIN is wrong."}
    tool_context.state["verified_customer"] = customer_id
    return {"status": "verified", "name": c["name"], "plan": c["plan"]}


def get_invoice(customer_id: str, tool_context: ToolContext) -> dict:
    """Returns the latest invoice summary for a customer.

    Args:
        customer_id: Customer id, for example "C-1001".
    """
    c = CUSTOMERS.get(customer_id)
    if not c:
        return {"status": "error", "error": "Unknown customer."}
    return {"status": "ok", "plan": c["plan"], "balance_due": c["balance_due"],
            "lines": [{"item": c["plan"], "amount": 199.90},
                      {"item": "Router rental", "amount": 50.00}]}


def issue_refund(customer_id: str, amount: float, reason: str,
                 tool_context: ToolContext) -> dict:
    """Issues a refund to the customer's original payment method.

    Args:
        customer_id: Customer id, for example "C-1001".
        amount: Refund amount in TRY.
        reason: Short reason for the refund.
    """
    return {"status": "refunded", "customer_id": customer_id, "amount": amount}


def run_line_diagnostics(customer_id: str, tool_context: ToolContext) -> dict:
    """Runs a remote diagnostic on the customer's internet line and modem.

    Args:
        customer_id: Customer id, for example "C-1002".
    """
    if os.getenv("FAULT") == "diagnostics_timeout":
        raise TimeoutError("Diagnostics service did not answer within 10s")
    c = CUSTOMERS.get(customer_id)
    if not c:
        return {"status": "error", "error": "Unknown customer."}
    return {"status": "ok", "line": c["line"],
            "advice": "Modem offline: a remote reset is recommended." if c["line"] != "ok"
            else "Line looks healthy."}


def reset_modem(customer_id: str, tool_context: ToolContext) -> dict:
    """Remotely restarts the customer's modem.

    Args:
        customer_id: Customer id, for example "C-1002".
    """
    return {"status": "ok", "message": "Modem restart requested, takes about 2 minutes."}


def cancel_subscription(customer_id: str, reason: str, tool_context: ToolContext) -> dict:
    """Cancels the customer's subscription at the end of the billing period.
    Only call this after the customer has clearly confirmed they want to cancel.

    Args:
        customer_id: Customer id, for example "C-1001".
        reason: The customer's stated reason for cancelling.
    """
    return {"status": "cancel_scheduled", "customer_id": customer_id}


def handoff_to_human(reason: str, queue: str = "general") -> dict:
    """Transfers the call to a human agent. Use for explicit requests for a person,
    legal threats, bereavement, safety concerns, or anything you cannot resolve.

    Args:
        reason: One sentence summary for the human agent.
        queue: "general" or "escalation".
    """
    return {"status": "handoff_queued", "queue": queue, "reason": reason}
