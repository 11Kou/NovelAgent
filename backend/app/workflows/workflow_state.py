from typing import Any, TypedDict

from app.schemas.memory import MemoryDraft
from app.schemas.story import ChapterEventDraft
from app.storage.models import Chapter


class ChapterGenerationState(TypedDict, total=False):
    story_id: int
    chapter_event: ChapterEventDraft
    rewrite_note: str
    entity_ids: list[str]
    static_context: dict[str, Any]
    dynamic_context: dict[str, Any]
    related_history: list[str]
    assembled_prompt: str
    content: str
    workflow_trace: list[str]


class ChapterConfirmationState(TypedDict, total=False):
    story_id: int
    chapter_event: ChapterEventDraft
    content: str
    chapter: Chapter
    memory: MemoryDraft
    workflow_trace: list[str]
