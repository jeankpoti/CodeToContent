"""
Publisher Tools

LangChain tools for generating and publishing LinkedIn posts.
"""

from langchain.tools import tool

from agent.memory.database import Database
from agent.memory.learner import InsightLearner
from generator.post_generator import PostGenerator
from rag.retriever import CodeRetriever
from rag.loader import RepoLoader


# Global instances
_db = None
_generator = None
_retriever = None
_loader = None
_learner = None


def _get_db() -> Database:
    global _db
    if _db is None:
        _db = Database()
    return _db


def _get_generator() -> PostGenerator:
    global _generator
    if _generator is None:
        _generator = PostGenerator()
    return _generator


def _get_retriever() -> CodeRetriever:
    global _retriever
    if _retriever is None:
        _retriever = CodeRetriever()
    return _retriever


def _get_loader() -> RepoLoader:
    global _loader
    if _loader is None:
        _loader = RepoLoader()
    return _loader


def _get_learner() -> InsightLearner:
    global _learner
    if _learner is None:
        _learner = InsightLearner()
    return _learner


@tool
def generate_post_tool(
    chat_id: str,
    repo_url: str,
    trend: str = None,
    style: str = "adaptive"
) -> str:
    """
    Generate a LinkedIn post about code from a repository.

    Args:
        chat_id: The user's Telegram chat ID (for saving the post)
        repo_url: The GitHub repository URL to generate content about
        trend: Optional trend to connect the content to (e.g., "AI", "performance")
        style: Post style - "short", "long", or "adaptive" (default)

    Returns:
        Generated LinkedIn post content
    """
    db = _get_db()
    generator = _get_generator()
    retriever = _get_retriever()
    loader = _get_loader()
    learner = _get_learner()

    try:
        # Get learned recommendations
        recommendations = learner.get_content_recommendations(chat_id)

        # Apply learned preferences if available
        if style == "adaptive" and recommendations["length"]:
            style = recommendations["length"]

        # Get code context
        focus = trend if trend else "interesting features and patterns"
        code_context = retriever.get_code_for_post(repo_url=repo_url, focus=focus)

        if not code_context["main_context"]:
            return f"Could not find relevant code in {repo_url}. Make sure the repo is indexed."

        # Get recent commits
        git_diff = ""
        try:
            commits = loader.get_recent_commits(repo_url, days=7)
            if commits:
                git_diff = "\n".join([
                    f"- {c['message'][:80]}" for c in commits[:5]
                ])
        except Exception:
            pass

        # Generate the post
        post_content = generator.generate_post(
            repo_url=repo_url,
            code_context=code_context["main_context"] + "\n\n" + code_context["supporting_context"],
            code_snippets=code_context["code_snippets"],
            git_diff=git_diff,
            post_style=style
        )

        # Build reasoning
        reasoning = f"Selected repo: {repo_url}\n"
        if trend:
            reasoning += f"Matched to trend: {trend}\n"
        reasoning += f"Style: {style}\n"
        reasoning += f"Files analyzed: {', '.join(code_context['files_analyzed'][:3])}"

        # Save to database
        post_id = db.create_post(
            chat_id=chat_id,
            content=post_content,
            repo_url=repo_url,
            trend_matched=trend,
            reasoning=reasoning
        )

        return f"""=== Generated LinkedIn Post ===

{post_content}

---
Post ID: {post_id}
Repository: {repo_url.split('/')[-1]}
Trend: {trend or 'None'}
Style: {style}

Reply with 'post', 'yes', 'go', or 'ship' to publish to LinkedIn."""

    except Exception as e:
        return f"Error generating post: {str(e)}"


@tool
def generate_post_with_insights_tool(chat_id: str) -> str:
    """
    Generate an optimized LinkedIn post using all available insights.

    This is a high-level tool that:
    1. Picks the best repo based on history
    2. Matches current trends
    3. Applies learned style preferences
    4. Generates an optimized post

    Args:
        chat_id: The user's Telegram chat ID

    Returns:
        Generated LinkedIn post with explanation of choices
    """
    db = _get_db()
    learner = _get_learner()

    repos = db.get_repos(chat_id)
    if not repos:
        return "No repositories connected. Add repos with /addrepo first."

    # Get best repo
    best_repo = learner.get_best_repo_for_today(chat_id, repos)

    # Get recommendations
    recommendations = learner.get_content_recommendations(chat_id)

    # Get a trending topic to connect to
    from .trends import get_trend_keywords
    keywords = get_trend_keywords()
    trend = keywords[0] if keywords else None

    # Determine style
    style = recommendations["length"] if recommendations["length"] else "adaptive"

    # Generate the post
    result = generate_post_tool.invoke({
        "chat_id": chat_id,
        "repo_url": best_repo,
        "trend": trend,
        "style": style
    })

    # Add insight explanation
    explanation = [
        "\n--- Why these choices? ---",
        f"Repo: {best_repo.split('/')[-1]} (best historical performance + avoiding repetition)"
    ]

    if trend:
        explanation.append(f"Trend: '{trend}' (currently trending on HackerNews)")

    if recommendations["style"]:
        style_desc = "with code" if recommendations["style"] == "with_code" else "without code"
        explanation.append(f"Style: {style_desc} posts perform best for you")

    if recommendations["summary"]:
        explanation.append(f"Note: {recommendations['summary']}")

    return result + "\n" + "\n".join(explanation)


def save_post_as_published(post_id: str, linkedin_post_id: str):
    """
    Mark a post as published to LinkedIn.

    Args:
        post_id: The internal post ID
        linkedin_post_id: The LinkedIn post ID
    """
    db = _get_db()
    db.mark_post_published(post_id, linkedin_post_id)
