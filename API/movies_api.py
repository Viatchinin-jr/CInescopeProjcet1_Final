import requests

from constants import MOVIES_ENDPOINT, MOVIES_ID_ENDPOINT
from custom_requester.custom_requester import CustomRequester


class MoviesAPI(CustomRequester):
    """
    Клиент для работы с сервисом Movies.
    Предоставляет методы для управления сущностями фильмов через REST API.
    """
    def __init__(self, session: requests.Session):
        """
        Инициализирует экземпляр MoviesAPI.

        :param session: активная HTTP-сессия requests.Session, содержащая базовый URL и настройки авторизации.
        """
        super().__init__(session=session, base_url=session.api_base_url) #тут берем за base_url - url апишки movies


    def get_list_movies(self, params: dict | None = None, expected_status: int = 200):
        """
        Получает список фильмов.

        :param params: дополнительные параметры фильтрации запроса.
        :param expected_status: ожидаемый HTTP-код ответа.
        :return: объект requests.Response с данными ответа API.
        """
        return self.send_request("GET", endpoint=MOVIES_ENDPOINT, params=params, expected_status=expected_status)

    def create_movie(self, movie_data: dict,  expected_status: int = 201):
        """
        Создает новый фильм.

        :param movie_data: данные нового фильма в формате словаря.
        :param expected_status: ожидаемый HTTP-код ответа, по умолчанию 201.
        :return: объект requests.Response с данными ответа API.
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

    def delete_movie(self, movie_id: int, expected_status: int = 204):
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

    def patch_movie(self, movie_id: int, patch_data: dict, expected_status: int = 200):
        """
        Частично обновляет данные фильма.

        :param movie_id: уникальный идентификатор фильма.
        :param patch_data: словарь с изменяемыми полями фильма.
        :param expected_status: ожидаемый HTTP-код ответа.
        :return: объект requests.Response с данными обновленного фильма.
        """
        return self.send_request("PATCH", endpoint=MOVIES_ID_ENDPOINT.format(id=movie_id), data=patch_data, expected_status=expected_status)