"""
/auth Command

Handles LinkedIn OAuth authentication flow.
"""

import sys
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ..config import ConfigStore
from linkedin.oauth import linkedin_oauth


# Initialize config store
config_store = ConfigStore()


async def auth_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /auth command.

    Initiates LinkedIn OAuth flow.
    """
    chat_id = update.effective_chat.id
    config = config_store.get(chat_id)

    # Check if already connected
    if config.is_linkedin_connected():
        await update.message.reply_text(
            "*LinkedIn is already connected!*\n\n"
            "Use `/authstatus` to check your connection.\n"
            "Use `/deauth` to disconnect and re-authenticate.",
            parse_mode="Markdown"
        )
        return

    # Check if OAuth is configured
    if not linkedin_oauth.is_configured():
        await update.message.reply_text(
            "*LinkedIn OAuth not configured.*\n\n"
            "The bot administrator needs to set up:\n"
            "• `LINKEDIN_CLIENT_ID`\n"
            "• `LINKEDIN_CLIENT_SECRET`\n\n"
            "See the README for setup instructions.",
            parse_mode="Markdown"
        )
        return

    try:
        # Generate auth URL
        auth_url = linkedin_oauth.generate_auth_url(chat_id)

        await update.message.reply_text(
            "*Connect your LinkedIn account:*\n\n"
            f"1. Click this link to authorize:\n{auth_url}\n\n"
            "2. After authorizing, you'll be redirected to a callback page.\n"
            "3. Copy the authorization code and send it here with:\n"
            "   `/authcode YOUR_CODE`\n\n"
            "_The link expires in 10 minutes._",
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

    except Exception as e:
        await update.message.reply_text(
            f"Error starting OAuth flow:\n`{str(e)}`",
            parse_mode="Markdown"
        )


async def authcode_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /authcode command.

    Completes OAuth flow with authorization code.
    """
    chat_id = update.effective_chat.id

    # Check if code was provided
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "Please provide the authorization code.\n\n"
            "Usage: `/authcode YOUR_CODE`",
            parse_mode="Markdown"
        )
        return

    code = context.args[0].strip()

    status_msg = await update.message.reply_text(
        "Completing LinkedIn authentication..."
    )

    try:
        # Exchange code for tokens
        tokens = linkedin_oauth.exchange_code(code)

        # Get user profile to verify
        profile = linkedin_oauth.get_user_profile(tokens.access_token)
        name = profile.get("name", "Unknown")

        # Save to config
        config_store.update(
            chat_id=chat_id,
            linkedin_token=tokens.access_token,
            linkedin_token_expiry=tokens.expires_at.isoformat()
        )

        await status_msg.edit_text(
            f"*LinkedIn connected successfully!*\n\n"
            f"Logged in as: {name}\n\n"
            "You can now approve posts and they'll be published to LinkedIn.\n\n"
            "Try `/generate` to create your first post!",
            parse_mode="Markdown"
        )

    except Exception as e:
        await status_msg.edit_text(
            f"*Authentication failed:*\n`{str(e)}`\n\n"
            "Please try `/auth` again.",
            parse_mode="Markdown"
        )


async def authstatus_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /authstatus command.

    Shows LinkedIn connection status.
    """
    chat_id = update.effective_chat.id
    config = config_store.get(chat_id)

    if config.is_linkedin_connected():
        try:
            # Verify token is still valid
            profile = linkedin_oauth.get_user_profile(config.linkedin_token)
            name = profile.get("name", "Unknown")

            await update.message.reply_text(
                f"*LinkedIn Status: Connected*\n\n"
                f"Account: {name}\n"
                f"Token expires: {config.linkedin_token_expiry}\n\n"
                "Use `/deauth` to disconnect.",
                parse_mode="Markdown"
            )
        except:
            await update.message.reply_text(
                "*LinkedIn Status: Token Expired*\n\n"
                "Your LinkedIn token has expired.\n"
                "Use `/auth` to reconnect.",
                parse_mode="Markdown"
            )
    else:
        await update.message.reply_text(
            "*LinkedIn Status: Not Connected*\n\n"
            "Use `/auth` to connect your LinkedIn account.",
            parse_mode="Markdown"
        )


async def deauth_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /deauth command.

    Disconnects LinkedIn account.
    """
    chat_id = update.effective_chat.id
    config = config_store.get(chat_id)

    if not config.linkedin_token:
        await update.message.reply_text(
            "LinkedIn is not connected.\n\n"
            "Use `/auth` to connect.",
            parse_mode="Markdown"
        )
        return

    # Clear LinkedIn tokens
    config_store.update(
        chat_id=chat_id,
        linkedin_token=None,
        linkedin_token_expiry=None
    )

    await update.message.reply_text(
        "*LinkedIn disconnected.*\n\n"
        "Use `/auth` to connect again.",
        parse_mode="Markdown"
    )
