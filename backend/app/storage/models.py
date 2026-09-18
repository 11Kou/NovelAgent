from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Story(SQLModel, table=True):
    __tablename__ = "stories"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    premise: str
    style: str = ""
    worldview: str = ""
    created_at: datetime = Field(default_factory=utc_now)


class Character(SQLModel, table=True):
    __tablename__ = "characters"

    id: Optional[int] = Field(default=None, primary_key=True)
    story_id: int = Field(index=True, foreign_key="stories.id")
    entity_id: str = Field(index=True)
    name: str
    identity: str = ""
    personality: str = ""
    goal: str = ""
    background: str = ""


class Location(SQLModel, table=True):
    __tablename__ = "locations"

    id: Optional[int] = Field(default=None, primary_key=True)
    story_id: int = Field(index=True, foreign_key="stories.id")
    entity_id: str = Field(index=True)
    name: str
    description: str = ""


class Item(SQLModel, table=True):
    __tablename__ = "items"

    id: Optional[int] = Field(default=None, primary_key=True)
    story_id: int = Field(index=True, foreign_key="stories.id")
    entity_id: str = Field(index=True)
    name: str
    description: str = ""


class WorldRule(SQLModel, table=True):
    __tablename__ = "world_rules"

    id: Optional[int] = Field(default=None, primary_key=True)
    story_id: int = Field(index=True, foreign_key="stories.id")
    content: str


class Taboo(SQLModel, table=True):
    __tablename__ = "taboos"

    id: Optional[int] = Field(default=None, primary_key=True)
    story_id: int = Field(index=True, foreign_key="stories.id")
    content: str


class OutlineNode(SQLModel, table=True):
    __tablename__ = "outline_nodes"

    id: Optional[int] = Field(default=None, primary_key=True)
    story_id: int = Field(index=True, foreign_key="stories.id")
    title: str
    required_events: str = ""
    status: str = "pending"
    order_index: int = Field(default=0, index=True)


class Chapter(SQLModel, table=True):
    __tablename__ = "chapters"
    __table_args__ = (UniqueConstraint("story_id", "chapter_index", name="uq_chapter_story_index"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    story_id: int = Field(index=True, foreign_key="stories.id")
    chapter_index: int = Field(index=True)
    title: str = ""
    event_description: str
    content: str
    status: str = "confirmed"
    created_at: datetime = Field(default_factory=utc_now)


class EntityLatestState(SQLModel, table=True):
    __tablename__ = "entity_latest_states"
    __table_args__ = (
        UniqueConstraint("story_id", "entity_id", "state_type", name="uq_latest_state_entity_type"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    story_id: int = Field(index=True, foreign_key="stories.id")
    entity_id: str = Field(index=True)
    entity_type: str = Field(index=True)
    state_type: str = Field(index=True)
    state_value: str
    chapter_id: int = Field(index=True, foreign_key="chapters.id")
    updated_at: datetime = Field(default_factory=utc_now)


class StateHistory(SQLModel, table=True):
    __tablename__ = "state_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    story_id: int = Field(index=True, foreign_key="stories.id")
    chapter_id: int = Field(index=True, foreign_key="chapters.id")
    entity_id: str = Field(index=True)
    entity_type: str = Field(index=True)
    state_type: str = Field(index=True)
    old_value: str = ""
    new_value: str
    description: str
    created_at: datetime = Field(default_factory=utc_now)


class StateDescription(SQLModel, table=True):
    __tablename__ = "state_descriptions"
    __table_args__ = (UniqueConstraint("state_history_id", name="uq_state_description_history"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    story_id: int = Field(index=True, foreign_key="stories.id")
    chapter_id: int = Field(index=True, foreign_key="chapters.id")
    state_history_id: int = Field(index=True, foreign_key="state_history.id")
    entity_id: str = Field(index=True)
    entity_type: str = Field(index=True)
    text: str
    embedding_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=utc_now)


class ChapterSummary(SQLModel, table=True):
    __tablename__ = "chapter_summaries"
    __table_args__ = (UniqueConstraint("chapter_id", name="uq_chapter_summary_chapter"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    story_id: int = Field(index=True, foreign_key="stories.id")
    chapter_id: int = Field(index=True, foreign_key="chapters.id")
    summary: str


class RollingSummary(SQLModel, table=True):
    __tablename__ = "rolling_summaries"

    id: Optional[int] = Field(default=None, primary_key=True)
    story_id: int = Field(index=True, foreign_key="stories.id")
    summary: str
    updated_chapter_id: int = Field(index=True, foreign_key="chapters.id")
    updated_at: datetime = Field(default_factory=utc_now)

