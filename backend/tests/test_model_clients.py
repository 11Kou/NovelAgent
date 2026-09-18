from app.config.settings import Settings
from app.services.model_clients import EmbeddingClient, LLMClient, ModelClientError


def test_llm_client_missing_key_returns_clear_error() -> None:
    settings = Settings(deepseek_api_key="")
    client = LLMClient(settings)

    try:
        client.generate_text([{"role": "user", "content": "hello"}])
    except ModelClientError as exc:
        assert "DEEPSEEK_API_KEY is not configured" in str(exc)
        assert ".env" in str(exc)
    else:
        raise AssertionError("Expected missing DeepSeek key to raise ModelClientError.")


def test_llm_client_wraps_generation_failures_with_config_hint(monkeypatch) -> None:
    settings = Settings(deepseek_api_key="key", model_max_retries=1)
    client = LLMClient(settings)

    def fail_chat(*args, **kwargs):
        raise TimeoutError("timed out")

    monkeypatch.setattr(client, "_chat", fail_chat)

    try:
        client.generate_text([{"role": "user", "content": "hello"}])
    except ModelClientError as exc:
        message = str(exc)
        assert "DeepSeek generation failed after 2 attempt(s)" in message
        assert "DEEPSEEK_BASE_URL" in message
        assert "DEEPSEEK_MODEL" in message
        assert "timed out" in message
    else:
        raise AssertionError("Expected DeepSeek generation failure to raise ModelClientError.")


def test_embedding_client_wraps_ollama_failures_with_model_hint(monkeypatch) -> None:
    settings = Settings(model_max_retries=0, ollama_embedding_model="missing-m3")
    client = EmbeddingClient(settings)

    def fail_embed(texts):
        raise ConnectionError("connection refused")

    monkeypatch.setattr(client, "_embed", fail_embed)

    try:
        client.embed("hello")
    except ModelClientError as exc:
        message = str(exc)
        assert "Ollama embedding failed after 1 attempt(s)" in message
        assert "Ollama" in message
        assert "missing-m3" in message
        assert "connection refused" in message
    else:
        raise AssertionError("Expected Ollama embedding failure to raise ModelClientError.")
