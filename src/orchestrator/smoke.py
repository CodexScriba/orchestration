"""Provider health verification (smoke tests)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from orchestrator.models import InvocationResult, ProviderAliasConfig, StageTimeoutConfig

if TYPE_CHECKING:
    from orchestrator.dispatcher import Dispatcher


_logger = logging.getLogger(__name__)


class SmokeTester:
    """Runs connectivity and basic response tests for configured providers."""

    def __init__(self, dispatcher: Dispatcher) -> None:
        """Initialize the smoke tester.

        Args:
            dispatcher: A configured Dispatcher instance.
        """
        self.dispatcher = dispatcher

    def run_all(self) -> dict[str, bool]:
        """Run smoke tests for all configured provider aliases.

        Returns:
            Mapping of provider alias to success status.
        """
        results: dict[str, bool] = {}
        # We test all unique aliases found in providers or fallback chains
        aliases: set[str] = {p.alias for p in self.dispatcher.config.providers.values()}
        for chain in self.dispatcher.config.fallback_chains.values():
            for entry in chain:
                aliases.add(entry.alias)

        print(f"Running smoke tests for {len(aliases)} providers...\n")

        for alias in sorted(aliases):
            success = self.run_provider_test(alias)
            results[alias] = success

        print("\n" + "=" * 20)
        print("SMOKE TEST SUMMARY")
        print("=" * 20)
        for alias, ok in results.items():
            status = "✅ PASS" if ok else "❌ FAIL"
            print(f"{alias:.<20} {status}")

        return results

    def run_provider_test(self, alias: str) -> bool:
        """Run a smoke test for a specific provider alias.

        Args:
            alias: Provider alias to test.

        Returns:
            True if the provider responded correctly, False otherwise.
        """
        print(f"Testing {alias}...", end=" ", flush=True)

        # Build a dummy config for testing
        alias_config = ProviderAliasConfig(alias=alias)
        try:
            # Re-using Dispatcher's provider building logic
            provider = self.dispatcher._build_provider(alias, alias_config)
        except Exception as exc:  # noqa: BLE001
            print(f"\n   ❌ Failed to build provider: {exc}")
            return False

        prompt = "Say exactly: hello"
        output_dir = self.dispatcher.repo_root / ".kanban2code" / "tmp" / "smoke" / alias
        output_dir.mkdir(parents=True, exist_ok=True)

        # Smoke test uses a very short timeout
        timeouts = StageTimeoutConfig(wall_seconds=30, idle_seconds=10)

        try:
            invocation = provider.invoke(
                prompt=prompt,
                task_path=Path("smoke_test.md"),  # Dummy path
                output_dir=output_dir,
                timeouts=timeouts,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"\n   ❌ Invocation crashed: {exc}")
            return False

        if not invocation.ok:
            print(f"\n   ❌ Provider error: {invocation.error_message}")
            return False

        # Check if "hello" is in the final message
        if invocation.final_message and "hello" in invocation.final_message.lower():
            print("✅")
            return True

        print(f"\n   ❌ Unexpected response: {invocation.final_message}")
        return False
