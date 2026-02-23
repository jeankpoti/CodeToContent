"""
/connect Command

Connects a GitHub repository for content generation.
"""

import re
from telegram import Update
from telegram.ext import ContextTypes

from ..config import ConfigStore


# Initialize config store
config_store = ConfigStore()


def is_valid_github_url(url: str) -> bool:
    """Validate GitHub repository URL."""
    pattern = r'^https://github\.com/[\w\-\.]+/[\w\-\.]+/?$'
    return bool(re.match(pattern, url))


async def connect_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /connect command.

    Usage: /connect https://github.com/user/repo
    """
    chat_id = update.effective_chat.id

    # Check if URL was provided
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "Please provide a GitHub repository URL.\n\n"
            "Usage: `/connect https://github.com/username/repo`",
            parse_mode="Markdown"
        )
        return

    github_url = context.args[0].strip()

    # Validate URL
    if not is_valid_github_url(github_url):
        await update.message.reply_text(
            "Invalid GitHub URL format.\n\n"
            "Please use: `https://github.com/username/repo`",
            parse_mode="Markdown"
        )
        return

    # Check if it's a public repo (basic check - just ensure URL is accessible)
    # For MVP, we assume public repos only

    # Save to config
    config = config_store.update(
        chat_id=chat_id,
        github_url=github_url
    )

    await update.message.reply_text(
        f"Connected to repository:\n`{github_url}`\n\n"
        "Next steps:\n"
        "1. Set your preferred posting time with `/time HH:MM`\n"
        "2. Generate a test post with `/generate`\n"
        "3. Connect LinkedIn with `/auth` (coming soon)",
        parse_mode="Markdown"
    )


async def disconnect_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /disconnect command.

    Removes the connected repository.
    """
    chat_id = update.effective_chat.id
    config = config_store.get(chat_id)

    if not config.github_url:
        await update.message.reply_text(
            "No repository connected.\n\n"
            "Use `/connect https://github.com/user/repo` to connect one.",
            parse_mode="Markdown"
        )
        return

    old_url = config.github_url
    config_store.update(chat_id=chat_id, github_url=None)

    await update.message.reply_text(
        f"Disconnected from:\n`{old_url}`\n\n"
        "Use `/connect` to connect a new repository.",
        parse_mode="Markdown"
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /status command.

    Shows current configuration status.
    """
    chat_id = update.effective_chat.id
    config = config_store.get(chat_id)

    # Build status message
    status_lines = ["*Your Configuration:*\n"]

    # GitHub
    if config.github_url:
        status_lines.append(f"GitHub: `{config.github_url}`")
    else:
        status_lines.append("GitHub: Not connected")

    # Posting time
    if config.preferred_time:
        status_lines.append(f"Daily post time: `{config.preferred_time}`")
    else:
        status_lines.append("Daily post time: Not set")

    # LinkedIn
    if config.is_linkedin_connected():
        status_lines.append("LinkedIn: Connected")
    else:
        status_lines.append("LinkedIn: Not connected")

    # Ready status
    status_lines.append("")
    if config.is_configured():
        status_lines.append("Ready to generate posts with `/generate`")
    else:
        status_lines.append("Connect a repo with `/connect` to get started")

    await update.message.reply_text(
        "\n".join(status_lines),
        parse_mode="Markdown"
    )
