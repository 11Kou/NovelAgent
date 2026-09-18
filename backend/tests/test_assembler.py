from app.retrieval.assembler import PromptAssembler
from app.schemas.story import ChapterEventDraft


class Obj:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_assembler_keeps_strong_constraints_before_event() -> None:
    static = {
        "story": Obj(title="失忆之城", premise="寻找身份", worldview="记忆可交易", style="悬疑"),
        "characters": [Obj(entity_id="char_linxia", name="林夏", identity="失忆少女", personality="谨慎", goal="寻找身份", background="")],
        "locations": [],
        "items": [],
        "world_rules": [Obj(content="记忆可以买卖")],
        "taboos": [Obj(content="不要让主角无理由获得真相")],
    }
    dynamic = {
        "latest_states": [Obj(entity_id="char_linxia", state_type="location", state_value="废弃地铁站")],
        "recent_history": [],
        "chapter_summaries": [],
        "rolling_summary": None,
        "last_chapter_ending": "",
    }
    event = ChapterEventDraft(chapter_index=1, event_description="林夏发现旧标记。")

    prompt = PromptAssembler(token_budget=1000).assemble(
        static_context=static,
        dynamic_context=dynamic,
        related_history=[],
        chapter_event=event,
    )

    assert prompt.index("【强约束区】") < prompt.index("【本章事件】")
    assert "不要让主角无理由获得真相" in prompt
    assert "char_linxia.location = 废弃地铁站" in prompt

