"""
/generate Command

Generates a LinkedIn post from the connected repository.
"""

import sys
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ..config import ConfigStore
from rag.loader import RepoLoader
from rag.chunker import CodeChunker
from rag.store import VectorStore
from rag.retriever import CodeRetriever
from generator.post_generator import PostGenerator


# Initialize components
config_store = ConfigStore()
repo_loader = RepoLoader()
vector_store = VectorStore()
retriever = CodeRetriever(vector_store)
post_generator = PostGenerator()


async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /generate command.

    Generates a LinkedIn post from the connected repository.
    """
    chat_id = update.effective_chat.id
    config = config_store.get(chat_id)

    # Check if repo is connected
    if not config.github_url:
        await update.message.reply_text(
            "No repository connected.\n\n"
            "Use `/connect https://github.com/user/repo` first.",
            parse_mode="Markdown"
        )
        return

    # Send "generating" message
    status_msg = await update.message.reply_text(
        "Generating your LinkedIn post...\n\n"
        "This may take a moment."
    )

    try:
        # Check if repo is indexed
        if not vector_store.load_collection(config.github_url):
            await status_msg.edit_text(
                "Indexing your repository for the first time...\n\n"
                "This may take a few minutes."
            )

            # Index the repository
            await index_repository(config.github_url)

        # Get git diff for recent changes
        await status_msg.edit_text(
            "Checking for recent changes..."
        )
        git_diff = repo_loader.get_git_diff(config.github_url)

        # Retrieve relevant code context
        await status_msg.edit_text(
            "Finding interesting code to write about..."
        )
        code_context = retriever.get_code_for_post(config.github_url)

        if not code_context["main_context"]:
            await status_msg.edit_text(
                "Couldn't find interesting code in the repository.\n\n"
                "Try `/refresh` to re-index the repository."
            )
            return

        # Generate the post
        await status_msg.edit_text(
            "Writing your LinkedIn post..."
        )

        post = post_generator.generate_post(
            repo_url=config.github_url,
            code_context=code_context["main_context"],
            code_snippets=code_context["code_snippets"],
            git_diff=git_diff,
            post_style="adaptive"
        )

        # Send the generated post
        await status_msg.delete()

        # Split into header and post content
        header = (
            "*Your LinkedIn Post Draft:*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        footer = (
            "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Reply with `post`, `yes`, `go`, or `ship` to publish.\n"
            "Or `/generate` for a new version."
        )

        # Store the draft for approval
        context.user_data["pending_post"] = post
        context.user_data["pending_repo"] = config.github_url

        await update.message.reply_text(
            header + post + footer,
            parse_mode="Markdown"
        )

    except Exception as e:
        await status_msg.edit_text(
            f"Error generating post:\n`{str(e)}`\n\n"
            "Please try again or check your configuration with `/status`.",
            parse_mode="Markdown"
        )


async def index_repository(github_url: str) -> None:
    """
    Index a repository for RAG retrieval.

    Args:
        github_url: GitHub repository URL
    """
    # Load repository
    repo_path = repo_loader.load(github_url, force_refresh=False)

    # Get file list
    files = repo_loader.get_file_list(github_url)

    if not files:
        raise ValueError("No code files found in repository")

    # Chunk files
    chunker = CodeChunker()
    chunks = chunker.chunk_files(files, repo_path)
    documents = chunker.create_chunk_documents(chunks)

    # Store embeddings
    vector_store.add_documents(documents, github_url)


async def refresh_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /refresh command.

    Re-indexes the connected repository.
    """
    chat_id = update.effective_chat.id
    config = config_store.get(chat_id)

    if not config.github_url:
        await update.message.reply_text(
            "No repository connected.\n\n"
            "Use `/connect https://github.com/user/repo` first.",
            parse_mode="Markdown"
        )
        return

    status_msg = await update.message.reply_text(
        f"Re-indexing repository:\n`{config.github_url}`\n\n"
        "This may take a few minutes...",
        parse_mode="Markdown"
    )

    try:
        # Delete existing collection
        vector_store.delete_collection(config.github_url)

        # Force refresh and re-index
        repo_path = repo_loader.load(config.github_url, force_refresh=True)
        files = repo_loader.get_file_list(config.github_url)

        if not files:
            await status_msg.edit_text(
                "No code files found in repository.\n\n"
                "Make sure the repository contains code files."
            )
            return

        chunker = CodeChunker()
        chunks = chunker.chunk_files(files, repo_path)
        documents = chunker.create_chunk_documents(chunks)
        vector_store.add_documents(documents, config.github_url)

        await status_msg.edit_text(
            f"Repository re-indexed successfully!\n\n"
            f"Found {len(files)} code files.\n"
            f"Created {len(documents)} searchable chunks.\n\n"
            "Use `/generate` to create a new post.",
            parse_mode="Markdown"
        )

    except Exception as e:
        await status_msg.edit_text(
            f"Error refreshing repository:\n`{str(e)}`",
            parse_mode="Markdown"
        )
