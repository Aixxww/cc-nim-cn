import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from api.app import app
from api.dependencies import get_settings
from config.settings import Settings


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_settings():
    settings = Settings()
    settings.fast_prefix_detection = True
    settings.enable_network_probe_mock = True
    settings.enable_title_generation_skip = True
    return settings


def test_create_message_fast_prefix_detection(client, mock_settings):
    app.dependency_overrides[get_settings] = lambda: mock_settings

    payload = {
        "model": "claude-3-sonnet",
        "max_tokens": 100,
        "messages": [{"role": "user", "content": "What is the prefix?"}],
    }

    with patch("api.routes.is_prefix_detection_request", return_value=(True, "/ask")):
        response = client.post("/v1/messages", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "/ask" in data["content"][0]["text"]

    app.dependency_overrides.clear()


def test_create_message_quota_check_mock(client, mock_settings):
    app.dependency_overrides[get_settings] = lambda: mock_settings

    payload = {
        "model": "claude-3-sonnet",
        "max_tokens": 100,
        "messages": [{"role": "user", "content": "quota check"}],
    }

    with patch("api.routes.is_quota_check_request", return_value=True):
        response = client.post("/v1/messages", json=payload)

    assert response.status_code == 200
    assert "Quota check passed" in response.json()["content"][0]["text"]

    app.dependency_overrides.clear()


def test_create_message_title_generation_skip(client, mock_settings):
    app.dependency_overrides[get_settings] = lambda: mock_settings

    payload = {
        "model": "claude-3-sonnet",
        "max_tokens": 100,
        "messages": [{"role": "user", "content": "generate title"}],
    }

    with patch("api.routes.is_title_generation_request", return_value=True):
        response = client.post("/v1/messages", json=payload)

    assert response.status_code == 200
    assert "Conversation" in response.json()["content"][0]["text"]

    app.dependency_overrides.clear()


def test_count_tokens_endpoint(client):
    payload = {
        "model": "claude-3-sonnet",
        "messages": [{"role": "user", "content": "hello"}],
    }

    with patch("api.routes.get_token_count", return_value=5):
        response = client.post("/v1/messages/count_tokens", json=payload)

    assert response.status_code == 200
    assert response.json()["input_tokens"] == 5

# Note: test_stop_cli_with_handler and test_stop_cli_fallback_to_manager removed
# as the /stop route was removed in v2.2.0 when switching to proxy-only mode
