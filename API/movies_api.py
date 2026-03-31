import requests

from constants import MOVIES_ENDPOINT, MOVIES_ID_ENDPOINT, API_BASE_URL
from custom_requester.custom_requester import CustomRequester
from models.movies_model import GetListMoviesParams, MovieCreateRequest


class MoviesAPI(CustomRequester):
    MOVIE_API_BASE_URL = "https://api.dev-cinescope.coconutqa.ru/"
    """
    Клиент для работы с сервисом Movies.
    Предоставляет методы для управления сущностями фильмов через REST API.
    """
    def __init__(self, session: requests.Session):
        """
        Инициализирует экземпляр MoviesAPI.

        :param session: активная HTTP-сессия requests.Session, содержащая базовый URL и настройки авторизации.
        """
        super().__init__(session=session, base_url=self.MOVIE_API_BASE_URL) #тут base_url ставим url для Movies


    def get_list_movies(self, params: GetListMoviesParams | dict | None = None, expected_status: int = 200):
        """
        Получает список фильмов.
        """
        # 1. Проверяем, если пришла модель Pydantic, превращаем ее в словарь
        if isinstance(params, GetListMoviesParams):
            params = params.model_dump(exclude_unset=True, by_alias=True)

        # Если пришел dict - мы его не трогаем и просто прокидываем данные.
        # Если пришел None - requests поймет, что параметров нет

        return self.send_request("GET", endpoint=MOVIES_ENDPOINT, params=params, expected_status=expected_status)

    def create_movie(self, movie_data: MovieCreateRequest | dict, expected_status: int = 201):
        """
        Создает новый фильм.
        """
        return self.send_request("POST", endpoint=MOVIES_ENDPOINT, data=movie_data, expected_status=expected_status)

    def get_movie_by_id(self, movie_id: int, expected_status: int = 200):
        """
        Возвращает данные фильма по его идентификатору.

        :param movie_id: уникальный идентификатор фильма.
        :param expected_status: ожидаемый HTTP-код ответа.
        :return: объект requests.Response с данными фильма.
        """
        return self.send_request("GET", endpoint=MOVIES_ID_ENDPOINT.format(id=movie_id), expected_status=expected_status)

    def delete_movie_by_id(self, movie_id: int, expected_status=(200, 204)):
        """
        Удаляет фильм по его идентификатору.

        :param movie_id: уникальный идентификатор фильма.
        :param expected_status: ожидаемый HTTP-код ответа, по умолчанию 204.
        :return: объект requests.Response.
        """
        return self.send_request(
            "DELETE",
            endpoint=MOVIES_ID_ENDPOINT.format(id=movie_id),
            expected_status=expected_status
        )

    def patch_movie_by_id(self, movie_id: int, patch_data: dict, expected_status: int = 200):
        """
        Частично обновляет данные фильма.

        :param movie_id: уникальный идентификатор фильма.
        :param patch_data: словарь с изменяемыми полями фильма.
        :param expected_status: ожидаемый HTTP-код ответа.
        :return: объект requests.Response с данными обновленного фильма.
        """
        return self.send_request("PATCH", endpoint=MOVIES_ID_ENDPOINT.format(id=movie_id), data=patch_data, expected_status=expected_status)