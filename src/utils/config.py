"""
Configuration management for the MCP Slack Bot.

This module handles all environment variables and configuration settings
using Pydantic for validation and type safety.
"""

import os
from typing import Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


class Config(BaseSettings):
    """Application configuration with validation."""
    
    # Slack Configuration
    slack_bot_token: str = Field(..., env="SLACK_BOT_TOKEN")
    slack_app_token: str = Field(..., env="SLACK_APP_TOKEN")
    slack_signing_secret: str = Field(..., env="SLACK_SIGNING_SECRET")
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-1106-preview", env="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.3, env="OPENAI_TEMPERATURE")
    
    # Supabase Configuration
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_service_key: str = Field(..., env="SUPABASE_SERVICE_KEY")
    supabase_anon_key: str = Field(..., env="SUPABASE_ANON_KEY")
    
    # ClickUp Configuration
    clickup_api_token: str = Field(..., env="CLICKUP_API_TOKEN")
    clickup_team_id: str = Field(..., env="CLICKUP_TEAM_ID")
    
    # Application Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    environment: str = Field(default="development", env="ENVIRONMENT")
    port: int = Field(default=3000, env="PORT")
    
    # Cache Configuration
    cache_ttl_seconds: int = Field(default=300, env="CACHE_TTL_SECONDS")  # 5 minutes
    
    @validator("slack_bot_token")
    def validate_slack_bot_token(cls, v):
        if not v.startswith("xoxb-"):
            raise ValueError("Slack bot token must start with 'xoxb-'")
        return v
    
    @validator("slack_app_token")
    def validate_slack_app_token(cls, v):
        if not v.startswith("xapp-"):
            raise ValueError("Slack app token must start with 'xapp-'")
        return v
    
    @validator("openai_api_key")
    def validate_openai_api_key(cls, v):
        if not v.startswith("sk-"):
            raise ValueError("OpenAI API key must start with 'sk-'")
        return v
    
    @validator("supabase_url")
    def validate_supabase_url(cls, v):
        if not v.startswith("https://"):
            raise ValueError("Supabase URL must start with 'https://'")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @validator("openai_temperature")
    def validate_temperature(cls, v):
        if not 0.0 <= v <= 2.0:
            raise ValueError("OpenAI temperature must be between 0.0 and 2.0")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global configuration instance
config = Config()


def get_config() -> Config:
    """Get the global configuration instance."""
    return config


def is_production() -> bool:
    """Check if running in production environment."""
    return config.environment.lower() == "production"


def is_development() -> bool:
    """Check if running in development environment."""
    return config.environment.lower() == "development"
