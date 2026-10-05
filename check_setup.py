#!/usr/bin/env python
"""Kurulum kontrolu: kimlik dogrulama + model adi + 1 kucuk cagri (yaklasik $0.0001)."""
import os
import sys
import time

from shared import config  # noqa: F401  (.env yuklenir)

if os.getenv("USE_FAKE_MODEL") == "1":
    print("USE_FAKE_MODEL=1 -> sahte model aktif, gercek cagri yapilmayacak. Tamam.")
    sys.exit(0)

from google import genai  # noqa: E402

mode = "Vertex AI" if os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").upper() in ("TRUE", "1") else "AI Studio anahtari"
print(f"Kimlik modu : {mode}")
print(f"Proje/konum : {os.getenv('GOOGLE_CLOUD_PROJECT', '-')} / {os.getenv('GOOGLE_CLOUD_LOCATION', '-')}")
print(f"Model       : {config.MODEL}")
try:
    client = genai.Client()
    t0 = time.time()
    r = client.models.generate_content(model=config.MODEL, contents="Reply with the single word: OK")
    u = r.usage_metadata
    print(f"Yanit       : {r.text.strip()!r} ({time.time() - t0:.1f}s, "
          f"{u.prompt_token_count} giris / {u.candidates_token_count} cikis token)")
    print("TAMAM: ortam hazir.")
except Exception as e:  # noqa: BLE001
    print(f"\nHATA: {type(e).__name__}: {str(e)[:400]}\n")
    print("Sik nedenler:\n"
          " - 404/NOT_FOUND: model adi bu konumda yok. .env'de GOOGLE_CLOUD_LOCATION=global deneyin\n"
          "   veya MODEL=... degerini degistirin.\n"
          " - 403/PERMISSION: 'gcloud services enable aiplatform.googleapis.com' calistirin, kredinin\n"
          "   projeye bagli oldugunu kontrol edin.\n"
          " - Kredi gecikmesi: yedek olarak AI Studio anahtarini .env'ye GOOGLE_API_KEY olarak koyun.")
    sys.exit(1)
