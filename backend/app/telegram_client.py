"""
Gestione del client Telethon (MTProto) e dello streaming dei file video.

Il client viene creato una sola volta all'avvio dell'app (vedi main.py,
evento startup) e riusato per tutte le richieste: mantiene una connessione
persistente, cosa che una funzione serverless non permetterebbe.

La parte piu' delicata e' la traduzione delle richieste HTTP Range in
richieste MTProto: Telegram impone che offset e request_size siano
multipli di 4096 byte, quindi non possiamo passare direttamente i byte
richiesti dal browser ma dobbiamo arrotondare e poi tagliare l'eccesso.
"""
from typing import AsyncIterator

from telethon import TelegramClient
from telethon.sessions import StringSession

from app.config import get_settings

settings = get_settings()

# Allineamento richiesto dal protocollo MTProto per le richieste di file a blocchi
CHUNK_ALIGNMENT = 4096

_client: TelegramClient | None = None
_channel_entity = None


def _parse_channel_setting(raw_value: str):
    """Un ID numerico (es. -1001234567890) va passato come int a Telethon;
    uno username (es. @NomeCanale) resta una stringa."""
    raw_value = raw_value.strip()
    try:
        return int(raw_value)
    except ValueError:
        return raw_value


async def resolve_channel(client: TelegramClient, raw_value: str):
    """
    Risolve il canale in un'entita' Telethon utilizzabile.

    Con uno username Telethon risolve sempre da solo. Con un ID numerico
    invece riesce a farlo solo se l'entita' e' gia' in cache nella sessione:
    per questo, se la risoluzione diretta fallisce, carichiamo prima tutti i
    dialoghi dell'account (client.get_dialogs()) cosi' Telegram "vede" anche
    i canali privati di cui l'account e' membro, poi ritentiamo.
    """
    channel = _parse_channel_setting(raw_value)
    try:
        return await client.get_entity(channel)
    except ValueError:
        if isinstance(channel, int):
            print("Canale non ancora in cache: carico la lista dei tuoi dialoghi Telegram...")
            await client.get_dialogs()
            return await client.get_entity(channel)
        raise


async def start_telegram_client() -> TelegramClient:
    """Da chiamare una sola volta, nell'evento startup di FastAPI."""
    global _client
    _client = TelegramClient(
        StringSession(settings.telegram_session_string),
        settings.telegram_api_id,
        settings.telegram_api_hash,
    )
    await _client.connect()
    if not await _client.is_user_authorized():
        raise RuntimeError(
            "La sessione Telegram non e' autorizzata. "
            "Genera una TELEGRAM_SESSION_STRING valida con lo script genera_sessione.py"
        )

    global _channel_entity
    _channel_entity = await resolve_channel(_client, settings.telegram_channel)

    return _client


async def stop_telegram_client() -> None:
    """Da chiamare nell'evento shutdown di FastAPI."""
    if _client is not None:
        await _client.disconnect()


def get_telegram_client() -> TelegramClient:
    if _client is None:
        raise RuntimeError("Il client Telegram non e' stato inizializzato")
    return _client


def get_channel_entity():
    if _channel_entity is None:
        raise RuntimeError("Il canale Telegram non e' stato risolto")
    return _channel_entity


async def stream_file_range(
    file_reference,
    file_size: int,
    range_start: int,
    range_end: int,
) -> AsyncIterator[bytes]:
    """
    Restituisce esattamente i byte compresi tra range_start e range_end
    (inclusi), scaricandoli da Telegram in blocchi allineati a 4096 byte.

    file_reference: oggetto restituito da client.get_input_entity /
        il documento del messaggio (vedi routers/stream.py per come si ottiene).
    """
    client = get_telegram_client()

    # Arrotonda l'offset per difetto al multiplo di 4096 piu' vicino
    aligned_start = (range_start // CHUNK_ALIGNMENT) * CHUNK_ALIGNMENT
    # Quanti byte in piu' stiamo scaricando all'inizio rispetto a quanto richiesto
    leading_skip = range_start - aligned_start

    bytes_needed = range_end - range_start + 1
    bytes_remaining_to_send = bytes_needed
    first_chunk = True

    async for chunk in client.iter_download(
        file_reference,
        offset=aligned_start,
        request_size=settings.stream_chunk_size,
    ):
        if first_chunk:
            # Nel primo chunk togliamo i byte iniziali che non erano stati richiesti
            chunk = chunk[leading_skip:]
            first_chunk = False

        if len(chunk) > bytes_remaining_to_send:
            # Ultimo chunk: tagliamo l'eccesso finale
            chunk = chunk[:bytes_remaining_to_send]

        if chunk:
            yield chunk

        bytes_remaining_to_send -= len(chunk)
        if bytes_remaining_to_send <= 0:
            break
