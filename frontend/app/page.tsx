"use client";

import { useEffect, useState } from "react";
import { fetchGenres, fetchMovies, MovieCardData } from "@/lib/api";
import MovieCard from "@/components/MovieCard";
import FilmStrip from "@/components/FilmStrip";

export default function HomePage() {
  const [search, setSearch] = useState("");
  const [genre, setGenre] = useState("");
  const [genres, setGenres] = useState<string[]>([]);
  const [movies, setMovies] = useState<MovieCardData[]>([]);
  const [loading, setLoading] = useState(true);

  // Carica una volta la lista dei generi disponibili, per popolare il filtro
  useEffect(() => {
    fetchGenres().then(setGenres);
  }, []);

  // Ricarica i film ogni volta che cambia la ricerca o il filtro genere,
  // con un piccolo debounce per non fare una richiesta ad ogni tasto premuto
  useEffect(() => {
    setLoading(true);
    const timeout = setTimeout(() => {
      fetchMovies({ search, genre })
        .then((res) => setMovies(res.items))
        .finally(() => setLoading(false));
    }, 300);
    return () => clearTimeout(timeout);
  }, [search, genre]);

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <header>
        <h1 className="font-display text-4xl font-semibold text-paper">
          GioptFlix Films
        </h1>
        <p className="mt-1 font-sans text-sm text-muted">
          {movies.length > 0 ? `${movies.length} film in archivio` : "Il tuo archivio personale"}
        </p>
      </header>

      <div className="mt-6">
        <FilmStrip />
      </div>

      <div className="mt-6 flex flex-col gap-3 sm:flex-row">
        <input
          type="text"
          placeholder="Cerca per titolo..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 rounded-lg border border-reel-border bg-reel-surface px-4 py-2 font-sans text-paper placeholder:text-muted focus:border-marquee focus:outline-none"
        />
        <select
          value={genre}
          onChange={(e) => setGenre(e.target.value)}
          className="rounded-lg border border-reel-border bg-reel-surface px-4 py-2 font-sans text-paper focus:border-marquee focus:outline-none"
        >
          <option value="">Tutti i generi</option>
          {genres.map((g) => (
            <option key={g} value={g}>
              {g}
            </option>
          ))}
        </select>
      </div>

      <div className="mt-8 grid grid-cols-2 gap-5 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
        {loading ? (
          <p className="col-span-full text-center font-mono text-sm text-muted">
            Caricamento...
          </p>
        ) : movies.length === 0 ? (
          <p className="col-span-full text-center font-mono text-sm text-muted">
            Nessun film trovato.
          </p>
        ) : (
          movies.map((movie) => <MovieCard key={movie.id} movie={movie} />)
        )}
      </div>
    </main>
  );
}
