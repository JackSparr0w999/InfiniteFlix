"""
API per consultare il catalogo: lista paginata con ricerca/filtro, dettaglio
di un film, e lista dei generi disponibili per popolare il filtro nel frontend.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import distinct, desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Movie
from app.schemas import MovieList, MovieDetail

router = APIRouter(prefix="/api", tags=["movies"])


@router.get("/movies", response_model=MovieList)
def list_movies(
    search: str | None = Query(None, description="Ricerca nel titolo"),
    genre: str | None = Query(None, description="Filtra per genere esatto"),
    min_year: int | None = Query(None, description="Anno minimo (es. 2019)"),
    max_year: int | None = Query(None, description="Anno massimo (es. 2023)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Movie)

    if search:
        query = query.filter(Movie.title.ilike(f"%{search}%"))
    if genre:
        query = query.filter(Movie.genre == genre)
    if min_year:
        query = query.filter(Movie.year >= min_year)
    if max_year:
        query = query.filter(Movie.year <= max_year)

    total = query.count()
    items = (
        query.order_by(
            desc(Movie.has_tmdb_poster),  # 1. Prima tutti i film con poster TMDB (500x750)
            Movie.year.desc(),            # 2. Poi per anno (più recenti prima)
            Movie.created_at.desc()       # 3. Poi per data di aggiunta
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return MovieList(items=items, total=total, page=page, page_size=page_size)


@router.get("/movies/{movie_id}", response_model=MovieDetail)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if movie is None:
        raise HTTPException(status_code=404, detail="Film non trovato")
    return movie


@router.get("/genres", response_model=list[str])
def list_genres(db: Session = Depends(get_db)):
    rows = db.query(distinct(Movie.genre)).filter(Movie.genre.isnot(None)).all()
    return sorted(r[0] for r in rows if r[0])