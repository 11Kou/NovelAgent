from collections.abc import Generator
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.api.routes import get_story_service
from app.config.settings import Settings
from app.main import app
from app.schemas.memory import MemoryDraft, StateChange
from app.schemas.story import ChapterEventDraft, StorySettingsDraft
from app.services.story_service import StoryService


class FakeLLMClient:
    def generate_json(self, messages: list[dict[str, str]], schema, **kwargs):
        if schema is StorySettingsDraft:
            return StorySettingsDraft(
                title="测试故事",
                premise="失忆少女寻找身份。",
                worldview="记忆可以交易。",
                style="悬疑",
                characters=[
                    {
                        "entity_id": "char_linxia",
                        "name": "林夏",
                        "identity": "失忆少女",
                    }
                ],
                locations=[
                    {
                        "entity_id": "loc_station",
                        "name": "废弃地铁站",
                        "description": "故事开端地点。",
                    }
                ],
                world_rules=["记忆交易必须留下痕迹。"],
                taboos=["不要让主角无理由获得真相。"],
            )
        if schema is ChapterEventDraft:
            return ChapterEventDraft(
                chapter_index=1,
                title="醒来",
                event_description="林夏在废弃地铁站醒来，并发现掌心的银色编号。",
                involved_entities=["char_linxia", "loc_station"],
            )
        if schema is MemoryDraft:
            return MemoryDraft(
                chapter_id=0,
                state_changes=[
                    StateChange(
                        entity_id="char_linxia",
                        entity_type="character",
                        state_type="location",
                        old_value="未知",
                        new_value="废弃地铁站",
                        description="第一章中，林夏在废弃地铁站醒来。",
                    )
                ],
                chapter_summary="林夏在废弃地铁站醒来，发现掌心的银色编号。",
            )
        raise AssertionError(f"Unexpected schema: {schema}")

    def generate_text(self, messages: list[dict[str, str]], **kwargs) -> str:
        user_message = messages[-1]["content"]
        return "林夏在废弃地铁站醒来，掌心的银色编号正在发热。\n" + user_message[:80]


class FakeEmbeddingClient:
    def embed(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]


class FakeVectorStore:
    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []

    def add_state_description(
        self,
        *,
        embedding_id: str,
        text: str,
        embedding: list[float],
        metadata: dict,
    ) -> None:
        self.documents.append(
            {
                "embedding_id": embedding_id,
                "text": text,
                "embedding": embedding,
                "metadata": metadata,
            }
        )

    def query(self, *, embedding: list[float], story_id: int, top_k: int = 5) -> list[str]:
        return [
            item["text"]
            for item in self.documents
            if item["metadata"].get("story_id") == story_id
        ][:top_k]


def test_api_story_to_memory_flow_without_external_models() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    vector_store = FakeVectorStore()

    def override_story_service() -> Generator[StoryService, None, None]:
        with Session(engine) as session:
            yield StoryService(
                session,
                Settings(model_max_retries=0),
                llm_client=FakeLLMClient(),
                embedding_client=FakeEmbeddingClient(),
                vector_store=vector_store,
            )

    app.dependency_overrides[get_story_service] = override_story_service
    try:
        client = TestClient(app)

        settings_response = client.post(
            "/api/stories/draft-settings",
            json={"idea": "写一个未来城市悬疑故事。"},
        )
        assert settings_response.status_code == 200
        settings_payload = settings_response.json()
        assert settings_payload["title"] == "测试故事"
        assert settings_payload["taboos"] == ["不要让主角无理由获得真相。"]

        story_response = client.post("/api/stories", json={"settings": settings_payload})
        assert story_response.status_code == 200
        story_id = story_response.json()["story_id"]

        event_response = client.post(
            f"/api/stories/{story_id}/chapter-events/draft",
            json={"user_note": "开场紧凑。"},
        )
        assert event_response.status_code == 200
        chapter_event = event_response.json()
        assert chapter_event["chapter_index"] == 1

        draft_response = client.post(
            f"/api/stories/{story_id}/chapters/draft",
            json={"chapter_event": chapter_event, "rewrite_note": "少一点对白。"},
        )
        assert draft_response.status_code == 200
        chapter_draft = draft_response.json()
        assert chapter_draft["workflow_trace"] == [
            "retrieve_static_context",
            "retrieve_dynamic_context",
            "retrieve_vector_context",
            "assemble_prompt",
            "write_chapter",
        ]
        assert "林夏在废弃地铁站醒来" in chapter_draft["content"]
        assert "【强约束区】" in chapter_draft["assembled_prompt"]

        confirm_response = client.post(
            f"/api/stories/{story_id}/chapters",
            json={
                "chapter_event": chapter_event,
                "content": chapter_draft["content"],
            },
        )
        assert confirm_response.status_code == 200
        confirmed = confirm_response.json()
        assert confirmed["chapter_index"] == 1
        assert confirmed["memory"]["chapter_id"] == confirmed["chapter_id"]
        assert confirmed["workflow_trace"] == ["save_chapter", "extract_and_save_memory"]

        memory_response = client.get(f"/api/stories/{story_id}/memory")
        assert memory_response.status_code == 200
        memory = memory_response.json()
        assert memory["latest_states"][0]["state_value"] == "废弃地铁站"
        assert memory["chapter_summaries"][0]["chapter_index"] == 1
        assert memory["state_history"][0]["description"] == "第一章中，林夏在废弃地铁站醒来。"

        assert vector_store.documents == [
            {
                "embedding_id": "state-history-1",
                "text": "第一章中，林夏在废弃地铁站醒来。",
                "embedding": [0.1, 0.2, 0.3],
                "metadata": {
                    "story_id": story_id,
                    "chapter_id": confirmed["chapter_id"],
                    "state_history_id": 1,
                    "entity_id": "char_linxia",
                    "entity_type": "character",
                    "state_type": "location",
                },
            }
        ]
    finally:
        app.dependency_overrides.clear()
