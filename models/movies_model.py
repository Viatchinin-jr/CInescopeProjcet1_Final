from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, List, Optional
from datetime import datetime


class GenreInfo(BaseModel):
    """Вложенная модель для информации о жанре"""


class MovieCreateRequest(BaseModel):
    """
    Модель для отправки данных (POST).
    Описывает структуру фильма, которую мы создаем или полностью заменяем.
    """
    model_config = ConfigDict(populate_by_name=True)

    name: str
    price: int
    description: str
    image_url: Optional[str] = Field(None, alias="imageUrl") # Теперь разрешаем None
    location: Literal["MSK", "SPB"]
    published: bool
    rating: float
    genre_id: int = Field(alias="genreId")


class MovieResponse(MovieCreateRequest):
    """
    Полная модель фильма из ответа.
    """
    id: int
    genre: GenreInfo # вложенный объект жанра
    created_at: datetime = Field(alias="createdAt")
    rating: float

# Модель для списка фильмов
class GetListMoviesResponse(BaseModel):
    """
    Модель ответ списка фильмов с пагинацией (GET).
    """
    movies: List[MovieResponse]
    count: int
    page: int
    pageSize: int
    pageCount: int = Field(alias="pageCount")


# Модель для параметров фильтрации
class GetListMoviesParams(BaseModel):
    """
    Модель для Query-параметров запроса GET.
    Обеспечивает типизацию и валидацию фильтров перед отправкой.
    """
    model_config = ConfigDict(populate_by_name=True)

    page: Optional[int] = Field(default=1, description="Номер страницы")
    page_size: Optional[int] = Field(default=10, alias="pageSize", description="Размер страницы")

    min_price: Optional[int] = Field(default=1, alias="minPrice")
    max_price: Optional[int] = Field(default=1000, alias="maxPrice")

    locations: Optional[List[Literal["MSK", "SPB"]]] = Field(default=["MSK", "SPB"])

    published: Optional[bool] = Field(default=True)
    genre_id: Optional[int] = Field(default=None, alias="genreId")

    created_at: Optional[Literal["asc", "desc"]] = Field(default="asc", alias="createdAt")

class ErrorResponse(BaseModel):
    message: str | List[str]
    error: str | None = None
    statusCode: int

# Информация о пользователе внутри отзыва
class ReviewUserInfo(BaseModel):
    full_name: str = Field(alias="fullName")

# Модель одного отзыва
class MovieReview(BaseModel):
    user_id: str = Field(alias="userId")
    rating: int
    text: str
    hidden: bool
    created_at: datetime = Field(alias="createdAt")
    user: ReviewUserInfo

# Модель фильма (Для GET по ID).
class MovieDetailResponse(MovieResponse):
    # Наследуем все от MovieResponse и добавляем список отзывов
    # Для себя: указываю что reviews - это список, внутри которого объекты должны соответствовать модели MovieReview. '= []' - это страховка чтобы тест не упал, если придет фильм без отзыва.
    reviews: List[MovieReview] = []

# Модель запроса для PATCH
class MovieUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[str] = None
    location: Optional[str] = None
    image_url: Optional[str] = Field(None, alias="imageUrl")
    published: Optional[bool] = None
    genre_id: Optional[int] = Field(None, alias="genreId")