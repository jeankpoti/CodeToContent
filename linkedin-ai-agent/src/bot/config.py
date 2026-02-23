"""
Per-Chat Configuration Storage

Stores user preferences using Telegram chat ID as the key.
No database required - uses JSON files for simplicity.
"""

import json
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime


@dataclass
class UserConfig:
    """User configuration stored per Telegram chat."""
    chat_id: int
    github_url: Optional[str] = None
    linkedin_token: Optional[str] = None
    linkedin_token_expiry: Optional[str] = None
    preferred_time: Optional[str] = None  # HH:MM format
    timezone_offset: Optional[int] = None  # Offset from UTC in seconds
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def is_configured(self) -> bool:
        """Check if minimum config is set for post generation."""
        return self.github_url is not None

    def is_linkedin_connected(self) -> bool:
        """Check if LinkedIn is connected and token is valid."""
        if not self.linkedin_token or not self.linkedin_token_expiry:
            return False
        try:
            expiry = datetime.fromisoformat(self.linkedin_token_expiry)
            return datetime.now() < expiry
        except:
            return False


class ConfigStore:
    """Manages per-chat configuration storage."""

    def __init__(self, config_dir: str = "./user_configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _get_config_path(self, chat_id: int) -> Path:
        """Get path to config file for a chat."""
        return self.config_dir / f"chat_{chat_id}.json"

    def get(self, chat_id: int) -> UserConfig:
        """
        Get configuration for a chat.

        Args:
            chat_id: Telegram chat ID

        Returns:
            UserConfig object (empty if not found)
        """
        config_path = self._get_config_path(chat_id)

        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    data = json.load(f)
                    return UserConfig(**data)
            except Exception as e:
                print(f"Error loading config for chat {chat_id}: {e}")

        return UserConfig(chat_id=chat_id)

    def save(self, config: UserConfig) -> None:
        """
        Save configuration for a chat.

        Args:
            config: UserConfig object to save
        """
        config_path = self._get_config_path(config.chat_id)

        # Update timestamps
        now = datetime.now().isoformat()
        if not config.created_at:
            config.created_at = now
        config.updated_at = now

        try:
            with open(config_path, "w") as f:
                json.dump(asdict(config), f, indent=2)
        except Exception as e:
            print(f"Error saving config for chat {config.chat_id}: {e}")

    def update(self, chat_id: int, **kwargs) -> UserConfig:
        """
        Update specific fields in a chat's configuration.

        Args:
            chat_id: Telegram chat ID
            **kwargs: Fields to update

        Returns:
            Updated UserConfig object
        """
        config = self.get(chat_id)

        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

        self.save(config)
        return config

    def delete(self, chat_id: int) -> bool:
        """
        Delete configuration for a chat.

        Args:
            chat_id: Telegram chat ID

        Returns:
            True if deleted, False if not found
        """
        config_path = self._get_config_path(chat_id)

        if config_path.exists():
            config_path.unlink()
            return True
        return False

    def list_all(self) -> list[UserConfig]:
        """
        List all stored configurations.

        Returns:
            List of UserConfig objects
        """
        configs = []

        for config_file in self.config_dir.glob("chat_*.json"):
            try:
                with open(config_file, "r") as f:
                    data = json.load(f)
                    configs.append(UserConfig(**data))
            except Exception as e:
                print(f"Error loading config {config_file}: {e}")

        return configs
