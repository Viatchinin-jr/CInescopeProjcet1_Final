from requests import Session

from constants import REGISTER_ENDPOINT, LOGIN_ENDPOINT
from custom_requester.custom_requester import CustomRequester
import requests
from typing import Iterable

class AuthAPI(CustomRequester):
    """
    Класс для работы с аутентификацией.
    """

    def __init__(self, session: Session) -> None:
        """
        Инициализирует клиент AuthAPI.

        :param session: объект requests.Session, содержащий базовые настройки и URL.
        """
        super().__init__(session=session, base_url=session.base_url)

    def register_user(self, user_data: dict, expected_status: int = 201) -> requests.Response:
        """
        Регистрирует нового пользователя.

        :param user_data: данные пользователя в формате словаря.
        :param expected_status: ожидаемый HTTP-код ответа, по умолчанию 201.
        :return: объект requests.Response.
        """
        return self.send_request(
            method="POST",
            endpoint=REGISTER_ENDPOINT,
            data=user_data,
            expected_status=expected_status,
        )

    def login_user(self, login_data: dict, expected_status: int | Iterable[int] = (200,201)) -> requests.Response:
        """
        Авторизует пользователя.

        :param login_data: данные для авторизации (логин/пароль).
        :param expected_status: ожидаемый HTTP-код ответа.
        :return: объект requests.Response.
        """
        return self.send_request(
            method="POST",
            endpoint=LOGIN_ENDPOINT,
            data=login_data,
            expected_status=expected_status,
        )

    def authenticate(self, user_creds: tuple[str, str]) -> str:
        """
        Выполняет авторизацию и устанавливает токен в заголовки сессии.

        :param user_creds: кортеж (email, password).
        :return: строка - access token.
        :raises KeyError: если в ответе отсутствует accessToken.
        """
        login_data = {
            "email": user_creds[0],
            "password": user_creds[1]
        }

        data = self.login_user(login_data, expected_status=[200, 201]).json()

        if "accessToken" not in data:
            raise KeyError("token is missing")

        token = data["accessToken"]
        self._update_session_headers(Authorization=f"Bearer {token}")
        return token

