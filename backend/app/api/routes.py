from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.config.settings import Settings, get_settings
from app.schemas.memory import MemoryView, StateCorrectionRequest
from app.schemas.story import (
    ChapterConfirmRequest,
    ChapterConfirmResponse,
    ChapterDraftRequest,
    ChapterDraftResponse,
    ChapterEventDraft,
    ChapterEventRequest,
    StoryCreateRequest,
    StoryCreateResponse,
    StoryIdeaRequest,
    StorySettingsDraft,
)
from app.services.model_clients import ModelClientError
from app.services.story_service import StoryService
from app.storage.db import get_session


router = APIRouter(prefix="/api")


def get_story_service(
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> StoryService:
    return StoryService(session, settings)


@router.post("/stories/draft-settings", response_model=StorySettingsDraft)
def draft_story_settings(
    request: StoryIdeaRequest,
    service: StoryService = Depends(get_story_service),
) -> StorySettingsDraft:
    return _call_model(lambda: service.draft_settings(request.idea))


@router.post("/stories", response_model=StoryCreateResponse)
def create_story(
    request: StoryCreateRequest,
    service: StoryService = Depends(get_story_service),
) -> StoryCreateResponse:
    return service.confirm_story_settings(request.settings)


@router.post("/stories/{story_id}/chapter-events/draft", response_model=ChapterEventDraft)
def draft_chapter_event(
    story_id: int,
    request: ChapterEventRequest,
    service: StoryService = Depends(get_story_service),
) -> ChapterEventDraft:
    return _call_model(lambda: service.draft_chapter_event(story_id, request))


@router.post("/stories/{story_id}/chapters/draft", response_model=ChapterDraftResponse)
def draft_chapter(
    story_id: int,
    request: ChapterDraftRequest,
    service: StoryService = Depends(get_story_service),
) -> ChapterDraftResponse:
    return _call_model(lambda: service.draft_chapter(story_id, request))


@router.post("/stories/{story_id}/chapters", response_model=ChapterConfirmResponse)
def confirm_chapter(
    story_id: int,
    request: ChapterConfirmRequest,
    service: StoryService = Depends(get_story_service),
) -> ChapterConfirmResponse:
    return _call_model(lambda: service.confirm_chapter(story_id, request))


@router.get("/stories/{story_id}/memory", response_model=MemoryView)
def view_memory(
    story_id: int,
    service: StoryService = Depends(get_story_service),
) -> MemoryView:
    return service.view_memory(story_id)


@router.patch("/stories/{story_id}/memory/latest-state", response_model=MemoryView)
def correct_memory(
    story_id: int,
    request: StateCorrectionRequest,
    service: StoryService = Depends(get_story_service),
) -> MemoryView:
    return service.correct_memory(story_id, request)


def _call_model(fn):
    try:
        return fn()
    except ModelClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

