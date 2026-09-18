from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.config.settings import get_settings  # noqa: E402


def main() -> int:
    settings = get_settings()
    tags_url = f"{settings.ollama_host.rstrip('/')}/api/tags"

    try:
        with urlopen(tags_url, timeout=settings.model_timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except URLError as exc:
        print(f"[fail] Cannot reach Ollama at {settings.ollama_host}: {exc}")
        print("[hint] Start the Ollama desktop app or run `ollama serve`, then retry.")
        return 1
    except TimeoutError:
        print(f"[fail] Timed out while connecting to Ollama at {settings.ollama_host}.")
        return 1

    names = sorted(item.get("name", "") for item in payload.get("models", []) if item.get("name"))
    if not names:
        print("[fail] Ollama is reachable, but no local models were returned.")
        print("[hint] Pull bge-m3 in Ollama, then set OLLAMA_EMBEDDING_MODEL in .env.")
        return 1

    print("[ok] Ollama is reachable")
    print("[ok] Local Ollama models:")
    for name in names:
        print(f"  - {name}")

    configured = settings.ollama_embedding_model
    aliases = {configured, f"{configured}:latest"}
    if configured.endswith(":latest"):
        aliases.add(configured.removesuffix(":latest"))

    if aliases.intersection(names):
        print(f"[ok] Configured embedding model is available: {configured}")
        return 0

    print(f"[fail] Configured embedding model was not found: {configured}")
    print("[hint] Update OLLAMA_EMBEDDING_MODEL in .env to one of the names above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
