"""
Post Approval Handler

Handles approval flow and LinkedIn posting.
"""

import sys
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from .config import ConfigStore
from linkedin.poster import linkedin_poster


# Initialize config store
config_store = ConfigStore()

# Approval keywords
APPROVAL_KEYWORDS = {"post", "yes", "go", "ship", "publish", "send"}


def is_approval_message(text: str) -> bool:
    """
    Check if a message is an approval command.

    Args:
        text: Message text

    Returns:
        True if this is an approval
    """
    text = text.strip().lower()

    # Exact match
    if text in APPROVAL_KEYWORDS:
        return True

    # Partial match in short messages
    for keyword in APPROVAL_KEYWORDS:
        if keyword in text and len(text) < 50:
            return True

    return False


async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Handle post approval and publish to LinkedIn.

    Args:
        update: Telegram update
        context: Bot context

    Returns:
        True if approval was handled
    """
    chat_id = update.effective_chat.id

    # Check for pending post
    pending_post = context.user_data.get("pending_post")

    if not pending_post:
        await update.message.reply_text(
            "No pending post to approve.\n\n"
            "Use `/generate` to create a new post first.",
            parse_mode="Markdown"
        )
        return True

    # Get user config
    config = config_store.get(chat_id)

    # Check if LinkedIn is connected
    if not config.is_linkedin_connected():
        # Clear pending post
        context.user_data.pop("pending_post", None)
        context.user_data.pop("pending_repo", None)

        await update.message.reply_text(
            "*Post approved!*\n\n"
            "However, LinkedIn is not connected.\n"
            "Use `/auth` to connect LinkedIn, then your posts will be published automatically.\n\n"
            "For now, you can copy the post and share it manually.",
            parse_mode="Markdown"
        )
        return True

    # Publish to LinkedIn
    status_msg = await update.message.reply_text(
        "Publishing to LinkedIn..."
    )

    try:
        result = linkedin_poster.create_post(
            access_token=config.linkedin_token,
            text=pending_post
        )

        # Clear pending post
        context.user_data.pop("pending_post", None)
        context.user_data.pop("pending_repo", None)

        if result.success:
            success_msg = "*Posted to LinkedIn!*\n\n"

            if result.post_url:
                success_msg += f"View your post: {result.post_url}\n\n"

            success_msg += "Use `/generate` to create another post."

            await status_msg.edit_text(
                success_msg,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
        else:
            await status_msg.edit_text(
                f"*Failed to post to LinkedIn:*\n`{result.error}`\n\n"
                "Please try again or check your LinkedIn connection with `/authstatus`.",
                parse_mode="Markdown"
            )

    except Exception as e:
        await status_msg.edit_text(
            f"*Error posting to LinkedIn:*\n`{str(e)}`\n\n"
            "Please try again.",
            parse_mode="Markdown"
        )

    return True


async def generate_scheduled_post(
    chat_id: int,
    bot,
    config_store: ConfigStore
) -> None:
    """
    Generate a scheduled post for a user.

    This is called by the scheduler at the user's preferred time.

    Args:
        chat_id: Telegram chat ID
        bot: Telegram bot instance
        config_store: Config store instance
    """
    from rag.loader import RepoLoader
    from rag.store import VectorStore
    from rag.retriever import CodeRetriever
    from generator.post_generator import PostGenerator

    config = config_store.get(chat_id)

    if not config.github_url:
        return

    try:
        # Initialize components
        repo_loader = RepoLoader()
        vector_store = VectorStore()
        retriever = CodeRetriever(vector_store)
        post_generator = PostGenerator()

        # Load collection
        if not vector_store.load_collection(config.github_url):
            # Repository not indexed, skip
            await bot.send_message(
                chat_id=chat_id,
                text="Daily post skipped: Repository needs to be indexed.\n"
                     "Use `/refresh` to index your repository.",
                parse_mode="Markdown"
            )
            return

        # Get git diff
        git_diff = repo_loader.get_git_diff(config.github_url)

        # Get code context
        code_context = retriever.get_code_for_post(config.github_url)

        if not code_context["main_context"]:
            await bot.send_message(
                chat_id=chat_id,
                text="Daily post skipped: Couldn't find interesting code.\n"
                     "Use `/refresh` to re-index your repository.",
                parse_mode="Markdown"
            )
            return

        # Generate post
        post = post_generator.generate_post(
            repo_url=config.github_url,
            code_context=code_context["main_context"],
            code_snippets=code_context["code_snippets"],
            git_diff=git_diff,
            post_style="adaptive"
        )

        # Send the draft
        header = (
            "*Your Daily LinkedIn Post Draft:*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        footer = (
            "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Reply with `post`, `yes`, `go`, or `ship` to publish.\n"
            "Or `/generate` for a new version."
        )

        # Note: For scheduled posts, we can't use context.user_data
        # In a production system, you'd store pending posts in a database
        # For MVP, scheduled posts go directly to the user for manual action

        await bot.send_message(
            chat_id=chat_id,
            text=header + post + footer,
            parse_mode="Markdown"
        )

    except Exception as e:
        await bot.send_message(
            chat_id=chat_id,
            text=f"Error generating daily post:\n`{str(e)}`",
            parse_mode="Markdown"
        )
