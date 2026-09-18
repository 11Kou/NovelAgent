from datetime import datetime

from pydantic import BaseModel, Field


class StateChange(BaseModel):
    entity_id: str
    entity_type: str
    state_type: str
    old_value: str = ""
    new_value: str
    description: str


class MemoryDraft(BaseModel):
    chapter_id: int | None = None
    state_changes: list[StateChange] = Field(default_factory=list)
    chapter_summary: str
    rolling_summary: str | None = None


class LatestStateView(BaseModel):
    id: int
    entity_id: str
    entity_type: str
    state_type: str
    state_value: str
    chapter_id: int
    updated_at: datetime


class StateHistoryView(BaseModel):
    id: int
    chapter_id: int
    entity_id: str
    entity_type: str
    state_type: str
    old_value: str
    new_value: str
    description: str
    created_at: datetime


class ChapterSummaryView(BaseModel):
    chapter_id: int
    chapter_index: int
    summary: str


class MemoryView(BaseModel):
    latest_states: list[LatestStateView]
    state_history: list[StateHistoryView]
    chapter_summaries: list[ChapterSummaryView]
    rolling_summary: str = ""


class StateCorrectionRequest(BaseModel):
    entity_id: str
    entity_type: str
    state_type: str
    state_value: str
    note: str = "用户手动修正"
