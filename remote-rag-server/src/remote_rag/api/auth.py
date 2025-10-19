"""API key authentication middleware."""

from collections.abc import Callable

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from remote_rag.config import settings


async def api_key_middleware(request: Request, call_next: Callable) -> JSONResponse:  # type: ignore[type-arg]
    """
    Middleware to validate API key authentication.

    Args:
        request: FastAPI request object
        call_next: Next middleware/handler in the chain

    Returns:
        Response from the next handler

    Raises:
        HTTPException: If API key is missing or invalid
    """
    # Skip authentication for health check endpoint
    if request.url.path == "/health":
        return await call_next(request)  # type: ignore[no-any-return]

    # Check for API key in header
    api_key = request.headers.get("X-API-Key")

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )

    # API key is valid, proceed with request
    response = await call_next(request)
    return response  # type: ignore[no-any-return]
