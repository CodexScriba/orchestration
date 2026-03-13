from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from orchestrator.accounts import AccountError, AccountManager


def _make_accounts_dir(tmp_path: Path, accounts: list[str]) -> Path:
    codex_dir = tmp_path / ".codex"
    accounts_dir = codex_dir / "accounts"
    accounts_dir.mkdir(parents=True)
    for name in accounts:
        (accounts_dir / f"{name}.json").write_text(
            json.dumps({"account": name}), encoding="utf-8"
        )
    return codex_dir


def test_account_rotation_picks_accounts_in_pool_order(tmp_path: Path) -> None:
    codex_dir = _make_accounts_dir(tmp_path, ["alpha", "beta", "gamma"])
    manager = AccountManager(pool=["alpha", "beta", "gamma"], codex_dir=codex_dir)

    with patch.object(manager, "_health_check", return_value=True):
        a1 = manager.get_account_for_task("task-1")
        a2 = manager.get_account_for_task("task-2")
        a3 = manager.get_account_for_task("task-3")

    assert a1 == "alpha"
    assert a2 == "beta"
    assert a3 == "gamma"


def test_same_account_persists_through_bounces(tmp_path: Path) -> None:
    codex_dir = _make_accounts_dir(tmp_path, ["alpha", "beta"])
    manager = AccountManager(pool=["alpha", "beta"], codex_dir=codex_dir)

    with patch.object(manager, "_health_check", return_value=True):
        first = manager.get_account_for_task("task-bounce")
        second = manager.get_account_for_task("task-bounce")

    assert first == second


def test_failed_account_triggers_fallback_to_next(tmp_path: Path) -> None:
    codex_dir = _make_accounts_dir(tmp_path, ["bad", "good"])
    manager = AccountManager(pool=["bad", "good"], codex_dir=codex_dir)

    health_results = {"bad": False, "good": True}

    def fake_health(self=manager) -> bool:
        current = (codex_dir / "current").read_text(encoding="utf-8").strip()
        return health_results[current]

    with patch.object(manager, "_health_check", side_effect=fake_health):
        account = manager.get_account_for_task("task-fallback")

    assert account == "good"


def test_all_accounts_failing_raises_account_error(tmp_path: Path) -> None:
    codex_dir = _make_accounts_dir(tmp_path, ["a", "b"])
    manager = AccountManager(pool=["a", "b"], codex_dir=codex_dir)

    with patch.object(manager, "_health_check", return_value=False):
        with pytest.raises(AccountError, match="All accounts in pool failed"):
            manager.get_account_for_task("task-all-fail")


def test_health_check_parses_codex_login_status_output(tmp_path: Path) -> None:
    codex_dir = _make_accounts_dir(tmp_path, ["me"])
    manager = AccountManager(pool=["me"], codex_dir=codex_dir)

    import subprocess

    # Simulate successful exit code
    with patch("orchestrator.accounts.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["codex", "login", "status"],
            returncode=0,
            stdout="Logged in as user@example.com",
            stderr="",
        )
        assert manager._health_check() is True

    # Simulate failure with no success indicator
    with patch("orchestrator.accounts.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["codex", "login", "status"],
            returncode=1,
            stdout="Error: session expired",
            stderr="",
        )
        assert manager._health_check() is False

    # Simulate success indicator in output despite non-zero exit
    with patch("orchestrator.accounts.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["codex", "login", "status"],
            returncode=1,
            stdout="authenticated as admin",
            stderr="",
        )
        assert manager._health_check() is True


def test_account_symlink_is_created_on_switch(tmp_path: Path) -> None:
    codex_dir = _make_accounts_dir(tmp_path, ["target"])
    manager = AccountManager(pool=["target"], codex_dir=codex_dir)

    manager._switch_to("target")

    auth_link = codex_dir / "auth.json"
    assert auth_link.exists()
    assert auth_link.is_symlink() or auth_link.exists()
    current = (codex_dir / "current").read_text(encoding="utf-8").strip()
    assert current == "target"


def test_missing_account_file_raises_account_error(tmp_path: Path) -> None:
    codex_dir = tmp_path / ".codex"
    (codex_dir / "accounts").mkdir(parents=True)
    manager = AccountManager(pool=["nonexistent"], codex_dir=codex_dir)

    with pytest.raises(AccountError, match="Account file not found"):
        manager._switch_to("nonexistent")


def test_release_task_removes_mapping(tmp_path: Path) -> None:
    codex_dir = _make_accounts_dir(tmp_path, ["alpha"])
    manager = AccountManager(pool=["alpha"], codex_dir=codex_dir)

    with patch.object(manager, "_health_check", return_value=True):
        manager.get_account_for_task("task-x")

    assert "task-x" in manager._task_accounts
    manager.release_task("task-x")
    assert "task-x" not in manager._task_accounts
