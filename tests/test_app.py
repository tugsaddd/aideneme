"""
Temel birim testleri.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# OllamaClient testleri
# ---------------------------------------------------------------------------

class TestOllamaClient:
    def test_build_payload_with_system(self):
        from ollama_client import OllamaClient

        payload = OllamaClient._build_payload(
            model="llama3.2",
            messages=[{"role": "user", "content": "Merhaba"}],
            system_prompt="Sen bir asistansın",
            stream=False,
        )
        assert payload["model"] == "llama3.2"
        assert payload["stream"] is False
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][1]["role"] == "user"

    def test_build_payload_without_system(self):
        from ollama_client import OllamaClient

        payload = OllamaClient._build_payload(
            model="llama3.2",
            messages=[{"role": "user", "content": "Merhaba"}],
            system_prompt=None,
            stream=True,
        )
        assert payload["messages"][0]["role"] == "user"
        assert len(payload["messages"]) == 1

    def test_is_available_returns_false_on_connection_error(self):
        from ollama_client import OllamaClient

        client = OllamaClient(base_url="http://localhost:9999")
        assert client.is_available() is False

    def test_list_models(self):
        from ollama_client import OllamaClient

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "models": [{"name": "llama3.2"}, {"name": "mistral"}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
            mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)

            client = OllamaClient(base_url="http://localhost:11434")
            models = client.list_models()

        assert models == ["llama3.2", "mistral"]


# ---------------------------------------------------------------------------
# Config testleri
# ---------------------------------------------------------------------------

class TestConfig:
    def test_load_config_returns_dict(self):
        from config import load_config

        cfg = load_config()
        assert isinstance(cfg, dict)
        assert "ollama" in cfg
        assert "server" in cfg
        assert "chat" in cfg

    def test_ollama_config_has_required_keys(self):
        from config import load_config

        cfg = load_config()
        ollama_cfg = cfg["ollama"]
        assert "base_url" in ollama_cfg
        assert "default_model" in ollama_cfg
        assert "timeout" in ollama_cfg

    def test_chat_config_has_required_keys(self):
        from config import load_config

        cfg = load_config()
        chat_cfg = cfg["chat"]
        assert "system_prompt" in chat_cfg
        assert "max_history" in chat_cfg


# ---------------------------------------------------------------------------
# FastAPI uç nokta testleri
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Test istemcisi – Ollama bağlantısı olmadan."""
    from app import app
    return TestClient(app, raise_server_exceptions=False)


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        with patch("app.ollama") as mock_ollama:
            mock_ollama.is_available.return_value = True
            response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_structure(self, client):
        with patch("app.ollama") as mock_ollama:
            mock_ollama.is_available.return_value = True
            response = client.get("/api/health")
        data = response.json()
        assert "status" in data
        assert "ollama" in data


class TestModelsEndpoint:
    def test_models_returns_list(self, client):
        with patch("app.ollama") as mock_ollama:
            mock_ollama.list_models.return_value = ["llama3.2", "mistral"]
            response = client.get("/api/models")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert "llama3.2" in data["models"]

    def test_models_503_when_ollama_unavailable(self, client):
        with patch("app.ollama") as mock_ollama:
            mock_ollama.list_models.side_effect = Exception("Bağlantı hatası")
            response = client.get("/api/models")
        assert response.status_code == 503


class TestIndexEndpoint:
    def test_index_returns_html(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
