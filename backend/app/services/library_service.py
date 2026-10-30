import json
from pathlib import Path

from sqlmodel import Session, select

from app.schemas.game import CharacterCard, SavedCharacterCard, SavedWorldBook, WorldBook
from app.services.game_service import GameNotFound
from app.services.worldbook import import_worldbook
from app.storage.game_models import LibraryCharacterCard, LibraryWorldBook
from app.storage.models import utc_now


def import_character(content: str, filename: str) -> CharacterCard:
    text = content.lstrip("\ufeff").strip()
    if not text:
        raise ValueError("人设卡内容不能为空。")
    if not filename.lower().endswith(".json") and not text.startswith("{"):
        return CharacterCard(name=Path(filename).stem[:120] or "未命名角色", description=text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("人设卡 JSON 格式不正确。") from exc
    if isinstance(data, dict) and "data" in data:
        data = data["data"]
    if not isinstance(data, dict):
        raise ValueError("人设卡必须是 JSON 对象。")
    fields = {field: data[field] for field in CharacterCard.model_fields if field in data}
    if data.get("character_book"):
        fields["worldbook"] = import_worldbook(json.dumps(data["character_book"], ensure_ascii=False), filename)
    return CharacterCard.model_validate(fields)


class LibraryService:
    def __init__(self, session: Session):
        self.session = session

    def list_books(self):
        return [self._book_view(row) for row in self.session.exec(
            select(LibraryWorldBook).order_by(LibraryWorldBook.updated_at.desc())
        ).all()]

    def save_book(self, book: WorldBook, book_id: int | None = None):
        row = self.session.get(LibraryWorldBook, book_id) if book_id is not None else LibraryWorldBook(content_json="")
        if row is None:
            raise GameNotFound("找不到这本世界书。")
        row.content_json = book.model_dump_json()
        row.updated_at = utc_now()
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return self._book_view(row)

    def list_cards(self):
        return [self._card_view(row) for row in self.session.exec(
            select(LibraryCharacterCard).order_by(LibraryCharacterCard.updated_at.desc())
        ).all()]

    def save_card(self, card: CharacterCard, card_id: int | None = None):
        row = self.session.get(LibraryCharacterCard, card_id) if card_id is not None else LibraryCharacterCard(content_json="")
        if row is None:
            raise GameNotFound("找不到这张人设卡。")
        row.content_json = card.model_dump_json()
        row.updated_at = utc_now()
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return self._card_view(row)

    @staticmethod
    def _book_view(row):
        return SavedWorldBook(id=row.id, book=WorldBook.model_validate_json(row.content_json), updated_at=row.updated_at)

    @staticmethod
    def _card_view(row):
        return SavedCharacterCard(id=row.id, card=CharacterCard.model_validate_json(row.content_json), updated_at=row.updated_at)
