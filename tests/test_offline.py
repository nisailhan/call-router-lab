#!/usr/bin/env python
"""Model GEREKTIRMEYEN testler: guardrail'ler, arac hata yolu, eval puanlama, ajan ici aktarimi.
Egitmen provasi icin:   python tests/test_offline.py
"""
import asyncio
import os
import sys
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["USE_FAKE_MODEL"] = "1"

from google.genai import types  # noqa: E402

from shared import guards  # noqa: E402
from shared.agents import build_router  # noqa: E402
from shared.mock_backend import run_line_diagnostics, verify_customer  # noqa: E402


def ctx_with(state=None):
    return NS(state=state if state is not None else {}, agent_name="t")


def test_access_control():
    tool = NS(name="get_invoice")
    denied = guards.require_verified(tool, {"customer_id": "C-1001"}, ctx_with())
    assert denied and denied["status"] == "denied"
    assert guards.require_verified(tool, {"customer_id": "C-1001"},
                                   ctx_with({"verified_customer": "C-1001"})) is None
    # baska musterinin hesabi: dogrulanan C-1001 iken C-1002 istenirse yine red
    assert guards.require_verified(tool, {"customer_id": "C-1002"},
                                   ctx_with({"verified_customer": "C-1001"}))["status"] == "denied"


def test_refund_limit():
    tool = NS(name="issue_refund")
    st = {"verified_customer": "C-1001"}
    assert guards.require_verified(tool, {"customer_id": "C-1001", "amount": 50}, ctx_with(st)) is None
    r = guards.require_verified(tool, {"customer_id": "C-1001", "amount": 500}, ctx_with(st))
    assert r["status"] == "needs_human_approval"


def test_pii_masking():
    text = "Kart 4111 1111 1111 1111, TC 12345678901, PIN 4821 ile giris yapildi."
    resp = NS(content=types.Content(role="model", parts=[types.Part(text=text)]))
    out = guards.mask_pii(None, resp)
    masked = out.content.parts[0].text
    assert "4111" not in masked and "12345678901" not in masked and "4821" not in masked, masked


def test_tool_error_and_fault(monkeypatch_env=True):
    os.environ["FAULT"] = "diagnostics_timeout"
    try:
        try:
            run_line_diagnostics("C-1002", ctx_with())
            raise AssertionError("TimeoutError bekleniyordu")
        except TimeoutError as e:
            r = guards.tool_error_fallback(NS(name="run_line_diagnostics"), {}, ctx_with(), e)
            assert r["status"] == "error" and "handoff_to_human" in r["instruction"]
    finally:
        os.environ["FAULT"] = ""


def test_verify_sets_state():
    st = ctx_with()
    assert verify_customer("C-1001", "0000", st)["status"] == "failed"
    assert verify_customer("C-1001", "4821", st)["status"] == "verified"
    assert st.state["verified_customer"] == "C-1001"


def test_router_structure():
    agent = build_router(guarded=True)
    names = [a.name for a in agent.sub_agents]
    assert names == ["billing_agent", "tech_agent", "cancel_agent"], names
    assert all(a.disallow_transfer_to_peers for a in agent.sub_agents)
    assert all(a.before_tool_callback for a in agent.sub_agents)


def test_end_to_end_transfer_with_fake():
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService

    async def go():
        agent = build_router()
        svc = InMemorySessionService()
        runner = Runner(agent=agent, app_name="t", session_service=svc)
        s = await svc.create_session(app_name="t", user_id="u")
        msg = types.Content(role="user", parts=[types.Part(text="My internet keeps dropping")])
        authors = [e.author async for e in runner.run_async(user_id="u", session_id=s.id,
                                                            new_message=msg)]
        return authors

    authors = asyncio.run(go())
    assert "router" in authors and "tech_agent" in authors, authors


def test_specialists_do_not_ask_for_national_id():
    from shared.agents import SPECIALIST_INSTRUCTIONS
    for name, text in SPECIALIST_INSTRUCTIONS.items():
        assert "ONLY for the customer id" in text and "national ID" in text, name


def test_a2a_router_structure():
    from shared.agents import A2A_TECH_CARD_URL
    agent = build_router(guarded=True, remote_tech_url=A2A_TECH_CARD_URL)
    kinds = {a.name: type(a).__name__ for a in agent.sub_agents}
    assert kinds == {"billing_agent": "LlmAgent", "tech_agent": "RemoteA2aAgent",
                     "cancel_agent": "LlmAgent"}, kinds


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
    print("Hepsi gecti.")
