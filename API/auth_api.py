from constants import REGISTER_ENDPOINT, BASE_URL, LOGIN_ENDPOINT
from custom_requester.custom_requester import CustomRequester

class AuthAPI(CustomRequester):
    """
      Класс для работы с аутентификацией.
      """

    def __init__(self, session):
        super().__init__(session=session, base_url=session.base_url)

    def register_user(self, user_data, expected_status=201):
        """
        Регистрация нового пользователя.
        :param user_data: Данные пользователя.
        :param expected_status: Ожидаемый статус-код.
        """
        return self.send_request(
            method="POST",
            endpoint=REGISTER_ENDPOINT,
            data=user_data,
            expected_status=expected_status
        )

    def login_user(self, login_data, expected_status=200):
        """
        Авторизация пользователя.
        :param login_data: Данные для логина.
        :param expected_status: Ожидаемый статус-код.
        """
        return self.send_request(
            method="POST",
            endpoint=LOGIN_ENDPOINT,
            data=login_data,
            expected_status=expected_status
        )

    def authenticate(self, user_creds):
        login_data = {
            "email": user_creds[0],
            "password": user_creds[1]
        }

        # тут костыль потому что бек мне отвечал то 200, то 201
        try:
            # типа правильно - 200
            data = self.login_user(login_data, expected_status=200).json()
        except ValueError:
            # бэк может вернуть 201, тогда
            data = self.login_user(login_data, expected_status=200).json()

        if "accessToken" not in data:
            raise KeyError("token is missing")

        token = data["accessToken"]
        self._update_session_headers(Authorization=f"Bearer {token}")
        return token

