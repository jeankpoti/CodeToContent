"""
Telegram Bot Handlers

Main message and command handlers for the bot.
"""

from telegram import Update
from telegram.ext import ContextTypes

from .config import ConfigStore
from .approval import is_approval_message, handle_approval


# Initialize config store
config_store = ConfigStore()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command.

    Welcome message and instructions.
    """
    user = update.effective_user
    first_name = user.first_name if user else "there"

    welcome_message = f"""
*Welcome to LinkedIn AI Content Agent!*

Hey {first_name}! I help you create engaging LinkedIn posts from your GitHub repositories.

*Quick Start:*
1️⃣ Connect your repo: `/connect https://github.com/user/repo`
2️⃣ Set posting time: `/time 09:00`
3️⃣ Generate a post: `/generate`

*Commands:*
• `/connect <url>` - Connect a GitHub repo
• `/disconnect` - Remove connected repo
• `/time <HH:MM>` - Set daily posting time
• `/cleartime` - Disable daily posts
• `/generate` - Generate a post now
• `/refresh` - Re-index your repository
• `/status` - View your configuration
• `/help` - Show this help message

*How it works:*
I analyze your code and recent commits to write authentic LinkedIn posts about your work. You approve each post before it goes live.

Let's get started!
    """

    await update.message.reply_text(
        welcome_message.strip(),
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /help command.

    Shows available commands and usage.
    """
    help_message = """
*LinkedIn AI Content Agent - Help*

*Setup Commands:*
• `/connect <url>` - Connect a public GitHub repo
• `/disconnect` - Remove connected repo
• `/time <HH:MM>` - Set daily post time (24h format)
• `/cleartime` - Disable automatic daily posts

*Content Commands:*
• `/generate` - Generate a LinkedIn post now
• `/refresh` - Re-index your repository

*Info Commands:*
• `/status` - View your current configuration
• `/help` - Show this help message

*Approving Posts:*
When I send you a draft, reply with any of these to publish:
• `post` • `yes` • `go` • `ship` • `publish` • `send`

*Tips:*
• Posts are based on your recent commits when available
• If no recent commits, I'll highlight interesting code
• Each post includes relevant code snippets
• Posts adapt their length to the content

*Questions or issues?*
Check out the project: github.com/your-repo/linkedin-ai-agent
    """

    await update.message.reply_text(
        help_message.strip(),
        parse_mode="Markdown"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle regular text messages.

    Checks for approval keywords and pending posts.
    """
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    # Check for approval message
    if is_approval_message(text):
        await handle_approval(update, context)
        return

    # Default response for unrecognized messages
    await update.message.reply_text(
        "I didn't understand that.\n\n"
        "Use `/help` to see available commands, or `/generate` to create a post.",
        parse_mode="Markdown"
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle errors in the bot.

    Logs the error and notifies the user.
    """
    print(f"Error: {context.error}")

    if update and update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Oops! Something went wrong.\n\n"
                 "Please try again or use `/help` for assistance.",
            parse_mode="Markdown"
        )
