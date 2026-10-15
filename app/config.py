from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    ai_provider: Literal["fake", "ollama"] = "ollama"
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"
    # Modèle pour la phrase des brouillons ; vide = même modèle que l'analyse.
    ollama_model_brouillon: str | None = None
    ai_timeout_s: float = 60.0


settings = Settings()
