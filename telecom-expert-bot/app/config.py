from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List


class Settings(BaseSettings):
    app_name: str = Field(default="telecom-expert-bot")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    database_url: str = Field(default="sqlite+aiosqlite:///./telecom_bot.db")

    chroma_persist_directory: str = Field(default="./chroma_data")
    chroma_collection_name: str = Field(default="3gpp_specs")

    llm_provider: str = Field(default="openai")
    openai_api_key: Optional[str] = Field(default=None)
    openai_model: str = Field(default="gpt-4")

    azure_openai_api_key: Optional[str] = Field(default=None)
    azure_openai_endpoint: Optional[str] = Field(default=None)
    azure_openai_deployment: Optional[str] = Field(default=None)
    azure_openai_api_version: str = Field(default="2024-02-01")

    jwt_secret_key: str = Field(default="change-me-in-production")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=1440)

    cors_origins: List[str] = Field(default=["*"])

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
