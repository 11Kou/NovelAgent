from sqlmodel import Session

from app.agents.memory_agent import MemoryAgent
from app.config.settings import Settings
from app.schemas.memory import MemoryDraft, MemoryView, StateCorrectionRequest
from app.services.model_clients import EmbeddingClient
from app.storage.dynamic_store import DynamicStore
from app.storage.vector_store import VectorStore


class MemoryService:
    def __init__(
        self,
        *,
        session: Session,
        settings: Settings,
        memory_agent: MemoryAgent,
        embedding_client: EmbeddingClient,
        vector_store: VectorStore,
    ):
        self.session = session
        self.settings = settings
        self.memory_agent = memory_agent
        self.embedding_client = embedding_client
        self.vector_store = vector_store
        self.dynamic_store = DynamicStore(session)

    def extract_and_save(
        self,
        *,
        story_id: int,
        chapter_id: int,
        chapter_index: int,
        chapter_event: str,
        chapter_content: str,
    ) -> MemoryDraft:
        draft = self.memory_agent.extract_memory(
            chapter_id=chapter_id,
            chapter_index=chapter_index,
            chapter_event=chapter_event,
            chapter_content=chapter_content,
        )
        self.save_memory(story_id=story_id, chapter_id=chapter_id, chapter_index=chapter_index, draft=draft)
        return draft

    def save_memory(
        self,
        *,
        story_id: int,
        chapter_id: int,
        chapter_index: int,
        draft: MemoryDraft,
    ) -> None:
        for change in draft.state_changes:
            history = self.dynamic_store.save_state_change(
                story_id=story_id,
                chapter_id=chapter_id,
                change=change,
            )
            embedding_id = f"state-history-{history.id}"
            embedding = self.embedding_client.embed(change.description)
            self.vector_store.add_state_description(
                embedding_id=embedding_id,
                text=change.description,
                embedding=embedding,
                metadata={
                    "story_id": story_id,
                    "chapter_id": chapter_id,
                    "state_history_id": history.id,
                    "entity_id": change.entity_id,
                    "entity_type": change.entity_type,
                    "state_type": change.state_type,
                },
            )
            self.dynamic_store.save_state_description(
                story_id=story_id,
                chapter_id=chapter_id,
                history_id=history.id,
                entity_id=change.entity_id,
                entity_type=change.entity_type,
                text=change.description,
                embedding_id=embedding_id,
            )

        self.dynamic_store.save_chapter_summary(
            story_id=story_id,
            chapter_id=chapter_id,
            summary=draft.chapter_summary,
        )

        if chapter_index % self.settings.rolling_summary_interval == 0:
            previous = self.dynamic_store.latest_rolling_summary(story_id)
            recent = self.dynamic_store.chapter_summaries(
                story_id,
                limit=self.settings.rolling_summary_interval,
            )
            rolling = self.memory_agent.update_rolling_summary(
                previous.summary if previous else "",
                [item.summary for item in reversed(recent)],
            )
            self.dynamic_store.save_rolling_summary(
                story_id=story_id,
                chapter_id=chapter_id,
                summary=rolling,
            )
            draft.rolling_summary = rolling

    def view_memory(self, story_id: int) -> MemoryView:
        rolling = self.dynamic_store.latest_rolling_summary(story_id)
        return MemoryView(
            latest_states=[item.model_dump() for item in self.dynamic_store.latest_states(story_id)],
            state_history=[item.model_dump() for item in self.dynamic_store.recent_history(story_id, limit=100)],
            chapter_summaries=[
                {"chapter_id": item.chapter_id, "summary": item.summary}
                for item in self.dynamic_store.chapter_summaries(story_id, limit=100)
            ],
            rolling_summary=rolling.summary if rolling else "",
        )

    def correct_state(self, story_id: int, request: StateCorrectionRequest) -> MemoryView:
        self.dynamic_store.correct_latest_state(
            story_id=story_id,
            entity_id=request.entity_id,
            entity_type=request.entity_type,
            state_type=request.state_type,
            state_value=request.state_value,
            note=request.note,
        )
        return self.view_memory(story_id)

