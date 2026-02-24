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

Hey {first_name}! I'm an AI agent that creates engaging LinkedIn posts from your GitHub repositories.

*Quick Start:*
1️⃣ Add your repos: `/addrepo https://github.com/user/repo`
2️⃣ Set posting time: `/time 09:00`
3️⃣ Generate a post: `/generate`

*Commands:*
• `/addrepo <url>` - Add a GitHub repo (up to 5)
• `/repos` - List connected repos
• `/generate` - Generate a post now
• `/trends` - View current dev trends
• `/insights` - View content insights
• `/stats` - Input post engagement
• `/why` - Explain last post
• `/help` - Show all commands

*How it works:*
1. I fetch trending developer topics from HackerNews
2. I analyze your repos to find matching code
3. I check what content has performed best for you
4. I generate an optimized post connecting trends to your code
5. You approve, and I post to LinkedIn
6. I learn from engagement to improve over time

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

*How It Works:*
I'm a ReAct AI agent that autonomously:
1. Fetches trends from HackerNews (free!)
2. Analyzes your repos for matching content
3. Learns what posts perform best for you
4. Generates optimized LinkedIn posts

*Repository Commands:*
• `/addrepo <url>` - Add a GitHub repo (up to 5)
• `/repos` - List connected repositories
• `/removerepo <url>` - Remove a repository
• `/refresh` - Re-index all repositories

*Scheduling:*
• `/time <HH:MM>` - Set daily post time (24h format)
• `/cleartime` - Disable automatic daily posts

*Content Generation:*
• `/generate` - Generate a post (agent picks best repo + trend)
• `/trends` - View current developer trends
• `/insights` - See what content performs best
• `/why` - Explain the agent's choices
• `/stats <likes> <comments>` - Input post metrics

*LinkedIn:*
• `/auth` - Connect your LinkedIn account
• `/authstatus` - Check LinkedIn connection

*Info:*
• `/status` - View your current configuration
• `/help` - Show this help message

*Approving Posts:*
Reply with: `post` • `yes` • `go` • `ship`

*Learning System:*
After posting, use `/stats 50 10` to report engagement (50 likes, 10 comments). The agent learns which topics, styles, and repos perform best for you!
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
