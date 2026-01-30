from API.api_manager import ApiManager
from models.user_model import UserTest, RegisterUserResponse, PatchUserRequest
from models.auth_model import LoginRequest, LoginResponse, RefreshTokenResponse
from utils.data_generator import DataGenerator


class TestAuthAPI:
    def test_register_user(self, api_manager: ApiManager, test_user):
        response = api_manager.auth_api.register_user(test_user)
        register_user_response = RegisterUserResponse(**response.json())

        assert register_user_response.email == test_user.email, "Email не совпадает"

    def test_register_and_login_user(self, api_manager, registered_user):
        login_req = LoginRequest(
            email=registered_user.email,
            password=registered_user.password
        )

        response = api_manager.auth_api.login_user(login_req)
        login_resp = LoginResponse.model_validate(response.json())

        # Проверки
        assert login_resp.accessToken, "Токен доступа отсутствует в ответе"
        assert login_resp.user.email == registered_user.email, "Email не совпадает"


    def test_refresh_tokens(self, api_manager, registered_user):
        # 1. Логин, чтобы refresh_token появился в cookies
        login_req = LoginRequest(email=registered_user.email, password=registered_user.password)
        api_manager.auth_api.login_user(login_req)

        # 2. Делаем refresh
        resp = api_manager.auth_api.refresh_token()
        refreshed = RefreshTokenResponse.model_validate(resp.json())

        # 3. Проверки
        assert refreshed.accessToken
        assert isinstance(refreshed.accessToken, str)

    def test_logout(self, api_manager,registered_user):
        # 1. Логин - refresh_token появится в cookie
        login_req = LoginRequest(email=registered_user.email, password=registered_user.password)
        api_manager.auth_api.login_user(login_req)

        # 2. Logout
        resp = api_manager.auth_api.logout(expected_status=200)
        assert resp.status_code == 200

        # 3. Контроль
        refresh = api_manager.auth_api.refresh_token(expected_status=401)
        assert refresh.status_code == 401


class TestAuthNegative:

    def test_login_bad_wrong_data_401(self, api_manager):
        bad_payload = {
            "email": "wrong_format",
            "password": "1234567a"
        }

        resp = api_manager.auth_api.login_user(bad_payload, expected_status=401)
        assert resp.status_code == 401

    def test_login_unverified_user_403(self, api_manager, super_admin, test_user):
        # 1. Регаем юзера
        reg_resp = api_manager.auth_api.register_user(test_user, expected_status=201)
        created = RegisterUserResponse.model_validate(reg_resp.json())

        # 2. Админ делает verified=false
        patch_data = PatchUserRequest(verified=False)
        super_admin.api.user_api.patch_user(created.id, patch_data, expected_status=200)

        # 3. Попытка логиниться
        login_req = {"email": test_user.email, "password": test_user.password}
        resp = api_manager.auth_api.login_user(login_req, expected_status=403)
        assert resp.status_code == 403

    def test_refresh_tokens_negative(self, api_manager):
        # Не логинимся
        resp = api_manager.auth_api.refresh_token(expected_status=401)
        assert resp.status_code == 401

    def test_register_user_negative_409(self, api_manager, registered_user):
        # registered_user уже создан фикстуройъ
        registered_req = UserTest(
            email=registered_user.email, # тот же email
            fullName="Another Name",
            password=registered_user.password,
            passwordRepeat=registered_user.password,
            roles=["USER"]
        )

        resp = api_manager.auth_api.register_user(
            registered_req, expected_status=409
        )
        assert resp.status_code == 409

    def test_register_user_wrong_data_400(self, api_manager):
        resp = api_manager.auth_api.register_user({}, expected_status=400)
        assert resp.status_code == 400

