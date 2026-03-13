"""Public package exports for the orchestration scaffold."""

from __future__ import annotations

from orchestrator.config import ConfigError, load_config
from orchestrator.models import OrchestratorConfig
from orchestrator.dispatcher import Dispatcher

__all__ = ["__version__", "ConfigError", "Dispatcher", "OrchestratorConfig", "load_config"]

__version__ = "0.1.0"
