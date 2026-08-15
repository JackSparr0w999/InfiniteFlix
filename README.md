# InfiniteFlix

### Description
I am creating a PWA that allows to gather all the films found in a single telegram channel (or more than one) or online, to easily watch them and choose them. 

### How to use it

_Nota: Per funzionare dovete conoscere un canale Telegram che contenga video (film) postati in messaggi del tipo <video mp4, anno, durata, genere,...> o eventualmente cambiare algoritmo di riconoscimento dei film in base a come sono stati postati._

**Opzione 0**. _Con Visual Studio Code._
E' sufficiente entrare nella cartella backend da terminale e scrivere: `python3 -m uvicorn app.main:app --reload`

Poi aprire un altro terminale, andare nella cartella frontend e scrivere: `npm rum dev`.

Fatto questo, sarà possibile vedere il link localhost dove poter visualizzare il sito.

**Opzione 1**. _Esperienza nativa "App" su Mac (Niente terminali aperti o Visual studio)._
Creo uno script (guarda quello sotto come esempio) e con Automator / Script Editor: Incolla lo script in un'applicazione creata con Automator di macOS, assegnagli un'icona personalizzata e mettila nella cartella Applicazioni o sul Dock. Facendo doppio clic sull'icona, i server si avviano da soli e si apre la finestra.
PWA (Progressive Web App): Se apri http://localhost:5173 su Chrome o Safari, puoi cliccare su "Installa come App" / "Aggiungi al Dock". Si aprirà in una finestra isolata senza barre degli indirizzi, esattamente come l'app di Netflix.

```
#!/bin/bash

# 1. Pulizia preventiva delle porte
kill -9 $(lsof -t -i:8000) 2>/dev/null || true
kill -9 $(lsof -t -i:3000) 2>/dev/null || true
kill -9 $(lsof -t -i:5173) 2>/dev/null || true
pkill -9 -f uvicorn 2>/dev/null || true
pkill -9 -f "npm run dev" 2>/dev/null || true

# 2. Avvio Backend e Frontend in due finestre native del Terminale (senza keystroke)
osascript <<EOF
tell application "Terminal"
    activate
    -- Finestra 1: Backend FastAPI
    do script "cd '/YourPath/InfiniteFlix/backend' && python3 -m uvicorn app.main:app --reload"
    
    -- Finestra 2: Frontend (si apre da sola senza comandi da tastiera)
    do script "cd '/YourPath/InfiniteFlix/frontend' && npm run dev"
end tell
EOF

# 3. Attesa e apertura browser
sleep 2.5
open "http://localhost:3000"
```

**Opzione 2**. _Server su Mini PC / Raspberry Pi (Il vero Home Server)_
Come configurarlo:
1. Collega un Hard Disk esterno al Raspberry Pi per salvare database, thumbnail e file.
2. Docker o Systemd: Imposti FastAPI e il database come servizio di sistema (systemd o Docker Compose). Si avvia da solo ogni volta che il Raspberry si accende.
3. Accesso locale: Il backend sarà raggiungibile da qualsiasi dispositivo connesso al Wi-Fi di casa tramite l'IP locale (es. [http://192.168.1.150:8000](http://192.168.1.150:8000)).

**Opzione 3**. _Come vederlo su TV e Fire TV Stick_
Non serve installare Python sulla Fire TV Stick (sarebbe complesso e inefficiente). La Fire TV deve solo fare da schermo/riproduttore.

|Metodo|Come funziona|
|------|-------------|
|Amazon Silk Browser|	Apri il browser integrato sulla Fire TV Stick e digiti l'indirizzo IP del Mac o del Raspberry (es. [http://192.168.1.100:5173](http://192.168.1.100:5173)). Puoi navigare con il telecomando e guardare i film a schermo intero.
Plex / Jellyfin (Server locale) |	Usi Jellyfin (gratuito e open source) puntato sulla tua cartella film/hard disk e installi l'app ufficiale Jellyfin sulla Fire TV Stick.
App Android / Fire TV dedicata	|Usa Capacitor o Cordova, crea il file .apk e fai il sideload diretto sulla Fire TV Stick.


### Problems found during the developing and how I solved them
_**1. Problema delle Thumbnails:**_ richiedere le copertine dei film a TMDB permette di procedere molto più velocemente perché per scaricare le locandine usiamo normali richieste HTTP (requests) senza scomodare il client di Telegram né rischiare timeout di sessione. Inizialmente ho usato uno script che prelevava il primo frame del film giusto per mettere velocemente una copertina al film, ma questo spesso salvava thumbnail completamente nere. Poi ho pensato a TMDB, questo significa che nel progetto ho uno script aggiuntivo che mi va a sovrascrivere solo le thumbnail dei film che TMDB conosce, lasciando invariate cioè “nere”, quelle che TMDB non conosce.

_**2. Problema dei generi:**_ nel canale telegram usato i generi scritti possono differenziarsi sintatticamente (es. Fantascienza, fantascienza, … errori di battitura) quindi non considero un unione di generi di questo tipo, ma semplicemente considero il genere correlato ad ogni film e trovato su TMDB. Problema 2: se un film non è presente in tmdb comparirebbe Da solo marchiato con il suo genere errato. Allora, per capire a quale genere REALE di TMDB corrisponde un genere scritto sbagliato tipo "avventura" o "aventura" useremo la seguente logica: se un nome di genere è uguale per un tot numeri di caratteri a quello del genere "vero" di TMDB allora stiamo vedendo lo stesso genere. In altre parole, usiamo un algoritmo di somiglianza testuale (Fuzzy / Similarity Matching).

### Highlights & Architecture Breakdown

***Zero-Disk In-Memory Video Streaming***: Il backend non salva mai i file video su disco né usa storage temporaneo. I dati vengono inviati in streaming direttamente dai server Telegram (MTProto) al browser del client in tempo reale tramite generatori asincroni (AsyncIterator[bytes]).

***MTProto 4096-byte Alignment & HTTP 206 Support***: Supporto completo agli header HTTP Range (Partial Content) per il seeking video istantaneo nel browser. Il proxy calcola gli offset e gestisce in automatico l'allineamento a blocchi di 4096 byte imposto dal protocollo binario di Telegram.
Persistent MTProto Client: Connessione persistente Telegram gestita nel ciclo di vita di FastAPI (lifespan/startup), evitando l'overhead di connessione per ogni richiesta HTTP.

***Stateful Incremental Sync***: Sincronizzazione intelligente del canale che traccia l'ultimo telegram_message_id indicizzato su SQLite per elaborare solo i nuovi post senza riscaricare l'intero storico.

***Smart Album & Media Group Pairing***: Riconoscimento automatico dei poster inviati come album Telegram (grouped_id), associando prioritariamente la locandina in alta definizione caricata dall'utente rispetto al fotogramma generato automaticamente.

***Resilient Non-blocking Asset Pipeline***: Il download delle thumbnail gestisce timeout ed errori transitori di Telegram con retry esponenziale senza bloccare la transazione del film nel database.

***Channel Entity Auto-Discovery***: Risoluzione flessibile dei canali che supporta sia username pubblici (@channel) sia ID privati (-100...), caricando dinamicamente la cache dei dialoghi in caso di canali privati.

***Decoupled Modern Stack***: Backend scalabile in FastAPI con validazione Pydantic Settings, database SQLite portabile e frontend reattivo in Next.js (App Router) + Tailwind CSS interamente containerizzati via Docker Compose.

***TMDB Single Source of Truth***: I generi estratti dalle descrizioni Telegram (spesso affetti da variazioni sintattiche, maiuscole/minuscole incoerenti o typo) vengono prioritariamente sovrascritti e normalizzati usando la tassonomia ufficiale di TMDB associata al film.

***Fuzzy Similarity Genre Fallback***: Per i film non presenti su TMDB o privi di corrispondenza diretta, il sistema implementa un algoritmo di similarità testuale (Fuzzy / Levenshtein Distance). Confrontando la stringa della caption con la lista dei generi canonici di TMDB, il backend riconosce e mappa automaticamente errori di battitura e varianti (es. "aventura" → "Avventura", "fantascienza" → "Fantascienza"), evitando la duplicazione o la frammentazione delle categorie nel frontend.
