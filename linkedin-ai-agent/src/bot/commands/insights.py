"""
Insights Commands

Commands for viewing agent insights and explaining decisions.
"""

from telegram import Update
from telegram.ext import ContextTypes

from agent.memory.database import Database
from agent.memory.learner import InsightLearner
from trends.hackernews import HackerNewsTrends
from trends.twitter import TwitterTrends
from scheduler.metrics_fetcher import get_manual_input


# Initialize components
db = Database()
learner = InsightLearner(db)
manual_input = get_manual_input()


async def insights_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /insights command.

    Shows learned patterns about what content performs best.
    """
    chat_id = str(update.effective_chat.id)

    # Process any unprocessed posts
    learner.process_all_pending(chat_id)

    # Get recommendations
    recommendations = learner.get_content_recommendations(chat_id)

    lines = ["*Content Strategy Insights*\n"]

    # Summary
    if recommendations["summary"]:
        lines.append(f"_{recommendations['summary']}_\n")

    # Top topics
    if recommendations["topics"]:
        lines.append("*Best Performing Topics:*")
        for topic in recommendations["topics"][:5]:
            score_bar = "█" * int(topic["score"] / 20) + "░" * (5 - int(topic["score"] / 20))
            lines.append(f"• {topic['topic']} [{score_bar}]")
        lines.append("")

    # Best style
    if recommendations["style"]:
        style_desc = {
            "with_code": "Posts WITH code snippets",
            "no_code": "Posts WITHOUT code"
        }.get(recommendations["style"], recommendations["style"])
        lines.append(f"*Best Style:* {style_desc}")

    # Best length
    if recommendations["length"]:
        lines.append(f"*Best Length:* {recommendations['length'].title()} posts")

    # Best repos
    if recommendations["repos"]:
        lines.append("\n*Best Performing Repos:*")
        for repo in recommendations["repos"][:3]:
            lines.append(f"• {repo['repo']} (score: {repo['score']:.0f})")

    # Not enough data
    if not any([recommendations["topics"], recommendations["style"], recommendations["repos"]]):
        lines.append("*Not enough data yet.*")
        lines.append("")
        lines.append("Generate and post more content to learn patterns.")
        lines.append("Need at least 3 posts with engagement metrics.")
        lines.append("")
        lines.append("_Tip: Use `/generate` to create a post!_")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown"
    )


async def trends_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /trends command.

    Shows current trending developer topics.
    """
    status_msg = await update.message.reply_text(
        "Fetching current developer trends..."
    )

    try:
        lines = ["*Current Developer Trends*\n"]

        # HackerNews trends (always available)
        hn = HackerNewsTrends()
        hn_trends = hn.get_trending(limit=7)

        if hn_trends:
            lines.append("*HackerNews:*")
            for i, trend in enumerate(hn_trends, 1):
                keywords = ", ".join(trend.keywords[:2]) if trend.keywords else ""
                keywords_str = f" ({keywords})" if keywords else ""
                title = trend.title[:50] + "..." if len(trend.title) > 50 else trend.title
                lines.append(f"{i}. {title}{keywords_str}")
            lines.append("")

        # Twitter trends (if available)
        tw = TwitterTrends()
        if tw.is_available():
            tw_trends = tw.get_trending(limit=5)
            if tw_trends:
                lines.append("*Twitter:*")
                for i, trend in enumerate(tw_trends, 1):
                    title = trend.title[:40] + "..." if len(trend.title) > 40 else trend.title
                    lines.append(f"{i}. {title}")
                lines.append("")
        else:
            lines.append("_Twitter: Not configured (optional)_\n")

        lines.append("Use `/generate` to create a post matching these trends!")

        await status_msg.edit_text(
            "\n".join(lines),
            parse_mode="Markdown"
        )

    except Exception as e:
        await status_msg.edit_text(
            f"Error fetching trends:\n`{str(e)}`",
            parse_mode="Markdown"
        )


async def why_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /why command.

    Explains why the last post was generated the way it was.
    """
    chat_id = str(update.effective_chat.id)

    last_post = db.get_last_post(chat_id)

    if not last_post:
        await update.message.reply_text(
            "*No posts found.*\n\n"
            "Use `/generate` to create a post first.",
            parse_mode="Markdown"
        )
        return

    lines = ["*Last Post Analysis*\n"]

    # Basic info
    repo = last_post.get("repo_url", "")
    repo_name = repo.rstrip("/").split("/")[-1] if repo else "Unknown"
    trend = last_post.get("trend_matched", "None")
    created = last_post.get("created_at", "")[:19] if last_post.get("created_at") else "Unknown"

    lines.append(f"*Repository:* `{repo_name}`")
    lines.append(f"*Trend Matched:* {trend}")
    lines.append(f"*Created:* {created}")

    # Reasoning
    reasoning = last_post.get("reasoning")
    if reasoning:
        lines.append("")
        lines.append("*Agent Reasoning:*")
        lines.append(f"```\n{reasoning}\n```")

    # Status
    if last_post.get("posted_at"):
        posted_at = last_post["posted_at"][:10]
        lines.append("")
        lines.append(f"*Status:* Published on {posted_at}")
    else:
        lines.append("")
        lines.append("*Status:* Draft (not published)")

    # Preview
    content = last_post.get("content", "")
    if content:
        preview = content[:150] + "..." if len(content) > 150 else content
        lines.append("")
        lines.append("*Preview:*")
        lines.append(f"_{preview}_")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown"
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /stats command.

    Manually input engagement metrics for the last post.
    Usage: /stats <likes> <comments> [shares] [impressions]
    """
    chat_id = str(update.effective_chat.id)

    # Check arguments
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "*Manual Stats Input*\n\n"
            "*Usage:* `/stats <likes> <comments> [shares] [impressions]`\n\n"
            "*Examples:*\n"
            "• `/stats 50 10` - 50 likes, 10 comments\n"
            "• `/stats 50 10 5` - with 5 shares\n"
            "• `/stats 50 10 5 1000` - with impressions\n\n"
            "_This updates the last published post's metrics._",
            parse_mode="Markdown"
        )
        return

    # Parse the stats
    args_text = " ".join(context.args)
    metrics, error = manual_input.parse_stats_command(args_text)

    if error:
        await update.message.reply_text(
            f"*Error:* {error}",
            parse_mode="Markdown"
        )
        return

    # Update the metrics
    success, message = manual_input.update_last_post_metrics(
        chat_id=chat_id,
        likes=metrics["likes"],
        comments=metrics["comments"],
        shares=metrics["shares"],
        impressions=metrics["impressions"]
    )

    if success:
        await update.message.reply_text(
            f"*Stats Updated!*\n\n"
            f"• Likes: {metrics['likes']}\n"
            f"• Comments: {metrics['comments']}\n"
            f"• Shares: {metrics['shares']}\n"
            f"• Impressions: {metrics['impressions']}\n\n"
            "_Insights have been updated. Use `/insights` to see patterns._",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"*Could not update stats:*\n{message}",
            parse_mode="Markdown"
        )
