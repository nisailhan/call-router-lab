"""DEMO A2A - SUNUCU TARAFI: tech_agent'i bagimsiz bir A2A sunucusu olarak yayinlar.

Repo kokunden calistirin (ayri bir terminalde):
  uvicorn demo_a2a.tech_server:a2a_app --port 8001

Kart adresi:  http://localhost:8001/.well-known/agent-card.json
Yetki kontrolu ve olcum callback'leri (guarded=True) BU sunucuda, uzak ajanin kendi sinirinda calisir.
"""
from google.adk.a2a.utils.agent_to_a2a import to_a2a

from shared.agents import A2A_TECH_PORT, build_specialist

tech_agent = build_specialist("tech_agent", guarded=True)
a2a_app = to_a2a(tech_agent, port=A2A_TECH_PORT)
