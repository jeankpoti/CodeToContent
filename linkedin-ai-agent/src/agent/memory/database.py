"""
Database Module

SQLite storage for posts, engagement metrics, and learned insights.
"""

import os
import sqlite3
import uuid
from datetime import datetime
from typing import Optional
from contextlib import contextmanager


class Database:
    """SQLite database for agent memory."""

    def __init__(self, db_path: str = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file. Defaults to ./agent_memory.db
        """
        self.db_path = db_path or os.getenv("AGENT_DB_PATH", "./agent_memory.db")
        self._init_tables()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_tables(self):
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Posts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    id TEXT PRIMARY KEY,
                    chat_id TEXT NOT NULL,
                    repo_url TEXT,
                    content TEXT NOT NULL,
                    trend_matched TEXT,
                    linkedin_post_id TEXT,
                    reasoning TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    posted_at TIMESTAMP
                )
            """)

            # Engagement metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id TEXT PRIMARY KEY,
                    post_id TEXT NOT NULL,
                    likes INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    shares INTEGER DEFAULT 0,
                    impressions INTEGER DEFAULT 0,
                    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES posts(id)
                )
            """)

            # Learned insights table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS insights (
                    id TEXT PRIMARY KEY,
                    chat_id TEXT NOT NULL,
                    insight_type TEXT NOT NULL,
                    insight_key TEXT NOT NULL,
                    score REAL DEFAULT 0.0,
                    sample_size INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(chat_id, insight_type, insight_key)
                )
            """)

            # User repos table (supports 1-5 repos per user)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_repos (
                    id TEXT PRIMARY KEY,
                    chat_id TEXT NOT NULL,
                    repo_url TEXT NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_indexed_at TIMESTAMP,
                    UNIQUE(chat_id, repo_url)
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_chat_id ON posts(chat_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_post_id ON metrics(post_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_insights_chat_id ON insights(chat_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_repos_chat_id ON user_repos(chat_id)")

    # ==================== Posts ====================

    def create_post(
        self,
        chat_id: str,
        content: str,
        repo_url: str = None,
        trend_matched: str = None,
        reasoning: str = None
    ) -> str:
        """
        Create a new post record.

        Returns:
            Post ID
        """
        post_id = str(uuid.uuid4())
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO posts (id, chat_id, repo_url, content, trend_matched, reasoning)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (post_id, chat_id, repo_url, content, trend_matched, reasoning)
            )
        return post_id

    def mark_post_published(self, post_id: str, linkedin_post_id: str):
        """Mark a post as published to LinkedIn."""
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE posts SET linkedin_post_id = ?, posted_at = ?
                WHERE id = ?
                """,
                (linkedin_post_id, datetime.utcnow(), post_id)
            )

    def get_post(self, post_id: str) -> Optional[dict]:
        """Get a post by ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM posts WHERE id = ?", (post_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_recent_posts(self, chat_id: str, limit: int = 10) -> list[dict]:
        """Get recent posts for a user."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM posts WHERE chat_id = ?
                ORDER BY created_at DESC LIMIT ?
                """,
                (chat_id, limit)
            ).fetchall()
            return [dict(row) for row in rows]

    def get_last_post(self, chat_id: str) -> Optional[dict]:
        """Get the most recent post for a user."""
        posts = self.get_recent_posts(chat_id, limit=1)
        return posts[0] if posts else None

    # ==================== Metrics ====================

    def update_metrics(
        self,
        post_id: str,
        likes: int = 0,
        comments: int = 0,
        shares: int = 0,
        impressions: int = 0
    ):
        """Update engagement metrics for a post."""
        metric_id = str(uuid.uuid4())
        with self._get_connection() as conn:
            # Delete old metrics for this post
            conn.execute("DELETE FROM metrics WHERE post_id = ?", (post_id,))
            # Insert new metrics
            conn.execute(
                """
                INSERT INTO metrics (id, post_id, likes, comments, shares, impressions)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (metric_id, post_id, likes, comments, shares, impressions)
            )

    def get_metrics(self, post_id: str) -> Optional[dict]:
        """Get metrics for a post."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM metrics WHERE post_id = ?", (post_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_posts_with_metrics(self, chat_id: str, limit: int = 20) -> list[dict]:
        """Get posts with their engagement metrics."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT p.*, m.likes, m.comments, m.shares, m.impressions
                FROM posts p
                LEFT JOIN metrics m ON p.id = m.post_id
                WHERE p.chat_id = ? AND p.posted_at IS NOT NULL
                ORDER BY p.posted_at DESC
                LIMIT ?
                """,
                (chat_id, limit)
            ).fetchall()
            return [dict(row) for row in rows]

    # ==================== Insights ====================

    def update_insight(
        self,
        chat_id: str,
        insight_type: str,
        insight_key: str,
        score: float,
        sample_size: int = 1
    ):
        """Update or create an insight."""
        insight_id = str(uuid.uuid4())
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO insights (id, chat_id, insight_type, insight_key, score, sample_size, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(chat_id, insight_type, insight_key) DO UPDATE SET
                    score = (score * sample_size + excluded.score) / (sample_size + 1),
                    sample_size = sample_size + 1,
                    updated_at = excluded.updated_at
                """,
                (insight_id, chat_id, insight_type, insight_key, score, sample_size, datetime.utcnow())
            )

    def get_insights(self, chat_id: str, insight_type: str = None) -> list[dict]:
        """Get insights for a user, optionally filtered by type."""
        with self._get_connection() as conn:
            if insight_type:
                rows = conn.execute(
                    """
                    SELECT * FROM insights
                    WHERE chat_id = ? AND insight_type = ?
                    ORDER BY score DESC
                    """,
                    (chat_id, insight_type)
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM insights
                    WHERE chat_id = ?
                    ORDER BY insight_type, score DESC
                    """,
                    (chat_id,)
                ).fetchall()
            return [dict(row) for row in rows]

    def get_top_insights(self, chat_id: str, limit: int = 5) -> list[dict]:
        """Get top-performing insights across all types."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM insights
                WHERE chat_id = ? AND sample_size >= 3
                ORDER BY score DESC
                LIMIT ?
                """,
                (chat_id, limit)
            ).fetchall()
            return [dict(row) for row in rows]

    # ==================== User Repos ====================

    def add_repo(self, chat_id: str, repo_url: str) -> tuple[bool, str]:
        """
        Add a repository for a user.

        Returns:
            (success, message)
        """
        # Check current count
        with self._get_connection() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM user_repos WHERE chat_id = ?", (chat_id,)
            ).fetchone()[0]

            if count >= 5:
                return False, "Maximum 5 repos allowed. Remove one first with /removerepo"

            try:
                repo_id = str(uuid.uuid4())
                conn.execute(
                    """
                    INSERT INTO user_repos (id, chat_id, repo_url)
                    VALUES (?, ?, ?)
                    """,
                    (repo_id, chat_id, repo_url)
                )
                return True, f"Added repo: {repo_url}"
            except sqlite3.IntegrityError:
                return False, "Repo already added"

    def remove_repo(self, chat_id: str, repo_url: str) -> tuple[bool, str]:
        """Remove a repository for a user."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM user_repos WHERE chat_id = ? AND repo_url = ?",
                (chat_id, repo_url)
            )
            if cursor.rowcount > 0:
                return True, f"Removed repo: {repo_url}"
            return False, "Repo not found"

    def get_repos(self, chat_id: str) -> list[str]:
        """Get all repos for a user."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT repo_url FROM user_repos WHERE chat_id = ? ORDER BY added_at",
                (chat_id,)
            ).fetchall()
            return [row["repo_url"] for row in rows]

    def update_repo_indexed(self, chat_id: str, repo_url: str):
        """Mark a repo as recently indexed."""
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE user_repos SET last_indexed_at = ?
                WHERE chat_id = ? AND repo_url = ?
                """,
                (datetime.utcnow(), chat_id, repo_url)
            )
