"""
LinkedIn AI Content Agent - Telegram Bot

Main entry point for the Telegram bot.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from bot.handlers import (
    start_command,
    help_command,
    handle_message,
    error_handler,
)
from bot.commands.connect import (
    connect_command,
    disconnect_command,
    status_command,
)
from bot.commands.time import (
    time_command,
    clear_time_command,
)
from bot.commands.generate import (
    generate_command,
    refresh_command,
)
from bot.commands.auth import (
    auth_command,
    authcode_command,
    authstatus_command,
    deauth_command,
)
from bot.commands.repos import (
    repos_command,
    addrepo_command,
    removerepo_command,
)
from bot.commands.insights import (
    insights_command,
    trends_command,
    why_command,
    stats_command,
)
from scheduler.cron import post_scheduler
from bot.approval import generate_scheduled_post
from bot.config import ConfigStore


# Config store for scheduler
config_store = ConfigStore()


async def scheduled_post_callback(chat_id: int) -> None:
    """
    Callback for scheduled posts.

    Args:
        chat_id: Telegram chat ID
    """
    # Get bot from the scheduler's application context
    # This will be set when the bot starts
    if hasattr(scheduled_post_callback, 'bot'):
        await generate_scheduled_post(
            chat_id=chat_id,
            bot=scheduled_post_callback.bot,
            config_store=config_store
        )


async def post_init(application) -> None:
    """Called after the application is initialized and event loop is running."""
    post_scheduler.set_post_callback(scheduled_post_callback)
    post_scheduler.start()
    print("\nScheduler active for daily posts.")


def main() -> None:
    """
    Start the Telegram bot.
    """
    # Load environment variables
    load_dotenv()

    # Get bot token
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not found in environment variables.")
        print("Please add it to your .env file:")
        print("  TELEGRAM_BOT_TOKEN=your_bot_token_here")
        print("\nGet a token from @BotFather on Telegram.")
        sys.exit(1)

    # Create application
    print("Starting LinkedIn AI Content Agent bot...")
    application = Application.builder().token(token).post_init(post_init).build()

    # Store bot reference for scheduler
    scheduled_post_callback.bot = application.bot

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))

    # Setup commands
    application.add_handler(CommandHandler("connect", connect_command))
    application.add_handler(CommandHandler("disconnect", disconnect_command))
    application.add_handler(CommandHandler("status", status_command))

    # Time commands
    application.add_handler(CommandHandler("time", time_command))
    application.add_handler(CommandHandler("cleartime", clear_time_command))

    # Content commands
    application.add_handler(CommandHandler("generate", generate_command))
    application.add_handler(CommandHandler("refresh", refresh_command))

    # LinkedIn auth commands
    application.add_handler(CommandHandler("auth", auth_command))
    application.add_handler(CommandHandler("authcode", authcode_command))
    application.add_handler(CommandHandler("authstatus", authstatus_command))
    application.add_handler(CommandHandler("deauth", deauth_command))

    # Repository management commands (Agent Phase 4)
    application.add_handler(CommandHandler("repos", repos_command))
    application.add_handler(CommandHandler("addrepo", addrepo_command))
    application.add_handler(CommandHandler("removerepo", removerepo_command))

    # Agent insight commands (Agent Phase 4)
    application.add_handler(CommandHandler("insights", insights_command))
    application.add_handler(CommandHandler("trends", trends_command))
    application.add_handler(CommandHandler("why", why_command))
    application.add_handler(CommandHandler("stats", stats_command))

    # Message handler (for approvals and other text)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Error handler
    application.add_error_handler(error_handler)

    # Start the bot
    print("Bot is running! Press Ctrl+C to stop.")
    print("\nAvailable commands:")
    print("  /start       - Welcome message")
    print("  /addrepo     - Add GitHub repo (up to 5)")
    print("  /repos       - List repositories")
    print("  /removerepo  - Remove a repository")
    print("  /time        - Set posting time")
    print("  /generate    - Generate a post (with AI agent)")
    print("  /trends      - View current trends")
    print("  /insights    - View content insights")
    print("  /why         - Explain last post")
    print("  /stats       - Input post metrics manually")
    print("  /refresh     - Re-index repository")
    print("  /auth        - Connect LinkedIn")
    print("  /authstatus  - Check LinkedIn status")
    print("  /status      - View configuration")
    print("  /help        - Show help")

    try:
        application.run_polling(allowed_updates=["message"])
    finally:
        post_scheduler.stop()


if __name__ == "__main__":
    main()
