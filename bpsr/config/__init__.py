from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ..logutil import get_logger

logger = get_logger("Config")


@dataclass(slots=True)
class DiscordSettings:
    websocket_url: str = ""
    jwt_token: str = ""
    reconnect_delay: float = 5.0
    ping_interval: float = 30.0
    max_retries: int = 10
    enabled: bool = False


@dataclass(slots=True)
class Config:
    discord: DiscordSettings

    def __init__(self) -> None:
        self.discord = DiscordSettings()

    @classmethod
    def load_from_file(cls, config_path: Path) -> Config:
        config = cls()

        if not config_path.exists():
            logger.info(f"Configuration file not found: {config_path}")
            return config

        try:
            with config_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            if "discord" in data:
                discord_data = data["discord"]
                config.discord = DiscordSettings(
                    websocket_url=discord_data.get("websocket_url", ""),
                    jwt_token=discord_data.get("jwt_token", ""),
                    reconnect_delay=discord_data.get("reconnect_delay", 5.0),
                    ping_interval=discord_data.get("ping_interval", 30.0),
                    max_retries=discord_data.get("max_retries", 10),
                    enabled=discord_data.get("enabled", False),
                )

            logger.info(f"Configuration loaded from: {config_path}")

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")

        return config

    def save_to_file(self, config_path: Path) -> None:
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)

            data = {"discord": asdict(self.discord)}

            with config_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Configuration saved to: {config_path}")

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")

    def to_dict(self) -> dict[str, Any]:
        return {"discord": asdict(self.discord)}


def get_default_config_path() -> Path:
    return Path.cwd() / "config.json"
