from app.schemas.story import ChapterEventDraft


class PromptAssembler:
    def __init__(self, token_budget: int):
        self.token_budget = token_budget

    def assemble(
        self,
        *,
        static_context: dict,
        dynamic_context: dict,
        related_history: list[str],
        chapter_event: ChapterEventDraft,
    ) -> str:
        strong_constraints = self._strong_constraints(static_context)
        latest_states = self._latest_states(dynamic_context["latest_states"])
        event = f"【本章事件】\n{chapter_event.event_description}"
        last_ending = self._section("【上一章结尾】", dynamic_context["last_chapter_ending"])
        recent = self._recent_context(dynamic_context)
        rolling = self._section(
            "【前情提要】",
            dynamic_context["rolling_summary"].summary if dynamic_context["rolling_summary"] else "",
        )
        related = self._section("【相关历史】", "\n".join(f"- {item}" for item in related_history))

        optional_sections = [related, recent, rolling]
        required = "\n\n".join(part for part in [strong_constraints, latest_states, event, last_ending] if part)
        prompt = self._fit(required, optional_sections)
        return (
            prompt
            + "\n\n【生成要求】\n"
            "写成本章正文。保持叙事连贯，完成本章事件，不违反强约束区和最新状态。"
        )

    def _fit(self, required: str, optional_sections: list[str]) -> str:
        char_budget = self.token_budget * 4
        sections = [section for section in optional_sections if section]
        while sections and len(required + "\n\n".join(sections)) > char_budget:
            sections.pop(0)
        return "\n\n".join([required, *sections])

    @staticmethod
    def _section(title: str, content: str) -> str:
        return f"{title}\n{content}" if content.strip() else ""

    @staticmethod
    def _strong_constraints(static_context: dict) -> str:
        story = static_context["story"]
        lines = [
            "【强约束区】",
            f"标题：{story.title}",
            f"核心前提：{story.premise}",
            f"世界观：{story.worldview}",
            f"风格：{story.style}",
            "角色：",
        ]
        lines.extend(
            f"- {c.entity_id} / {c.name}：{c.identity}；性格：{c.personality}；目标：{c.goal}；背景：{c.background}"
            for c in static_context["characters"]
        )
        lines.append("地点：")
        lines.extend(f"- {l.entity_id} / {l.name}：{l.description}" for l in static_context["locations"])
        lines.append("道具：")
        lines.extend(f"- {i.entity_id} / {i.name}：{i.description}" for i in static_context["items"])
        lines.append("世界规则：")
        lines.extend(f"- {r.content}" for r in static_context["world_rules"])
        lines.append("禁忌：")
        lines.extend(f"- {t.content}" for t in static_context["taboos"])
        return "\n".join(lines)

    @staticmethod
    def _latest_states(states) -> str:
        if not states:
            return ""
        lines = ["【最新状态】"]
        lines.extend(f"- {s.entity_id}.{s.state_type} = {s.state_value}" for s in states)
        return "\n".join(lines)

    @staticmethod
    def _recent_context(dynamic_context: dict) -> str:
        lines = ["【近期状态】"]
        summaries = dynamic_context["chapter_summaries"]
        history = dynamic_context["recent_history"]
        if summaries:
            lines.append("章节摘要：")
            lines.extend(f"- {s.summary}" for s in reversed(summaries))
        if history:
            lines.append("状态变化：")
            lines.extend(f"- {h.description}" for h in reversed(history[-12:]))
        return "\n".join(lines) if len(lines) > 1 else ""

