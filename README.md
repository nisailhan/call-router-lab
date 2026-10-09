# Çağrı Merkezi Yönlendirme Ajanı: Prototipten Üretime (ADK + Gemini)

60 dakikalık workshop için lab paketi.

- **Katılımcılar:** [`LAB.md`](LAB.md)
- **Örnek sorular:** [`ORNEK_SORULAR.md`](ORNEK_SORULAR.md) (her uygulama için kopyala-yapıştır mesajlar)

```
lab1_monolith/           Lab 1: tek ajan, 7 araç
lab2_router/             Lab 2-3: 5 TODO'lu yönlendirici
lab2_router_solution/    Lab 2 çözümü (Lab 3 buradan da sürdürülebilir)
lab2_tech_only/          İsteğe bağlı: teknik uzman tek başına
demo_guarded/            Demo: yetki, guardrail, arıza yönetimi, ölçüm
demo_a2a/                Demo: tech_agent ayrı A2A sunucusunda (deneysel)
evals/                   Lab 3: 30 vakalık set, holdout seti, eval betiği
shared/                  Sahte arka uç, callback'ler, ortak kurucu
tests/test_offline.py    Model gerektirmeyen provalar
```

Kurulum: `./setup.sh && source .venv/bin/activate && python check_setup.py`
