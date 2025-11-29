from requests import Session

from custom_requester.custom_requester import CustomRequester

class UserAPI(CustomRequester):
    """
    Класс для работы с API пользователей.
    """

    def __init__(self, session: Session):
        """
        Инициализирует клиент UserAPI.

        :param session: HTTP-сессия requests.Session с базовым URL и настройками.
        """
        super().__init__(session=session, base_url=session.base_url)


    def get_user_info(self, user_id: int, expected_status: int=200):
        """
        Получает информацию о пользователе по его идентификатору.

        :param user_id: ID пользователя.
        :param expected_status: Ожидаемый HTTP-код ответа.
        :return: объект requests.Response.
        """
        return self.send_request(
            method="GET",
            endpoint=f"/user/{user_id}",
            expected_status=expected_status
        )

    def delete_user(self, user_id: int, expected_status: int=204):
        """
        Удаляет пользователя по его идентификатору.

        :param user_id: ID пользователя.
        :param expected_status: Ожидаемый HTTP-код ответа.
        :return: объект requests.Response.
        """
        return self.send_request(
            method="DELETE",
            endpoint=f"/user/{user_id}",
            expected_status=expected_status
        )
