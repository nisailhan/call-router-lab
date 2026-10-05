"""DEMO (egitmen gosterir) - Ayni yonlendirici + uretim onlemleri.

Kod: shared/guards.py   Baglanti: shared/agents.py icindeki _guard_kwargs
Arizayi acmak icin:  FAULT=diagnostics_timeout adk web .
"""
from shared.agents import ROUTER_V2, build_router

root_agent = build_router(instruction=ROUTER_V2, guarded=True)
