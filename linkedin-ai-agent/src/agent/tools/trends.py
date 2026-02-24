"""
Trend Tools

LangChain tools for fetching trending developer topics.
"""

from langchain.tools import tool
from typing import List, Literal

from trends.hackernews import HackerNewsTrends
from trends.twitter import TwitterTrends


@tool
def fetch_trends_tool(source: Literal["hackernews", "twitter", "all"] = "hackernews", limit: int = 10) -> str:
    """
    Fetch trending developer topics from a specific source.

    Args:
        source: Which source to fetch from - "hackernews" (free), "twitter" (requires API key), or "all"
        limit: Maximum number of trends to return (default 10)

    Returns:
        Formatted string of current trends with titles, scores, and keywords
    """
    results = []

    if source in ("hackernews", "all"):
        hn = HackerNewsTrends()
        trends = hn.get_trending(limit=limit)
        if trends:
            results.append("=== HackerNews Trends ===")
            for i, trend in enumerate(trends, 1):
                keywords = ", ".join(trend.keywords[:3]) if trend.keywords else "general"
                results.append(f"{i}. {trend.title}")
                results.append(f"   Score: {trend.score} | Keywords: {keywords}")

    if source in ("twitter", "all"):
        tw = TwitterTrends()
        if tw.is_available():
            trends = tw.get_trending(limit=limit)
            if trends:
                results.append("\n=== Twitter Trends ===")
                for i, trend in enumerate(trends, 1):
                    keywords = ", ".join(trend.keywords[:3]) if trend.keywords else "general"
                    title = trend.title[:100] + "..." if len(trend.title) > 100 else trend.title
                    results.append(f"{i}. {title}")
                    results.append(f"   Engagement: {trend.score} | Keywords: {keywords}")
        else:
            results.append("\n=== Twitter ===")
            results.append("Twitter API not configured (optional - set TWITTER_BEARER_TOKEN)")

    if not results:
        return "No trends found. Try again later."

    return "\n".join(results)


@tool
def get_all_trends_tool() -> str:
    """
    Get all current developer trends from all available sources.
    This is a convenience tool that fetches from HackerNews (free) and Twitter (if configured).

    Returns:
        Comprehensive list of current developer trends
    """
    return fetch_trends_tool.invoke({"source": "all", "limit": 10})


def get_trend_keywords() -> List[str]:
    """
    Get a flat list of all current trend keywords.
    Useful for matching against code.

    Returns:
        List of keyword strings
    """
    keywords = set()

    # HackerNews (always available)
    hn = HackerNewsTrends()
    for trend in hn.get_trending(limit=15):
        keywords.update(trend.keywords)

    # Twitter (if available)
    tw = TwitterTrends()
    if tw.is_available():
        for trend in tw.get_trending(limit=10):
            keywords.update(trend.keywords)

    return list(keywords)
