from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
import yaml

from app.services.model_clients import LLMClient


PROMPT_DIR = Path(__file__).resolve().parent.parent / "config" / "prompts"


class BaseAgent:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def prompt(self, name: str) -> str:
        path = PROMPT_DIR / f"{name}.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data["system"]

    def messages(self, *, system: str, user: str) -> list[dict[str, str]]:
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", user),
            ]
        )
        rendered = prompt.invoke({})
        role_map = {"system": "system", "human": "user", "ai": "assistant"}
        return [
            {"role": role_map.get(message.type, message.type), "content": str(message.content)}
            for message in rendered.messages
        ]
