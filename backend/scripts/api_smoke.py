from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.config.settings import get_settings  # noqa: E402
from app.main import app  # noqa: E402
from app.storage.db import create_db_and_tables  # noqa: E402


def post(client: TestClient, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = client.post(path, json=payload)
    if response.status_code >= 400:
        raise RuntimeError(f"POST {path} failed: {response.status_code} {response.text}")
    return response.json()


def main() -> int:
    settings = get_settings()
    if not settings.deepseek_api_key:
        print("[skip] DEEPSEEK_API_KEY is not configured. Fill .env before running API smoke.")
        return 0

    create_db_and_tables()
    client = TestClient(app)

    idea = "写一个未来城市里，失忆少女寻找真实身份的悬疑故事。请保持设定简洁，便于 smoke test。"
    settings_draft = post(client, "/api/stories/draft-settings", {"idea": idea})
    print(f"[ok] drafted settings: {settings_draft.get('title', '<untitled>')}")

    created = post(client, "/api/stories", {"settings": settings_draft})
    story_id = created["story_id"]
    print(f"[ok] created story: {story_id}")

    chapter_event = post(
        client,
        f"/api/stories/{story_id}/chapter-events/draft",
        {"user_note": "第一章只写一个紧凑开端。"},
    )
    print(f"[ok] drafted chapter event: chapter {chapter_event['chapter_index']}")

    chapter_draft = post(
        client,
        f"/api/stories/{story_id}/chapters/draft",
        {
            "chapter_event": chapter_event,
            "rewrite_note": "控制篇幅，适合接口 smoke test。",
        },
    )
    generation_trace = chapter_draft.get("workflow_trace", [])
    if generation_trace != [
        "retrieve_static_context",
        "retrieve_dynamic_context",
        "retrieve_vector_context",
        "assemble_prompt",
        "write_chapter",
    ]:
        raise RuntimeError(f"Unexpected generation workflow trace: {generation_trace}")
    print(f"[ok] drafted chapter through LangGraph: {' -> '.join(generation_trace)}")

    confirmed = post(
        client,
        f"/api/stories/{story_id}/chapters",
        {
            "chapter_event": chapter_event,
            "content": chapter_draft["content"],
        },
    )
    confirmation_trace = confirmed.get("workflow_trace", [])
    if confirmation_trace != ["save_chapter", "extract_and_save_memory"]:
        raise RuntimeError(f"Unexpected confirmation workflow trace: {confirmation_trace}")
    print(f"[ok] confirmed chapter through LangGraph: {' -> '.join(confirmation_trace)}")

    memory = client.get(f"/api/stories/{story_id}/memory")
    if memory.status_code >= 400:
        raise RuntimeError(f"GET memory failed: {memory.status_code} {memory.text}")
    memory_json = memory.json()
    print(f"[ok] latest states: {len(memory_json.get('latest_states', []))}")
    print(f"[ok] chapter summaries: {len(memory_json.get('chapter_summaries', []))}")
    print("[ok] API smoke completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

