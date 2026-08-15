"""
Da eseguire UNA SOLA VOLTA, manualmente, per generare la sessione Telegram.

Chiede numero di telefono e codice di accesso (e password 2FA se attiva),
poi stampa una TELEGRAM_SESSION_STRING da copiare nel file .env.
Da quel momento in poi il server si connette senza bisogno di rifare il login.

Uso:
    python -m app.sync.genera_sessione
"""
import asyncio

from telethon import TelegramClient
from telethon.sessions import StringSession

from app.config import get_settings


async def main():
    settings = get_settings()
    async with TelegramClient(
        StringSession(), settings.telegram_api_id, settings.telegram_api_hash
    ) as client:
        session_string = client.session.save()
        print("\nSessione generata con successo.")
        print("Copia questa stringa nella variabile TELEGRAM_SESSION_STRING del tuo file .env:\n")
        print(session_string)
        print("\nATTENZIONE: trattala come una password, da' accesso completo al tuo account.")


if __name__ == "__main__":
    asyncio.run(main())
