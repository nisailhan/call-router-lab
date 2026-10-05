"""Ortak ayarlar. Tum labs buradan model adini alir."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
# Zaten tanimli ortam degiskenlerini ezmez (ornegin: MODEL=... python evals/...)
load_dotenv(ROOT / ".env")

MODEL = os.getenv("MODEL", "gemini-3.5-flash-lite")
PRICE_IN_PER_M = float(os.getenv("PRICE_IN_PER_M", "0.30"))
PRICE_OUT_PER_M = float(os.getenv("PRICE_OUT_PER_M", "2.50"))


def get_model():
    """Model adini (str) dondurur. USE_FAKE_MODEL=1 ise kredi harcamayan sahte model."""
    if os.getenv("USE_FAKE_MODEL", "0") == "1":
        from shared.fake_model import FakeRouterModel

        return FakeRouterModel(model="fake-router")
    return MODEL


def estimate_cost(tokens_in: int, tokens_out: int) -> float:
    return tokens_in / 1e6 * PRICE_IN_PER_M + tokens_out / 1e6 * PRICE_OUT_PER_M
