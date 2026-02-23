"""
LinkedIn AI Content Agent - CLI Entry Point

Generate LinkedIn posts from your GitHub repositories.
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rag.loader import RepoLoader
from rag.chunker import CodeChunker
from rag.store import VectorStore
from rag.retriever import CodeRetriever
from generator.post_generator import PostGenerator


def index_repository(repo_url: str, force_refresh: bool = False) -> None:
    """
    Clone and index a GitHub repository.

    Args:
        repo_url: GitHub repository URL
        force_refresh: If True, re-clone and re-index
    """
    print(f"\n{'='*60}")
    print(f"Indexing repository: {repo_url}")
    print(f"{'='*60}\n")

    # Step 1: Load repository
    print("Step 1: Loading repository...")
    loader = RepoLoader()
    repo_path = loader.load(repo_url, force_refresh=force_refresh)
    print(f"Repository loaded at: {repo_path}\n")

    # Step 2: Get file list
    print("Step 2: Finding code files...")
    files = loader.get_file_list(repo_url)
    print(f"Found {len(files)} code files\n")

    if not files:
        print("No code files found in repository!")
        return

    # Step 3: Chunk files
    print("Step 3: Chunking code files...")
    chunker = CodeChunker()
    chunks = chunker.chunk_files(files, repo_path)
    documents = chunker.create_chunk_documents(chunks)
    print(f"Created {len(documents)} document chunks\n")

    # Step 4: Store embeddings
    print("Step 4: Generating embeddings and storing...")
    store = VectorStore()
    store.add_documents(documents, repo_url)
    print("Indexing complete!\n")


def generate_post(
    repo_url: str,
    focus: str = None,
    style: str = "adaptive"
) -> str:
    """
    Generate a LinkedIn post for a repository.

    Args:
        repo_url: GitHub repository URL
        focus: Optional focus area for the post
        style: Post style ("short", "long", "adaptive")

    Returns:
        Generated LinkedIn post
    """
    print(f"\n{'='*60}")
    print(f"Generating LinkedIn post for: {repo_url}")
    print(f"{'='*60}\n")

    # Load repository and get git diff
    print("Checking for recent changes...")
    loader = RepoLoader()
    git_diff = loader.get_git_diff(repo_url)

    if git_diff:
        print(f"Found recent commits:\n{git_diff[:500]}...\n")
    else:
        print("No recent commits, will highlight existing code\n")

    # Retrieve relevant code context
    print("Retrieving relevant code context...")
    retriever = CodeRetriever()
    context = retriever.get_code_for_post(repo_url, focus=focus)

    if not context["main_context"]:
        print("No context found! Make sure the repository is indexed.")
        print("Run with --index flag first.")
        return ""

    print(f"Found context from {len(context['files_analyzed'])} files\n")

    # Generate post
    print("Generating LinkedIn post...")
    generator = PostGenerator()
    post = generator.generate_post(
        repo_url=repo_url,
        code_context=context["main_context"],
        code_snippets=context["code_snippets"],
        git_diff=git_diff,
        post_style=style
    )

    return post


def main():
    parser = argparse.ArgumentParser(
        description="LinkedIn AI Content Agent - Generate LinkedIn posts from your GitHub repos"
    )

    parser.add_argument(
        "--repo",
        type=str,
        required=True,
        help="GitHub repository URL (e.g., https://github.com/user/repo)"
    )

    parser.add_argument(
        "--index",
        action="store_true",
        help="Index/re-index the repository before generating"
    )

    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Force refresh: re-clone and re-index the repository"
    )

    parser.add_argument(
        "--focus",
        type=str,
        default=None,
        help="Focus area for the post (e.g., 'authentication', 'API design')"
    )

    parser.add_argument(
        "--style",
        type=str,
        choices=["short", "long", "adaptive"],
        default="adaptive",
        help="Post style: short (tips), long (tutorials), adaptive (auto)"
    )

    parser.add_argument(
        "--variations",
        type=int,
        default=1,
        help="Number of post variations to generate (1-3)"
    )

    args = parser.parse_args()

    # Validate repo URL
    if not args.repo.startswith("https://github.com/"):
        print("Error: Please provide a valid GitHub URL (https://github.com/user/repo)")
        sys.exit(1)

    # Index if requested or if this is a new repo
    if args.index or args.refresh:
        index_repository(args.repo, force_refresh=args.refresh)

    # Check if we need to index first
    store = VectorStore()
    if not store.load_collection(args.repo):
        print("Repository not indexed yet. Indexing now...")
        index_repository(args.repo)

    # Generate post(s)
    if args.variations > 1:
        print(f"\nGenerating {args.variations} post variations...\n")

        loader = RepoLoader()
        git_diff = loader.get_git_diff(args.repo)

        retriever = CodeRetriever()
        context = retriever.get_code_for_post(args.repo, focus=args.focus)

        generator = PostGenerator()
        posts = generator.generate_multiple_variations(
            repo_url=args.repo,
            code_context=context["main_context"],
            code_snippets=context["code_snippets"],
            git_diff=git_diff,
            num_variations=min(args.variations, 3)
        )

        for i, post in enumerate(posts, 1):
            print(f"\n{'='*60}")
            print(f"VARIATION {i}")
            print(f"{'='*60}\n")
            print(post)
            print()

    else:
        post = generate_post(args.repo, focus=args.focus, style=args.style)

        if post:
            print(f"\n{'='*60}")
            print("GENERATED LINKEDIN POST")
            print(f"{'='*60}\n")
            print(post)
            print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
