"""
Configuration management using Pydantic Settings.
Environment variables are loaded from .env file or system environment.
"""

from typing import Literal, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation."""

    # Application
    app_name: str = "AI-Powered Support Co-Pilot API"
    app_version: str = "1.0.0"
    app_env: Literal["dev", "staging", "production"] = Field(
        default="dev", description="Environment name"
    )
    api_port: int = Field(default=8000, description="API server port")
    log_level: str = Field(default="INFO", description="Logging level")

    # Security
    api_key: str = Field(..., description="API authentication key")

    # Supabase Configuration
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_service_role_key: str = Field(
        ..., description="Supabase service role key (NOT anon key)"
    )

    # LLM Provider Configuration
    llm_provider: Literal["openai", "huggingface", "anthropic", "ollama"] = Field(
        default="openai", description="LLM provider to use"
    )
    openai_api_key: Optional[str] = Field(
        default=None, description="OpenAI API key (required if provider=openai)"
    )
    hf_api_token: Optional[str] = Field(
        default=None, description="HuggingFace API token (required if provider=huggingface)"
    )
    anthropic_api_key: Optional[str] = Field(
        default=None, description="Anthropic API key (required if provider=anthropic)"
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434", description="Ollama server URL"
    )

    # LLM Model Configuration
    llm_model: str = Field(
        default="gpt-3.5-turbo", description="Model name/identifier"
    )
    llm_temperature: float = Field(
        default=0.0, ge=0.0, le=2.0, description="Model temperature (0=deterministic)"
    )
    llm_max_tokens: int = Field(
        default=200, ge=50, le=4000, description="Max tokens in response"
    )
    llm_timeout: int = Field(
        default=10, ge=5, le=60, description="Request timeout in seconds"
    )

    # Retry Configuration
    max_retries: int = Field(
        default=3, ge=0, le=10, description="Max retry attempts for LLM calls"
    )
    retry_backoff: float = Field(
        default=2.0, ge=1.0, le=10.0, description="Exponential backoff multiplier"
    )

    # Feature Flags
    enable_metrics: bool = Field(
        default=True, description="Enable Prometheus metrics endpoint"
    )
    enable_confidence_scores: bool = Field(
        default=False, description="Include confidence scores in responses"
    )

    # CORS Configuration
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "https://ia-powered-support.vercel.app"],
        description="Allowed CORS origins",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_llm_credentials(self) -> "Settings":
        """Ensure required API keys are present for selected provider."""
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY required when LLM_PROVIDER=openai")
        elif self.llm_provider == "huggingface" and not self.hf_api_token:
            raise ValueError("HF_API_TOKEN required when LLM_PROVIDER=huggingface")
        elif self.llm_provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY required when LLM_PROVIDER=anthropic"
            )
        # Ollama doesn't require API keys
        return self

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure valid logging level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v_upper


# Global settings instance
settings = Settings()
