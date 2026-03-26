"""
FastAPI tabanlı web sunucusu - Yerel AI sohbet arayüzü.

Başlatmak için:
    python app.py
veya:
    uvicorn app:app --host 127.0.0.1 --port 8000
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import AsyncIterator

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from config import load_config
from ollama_client import OllamaClient

# ---------------------------------------------------------------------------
# Uygulama kurulumu
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
config = load_config()

ollama = OllamaClient(
    base_url=config["ollama"]["base_url"],
    timeout=config["ollama"]["timeout"],
)

app = FastAPI(title="Yerel AI", version="1.0.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# ---------------------------------------------------------------------------
# Veri modelleri
# ---------------------------------------------------------------------------


class ChatMessage(BaseModel):
    role: str          # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    model: str | None = None
    stream: bool = True
    system_prompt: str | None = None


# ---------------------------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------------------------


def get_model(requested: str | None) -> str:
    return requested or config["ollama"]["default_model"]


def get_system_prompt() -> str:
    return config["chat"]["system_prompt"]


def trim_history(messages: list[dict]) -> list[dict]:
    """Geçmişi maksimum uzunlukla sınırla."""
    max_history = config["chat"].get("max_history", 20)
    return messages[-max_history:]


# ---------------------------------------------------------------------------
# API uç noktaları
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Ana sohbet sayfasını döndürür."""
    return templates.TemplateResponse(request, "index.html")


@app.get("/api/models")
async def list_models() -> dict:
    """Sistemde yüklü Ollama modellerini listeler."""
    try:
        models = ollama.list_models()
        return {"models": models, "default": config["ollama"]["default_model"]}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Ollama'ya bağlanılamadı: {exc}") from exc


@app.get("/api/health")
async def health() -> dict:
    """Sistem durumunu kontrol eder."""
    available = ollama.is_available()
    return {
        "status": "ok" if available else "ollama_unavailable",
        "ollama": available,
        "ollama_url": config["ollama"]["base_url"],
    }


@app.post("/api/chat")
async def chat(req: ChatRequest) -> StreamingResponse:
    """Sohbet isteğini işler ve yanıtı akış olarak döndürür."""
    model = get_model(req.model)
    messages = trim_history([m.model_dump() for m in req.messages])
    system_prompt = req.system_prompt if req.system_prompt is not None else get_system_prompt()

    if req.stream:
        return StreamingResponse(
            _stream_response(model, messages, system_prompt),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    # Akışsız yanıt
    try:
        reply = await asyncio.to_thread(ollama.chat, model, messages, system_prompt)
        return StreamingResponse(
            _single_event(reply),
            media_type="text/event-stream",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Yardımcı async jeneratörler
# ---------------------------------------------------------------------------


async def _stream_response(
    model: str,
    messages: list[dict],
    system_prompt: str,
) -> AsyncIterator[str]:
    """SSE formatında akış üretir."""
    try:
        async for chunk in ollama.chat_stream_async(model, messages, system_prompt):
            payload = json.dumps({"content": chunk, "done": False})
            yield f"data: {payload}\n\n"
        yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"
    except Exception as exc:
        error_payload = json.dumps({"error": str(exc), "done": True})
        yield f"data: {error_payload}\n\n"


async def _single_event(content: str) -> AsyncIterator[str]:
    payload = json.dumps({"content": content, "done": True})
    yield f"data: {payload}\n\n"


# ---------------------------------------------------------------------------
# Giriş noktası
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    print("=" * 60)
    print("  Yerel AI Sohbet Uygulaması")
    print("=" * 60)
    print(f"  Adres : http://{config['server']['host']}:{config['server']['port']}")
    print(f"  Model  : {config['ollama']['default_model']}")
    print(f"  Ollama : {config['ollama']['base_url']}")
    print("=" * 60)
    if not ollama.is_available():
        print("\n  UYARI: Ollama çalışmıyor!")
        print("  Ollama'yı kurmak için: https://ollama.ai")
        print("  Model indirmek için : ollama pull llama3.2\n")
    else:
        models = ollama.list_models()
        print(f"\n  Yüklü modeller: {', '.join(models) if models else 'Yok'}\n")

    uvicorn.run(
        "app:app",
        host=config["server"]["host"],
        port=config["server"]["port"],
        reload=config["server"]["reload"],
    )
