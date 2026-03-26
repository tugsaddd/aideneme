"""
Yerel AI Sistemi - Ollama tabanlı sohbet uygulaması
"""

import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.yaml"


def load_config() -> dict:
    """config.yaml dosyasını yükler."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
