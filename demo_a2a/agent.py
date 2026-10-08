"""DEMO A2A - ISTEMCI TARAFI: router ayni, ama tech_agent artik uzak bir sunucuda (A2A).

Once tech_server'i baska bir terminalde baslatin:
  uvicorn demo_a2a.tech_server:a2a_app --port 8001
Sonra:  adk web .   ->  demo_a2a
"""
from shared.agents import A2A_TECH_CARD_URL, ROUTER_V2, build_router

root_agent = build_router(instruction=ROUTER_V2, guarded=True, remote_tech_url=A2A_TECH_CARD_URL)
