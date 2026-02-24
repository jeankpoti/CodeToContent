"""
Twitter/X Trends

Fetches trending developer topics from Twitter/X.
OPTIONAL - Requires TWITTER_BEARER_TOKEN environment variable.

If token is not set, this module gracefully returns empty results.
"""

import os
import re
from typing import Optional
from dataclasses import dataclass

# Check if tweepy is available
try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False


@dataclass
class Trend:
    """A trending topic."""
    title: str
    url: Optional[str]
    score: int
    source: str
    keywords: list[str]


class TwitterTrends:
    """Fetches trending developer topics from Twitter/X."""

    # Developer-related accounts to monitor
    DEV_ACCOUNTS = [
        "github", "vercel", "nodejs", "reactjs", "vuejs",
        "typescript", "rustlang", "golang", "python",
        "awscloud", "googlecloud", "azure",
        "openai", "anthropic", "docker", "kubernetes"
    ]

    # Developer hashtags to track
    DEV_HASHTAGS = [
        "#100DaysOfCode", "#DevCommunity", "#CodeNewbie",
        "#Python", "#JavaScript", "#TypeScript", "#Rust", "#Golang",
        "#WebDev", "#Frontend", "#Backend", "#FullStack",
        "#AI", "#ML", "#LLM", "#OpenSource", "#DevOps",
        "#CloudComputing", "#AWS", "#Azure", "#GCP"
    ]

    def __init__(self):
        """Initialize Twitter trends fetcher."""
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        self.client = None

        if self.bearer_token and TWEEPY_AVAILABLE:
            try:
                self.client = tweepy.Client(bearer_token=self.bearer_token)
            except Exception:
                self.client = None

    def is_available(self) -> bool:
        """Check if Twitter API is available."""
        return self.client is not None

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract developer-relevant keywords from text."""
        if not text:
            return []

        keywords = []

        # Extract hashtags
        hashtags = re.findall(r'#(\w+)', text)
        keywords.extend([h.lower() for h in hashtags])

        # Check for common dev terms
        dev_terms = [
            "api", "database", "deploy", "release", "update",
            "feature", "bug", "fix", "security", "performance",
            "open source", "beta", "alpha", "v1", "v2"
        ]
        text_lower = text.lower()
        for term in dev_terms:
            if term in text_lower:
                keywords.append(term)

        return list(set(keywords))[:5]

    def get_trending(self, limit: int = 10) -> list[Trend]:
        """
        Get trending developer topics from Twitter.

        Args:
            limit: Maximum number of trends to return

        Returns:
            List of Trend objects (empty if API not available)
        """
        if not self.is_available():
            return []

        trends = []

        try:
            # Search for recent popular tweets with dev hashtags
            for hashtag in self.DEV_HASHTAGS[:5]:  # Limit API calls
                if len(trends) >= limit:
                    break

                tweets = self.client.search_recent_tweets(
                    query=f"{hashtag} -is:retweet lang:en",
                    max_results=10,
                    tweet_fields=["public_metrics", "created_at"]
                )

                if not tweets.data:
                    continue

                for tweet in tweets.data:
                    metrics = tweet.public_metrics or {}
                    engagement = (
                        metrics.get("like_count", 0) +
                        metrics.get("retweet_count", 0) * 2 +
                        metrics.get("reply_count", 0) * 3
                    )

                    if engagement > 50:  # Only include engaging tweets
                        trend = Trend(
                            title=tweet.text[:200],
                            url=f"https://twitter.com/i/status/{tweet.id}",
                            score=engagement,
                            source="twitter",
                            keywords=self._extract_keywords(tweet.text)
                        )
                        trends.append(trend)

                        if len(trends) >= limit:
                            break

        except Exception:
            # Silently fail - Twitter is optional
            pass

        # Sort by engagement score
        trends.sort(key=lambda x: x.score, reverse=True)
        return trends[:limit]

    def get_trends_summary(self, limit: int = 10) -> str:
        """
        Get a text summary of current trends.

        Returns:
            Formatted string of trends
        """
        if not self.is_available():
            return "Twitter API not configured. Set TWITTER_BEARER_TOKEN to enable."

        trends = self.get_trending(limit=limit)

        if not trends:
            return "No developer trends found on Twitter right now."

        lines = ["Current Twitter Developer Trends:"]
        for i, trend in enumerate(trends, 1):
            # Truncate long tweets
            title = trend.title[:100] + "..." if len(trend.title) > 100 else trend.title
            keywords_str = ", ".join(trend.keywords[:3]) if trend.keywords else "general"
            lines.append(f"{i}. {title} (engagement: {trend.score}, tags: {keywords_str})")

        return "\n".join(lines)


def get_trends(limit: int = 10) -> list[Trend]:
    """Convenience function to get trends."""
    fetcher = TwitterTrends()
    return fetcher.get_trending(limit=limit)


def is_available() -> bool:
    """Check if Twitter API is available."""
    return TwitterTrends().is_available()


if __name__ == "__main__":
    # Test the fetcher
    fetcher = TwitterTrends()

    if fetcher.is_available():
        print("Fetching Twitter trends...")
        trends = fetcher.get_trending(limit=5)

        for trend in trends:
            print(f"\n- {trend.title[:100]}...")
            print(f"  Engagement: {trend.score}")
            print(f"  Keywords: {', '.join(trend.keywords)}")
    else:
        print("Twitter API not available.")
        print("Set TWITTER_BEARER_TOKEN environment variable to enable.")
