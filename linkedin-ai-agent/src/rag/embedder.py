"""
Code Embedder

Generates embeddings for code chunks using OpenAI.
"""

import os
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()


class CodeEmbedder:
    """Generates embeddings for code chunks."""

    def __init__(self, model: str = "text-embedding-3-small"):
        """
        Initialize the embedder.

        Args:
            model: OpenAI embedding model to use
        """
        self.model = model
        self.embeddings = OpenAIEmbeddings(
            model=model,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

    def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        return self.embeddings.embed_query(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        return self.embeddings.embed_documents(texts)

    def get_embeddings_model(self) -> OpenAIEmbeddings:
        """
        Get the LangChain embeddings model for use with vector stores.

        Returns:
            OpenAIEmbeddings instance
        """
        return self.embeddings
