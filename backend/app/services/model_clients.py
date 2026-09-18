import json
import re
import time
from typing import Any, TypeVar

from ollama import Client as OllamaClient
from openai import OpenAI
from pydantic import BaseModel, ValidationError

from app.config.settings import Settings


class ModelClientError(RuntimeError):
    pass


T = TypeVar("T", bound=BaseModel)


class LLMClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = OpenAI(
            api_key=settings.deepseek_api_key or "missing",
            base_url=settings.deepseek_base_url,
            timeout=settings.model_timeout_seconds,
            max_retries=0,
        )

    def generate_text(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        if not self.settings.deepseek_api_key:
            raise ModelClientError(
                "DEEPSEEK_API_KEY is not configured. 请在项目根目录 .env 中配置 DeepSeek API Key。"
            )
        return self._retry(lambda: self._chat(messages, temperature, max_tokens), "DeepSeek generation")

    def generate_json(
        self,
        messages: list[dict[str, str]],
        schema: type[T],
        *,
        temperature: float = 0.2,
    ) -> T:
        text = self.generate_text(messages, temperature=temperature)
        payload = self._extract_json(text)
        try:
            return schema.model_validate(payload)
        except ValidationError as exc:
            raise ModelClientError(f"Model returned invalid JSON for {schema.__name__}: {exc}") from exc

    def _chat(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int | None,
    ) -> str:
        kwargs: dict[str, Any] = {
            "model": self.settings.deepseek_model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        response = self.client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        if not content:
            raise ModelClientError("DeepSeek returned an empty response.")
        return content

    def _retry(self, fn, label: str):
        last_error: Exception | None = None
        attempts = self.settings.model_max_retries + 1
        for attempt in range(1, attempts + 1):
            try:
                return fn()
            except Exception as exc:  # noqa: BLE001 - wrap third-party failures for API callers.
                last_error = exc
                if attempt < attempts:
                    time.sleep(min(2 ** (attempt - 1), 4))
        raise ModelClientError(
            f"{label} failed after {attempts} attempt(s). "
            f"请检查 DEEPSEEK_API_KEY、DEEPSEEK_BASE_URL={self.settings.deepseek_base_url} "
            f"和 DEEPSEEK_MODEL={self.settings.deepseek_model}。"
            f"原始错误：{_summarize_exception(last_error)}"
        ) from last_error

    @staticmethod
    def _extract_json(text: str) -> Any:
        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
            stripped = re.sub(r"```$", "", stripped).strip()
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            match = re.search(r"(\{.*\}|\[.*\])", stripped, flags=re.DOTALL)
            if not match:
                raise ModelClientError("Model response did not contain JSON.")
            return json.loads(match.group(1))


class EmbeddingClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = OllamaClient(
            host=settings.ollama_host,
            timeout=settings.model_timeout_seconds,
        )

    def embed(self, text: str) -> list[float]:
        return self.embed_many([text])[0]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self._retry(lambda: self._embed(texts), "Ollama embedding")

    def _embed(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embed(
            model=self.settings.ollama_embedding_model,
            input=texts,
            truncate=True,
        )
        embeddings = getattr(response, "embeddings", None)
        if embeddings is None and isinstance(response, dict):
            embeddings = response.get("embeddings")
        if not embeddings:
            raise ModelClientError(
                "Ollama returned no embeddings. 请检查 Ollama 是否已启动，"
                f"并确认 embedding 模型名 '{self.settings.ollama_embedding_model}' 可用。"
            )
        return [list(vector) for vector in embeddings]

    def _retry(self, fn, label: str):
        last_error: Exception | None = None
        attempts = self.settings.model_max_retries + 1
        for attempt in range(1, attempts + 1):
            try:
                return fn()
            except Exception as exc:  # noqa: BLE001 - wrap third-party failures for API callers.
                last_error = exc
                if attempt < attempts:
                    time.sleep(min(2 ** (attempt - 1), 4))
        raise ModelClientError(
            f"{label} failed after {attempts} attempt(s). 请检查 Ollama 是否已启动 "
            f"({self.settings.ollama_host})，并确认 embedding 模型名 "
            f"'{self.settings.ollama_embedding_model}' 是否正确。"
            f"原始错误：{_summarize_exception(last_error)}"
        ) from last_error


def _summarize_exception(exc: Exception | None) -> str:
    if exc is None:
        return "未知错误"
    message = str(exc).strip()
    if not message:
        message = exc.__class__.__name__
    return message[:500]
