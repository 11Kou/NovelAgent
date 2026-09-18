from pathlib import Path

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

