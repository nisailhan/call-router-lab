#!/usr/bin/env bash
# Cloud Shell icin tek komutluk kurulum:  ./setup.sh
set -e
cd "$(dirname "$0")"

python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  if command -v gcloud >/dev/null 2>&1; then
    PROJECT="$(gcloud config get-value project 2>/dev/null || true)"
    if [ -n "$PROJECT" ] && [ "$PROJECT" != "(unset)" ]; then
      sed -i "s/your-project-id/${PROJECT}/" .env
      echo "Proje: ${PROJECT}"
      gcloud services enable aiplatform.googleapis.com --quiet || true
    fi
  fi
fi

echo
echo "Kurulum bitti. Siradaki komutlar:"
echo "  source .venv/bin/activate"
echo "  python check_setup.py"
