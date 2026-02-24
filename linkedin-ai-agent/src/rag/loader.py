"""
GitHub Repository Loader

Fetches and clones public GitHub repositories for analysis.
"""

import os
import shutil
from pathlib import Path
from git import Repo
from git.exc import GitCommandError


class RepoLoader:
    """Handles cloning and updating GitHub repositories."""

    def __init__(self, cache_dir: str = "./repos_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_repo_name(self, github_url: str) -> str:
        """Extract repo name from GitHub URL."""
        # Handle URLs like https://github.com/user/repo or https://github.com/user/repo.git
        url = github_url.rstrip("/").rstrip(".git")
        return url.split("/")[-1]

    def _get_repo_path(self, github_url: str) -> Path:
        """Get local path for cached repo."""
        repo_name = self._get_repo_name(github_url)
        return self.cache_dir / repo_name

    def load(self, github_url: str, force_refresh: bool = False) -> Path:
        """
        Clone or update a GitHub repository.

        Args:
            github_url: Public GitHub repository URL
            force_refresh: If True, delete and re-clone the repo

        Returns:
            Path to the local repository
        """
        repo_path = self._get_repo_path(github_url)

        if force_refresh and repo_path.exists():
            shutil.rmtree(repo_path)

        if repo_path.exists():
            # Pull latest changes
            try:
                repo = Repo(repo_path)
                origin = repo.remotes.origin
                origin.pull()
                print(f"Updated existing repo: {repo_path}")
            except GitCommandError as e:
                print(f"Error pulling repo, re-cloning: {e}")
                shutil.rmtree(repo_path)
                Repo.clone_from(github_url, repo_path)
        else:
            # Clone fresh
            print(f"Cloning repo: {github_url}")
            Repo.clone_from(github_url, repo_path)
            print(f"Cloned to: {repo_path}")

        return repo_path

    def get_git_diff(self, github_url: str, days: int = 7) -> str:
        """
        Get recent git changes from the repository.

        Args:
            github_url: GitHub repository URL
            days: Number of days to look back

        Returns:
            String containing recent commit messages and changed files
        """
        repo_path = self._get_repo_path(github_url)

        if not repo_path.exists():
            return ""

        try:
            repo = Repo(repo_path)

            # Get commits from last N days
            commits = list(repo.iter_commits(max_count=20))

            if not commits:
                return ""

            diff_content = []
            for commit in commits[:10]:  # Last 10 commits
                diff_content.append(f"Commit: {commit.hexsha[:7]}")
                diff_content.append(f"Message: {commit.message.strip()}")
                diff_content.append(f"Files changed: {len(commit.stats.files)}")
                diff_content.append("---")

            return "\n".join(diff_content)

        except Exception as e:
            print(f"Error getting git diff: {e}")
            return ""

    def get_file_list(self, github_url: str) -> list[Path]:
        """
        Get list of code files in the repository.

        Args:
            github_url: GitHub repository URL

        Returns:
            List of file paths
        """
        repo_path = self._get_repo_path(github_url)

        if not repo_path.exists():
            return []

        # Code file extensions to include
        code_extensions = {
            ".py", ".js", ".ts", ".tsx", ".jsx",
            ".java", ".go", ".rs", ".cpp", ".c", ".h",
            ".rb", ".php", ".swift", ".kt", ".scala",
            ".md", ".rst", ".txt"
        }

        # Directories to skip
        skip_dirs = {
            ".git", "node_modules", "__pycache__", ".venv",
            "venv", "env", ".env", "dist", "build", ".next",
            "coverage", ".pytest_cache", ".mypy_cache"
        }

        files = []
        for file_path in repo_path.rglob("*"):
            if file_path.is_file():
                # Skip if in excluded directory
                if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
                    continue
                # Include if has valid extension
                if file_path.suffix.lower() in code_extensions:
                    files.append(file_path)

        return files

    def clone_or_pull(self, github_url: str) -> Path:
        """Alias for load() - clone or update a repo."""
        return self.load(github_url)

    def get_recent_commits(self, github_url: str, days: int = 7) -> list[dict]:
        """
        Get recent commits from the repository.

        Args:
            github_url: GitHub repository URL
            days: Number of days to look back

        Returns:
            List of commit dicts with 'hash', 'message', 'author', 'date'
        """
        repo_path = self._get_repo_path(github_url)

        if not repo_path.exists():
            return []

        try:
            repo = Repo(repo_path)
            commits = []

            for commit in repo.iter_commits(max_count=20):
                commits.append({
                    "hash": commit.hexsha[:7],
                    "message": commit.message.strip(),
                    "author": str(commit.author),
                    "date": commit.committed_datetime.isoformat(),
                    "files_changed": len(commit.stats.files)
                })

            return commits

        except Exception as e:
            print(f"Error getting commits: {e}")
            return []

    def get_repo_stats(self, github_url: str) -> dict:
        """
        Get statistics about a repository.

        Args:
            github_url: GitHub repository URL

        Returns:
            Dict with file_count, has_readme, has_tests, languages
        """
        repo_path = self._get_repo_path(github_url)

        if not repo_path.exists():
            return {}

        files = self.get_file_list(github_url)

        # Count by extension
        extensions = {}
        for f in files:
            ext = f.suffix.lower()
            extensions[ext] = extensions.get(ext, 0) + 1

        # Check for common files
        all_files = [f.name.lower() for f in repo_path.rglob("*") if f.is_file()]

        return {
            "file_count": len(files),
            "has_readme": any(f.startswith("readme") for f in all_files),
            "has_tests": any("test" in f for f in all_files),
            "has_docs": (repo_path / "docs").exists(),
            "languages": extensions
        }

    def get_interesting_files(self, github_url: str, limit: int = 5) -> list[str]:
        """
        Get a list of potentially interesting files for content.

        Prioritizes:
        - Main entry points (main.py, index.js, etc.)
        - API routes
        - Core modules

        Args:
            github_url: GitHub repository URL
            limit: Max files to return

        Returns:
            List of relative file paths
        """
        repo_path = self._get_repo_path(github_url)

        if not repo_path.exists():
            return []

        files = self.get_file_list(github_url)

        # Score files by interestingness
        scored_files = []
        interesting_patterns = [
            "main", "index", "app", "server", "api",
            "routes", "handler", "controller", "service",
            "core", "engine", "utils", "helpers"
        ]

        for f in files:
            score = 0
            name_lower = f.stem.lower()

            # Check for interesting patterns
            for pattern in interesting_patterns:
                if pattern in name_lower:
                    score += 10

            # Prefer shorter paths (likely more important)
            depth = len(f.relative_to(repo_path).parts)
            score -= depth * 2

            # Prefer certain extensions
            if f.suffix in [".py", ".ts", ".js"]:
                score += 5

            scored_files.append((str(f.relative_to(repo_path)), score))

        # Sort by score and return top files
        scored_files.sort(key=lambda x: x[1], reverse=True)
        return [f[0] for f in scored_files[:limit]]
