"""
bot.py — TermiHub entry point.

Builds the Telegram Application, registers all command handlers,
and starts polling. Run via start.sh (which loads the .env file first).

python-telegram-bot v20+ uses a fully async Application pattern.
The Application polls Telegram's servers continuously; no webhook
or open port is needed on the phone.
"""

import logging

from telegram import BotCommand, Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes

import config  # noqa: F401 — imported early so missing env vars fail fast
from auth import restricted
from handlers.phone import battery, ip, ram, storage, temperature, uptime, wifi

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ── /start ────────────────────────────────────────────────────────────────────

@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        f"👋 *{config.BOT_NAME}* is online.\n\n"
        "*Phone commands*\n"
        "/battery — charge level & health\n"
        "/storage — internal storage usage\n"
        "/ram — memory usage\n"
        "/temperature — battery & CPU temps\n"
        "/uptime — time since last reboot\n"
        "/ip — local Wi-Fi IP address\n"
        "/wifi — Wi-Fi SSID & signal\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ── /help ─────────────────────────────────────────────────────────────────────

@restricted
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)


# ── Bot command menu (shown in Telegram's / menu) ────────────────────────────

BOT_COMMANDS = [
    BotCommand("start", "Show help"),
    BotCommand("battery", "Charge level & health"),
    BotCommand("storage", "Internal storage usage"),
    BotCommand("ram", "Memory usage"),
    BotCommand("temperature", "Battery & CPU temperatures"),
    BotCommand("uptime", "Time since last reboot"),
    BotCommand("ip", "Local Wi-Fi IP address"),
    BotCommand("wifi", "Wi-Fi SSID & signal strength"),
]


async def _post_init(application: Application) -> None:
    """Runs once after the bot connects — registers the command menu."""
    await application.bot.set_my_commands(BOT_COMMANDS)
    logger.info("%s started. Allowed user IDs: %s", config.BOT_NAME, config.ALLOWED_USER_IDS)


# ── Wire everything together ─────────────────────────────────────────────────

def main() -> None:
    app = (
        ApplicationBuilder()
        .token(config.BOT_TOKEN)
        .post_init(_post_init)
        .build()
    )

    # Register handlers — order matters: more specific patterns first.
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("battery", battery))
    app.add_handler(CommandHandler("storage", storage))
    app.add_handler(CommandHandler("ram", ram))
    app.add_handler(CommandHandler("temperature", temperature))
    app.add_handler(CommandHandler("uptime", uptime))
    app.add_handler(CommandHandler("ip", ip))
    app.add_handler(CommandHandler("wifi", wifi))

    logger.info("Starting polling...")
    # run_polling blocks until Ctrl-C / SIGTERM
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
