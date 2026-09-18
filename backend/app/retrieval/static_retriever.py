from sqlmodel import Session, select

from app.storage.models import Character, Item, Location, OutlineNode, Story, Taboo, WorldRule


class StaticRetriever:
    def __init__(self, session: Session):
        self.session = session

    def retrieve(self, story_id: int) -> dict:
        story = self.session.get(Story, story_id)
        if story is None:
            raise ValueError(f"Story {story_id} not found.")
        return {
            "story": story,
            "characters": self.session.exec(select(Character).where(Character.story_id == story_id)).all(),
            "locations": self.session.exec(select(Location).where(Location.story_id == story_id)).all(),
            "items": self.session.exec(select(Item).where(Item.story_id == story_id)).all(),
            "world_rules": self.session.exec(select(WorldRule).where(WorldRule.story_id == story_id)).all(),
            "taboos": self.session.exec(select(Taboo).where(Taboo.story_id == story_id)).all(),
            "outline": self.session.exec(
                select(OutlineNode).where(OutlineNode.story_id == story_id).order_by(OutlineNode.order_index)
            ).all(),
        }

