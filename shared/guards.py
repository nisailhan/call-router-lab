"""Uretim onlemleri (Demo 1 ve Demo 2). ADK callback'leri olarak yazildi.

Callback imzalari (ADK 2.x):
  before_model_callback(ctx, llm_request)        -> None | LlmResponse
  after_model_callback(ctx, llm_response)        -> None | LlmResponse
  before_tool_callback(tool, args, ctx)          -> None | dict   (dict donerse arac CALISMAZ)
  on_tool_error_callback(tool, args, ctx, error) -> None | dict
None dondurmek "dokunma, devam et" demektir.
"""
import re
import time

from shared.config import estimate_cost

REFUND_LIMIT = 100.0  # TRY. Bunun ustu insan onayi ister.
PROTECTED_TOOLS = {"get_invoice", "issue_refund", "run_line_diagnostics",
                   "reset_modem", "cancel_subscription"}


# ---------- 1) ERISIM KONTROLU: arac cagrisindan ONCE ----------
def require_verified(tool, args, ctx):
    """Kimligi dogrulanmamis musteri adina hesap araci calistirma.
    Bu kural prompt'ta degil KODDA durur: model ikna edilse bile asilamaz."""
    if tool.name in PROTECTED_TOOLS:
        if ctx.state.get("verified_customer") != args.get("customer_id"):
            return {
                "status": "denied",
                "error": "Customer is not verified. Ask for the customer id and PIN, "
                         "call verify_customer, then retry.",
            }
    if tool.name == "issue_refund" and float(args.get("amount", 0)) > REFUND_LIMIT:
        return {
            "status": "needs_human_approval",
            "error": f"Refunds above {REFUND_LIMIT:.0f} TRY need a human. "
                     "Call handoff_to_human with queue 'escalation'.",
        }
    return None


# ---------- 2) CIKTI GUARDRAIL'I: model cevabindan SONRA ----------
_PATTERNS = [
    (re.compile(r"\b(?:\d[ -]?){13,19}\b"), "[CARD REDACTED]"),
    (re.compile(r"\b\d{11}\b"), "[ID REDACTED]"),
    (re.compile(r"(?i)\bpin\b\D{0,12}\d{4}\b"), "PIN [REDACTED]"),
]


def mask_pii(ctx, llm_response):
    """Kart, kimlik no ve PIN'i musteriye giden metinden maskeler."""
    content = llm_response.content
    if not content or not content.parts:
        return None
    changed = False
    for part in content.parts:
        if part.text:
            new = part.text
            for pattern, repl in _PATTERNS:
                new = pattern.sub(repl, new)
            if new != part.text:
                part.text = new
                changed = True
    return llm_response if changed else None


# ---------- 3) MALIYET VE GECIKME: her model cagrisini olc ----------
def start_timer(ctx, llm_request):
    ctx.state["temp:t0"] = time.time()
    ctx.state["llm_calls"] = ctx.state.get("llm_calls", 0) + 1
    return None


def log_usage(ctx, llm_response):
    um = llm_response.usage_metadata
    t_in = (um.prompt_token_count or 0) if um else 0
    t_out = (um.candidates_token_count or 0) if um else 0
    ctx.state["tokens_in"] = ctx.state.get("tokens_in", 0) + t_in
    ctx.state["tokens_out"] = ctx.state.get("tokens_out", 0) + t_out
    dt = time.time() - ctx.state.get("temp:t0", time.time())
    total = estimate_cost(ctx.state["tokens_in"], ctx.state["tokens_out"])
    print(f"[usage] agent={getattr(ctx, 'agent_name', '?')} call#{ctx.state.get('llm_calls')} "
          f"in={t_in} out={t_out} {dt:.2f}s | session total ~${total:.5f}")
    return None


# ---------- 4) YARIDA KIRILAN KOSU: arac hatasini kontrollu yonet ----------
def tool_error_fallback(tool, args, ctx, error):
    """Arac patlarsa kosu cokmesin; model insana devretsin. Hata yine trace'te gorunur."""
    return {
        "status": "error",
        "error_type": type(error).__name__,
        "message": str(error),
        "instruction": "The system is temporarily unavailable. Apologise in one sentence "
                       "and call handoff_to_human with queue 'general'.",
    }
