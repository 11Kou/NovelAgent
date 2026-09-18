from app.agents.base import BaseAgent
from app.schemas.story import ChapterEventDraft, StorySettingsDraft


class PlanningAgent(BaseAgent):
    def draft_settings(self, idea: str) -> StorySettingsDraft:
        return self.llm.generate_json(
            [
                {"role": "system", "content": self.prompt("planning")},
                {
                    "role": "user",
                    "content": (
                        "请根据用户想法生成第一版故事设定卡，只返回 JSON。\n"
                        f"用户想法：{idea}"
                    ),
                },
            ],
            StorySettingsDraft,
        )

    def draft_chapter_event(
        self,
        *,
        chapter_index: int,
        story_context: str,
        user_note: str = "",
    ) -> ChapterEventDraft:
        return self.llm.generate_json(
            [
                {"role": "system", "content": self.prompt("chapter_event")},
                {
                    "role": "user",
                    "content": (
                        f"当前章节序号：{chapter_index}\n"
                        f"故事上下文：\n{story_context}\n\n"
                        f"用户补充要求：{user_note or '无'}\n"
                        "请输出本章事件 JSON。"
                    ),
                },
            ],
            ChapterEventDraft,
        )

