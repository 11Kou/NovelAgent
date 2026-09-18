from sqlmodel import Session

from app.config.settings import Settings
from app.retrieval.assembler import PromptAssembler
from app.retrieval.dynamic_retriever import DynamicRetriever
from app.retrieval.static_retriever import StaticRetriever
from app.retrieval.vector_retriever import VectorRetriever
from app.schemas.story import (
    ChapterConfirmRequest,
    ChapterConfirmResponse,
    ChapterDraftRequest,
    ChapterDraftResponse,
)
from app.services.memory_service import MemoryService
from app.storage.dynamic_store import DynamicStore
from app.storage.vector_store import VectorStore
from app.services.model_clients import EmbeddingClient
from app.workflows.chapter_confirmation_graph import build_chapter_confirmation_graph
from app.workflows.chapter_generation_graph import build_chapter_generation_graph


class StoryGraphRunner:
    def __init__(
        self,
        *,
        session: Session,
        settings: Settings,
        dynamic_store: DynamicStore,
        memory_service: MemoryService,
        embedding_client: EmbeddingClient,
        vector_store: VectorStore,
        writing_agent,
    ):
        self.session = session
        self.settings = settings
        self.dynamic_store = dynamic_store
        self.memory_service = memory_service
        self.embedding_client = embedding_client
        self.vector_store = vector_store
        self.writing_agent = writing_agent

    def draft_chapter(self, story_id: int, request: ChapterDraftRequest) -> ChapterDraftResponse:
        graph = build_chapter_generation_graph(
            static_retriever=StaticRetriever(self.session),
            dynamic_retriever=DynamicRetriever(self.session, self.settings),
            vector_retriever=VectorRetriever(self.embedding_client, self.vector_store),
            assembler=PromptAssembler(self.settings.prompt_token_budget),
            writing_agent=self.writing_agent,
        )
        state = graph.invoke(
            {
                "story_id": story_id,
                "chapter_event": request.chapter_event,
                "rewrite_note": request.rewrite_note,
            }
        )
        return ChapterDraftResponse(
            chapter_event=request.chapter_event,
            assembled_prompt=state["assembled_prompt"],
            content=state["content"],
            workflow_trace=state.get("workflow_trace", []),
        )

    def confirm_chapter(self, story_id: int, request: ChapterConfirmRequest) -> ChapterConfirmResponse:
        graph = build_chapter_confirmation_graph(
            dynamic_store=self.dynamic_store,
            memory_service=self.memory_service,
        )
        state = graph.invoke(
            {
                "story_id": story_id,
                "chapter_event": request.chapter_event,
                "content": request.content,
            }
        )
        chapter = state["chapter"]
        return ChapterConfirmResponse(
            chapter_id=chapter.id,
            chapter_index=chapter.chapter_index,
            memory=state["memory"],
            workflow_trace=state.get("workflow_trace", []),
        )
