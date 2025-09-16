from datetime import date
from typing import Optional, List
from pydantic import BaseModel


class PeopleSchema(BaseModel):
    people_id: int
    name: str
    photo: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True


class JobSchema(BaseModel):
    job_id: int
    title: str

    class Config:
        orm_mode = True
        from_attributes = True


class GenreSchema(BaseModel):
    genre_id: int
    name: str

    class Config:
        orm_mode = True
        from_attributes = True


class CreditSchema(BaseModel):
    credit_id: int
    id_movie: int
    id_people: int
    id_job: int
    character_name: Optional[str]
    cast_order: Optional[int]
    job: Optional["JobSchema"] = None
    people: Optional["PeopleSchema"] = None

    class Config:
        orm_mode = True
        from_attributes = True


class MovieSchema(BaseModel):
    movie_id: int
    title: str
    release_date: Optional[date] = None
    budget: Optional[float] = None
    revenue: Optional[float] = None
    runtime: Optional[int] = None
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    tagline: Optional[str] = None
    overview: Optional[str] = None
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    genres: Optional[List[GenreSchema]] = None
    credits: Optional[List[CreditSchema]] = None

    class Config:
        orm_mode = True
        from_attributes = True


class RecommendationSchema(BaseModel):
    movie_id: int
    title: str
    release_date: Optional[date] = None
    vote_average: Optional[float] = None
    backdrop_path: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True
