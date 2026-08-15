"""
Setup della connessione al database tramite SQLAlchemy.

Si usa SQLite: sufficiente per un catalogo personale con un solo utente
e nessuna scrittura concorrente rilevante.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import get_settings

settings = get_settings()

# check_same_thread=False necessario perche' FastAPI puo' servire richieste
# da thread diversi; per SQLite con un solo processo scrivente non e' un problema.
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency FastAPI: fornisce una sessione DB e la chiude sempre a fine richiesta."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
