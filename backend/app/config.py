"""
Configurazione centralizzata dell'applicazione.

Tutte le variabili sensibili (credenziali Telegram, percorsi, ecc.) vengono
lette da un file .env e mai scritte hard-coded nel codice.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Credenziali Telegram (ottenute da https://my.telegram.org)
    telegram_api_id: int
    telegram_api_hash: str
    telegram_channel: str
    telegram_session_string: str = ""

    # Database
    database_url: str = "sqlite:///./data/catalog.db"

    # Thumbnail
    thumbnails_dir: str = "./thumbnails"

    # Streaming: dimensione dei chunk richiesti a Telegram (deve essere multiplo di 4096)
    stream_chunk_size: int = 1024 * 1024  # 1 MiB

    # CORS
    cors_origins: str = "http://localhost:3000"
    
    # TMDB API, per thumbnail, trama, ... (e in caso si volesse aggiungere: cast, imdb score,...)
    tmdb_api_key: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cache delle impostazioni: lette da .env una sola volta per processo."""
    return Settings()
