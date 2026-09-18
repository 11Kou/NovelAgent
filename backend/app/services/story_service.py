from sqlmodel import Session

from app.agents.memory_agent import MemoryAgent
from app.agents.planning_agent import PlanningAgent
from app.agents.writing_agent import WritingAgent
from app.config.settings import Settings
from app.schemas.memory import MemoryView, StateCorrectionRequest
from app.schemas.story import (
    ChapterConfirmRequest,
    ChapterConfirmResponse,
    ChapterDraftRequest,
    ChapterDraftResponse,
    ChapterEventDraft,
    ChapterEventRequest,
    StoryCreateResponse,
    StorySettingsDraft,
)
from app.services.memory_service import MemoryService
from app.services.model_clients import EmbeddingClient, LLMClient
from app.storage.dynamic_store import DynamicStore
from app.storage.static_store import StaticStore
from app.storage.vector_store import VectorStore
from app.workflows.graph_runner import StoryGraphRunner


class StoryService:
    def __init__(
        self,
        session: Session,
        settings: Settings,
        *,
        llm_client: LLMClient | None = None,
        embedding_client: EmbeddingClient | None = None,
        vector_store: VectorStore | None = None,
    ):
        self.session = session
        self.settings = settings
        llm = llm_client or LLMClient(settings)
        embedding = embedding_client or EmbeddingClient(settings)
        vector_store = vector_store or VectorStore(settings)
        self.planning_agent = PlanningAgent(llm)
        self.writing_agent = WritingAgent(llm)
        self.memory_agent = MemoryAgent(llm)
        self.embedding_client = embedding
        self.vector_store = vector_store
        self.static_store = StaticStore(session)
        self.dynamic_store = DynamicStore(session)
        self.memory_service = MemoryService(
            session=session,
            settings=settings,
            memory_agent=self.memory_agent,
            embedding_client=embedding,
            vector_store=vector_store,
        )
        self.graph_runner = StoryGraphRunner(
            session=session,
            settings=settings,
            dynamic_store=self.dynamic_store,
            memory_service=self.memory_service,
            embedding_client=embedding,
            vector_store=vector_store,
            writing_agent=self.writing_agent,
        )

    def draft_settings(self, idea: str) -> StorySettingsDraft:
        return self.planning_agent.draft_settings(idea)

    def confirm_story_settings(self, settings: StorySettingsDraft) -> StoryCreateResponse:
        story = self.static_store.create_story(settings)
        return StoryCreateResponse(story_id=story.id, settings=self.static_store.export_settings(story.id))

    def draft_chapter_event(self, story_id: int, request: ChapterEventRequest) -> ChapterEventDraft:
        chapter_index = request.chapter_index or self.dynamic_store.next_chapter_index(story_id)
        context = self._planning_context(story_id)
        event = self.planning_agent.draft_chapter_event(
            chapter_index=chapter_index,
            story_context=context,
            user_note=request.user_note,
        )
        event.chapter_index = chapter_index
        return event

    def draft_chapter(self, story_id: int, request: ChapterDraftRequest) -> ChapterDraftResponse:
        return self.graph_runner.draft_chapter(story_id, request)

    def confirm_chapter(self, story_id: int, request: ChapterConfirmRequest) -> ChapterConfirmResponse:
        return self.graph_runner.confirm_chapter(story_id, request)

    def view_memory(self, story_id: int) -> MemoryView:
        return self.memory_service.view_memory(story_id)

    def correct_memory(self, story_id: int, request: StateCorrectionRequest) -> MemoryView:
        return self.memory_service.correct_state(story_id, request)

    def _planning_context(self, story_id: int) -> str:
        settings = self.static_store.export_settings(story_id)
        memory = self.memory_service.view_memory(story_id)
        latest = "\n".join(
            f"- {state.entity_id}.{state.state_type}: {state.state_value}"
            for state in memory.latest_states
        )
        return (
            f"标题：{settings.title}\n"
            f"前提：{settings.premise}\n"
            f"世界观：{settings.worldview}\n"
            f"风格：{settings.style}\n"
            f"最新状态：\n{latest or '无'}"
        )
