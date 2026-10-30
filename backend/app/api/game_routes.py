from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.config.settings import Settings, get_settings
from app.schemas.game import (
    CharacterCard, GameAction, GameCreate, GameListItem, GameSettingsUpdate, GameView,
    SavedCharacterCard, SavedWorldBook, WorldBook, WorldBookImport,
)
from app.services.library_service import LibraryService, import_character
from app.services.game_service import GameConflict, GameNotFound, GameService
from app.services.model_clients import ModelClientError
from app.services.worldbook import import_worldbook
from app.storage.db import get_session


router = APIRouter(prefix="/api")


def get_game_service(
    session: Session = Depends(get_session), settings: Settings = Depends(get_settings),
) -> GameService:
    return GameService(session, settings)


def get_library_service(session: Session = Depends(get_session)) -> LibraryService:
    return LibraryService(session)


def call_game(fn):
    try:
        return fn()
    except GameNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except GameConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ModelClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/worldbooks/import", response_model=WorldBook)
def parse_worldbook(request: WorldBookImport):
    return call_game(lambda: import_worldbook(request.content, request.filename))


@router.get("/games", response_model=list[GameListItem])
def list_games(service: GameService = Depends(get_game_service)):
    return service.list_games()


@router.post("/games", response_model=GameView)
def create_game(request: GameCreate, service: GameService = Depends(get_game_service)):
    return call_game(lambda: service.create_game(request))


@router.get("/games/{game_id}", response_model=GameView)
def get_game(game_id: int, service: GameService = Depends(get_game_service)):
    return call_game(lambda: service.get_game(game_id))


@router.post("/games/{game_id}/actions", response_model=GameView)
def act(game_id: int, request: GameAction, service: GameService = Depends(get_game_service)):
    return call_game(lambda: service.act(game_id, request))


@router.put("/games/{game_id}/settings", response_model=GameView)
def update_settings(game_id: int, request: GameSettingsUpdate, service: GameService = Depends(get_game_service)):
    return call_game(lambda: service.update_settings(game_id, request))


@router.get("/library/worldbooks", response_model=list[SavedWorldBook])
def list_books(service: LibraryService = Depends(get_library_service)):
    return service.list_books()


@router.post("/library/worldbooks", response_model=SavedWorldBook)
def save_book(request: WorldBook, service: LibraryService = Depends(get_library_service)):
    return call_game(lambda: service.save_book(request))


@router.put("/library/worldbooks/{book_id}", response_model=SavedWorldBook)
def update_book(book_id: int, request: WorldBook, service: LibraryService = Depends(get_library_service)):
    return call_game(lambda: service.save_book(request, book_id))


@router.post("/characters/import", response_model=CharacterCard)
def parse_character(request: WorldBookImport):
    return call_game(lambda: import_character(request.content, request.filename))


@router.get("/library/characters", response_model=list[SavedCharacterCard])
def list_cards(service: LibraryService = Depends(get_library_service)):
    return service.list_cards()


@router.post("/library/characters", response_model=SavedCharacterCard)
def save_card(request: CharacterCard, service: LibraryService = Depends(get_library_service)):
    return call_game(lambda: service.save_card(request))


@router.put("/library/characters/{card_id}", response_model=SavedCharacterCard)
def update_card(card_id: int, request: CharacterCard, service: LibraryService = Depends(get_library_service)):
    return call_game(lambda: service.save_card(request, card_id))
