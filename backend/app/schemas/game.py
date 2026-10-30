from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class LoreEntry(BaseModel):
    title: str = Field(default="设定", max_length=200)
    content: str = Field(min_length=1, max_length=24000)
    keys: list[str] = Field(default_factory=list, max_length=100)
    constant: bool = True
    enabled: bool = True


class WorldBook(BaseModel):
    name: str = Field(default="未命名世界", max_length=120)
    entries: list[LoreEntry] = Field(min_length=1, max_length=500)

    @field_validator("entries")
    @classmethod
    def limit_content(cls, entries):
        if sum(len(entry.content) for entry in entries) > 100000:
            raise ValueError("世界书正文总长度不能超过 100000 字符。")
        if not any(entry.enabled for entry in entries):
            raise ValueError("世界书至少需要一个启用的条目。")
        return entries


class WorldBookImport(BaseModel):
    content: str = Field(min_length=1, max_length=500000)
    filename: str = Field(default="世界书", max_length=255)


class CharacterCard(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=12000)
    personality: str = Field(default="", max_length=4000)
    background: str = Field(default="", max_length=6000)
    goal: str = Field(default="", max_length=2000)
    scenario: str = Field(default="", max_length=4000)
    first_mes: str = Field(default="", max_length=4000)
    mes_example: str = Field(default="", max_length=4000)
    worldbook: WorldBook | None = None

    @field_validator("name")
    @classmethod
    def reject_blank_name(cls, value):
        if not value.strip():
            raise ValueError("角色姓名不能为空。")
        return value.strip()


class StoryCharacter(BaseModel):
    card: CharacterCard
    role: Literal["player", "npc"] = "npc"
    enabled: bool = True


def validate_characters(characters):
    if sum(character.enabled and character.role == "player" for character in characters) > 1:
        raise ValueError("一份存档只能启用一张玩家人设卡。")
    if sum(len(character.model_dump_json()) for character in characters) > 50000:
        raise ValueError("角色设定总量过大，请精简角色卡。")
    return characters


class GameCreate(BaseModel):
    request_id: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=120)
    worldbook: WorldBook
    persona: str = Field(min_length=1, max_length=3000)
    opening: str = Field(default="", max_length=3000)
    style: str = Field(default="沉浸式小说，第二人称，细腻但不拖沓", max_length=1000)
    characters: list[StoryCharacter] = Field(default_factory=list, max_length=20)

    _validate_characters = field_validator("characters")(validate_characters)

    @field_validator("title", "persona")
    @classmethod
    def reject_blank(cls, value):
        if not value.strip():
            raise ValueError("内容不能为空。")
        return value.strip()


class GameAction(BaseModel):
    request_id: str = Field(min_length=1, max_length=80)
    expected_version: int = Field(ge=1)
    expected_settings_revision: int = Field(default=0, ge=0)
    action: str = Field(min_length=1, max_length=3000)

    @field_validator("action")
    @classmethod
    def reject_blank(cls, value):
        if not value.strip():
            raise ValueError("请填写行动。")
        return value.strip()


class GameFact(BaseModel):
    label: str = Field(min_length=1, max_length=100)
    value: str = Field(min_length=1, max_length=500)


class SceneDraft(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=12000)
    choices: list[str] = Field(min_length=2, max_length=4)
    state: list[GameFact] = Field(default_factory=list, max_length=24)
    summary: str = Field(min_length=1, max_length=5000)

    @field_validator("choices")
    @classmethod
    def validate_choices(cls, choices):
        if any(not choice.strip() or len(choice) > 300 for choice in choices):
            raise ValueError("选项不能为空或超过 300 字符。")
        return choices


class TurnView(BaseModel):
    turn_index: int
    action: str
    title: str
    content: str
    choices: list[str]


class GameListItem(BaseModel):
    id: int
    title: str
    world_name: str
    persona: str
    version: int
    updated_at: datetime


class GameView(GameListItem):
    worldbook: WorldBook
    state: list[GameFact]
    summary: str
    turns: list[TurnView]
    characters: list[StoryCharacter] = Field(default_factory=list)
    settings_revision: int = 0
    style: str = ""


class GameSettingsUpdate(BaseModel):
    expected_version: int = Field(ge=1)
    expected_settings_revision: int = Field(ge=0)
    worldbook: WorldBook
    persona: str = Field(min_length=1, max_length=3000)
    style: str = Field(default="", max_length=1000)
    characters: list[StoryCharacter] = Field(default_factory=list, max_length=20)

    _validate_characters = field_validator("characters")(validate_characters)

    @field_validator("persona")
    @classmethod
    def reject_blank_persona(cls, value):
        if not value.strip():
            raise ValueError("玩家身份不能为空。")
        return value.strip()


class SavedWorldBook(BaseModel):
    id: int
    book: WorldBook
    updated_at: datetime


class SavedCharacterCard(BaseModel):
    id: int
    card: CharacterCard
    updated_at: datetime
