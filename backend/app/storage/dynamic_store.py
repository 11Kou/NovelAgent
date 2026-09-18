from sqlmodel import Session, select

from app.schemas.memory import StateChange
from app.storage.models import (
    Chapter,
    ChapterSummary,
    EntityLatestState,
    RollingSummary,
    StateDescription,
    StateHistory,
    utc_now,
)


class DynamicStore:
    def __init__(self, session: Session):
        self.session = session

    def next_chapter_index(self, story_id: int) -> int:
        chapter = self.session.exec(
            select(Chapter)
            .where(Chapter.story_id == story_id)
            .order_by(Chapter.chapter_index.desc())
        ).first()
        return 1 if chapter is None else chapter.chapter_index + 1

    def save_chapter(
        self,
        *,
        story_id: int,
        chapter_index: int,
        title: str,
        event_description: str,
        content: str,
    ) -> Chapter:
        chapter = Chapter(
            story_id=story_id,
            chapter_index=chapter_index,
            title=title,
            event_description=event_description,
            content=content,
        )
        self.session.add(chapter)
        self.session.commit()
        self.session.refresh(chapter)
        return chapter

    def save_state_change(
        self,
        *,
        story_id: int,
        chapter_id: int,
        change: StateChange,
    ) -> StateHistory:
        latest = self.session.exec(
            select(EntityLatestState).where(
                EntityLatestState.story_id == story_id,
                EntityLatestState.entity_id == change.entity_id,
                EntityLatestState.state_type == change.state_type,
            )
        ).first()
        old_value = latest.state_value if latest else change.old_value
        history = StateHistory(
            story_id=story_id,
            chapter_id=chapter_id,
            entity_id=change.entity_id,
            entity_type=change.entity_type,
            state_type=change.state_type,
            old_value=old_value,
            new_value=change.new_value,
            description=change.description,
        )
        self.session.add(history)
        self.session.commit()
        self.session.refresh(history)

        if latest is None:
            latest = EntityLatestState(
                story_id=story_id,
                entity_id=change.entity_id,
                entity_type=change.entity_type,
                state_type=change.state_type,
                state_value=change.new_value,
                chapter_id=chapter_id,
            )
        else:
            latest.entity_type = change.entity_type
            latest.state_value = change.new_value
            latest.chapter_id = chapter_id
            latest.updated_at = utc_now()
        self.session.add(latest)
        self.session.commit()
        return history

    def save_state_description(
        self,
        *,
        story_id: int,
        chapter_id: int,
        history_id: int,
        entity_id: str,
        entity_type: str,
        text: str,
        embedding_id: str,
    ) -> StateDescription:
        description = StateDescription(
            story_id=story_id,
            chapter_id=chapter_id,
            state_history_id=history_id,
            entity_id=entity_id,
            entity_type=entity_type,
            text=text,
            embedding_id=embedding_id,
        )
        self.session.add(description)
        self.session.commit()
        self.session.refresh(description)
        return description

    def save_chapter_summary(self, *, story_id: int, chapter_id: int, summary: str) -> ChapterSummary:
        chapter_summary = ChapterSummary(story_id=story_id, chapter_id=chapter_id, summary=summary)
        self.session.add(chapter_summary)
        self.session.commit()
        self.session.refresh(chapter_summary)
        return chapter_summary

    def save_rolling_summary(self, *, story_id: int, chapter_id: int, summary: str) -> RollingSummary:
        rolling = RollingSummary(story_id=story_id, updated_chapter_id=chapter_id, summary=summary)
        self.session.add(rolling)
        self.session.commit()
        self.session.refresh(rolling)
        return rolling

    def latest_states(self, story_id: int, entity_ids: list[str] | None = None) -> list[EntityLatestState]:
        query = select(EntityLatestState).where(EntityLatestState.story_id == story_id)
        if entity_ids:
            query = query.where(EntityLatestState.entity_id.in_(entity_ids))
        return list(self.session.exec(query).all())

    def recent_history(self, story_id: int, limit: int = 30) -> list[StateHistory]:
        return list(
            self.session.exec(
                select(StateHistory)
                .where(StateHistory.story_id == story_id)
                .order_by(StateHistory.created_at.desc())
                .limit(limit)
            ).all()
        )

    def chapter_summaries(self, story_id: int, limit: int | None = None) -> list[ChapterSummary]:
        query = (
            select(ChapterSummary)
            .join(Chapter, Chapter.id == ChapterSummary.chapter_id)
            .where(ChapterSummary.story_id == story_id)
            .order_by(Chapter.chapter_index.desc())
        )
        if limit:
            query = query.limit(limit)
        return list(self.session.exec(query).all())

    def latest_rolling_summary(self, story_id: int) -> RollingSummary | None:
        return self.session.exec(
            select(RollingSummary)
            .where(RollingSummary.story_id == story_id)
            .order_by(RollingSummary.updated_at.desc())
        ).first()

    def last_chapter_ending(self, story_id: int, chars: int = 700) -> str:
        chapter = self.session.exec(
            select(Chapter).where(Chapter.story_id == story_id).order_by(Chapter.chapter_index.desc())
        ).first()
        if chapter is None:
            return ""
        return chapter.content[-chars:]

    def all_chapters(self, story_id: int) -> list[Chapter]:
        return list(
            self.session.exec(
                select(Chapter).where(Chapter.story_id == story_id).order_by(Chapter.chapter_index)
            ).all()
        )

    def correct_latest_state(
        self,
        *,
        story_id: int,
        entity_id: str,
        entity_type: str,
        state_type: str,
        state_value: str,
        note: str,
    ) -> EntityLatestState:
        latest_chapter = self.session.exec(
            select(Chapter).where(Chapter.story_id == story_id).order_by(Chapter.chapter_index.desc())
        ).first()
        if latest_chapter is None:
            raise ValueError("Cannot correct memory before at least one chapter exists.")
        latest = self.session.exec(
            select(EntityLatestState).where(
                EntityLatestState.story_id == story_id,
                EntityLatestState.entity_id == entity_id,
                EntityLatestState.state_type == state_type,
            )
        ).first()
        old_value = latest.state_value if latest else ""
        history = StateHistory(
            story_id=story_id,
            chapter_id=latest_chapter.id,
            entity_id=entity_id,
            entity_type=entity_type,
            state_type=state_type,
            old_value=old_value,
            new_value=state_value,
            description=note,
        )
        self.session.add(history)
        if latest is None:
            latest = EntityLatestState(
                story_id=story_id,
                entity_id=entity_id,
                entity_type=entity_type,
                state_type=state_type,
                state_value=state_value,
                chapter_id=latest_chapter.id,
            )
        else:
            latest.entity_type = entity_type
            latest.state_value = state_value
            latest.chapter_id = latest_chapter.id
            latest.updated_at = utc_now()
        self.session.add(latest)
        self.session.commit()
        self.session.refresh(latest)
        return latest

