from requests import Session

from constants import REGISTER_ENDPOINT, LOGIN_ENDPOINT, LOGOUT_ENDPOINT, REFRESH_ENDPOINT
from custom_requester.custom_requester import CustomRequester
import requests
from typing import Iterable

from models.auth_model import LoginRequest, LoginResponse
from models.user_model import UserTest

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

    def register_user(self, user_data: UserTest, expected_status: int = 201) -> requests.Response:
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

    def login_user(self, login_data: LoginRequest, expected_status: int | Iterable[int] = (200,201)) -> requests.Response:
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
        login_req = LoginRequest(email=user_creds[0], password=user_creds[1])

        resp = self.login_user(login_req, expected_status=[200, 201])
        login_resp = LoginResponse.model_validate(resp.json())

        token = login_resp.accessToken
        self._update_session_headers(Authorization=f"Bearer {token}")
        return token

    def refresh_token(self, expected_status: int | Iterable[int] = (200, 201)) -> requests.Response:
        """
        Обновление refreshToken и accessToken пользователя
        """
        return self.send_request(
            method="GET",
            endpoint=REFRESH_ENDPOINT,
            expected_status=expected_status
        )

    def logout(self, expected_status: int | Iterable[int] = 200) -> requests.Response:
        """
        Выход из учетной записи и удаление refresh_token пользователя.
        """
        return self.send_request(
            method="GET",
            endpoint=LOGOUT_ENDPOINT,
            expected_status=expected_status
        )