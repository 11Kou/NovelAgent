from sqlmodel import Session

from app.config.settings import Settings
from app.storage.dynamic_store import DynamicStore


class DynamicRetriever:
    def __init__(self, session: Session, settings: Settings):
        self.store = DynamicStore(session)
        self.settings = settings

    def retrieve(self, story_id: int, entity_ids: list[str] | None = None) -> dict:
        return {
            "latest_states": self.store.latest_states(story_id, entity_ids),
            "recent_history": self.store.recent_history(story_id, limit=30),
            "chapter_summaries": self.store.chapter_summaries(
                story_id,
                limit=self.settings.recent_chapter_window,
            ),
            "rolling_summary": self.store.latest_rolling_summary(story_id),
            "last_chapter_ending": self.store.last_chapter_ending(story_id),
        }

