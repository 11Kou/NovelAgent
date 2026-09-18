from app.agents.base import BaseAgent
from app.schemas.memory import MemoryDraft


class MemoryAgent(BaseAgent):
    def extract_memory(
        self,
        *,
        chapter_id: int,
        chapter_index: int,
        chapter_event: str,
        chapter_content: str,
    ) -> MemoryDraft:
        draft = self.llm.generate_json(
            self.messages(
                system=self.prompt("extraction"),
                user=(
                    f"chapter_id: {chapter_id}\n"
                    f"chapter_index: {chapter_index}\n"
                    f"本章事件：{chapter_event}\n\n"
                    f"章节正文：\n{chapter_content}\n"
                ),
            ),
            MemoryDraft,
            temperature=0.1,
        )
        draft.chapter_id = chapter_id
        return draft

    def update_rolling_summary(self, previous_summary: str, recent_summaries: list[str]) -> str:
        return self.llm.generate_text(
            self.messages(
                system=self.prompt("summary"),
                user=(
                    f"已有滚动摘要：\n{previous_summary or '无'}\n\n"
                    "需要合并的近期章节摘要：\n"
                    + "\n".join(f"- {summary}" for summary in recent_summaries)
                ),
            ),
            temperature=0.2,
        )
