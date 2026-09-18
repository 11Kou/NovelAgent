from pydantic import BaseModel, Field


class CharacterData(BaseModel):
    entity_id: str | None = None
    name: str
    identity: str = ""
    personality: str = ""
    goal: str = ""
    background: str = ""


class LocationData(BaseModel):
    entity_id: str | None = None
    name: str
    description: str = ""


class ItemData(BaseModel):
    entity_id: str | None = None
    name: str
    description: str = ""


class OutlineNodeData(BaseModel):
    title: str
    required_events: str = ""
    status: str = "pending"
    order_index: int = 0


class StorySettingsDraft(BaseModel):
    title: str
    premise: str
    worldview: str = ""
    style: str = ""
    characters: list[CharacterData] = Field(default_factory=list)
    locations: list[LocationData] = Field(default_factory=list)
    items: list[ItemData] = Field(default_factory=list)
    world_rules: list[str] = Field(default_factory=list)
    taboos: list[str] = Field(default_factory=list)
    outline: list[OutlineNodeData] = Field(default_factory=list)


class StoryIdeaRequest(BaseModel):
    idea: str


class StoryCreateRequest(BaseModel):
    settings: StorySettingsDraft


class StoryCreateResponse(BaseModel):
    story_id: int
    settings: StorySettingsDraft


class ChapterEventDraft(BaseModel):
    chapter_index: int
    title: str = ""
    event_description: str
    involved_entities: list[str] = Field(default_factory=list)


class ChapterEventRequest(BaseModel):
    chapter_index: int | None = None
    user_note: str = ""


class ChapterDraftRequest(BaseModel):
    chapter_event: ChapterEventDraft
    rewrite_note: str = ""


class ChapterDraftResponse(BaseModel):
    chapter_event: ChapterEventDraft
    assembled_prompt: str
    content: str


class ChapterConfirmRequest(BaseModel):
    chapter_event: ChapterEventDraft
    content: str


class ChapterConfirmResponse(BaseModel):
    chapter_id: int
    chapter_index: int
    memory: "MemoryDraft"


from app.schemas.memory import MemoryDraft  # noqa: E402

ChapterConfirmResponse.model_rebuild()

