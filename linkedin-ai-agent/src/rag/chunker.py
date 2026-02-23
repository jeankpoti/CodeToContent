"""
Code Chunker

Splits code files into manageable chunks for embedding.
"""

from pathlib import Path
from dataclasses import dataclass
from langchain.text_splitter import RecursiveCharacterTextSplitter


@dataclass
class CodeChunk:
    """Represents a chunk of code with metadata."""
    content: str
    file_path: str
    file_type: str
    chunk_index: int
    total_chunks: int
    start_line: int
    end_line: int


class CodeChunker:
    """Splits code files into chunks for embedding."""

    def __init__(
        self,
        chunk_size: int = 1500,
        chunk_overlap: int = 200
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Language-specific separators for better chunking
        self.separators = [
            # Class and function definitions
            "\nclass ",
            "\ndef ",
            "\nasync def ",
            "\nfunction ",
            "\nconst ",
            "\nexport ",
            # Block separators
            "\n\n",
            "\n",
            " ",
        ]

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=self.separators,
            length_function=len,
        )

    def _get_file_type(self, file_path: Path) -> str:
        """Determine file type from extension."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript-react",
            ".jsx": "javascript-react",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".cpp": "cpp",
            ".c": "c",
            ".rb": "ruby",
            ".php": "php",
            ".swift": "swift",
            ".kt": "kotlin",
            ".md": "markdown",
            ".rst": "restructuredtext",
        }
        return ext_map.get(file_path.suffix.lower(), "text")

    def chunk_file(self, file_path: Path, repo_root: Path) -> list[CodeChunk]:
        """
        Split a single file into chunks.

        Args:
            file_path: Path to the code file
            repo_root: Root path of the repository

        Returns:
            List of CodeChunk objects
        """
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return []

        if not content.strip():
            return []

        # Get relative path for metadata
        try:
            relative_path = file_path.relative_to(repo_root)
        except ValueError:
            relative_path = file_path

        file_type = self._get_file_type(file_path)

        # Split content
        text_chunks = self.splitter.split_text(content)

        # Create CodeChunk objects with metadata
        chunks = []
        current_line = 1

        for i, chunk_text in enumerate(text_chunks):
            # Estimate line numbers
            chunk_lines = chunk_text.count("\n") + 1

            chunk = CodeChunk(
                content=chunk_text,
                file_path=str(relative_path),
                file_type=file_type,
                chunk_index=i,
                total_chunks=len(text_chunks),
                start_line=current_line,
                end_line=current_line + chunk_lines - 1,
            )
            chunks.append(chunk)

            # Update line counter (accounting for overlap)
            current_line += max(1, chunk_lines - (self.chunk_overlap // 50))

        return chunks

    def chunk_files(self, file_paths: list[Path], repo_root: Path) -> list[CodeChunk]:
        """
        Chunk multiple files.

        Args:
            file_paths: List of file paths to chunk
            repo_root: Root path of the repository

        Returns:
            List of all CodeChunk objects
        """
        all_chunks = []

        for file_path in file_paths:
            chunks = self.chunk_file(file_path, repo_root)
            all_chunks.extend(chunks)
            if chunks:
                print(f"Chunked {file_path.name}: {len(chunks)} chunks")

        print(f"Total chunks created: {len(all_chunks)}")
        return all_chunks

    def create_chunk_documents(self, chunks: list[CodeChunk]) -> list[dict]:
        """
        Convert chunks to document format for embedding.

        Args:
            chunks: List of CodeChunk objects

        Returns:
            List of document dicts with content and metadata
        """
        documents = []

        for chunk in chunks:
            # Create rich context for embedding
            header = f"File: {chunk.file_path} ({chunk.file_type})\n"
            header += f"Lines: {chunk.start_line}-{chunk.end_line}\n"
            header += "---\n"

            doc = {
                "content": header + chunk.content,
                "metadata": {
                    "file_path": chunk.file_path,
                    "file_type": chunk.file_type,
                    "chunk_index": chunk.chunk_index,
                    "total_chunks": chunk.total_chunks,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                }
            }
            documents.append(doc)

        return documents
