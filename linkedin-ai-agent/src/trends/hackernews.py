"""
HackerNews Trends

Fetches trending developer topics from HackerNews.
FREE API - No authentication required!

API Docs: https://github.com/HackerNews/API
"""

import re
import requests
from typing import Optional
from dataclasses import dataclass


@dataclass
class Trend:
    """A trending topic."""
    title: str
    url: Optional[str]
    score: int
    source: str
    keywords: list[str]


class HackerNewsTrends:
    """Fetches trending topics from HackerNews."""

    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    # Keywords that indicate developer-relevant content
    DEV_KEYWORDS = {
        "python", "javascript", "typescript", "rust", "go", "golang",
        "api", "database", "sql", "nosql", "postgres", "mongodb",
        "react", "vue", "angular", "svelte", "nextjs", "node",
        "docker", "kubernetes", "k8s", "aws", "cloud", "devops",
        "ai", "ml", "llm", "gpt", "openai", "anthropic", "claude",
        "git", "github", "gitlab", "ci", "cd", "pipeline",
        "security", "auth", "oauth", "jwt", "encryption",
        "performance", "optimization", "scaling", "architecture",
        "testing", "tdd", "debugging", "refactoring",
        "startup", "saas", "open source", "oss",
        "frontend", "backend", "fullstack", "web", "mobile",
        "linux", "unix", "terminal", "cli", "shell",
    }

    def __init__(self, timeout: int = 10):
        """
        Initialize HackerNews trends fetcher.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()

    def _fetch_item(self, item_id: int) -> Optional[dict]:
        """Fetch a single HN item."""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/item/{item_id}.json",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract developer-relevant keywords from text."""
        if not text:
            return []

        text_lower = text.lower()
        words = set(re.findall(r'\b\w+\b', text_lower))

        found_keywords = []
        for keyword in self.DEV_KEYWORDS:
            if keyword in text_lower or keyword in words:
                found_keywords.append(keyword)

        return found_keywords

    def _is_dev_relevant(self, item: dict) -> bool:
        """Check if an item is developer-relevant."""
        title = item.get("title", "")
        url = item.get("url", "")

        # Check title for dev keywords
        keywords = self._extract_keywords(title)
        if keywords:
            return True

        # Check URL for dev-related domains
        dev_domains = [
            "github.com", "gitlab.com", "dev.to", "medium.com",
            "stackoverflow.com", "npmjs.com", "pypi.org",
            "docs.python.org", "developer.mozilla.org",
            "aws.amazon.com", "cloud.google.com", "azure.microsoft.com"
        ]
        for domain in dev_domains:
            if domain in url:
                return True

        return False

    def get_top_stories(self, limit: int = 30) -> list[int]:
        """Get top story IDs."""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/topstories.json",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()[:limit]
        except Exception:
            return []

    def get_trending(self, limit: int = 10) -> list[Trend]:
        """
        Get trending developer topics.

        Args:
            limit: Maximum number of trends to return

        Returns:
            List of Trend objects
        """
        story_ids = self.get_top_stories(limit=50)  # Fetch more to filter

        trends = []
        for story_id in story_ids:
            if len(trends) >= limit:
                break

            item = self._fetch_item(story_id)
            if not item:
                continue

            # Filter for developer-relevant content
            if not self._is_dev_relevant(item):
                continue

            keywords = self._extract_keywords(item.get("title", ""))

            trend = Trend(
                title=item.get("title", ""),
                url=item.get("url"),
                score=item.get("score", 0),
                source="hackernews",
                keywords=keywords
            )
            trends.append(trend)

        return trends

    def get_trends_summary(self, limit: int = 10) -> str:
        """
        Get a text summary of current trends.

        Returns:
            Formatted string of trends
        """
        trends = self.get_trending(limit=limit)

        if not trends:
            return "No developer trends found on HackerNews right now."

        lines = ["Current HackerNews Developer Trends:"]
        for i, trend in enumerate(trends, 1):
            keywords_str = ", ".join(trend.keywords[:3]) if trend.keywords else "general"
            lines.append(f"{i}. {trend.title} (score: {trend.score}, tags: {keywords_str})")

        return "\n".join(lines)


def get_trends(limit: int = 10) -> list[Trend]:
    """Convenience function to get trends."""
    fetcher = HackerNewsTrends()
    return fetcher.get_trending(limit=limit)


if __name__ == "__main__":
    # Test the fetcher
    print("Fetching HackerNews trends...")
    fetcher = HackerNewsTrends()
    trends = fetcher.get_trending(limit=5)

    for trend in trends:
        print(f"\n- {trend.title}")
        print(f"  Score: {trend.score}")
        print(f"  Keywords: {', '.join(trend.keywords)}")
