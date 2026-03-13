"""Abstract provider interface used by the execution engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from orchestrator.models import InvocationResult, StageTimeoutConfig


class ProviderError(RuntimeError):
    """Raised when a provider cannot be configured or invoked."""


class BaseProvider(ABC):
    """Abstract base class for provider runtimes."""

    @abstractmethod
    def invoke(
        self,
        prompt: str,
        task_path: Path,
        output_dir: Path,
        timeouts: StageTimeoutConfig,
    ) -> InvocationResult:
        """Invoke the provider for a single stage."""
