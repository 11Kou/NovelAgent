from app.config.settings import Settings
from app.services.model_clients import LLMClient, ModelClientError


def test_llm_client_missing_key_returns_clear_error() -> None:
    settings = Settings(deepseek_api_key="")
    client = LLMClient(settings)

    try:
        client.generate_text([{"role": "user", "content": "hello"}])
    except ModelClientError as exc:
        assert str(exc) == "DEEPSEEK_API_KEY is not configured."
    else:
        raise AssertionError("Expected missing DeepSeek key to raise ModelClientError.")

