"""
auth.py — Whitelist-based access control.

Wrap any handler with @restricted to silently drop messages from users
who are not in config.ALLOWED_USER_IDS.

Usage:
    @restricted
    async def my_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        ...
"""

import logging
from functools import wraps
from typing import Callable

from telegram import Update
from telegram.ext import ContextTypes

from config import ALLOWED_USER_IDS

logger = logging.getLogger(__name__)


def restricted(func: Callable) -> Callable:
    """Decorator: only allow calls from whitelisted Telegram user IDs."""

    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if user is None or user.id not in ALLOWED_USER_IDS:
            uid = user.id if user else "unknown"
            logger.warning("Blocked unauthorised access attempt from user_id=%s", uid)
            # Stay silent — don't reveal the bot exists to strangers.
            return
        return await func(update, context, *args, **kwargs)

    return wrapper
