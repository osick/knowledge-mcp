"""Configuration management for Local MCP Server."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    rag_api_url: str = "http://localhost:8000"
    rag_api_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
