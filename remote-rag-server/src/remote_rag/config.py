"""Configuration management using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    # Azure OpenAI configuration
    azure_openai_api_key: str = "test-key"  # Default for testing
    azure_openai_endpoint: str = "https://test.openai.azure.com"  # Default for testing
    azure_openai_embedding_deployment: str = "text-embedding-3-small"
    azure_openai_api_version: str = "2024-02-01"
    azure_openai_embedding_dimensions: int = 1536

    # Qdrant configuration
    qdrant_url: str = "http://localhost:6333"  # Default for testing
    qdrant_api_key: str = "test-key"  # Default for testing
    qdrant_default_collection: str = "default"

    # Chunking configuration
    chunk_size: int = 512
    chunk_overlap: int = 50

    # API configuration
    api_key: str = "test-api-key"  # Default for testing
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "json"  # json or console

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields in .env
    )


# Global settings instance
settings = Settings()
