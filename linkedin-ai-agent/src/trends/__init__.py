"""
Trend Sources

Fetches trending developer topics from various sources.
"""

from .hackernews import HackerNewsTrends
from .twitter import TwitterTrends

__all__ = ["HackerNewsTrends", "TwitterTrends"]
