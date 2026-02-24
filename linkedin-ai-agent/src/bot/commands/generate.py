"""
/generate Command

Generates a LinkedIn post from the connected repository.
Supports both legacy mode (single repo) and agent mode (multi-repo with trends).
"""

import os
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
from agent.memory.database import Database
from agent.strategist import ContentStrategist


# Initialize components
config_store = ConfigStore()
repo_loader = RepoLoader()
vector_store = VectorStore()
retriever = CodeRetriever(vector_store)
post_generator = PostGenerator()
agent_db = Database()

# Check if agent mode is enabled
AGENT_MODE = os.getenv("AGENT_MODE", "true").lower() == "true"


async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /generate command.

    Generates a LinkedIn post from the connected repository.
    Uses agent mode if multiple repos are connected or AGENT_MODE is enabled.
    """
    chat_id = str(update.effective_chat.id)
    config = config_store.get(int(chat_id))

    # Check for repos in new agent database
    agent_repos = agent_db.get_repos(chat_id)

    # Check if repo is connected (either legacy or new mode)
    if not config.github_url and not agent_repos:
        await update.message.reply_text(
            "No repository connected.\n\n"
            "Use `/addrepo https://github.com/user/repo` to add one.\n"
            "You can connect up to 5 repositories.",
            parse_mode="Markdown"
        )
        return

    # Use agent mode if multiple repos or explicitly enabled
    if AGENT_MODE and (len(agent_repos) > 1 or agent_repos):
        await generate_with_agent(update, context, chat_id, agent_repos)
        return

    # Legacy single-repo mode
    if not config.github_url and agent_repos:
        # Use first agent repo as fallback
        config.github_url = agent_repos[0]

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


async def generate_with_agent(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: str,
    repos: list[str]
) -> None:
    """
    Generate a post using the AI agent.

    The agent will:
    1. Analyze all connected repos
    2. Check current trends
    3. Apply learned insights
    4. Generate an optimized post
    """
    status_msg = await update.message.reply_text(
        "🤖 *Agent Mode Active*\n\n"
        f"Analyzing {len(repos)} repositories...\n"
        "Checking trends and insights...",
        parse_mode="Markdown"
    )

    try:
        # Initialize agent
        agent = ContentStrategist(verbose=False)

        # Ensure all repos are indexed
        for repo_url in repos:
            if not vector_store.load_collection(repo_url):
                await status_msg.edit_text(
                    f"Indexing repository: `{repo_url.split('/')[-1]}`...",
                    parse_mode="Markdown"
                )
                await index_repository(repo_url)

        # Update status
        await status_msg.edit_text(
            "🤖 *Agent thinking...*\n\n"
            "• Fetching trends\n"
            "• Comparing repos\n"
            "• Applying insights\n"
            "• Generating post",
            parse_mode="Markdown"
        )

        # Run the agent
        result = agent.generate_daily_post(chat_id)

        if not result["success"]:
            await status_msg.edit_text(
                f"❌ Agent error:\n`{result['output']}`",
                parse_mode="Markdown"
            )
            return

        # Extract the post from the agent output
        output = result["output"]

        # Parse the generated post
        post_content = output
        if "===" in output:
            # Extract just the post content
            parts = output.split("===")
            for part in parts:
                if part.strip() and "Reply with" not in part and "Post ID" not in part:
                    post_content = part.strip()
                    break

        # Clean up the content
        if "Generated LinkedIn Post" in post_content:
            post_content = post_content.replace("Generated LinkedIn Post", "").strip()

        await status_msg.delete()

        # Build reasoning summary
        reasoning_lines = []
        if result["reasoning"]:
            for step in result["reasoning"][:3]:  # Show first 3 steps
                reasoning_lines.append(f"• {step['tool']}")

        reasoning_text = ""
        if reasoning_lines:
            reasoning_text = "\n\n*Agent steps:*\n" + "\n".join(reasoning_lines)

        # Store the draft
        context.user_data["pending_post"] = post_content
        context.user_data["pending_repo"] = repos[0] if repos else ""

        # Send the post
        header = (
            "🤖 *Your AI-Generated LinkedIn Post:*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        footer = (
            "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Reply with `post`, `yes`, `go`, or `ship` to publish.\n"
            "Or `/generate` for a new version.\n"
            "Use `/why` to understand the agent's choices."
            + reasoning_text
        )

        await update.message.reply_text(
            header + post_content + footer,
            parse_mode="Markdown"
        )

    except Exception as e:
        await status_msg.edit_text(
            f"❌ Error generating post:\n`{str(e)}`\n\n"
            "Try `/generate` again or check `/status`.",
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
