/**
 * Wrapper minimale per le chiamate al backend FastAPI.
 * Nessuna autenticazione: le richieste sono dirette, senza token/cookie.
 */
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface MovieCardData {
  id: number;
  title: string;
  year: number | null;
  quality: string | null;
  genre: string | null;
  thumbnail_path: string | null;
}

export interface MovieDetailData extends MovieCardData {
  duration: string | null;
  description: string | null;
  file_size: number;
}

export interface MovieListResponse {
  items: MovieCardData[];
  total: number;
  page: number;
  page_size: number;
}

export async function fetchMovies(params: {
  search?: string;
  genre?: string;
  page?: number;
}): Promise<MovieListResponse> {
  const query = new URLSearchParams();
  if (params.search) query.set("search", params.search);
  if (params.genre) query.set("genre", params.genre);
  if (params.page) query.set("page", String(params.page));

  const res = await fetch(`${API_URL}/api/movies?${query.toString()}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Impossibile caricare il catalogo");
  return res.json();
}

export async function fetchMovie(id: string): Promise<MovieDetailData> {
  const res = await fetch(`${API_URL}/api/movies/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Film non trovato");
  return res.json();
}

export async function fetchGenres(): Promise<string[]> {
  const res = await fetch(`${API_URL}/api/genres`, { cache: "no-store" });
  if (!res.ok) return [];
  return res.json();
}

export function thumbnailUrl(path: string | null): string | null {
  if (!path) return null;
  return `${API_URL}/thumbnails/${path}`;
}

export function streamUrl(id: number): string {
  return `${API_URL}/stream/${id}`;
}
