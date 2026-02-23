"""
/time Command

Sets the preferred daily posting time.
"""

import re
from typing import Optional, Tuple

from telegram import Update
from telegram.ext import ContextTypes

from ..config import ConfigStore


# Initialize config store
config_store = ConfigStore()


def parse_time(time_str: str) -> Optional[Tuple[int, int]]:
    """
    Parse time string in HH:MM format.

    Returns:
        Tuple of (hour, minute) or None if invalid
    """
    # Try HH:MM format
    match = re.match(r'^(\d{1,2}):(\d{2})$', time_str.strip())
    if match:
        hour, minute = int(match.group(1)), int(match.group(2))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return (hour, minute)

    # Try H:MM format
    match = re.match(r'^(\d):(\d{2})$', time_str.strip())
    if match:
        hour, minute = int(match.group(1)), int(match.group(2))
        if 0 <= hour <= 9 and 0 <= minute <= 59:
            return (hour, minute)

    return None


def format_time(hour: int, minute: int) -> str:
    """Format time as HH:MM."""
    return f"{hour:02d}:{minute:02d}"


async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /time command.

    Usage: /time HH:MM
    Example: /time 09:00
    """
    chat_id = update.effective_chat.id

    # Check if time was provided
    if not context.args or len(context.args) == 0:
        config = config_store.get(chat_id)
        current_time = config.preferred_time or "Not set"

        await update.message.reply_text(
            f"*Current posting time:* `{current_time}`\n\n"
            "To change it, use:\n"
            "`/time HH:MM`\n\n"
            "Examples:\n"
            "• `/time 09:00` - 9 AM\n"
            "• `/time 14:30` - 2:30 PM\n"
            "• `/time 18:00` - 6 PM",
            parse_mode="Markdown"
        )
        return

    time_str = context.args[0].strip()
    parsed = parse_time(time_str)

    if not parsed:
        await update.message.reply_text(
            "Invalid time format.\n\n"
            "Please use `HH:MM` format (24-hour).\n\n"
            "Examples:\n"
            "• `09:00` - 9 AM\n"
            "• `14:30` - 2:30 PM\n"
            "• `18:00` - 6 PM",
            parse_mode="Markdown"
        )
        return

    hour, minute = parsed
    formatted_time = format_time(hour, minute)

    # Get timezone offset from Telegram user (if available)
    # For now, we'll store the time as-is and handle timezone in scheduler
    user = update.effective_user

    # Save to config
    config_store.update(
        chat_id=chat_id,
        preferred_time=formatted_time
    )

    # Determine AM/PM for friendly message
    if hour < 12:
        period = "AM"
        display_hour = hour if hour > 0 else 12
    elif hour == 12:
        period = "PM"
        display_hour = 12
    else:
        period = "PM"
        display_hour = hour - 12

    await update.message.reply_text(
        f"Daily posting time set to `{formatted_time}` ({display_hour}:{minute:02d} {period})\n\n"
        "I'll send you a draft post at this time each day.\n"
        "You can approve it by replying with `post`, `yes`, `go`, or `ship`.",
        parse_mode="Markdown"
    )


async def clear_time_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /cleartime command.

    Removes the scheduled posting time (disables daily posts).
    """
    chat_id = update.effective_chat.id
    config = config_store.get(chat_id)

    if not config.preferred_time:
        await update.message.reply_text(
            "No posting time is set.\n\n"
            "Use `/time HH:MM` to set one.",
            parse_mode="Markdown"
        )
        return

    old_time = config.preferred_time
    config_store.update(chat_id=chat_id, preferred_time=None)

    await update.message.reply_text(
        f"Cleared posting time (was `{old_time}`).\n\n"
        "Daily automatic posts are now disabled.\n"
        "You can still generate posts manually with `/generate`.",
        parse_mode="Markdown"
    )
