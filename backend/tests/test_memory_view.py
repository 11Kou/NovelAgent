from sqlmodel import Session, SQLModel, create_engine

from app.schemas.memory import MemoryDraft
from app.services.memory_service import MemoryService
from app.storage.dynamic_store import DynamicStore
from app.storage.models import Story


class FakeMemoryAgent:
    pass


class FakeEmbeddingClient:
    pass


class FakeVectorStore:
    pass


class Settings:
    pass


def test_memory_view_uses_chapter_index_for_summaries() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        story = Story(title="测试", premise="测试")
        session.add(story)
        session.commit()
        session.refresh(story)

        store = DynamicStore(session)
        chapter = store.save_chapter(
            story_id=story.id,
            chapter_index=1,
            title="第一章",
            event_description="事件",
            content="正文",
        )
        store.save_chapter(
            story_id=story.id,
            chapter_index=2,
            title="第二章",
            event_description="事件",
            content="正文",
        )
        store.save_chapter_summary(
            story_id=story.id,
            chapter_id=chapter.id,
            summary="第一章摘要",
        )

        service = MemoryService(
            session=session,
            settings=Settings(),
            memory_agent=FakeMemoryAgent(),
            embedding_client=FakeEmbeddingClient(),
            vector_store=FakeVectorStore(),
        )
        memory = service.view_memory(story.id)

        assert memory.chapter_summaries[0].chapter_id == chapter.id
        assert memory.chapter_summaries[0].chapter_index == 1
        assert memory.chapter_summaries[0].summary == "第一章摘要"
