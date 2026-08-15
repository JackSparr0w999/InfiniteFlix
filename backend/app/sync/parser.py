"""
Parser del testo dei messaggi Telegram.

Il formato atteso (con piccole variazioni ed emoji iniziali da ignorare):

    [TITOLO]
    Anno: XXXX
    Durata: XXX
    Genere: XXX
    Qualita: XXX
    @NomeCanale

Nota: questo parser e' generico e "best effort". Quando saranno disponibili
esempi reali dei messaggi, i pattern regex vanno rifiniti su quelli veri
(vedi commenti "DA ADATTARE" sotto). Nessun messaggio viene mai scartato
silenziosamente: se un campo non si trova, il film viene comunque salvato
con parse_status="partial" cosi' resta visibile e correggibile a mano.


OLTRE A SCORRERE I FILM SU TELEGRAM, per ogni film andrò a 
1. prelevare in primis la descrizione con la funzione "ottieni_trama_film()", 
2. la thumbanail con la funzione "ottieni_poster_url_film()", 
3. il genere con la funzione "ottieni_genere_film()"
tutto tramite l'API di The movie DB. 
"""
import re
from dataclasses import dataclass
from difflib import get_close_matches
import requests

from app.models import ParseStatus

# Configurazione API TMDB, che verrà presa dalle funzioni per popolare la trama, le thumbnail e i generi dei film
TMDB_API_KEY = "fb6ba7ad4d362f66740b5709674150d9"

# Mappa ufficiale degli ID generi di TMDB in Italiano
TMDB_GENRES = {
    28: "Azione",
    12: "Avventura",
    16: "Animazione",
    35: "Commedia",
    80: "Crime",
    99: "Documentario",
    18: "Dramma",
    10751: "Famiglia",
    14: "Fantasy",
    36: "Storia",
    27: "Horror",
    10402: "Musica",
    9648: "Mistero",
    10749: "Romance",
    878: "Fantascienza",
    10770: "Film TV",
    53: "Thriller",
    10752: "Guerra",
    37: "Western",
}

GENERI_UFFICIALI_TMDB = list(TMDB_GENRES.values())
MAPPA_MINUSCOLO_A_UFFICIALE = {g.lower(): g for g in GENERI_UFFICIALI_TMDB}

# Rimuove qualunque carattere emoji generico a inizio riga (e non solo),
# usando i blocchi Unicode dedicati alle emoji invece di un elenco fisso:
# regge anche emoji nuove non ancora viste.
EMOJI_PATTERN = re.compile(
    "[\U0001F000-\U0001FFFF"      # pittogrammi, simboli, trasporti, faccine
    "\U00002300-\U000023FF"       # simboli tecnici (orologi, clessidre, ecc. - es. la emoji orologio)
    "\U00002600-\U000027BF"       # simboli vari + dingbat
    "\U00002B00-\U00002BFF"       # stelle e frecce varie
    "\U0001F1E6-\U0001F1FF"       # bandiere
    "\uFE0F\u200D]+",             # variation selector ed emoji zero-width-joiner
    flags=re.UNICODE,
)

# DA ADATTARE: pattern per ciascun campo. Case-insensitive, tollerante a spazi
# e a due punti seguiti o meno da spazio.
FIELD_PATTERNS = {
    "year": re.compile(r"anno\s*:\s*(\d{4})", re.IGNORECASE),
    "duration": re.compile(r"durata\s*:\s*(.+)", re.IGNORECASE),
    "genre": re.compile(r"genere\s*:\s*(.+)", re.IGNORECASE),
    "quality": re.compile(r"qualit[aà]\s*:\s*(.+)", re.IGNORECASE),
}


@dataclass
class ParsedCaption:
    title: str | None
    year: int | None
    duration: str | None
    genre: str | None
    quality: str | None
    status: ParseStatus


def _clean_line(line: str) -> str:
    """Rimuove emoji e spazi superflui da una riga."""
    return EMOJI_PATTERN.sub("", line).strip(" \t*_-")


def trova_genere_simile(genere_raw: str | None, soglia_somiglianza: float = 0.65) -> str:
    """
    Pulisce il testo e cerca se il genere e' simile per caratteri 
    a uno dei generi ufficiali di TMDB.
    """
    if not genere_raw:
        return "Non definito"

    pulito = genere_raw.replace("#", "").strip().lower()
    if not pulito:
        return "Non definito"

    # Match esatto (es. "fantascienza" -> "Fantascienza")
    if pulito in MAPPA_MINUSCOLO_A_UFFICIALE:
        return MAPPA_MINUSCOLO_A_UFFICIALE[pulito]

    # Match somiglianza caratteri
    nomi_generi_lower = list(MAPPA_MINUSCOLO_A_UFFICIALE.keys())
    match_trovati = get_close_matches(pulito, nomi_generi_lower, n=1, cutoff=soglia_somiglianza)

    if match_trovati:
        return MAPPA_MINUSCOLO_A_UFFICIALE[match_trovati[0]]

    return pulito.capitalize()


def parse_caption(raw_caption: str) -> ParsedCaption:
    if not raw_caption or not raw_caption.strip():
        return ParsedCaption(None, None, None, None, None, ParseStatus.FAILED)

    lines = [_clean_line(l) for l in raw_caption.splitlines()]
    lines = [l for l in lines if l]  # rimuove righe vuote

    year = duration = genre = quality = None
    title = None

    for line in lines:
        # Salta la riga del canale (es. "@NomeCanale")
        if line.startswith("@"):
            continue

        matched_field = False
        for field, pattern in FIELD_PATTERNS.items():
            match = pattern.match(line)
            if match:
                value = match.group(1).strip()
                if field == "year":
                    year = int(value)
                elif field == "duration":
                    duration = value
                elif field == "genre":
                    genre = trova_genere_simile(value)
                elif field == "quality":
                    quality = value.replace("#", "").strip()
                matched_field = True
                break

        # La prima riga che non corrisponde a nessun campo noto e non e'
        # la riga del canale viene considerata il titolo.
        if not matched_field and title is None:
            title = line

    fields_found = sum(x is not None for x in (year, duration, genre, quality))
    if title is None:
        status = ParseStatus.FAILED
    elif fields_found < 4:
        status = ParseStatus.PARTIAL
    else:
        status = ParseStatus.OK

    return ParsedCaption(title, year, duration, genre, quality, status)


def ottieni_trama_film(titolo: str, anno: int = None) -> str:
    """
    Cerca un film su TMDB tramite titolo e anno facoltativo
    e restituisce la sinossi breve in italiano.
    """
    if not titolo:
        return "Trama non disponibile."

    url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": titolo,
        "language": "it-IT",  # Trama in italiano
    }
    if anno:
        params["year"] = anno

    try:
        response = requests.get(url, params=params, timeout=5).json()
        results = response.get("results", [])
        if results and results[0].get("overview"):
            return results[0]["overview"]  # Ritorna la trama breve
    except Exception as e:
        print(f"Errore nel recupero trama per '{titolo}': {e}")

    return "Trama non disponibile."


def ottieni_poster_url_film(titolo: str, anno: int | None = None) -> str | None:
    """
    Cerca un film su TMDB e restituisce l'URL del poster/copertina.
    Ritorna None se non trovato.
    """
    if not TMDB_API_KEY:
        return None

    try:
        url = "https://api.themoviedb.org/3/search/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "query": titolo,
            "language": "it-IT",
            "include_adult": "false"
        }
        if anno:
            params["year"] = anno

        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            dati = response.json()
            risultati = dati.get("results", [])
            if risultati:
                poster_path = risultati[0].get("poster_path")
                if poster_path:
                    # w500 e' la risoluzione ideale per nitidezza e velocita'
                    return f"https://image.tmdb.org/t/p/w500{poster_path}"
    except Exception as e:
        print(f"Errore TMDB poster per '{titolo}': {e}")

    return None


def ottieni_genere_film(titolo: str, anno: int | None = None) -> str | None:
    """
    Cerca un film su TMDB ed estrae ESCLUSIVAMENTE il genere principale (il primo).
    Ritorna None se non trovato.
    """
    if not TMDB_API_KEY or not titolo:
        return None

    try:
        url = "https://api.themoviedb.org/3/search/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "query": titolo,
            "language": "it-IT",
            "include_adult": "false"
        }
        if anno:
            params["year"] = anno

        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            dati = response.json()
            risultati = dati.get("results", [])
            if risultati:
                genre_ids = risultati[0].get("genre_ids", [])
                if genre_ids:
                    primo_id = genre_ids[0]
                    return TMDB_GENRES.get(primo_id)
    except Exception as e:
        print(f"Errore TMDB genere per '{titolo}': {e}")

    return None
