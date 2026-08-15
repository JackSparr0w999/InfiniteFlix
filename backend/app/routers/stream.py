"""
Endpoint di streaming: e' il cuore del progetto.

Non scarica MAI il file su disco. Per ogni richiesta:
1. legge dal DB dimensione del file e riferimento al messaggio Telegram;
2. recupera il messaggio (e quindi il documento) da Telegram;
3. traduce l'header HTTP Range in una richiesta di chunk allineata a Telegram;
4. restituisce una risposta 206 Partial Content in streaming.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Movie
from app.telegram_client import get_telegram_client, get_channel_entity, stream_file_range

router = APIRouter(tags=["stream"])
settings = get_settings()


@router.get("/stream/{movie_id}")
async def stream_movie(movie_id: int, request: Request, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if movie is None:
        raise HTTPException(status_code=404, detail="Film non trovato")

    file_size = movie.file_size
    range_header = request.headers.get("range")

    # Se il browser non manda Range, serviamo l'intero file (caso raro: primo
    # caricamento di alcuni browser prima di iniziare a fare seek)
    if range_header is None:
        range_start, range_end = 0, file_size - 1
        status_code = 200
    else:
        # Formato tipico: "bytes=1000-2000" oppure "bytes=1000-"
        range_value = range_header.replace("bytes=", "").strip()
        start_str, _, end_str = range_value.partition("-")
        range_start = int(start_str) if start_str else 0
        range_end = int(end_str) if end_str else file_size - 1
        range_end = min(range_end, file_size - 1)
        status_code = 206

    if range_start >= file_size or range_start > range_end:
        raise HTTPException(status_code=416, detail="Range non valido")

    # Recupera il messaggio Telegram (contiene il riferimento al documento video)
    client = get_telegram_client()
    message = await client.get_messages(get_channel_entity(), ids=movie.telegram_message_id)
    if message is None or message.document is None:
        raise HTTPException(status_code=502, detail="File non piu' disponibile su Telegram")

    headers = {
        "Content-Range": f"bytes {range_start}-{range_end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(range_end - range_start + 1),
        "Content-Type": movie.mime_type or "video/mp4",
    }

    return StreamingResponse(
        stream_file_range(message.document, file_size, range_start, range_end),
        status_code=status_code,
        headers=headers,
        media_type=movie.mime_type or "video/mp4",
    )
