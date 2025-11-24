from constants import MOVIES_ENDPOINT, MOVIES_ID_ENDPOINT
from custom_requester.custom_requester import CustomRequester
from API.auth_api import AuthAPI
from utils.data_generator import DataGenerator

class MoviesAPI(CustomRequester):
    """
    Класс для работы с MOVIES api
    """
    def __init__(self, session):
        super().__init__(session=session, base_url=session.api_base_url) #тут берем за base_url - url апишки movies

    def get_list_movies(self, params: dict | None = None, expected_status: int = 200):
        """
        Это на получение гетом списка всех фильмов
        :param params: словарь фильтров, пока не нужен вроде хз
        :param expected_status: 200
        :return: объект request.Response
        """
        return self.send_request("GET", endpoint=MOVIES_ENDPOINT, params=params, expected_status=expected_status)

    def create_movie(self, movie_data: dict,  expected_status: int = 201):
        """
        Создание фильма
        :param params:
        :param expected_status:
        :return:
        """
        return self.send_request("POST", endpoint=MOVIES_ENDPOINT, data=movie_data, expected_status=expected_status)

    def get_movie_by_id(self, movie_id, expected_status: int = 200):
        """
        На получение информации о фильме по ID

        """
        return self.send_request("GET", endpoint=MOVIES_ID_ENDPOINT.format(id=movie_id), expected_status=expected_status)

    def delete_movie(self, movie_id, expected_status=204):
        """
        Удаляет фильм по ID
        :param movie_id: ID фильма
        :param expected_status: ожидаемый статус (по умолчанию 204)
        """
        return self.send_request(
            "DELETE",
            endpoint=MOVIES_ID_ENDPOINT.format(id=movie_id),
            expected_status=expected_status
        )

    def patch_movie(self, movie_id: dict, patch_data: dict, expected_status=200):
        return self.send_request("PATCH", endpoint=MOVIES_ID_ENDPOINT.format(id=movie_id), data=patch_data, expected_status=expected_status)