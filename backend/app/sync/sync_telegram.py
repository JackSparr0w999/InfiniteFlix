"""
Script di sincronizzazione incrementale.

Alla prima esecuzione legge tutto il canale dal messaggio piu' vecchio al
piu' recente. Alle esecuzioni successive riparte subito dopo l'ultimo
telegram_message_id gia' salvato nel DB, senza rileggere tutto lo storico.

Uso:
    python -m app.sync.sync_telegram
"""
import asyncio
import os

from telethon import TelegramClient
from telethon.sessions import StringSession

from app.config import get_settings
from app.database import Base, engine, SessionLocal
from app.models import Movie
from app.sync.parser import parse_caption
from app.telegram_client import resolve_channel

settings = get_settings()


def _get_last_synced_message_id(db) -> int:
    last = db.query(Movie).order_by(Movie.telegram_message_id.desc()).first()
    return last.telegram_message_id if last else 0


async def _download_thumbnail(
    client, message, movie_id: int, album_photo_message=None, max_attempts: int = 3
) -> str | None:
    """
    Scarica la copertina del film e restituisce il percorso relativo salvato.

    Priorita':
    1. Se il messaggio fa parte di un "album" Telegram (foto poster + video
       inviati insieme, es. il logo dello studio prima del titolo) usiamo
       quella foto: e' la copertina "vera" pensata da chi ha postato il film.
    2. Altrimenti ripieghiamo sulla thumbnail automatica generata da Telegram
       per il video, che pero' spesso e' solo un fotogramma iniziale scuro.

    I timeout di Telegram su queste richieste sono abbastanza frequenti e
    quasi sempre transitori: ritentiamo alcune volte con una breve pausa
    prima di arrenderci.
    """
    has_album_photo = album_photo_message is not None
    has_document_thumb = bool(message.document and message.document.thumbs)

    if not has_album_photo and not has_document_thumb:
        return None

    os.makedirs(settings.thumbnails_dir, exist_ok=True)
    filename = f"{movie_id}.jpg"
    destination = os.path.join(settings.thumbnails_dir, filename)

    for attempt in range(1, max_attempts + 1):
        try:
            if has_album_photo:
                # Scarica la foto intera dell'album (non e' un "thumb" del
                # documento, e' un messaggio a se' stante con una sua foto)
                await client.download_media(album_photo_message, file=destination)
            else:
                await client.download_media(message, file=destination, thumb=-1)
            return filename
        except Exception:
            if attempt == max_attempts:
                raise
            await asyncio.sleep(2 * attempt)


def _is_mp4_video(message) -> bool:
    if not message.document:
        return False
    if message.document.mime_type != "video/mp4":
        return False
    return True


async def sync_channel():
    client = TelegramClient(
        StringSession(settings.telegram_session_string),
        settings.telegram_api_id,
        settings.telegram_api_hash,
        timeout=30,
        request_retries=3,
        retry_delay=2,
    )
    await client.connect()
    if not await client.is_user_authorized():
        raise RuntimeError(
            "Sessione non autorizzata. Esegui prima app/sync/genera_sessione.py"
        )

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        last_id = _get_last_synced_message_id(db)
        is_first_run = last_id == 0
        print(
            "Prima sincronizzazione: indicizzo tutto il canale."
            if is_first_run
            else f"Sincronizzazione incrementale: riparto dopo il messaggio {last_id}."
        )

        channel_entity = await resolve_channel(client, settings.telegram_channel)

        new_count = 0

        # Tiene traccia delle foto "album" incontrate (poster/logo inviati
        # insieme al video, con lo stesso grouped_id) in attesa del video
        # corrispondente, che nell'ordine del canale arriva quasi sempre
        # a ridosso della foto (message_id molto vicini).
        pending_album_photos: dict[int, object] = {}

        async for message in client.iter_messages(
            channel_entity, min_id=last_id, reverse=True
        ):
            # Messaggio con foto ma senza documento video: probabile poster
            # di un album, lo mettiamo da parte per quando arrivera' il video.
            if message.photo and not message.document:
                if message.grouped_id:
                    pending_album_photos[message.grouped_id] = message
                continue

            if not _is_mp4_video(message):
                continue

            parsed = parse_caption(message.text or "")

            movie = Movie(
                telegram_message_id=message.id,
                telegram_file_id=str(message.document.id),
                file_unique_id=getattr(message.document, "access_hash", None) and str(message.document.access_hash),
                file_size=message.document.size,
                mime_type=message.document.mime_type,
                title=parsed.title or f"Film senza titolo ({message.id})",
                year=parsed.year,
                duration=parsed.duration,
                genre=parsed.genre,
                quality=parsed.quality,
                description=message.text,
                raw_caption=message.text,
                parse_status=parsed.status,
            )
            db.add(movie)
            db.flush()  # per ottenere movie.id prima del commit, usato nel nome della thumbnail

            album_photo = pending_album_photos.pop(message.grouped_id, None) if message.grouped_id else None

            # La copertina e' un extra: se Telegram da' un errore temporaneo
            # (timeout, capita spesso ed e' normale) non vogliamo perdere
            # tutto il progresso della sincronizzazione. Il film viene
            # salvato comunque, senza copertina.
            try:
                thumbnail_filename = await _download_thumbnail(
                    client, message, movie.id, album_photo_message=album_photo
                )
                movie.thumbnail_path = thumbnail_filename
            except Exception as exc:
                print(f"  ! Copertina non scaricata per '{movie.title}' ({exc}); film salvato comunque")
                movie.thumbnail_path = None

            db.commit()
            new_count += 1
            print(f"  + [{parsed.status.value}] {movie.title}")

        print(f"\nFatto. Film aggiunti in questa esecuzione: {new_count}")

    finally:
        db.close()
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(sync_channel())