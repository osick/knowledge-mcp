"""Qdrant vector database service."""

from typing import List, Dict, Any, Optional
from uuid import uuid4
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from remote_rag.config import settings


class QdrantError(Exception):
    """Raised when Qdrant operations fail."""

    pass


class QdrantService:
    """Service for interacting with Qdrant vector database."""

    def __init__(self) -> None:
        """Initialize the Qdrant service with async client."""
        self.client = AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
        )
        self.vector_size = settings.azure_openai_embedding_dimensions

    async def create_collection(
        self,
        collection_name: str,
        distance: Distance = Distance.COSINE,
    ) -> None:
        """
        Create a new collection if it doesn't exist.

        Args:
            collection_name: Name of the collection
            distance: Distance metric to use (default: COSINE)

        Raises:
            QdrantError: If collection creation fails
        """
        try:
            # Check if collection exists
            collections = await self.client.get_collections()
            exists = any(col.name == collection_name for col in collections.collections)

            if exists:
                return  # Collection already exists

            # Create new collection
            await self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=distance,
                ),
            )

        except Exception as e:
            raise QdrantError(f"Failed to create collection '{collection_name}': {str(e)}") from e

    async def upsert_points(
        self,
        collection_name: str,
        embeddings: List[List[float]],
        metadata_list: List[Dict[str, Any]],
    ) -> List[str]:
        """
        Insert or update points in a collection.

        Args:
            collection_name: Name of the collection
            embeddings: List of embedding vectors
            metadata_list: List of metadata dicts (one per embedding)

        Returns:
            List of point IDs that were upserted

        Raises:
            QdrantError: If upsert fails
        """
        if len(embeddings) != len(metadata_list):
            raise QdrantError(
                f"Embeddings and metadata count mismatch: {len(embeddings)} vs {len(metadata_list)}"
            )

        if not embeddings:
            raise QdrantError("Cannot upsert empty list of points")

        try:
            # Ensure collection exists
            await self.create_collection(collection_name)

            # Generate UUIDs for points
            point_ids = [str(uuid4()) for _ in embeddings]

            # Create points
            points = [
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=metadata,
                )
                for point_id, embedding, metadata in zip(point_ids, embeddings, metadata_list)
            ]

            # Upsert points
            await self.client.upsert(
                collection_name=collection_name,
                points=points,
            )

            return point_ids

        except Exception as e:
            if isinstance(e, QdrantError):
                raise
            raise QdrantError(f"Failed to upsert points to '{collection_name}': {str(e)}") from e

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: float = 0.0,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in a collection.

        Args:
            collection_name: Name of the collection
            query_vector: Query embedding vector
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score (0.0 to 1.0)
            filter_conditions: Optional metadata filters

        Returns:
            List of search results with id, score, and payload

        Raises:
            QdrantError: If search fails
        """
        try:
            # Build filter if conditions provided
            query_filter = None
            if filter_conditions:
                conditions = []
                for key, value in filter_conditions.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value),
                        )
                    )
                query_filter = Filter(must=conditions)

            # Perform search
            results = await self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter,
            )

            # Format results
            return [
                {
                    "id": str(result.id),
                    "score": result.score,
                    "payload": result.payload,
                }
                for result in results
            ]

        except Exception as e:
            raise QdrantError(f"Failed to search in '{collection_name}': {str(e)}") from e

    async def get_document(
        self,
        collection_name: str,
        document_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific document by ID.

        Args:
            collection_name: Name of the collection
            document_id: Document ID (point ID)

        Returns:
            Document payload or None if not found

        Raises:
            QdrantError: If retrieval fails
        """
        try:
            points = await self.client.retrieve(
                collection_name=collection_name,
                ids=[document_id],
            )

            if not points:
                return None

            return points[0].payload

        except Exception as e:
            raise QdrantError(
                f"Failed to get document '{document_id}' from '{collection_name}': {str(e)}"
            ) from e

    async def list_collections(self) -> List[str]:
        """
        List all collections.

        Returns:
            List of collection names

        Raises:
            QdrantError: If listing fails
        """
        try:
            collections = await self.client.get_collections()
            return [col.name for col in collections.collections]

        except Exception as e:
            raise QdrantError(f"Failed to list collections: {str(e)}") from e

    async def delete_collection(self, collection_name: str) -> None:
        """
        Delete a collection.

        Args:
            collection_name: Name of the collection to delete

        Raises:
            QdrantError: If deletion fails
        """
        try:
            await self.client.delete_collection(collection_name=collection_name)

        except Exception as e:
            raise QdrantError(f"Failed to delete collection '{collection_name}': {str(e)}") from e

    async def close(self) -> None:
        """Close the Qdrant client."""
        await self.client.close()

    async def __aenter__(self) -> "QdrantService":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
