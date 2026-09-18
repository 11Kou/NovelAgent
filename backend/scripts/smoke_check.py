from __future__ import annotations

import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.config.settings import get_settings  # noqa: E402
from app.main import app  # noqa: E402
from app.services.model_clients import EmbeddingClient, LLMClient, ModelClientError  # noqa: E402
from app.storage.db import create_db_and_tables  # noqa: E402


def main() -> int:
    settings = get_settings()
    warnings: list[str] = []
    failures: list[str] = []

    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        print("[ok] .env exists")
    else:
        warnings.append(".env is missing. Copy .env.example to .env before real DeepSeek calls.")

    print(f"[ok] FastAPI app imports: {app.title}")

    try:
        create_db_and_tables()
        print("[ok] SQLite tables are ready")
    except Exception as exc:  # noqa: BLE001 - smoke check should report setup failures.
        failures.append(f"SQLite setup failed: {exc}")

    print(f"[ok] generation model: {settings.deepseek_model}")
    print(f"[ok] embedding model: {settings.ollama_embedding_model}")
    print(f"[ok] ollama host: {settings.ollama_host}")

    if settings.deepseek_api_key:
        print("[ok] DEEPSEEK_API_KEY is configured")
    else:
        warnings.append("DEEPSEEK_API_KEY is not configured. Generation endpoints will return a clear 502 error.")
        try:
            LLMClient(settings).generate_text([{"role": "user", "content": "hello"}])
            failures.append("DeepSeek missing-key guard did not trigger.")
        except ModelClientError as exc:
            if "DEEPSEEK_API_KEY is not configured" in str(exc):
                print("[ok] DeepSeek missing-key guard returns a clear error")
            else:
                failures.append(f"Unexpected DeepSeek missing-key error: {exc}")

    try:
        embedding = EmbeddingClient(settings).embed("NovelAgent smoke check")
        print(f"[ok] Ollama embedding succeeded, dimension={len(embedding)}")
    except ModelClientError as exc:
        failures.append(str(exc))

    for warning in warnings:
        print(f"[warn] {warning}")

    if failures:
        for failure in failures:
            print(f"[fail] {failure}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

