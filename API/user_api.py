from requests import Session
from custom_requester.custom_requester import CustomRequester
from models.user_model import CreateUserRequest, PatchUserRequest, GetAllUsersRequest


class UserAPI(CustomRequester):
    AUTH_USER_BASE_URL = "https://auth.dev-cinescope.coconutqa.ru"

    """
    Класс для работы с API пользователей.
    """

    def __init__(self, session: Session):
        """
        Инициализирует клиент UserAPI.
        """
        self.session = session
        super().__init__(session=session, base_url=self.AUTH_USER_BASE_URL)

    def get_user(self, user_locator, expected_status=200):
        return self.send_request("GET", f"/user/{user_locator}", expected_status=expected_status)

    def delete_user(self, user_id: int, expected_status: int=200):
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

    def create_user(self, user_data: CreateUserRequest, expected_status=201):
        return self.send_request(
            method="POST",
            endpoint="/user",
            data=user_data,
            expected_status=expected_status
        )

    def patch_user(self, user_id: str, patch_data: PatchUserRequest, expected_status: int = 200):
        return self.send_request(
            method="PATCH",
            endpoint=f"/user/{user_id}",
            data=patch_data,
            expected_status=expected_status
        )

    def get_all_users(self, request: GetAllUsersRequest, expected_status=200):
        return self.send_request(
            method="GET",
            endpoint="/user",
            params=request.model_dump(exclude_unset=True),
            expected_status=expected_status
        )



