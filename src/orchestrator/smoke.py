"""Provider health verification (smoke tests)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from orchestrator.models import InvocationResult, ProviderAliasConfig, StageTimeoutConfig
from orchestrator.scanner import split_frontmatter

if TYPE_CHECKING:
    from orchestrator.dispatcher import Dispatcher


_logger = logging.getLogger(__name__)

# The four provider families that must always be verified.
REQUIRED_FAMILIES = ("codex", "claude", "gemini", "qwen")

# Maps provider metadata fields (provider type / cli) to family names.
_CLI_TO_FAMILY: dict[str, str] = {
    "codex": "codex",
    "claude": "claude",
    "gemini": "gemini",
    "kimi": "qwen",
    "kilo": "qwen",
}

_PROVIDER_TYPE_TO_FAMILY: dict[str, str] = {
    "openai": "codex",
    "codex": "codex",
    "anthropic": "claude",
    "google": "gemini",
    "moonshot": "qwen",
    "zai": "qwen",
}


def _resolve_family_for_alias(alias: str, provider_dir: Path) -> str | None:
    """Determine which provider family an alias belongs to.

    Reads the provider's frontmatter metadata file to inspect the
    ``provider`` and ``cli`` fields — the same logic used by
    ``Dispatcher._build_provider``.

    Args:
        alias: Provider alias name.
        provider_dir: Path to the ``_providers/`` directory.

    Returns:
        Family name (one of :data:`REQUIRED_FAMILIES`), or ``None``.
    """
    config_path = provider_dir / f"{alias}.md"
    if not config_path.exists():
        # Fall back to substring matching on the alias itself
        alias_lower = alias.lower()
        for key, family in _CLI_TO_FAMILY.items():
            if key in alias_lower:
                return family
        return None

    try:
        metadata, _ = split_frontmatter(config_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None

    provider_type = str(metadata.get("provider", "")).strip().lower()
    cli = str(metadata.get("cli", "")).strip().lower()

    if provider_type in _PROVIDER_TYPE_TO_FAMILY:
        return _PROVIDER_TYPE_TO_FAMILY[provider_type]
    if cli in _CLI_TO_FAMILY:
        return _CLI_TO_FAMILY[cli]
    return None


class SmokeTester:
    """Runs connectivity and basic response tests for configured providers."""

    def __init__(self, dispatcher: Dispatcher) -> None:
        """Initialize the smoke tester.

        Args:
            dispatcher: A configured Dispatcher instance.
        """
        self.dispatcher = dispatcher
        self._provider_dir = dispatcher.repo_root / ".kanban2code" / "_providers"

    def run_all(self) -> dict[str, bool]:
        """Run smoke tests for all configured provider aliases.

        Ensures that at least one alias per required family (Codex, Claude,
        Gemini, Qwen) is tested, in addition to any other configured aliases.

        Returns:
            Mapping of provider alias to success status.
        """
        results: dict[str, bool] = {}

        # Collect all unique aliases found in providers or fallback chains,
        # preserving the configured ProviderAliasConfig for each.
        alias_configs: dict[str, ProviderAliasConfig] = {}
        for pac in self.dispatcher.config.providers.values():
            alias_configs.setdefault(pac.alias, pac)
        for chain in self.dispatcher.config.fallback_chains.values():
            for entry in chain:
                alias_configs.setdefault(
                    entry.alias,
                    ProviderAliasConfig(
                        alias=entry.alias,
                        model=entry.model,
                        config_overrides=dict(entry.config_overrides),
                    ),
                )

        # Build family → alias mapping from provider metadata.
        family_to_aliases: dict[str, list[str]] = {f: [] for f in REQUIRED_FAMILIES}
        for alias in alias_configs:
            family = _resolve_family_for_alias(alias, self._provider_dir)
            if family and family in family_to_aliases:
                family_to_aliases[family].append(alias)

        # Ensure every required family has at least one alias to test.
        # If a family has no configured alias, scan the _providers dir for one.
        for family in REQUIRED_FAMILIES:
            if not family_to_aliases[family]:
                discovered = self._discover_alias_for_family(family)
                if discovered:
                    alias_configs.setdefault(
                        discovered, ProviderAliasConfig(alias=discovered)
                    )
                    family_to_aliases[family].append(discovered)
                else:
                    _logger.warning("No provider alias found for family %r", family)

        all_aliases = sorted(alias_configs)
        print(f"Running smoke tests for {len(all_aliases)} providers...\n")

        for alias in all_aliases:
            success = self.run_provider_test(alias, alias_configs[alias])
            results[alias] = success

        print("\n" + "=" * 20)
        print("SMOKE TEST SUMMARY")
        print("=" * 20)
        for alias, ok in results.items():
            status = "✅ PASS" if ok else "❌ FAIL"
            print(f"{alias:.<20} {status}")

        # Per-family summary
        print("\nPer-family coverage:")
        for family in REQUIRED_FAMILIES:
            family_aliases = family_to_aliases[family]
            tested = [a for a in family_aliases if a in results]
            if tested:
                ok = any(results[a] for a in tested)
                status = "✅ PASS" if ok else "❌ FAIL"
                print(f"  {family:.<16} {status} ({', '.join(tested)})")
            else:
                print(f"  {family:.<16} ❌ NOT CONFIGURED")

        return results

    def _discover_alias_for_family(self, family: str) -> str | None:
        """Scan the _providers directory for an alias matching a family.

        Args:
            family: Required family name.

        Returns:
            An alias name, or None if nothing found.
        """
        if not self._provider_dir.is_dir():
            return None
        for md_file in sorted(self._provider_dir.glob("*.md")):
            alias = md_file.stem
            if _resolve_family_for_alias(alias, self._provider_dir) == family:
                return alias
        return None

    def run_provider_test(
        self, alias: str, alias_config: ProviderAliasConfig | None = None
    ) -> bool:
        """Run a smoke test for a specific provider alias.

        Args:
            alias: Provider alias to test.
            alias_config: Optional configured alias config to preserve
                model and override settings.

        Returns:
            True if the provider responded correctly, False otherwise.
        """
        print(f"Testing {alias}...", end=" ", flush=True)

        config = alias_config or ProviderAliasConfig(alias=alias)
        try:
            provider = self.dispatcher._build_provider(alias, config)
        except Exception as exc:  # noqa: BLE001
            print(f"\n   ❌ Failed to build provider: {exc}")
            return False

        prompt = "Say exactly: hello"
        output_dir = self.dispatcher.repo_root / ".kanban2code" / "tmp" / "smoke" / alias
        output_dir.mkdir(parents=True, exist_ok=True)

        timeouts = StageTimeoutConfig(wall_seconds=30, idle_seconds=10)

        try:
            invocation = provider.invoke(
                prompt=prompt,
                task_path=Path("smoke_test.md"),
                output_dir=output_dir,
                timeouts=timeouts,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"\n   ❌ Invocation crashed: {exc}")
            return False

        if not invocation.ok:
            print(f"\n   ❌ Provider error: {invocation.error_message}")
            return False

        if invocation.final_message and "hello" in invocation.final_message.lower():
            print("✅")
            return True

        print(f"\n   ❌ Unexpected response: {invocation.final_message}")
        return False
