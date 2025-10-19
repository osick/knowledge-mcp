"""Embedding service using Azure OpenAI."""


from openai import AsyncAzureOpenAI

from remote_rag.config import settings


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""

    pass


class EmbedderService:
    """Service for generating embeddings using Azure OpenAI."""

    def __init__(self) -> None:
        """Initialize the embedder service with Azure OpenAI client."""
        self.client = AsyncAzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint,
        )
        self.deployment = settings.azure_openai_embedding_deployment
        self.dimensions = settings.azure_openai_embedding_dimensions

    async def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding vector for a single text.

        Args:
            text: The text to embed

        Returns:
            Embedding vector as list of floats

        Raises:
            EmbeddingError: If embedding generation fails
        """
        if not text or not text.strip():
            raise EmbeddingError("Cannot embed empty or whitespace-only text")

        try:
            response = await self.client.embeddings.create(
                input=text,
                model=self.deployment,
                dimensions=self.dimensions,
            )

            # Extract the embedding vector from the response
            embedding = response.data[0].embedding

            if not embedding or len(embedding) != self.dimensions:
                raise EmbeddingError(
                    f"Invalid embedding dimensions: expected {self.dimensions}, "
                    f"got {len(embedding) if embedding else 0}"
                )

            return embedding

        except Exception as e:
            if isinstance(e, EmbeddingError):
                raise
            raise EmbeddingError(f"Failed to generate embedding: {str(e)}") from e

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embedding vectors for multiple texts in a batch.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingError: If embedding generation fails
        """
        if not texts:
            raise EmbeddingError("Cannot embed empty list of texts")

        # Filter out empty strings
        valid_texts = [text for text in texts if text and text.strip()]

        if not valid_texts:
            raise EmbeddingError("All texts are empty or whitespace-only")

        if len(valid_texts) != len(texts):
            raise EmbeddingError(
                f"Some texts are empty: {len(texts) - len(valid_texts)} out of {len(texts)}"
            )

        try:
            response = await self.client.embeddings.create(
                input=valid_texts,
                model=self.deployment,
                dimensions=self.dimensions,
            )

            # Extract embeddings in the correct order
            embeddings = [item.embedding for item in response.data]

            if len(embeddings) != len(valid_texts):
                raise EmbeddingError(
                    f"Embedding count mismatch: expected {len(valid_texts)}, "
                    f"got {len(embeddings)}"
                )

            # Validate all embeddings have correct dimensions
            for i, emb in enumerate(embeddings):
                if not emb or len(emb) != self.dimensions:
                    raise EmbeddingError(
                        f"Invalid embedding at index {i}: expected {self.dimensions} dimensions, "
                        f"got {len(emb) if emb else 0}"
                    )

            return embeddings

        except Exception as e:
            if isinstance(e, EmbeddingError):
                raise
            raise EmbeddingError(f"Failed to generate batch embeddings: {str(e)}") from e

    async def close(self) -> None:
        """Close the Azure OpenAI client."""
        await self.client.close()

    async def __aenter__(self) -> "EmbedderService":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Async context manager exit."""
        await self.close()
