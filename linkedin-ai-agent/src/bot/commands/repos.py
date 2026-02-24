"""
Repository Management Commands

Commands for managing multiple GitHub repositories.
"""

import re
from telegram import Update
from telegram.ext import ContextTypes

from agent.memory.database import Database


# Initialize database
db = Database()


def is_valid_github_url(url: str) -> bool:
    """Check if a URL is a valid GitHub repository URL."""
    pattern = r'^https?://github\.com/[\w-]+/[\w.-]+/?$'
    return bool(re.match(pattern, url))


async def repos_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /repos command.

    Lists all connected repositories.
    """
    chat_id = str(update.effective_chat.id)
    repos = db.get_repos(chat_id)

    if not repos:
        await update.message.reply_text(
            "*No repositories connected.*\n\n"
            "Use `/addrepo https://github.com/user/repo` to add one.\n"
            "You can connect up to 5 repositories.",
            parse_mode="Markdown"
        )
        return

    lines = [f"*Connected Repositories ({len(repos)}/5):*\n"]

    for i, repo_url in enumerate(repos, 1):
        repo_name = repo_url.rstrip("/").split("/")[-1]
        owner = repo_url.rstrip("/").split("/")[-2]
        lines.append(f"{i}. `{owner}/{repo_name}`")
        lines.append(f"   {repo_url}")

    lines.append("\n*Commands:*")
    lines.append("• `/addrepo <url>` - Add a repository")
    lines.append("• `/removerepo <url>` - Remove a repository")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown"
    )


async def addrepo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /addrepo command.

    Adds a new GitHub repository (max 5).
    """
    chat_id = str(update.effective_chat.id)

    # Check for URL argument
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "*Usage:* `/addrepo https://github.com/user/repo`\n\n"
            "Provide a public GitHub repository URL.",
            parse_mode="Markdown"
        )
        return

    repo_url = context.args[0].strip()

    # Validate URL
    if not is_valid_github_url(repo_url):
        await update.message.reply_text(
            "*Invalid GitHub URL.*\n\n"
            "Please provide a valid public GitHub repository URL.\n"
            "Example: `https://github.com/user/repo`",
            parse_mode="Markdown"
        )
        return

    # Normalize URL (remove trailing slash)
    repo_url = repo_url.rstrip("/")

    # Try to add
    success, message = db.add_repo(chat_id, repo_url)

    if success:
        repo_name = repo_url.split("/")[-1]
        repos = db.get_repos(chat_id)
        await update.message.reply_text(
            f"*Repository added:* `{repo_name}`\n\n"
            f"Connected repos: {len(repos)}/5\n\n"
            "The agent will now consider this repo when generating posts.\n"
            "Use `/generate` to create a post.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"*Could not add repository:*\n{message}",
            parse_mode="Markdown"
        )


async def removerepo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /removerepo command.

    Removes a connected repository.
    """
    chat_id = str(update.effective_chat.id)

    # Check for URL argument
    if not context.args or len(context.args) < 1:
        repos = db.get_repos(chat_id)
        if repos:
            lines = ["*Usage:* `/removerepo <url>`\n", "*Your repositories:*"]
            for repo in repos:
                lines.append(f"• `{repo}`")
            await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
        else:
            await update.message.reply_text(
                "No repositories to remove.\n\n"
                "Use `/addrepo <url>` to add a repository.",
                parse_mode="Markdown"
            )
        return

    repo_url = context.args[0].strip().rstrip("/")

    # Try to remove
    success, message = db.remove_repo(chat_id, repo_url)

    if success:
        repo_name = repo_url.split("/")[-1]
        await update.message.reply_text(
            f"*Repository removed:* `{repo_name}`\n\n"
            "Use `/repos` to see your connected repositories.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"*Could not remove repository:*\n{message}\n\n"
            "Use `/repos` to see your connected repositories.",
            parse_mode="Markdown"
        )
