"""Account rotation manager for Codex auth tokens."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class AccountError(RuntimeError):
    """Raised when account rotation or health checks fail."""


class AccountManager:
    """Rotate Codex auth tokens per task using symlink switching.

    Args:
        pool: Ordered list of account names.
        codex_dir: Path to the Codex config directory (default: ~/.codex).
        current_index: Starting position in the rotation pool.
    """

    def __init__(
        self,
        pool: list[str],
        codex_dir: Path | None = None,
        current_index: int = 0,
    ) -> None:
        self._pool = list(pool)
        self._codex_dir = codex_dir or Path.home() / ".codex"
        self._current_index = current_index % len(pool) if pool else 0
        # task_id -> account name assigned for that task
        self._task_accounts: dict[str, str] = {}

    @property
    def pool(self) -> list[str]:
        """Return a copy of the account pool."""
        return list(self._pool)

    def get_account_for_task(self, task_id: str) -> str:
        """Return the account assigned to a task (same through bounces).

        Args:
            task_id: Unique task identifier.

        Returns:
            Account name assigned to this task.

        Raises:
            AccountError: If no healthy account is available.
        """
        if task_id in self._task_accounts:
            return self._task_accounts[task_id]

        account = self._rotate_and_activate()
        self._task_accounts[task_id] = account
        return account

    def _rotate_and_activate(self) -> str:
        """Try each account in round-robin order until one is healthy.

        Returns:
            Name of the successfully activated account.

        Raises:
            AccountError: If all accounts fail health checks.
        """
        if not self._pool:
            raise AccountError("Account pool is empty.")

        for attempt in range(len(self._pool)):
            index = (self._current_index + attempt) % len(self._pool)
            account = self._pool[index]
            try:
                self._switch_to(account)
                if self._health_check():
                    self._current_index = (index + 1) % len(self._pool)
                    logger.info("Active Codex account: %s", account)
                    return account
                logger.warning("Account %s failed health check, trying next.", account)
            except AccountError as exc:
                logger.warning("Account %s error: %s, trying next.", account, exc)

        raise AccountError(
            f"All accounts in pool failed: {self._pool}"
        )

    def _switch_to(self, account: str) -> None:
        """Symlink ~/.codex/auth.json to the named account file.

        Args:
            account: Account name (filename without .json extension).

        Raises:
            AccountError: If the account file does not exist.
        """
        accounts_dir = self._codex_dir / "accounts"
        target = accounts_dir / f"{account}.json"
        if not target.exists():
            raise AccountError(f"Account file not found: {target}")

        auth_link = self._codex_dir / "auth.json"
        # Force-replace the symlink atomically
        tmp_link = self._codex_dir / "auth.json.tmp"
        tmp_link.unlink(missing_ok=True)
        tmp_link.symlink_to(target)
        tmp_link.replace(auth_link)

        current_file = self._codex_dir / "current"
        current_file.write_text(account, encoding="utf-8")

    def _health_check(self) -> bool:
        """Run `codex login status` and return True if the account is healthy.

        Returns:
            True if the health check indicates the account is logged in.
        """
        try:
            result = subprocess.run(
                ["codex", "login", "status"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            output = (result.stdout + result.stderr).lower()
            if result.returncode == 0:
                return True
            # Some versions print success indicators even with non-zero exit
            for indicator in ("logged in", "authenticated", "active", "valid"):
                if indicator in output:
                    return True
            return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def release_task(self, task_id: str) -> None:
        """Remove the task-to-account mapping after the task completes.

        Args:
            task_id: Unique task identifier.
        """
        self._task_accounts.pop(task_id, None)

    @classmethod
    def from_config_pool(
        cls,
        pool: list[str],
        codex_dir: Path | None = None,
    ) -> AccountManager:
        """Construct from a config-sourced pool list.

        Args:
            pool: Ordered list of account names from config.
            codex_dir: Override Codex config directory.

        Returns:
            Configured AccountManager instance.
        """
        return cls(pool=pool, codex_dir=codex_dir)
