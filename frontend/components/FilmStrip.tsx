/**
 * Elemento distintivo della UI: una sottile striscia con "fori di pellicola",
 * usata una sola volta come separatore sotto l'header. Richiama il bordo
 * perforato delle pellicole 35mm senza essere decorativa fine a se stessa:
 * marca visivamente il confine tra intestazione e catalogo.
 */
export default function FilmStrip() {
  const holes = Array.from({ length: 40 });

  return (
    <div className="flex items-center gap-3 border-y border-reel-border py-2 opacity-70">
      {holes.map((_, i) => (
        <span
          key={i}
          className="h-1.5 w-1.5 flex-shrink-0 rounded-full bg-reel-border"
        />
      ))}
    </div>
  );
}
