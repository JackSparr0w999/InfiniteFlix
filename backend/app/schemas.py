"""
Schemi Pydantic: definiscono la forma dei dati esposti dalle API.
Separati dai modelli SQLAlchemy per non esporre mai direttamente colonne
interne (es. raw_caption, parse_status) nelle liste pubbliche.
"""
from typing import Optional

from pydantic import BaseModel, ConfigDict


class MovieCard(BaseModel):
    """Versione 'leggera' usata nella griglia della homepage."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    year: Optional[int] = None
    quality: Optional[str] = None
    genre: Optional[str] = None
    thumbnail_path: Optional[str] = None


class MovieDetail(BaseModel):
    """Versione completa usata nella pagina di dettaglio del film."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    year: Optional[int] = None
    duration: Optional[str] = None
    genre: Optional[str] = None
    quality: Optional[str] = None
    description: Optional[str] = None
    thumbnail_path: Optional[str] = None
    file_size: int


class MovieList(BaseModel):
    """Risposta paginata della lista film."""
    items: list[MovieCard]
    total: int
    page: int
    page_size: int
