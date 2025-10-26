"""Configuration management for Document Intelligence MCP Server."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for Document Intelligence MCP Server."""

    # Required: Azure AI Search settings
    azure_search_endpoint: str
    azure_search_key: str

    # Optional: Default settings
    default_index_name: str = "default"
    default_top_results: int = 5
    max_top_results: int = 50

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Global settings instance
settings = Settings()
