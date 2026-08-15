"""
Entry point dell'app FastAPI.

Nota su autenticazione: su richiesta esplicita dell'utente non e' presente
nessun livello di autenticazione applicativa. L'accesso va protetto a
livello di rete (es. VPN/Tailscale, IP allowlist) se il server e' esposto
pubblicamente.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import Base, engine
from app.routers import movies, stream
from app.telegram_client import start_telegram_client, stop_telegram_client

settings = get_settings()

# Crea le tabelle al primo avvio se non esistono ancora
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connessione Telegram aperta una sola volta e riusata per tutta la vita del processo
    await start_telegram_client()
    yield
    await stop_telegram_client()


app = FastAPI(title="Catalogo Film Telegram", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Le thumbnail sono file statici serviti direttamente, non passano da Telegram
app.mount("/thumbnails", StaticFiles(directory=settings.thumbnails_dir), name="thumbnails")

app.include_router(movies.router)
app.include_router(stream.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
