"""
Repository Tools

LangChain tools for managing and analyzing GitHub repositories.
"""

import os
from datetime import datetime, timedelta
from langchain.tools import tool

from agent.memory.database import Database
from rag.loader import RepoLoader
from rag.store import VectorStore


# Global instances (initialized lazily)
_db = None
_loader = None
_store = None


def _get_db() -> Database:
    global _db
    if _db is None:
        _db = Database()
    return _db


def _get_loader() -> RepoLoader:
    global _loader
    if _loader is None:
        _loader = RepoLoader()
    return _loader


def _get_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store


@tool
def list_repos_tool(chat_id: str) -> str:
    """
    List all repositories connected by a user.

    Args:
        chat_id: The user's Telegram chat ID

    Returns:
        List of connected repositories with their status
    """
    db = _get_db()
    repos = db.get_repos(chat_id)

    if not repos:
        return "No repositories connected. Use /addrepo <github-url> to add one."

    lines = [f"Connected repositories ({len(repos)}/5):"]
    for i, repo_url in enumerate(repos, 1):
        repo_name = repo_url.rstrip("/").split("/")[-1]
        lines.append(f"{i}. {repo_name} - {repo_url}")

    return "\n".join(lines)


@tool
def analyze_repo_tool(repo_url: str) -> str:
    """
    Analyze a GitHub repository for content potential.

    Checks:
    - Recent commit activity
    - Code structure
    - Interesting patterns
    - README quality

    Args:
        repo_url: The GitHub repository URL

    Returns:
        Analysis report with content potential score
    """
    loader = _get_loader()

    try:
        # Load/update the repo
        repo_path = loader.clone_or_pull(repo_url)

        # Get recent commits
        commits = loader.get_recent_commits(repo_url, days=7)

        # Get repo stats
        stats = loader.get_repo_stats(repo_url)

        # Calculate content potential score
        score = 0
        reasons = []

        # Recent activity is valuable
        if commits:
            score += min(len(commits) * 10, 40)
            reasons.append(f"{len(commits)} commits this week")
        else:
            reasons.append("No recent commits")

        # Large repos have more content potential
        file_count = stats.get("file_count", 0)
        if file_count > 50:
            score += 20
            reasons.append(f"{file_count} files to explore")
        elif file_count > 10:
            score += 10
            reasons.append(f"{file_count} files")

        # Check for interesting files
        has_readme = stats.get("has_readme", False)
        has_tests = stats.get("has_tests", False)

        if has_readme:
            score += 10
            reasons.append("Has README")
        if has_tests:
            score += 10
            reasons.append("Has tests")

        # Get sample of interesting code
        sample_files = loader.get_interesting_files(repo_url, limit=3)

        # Build report
        report = [
            f"=== Repository Analysis: {repo_url.split('/')[-1]} ===",
            f"Content Potential Score: {score}/100",
            "",
            "Factors:",
        ]
        for reason in reasons:
            report.append(f"  - {reason}")

        if commits:
            report.append("")
            report.append("Recent Commits:")
            for commit in commits[:3]:
                report.append(f"  - {commit['message'][:60]}...")

        if sample_files:
            report.append("")
            report.append("Interesting Files:")
            for f in sample_files:
                report.append(f"  - {f}")

        return "\n".join(report)

    except Exception as e:
        return f"Error analyzing repo: {str(e)}"


@tool
def compare_repos_tool(chat_id: str) -> str:
    """
    Compare all connected repositories and rank them by content potential.

    This helps decide which repo to post about today.

    Args:
        chat_id: The user's Telegram chat ID

    Returns:
        Ranked list of repos with recommendations
    """
    db = _get_db()
    repos = db.get_repos(chat_id)

    if not repos:
        return "No repositories connected. Use /addrepo to add repositories first."

    if len(repos) == 1:
        return f"Only one repo connected: {repos[0]}\nThis will be used for content generation."

    # Analyze each repo
    analyses = []
    for repo_url in repos:
        analysis = analyze_repo_tool.invoke({"repo_url": repo_url})

        # Extract score from analysis
        score = 0
        for line in analysis.split("\n"):
            if "Score:" in line:
                try:
                    score = int(line.split(":")[1].split("/")[0].strip())
                except:
                    pass
                break

        repo_name = repo_url.rstrip("/").split("/")[-1]
        analyses.append({
            "name": repo_name,
            "url": repo_url,
            "score": score,
            "analysis": analysis
        })

    # Sort by score
    analyses.sort(key=lambda x: x["score"], reverse=True)

    # Build comparison report
    report = ["=== Repository Comparison ===", ""]
    for i, repo in enumerate(analyses, 1):
        indicator = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        report.append(f"{indicator} {repo['name']} - Score: {repo['score']}/100")

    report.append("")
    report.append(f"Recommendation: Post about '{analyses[0]['name']}' today")
    report.append(f"Reason: Highest content potential score ({analyses[0]['score']}/100)")

    return "\n".join(report)
