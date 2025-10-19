"""HTTP client for Remote RAG API ingestion."""

import httpx
from typing import Optional


class IngestError(Exception):
    """Raised when ingestion fails."""
    pass


class IngestClient:
    """Client for sending documents to Remote RAG API for ingestion."""

    def __init__(self, api_url: str, api_key: str) -> None:
        """
        Initialize the ingest client.

        Args:
            api_url: Base URL of the Remote RAG API
            api_key: API key for authentication
        """
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
        return self._client

    async def ingest_text(
        self,
        text: str,
        filename: str,
        collection: str = "default",
        source: str = "local",
        **metadata: str,
    ) -> dict[str, any]:
        """
        Send text to Remote RAG API for ingestion.

        Args:
            text: Document text content
            filename: Original filename
            collection: Collection name (default: "default")
            source: Document source (default: "local")
            **metadata: Additional metadata fields

        Returns:
            Response from API containing status, doc_id, and chunks count

        Raises:
            IngestError: If ingestion fails
        """
        client = await self._get_client()

        payload = {
            "text": text,
            "metadata": {
                "filename": filename,
                "collection": collection,
                "source": source,
                **metadata,
            },
        }

        try:
            response = await client.post(
                f"{self.api_url}/api/v1/ingest",
                json=payload,
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            error_detail = "Unknown error"
            try:
                error_data = e.response.json()
                error_detail = error_data.get("detail", str(e))
            except Exception:
                error_detail = str(e)

            raise IngestError(
                f"Ingestion failed with status {e.response.status_code}: {error_detail}"
            ) from e

        except httpx.RequestError as e:
            raise IngestError(f"Network error during ingestion: {str(e)}") from e

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "IngestClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
