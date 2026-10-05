"""LAB 2 COZUMU. Takilan katilimcilar bu klasore gecip Lab 3'e devam eder.

Lab 3'te duzenlenecek yer: asagidaki INSTRUCTION. (Tam politika surumu: shared/agents.py -> ROUTER_V2)
"""
from shared.agents import build_router

INSTRUCTION = """You are the front-line call router of Nimbus Telecom.
Read the customer's message and transfer to the right specialist:
billing_agent, tech_agent or cancel_agent.
If the customer asks for a human, call handoff_to_human.
Do not try to solve the problem yourself."""

root_agent = build_router(instruction=INSTRUCTION, guarded=False)
