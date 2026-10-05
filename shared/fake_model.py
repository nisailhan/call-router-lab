"""Kredi harcamayan SAHTE model. Egitmen provasi ve yerel testler icin.

Gercek bir LLM degildir: anahtar kelimeye bakip yonlendirir. Amaci, kodun (yonlendirme,
callback'ler, eval betigi) model olmadan da calistigini dogrulamaktir. USE_FAKE_MODEL=1 ile acilir.
"""
from typing import AsyncGenerator

from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types

_HUMAN = ("real person", "sue ", "passed away", "yetkili", "manager", "human")
_CANCEL = ("cancel", "terminate", "leaving", "close my account", "iptal", "i'm done")
_TECH = ("internet", "modem", "wifi", "wi-fi", "speed", "router", "mobile data", "çalışmıyor")
_BILL = ("bill", "invoice", "charged", "fee", "payment", "fatura", "borç", "overcharged")


def _decide(text: str):
    t = text.lower()
    if any(k in t for k in _HUMAN):
        return "human"
    if any(k in t for k in _CANCEL):
        return "cancel_agent"
    if any(k in t for k in _BILL):
        return "billing_agent"
    if any(k in t for k in _TECH):
        return "tech_agent"
    return None


def _user_text(llm_request: LlmRequest) -> str:
    for content in reversed(llm_request.contents or []):
        if content.role == "user":
            texts = [p.text for p in (content.parts or []) if p.text]
            if texts:
                return " ".join(texts)
    return ""


class FakeRouterModel(BaseLlm):
    model: str = "fake-router"

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        usage = types.GenerateContentResponseUsageMetadata(
            prompt_token_count=120, candidates_token_count=15, total_token_count=135)
        last = llm_request.contents[-1] if llm_request.contents else None
        got_tool_result = bool(last and any(p.function_response for p in (last.parts or [])))
        tools = getattr(llm_request, "tools_dict", {}) or {}

        system = str(getattr(llm_request.config, "system_instruction", "") or "")
        is_specialist = "specialist of Nimbus" in system  # uzmanlar yonlendirme yapmaz

        part = types.Part(text="(fake) Done.")
        if not got_tool_result and not is_specialist and "transfer_to_agent" in tools:
            choice = _decide(_user_text(llm_request))
            if choice == "human":
                part = types.Part(function_call=types.FunctionCall(
                    name="handoff_to_human",
                    args={"reason": "customer asked for a person", "queue": "escalation"}))
            elif choice:
                part = types.Part(function_call=types.FunctionCall(
                    name="transfer_to_agent", args={"agent_name": choice}))
            else:
                part = types.Part(text="(fake) Could you tell me a bit more about the problem?")
        yield LlmResponse(content=types.Content(role="model", parts=[part]),
                          usage_metadata=usage)
