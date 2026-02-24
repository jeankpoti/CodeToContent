"""
Metrics Fetcher

Background job that fetches LinkedIn engagement metrics and updates insights.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from agent.memory.database import Database
from agent.memory.learner import InsightLearner
from linkedin.poster import LinkedInPoster


class MetricsFetcher:
    """Fetches LinkedIn engagement metrics and triggers learning."""

    def __init__(self):
        """Initialize the metrics fetcher."""
        self.db = Database()
        self.learner = InsightLearner(self.db)
        self.linkedin = LinkedInPoster()

    def fetch_metrics_for_post(self, post_id: str, linkedin_post_id: str) -> Optional[dict]:
        """
        Fetch engagement metrics for a single post.

        Args:
            post_id: Internal post ID
            linkedin_post_id: LinkedIn's post ID

        Returns:
            Dict with likes, comments, shares, impressions or None
        """
        try:
            metrics = self.linkedin.get_post_metrics(linkedin_post_id)
            if metrics:
                self.db.update_metrics(
                    post_id=post_id,
                    likes=metrics.get("likes", 0),
                    comments=metrics.get("comments", 0),
                    shares=metrics.get("shares", 0),
                    impressions=metrics.get("impressions", 0)
                )
                return metrics
        except Exception as e:
            print(f"Error fetching metrics for {linkedin_post_id}: {e}")
        return None

    def fetch_all_pending_metrics(self, chat_id: str) -> int:
        """
        Fetch metrics for all posts that need updating.

        Args:
            chat_id: User's chat ID

        Returns:
            Number of posts updated
        """
        # Get recent posts that have been published
        posts = self.db.get_posts_with_metrics(chat_id, limit=20)

        updated = 0
        for post in posts:
            if post.get("linkedin_post_id") and post.get("posted_at"):
                # Only fetch metrics for posts in the last 7 days
                posted_at = post.get("posted_at")
                if isinstance(posted_at, str):
                    try:
                        posted_dt = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
                        if datetime.now(posted_dt.tzinfo) - posted_dt > timedelta(days=7):
                            continue
                    except:
                        pass

                metrics = self.fetch_metrics_for_post(
                    post_id=post["id"],
                    linkedin_post_id=post["linkedin_post_id"]
                )
                if metrics:
                    updated += 1

        return updated

    def process_insights(self, chat_id: str):
        """
        Process all posts and update insights.

        Args:
            chat_id: User's chat ID
        """
        self.learner.process_all_pending(chat_id)

    def run_for_user(self, chat_id: str) -> dict:
        """
        Run the full metrics fetch and learning cycle for a user.

        Args:
            chat_id: User's chat ID

        Returns:
            Dict with stats about the run
        """
        # Fetch latest metrics
        posts_updated = self.fetch_all_pending_metrics(chat_id)

        # Process insights
        self.process_insights(chat_id)

        return {
            "posts_updated": posts_updated,
            "timestamp": datetime.utcnow().isoformat()
        }


class ManualMetricsInput:
    """
    Handles manual metrics input via Telegram.

    Usage: /stats <likes> <comments> [shares] [impressions]
    """

    def __init__(self):
        """Initialize manual metrics handler."""
        self.db = Database()
        self.learner = InsightLearner(self.db)

    def update_last_post_metrics(
        self,
        chat_id: str,
        likes: int,
        comments: int,
        shares: int = 0,
        impressions: int = 0
    ) -> tuple[bool, str]:
        """
        Update metrics for the last posted content.

        Args:
            chat_id: User's chat ID
            likes: Number of likes
            comments: Number of comments
            shares: Number of shares
            impressions: Number of impressions

        Returns:
            (success, message)
        """
        last_post = self.db.get_last_post(chat_id)

        if not last_post:
            return False, "No posts found. Generate and publish a post first."

        if not last_post.get("posted_at"):
            return False, "Last post hasn't been published yet."

        # Update metrics
        self.db.update_metrics(
            post_id=last_post["id"],
            likes=likes,
            comments=comments,
            shares=shares,
            impressions=impressions
        )

        # Process insights immediately
        self.learner.learn_from_post(last_post["id"], chat_id)

        return True, f"Updated metrics: {likes} likes, {comments} comments, {shares} shares"

    def parse_stats_command(self, text: str) -> tuple[Optional[dict], str]:
        """
        Parse a /stats command.

        Args:
            text: Command text like "50 10" or "50 10 5 1000"

        Returns:
            (metrics_dict or None, error_message)
        """
        parts = text.strip().split()

        if len(parts) < 2:
            return None, "Usage: /stats <likes> <comments> [shares] [impressions]"

        try:
            metrics = {
                "likes": int(parts[0]),
                "comments": int(parts[1]),
                "shares": int(parts[2]) if len(parts) > 2 else 0,
                "impressions": int(parts[3]) if len(parts) > 3 else 0
            }
            return metrics, ""
        except ValueError:
            return None, "Invalid numbers. Use: /stats 50 10 5 1000"


# Singleton instances
_metrics_fetcher = None
_manual_input = None


def get_metrics_fetcher() -> MetricsFetcher:
    """Get the metrics fetcher singleton."""
    global _metrics_fetcher
    if _metrics_fetcher is None:
        _metrics_fetcher = MetricsFetcher()
    return _metrics_fetcher


def get_manual_input() -> ManualMetricsInput:
    """Get the manual input handler singleton."""
    global _manual_input
    if _manual_input is None:
        _manual_input = ManualMetricsInput()
    return _manual_input
