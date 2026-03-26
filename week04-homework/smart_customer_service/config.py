"""Configuration management."""
import os
import threading
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


class Config:
    """Application configuration with hot reload support."""

    _lock = threading.RLock()

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0"))

    # Logging
    LOG_DIR: str = os.getenv("LOG_DIR", "logs")

    # Hot Reload Configuration
    HOT_RELOAD_ENABLED: bool = os.getenv("HOT_RELOAD_ENABLED", "true").lower() == "true"
    PLUGIN_WATCH_ENABLED: bool = os.getenv("PLUGIN_WATCH_ENABLED", "true").lower() == "true"

    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_RELOAD: bool = os.getenv("API_RELOAD", "false").lower() == "true"

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        return True

    @classmethod
    def reload(cls):
        """Reload configuration from environment variables."""
        with cls._lock:
            load_dotenv(env_path, override=True)
            cls.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
            cls.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
            cls.OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0"))
            cls.LOG_DIR = os.getenv("LOG_DIR", "logs")
            cls.HOT_RELOAD_ENABLED = os.getenv("HOT_RELOAD_ENABLED", "true").lower() == "true"
            cls.PLUGIN_WATCH_ENABLED = os.getenv("PLUGIN_WATCH_ENABLED", "true").lower() == "true"
            cls.API_HOST = os.getenv("API_HOST", "0.0.0.0")
            cls.API_PORT = int(os.getenv("API_PORT", "8000"))
            cls.API_RELOAD = os.getenv("API_RELOAD", "false").lower() == "true"

    @classmethod
    def get_dict(cls) -> dict:
        """Get configuration as dictionary."""
        with cls._lock:
            return {
                "openai_api_key": "***" if cls.OPENAI_API_KEY else "",
                "openai_model": cls.OPENAI_MODEL,
                "openai_temperature": cls.OPENAI_TEMPERATURE,
                "log_dir": cls.LOG_DIR,
                "hot_reload_enabled": cls.HOT_RELOAD_ENABLED,
                "plugin_watch_enabled": cls.PLUGIN_WATCH_ENABLED,
                "api_host": cls.API_HOST,
                "api_port": cls.API_PORT,
            }
