from API.api_manager import ApiManager
from models.user_model import UserTest, RegisterUserResponse, PatchUserRequest, PatchUserResponse
from models.auth_model import LoginRequest, LoginResponse, RefreshTokenResponse, RegisterUserRequest, ErrorRegisterResponse
import pytest
import datetime
import allure
from db_requester.db_client import get_confirmation_token_by_email


@allure.epic("Сервис Auth")
@allure.feature("Авторизация и Аутентификация (Позитив)")
@pytest.mark.api
@pytest.mark.auth
@pytest.mark.positive
class TestAuthAPI:

    @allure.story("Регистрация нового пользователя")
    @pytest.mark.smoke
    @allure.title("Тест регистрации пользователя")
    def test_register_user(self, api_manager: ApiManager, test_user: UserTest, check):
        with allure.step("Подготовка данных запроса"):
            register_req = RegisterUserRequest.model_validate(test_user.model_dump())

        with allure.step("Отправляем post-запрос на регистрацию через метод register_user"):
            response = api_manager.auth_api.register_user(register_req)

        with allure.step("Проверка статус-кода ответа"):
            assert response.status_code == 201, f"Неверный статус-код. Ожидали 201, а получили {response.status_code}"

        with allure.step("Валидация структуры ответа через Pydantic"):
            registered_user = RegisterUserResponse.model_validate(response.json())

        with allure.step("Проверка соответствия данных в ответе"):
            with check:
                check.equal(registered_user.email, test_user.email, f"Ожидали {test_user.email}, получили {registered_user.email}")
                check.equal(registered_user.fullName, test_user.fullName, f"Ожидали {test_user.fullName}, а получили {registered_user.fullName}")

    @allure.story("Регистрация (Mock-тест)")
    @allure.severity(allure.severity_level.MINOR)
    @allure.title("Тест регистрации пользователя с помощью Mock")
    def test_register_user_mock(self, api_manager: ApiManager, test_user: UserTest, mocker, check):
        with allure.step("Мокаем метод register_user в auth_api"):
            mock_response = RegisterUserResponse(
                    id="id",
                    email="email@email.com",
                    fullName="fullName",
                    verified=True,
                    banned=False,
                    roles=["SUPER_ADMIN"],
                    createdAt=str(datetime.datetime.now())
                )

            mocker.patch.object(
                api_manager.auth_api,
                "register_user",
                return_value=mock_response
            )
        with allure.step("Вызываем метод, который должен быть замокан"):
            register_user_response = api_manager.auth_api.register_user(test_user)

        with allure.step("Проверяем, что ответ соответствует ожидаемому"):
            with allure.step("Проверка поля персональных данных"):
                with check:
                    check.equal(register_user_response.fullName, mock_response.fullName)
                    check.equal(register_user_response.email, mock_response.email)

            with allure.step("Проверка поля banned"):
                with check("Проверка поля banned"):
                    check.equal(register_user_response.banned, mock_response.banned)

    @allure.story("Вход в систему (Login)")
    @pytest.mark.smoke
    @allure.title("Тест аутентификации пользователя")
    def test_login(self, api_manager, registered_user, check):
        with allure.step("Подготовка данных запроса"):
            login_data = LoginRequest.model_validate(registered_user.model_dump())

        with allure.step("Отправка запроса на аутентификацию (логин)"):
            resp = api_manager.auth_api.login_user(login_data)

        with allure.step("Проверка статус-кода ответа"):
            assert resp.status_code == 201, f"Ожидался ответ 201, а получен {resp.status_code}"

        with allure.step("Валидация ответа через модель"):
            login_resp = LoginResponse.model_validate(resp.json())

        with allure.step("Проверка успешной аутентификации"):
            with check:
                check.equal(login_resp.user.email, registered_user.email, f"Ожидался ответ {registered_user.email}, а получен {login_resp.user.email}")


    @allure.story("Обновление токенов (Refresh)")
    @allure.title("Тест обновления токена")
    def test_refresh_tokens(self, api_manager, registered_user):
        with allure.step("Подготовка данных"):
            login_data = LoginRequest.model_validate(registered_user.model_dump())
            resp = api_manager.auth_api.login_user(login_data)

        with allure.step("Делаем refresh_token"):
            resp = api_manager.auth_api.refresh_token()
            refreshed = RefreshTokenResponse.model_validate(resp.json())

        with allure.step("Проверки"):
            assert refreshed.accessToken
            assert isinstance(refreshed.accessToken, str)

    @allure.story("Выход из системы (Logout)")
    @pytest.mark.smoke
    @allure.title("Тест выхода из учетной записи")
    def test_logout(self, api_manager, registered_user, check):
        with allure.step("Подготовка данных и логин"):
            login_data = LoginRequest.model_validate(registered_user.model_dump())
            resp = api_manager.auth_api.login_user(login_data)

        with allure.step("Выполнение Logout"):
            resp_logout = api_manager.auth_api.logout()

        with allure.step("Проверка успешности Logout"):
            with check:
                check.equal(resp_logout.status_code, 200, f"Ожидался статус-код 200, а получен {resp_logout.status_code}")
                check.equal(resp_logout.text, "OK", f"Ожидался message - 'OK', а получен {resp_logout.text}")

        with allure.step("Контрольная проверка: попытка обновить токен после выхода."):
            refresh_resp = api_manager.auth_api.refresh_token(expected_status=401)
            assert refresh_resp.status_code == 401, f"Ожидался ответ 401, а получен {refresh_resp.status_code}"

    @allure.story("Подтверждение почты (Confirm Email)")
    @allure.title("Успешное подтверждение через email (Mock)")
    def test_confirm_email_positive(self, api_manager, test_user, check, mocker):
        fake_token = "12345-fake-token-67890"

        with allure.step("Мокаем получение токена из БД"):
            mocker.patch(
                f"{__name__}.get_confirmation_token_by_email",
                return_value = fake_token
            )

        with allure.step("Мокаем ответ API подтверждения"):
            mock_response = mocker.Mock()
            mock_response.status_code = 200
            mock_response.text = "Пользователь подтверждён"

            mocker.patch.object(
                api_manager.auth_api,
                "confirm_email",
                return_value=mock_response
            )

        with allure.step("Выполнение шагов теста с моками"):
            api_manager.auth_api.register_user(test_user)

            token = get_confirmation_token_by_email(test_user.email)

            resp = api_manager.auth_api.confirm_email(token)

        with allure.step("Проверка результата"):
            with check:
                check.equal(token, fake_token, "Токен не совпадает с фейковым")
                check.equal(resp.text, "Пользователь подтверждён")


@allure.epic("Сервис Auth")
@allure.feature("Обработка ошибок (Negative)")
@pytest.mark.api
@pytest.mark.auth
@pytest.mark.negative
class TestAuthNegative:

    @allure.story("Конфликт при регистрации (Duplicate Email)")
    @allure.title("Регистрация пользователя с уже существующим email")
    def test_register_user_negative_409(self, api_manager, registered_user, check):
        with allure.step("Подготовка данных: дубликат email"):
            dublicated_req = RegisterUserRequest(
                email=registered_user.email,
                fullName="Another Name",
                password=registered_user.password,
                passwordRepeat=registered_user.password,
            )

        with allure.step("Отправка запроса на регистрацию (ожидаем 409)"):
            resp = api_manager.auth_api.register_user(dublicated_req, expected_status=409)

        with allure.step("Валидация тела ошибки"):
            error_data = ErrorRegisterResponse.model_validate(resp.json())
            with check:
                check.equal(error_data.statusCode, 409)

    @allure.story("Валидация формата email")
    @allure.title("Регистрация с некорректным форматом email")
    def test_register_user_wrong_data_400(self, api_manager, check):
        with allure.step("Подготовка данных: некорректный email"):
            invalid_data = {
                "email": "it-is-not-a-valid-email",
                "fullName": "Nikita Test",
                "password": "qwerty123",
                "passwordRepeat": "qwerty123"
            }

        with allure.step("Отправка запроса на регистрацию: ожидаем 400"):
            resp = api_manager.auth_api.register_user(invalid_data, expected_status=400)

        with allure.step("Проверка статус-кода: ожидаем 400"):
            assert resp.status_code == 400, f"Ожидали 400, но сервер вернул {resp.status_code}"

        with allure.step("Валидация сообщения об ошибке"):
            error_data = ErrorRegisterResponse.model_validate(resp.json())
            with check:
                check.is_in("Некорректный email", error_data.message)

    @allure.story("Вход с неверными учетными данными")
    @allure.title("Тест логина с неверным паролем")
    def test_login_bad_wrong_data_401(self, api_manager, check):
        with allure.step("Подготовка данных"):

            bad_payload = {
              "email": "test1@email.com",
              "password": "12345678Aabra"
            }

        with allure.step("Отправка запроса на аутентификацию: ожидаем 401"):
            resp = api_manager.auth_api.login_user(bad_payload, expected_status=401)

        with allure.step("Проверка статус-кода: ожидаем 401"):
            assert resp.status_code == 401, f"Ожидался ответ 401, а получен {resp.status_code}"

        with allure.step("Валидация сообщения об ошибке"):
            error_data = ErrorRegisterResponse.model_validate(resp.json())
            with check:
                check.is_in("Неверный логин или пароль", error_data.message)
                check.is_in("Unauthorized", error_data.error)

    @allure.story("Вход неподтвержденным пользователем")
    @allure.title("Тест логина с неподтвержденным пользователем (403 Forbidden)")
    def test_login_unverified_user_403(self, api_manager, super_admin, test_user):
        with allure.step("Подготовка данных"):
            reg_resp = api_manager.auth_api.register_user(test_user, expected_status=201)
            created = RegisterUserResponse.model_validate(reg_resp.json())

        with allure.step("Меняем подтверждение пользователя через админа"):
            patch_data = PatchUserRequest(verified=False)
            patch_resp = super_admin.api.user_api.patch_user(created.id, patch_data, expected_status=200)
            patched = PatchUserResponse.model_validate(patch_resp.json())

        with allure.step("Попытка логиниться под непотвержденным пользователем"):
            login_data = LoginRequest(email=test_user.email, password=test_user.password)
            login_resp = api_manager.auth_api.login_user(login_data, expected_status=403)

    @allure.story("Передача поврежденного JSON")
    @allure.title("Передача невалидной структуры JSON при аутентификации")
    def test_login_malformed_json_400(self, api_manager, test_user, check):
        with allure.step("Подготовка данных"):
            bad_data = '{"email":, "password": "12345678Aabra"}'

        with allure.step("Отправка запроса на аутентификацию"):
            resp = api_manager.auth_api.login_user(bad_data, expected_status=400)

        with allure.step("Проверка статус-кода: ожидаем 400"):
            assert resp.status_code == 400, f"Ожидался ответ 400, а получен {resp.status_code}"

        with allure.step("Валидация сообщения об ошибке"):
            error_data = ErrorRegisterResponse.model_validate(resp.json())
            message = error_data.message
            with check:
                check.is_true(
                    message.startswith("Unexpected token"),
                    f"Ожидали начало на 'Unexpected token', получили на : {message}"
                )
                check.is_in("Bad Request", error_data.error)

    @allure.story("Refresh без авторизации")
    @allure.title("Обновление токенов без авторизации: ожидаем 401")
    def test_refresh_tokens_negative(self, api_manager, check):
        with allure.step("Отправка запроса на refresh-tokens без токена"):
            resp = api_manager.auth_api.refresh_token(expected_status=401)

        with allure.step("Валидация ответа"):
            error_data = ErrorRegisterResponse.model_validate(resp.json())

            with check:
                check.equal(resp.status_code, 401)
                check.is_in("Пользователь не авторизован", error_data.message)
                check.equal(error_data.error, "Unauthorized")

    @allure.story("Подтверждение почты с неверным токеном")
    @allure.title("Подтверждение email с неверным токеном (Mock)")
    def test_confirm_email_invalid_token_mock(self, api_manager, test_user, check, mocker):
        invalid_token = "wrong-token-12345"
        expected_error_body = {
            "message": "Неверный токен",
            "error": "Bad Request",
            "statusCode": 400
        }

        with allure.step("Мокаем получение невалидного токена из БД"):
            mocker.patch(
                f"{__name__}.get_confirmation_token_by_email",
                return_value=invalid_token
            )

        with allure.step("Мокаем ответ API 400 c JSON-телом"):
            mock_response = mocker.Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = expected_error_body

            mocker.patch.object(
                api_manager.auth_api,
                "confirm_email",
                return_value=mock_response
            )

        with allure.step("Выполнение запроса с плохим токеном"):
            token = get_confirmation_token_by_email(test_user.email)
            resp = api_manager.auth_api.confirm_email(token)


        with allure.step("Проверка структуры и содержания ошибки"):
            resp_json = resp.json()
            with check:
                check.equal(resp.status_code, 400, "Ожидался статус-код 400")
                check.equal(resp_json["message"], "Неверный токен", "Неверное сообщение об ошибке")
                check.equal(resp_json["error"], "Bad Request")
                check.equal(resp_json["statusCode"], 400)


