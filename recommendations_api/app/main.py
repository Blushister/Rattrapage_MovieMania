from traceback import print_tb
from typing import Any, Dict, List, Optional
from fastapi import Depends, FastAPI, HTTPException, Request, Query
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from dotenv import load_dotenv
from redis_connect import connect_to_redis
import os
from database import engine, get_db
from recommendations import (
    GenreBasedRecommendationFetcher,
    MovieBasedRecommendationFetcher,
    TrendingRecommendationFetcher,
    models,
)
from fastapi.middleware.cors import CORSMiddleware

import jwt
from jwt import PyJWTError
import datetime
from recommendations.schemas import (
    CreditSchema,
    GenreSchema,
    MovieSchema,
    PeopleSchema,
    JobSchema,
)
from starlette.middleware.cors import CORSMiddleware


load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ORIGINS = os.getenv("BACKEND_CORS_ORIGINS")

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
]


# Ajouter le middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)


def save_recommendations_to_redis(client, user_id, recommendations):
    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        key = f"recommendations:{user_id}:{timestamp}"
        client.set(key, str(recommendations))
        print(
            f"Recommandations enregistrées pour l'utilisateur {user_id} avec la clé {key}"
        )
    except Exception as e:
        print(f"Erreur lors de l'enregistrement des recommandations dans Redis : {e}")


class TokenData(BaseModel):
    user_id: int


async def get_current_user(request: Request) -> TokenData:
    """
    Retrieves the current user based on the provided request.

    Args:
        request (Request): The incoming request object.

    Returns:
        TokenData: The user's token data.

    Raises:
        HTTPException: If the user is not authenticated.
    """
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=403, detail="Not authenticated")

    # token = token.split(" ")[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=403, detail="Not authenticated")
        return TokenData(user_id=user_id)
    except PyJWTError:
        raise HTTPException(status_code=403, detail="Not authenticated")


@app.get("/recommendations/", response_model=Dict[str, Any])
async def get_recommendations(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client=Depends(connect_to_redis),
):
    """
    Get movie recommendations for the current user.
    """
    user_id = current_user.user_id
    recommendations = {}

    # Subquery to get movie ids that the current user has seen
    seen_movie_ids = (
        db.query(models.MovieUsers.movie_id)
        .filter(models.MovieUsers.user_id == user_id)
        .subquery()
    )

    # Query to get movie ids that the current user has not seen
    not_seen_movie_ids = (
        db.query(models.Movies.movie_id)
        .filter(~models.Movies.movie_id.in_(seen_movie_ids))
        .all()
    )
    not_seen_movie_ids = [movie_id[0] for movie_id in not_seen_movie_ids]

    genre_fetcher = GenreBasedRecommendationFetcher()
    genre_recommendations = genre_fetcher.fetch(db, user_id, not_seen_movie_ids)
    trending_fetcher = TrendingRecommendationFetcher()
    trending_recommendations = trending_fetcher.fetch(db, not_seen_movie_ids)
    movie_fetcher = MovieBasedRecommendationFetcher()

    loved_movie_ids = (
        db.query(models.MovieUsers.movie_id)
        .filter(models.MovieUsers.user_id == user_id, models.MovieUsers.note >= 4)
        .all()
    )
    loved_movie_ids = [movie_id[0] for movie_id in loved_movie_ids]

    for key, value in genre_recommendations.items():
        recommendations[key] = value
    for key, value in trending_recommendations.items():
        recommendations[key] = value
    for movie_id in loved_movie_ids:
        movie_recommendations = movie_fetcher.fetch(movie_id, db, not_seen_movie_ids)
        for key, value in movie_recommendations.items():
            recommendations[key] = value

    if redis_client:
        save_recommendations_to_redis(redis_client, user_id, recommendations)

    return recommendations


@app.get("/movies/{movie_id}", response_model=MovieSchema)
async def get_movie_details(movie_id: int, db: Session = Depends(get_db)):
    """
    Get movie details by movie ID.
    Parameters:
    - movie_id (int): The ID of the movie.
    - db (Session): The database session.
    Returns:
    - MovieSchema: The movie details.
    Raises:
    - HTTPException: If the movie is not found (status code 404).
    """
    movie = (
        db.query(models.Movies)
        .filter(models.Movies.movie_id == movie_id)
        .options(
            joinedload(models.Movies.genres),
            joinedload(models.Movies.credits).joinedload(models.Credits.people),
            joinedload(models.Movies.credits).joinedload(models.Credits.job),
        )
        .first()
    )

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    genres = [
        GenreSchema(genre_id=movie_genre.genre.genre_id, name=movie_genre.genre.name)
        for movie_genre in movie.genres
    ]

    important_jobs = {
        "Director",
        "Producer",
        "Writer",
        "Editor",
        "Original Music Composer",
        "Executive Producer",
        "Director of Photography",
    }

    credits = []
    actors = []
    for credit in movie.credits:
        if credit.job and credit.people:
            credit_data = CreditSchema(
                credit_id=credit.credit_id,
                id_movie=credit.id_movie,
                id_people=credit.id_people,
                id_job=credit.id_job,
                job=JobSchema(job_id=credit.job.job_id, title=credit.job.title),
                people=PeopleSchema(
                    people_id=credit.people.people_id,
                    name=credit.people.name,
                    photo=credit.people.photo,
                ),
                character_name=credit.character_name,
                cast_order=credit.cast_order,
            )
            if credit.job.title == "Acting":
                actors.append(credit_data)
            elif credit.job.title in important_jobs:
                credits.append(credit_data)

    top_actors = sorted(actors, key=lambda x: (x.cast_order or float("inf")))[:10]

    combined_credits = {
        credit.credit_id: credit for credit in top_actors + credits
    }.values()

    movie_details = MovieSchema(
        movie_id=movie.movie_id,
        title=movie.title,
        release_date=movie.release_date.isoformat() if movie.release_date else None,
        budget=movie.budget,
        revenue=movie.revenue,
        runtime=movie.runtime,
        vote_average=movie.vote_average,
        vote_count=movie.vote_count,
        tagline=movie.tagline,
        overview=movie.overview,
        poster_path=movie.poster_path,
        backdrop_path=movie.backdrop_path,
        genres=genres,
        credits=list(combined_credits),
    )

    return movie_details


@app.get("/genres", response_model=List[GenreSchema])
def read_genres(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    genres = db.query(models.Genres).offset(skip).limit(limit).all()
    return genres


@app.get("/movies/{movie_id}/credits", response_model=List[CreditSchema])
def read_credits(movie_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Credits)
        .options(joinedload(models.Credits.people))
        .filter(models.Credits.id_movie == movie_id)
        .all()
    )


@app.get("/movies/search/", response_model=List[MovieSchema])
async def search_movies(
    title: Optional[str] = Query(None, min_length=1),
    release_date: Optional[str] = Query(None),
    genre: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """
    Search for movies by title, release date, and genre with pagination.

    Args:
        title (str, optional): The title of the movie to search for. Defaults to None.
        release_date (str, optional): The release date of the movie to search for. Defaults to None.
        genre (str, optional): The genre of the movie to search for. Defaults to None.
        skip (int, optional): The number of records to skip for pagination. Defaults to 0.
        limit (int, optional): The maximum number of records to return. Defaults to 10.
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        List[MovieSchema]: A list of MovieSchema instances containing the details of each matching movie.

    Raises:
        HTTPException: If no movies are found with the given criteria.
    """
    query = db.query(models.Movies)

    if title:
        query = query.filter(models.Movies.title.ilike(f"%{title}%"))

    if release_date:
        # Convert release_date to date if needed
        from datetime import datetime

        try:
            release_date_obj = datetime.strptime(release_date, "%Y-%m-%d").date()
            query = query.filter(models.Movies.release_date == release_date_obj)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid date format. Use YYYY-MM-DD."
            )

    if genre:
        query = (
            query.join(models.MovieGenres)
            .join(models.Genres)
            .filter(models.Genres.name.ilike(f"%{genre}%"))
        )

    movies = query.offset(skip).limit(limit).all()

    if not movies:
        raise HTTPException(
            status_code=404, detail="No movies found with the given criteria"
        )

    return [
        MovieSchema(
            movie_id=movie.movie_id,
            title=movie.title,
            release_date=movie.release_date,
            budget=movie.budget,
            revenue=movie.revenue,
            runtime=movie.runtime,
            vote_average=movie.vote_average,
            vote_count=movie.vote_count,
            tagline=movie.tagline,
            overview=movie.overview,
            poster_path=movie.poster_path,
            backdrop_path=movie.backdrop_path,
        )
        for movie in movies
    ]
