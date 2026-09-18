from sqlmodel import Session, SQLModel, create_engine, select

from app.schemas.memory import MemoryDraft
from app.services.memory_service import MemoryService
from app.storage.dynamic_store import DynamicStore
from app.storage.models import RollingSummary, Story


class FakeMemoryAgent:
    def update_rolling_summary(self, previous_summary: str, recent_summaries: list[str]) -> str:
        prefix = f"{previous_summary}\n" if previous_summary else ""
        return prefix + " / ".join(recent_summaries)


class FakeEmbeddingClient:
    def embed(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]


class FakeVectorStore:
    def add_state_description(self, **kwargs) -> None:
        pass


class Settings:
    rolling_summary_interval = 5


def test_rolling_summary_updates_every_configured_interval() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        story = Story(title="测试", premise="测试")
        session.add(story)
        session.commit()
        session.refresh(story)

        store = DynamicStore(session)
        service = MemoryService(
            session=session,
            settings=Settings(),
            memory_agent=FakeMemoryAgent(),
            embedding_client=FakeEmbeddingClient(),
            vector_store=FakeVectorStore(),
        )

        for chapter_index in range(1, 11):
            chapter = store.save_chapter(
                story_id=story.id,
                chapter_index=chapter_index,
                title=f"第{chapter_index}章",
                event_description="事件",
                content="正文",
            )
            service.save_memory(
                story_id=story.id,
                chapter_id=chapter.id,
                chapter_index=chapter_index,
                draft=MemoryDraft(
                    chapter_id=chapter.id,
                    state_changes=[],
                    chapter_summary=f"摘要{chapter_index}",
                ),
            )

        rows = session.exec(select(RollingSummary).order_by(RollingSummary.updated_chapter_id)).all()

        assert len(rows) == 2
        assert rows[0].updated_chapter_id == 5
        assert rows[0].summary == "摘要1 / 摘要2 / 摘要3 / 摘要4 / 摘要5"
        assert rows[1].updated_chapter_id == 10
        assert rows[1].summary.endswith("摘要6 / 摘要7 / 摘要8 / 摘要9 / 摘要10")
