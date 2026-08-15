import Link from "next/link";
import { MovieCardData, thumbnailUrl } from "@/lib/api";

export default function MovieCard({ movie }: { movie: MovieCardData }) {
  const thumb = thumbnailUrl(movie.thumbnail_path);

  return (
    <Link
      href={`/movie/${movie.id}`}
      className="group block overflow-hidden rounded-lg border border-reel-border bg-reel-surface transition-colors hover:bg-reel-surfaceHover"
    >
      <div className="relative aspect-[2/3] w-full overflow-hidden bg-reel-bg">
        {thumb ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={thumb}
            alt={movie.title}
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-muted">
            <span className="font-display text-sm">Nessuna copertina</span>
          </div>
        )}
        {movie.quality && (
          <span className="absolute right-2 top-2 rounded bg-velvet/90 px-2 py-0.5 font-mono text-xs text-paper">
            {movie.quality}
          </span>
        )}
      </div>

      <div className="p-3">
        <h3 className="truncate font-display text-base font-medium text-paper">
          {movie.title}
        </h3>
        <div className="mt-1 flex items-center gap-2 font-mono text-xs text-muted">
          {movie.year && <span>{movie.year}</span>}
          {movie.genre && (
            <>
              <span aria-hidden>·</span>
              <span className="truncate">{movie.genre}</span>
            </>
          )}
        </div>
      </div>
    </Link>
  );
}
