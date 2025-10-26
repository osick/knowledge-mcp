"""Azure AI Search client wrapper for document operations."""

from typing import Any

from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient

from .models import Document, SearchResult


class AzureSearchError(Exception):
    """Raised when Azure Search operations fail."""

    pass


class AzureSearchClient:
    """Simple wrapper for Azure AI Search operations."""

    def __init__(self, endpoint: str, credential: str) -> None:
        """
        Initialize Azure Search client.

        Args:
            endpoint: Azure Search service endpoint (e.g., https://service.search.windows.net)
            credential: API key for authentication

        Raises:
            ValueError: If endpoint or credential is empty
        """
        if not endpoint:
            raise ValueError("endpoint cannot be empty")
        if not credential:
            raise ValueError("credential cannot be empty")

        self.endpoint = endpoint
        self.credential = AzureKeyCredential(credential)

    def _get_search_client(self, index_name: str) -> SearchClient:
        """
        Get a SearchClient for a specific index.

        Args:
            index_name: Name of the index

        Returns:
            SearchClient instance
        """
        return SearchClient(
            endpoint=self.endpoint, index_name=index_name, credential=self.credential
        )

    def _get_index_client(self) -> SearchIndexClient:
        """
        Get a SearchIndexClient for index management operations.

        Returns:
            SearchIndexClient instance
        """
        return SearchIndexClient(endpoint=self.endpoint, credential=self.credential)

    async def search(
        self, index_name: str, query: str, top: int = 5
    ) -> list[SearchResult]:
        """
        Perform hybrid search in Azure AI Search.

        Args:
            index_name: Name of the index to search
            query: Search query string
            top: Number of results to return (1-50)

        Returns:
            List of SearchResult objects

        Raises:
            ValueError: If parameters are invalid
            AzureSearchError: If search operation fails
        """
        # Validate inputs
        if not query:
            raise ValueError("query cannot be empty")
        if not index_name:
            raise ValueError("index_name cannot be empty")
        if top < 1 or top > 50:
            raise ValueError("top must be between 1 and 50")

        try:
            # Get search client for this index
            search_client = self._get_search_client(index_name)

            # Perform search - Azure SDK search() returns an async iterator
            results_iterator = search_client.search(search_text=query, top=top)

            # Parse results into SearchResult objects
            search_results = []
            async for result in results_iterator:
                # Extract required fields with defaults
                doc_id = result.get("id", "")
                score = result.get("@search.score", 0.0)
                content = result.get("content", "")

                # Collect all other fields as metadata
                metadata = {
                    key: value
                    for key, value in result.items()
                    if key not in ("id", "content", "@search.score")
                }

                search_results.append(
                    SearchResult(
                        document_id=doc_id,
                        score=score,
                        content=content,
                        metadata=metadata,
                    )
                )

            return search_results

        except ResourceNotFoundError as e:
            raise AzureSearchError(f"Index '{index_name}' not found") from e
        except HttpResponseError as e:
            raise AzureSearchError(f"Search failed in index '{index_name}': {str(e)}") from e
        except Exception as e:
            raise AzureSearchError(f"Unexpected error during search: {str(e)}") from e

    async def get_document(
        self, index_name: str, document_id: str
    ) -> Document | None:
        """
        Retrieve a specific document by ID.

        Args:
            index_name: Name of the index
            document_id: Document ID to retrieve

        Returns:
            Document object if found, None otherwise

        Raises:
            ValueError: If parameters are invalid
            AzureSearchError: If retrieval operation fails (except not found)
        """
        # Validate inputs
        if not index_name:
            raise ValueError("index_name cannot be empty")
        if not document_id:
            raise ValueError("document_id cannot be empty")

        try:
            # Get search client for this index
            search_client = self._get_search_client(index_name)

            # Get document by ID - Azure SDK method is async
            result = await search_client.get_document(key=document_id)

            # Extract content and metadata
            content = result.get("content", "")
            metadata = {
                key: value
                for key, value in result.items()
                if key not in ("id", "content")
            }

            return Document(
                document_id=document_id,
                content=content,
                metadata=metadata,
                index_name=index_name,
            )

        except ResourceNotFoundError:
            # Document not found - return None (not an error)
            return None
        except HttpResponseError as e:
            raise AzureSearchError(
                f"Failed to get document '{document_id}' from index '{index_name}': {str(e)}"
            ) from e
        except Exception as e:
            raise AzureSearchError(
                f"Unexpected error retrieving document: {str(e)}"
            ) from e

    async def list_indexes(self) -> list[str]:
        """
        List all available Azure AI Search indexes.

        Returns:
            List of index names

        Raises:
            AzureSearchError: If listing operation fails
        """
        try:
            # Get index client
            index_client = self._get_index_client()

            # List all indexes - Azure SDK method returns async iterator
            indexes_iterator = index_client.list_indexes()

            # Extract index names
            index_names = []
            async for index in indexes_iterator:
                index_names.append(index.name)
            return index_names

        except HttpResponseError as e:
            raise AzureSearchError(f"Failed to list indexes: {str(e)}") from e
        except Exception as e:
            raise AzureSearchError(
                f"Unexpected error listing indexes: {str(e)}"
            ) from e
