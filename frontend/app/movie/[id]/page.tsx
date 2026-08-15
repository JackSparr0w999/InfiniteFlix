"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { fetchMovie, MovieDetailData, streamUrl, thumbnailUrl } from "@/lib/api";

export default function MoviePage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [movie, setMovie] = useState<MovieDetailData | null>(null);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    fetchMovie(params.id).then(setMovie).catch(() => setMovie(null));
  }, [params.id]);

  if (!movie) {
    return (
      <main className="mx-auto max-w-4xl px-6 py-10">
        <p className="font-mono text-sm text-muted">Caricamento...</p>
      </main>
    );
  }

  const thumb = thumbnailUrl(movie.thumbnail_path);

  return (
    <main className="mx-auto max-w-4xl px-6 py-10">
      <button
        onClick={() => router.push("/")}
        className="mb-6 font-mono text-sm text-muted hover:text-marquee"
      >
        ← Torna al catalogo
      </button>

      {playing ? (
        // Player HTML5 nativo
        <video
          src={streamUrl(movie.id)}
          controls
          autoPlay
          className="w-full rounded-lg border border-reel-border bg-black"
        />
      ) : (
        <div className="grid gap-6 sm:grid-cols-[240px_1fr]">
          <div className="aspect-[2/3] overflow-hidden rounded-lg border border-reel-border bg-reel-surface">
            {thumb ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={thumb} alt={movie.title} className="h-full w-full object-cover" />
            ) : null}
          </div>

          <div>
            <h1 className="font-display text-3xl font-medium text-paper">{movie.title}</h1>
            
            {/* Info base / Tag */}
            <div className="mt-2 flex flex-wrap gap-3 font-mono text-sm text-muted">
              {movie.year && <span>{movie.year}</span>}
              {movie.duration && <span>{movie.duration}</span>}
              {movie.genre && <span>{movie.genre}</span>}
              {movie.quality && (
                <span className="rounded bg-velvet/90 px-2 py-0.5 text-paper">{movie.quality}</span>
              )}
            </div>

            {/* Bottone Riproduci */}
            <button
              onClick={() => setPlaying(true)}
              className="mt-6 rounded-lg bg-marquee px-6 py-2 font-sans font-medium text-reel-bg transition-opacity hover:opacity-90"
            >
              ▶ Riproduci
            </button>

            {/* --- LINEA SEPARATRICE --- */}
            <hr className="mt-8 border-reel-border" />

            {/* --- SEZIONE TRAMA STILE NETFLIX --- */}
            <div className="mt-6 space-y-2">
              <h2 className="font-sans text-xs font-semibold uppercase tracking-wider text-muted">
                Trama
              </h2>
              <p className="font-sans text-sm leading-relaxed text-paper/90">
                {movie.description || "Trama non disponibile per questo film."}
              </p>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
