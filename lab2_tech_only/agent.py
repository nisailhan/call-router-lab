"""LAB 2 (istege bagli) - Teknik destek uzmani TEK BASINA. Yonlendirici yok.

Bir uzmanin kendi basina nasil davrandigini gormek icin:  adk web .  ->  lab2_tech_only
"""
from shared.agents import build_specialist

root_agent = build_specialist("tech_agent", guarded=False)
