"""
History Tools

LangChain tools for accessing post history and learned insights.
"""

from langchain.tools import tool

from ..memory.database import Database
from ..memory.learner import InsightLearner


# Global instances
_db = None
_learner = None


def _get_db() -> Database:
    global _db
    if _db is None:
        _db = Database()
    return _db


def _get_learner() -> InsightLearner:
    global _learner
    if _learner is None:
        _learner = InsightLearner()
    return _learner


@tool
def get_post_history_tool(chat_id: str, limit: int = 10) -> str:
    """
    Get recent post history with engagement metrics.

    Args:
        chat_id: The user's Telegram chat ID
        limit: Maximum number of posts to return (default 10)

    Returns:
        List of recent posts with their performance metrics
    """
    db = _get_db()

    posts = db.get_posts_with_metrics(chat_id, limit=limit)

    if not posts:
        return "No posts in history yet. Generate and publish some posts first!"

    lines = [f"=== Recent Posts ({len(posts)}) ===\n"]

    for i, post in enumerate(posts, 1):
        # Format date
        posted_at = post.get("posted_at", "Not posted")
        if posted_at and posted_at != "Not posted":
            posted_at = posted_at[:10]  # Just the date

        # Get metrics
        likes = post.get("likes", 0) or 0
        comments = post.get("comments", 0) or 0
        shares = post.get("shares", 0) or 0

        # Get trend and repo
        trend = post.get("trend_matched", "No trend")
        repo = post.get("repo_url", "")
        repo_name = repo.rstrip("/").split("/")[-1] if repo else "Unknown"

        # Truncate content
        content = post.get("content", "")[:100] + "..." if len(post.get("content", "")) > 100 else post.get("content", "")

        lines.append(f"{i}. Posted: {posted_at}")
        lines.append(f"   Repo: {repo_name} | Trend: {trend}")
        lines.append(f"   Engagement: {likes} likes, {comments} comments, {shares} shares")
        lines.append(f"   Preview: {content}")
        lines.append("")

    return "\n".join(lines)


@tool
def get_insights_tool(chat_id: str) -> str:
    """
    Get learned insights about what content performs best.

    This tool returns patterns learned from past post performance:
    - Best topics
    - Best content styles
    - Best post lengths
    - Best performing repos

    Args:
        chat_id: The user's Telegram chat ID

    Returns:
        Summary of learned content strategy insights
    """
    learner = _get_learner()

    # Process any unprocessed posts first
    learner.process_all_pending(chat_id)

    # Get recommendations
    recommendations = learner.get_content_recommendations(chat_id)

    lines = ["=== Content Strategy Insights ===\n"]

    # Summary
    lines.append(f"Summary: {recommendations['summary']}")
    lines.append("")

    # Top topics
    if recommendations["topics"]:
        lines.append("Best Performing Topics:")
        for topic in recommendations["topics"]:
            lines.append(f"  - {topic['topic']} (score: {topic['score']:.1f})")
        lines.append("")

    # Best style
    if recommendations["style"]:
        style_desc = {
            "with_code": "Posts WITH code snippets",
            "no_code": "Posts WITHOUT code snippets"
        }.get(recommendations["style"], recommendations["style"])
        lines.append(f"Best Style: {style_desc}")

    # Best length
    if recommendations["length"]:
        lines.append(f"Best Length: {recommendations['length'].title()} posts")

    # Best repos
    if recommendations["repos"]:
        lines.append("")
        lines.append("Best Performing Repos:")
        for repo in recommendations["repos"]:
            lines.append(f"  - {repo['repo']} (score: {repo['score']:.1f})")

    if not any([recommendations["topics"], recommendations["style"], recommendations["repos"]]):
        lines.append("Not enough data yet. Post more content to learn patterns!")
        lines.append("Need at least 3 posts with engagement metrics.")

    return "\n".join(lines)


@tool
def get_last_post_reasoning_tool(chat_id: str) -> str:
    """
    Get the reasoning behind the last generated post.

    Useful for understanding why the agent chose a particular repo/trend.

    Args:
        chat_id: The user's Telegram chat ID

    Returns:
        Explanation of the last post's content strategy
    """
    db = _get_db()

    last_post = db.get_last_post(chat_id)

    if not last_post:
        return "No posts found. Generate a post first!"

    lines = ["=== Last Post Analysis ===\n"]

    # Basic info
    repo = last_post.get("repo_url", "")
    repo_name = repo.rstrip("/").split("/")[-1] if repo else "Unknown"
    trend = last_post.get("trend_matched", "No specific trend")

    lines.append(f"Repository: {repo_name}")
    lines.append(f"Trend Matched: {trend}")
    lines.append(f"Created: {last_post.get('created_at', 'Unknown')[:19]}")

    # Reasoning
    reasoning = last_post.get("reasoning")
    if reasoning:
        lines.append("")
        lines.append("Agent Reasoning:")
        lines.append(reasoning)
    else:
        lines.append("")
        lines.append("No detailed reasoning recorded for this post.")

    # Post status
    if last_post.get("posted_at"):
        lines.append("")
        lines.append(f"Status: Published on {last_post['posted_at'][:10]}")
        lines.append(f"LinkedIn Post ID: {last_post.get('linkedin_post_id', 'Unknown')}")
    else:
        lines.append("")
        lines.append("Status: Draft (not yet published)")

    return "\n".join(lines)


@tool
def suggest_next_post_tool(chat_id: str) -> str:
    """
    Suggest what to post about next based on history and trends.

    Combines:
    - Current trends
    - Historical performance
    - Repo activity
    - Avoiding repetition

    Args:
        chat_id: The user's Telegram chat ID

    Returns:
        Recommendation for next post topic and repo
    """
    db = _get_db()
    learner = _get_learner()

    repos = db.get_repos(chat_id)
    if not repos:
        return "No repositories connected. Add repos with /addrepo first."

    # Get best repo based on history
    best_repo = learner.get_best_repo_for_today(chat_id, repos)
    repo_name = best_repo.rstrip("/").split("/")[-1] if best_repo else "Unknown"

    # Get recommendations
    recommendations = learner.get_content_recommendations(chat_id)

    lines = ["=== Next Post Suggestion ===\n"]

    lines.append(f"Recommended Repository: {repo_name}")

    if recommendations["topics"]:
        top_topic = recommendations["topics"][0]["topic"]
        lines.append(f"Consider Topic: {top_topic} (your best performer)")

    if recommendations["style"]:
        style_tip = "Include code snippets" if recommendations["style"] == "with_code" else "Keep it conversational without code"
        lines.append(f"Style Tip: {style_tip}")

    if recommendations["length"]:
        lines.append(f"Length Tip: Aim for {recommendations['length']} format")

    lines.append("")
    lines.append("Use /generate to create a post with these recommendations!")

    return "\n".join(lines)
