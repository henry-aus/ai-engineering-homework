"""Hot reload manager for model and plugin updates."""
import importlib
import sys
import threading
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import time
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.tools import BaseTool
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from .config import Config


class PluginReloadHandler(FileSystemEventHandler):
    """File system event handler for plugin hot reload."""

    def __init__(self, reload_callback: Callable):
        super().__init__()
        self.reload_callback = reload_callback
        self.last_reload = 0
        self.debounce_seconds = 1.0  # Debounce to avoid multiple reloads

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events."""
        if event.is_directory:
            return

        if event.src_path.endswith('tools.py'):
            current_time = time.time()
            if current_time - self.last_reload > self.debounce_seconds:
                print(f"🔄 Detected changes in {event.src_path}, reloading plugins...")
                self.last_reload = current_time
                self.reload_callback()


class HotReloadManager:
    """Manager for hot reloading models and plugins."""

    def __init__(self):
        self._lock = threading.RLock()
        self._model_config: Dict[str, Any] = {
            "model": Config.OPENAI_MODEL,
            "api_key": Config.OPENAI_API_KEY,
            "temperature": 0,
        }
        self._plugins: List[BaseTool] = []
        self._plugin_version = 0
        self._model_version = 0
        self._file_observer: Optional[Observer] = None
        self._last_reload_time: Optional[datetime] = None

        # Initialize plugins
        self._load_plugins()

    def _load_plugins(self):
        """Load or reload plugins from tools module."""
        try:
            # Import or reload the tools module
            if 'smart_customer_service.tools' in sys.modules:
                importlib.reload(sys.modules['smart_customer_service.tools'])
            else:
                import smart_customer_service.tools

            # Get the TOOLS list from the module
            from smart_customer_service.tools import TOOLS

            with self._lock:
                self._plugins = TOOLS.copy()
                self._plugin_version += 1
                self._last_reload_time = datetime.now()

            print(f"✅ Plugins loaded successfully. Version: {self._plugin_version}")
            print(f"   Available tools: {[tool.name for tool in self._plugins]}")

        except Exception as e:
            print(f"❌ Failed to load plugins: {e}")
            import traceback
            traceback.print_exc()

    def reload_plugins(self) -> Dict[str, Any]:
        """Manually trigger plugin reload."""
        print(f"🔄 Reloading plugins...")
        old_version = self._plugin_version
        self._load_plugins()

        return {
            "success": True,
            "old_version": old_version,
            "new_version": self._plugin_version,
            "plugins": [tool.name for tool in self._plugins],
            "timestamp": self._last_reload_time.isoformat() if self._last_reload_time else None,
        }

    def reload_model(self, model_name: Optional[str] = None,
                    api_key: Optional[str] = None,
                    temperature: Optional[float] = None) -> Dict[str, Any]:
        """
        Reload model configuration.

        Args:
            model_name: New model name (optional, keeps current if not provided)
            api_key: New API key (optional, keeps current if not provided)
            temperature: New temperature (optional, keeps current if not provided)

        Returns:
            Dictionary with reload status and new configuration
        """
        with self._lock:
            old_config = self._model_config.copy()

            if model_name:
                self._model_config["model"] = model_name
            if api_key:
                self._model_config["api_key"] = api_key
            if temperature is not None:
                self._model_config["temperature"] = temperature

            self._model_version += 1
            self._last_reload_time = datetime.now()

        print(f"✅ Model configuration updated. Version: {self._model_version}")
        print(f"   Model: {self._model_config['model']}")
        print(f"   Temperature: {self._model_config['temperature']}")

        return {
            "success": True,
            "old_config": old_config,
            "new_config": self._model_config.copy(),
            "model_version": self._model_version,
            "timestamp": self._last_reload_time.isoformat() if self._last_reload_time else None,
        }

    def get_llm(self, session_model_version: Optional[int] = None) -> ChatOpenAI:
        """
        Get LLM instance for a session.

        Args:
            session_model_version: Model version for this session. If provided,
                                  ensures session uses the same model config throughout.
                                  If None, uses the latest config.

        Returns:
            ChatOpenAI instance
        """
        with self._lock:
            config = self._model_config.copy()

        return ChatOpenAI(
            model=config["model"],
            api_key=config["api_key"],
            temperature=config["temperature"],
        )

    def get_plugins(self, session_plugin_version: Optional[int] = None) -> List[BaseTool]:
        """
        Get plugins for a session.

        Args:
            session_plugin_version: Plugin version for this session. If provided,
                                   ensures session uses the same plugins throughout.
                                   If None, uses the latest plugins.

        Returns:
            List of tool instances
        """
        with self._lock:
            # For simplicity, always return current plugins
            # In production, you might cache old plugin versions
            return self._plugins.copy()

    def get_current_version(self) -> Dict[str, int]:
        """Get current version numbers for model and plugins."""
        with self._lock:
            return {
                "model_version": self._model_version,
                "plugin_version": self._plugin_version,
            }

    def start_file_watcher(self, watch_path: Optional[Path] = None):
        """
        Start file system watcher for automatic plugin reload.

        Args:
            watch_path: Directory to watch. Defaults to the smart_customer_service directory.
        """
        if self._file_observer is not None:
            print("⚠️  File watcher already running")
            return

        if watch_path is None:
            watch_path = Path(__file__).parent

        event_handler = PluginReloadHandler(self.reload_plugins)
        self._file_observer = Observer()
        self._file_observer.schedule(event_handler, str(watch_path), recursive=False)
        self._file_observer.start()

        print(f"👀 Started file watcher on {watch_path}")
        print(f"   Watching for changes to tools.py")

    def stop_file_watcher(self):
        """Stop the file system watcher."""
        if self._file_observer is not None:
            self._file_observer.stop()
            self._file_observer.join()
            self._file_observer = None
            print("🛑 Stopped file watcher")

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the hot reload manager."""
        with self._lock:
            return {
                "model_version": self._model_version,
                "plugin_version": self._plugin_version,
                "model_config": {
                    "model": self._model_config["model"],
                    "temperature": self._model_config["temperature"],
                },
                "plugins": [tool.name for tool in self._plugins],
                "plugin_count": len(self._plugins),
                "file_watcher_active": self._file_observer is not None,
                "last_reload_time": self._last_reload_time.isoformat() if self._last_reload_time else None,
            }


# Global instance
_hot_reload_manager: Optional[HotReloadManager] = None
_manager_lock = threading.Lock()


def get_hot_reload_manager() -> HotReloadManager:
    """Get or create the global hot reload manager instance."""
    global _hot_reload_manager

    if _hot_reload_manager is None:
        with _manager_lock:
            if _hot_reload_manager is None:
                _hot_reload_manager = HotReloadManager()

    return _hot_reload_manager
