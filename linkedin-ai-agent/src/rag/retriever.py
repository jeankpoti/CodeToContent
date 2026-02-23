"""
Code Retriever

Retrieves relevant code context for post generation.
"""

from .store import VectorStore


class CodeRetriever:
    """Retrieves relevant code context using semantic search."""

    def __init__(self, vector_store: VectorStore = None):
        """
        Initialize the retriever.

        Args:
            vector_store: VectorStore instance (creates new one if not provided)
        """
        self.vector_store = vector_store or VectorStore()

    def get_relevant_context(
        self,
        query: str,
        repo_url: str,
        k: int = 5
    ) -> list[dict]:
        """
        Retrieve relevant code context for a query.

        Args:
            query: Search query (e.g., "interesting features", "main functionality")
            repo_url: GitHub repository URL
            k: Number of results to return

        Returns:
            List of relevant code chunks with metadata
        """
        return self.vector_store.similarity_search(
            query=query,
            k=k,
            repo_url=repo_url
        )

    def get_code_for_post(
        self,
        repo_url: str,
        focus: str = None
    ) -> dict:
        """
        Get code context optimized for LinkedIn post generation.

        Args:
            repo_url: GitHub repository URL
            focus: Optional focus area (e.g., "authentication", "API endpoints")

        Returns:
            Dict with 'main_context', 'supporting_context', and 'code_snippets'
        """
        # Default queries for finding interesting code
        queries = [
            focus or "main features and core functionality",
            "interesting algorithms or clever solutions",
            "API endpoints or public interfaces",
        ]

        all_results = []
        for query in queries:
            results = self.get_relevant_context(query, repo_url, k=3)
            all_results.extend(results)

        # Deduplicate by file path
        seen_files = set()
        unique_results = []
        for result in all_results:
            file_path = result["metadata"].get("file_path", "")
            if file_path not in seen_files:
                seen_files.add(file_path)
                unique_results.append(result)

        # Organize results
        if not unique_results:
            return {
                "main_context": "",
                "supporting_context": "",
                "code_snippets": [],
                "files_analyzed": []
            }

        # Best result is main context
        main_result = unique_results[0]

        # Rest are supporting
        supporting_results = unique_results[1:4]

        # Extract clean code snippets
        code_snippets = []
        for result in unique_results[:3]:
            content = result["content"]
            # Remove the header we added during chunking
            if "---\n" in content:
                content = content.split("---\n", 1)[-1]
            code_snippets.append({
                "code": content.strip(),
                "file": result["metadata"].get("file_path", "unknown"),
                "lines": f"{result['metadata'].get('start_line', '?')}-{result['metadata'].get('end_line', '?')}"
            })

        return {
            "main_context": main_result["content"],
            "supporting_context": "\n\n".join([r["content"] for r in supporting_results]),
            "code_snippets": code_snippets,
            "files_analyzed": list(seen_files)
        }

    def get_langchain_retriever(self, repo_url: str, k: int = 5):
        """
        Get a LangChain-compatible retriever.

        Args:
            repo_url: GitHub repository URL
            k: Number of documents to retrieve

        Returns:
            LangChain retriever
        """
        return self.vector_store.get_retriever(repo_url=repo_url, k=k)
