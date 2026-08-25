"""
config.py — Central configuration for TermiHub.

Values are read from environment variables so no secrets ever live in source
code. Set them in ~/.termihub.env (loaded by start.sh) or export them
manually in your Termux session.

Required env vars:
  TERMIHUB_BOT_TOKEN      — token from @BotFather
  TERMIHUB_ALLOWED_IDS    — comma-separated numeric Telegram user IDs
                            e.g. "123456789" or "123456789,987654321"

Optional env vars:
  TERMIHUB_CMD_TIMEOUT    — seconds before a shell command is killed (default 10)
  TERMIHUB_BOT_NAME       — friendly name used in messages (default "TermiHub")
"""

import os


def _require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}\n"
            "Copy .env.example to .termihub.env, fill in your values, then run start.sh"
        )
    return value


def _parse_ids(raw: str) -> set[int]:
    ids: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if part:
            try:
                ids.add(int(part))
            except ValueError:
                raise RuntimeError(
                    f"TERMIHUB_ALLOWED_IDS contains a non-integer value: {part!r}"
                )
    if not ids:
        raise RuntimeError("TERMIHUB_ALLOWED_IDS must contain at least one user ID")
    return ids


# ── Resolved values ───────────────────────────────────────────────────────────

BOT_TOKEN: str = _require("TERMIHUB_BOT_TOKEN")
ALLOWED_USER_IDS: set[int] = _parse_ids(_require("TERMIHUB_ALLOWED_IDS"))
COMMAND_TIMEOUT: int = int(os.environ.get("TERMIHUB_CMD_TIMEOUT", "10"))
BOT_NAME: str = os.environ.get("TERMIHUB_BOT_NAME", "TermiHub")
