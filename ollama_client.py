"""
Ollama API ile iletişim kuran istemci modülü.
"""

from __future__ import annotations

import json
from typing import AsyncIterator, Iterator

import httpx


class OllamaClient:
    """Ollama REST API istemcisi."""

    def __init__(self, base_url: str, timeout: int = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Model yönetimi
    # ------------------------------------------------------------------

    def list_models(self) -> list[str]:
        """Sistemde yüklü modellerin listesini döndürür."""
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]

    # ------------------------------------------------------------------
    # Sohbet (stream=False)
    # ------------------------------------------------------------------

    def chat(
        self,
        model: str,
        messages: list[dict],
        system_prompt: str | None = None,
    ) -> str:
        """Ollama'ya istek gönderir ve tam yanıtı döndürür."""
        payload = self._build_payload(model, messages, system_prompt, stream=False)
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]

    # ------------------------------------------------------------------
    # Sohbet (stream=True)
    # ------------------------------------------------------------------

    def chat_stream(
        self,
        model: str,
        messages: list[dict],
        system_prompt: str | None = None,
    ) -> Iterator[str]:
        """Ollama'ya istek gönderir ve yanıtı parça parça döndürür (sync)."""
        payload = self._build_payload(model, messages, system_prompt, stream=True)
        with httpx.Client(timeout=self.timeout) as client:
            with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield content
                    if chunk.get("done"):
                        break

    async def chat_stream_async(
        self,
        model: str,
        messages: list[dict],
        system_prompt: str | None = None,
    ) -> AsyncIterator[str]:
        """Ollama'ya istek gönderir ve yanıtı parça parça döndürür (async)."""
        payload = self._build_payload(model, messages, system_prompt, stream=True)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield content
                    if chunk.get("done"):
                        break

    # ------------------------------------------------------------------
    # Yardımcılar
    # ------------------------------------------------------------------

    @staticmethod
    def _build_payload(
        model: str,
        messages: list[dict],
        system_prompt: str | None,
        stream: bool,
    ) -> dict:
        all_messages: list[dict] = []
        if system_prompt:
            all_messages.append({"role": "system", "content": system_prompt})
        all_messages.extend(messages)
        return {"model": model, "messages": all_messages, "stream": stream}

    def is_available(self) -> bool:
        """Ollama sunucusuna erişilebilir mi kontrol eder."""
        try:
            with httpx.Client(timeout=5) as client:
                client.get(f"{self.base_url}/api/tags")
            return True
        except Exception:
            return False
