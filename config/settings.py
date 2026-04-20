"""Settings management using Pydantic BaseSettings"""
import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Masumi Payment (REQUIRED for marketplace)
    # Pricing is configured in Payment Service admin - not here
    payment_service_url: str = Field(default="http://localhost:3001/api/v1")
    payment_api_key: Optional[str] = Field(default=None)
    agent_identifier: Optional[str] = Field(default=None)
    seller_vkey: Optional[str] = Field(default=None)
    network: str = Field(default="Preprod")

    # LLM (REQUIRED — Claude is primary)
    anthropic_api_key: Optional[str] = Field(default=None)
    anthropic_model: str = Field(default="claude-sonnet-4-20250514")
    openai_api_key: Optional[str] = Field(default=None)

    # Web Search (REQUIRED — pick one)
    serper_api_key: Optional[str] = Field(default=None)
    serpapi_api_key: Optional[str] = Field(default=None)

    # Expanded research data providers (OPTIONAL)
    newsapi_api_key: Optional[str] = Field(default=None)
    github_token: Optional[str] = Field(default=None)
    youtube_api_key: Optional[str] = Field(default=None)
    similarweb_api_key: Optional[str] = Field(default=None)

    # Future premium diligence providers (OPTIONAL placeholders)
    crunchbase_api_key: Optional[str] = Field(default=None)
    google_ads_developer_token: Optional[str] = Field(default=None)
    google_ads_client_id: Optional[str] = Field(default=None)
    google_ads_client_secret: Optional[str] = Field(default=None)
    google_ads_refresh_token: Optional[str] = Field(default=None)
    google_ads_login_customer_id: Optional[str] = Field(default=None)

    # === v1.0.2 — Sokosumi orchestration (hire other agents) ===
    # Bearer key for the Sokosumi marketplace API. The agent uses its OWN
    # account/credit balance to pay hired agents on Preprod or Mainnet.
    # Get from https://preprod.sokosumi.com (or sokosumi.com) → API keys.
    sokosumi_api_key: Optional[str] = Field(default=None)
    # Sokosumi API base. Default is the Preprod testing environment.
    sokosumi_api_url: str = Field(default="https://preprod.sokosumi.com/api/v1")
    # Master switch for v1.0.2 orchestration. Set to "true" to enable hiring.
    orchestration_enabled: bool = Field(default=False)
    # Comma-separated Sokosumi agent IDs that will be hired for every run.
    # Defaults to the two preprod research agents wired into v1.0.2.
    orchestration_external_agent_ids: str = Field(
        default="cmmqsoahf000504lcehryuaks,cmn7ae2or000904kyct3jumyt"
    )
    # Per-hire credit cap so a single run cannot drain the wallet.
    orchestration_max_credits_per_agent: int = Field(default=200)
    # Polling cadence + total wait budget per hired agent (seconds).
    orchestration_poll_interval_seconds: int = Field(default=15)
    orchestration_timeout_seconds: int = Field(default=900)  # 15 min
    # Optional human-readable tag prefix for the jobs we create on Sokosumi.
    orchestration_job_name_prefix: str = Field(default="VC-Validation-Agent")

    # Development mode (bypass payment for testing)
    dev_mode: bool = Field(default=False)

    # Agent configuration
    max_crew_timeout: int = Field(default=600)  # 10 minutes

    def external_agent_ids(self) -> list[str]:
        """Parsed list of Sokosumi agent IDs to hire."""
        raw = (self.orchestration_external_agent_ids or "").strip()
        if not raw:
            return []
        return [piece.strip() for piece in raw.split(",") if piece.strip()]

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
