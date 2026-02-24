"""
Insight Learner

Extracts patterns from post performance to improve future content strategy.
"""

from typing import Optional
from .database import Database


class InsightLearner:
    """Learns from post engagement to improve content strategy."""

    def __init__(self, database: Database = None):
        """
        Initialize the learner.

        Args:
            database: Database instance (creates new one if not provided)
        """
        self.db = database or Database()

    def calculate_engagement_score(
        self,
        likes: int = 0,
        comments: int = 0,
        shares: int = 0,
        impressions: int = 0
    ) -> float:
        """
        Calculate a normalized engagement score.

        Weights:
        - Comments are most valuable (3x)
        - Shares are valuable (2x)
        - Likes are baseline (1x)
        - Impressions provide context but don't directly score

        Returns:
            Engagement score (0-100 scale)
        """
        if impressions == 0:
            # Without impressions, use absolute numbers with diminishing returns
            raw_score = likes + (comments * 3) + (shares * 2)
            # Normalize with logarithmic scaling
            return min(100, raw_score * 2)

        # With impressions, calculate engagement rate
        engagement_rate = ((likes + comments * 3 + shares * 2) / impressions) * 100
        return min(100, engagement_rate * 10)  # Scale up for readability

    def learn_from_post(self, post_id: str, chat_id: str):
        """
        Extract insights from a post's performance.

        Analyzes:
        - Topic performance (based on trend_matched)
        - Repo performance (which repos get engagement)
        - Content patterns (length, code snippets, etc.)
        """
        post = self.db.get_post(post_id)
        metrics = self.db.get_metrics(post_id)

        if not post or not metrics:
            return

        score = self.calculate_engagement_score(
            likes=metrics.get("likes", 0),
            comments=metrics.get("comments", 0),
            shares=metrics.get("shares", 0),
            impressions=metrics.get("impressions", 0)
        )

        # Learn topic performance
        if post.get("trend_matched"):
            self.db.update_insight(
                chat_id=chat_id,
                insight_type="topic",
                insight_key=post["trend_matched"].lower(),
                score=score
            )

        # Learn repo performance
        if post.get("repo_url"):
            # Extract repo name from URL
            repo_name = post["repo_url"].rstrip("/").split("/")[-1]
            self.db.update_insight(
                chat_id=chat_id,
                insight_type="repo",
                insight_key=repo_name,
                score=score
            )

        # Learn content style
        content = post.get("content", "")

        # Has code snippet?
        has_code = "```" in content
        self.db.update_insight(
            chat_id=chat_id,
            insight_type="style",
            insight_key="with_code" if has_code else "no_code",
            score=score
        )

        # Content length
        word_count = len(content.split())
        if word_count < 100:
            length_key = "short"
        elif word_count < 250:
            length_key = "medium"
        else:
            length_key = "long"
        self.db.update_insight(
            chat_id=chat_id,
            insight_type="length",
            insight_key=length_key,
            score=score
        )

    def process_all_pending(self, chat_id: str):
        """Process all posts with metrics that haven't been learned from."""
        posts_with_metrics = self.db.get_posts_with_metrics(chat_id, limit=50)

        for post in posts_with_metrics:
            if post.get("likes") is not None:  # Has metrics
                self.learn_from_post(post["id"], chat_id)

    def get_content_recommendations(self, chat_id: str) -> dict:
        """
        Get content recommendations based on learned insights.

        Returns:
            Dict with recommendations for topics, style, length, repos
        """
        recommendations = {
            "topics": [],
            "style": None,
            "length": None,
            "repos": [],
            "summary": ""
        }

        # Get top topics
        topic_insights = self.db.get_insights(chat_id, "topic")
        if topic_insights:
            recommendations["topics"] = [
                {"topic": i["insight_key"], "score": i["score"]}
                for i in topic_insights[:5]
                if i["sample_size"] >= 2
            ]

        # Get best style
        style_insights = self.db.get_insights(chat_id, "style")
        if style_insights and style_insights[0]["sample_size"] >= 3:
            recommendations["style"] = style_insights[0]["insight_key"]

        # Get best length
        length_insights = self.db.get_insights(chat_id, "length")
        if length_insights and length_insights[0]["sample_size"] >= 3:
            recommendations["length"] = length_insights[0]["insight_key"]

        # Get best repos
        repo_insights = self.db.get_insights(chat_id, "repo")
        if repo_insights:
            recommendations["repos"] = [
                {"repo": i["insight_key"], "score": i["score"]}
                for i in repo_insights[:3]
                if i["sample_size"] >= 2
            ]

        # Generate summary
        summary_parts = []
        if recommendations["style"]:
            style_desc = "with code snippets" if recommendations["style"] == "with_code" else "without code"
            summary_parts.append(f"Posts {style_desc} perform better")
        if recommendations["length"]:
            summary_parts.append(f"{recommendations['length'].title()} posts get more engagement")
        if recommendations["topics"]:
            top_topic = recommendations["topics"][0]["topic"]
            summary_parts.append(f"'{top_topic}' is your best-performing topic")

        recommendations["summary"] = ". ".join(summary_parts) if summary_parts else "Not enough data yet"

        return recommendations

    def get_best_repo_for_today(self, chat_id: str, available_repos: list[str]) -> Optional[str]:
        """
        Suggest the best repo to post about today.

        Considers:
        - Historical performance
        - Recency (avoid posting about same repo twice in a row)
        - Availability
        """
        if not available_repos:
            return None

        if len(available_repos) == 1:
            return available_repos[0]

        # Get last post's repo to avoid repetition
        last_post = self.db.get_last_post(chat_id)
        last_repo_url = last_post.get("repo_url") if last_post else None

        # Get repo insights
        repo_insights = self.db.get_insights(chat_id, "repo")
        repo_scores = {i["insight_key"]: i["score"] for i in repo_insights}

        # Score available repos
        scored_repos = []
        for repo_url in available_repos:
            repo_name = repo_url.rstrip("/").split("/")[-1]
            score = repo_scores.get(repo_name, 50)  # Default score

            # Penalize if same as last post
            if repo_url == last_repo_url:
                score *= 0.5

            scored_repos.append((repo_url, score))

        # Sort by score and return best
        scored_repos.sort(key=lambda x: x[1], reverse=True)
        return scored_repos[0][0]
