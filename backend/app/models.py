"""
Modello del database. Una sola tabella: e' tutto cio' che serve per un
catalogo personale di metadati (il video vero resta solo su Telegram).
"""
import enum

from sqlalchemy import Column, Integer, String, Text, DateTime, BigInteger, Enum, Boolean, func

from app.database import Base


class ParseStatus(str, enum.Enum):
    OK = "ok"            # tutti i campi estratti correttamente
    PARTIAL = "partial"  # alcuni campi mancanti, da controllare a mano
    FAILED = "failed"    # non e' stato possibile estrarre quasi nulla


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)

    # Riferimenti Telegram: servono per la sincronizzazione incrementale e per lo streaming
    telegram_message_id = Column(BigInteger, unique=True, nullable=False, index=True)
    telegram_file_id = Column(String, nullable=False)
    file_unique_id = Column(String, nullable=True)
    file_size = Column(BigInteger, nullable=False)  # serve per Content-Length / Content-Range
    mime_type = Column(String, default="video/mp4")

    # Metadati estratti dal parser
    title = Column(String, nullable=False, index=True)
    year = Column(Integer, nullable=True)
    duration = Column(String, nullable=True)
    genre = Column(String, nullable=True, index=True)
    quality = Column(String, nullable=True)
    description = Column(Text, nullable=True)

    # Thumbnail salvata su disco (percorso relativo, es. "thumbnails/123.jpg")
    thumbnail_path = Column(String, nullable=True)
    has_tmdb_poster = Column(Boolean, default=False, index=True)

    # Testo grezzo del messaggio originale: utile per correggere/ri-processare a mano
    raw_caption = Column(Text, nullable=True)
    parse_status = Column(Enum(ParseStatus), default=ParseStatus.OK, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())