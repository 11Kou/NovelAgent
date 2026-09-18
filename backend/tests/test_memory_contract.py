from sqlmodel import Session, SQLModel, create_engine, select

from app.schemas.memory import StateChange
from app.storage.dynamic_store import DynamicStore
from app.storage.models import (
    Chapter,
    EntityLatestState,
    StateDescription,
    StateHistory,
    Story,
)


def test_state_change_updates_latest_and_keeps_history() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        story = Story(title="测试", premise="测试", style="", worldview="")
        session.add(story)
        session.commit()
        session.refresh(story)

        chapter = Chapter(
            story_id=story.id,
            chapter_index=1,
            title="第一章",
            event_description="事件",
            content="正文不会进入向量库。",
        )
        session.add(chapter)
        session.commit()
        session.refresh(chapter)

        store = DynamicStore(session)
        first = store.save_state_change(
            story_id=story.id,
            chapter_id=chapter.id,
            change=StateChange(
                entity_id="char_linxia",
                entity_type="character",
                state_type="location",
                old_value="未知",
                new_value="废弃地铁站",
                description="第一章中，林夏在废弃地铁站醒来。",
            ),
        )
        second = store.save_state_change(
            story_id=story.id,
            chapter_id=chapter.id,
            change=StateChange(
                entity_id="char_linxia",
                entity_type="character",
                state_type="location",
                old_value="废弃地铁站",
                new_value="地下诊所",
                description="第一章末，林夏抵达地下诊所。",
            ),
        )

        latest = session.exec(select(EntityLatestState)).all()
        history = session.exec(select(StateHistory).order_by(StateHistory.id)).all()

        assert len(latest) == 1
        assert latest[0].state_value == "地下诊所"
        assert [item.id for item in history] == [first.id, second.id]
        assert history[1].old_value == "废弃地铁站"


def test_state_description_is_one_to_one_with_history() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        story = Story(title="测试", premise="测试", style="", worldview="")
        session.add(story)
        session.commit()
        session.refresh(story)

        chapter = Chapter(story_id=story.id, chapter_index=1, event_description="事件", content="正文")
        session.add(chapter)
        session.commit()
        session.refresh(chapter)

        store = DynamicStore(session)
        history = store.save_state_change(
            story_id=story.id,
            chapter_id=chapter.id,
            change=StateChange(
                entity_id="item_key",
                entity_type="item",
                state_type="holder",
                old_value="未知",
                new_value="林夏",
                description="第一章中，银色钥匙被林夏拿到。",
            ),
        )
        description = store.save_state_description(
            story_id=story.id,
            chapter_id=chapter.id,
            history_id=history.id,
            entity_id="item_key",
            entity_type="item",
            text=history.description,
            embedding_id=f"state-history-{history.id}",
        )

        rows = session.exec(select(StateDescription)).all()

        assert len(rows) == 1
        assert rows[0].state_history_id == history.id
        assert rows[0].text == description.text
        assert "正文" not in rows[0].text

