"""
Matching Tools

LangChain tools for matching trends to code.
"""

from langchain.tools import tool

from agent.memory.database import Database
from rag.retriever import CodeRetriever
from rag.store import VectorStore
from .trends import get_trend_keywords


# Global instances
_db = None
_retriever = None


def _get_db() -> Database:
    global _db
    if _db is None:
        _db = Database()
    return _db


def _get_retriever() -> CodeRetriever:
    global _retriever
    if _retriever is None:
        _retriever = CodeRetriever()
    return _retriever


@tool
def match_trends_tool(chat_id: str, trend_keyword: str = None) -> str:
    """
    Find code in user's repos that matches current trends.

    This tool searches all connected repos for code related to trending topics.

    Args:
        chat_id: The user's Telegram chat ID
        trend_keyword: Optional specific trend to match. If not provided, uses current top trends.

    Returns:
        Matching code snippets with their relevance to trends
    """
    db = _get_db()
    retriever = _get_retriever()

    repos = db.get_repos(chat_id)
    if not repos:
        return "No repositories connected. Add repos first with /addrepo."

    # Get trend keywords to search for
    if trend_keyword:
        keywords = [trend_keyword]
    else:
        keywords = get_trend_keywords()[:5]  # Top 5 trends

    if not keywords:
        keywords = ["interesting code", "main functionality", "api endpoints"]

    results = []
    matches_found = False

    for repo_url in repos:
        repo_name = repo_url.rstrip("/").split("/")[-1]
        repo_matches = []

        for keyword in keywords:
            try:
                # Search for code matching this keyword
                context = retriever.get_relevant_context(
                    query=keyword,
                    repo_url=repo_url,
                    k=2
                )

                if context:
                    for item in context:
                        repo_matches.append({
                            "keyword": keyword,
                            "file": item["metadata"].get("file_path", "unknown"),
                            "snippet": item["content"][:200] + "..." if len(item["content"]) > 200 else item["content"]
                        })
                        matches_found = True

            except Exception:
                continue

        if repo_matches:
            results.append(f"\n=== {repo_name} ===")
            for match in repo_matches[:3]:  # Limit matches per repo
                results.append(f"\nTrend: '{match['keyword']}'")
                results.append(f"File: {match['file']}")
                results.append(f"Snippet: {match['snippet']}")

    if not matches_found:
        return "No direct matches found between current trends and your code. Try using search_code with specific queries."

    return "\n".join(results)


@tool
def search_code_tool(repo_url: str, query: str, limit: int = 5) -> str:
    """
    Search for specific code in a repository using semantic search.

    Args:
        repo_url: The GitHub repository URL
        query: What to search for (e.g., "authentication logic", "api endpoints", "error handling")
        limit: Maximum number of results (default 5)

    Returns:
        Relevant code snippets matching the query
    """
    retriever = _get_retriever()

    try:
        # Get code context
        context = retriever.get_code_for_post(repo_url=repo_url, focus=query)

        if not context["main_context"]:
            return f"No code found matching '{query}' in this repository."

        results = [f"=== Search Results for '{query}' ===\n"]

        # Add main context
        results.append("Main Match:")
        results.append(context["main_context"][:500])
        if len(context["main_context"]) > 500:
            results.append("... (truncated)")

        # Add code snippets
        if context["code_snippets"]:
            results.append("\n\nCode Snippets:")
            for snippet in context["code_snippets"][:limit]:
                results.append(f"\n--- {snippet['file']} (lines {snippet['lines']}) ---")
                results.append(snippet["code"][:300])
                if len(snippet["code"]) > 300:
                    results.append("... (truncated)")

        # Add files analyzed
        if context["files_analyzed"]:
            results.append(f"\n\nFiles searched: {', '.join(context['files_analyzed'][:5])}")

        return "\n".join(results)

    except Exception as e:
        return f"Error searching code: {str(e)}"


@tool
def find_best_content_match(chat_id: str) -> str:
    """
    Find the best match between current trends and user's code.

    This is a high-level tool that:
    1. Fetches current trends
    2. Searches all connected repos
    3. Returns the best match for content creation

    Args:
        chat_id: The user's Telegram chat ID

    Returns:
        Best content opportunity with trend, repo, and code snippet
    """
    db = _get_db()
    retriever = _get_retriever()

    repos = db.get_repos(chat_id)
    if not repos:
        return "No repositories connected."

    # Get current trend keywords
    keywords = get_trend_keywords()

    if not keywords:
        # Fallback to generic interesting content
        keywords = ["main functionality", "interesting patterns", "api"]

    best_match = None
    best_score = 0

    for repo_url in repos:
        for keyword in keywords[:5]:
            try:
                context = retriever.get_relevant_context(
                    query=keyword,
                    repo_url=repo_url,
                    k=1
                )

                if context:
                    # Simple scoring based on content length and keyword match
                    content = context[0]["content"]
                    score = len(content)

                    if keyword.lower() in content.lower():
                        score *= 1.5  # Boost for direct keyword match

                    if score > best_score:
                        best_score = score
                        best_match = {
                            "repo": repo_url,
                            "trend": keyword,
                            "file": context[0]["metadata"].get("file_path", "unknown"),
                            "content": content
                        }

            except Exception:
                continue

    if not best_match:
        return "Could not find a good content match. Try adding more repositories or wait for relevant trends."

    repo_name = best_match["repo"].rstrip("/").split("/")[-1]
    return f"""=== Best Content Opportunity ===

Trend: {best_match['trend']}
Repository: {repo_name}
File: {best_match['file']}

Code Context:
{best_match['content'][:500]}{'...' if len(best_match['content']) > 500 else ''}

This is a good opportunity for a LinkedIn post connecting the trending topic '{best_match['trend']}' with your code."""
