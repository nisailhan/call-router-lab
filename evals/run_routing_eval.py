#!/usr/bin/env python
"""Yonlendirme dogrulugunu olcer. LLM hakem YOK: beklenen etiket ile yapilan secim karsilastirilir.

Kullanim (repo kokunden):
  python evals/run_routing_eval.py --agent lab2_router
  python evals/run_routing_eval.py --agent lab2_router --tag v2          # sonuc dosyasina etiket
  python evals/run_routing_eval.py --agent lab2_router --cases evals/routing_holdout.jsonl
  python evals/run_routing_eval.py --agent lab2_router --repeat 3        # kararlilik (varyans) icin
  MODEL=gemini-3.1-flash-lite python evals/run_routing_eval.py --agent lab2_router   # model degisimi

Her kosu evals/results/ altina kaydedilir; bir sonraki kosu otomatik olarak bir oncekiyle karsilastirilir.
Yonlendirme karari verilir verilmez kosu DURDURULUR (uzman model cagrisi yapilmaz): ucuz ve hizli.
"""
import argparse
import asyncio
import importlib
import json
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from google.adk.runners import Runner  # noqa: E402
from google.adk.sessions import InMemorySessionService  # noqa: E402
from google.genai import types  # noqa: E402

from shared import config  # noqa: E402  (.env yuklenir)

APP = "routing_eval"
RESULTS = ROOT / "evals" / "results"


async def route_one(agent, text: str):
    """Tek mesaji ajana ver, ILK yonlendirme kararini dondur."""
    svc = InMemorySessionService()
    runner = Runner(agent=agent, app_name=APP, session_service=svc)
    session = await svc.create_session(app_name=APP, user_id="eval")
    msg = types.Content(role="user", parts=[types.Part(text=text)])
    t0, t_in, t_out, predicted = time.time(), 0, 0, None
    gen = runner.run_async(user_id="eval", session_id=session.id, new_message=msg)
    try:
        async for ev in gen:
            um = ev.usage_metadata
            if um:
                t_in += um.prompt_token_count or 0
                t_out += um.candidates_token_count or 0
            for fc in ev.get_function_calls():
                if fc.name == "transfer_to_agent":
                    predicted = str((fc.args or {}).get("agent_name", "?")).removesuffix("_agent")
                elif fc.name == "handoff_to_human":
                    predicted = "human"
            if predicted:
                break
    finally:
        await gen.aclose()
    # Ne transfer ne insan devri: yonlendirici kendisi cevap verdi (netlestirme sorusu)
    return (predicted or "clarify"), t_in, t_out, time.time() - t0


async def run_all(agent, cases, repeat, concurrency):
    sem = asyncio.Semaphore(concurrency)
    out = []

    async def one(case, rep):
        async with sem:
            try:
                pred, t_in, t_out, dt = await route_one(agent, case["text"])
                err = None
            except Exception as e:  # noqa: BLE001
                pred, t_in, t_out, dt, err = f"error:{type(e).__name__}", 0, 0, 0.0, str(e)[:200]
            out.append({"id": case["id"], "rep": rep, "pred": pred, "t_in": t_in,
                        "t_out": t_out, "latency": dt, "error": err})

    await asyncio.gather(*[one(c, r) for c in cases for r in range(repeat)])
    return out


def load_cases(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()
            if line.strip()]


def summarize(cases, runs):
    by_id = defaultdict(list)
    for r in runs:
        by_id[r["id"]].append(r)
    per_case = {}
    for c in cases:
        preds = [r["pred"] for r in by_id[c["id"]]]
        rate = sum(p == c["expected"] for p in preds) / len(preds)
        per_case[c["id"]] = {"expected": c["expected"], "kind": c["kind"], "text": c["text"],
                             "preds": preds, "correct_rate": rate}
    return per_case


def latest_previous(agent_name, cases_name):
    if not RESULTS.exists():
        return None
    files = sorted(RESULTS.glob(f"{agent_name}__{cases_name}__*.json"))
    return json.loads(files[-1].read_text()) if files else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True, help="klasor adi, ornek: lab2_router")
    ap.add_argument("--cases", default=str(ROOT / "evals" / "routing_cases.jsonl"))
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--tag", default="")
    ap.add_argument("--no-compare", action="store_true")
    args = ap.parse_args()

    agent = importlib.import_module(f"{args.agent}.agent").root_agent
    if not agent.sub_agents:
        sys.exit("HATA: yonlendiricinin sub_agents listesi bos. Lab 2'deki TODO'lari doldurdunuz mu?")
    cases = load_cases(args.cases)
    cases_name = Path(args.cases).stem
    model_name = config.MODEL if config.get_model() == config.MODEL else "fake-router"

    print(f"Agent: {args.agent} | Model: {model_name} | Cases: {len(cases)} x {args.repeat}")
    t0 = time.time()
    runs = asyncio.run(run_all(agent, cases, args.repeat, args.concurrency))
    wall = time.time() - t0
    per_case = summarize(cases, runs)

    total = len(runs)
    correct = sum(round(v["correct_rate"] * len(v["preds"])) for v in per_case.values())
    accuracy = correct / total
    errors = [r for r in runs if r["error"]]
    lat = [r["latency"] for r in runs if not r["error"]] or [0.0]
    t_in, t_out = sum(r["t_in"] for r in runs), sum(r["t_out"] for r in runs)
    cost = config.estimate_cost(t_in, t_out)

    print(f"\nDogruluk: {correct}/{total} = {accuracy:.1%}")
    for label, key in (("Tur (kind)", "kind"), ("Beklenen", "expected")):
        groups = defaultdict(lambda: [0, 0])
        for v in per_case.values():
            groups[v[key]][0] += round(v["correct_rate"] * len(v["preds"]))
            groups[v[key]][1] += len(v["preds"])
        print(f"{label}: " + " | ".join(f"{k} {a}/{b}" for k, (a, b) in sorted(groups.items())))

    wrong = [(i, v) for i, v in per_case.items() if v["correct_rate"] < 1]
    if wrong:
        print("\nHatalar:")
        for i, v in wrong:
            seen = Counter(v["preds"]).most_common()
            guess = ", ".join(f"{p}x{n}" for p, n in seen)
            print(f"  {i:4} beklenen={v['expected']:8} verilen={guess:18} | {v['text'][:60]}")
    unstable = [i for i, v in per_case.items() if len(set(v["preds"])) > 1]
    if args.repeat > 1:
        print(f"\nKararsiz vakalar (ayni mesaj, farkli sonuc): {unstable or 'yok'}")
    if errors:
        print(f"\n{len(errors)} kosu hata verdi. Ilk hata: {errors[0]['error']}")

    print(f"\nGecikme: ort {statistics.mean(lat):.2f}s | p95 {sorted(lat)[int(len(lat) * .95) - 1]:.2f}s "
          f"| toplam sure {wall:.1f}s")
    print(f"Token: girdi {t_in} / cikti {t_out} | tahmini maliyet ${cost:.4f} "
          f"(kosu basina ${cost / total:.5f})")

    result = {"agent": args.agent, "model": model_name, "cases": cases_name,
              "ts": datetime.now().isoformat(timespec="seconds"), "tag": args.tag,
              "repeat": args.repeat, "accuracy": accuracy, "latency_avg": statistics.mean(lat),
              "tokens_in": t_in, "tokens_out": t_out, "cost_usd": cost, "per_case": per_case}

    if not args.no_compare:
        prev = latest_previous(args.agent, cases_name)
        if prev:
            ok = lambda d, i: d["per_case"][i]["correct_rate"] >= 0.5  # noqa: E731
            ids = [i for i in per_case if i in prev["per_case"]]
            fixed = [i for i in ids if not ok(prev, i) and ok(result, i)]
            broken = [i for i in ids if ok(prev, i) and not ok(result, i)]
            print(f"\nOnceki kosuya gore ({prev['ts']}, model {prev['model']}, etiket '{prev['tag']}'):")
            print(f"  dogruluk {prev['accuracy']:.1%} -> {accuracy:.1%} "
                  f"({(accuracy - prev['accuracy']) * 100:+.1f} puan)")
            print(f"  DUZELEN: {fixed or '-'}   BOZULAN: {broken or '-'}")
            if prev["model"] != model_name:
                print(f"  DIKKAT: model degisti: {prev['model']} -> {model_name}")
        else:
            print("\n(Karsilastirilacak onceki kosu yok: bu kosu taban cizgisi olarak kaydedildi.)")

    RESULTS.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    name = f"{args.agent}__{cases_name}__{stamp}{('_' + args.tag) if args.tag else ''}.json"
    (RESULTS / name).write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nKaydedildi: evals/results/{name}")


if __name__ == "__main__":
    main()
