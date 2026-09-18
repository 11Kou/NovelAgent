from app.retrieval.assembler import PromptAssembler
from app.schemas.memory import MemoryDraft
from app.schemas.story import ChapterEventDraft
from app.storage.models import Chapter
from app.workflows.chapter_confirmation_graph import build_chapter_confirmation_graph
from app.workflows.chapter_generation_graph import build_chapter_generation_graph


class Obj:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class FakeStaticRetriever:
    def retrieve(self, story_id):
        return {
            "story": Obj(title="失忆之城", premise="寻找身份", worldview="记忆交易", style="悬疑"),
            "characters": [],
            "locations": [],
            "items": [],
            "world_rules": [],
            "taboos": [Obj(content="不要让主角无理由获得真相")],
        }


class FakeDynamicRetriever:
    def retrieve(self, story_id, entity_ids=None):
        return {
            "latest_states": [],
            "recent_history": [],
            "chapter_summaries": [],
            "rolling_summary": None,
            "last_chapter_ending": "",
        }


class FakeVectorRetriever:
    def retrieve(self, *, story_id, query, top_k):
        return ["第一章中，林夏发现墙上的旧标记。"]


class FakeWritingAgent:
    def write_chapter(self, assembled_prompt, rewrite_note=""):
        return f"正文：{rewrite_note or '默认'}\n{assembled_prompt[:20]}"


class FakeDynamicStore:
    def save_chapter(self, **kwargs):
        return Chapter(
            id=7,
            story_id=kwargs["story_id"],
            chapter_index=kwargs["chapter_index"],
            title=kwargs["title"],
            event_description=kwargs["event_description"],
            content=kwargs["content"],
        )


class FakeMemoryService:
    def extract_and_save(self, **kwargs):
        return MemoryDraft(
            chapter_id=kwargs["chapter_id"],
            state_changes=[],
            chapter_summary="林夏发现旧标记。",
        )


def test_chapter_generation_graph_invokes_pipeline() -> None:
    graph = build_chapter_generation_graph(
        static_retriever=FakeStaticRetriever(),
        dynamic_retriever=FakeDynamicRetriever(),
        vector_retriever=FakeVectorRetriever(),
        assembler=PromptAssembler(token_budget=1000),
        writing_agent=FakeWritingAgent(),
    )

    event = ChapterEventDraft(
        chapter_index=1,
        event_description="林夏发现旧标记。",
        involved_entities=["char_linxia"],
    )
    result = graph.invoke(
        {
            "story_id": 1,
            "chapter_event": event,
            "rewrite_note": "更悬疑",
        }
    )

    assert "【强约束区】" in result["assembled_prompt"]
    assert "不要让主角无理由获得真相" in result["assembled_prompt"]
    assert result["content"].startswith("正文：更悬疑")
    assert result["workflow_trace"] == [
        "retrieve_static_context",
        "retrieve_dynamic_context",
        "retrieve_vector_context",
        "assemble_prompt",
        "write_chapter",
    ]


def test_chapter_confirmation_graph_saves_chapter_then_memory() -> None:
    graph = build_chapter_confirmation_graph(
        dynamic_store=FakeDynamicStore(),
        memory_service=FakeMemoryService(),
    )
    event = ChapterEventDraft(chapter_index=2, title="追踪", event_description="林夏被追踪。")

    result = graph.invoke(
        {
            "story_id": 1,
            "chapter_event": event,
            "content": "章节正文",
        }
    )

    assert result["chapter"].id == 7
    assert result["memory"].chapter_id == 7
    assert result["memory"].chapter_summary == "林夏发现旧标记。"
    assert result["workflow_trace"] == ["save_chapter", "extract_and_save_memory"]
