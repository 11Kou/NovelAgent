from sqlmodel import Session

from app.agents.memory_agent import MemoryAgent
from app.agents.planning_agent import PlanningAgent
from app.agents.writing_agent import WritingAgent
from app.config.settings import Settings
from app.retrieval.assembler import PromptAssembler
from app.retrieval.dynamic_retriever import DynamicRetriever
from app.retrieval.static_retriever import StaticRetriever
from app.retrieval.vector_retriever import VectorRetriever
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


class StoryService:
    def __init__(self, session: Session, settings: Settings):
        self.session = session
        self.settings = settings
        llm = LLMClient(settings)
        embedding = EmbeddingClient(settings)
        vector_store = VectorStore(settings)
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
        static_context = StaticRetriever(self.session).retrieve(story_id)
        entity_ids = request.chapter_event.involved_entities
        dynamic_context = DynamicRetriever(self.session, self.settings).retrieve(story_id, entity_ids)
        related_history = VectorRetriever(self.embedding_client, self.vector_store).retrieve(
            story_id=story_id,
            query=request.chapter_event.event_description,
            top_k=5,
        )
        prompt = PromptAssembler(self.settings.prompt_token_budget).assemble(
            static_context=static_context,
            dynamic_context=dynamic_context,
            related_history=related_history,
            chapter_event=request.chapter_event,
        )
        content = self.writing_agent.write_chapter(prompt, request.rewrite_note)
        return ChapterDraftResponse(
            chapter_event=request.chapter_event,
            assembled_prompt=prompt,
            content=content,
        )

    def confirm_chapter(self, story_id: int, request: ChapterConfirmRequest) -> ChapterConfirmResponse:
        chapter = self.dynamic_store.save_chapter(
            story_id=story_id,
            chapter_index=request.chapter_event.chapter_index,
            title=request.chapter_event.title,
            event_description=request.chapter_event.event_description,
            content=request.content,
        )
        memory = self.memory_service.extract_and_save(
            story_id=story_id,
            chapter_id=chapter.id,
            chapter_index=chapter.chapter_index,
            chapter_event=chapter.event_description,
            chapter_content=chapter.content,
        )
        return ChapterConfirmResponse(
            chapter_id=chapter.id,
            chapter_index=chapter.chapter_index,
            memory=memory,
        )

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

