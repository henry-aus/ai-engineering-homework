"""Configuration management for the multi-agent system."""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Application configuration loaded from environment variables."""

    # API Keys
    anthropic_api_key: str
    tavily_api_key: str

    # Model Configuration
    claude_model: str = "claude-3-5-sonnet-20241022"
    temperature: float = 0.7
    max_tokens: int = 4000

    # Retry Configuration
    max_retries_level_1: int = 2
    max_retries_level_2: int = 2

    # HITL Configuration
    hitl_enabled: bool = True

    # Logging
    log_level: str = "INFO"

    # Paths
    report_path: str = "./report.md"

    # Research Configuration
    max_search_results: int = 7
    search_depth: str = "advanced"

    # Article Configuration
    target_word_count: int = 1500
    article_style: str = "professional"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from environment."""
        return cls()

    def validate_keys(self) -> None:
        """Validate that required API keys are present."""
        if not self.anthropic_api_key or self.anthropic_api_key == "":
            raise ValueError("ANTHROPIC_API_KEY is required")
        if not self.tavily_api_key or self.tavily_api_key == "":
            raise ValueError("TAVILY_API_KEY is required")


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create the global config instance."""
    global _config
    if _config is None:
        _config = Config.load()
        _config.validate_keys()
    return _config
