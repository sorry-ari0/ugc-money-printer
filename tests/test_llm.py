from unittest.mock import patch, MagicMock
import pytest
from ugc.llm import LLMRouter


def test_route_to_primary():
    router = LLMRouter(
        primary="anthropic", primary_model="claude-sonnet-4-6",
        fallback="ollama", fallback_model="llama-agent:latest",
        anthropic_api_key="test-key"
    )
    assert router.primary == "anthropic"
    assert router.primary_model == "claude-sonnet-4-6"


def test_route_to_fallback_when_no_api_key():
    router = LLMRouter(
        primary="anthropic", primary_model="claude-sonnet-4-6",
        fallback="ollama", fallback_model="llama-agent:latest",
        anthropic_api_key=""
    )
    provider, model = router.select()
    assert provider == "ollama"
    assert model == "llama-agent:latest"


def test_route_to_primary_when_api_key_present():
    router = LLMRouter(
        primary="anthropic", primary_model="claude-sonnet-4-6",
        fallback="ollama", fallback_model="llama-agent:latest",
        anthropic_api_key="sk-test"
    )
    provider, model = router.select()
    assert provider == "anthropic"


@patch("ugc.llm.Anthropic")
def test_chat_anthropic(mock_cls):
    mock_client = MagicMock()
    mock_cls.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="response text")]
    )

    router = LLMRouter(
        primary="anthropic", primary_model="claude-sonnet-4-6",
        fallback="ollama", fallback_model="llama-agent:latest",
        anthropic_api_key="sk-test"
    )
    result = router.chat("Hello")
    assert result == "response text"
    mock_client.messages.create.assert_called_once()


@patch("ugc.llm.ollama_chat")
def test_chat_ollama(mock_chat):
    mock_chat.return_value = {"message": {"content": "ollama response"}}

    router = LLMRouter(
        primary="ollama", primary_model="llama-agent:latest",
        fallback="ollama", fallback_model="llama-agent:latest",
        anthropic_api_key=""
    )
    result = router.chat("Hello")
    assert result == "ollama response"
