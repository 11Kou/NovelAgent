import re

from sqlmodel import Session, select

from app.schemas.story import StorySettingsDraft
from app.storage.models import (
    Character,
    Item,
    Location,
    OutlineNode,
    Story,
    Taboo,
    WorldRule,
)


def slugify_entity(prefix: str, name: str) -> str:
    normalized = re.sub(r"\W+", "_", name.lower()).strip("_")
    return f"{prefix}_{normalized or 'entity'}"


class StaticStore:
    def __init__(self, session: Session):
        self.session = session

    def create_story(self, settings: StorySettingsDraft) -> Story:
        story = Story(
            title=settings.title,
            premise=settings.premise,
            worldview=settings.worldview,
            style=settings.style,
        )
        self.session.add(story)
        self.session.commit()
        self.session.refresh(story)

        for character in settings.characters:
            self.session.add(
                Character(
                    story_id=story.id,
                    entity_id=character.entity_id or slugify_entity("char", character.name),
                    name=character.name,
                    identity=character.identity,
                    personality=character.personality,
                    goal=character.goal,
                    background=character.background,
                )
            )
        for location in settings.locations:
            self.session.add(
                Location(
                    story_id=story.id,
                    entity_id=location.entity_id or slugify_entity("loc", location.name),
                    name=location.name,
                    description=location.description,
                )
            )
        for item in settings.items:
            self.session.add(
                Item(
                    story_id=story.id,
                    entity_id=item.entity_id or slugify_entity("item", item.name),
                    name=item.name,
                    description=item.description,
                )
            )
        for content in settings.world_rules:
            self.session.add(WorldRule(story_id=story.id, content=content))
        for content in settings.taboos:
            self.session.add(Taboo(story_id=story.id, content=content))
        for node in settings.outline:
            self.session.add(
                OutlineNode(
                    story_id=story.id,
                    title=node.title,
                    required_events=node.required_events,
                    status=node.status,
                    order_index=node.order_index,
                )
            )
        self.session.commit()
        return story

    def get_story(self, story_id: int) -> Story | None:
        return self.session.get(Story, story_id)

    def export_settings(self, story_id: int) -> StorySettingsDraft:
        story = self.session.get(Story, story_id)
        if story is None:
            raise ValueError(f"Story {story_id} not found.")
        characters = self.session.exec(select(Character).where(Character.story_id == story_id)).all()
        locations = self.session.exec(select(Location).where(Location.story_id == story_id)).all()
        items = self.session.exec(select(Item).where(Item.story_id == story_id)).all()
        world_rules = self.session.exec(select(WorldRule).where(WorldRule.story_id == story_id)).all()
        taboos = self.session.exec(select(Taboo).where(Taboo.story_id == story_id)).all()
        outline = self.session.exec(
            select(OutlineNode).where(OutlineNode.story_id == story_id).order_by(OutlineNode.order_index)
        ).all()
        return StorySettingsDraft(
            title=story.title,
            premise=story.premise,
            worldview=story.worldview,
            style=story.style,
            characters=[c.model_dump() for c in characters],
            locations=[l.model_dump() for l in locations],
            items=[i.model_dump() for i in items],
            world_rules=[r.content for r in world_rules],
            taboos=[t.content for t in taboos],
            outline=[o.model_dump() for o in outline],
        )

