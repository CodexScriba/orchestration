"""Telegram notification delivery for orchestrator events."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import TYPE_CHECKING

from telegram import Bot
from telegram.error import TelegramError

if TYPE_CHECKING:
    from orchestrator.models import OrchestratorConfig, StageResult


_logger = logging.getLogger(__name__)


class Notifier:
    """Delivers notifications to Telegram."""

    def __init__(self, config: OrchestratorConfig) -> None:
        """Initialize the notifier with orchestrator configuration.

        Args:
            config: Orchestrator configuration containing notification settings.
        """
        self._config = config.notifications.telegram
        self._bot_token = os.environ.get(self._config.bot_token_env_var)
        self._chat_id = os.environ.get(self._config.chat_id_env_var)
        self._enabled = self._config.enabled and bool(self._bot_token) and bool(self._chat_id)

        if self._config.enabled and not self._enabled:
            _logger.warning(
                "Telegram notifications enabled but credentials missing (env vars: %s, %s)",
                self._config.bot_token_env_var,
                self._config.chat_id_env_var,
            )

    def notify_stage_change(self, result: StageResult) -> None:
        """Send a notification for a successful stage change.

        Args:
            result: The result of the stage execution.
        """
        if not self._enabled:
            return

        message = (
            f"✅ *Stage Change*: `{result.task_id}`\n"
            f"🔄 `{result.before_stage}` → `{result.after_stage}`\n"
            f"🤖 Agent: `{result.after_agent}`\n"
            f"🛠 Provider: `{result.provider_alias}` ({result.provider_model or 'default'})"
        )
        self._send_message(message)

    def notify_escalation(self, task_id: str, state: str, reason: str) -> None:
        """Send a notification for a task escalation or block.

        Args:
            task_id: Identifier of the task.
            state: The new state (e.g., 'blocked', 'handoff_required').
            reason: The reason for the escalation.
        """
        if not self._enabled:
            return

        emoji = "⚠️" if state == "blocked" else "🚨"
        message = (
            f"{emoji} *Escalation*: `{task_id}`\n"
            f"📌 State: `{state}`\n"
            f"📝 Reason: {reason}"
        )
        self._send_message(message)

    def _send_message(self, text: str) -> None:
        """Send a message to the configured Telegram chat.

        Args:
            text: Markdown-formatted message text.
        """
        if not self._bot_token or not self._chat_id:
            return

        async def _async_send():
            bot = Bot(token=self._bot_token)
            async with bot:
                await bot.send_message(
                    chat_id=self._chat_id,
                    text=text,
                    parse_mode="Markdown",
                )

        try:
            # Using asyncio.run to call the async send_message from sync code.
            # In a highly concurrent environment, this might need a dedicated loop thread.
            asyncio.run(_async_send())
        except (TelegramError, RuntimeError) as exc:
            _logger.error("Failed to send Telegram notification: %s", exc)
