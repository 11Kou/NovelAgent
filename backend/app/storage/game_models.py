from datetime import datetime
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

from app.storage.models import utc_now


class GameSession(SQLModel, table=True):
    __tablename__ = "game_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    request_id: str = Field(unique=True)
    title: str
    world_name: str
    worldbook_json: str
    persona: str
    opening: str = ""
    style: str = ""
    version: int = 1
    summary: str = ""
    state_json: str = "[]"
    updated_at: datetime = Field(default_factory=utc_now)


class GameTurn(SQLModel, table=True):
    __tablename__ = "game_turns"
    __table_args__ = (
        UniqueConstraint("game_id", "turn_index", name="uq_game_turn_index"),
        UniqueConstraint("game_id", "request_id", name="uq_game_turn_request"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    game_id: int = Field(index=True, foreign_key="game_sessions.id")
    request_id: str
    turn_index: int
    action: str
    title: str
    content: str
    choices_json: str


class GameConfiguration(SQLModel, table=True):
    __tablename__ = "game_configurations"

    game_id: int = Field(primary_key=True, foreign_key="game_sessions.id")
    revision: int = 0
    characters_json: str = "[]"


class LibraryWorldBook(SQLModel, table=True):
    __tablename__ = "library_worldbooks"

    id: Optional[int] = Field(default=None, primary_key=True)
    content_json: str
    updated_at: datetime = Field(default_factory=utc_now)


class LibraryCharacterCard(SQLModel, table=True):
    __tablename__ = "library_character_cards"

    id: Optional[int] = Field(default=None, primary_key=True)
    content_json: str
    updated_at: datetime = Field(default_factory=utc_now)
