"""
Vector Store

Stores and manages code embeddings using ChromaDB.
"""

import os
from pathlib import Path
from chromadb import PersistentClient
from chromadb.config import Settings
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()


class VectorStore:
    """Manages code embeddings storage with ChromaDB."""

    def __init__(
        self,
        persist_dir: str = "./chroma_db",
        collection_name: str = "code_chunks"
    ):
        """
        Initialize the vector store.

        Args:
            persist_dir: Directory to persist the database
            collection_name: Name of the collection
        """
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name

        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

        # Initialize or load existing store
        self.vectorstore = None

    def _get_collection_name(self, repo_url: str) -> str:
        """Generate collection name from repo URL."""
        # Extract repo name and sanitize
        repo_name = repo_url.rstrip("/").rstrip(".git").split("/")[-1]
        # ChromaDB collection names must be alphanumeric with underscores
        return f"repo_{repo_name.replace('-', '_').replace('.', '_')}"

    def add_documents(
        self,
        documents: list[dict],
        repo_url: str
    ) -> None:
        """
        Add documents to the vector store.

        Args:
            documents: List of document dicts with 'content' and 'metadata'
            repo_url: GitHub repository URL (used for collection name)
        """
        collection_name = self._get_collection_name(repo_url)

        texts = [doc["content"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]

        # Add repo URL to metadata
        for metadata in metadatas:
            metadata["repo_url"] = repo_url

        print(f"Adding {len(texts)} documents to collection: {collection_name}")

        self.vectorstore = Chroma.from_texts(
            texts=texts,
            embedding=self.embeddings,
            metadatas=metadatas,
            collection_name=collection_name,
            persist_directory=str(self.persist_dir)
        )

        print(f"Documents added and persisted to {self.persist_dir}")

    def load_collection(self, repo_url: str) -> bool:
        """
        Load an existing collection for a repo.

        Args:
            repo_url: GitHub repository URL

        Returns:
            True if collection exists and was loaded, False otherwise
        """
        collection_name = self._get_collection_name(repo_url)

        try:
            self.vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=str(self.persist_dir)
            )

            # Check if collection has documents
            count = self.vectorstore._collection.count()
            if count > 0:
                print(f"Loaded collection {collection_name} with {count} documents")
                return True
            return False

        except Exception as e:
            print(f"Could not load collection: {e}")
            return False

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        repo_url: str = None
    ) -> list[dict]:
        """
        Search for similar documents.

        Args:
            query: Search query
            k: Number of results to return
            repo_url: Optional repo URL to load specific collection

        Returns:
            List of matching documents with content and metadata
        """
        if repo_url and not self.vectorstore:
            self.load_collection(repo_url)

        if not self.vectorstore:
            print("No vector store loaded")
            return []

        results = self.vectorstore.similarity_search_with_score(query, k=k)

        documents = []
        for doc, score in results:
            documents.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "similarity_score": float(score)
            })

        return documents

    def delete_collection(self, repo_url: str) -> None:
        """
        Delete a collection for a repo.

        Args:
            repo_url: GitHub repository URL
        """
        collection_name = self._get_collection_name(repo_url)

        try:
            client = PersistentClient(path=str(self.persist_dir))
            client.delete_collection(collection_name)
            print(f"Deleted collection: {collection_name}")
        except Exception as e:
            print(f"Error deleting collection: {e}")

    def get_retriever(self, repo_url: str = None, k: int = 5):
        """
        Get a LangChain retriever for the vector store.

        Args:
            repo_url: Optional repo URL to load specific collection
            k: Number of documents to retrieve

        Returns:
            LangChain retriever
        """
        if repo_url and not self.vectorstore:
            self.load_collection(repo_url)

        if not self.vectorstore:
            raise ValueError("No vector store loaded")

        return self.vectorstore.as_retriever(search_kwargs={"k": k})
