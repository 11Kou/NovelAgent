from app.agents.base import BaseAgent


class WritingAgent(BaseAgent):
    def write_chapter(self, assembled_prompt: str, rewrite_note: str = "") -> str:
        note = f"\n\n用户重写要求：{rewrite_note}" if rewrite_note else ""
        return self.llm.generate_text(
            self.messages(
                system=self.prompt("writing"),
                user=assembled_prompt + note,
            ),
            temperature=0.75,
        )
