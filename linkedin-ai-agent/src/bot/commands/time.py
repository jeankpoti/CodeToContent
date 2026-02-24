"""
/time and /timezone Commands

Sets the preferred daily posting time and timezone.
"""

import re
from typing import Optional, Tuple
from zoneinfo import ZoneInfo, available_timezones

from telegram import Update
from telegram.ext import ContextTypes

from ..config import ConfigStore


# Initialize config store
config_store = ConfigStore()

# Common timezone aliases for easier input
TIMEZONE_ALIASES = {
    # UTC offsets
    "utc": "UTC",
    "utc+0": "UTC",
    "utc+1": "Africa/Lagos",
    "utc+2": "Africa/Cairo",
    "utc+3": "Africa/Nairobi",
    "utc+4": "Asia/Dubai",
    "utc+5": "Asia/Karachi",
    "utc+5:30": "Asia/Kolkata",
    "utc+6": "Asia/Dhaka",
    "utc+7": "Asia/Bangkok",
    "utc+8": "Asia/Singapore",
    "utc+9": "Asia/Tokyo",
    "utc+10": "Australia/Sydney",
    "utc+11": "Pacific/Noumea",
    "utc+12": "Pacific/Auckland",
    "utc-1": "Atlantic/Azores",
    "utc-2": "Atlantic/South_Georgia",
    "utc-3": "America/Sao_Paulo",
    "utc-4": "America/New_York",
    "utc-5": "America/Chicago",
    "utc-6": "America/Denver",
    "utc-7": "America/Los_Angeles",
    "utc-8": "America/Anchorage",
    "utc-9": "America/Adak",
    "utc-10": "Pacific/Honolulu",
    # Common city names
    "lagos": "Africa/Lagos",
    "london": "Europe/London",
    "paris": "Europe/Paris",
    "berlin": "Europe/Berlin",
    "moscow": "Europe/Moscow",
    "dubai": "Asia/Dubai",
    "mumbai": "Asia/Kolkata",
    "singapore": "Asia/Singapore",
    "tokyo": "Asia/Tokyo",
    "sydney": "Australia/Sydney",
    "new_york": "America/New_York",
    "newyork": "America/New_York",
    "chicago": "America/Chicago",
    "denver": "America/Denver",
    "los_angeles": "America/Los_Angeles",
    "la": "America/Los_Angeles",
    "sf": "America/Los_Angeles",
    "seattle": "America/Los_Angeles",
}


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


def resolve_timezone(tz_input: str) -> Optional[str]:
    """
    Resolve a timezone input to a valid IANA timezone name.

    Args:
        tz_input: User input (e.g., "Lagos", "UTC+1", "Africa/Lagos")

    Returns:
        Valid IANA timezone name or None if invalid
    """
    tz_input = tz_input.strip().lower().replace(" ", "_")

    # Check aliases first
    if tz_input in TIMEZONE_ALIASES:
        return TIMEZONE_ALIASES[tz_input]

    # Check if it's a valid IANA timezone (case-insensitive search)
    all_timezones = available_timezones()
    for tz in all_timezones:
        if tz.lower() == tz_input:
            return tz

    # Partial match (e.g., "lagos" -> "Africa/Lagos")
    for tz in all_timezones:
        if tz_input in tz.lower():
            return tz

    return None


def get_timezone_display(tz_name: str) -> str:
    """Get a friendly display string for a timezone."""
    try:
        from datetime import datetime
        tz = ZoneInfo(tz_name)
        now = datetime.now(tz)
        offset = now.strftime("%z")
        # Format offset as UTC+X or UTC-X
        offset_str = f"UTC{offset[:3]}:{offset[3:]}" if offset else "UTC"
        return f"{tz_name} ({offset_str})"
    except:
        return tz_name


async def timezone_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /timezone command.

    Usage: /timezone <timezone>
    Examples: /timezone Lagos, /timezone UTC+1, /timezone America/New_York
    """
    chat_id = update.effective_chat.id
    config = config_store.get(chat_id)

    # No arguments - show current timezone
    if not context.args or len(context.args) == 0:
        current_tz = config.timezone or "Not set (using server timezone)"
        display = get_timezone_display(config.timezone) if config.timezone else current_tz

        await update.message.reply_text(
            f"*Current timezone:* `{display}`\n\n"
            "*To change it, use:*\n"
            "`/timezone <timezone>`\n\n"
            "*Examples:*\n"
            "• `/timezone Lagos`\n"
            "• `/timezone UTC+1`\n"
            "• `/timezone America/New_York`\n"
            "• `/timezone Europe/London`\n"
            "• `/timezone Asia/Tokyo`\n\n"
            "_Your scheduled posts will trigger at your local time._",
            parse_mode="Markdown"
        )
        return

    # Parse timezone input
    tz_input = " ".join(context.args)
    resolved_tz = resolve_timezone(tz_input)

    if not resolved_tz:
        await update.message.reply_text(
            f"Could not find timezone: `{tz_input}`\n\n"
            "*Try one of these formats:*\n"
            "• City name: `Lagos`, `London`, `Tokyo`\n"
            "• UTC offset: `UTC+1`, `UTC-5`\n"
            "• Full name: `Africa/Lagos`, `America/New_York`\n\n"
            "_Tip: Search for your city name or use UTC offset._",
            parse_mode="Markdown"
        )
        return

    # Save timezone
    config_store.update(chat_id=chat_id, timezone=resolved_tz)
    display = get_timezone_display(resolved_tz)

    # Build response
    response = f"*Timezone set to:* `{display}`\n\n"

    if config.preferred_time:
        response += f"Your daily posts will now trigger at `{config.preferred_time}` in your local time."
    else:
        response += "Use `/time HH:MM` to set your daily posting time."

    await update.message.reply_text(response, parse_mode="Markdown")
