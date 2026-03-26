"""
Komut satırı arayüzü – Yerel AI sohbet.

Kullanım:
    python cli.py
    python cli.py --model llama3.2
    python cli.py --model mistral --system "Sen bir Python uzmanısın"
"""

from __future__ import annotations

import argparse
import sys

import httpx
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from config import load_config
from ollama_client import OllamaClient

console = Console()


def parse_args() -> argparse.Namespace:
    config = load_config()
    parser = argparse.ArgumentParser(
        description="Yerel AI – Komut satırı sohbet arayüzü",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Çıkmak için 'çıkış', 'exit' veya Ctrl+C yazın.",
    )
    parser.add_argument(
        "--model", "-m",
        default=config["ollama"]["default_model"],
        help="Kullanılacak Ollama modeli (varsayılan: %(default)s)",
    )
    parser.add_argument(
        "--system", "-s",
        default=config["chat"]["system_prompt"],
        help="Sistem mesajı (asistana verilecek rol)",
    )
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Akışlı yanıt yerine tek seferde al",
    )
    return parser.parse_args()


def run_cli() -> None:
    args = parse_args()
    config = load_config()

    ollama = OllamaClient(
        base_url=config["ollama"]["base_url"],
        timeout=config["ollama"]["timeout"],
    )

    # Başlık
    console.print(
        Panel.fit(
            f"[bold magenta]🤖 Yerel AI[/] – [cyan]{args.model}[/]\n"
            "[dim]Çıkmak için: 'çıkış' | 'exit' | Ctrl+C[/]",
            border_style="magenta",
        )
    )

    # Ollama kontrolü
    if not ollama.is_available():
        console.print(
            "[bold red]HATA:[/] Ollama çalışmıyor.\n"
            "  • Kurulum: [link=https://ollama.ai]https://ollama.ai[/link]\n"
            f"  • Model indirme: [bold]ollama pull {args.model}[/]"
        )
        sys.exit(1)

    models = ollama.list_models()
    if models:
        console.print(f"[dim]Yüklü modeller: {', '.join(models)}[/]")
    console.print()

    history: list[dict] = []
    EXIT_COMMANDS = {"çıkış", "cikis", "exit", "quit", "q"}

    while True:
        try:
            user_text = Prompt.ask("[bold green]Sen[/]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Görüşmek üzere! 👋[/]")
            break

        if not user_text:
            continue

        if user_text.lower() in EXIT_COMMANDS:
            console.print("[dim]Görüşmek üzere! 👋[/]")
            break

        if user_text.lower() in {"/temizle", "/clear", "/yeni", "/new"}:
            history.clear()
            console.clear()
            console.print("[dim]Sohbet temizlendi.[/]\n")
            continue

        if user_text.lower() in {"/modeller", "/models"}:
            mods = ollama.list_models()
            console.print(f"[dim]Yüklü modeller: {', '.join(mods) if mods else 'Yok'}[/]\n")
            continue

        history.append({"role": "user", "content": user_text})
        max_history = config["chat"].get("max_history", 20)
        trimmed = history[-max_history:]

        console.print(Text("🤖 AI:", style="bold blue"), end=" ")

        try:
            if args.no_stream:
                reply = ollama.chat(args.model, trimmed, args.system)
                console.print(Markdown(reply))
            else:
                full_reply = ""
                for chunk in ollama.chat_stream(args.model, trimmed, args.system):
                    console.print(chunk, end="", highlight=False)
                    full_reply += chunk
                console.print()  # satır sonu
                reply = full_reply

            history.append({"role": "assistant", "content": reply})
        except (httpx.HTTPError, httpx.ConnectError, OSError) as exc:
            console.print(f"\n[bold red]Hata:[/] {exc}")
            history.pop()  # başarısız kullanıcı mesajını geri al

        console.print()


if __name__ == "__main__":
    run_cli()
