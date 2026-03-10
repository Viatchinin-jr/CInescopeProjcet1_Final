from multiprocessing.resource_tracker import register
from API.api_manager import ApiManager
from models.user_model import UserTest, RegisterUserResponse, PatchUserRequest, PatchUserResponse
from models.auth_model import LoginRequest, LoginResponse, RefreshTokenResponse, RegisterUserRequest, ErrorRegisterResponse

from utils.data_generator import DataGenerator
from db_requester.db_client import get_db_session
from db_models.transaction_model import AccountTransactionTemplate
import datetime
import allure
import psycopg2
import time
from db_requester.db_client import get_confirmation_token_by_email



@allure.feature("Тесты авторизации")
class TestAuthAPI:
    @allure.title("Тест регистрации пользователя")
    def test_register_user(self, api_manager: ApiManager, test_user: UserTest, check):
        with allure.step("Подготовка данных запроса"):
            # Мы создаем модель запроса, которая возьмет только нужное из UserTest
            register_req = RegisterUserRequest.model_validate(test_user.model_dump())

        with allure.step("Отправляем post-запрос на регистрацию через метод register_user"):
            # Теперь мы передаем строго RegisterUserRequest
            response = api_manager.auth_api.register_user(register_req)

        with allure.step("Проверка статус-кода ответа"):
            assert response.status_code == 201, f"Неверный статус-код. Ожидали 201, а получили {response.status_code}"

        with allure.step("Валидация структуры ответа через Pydantic"):
            # 1. Берем JSON из ответа сервера: response.json()
            # 2. Передаем этот словарь в метод модели
            registered_user = RegisterUserResponse.model_validate(response.json())

        with allure.step("Проверка соответствия данных в ответе"):
            with check:
                check.equal(registered_user.email, test_user.email, f"Ожидали {test_user.email}, получили {registered_user.email}")
                check.equal(registered_user.fullName, test_user.fullName, f"Ожидали {test_user.fullName}, а получили {registered_user.fullName}")


    @allure.title("Тест регистрации пользователя с помощью Mock")
    @allure.severity(allure.severity_level.MINOR)
    @allure.label("qa_name", "Nikita")
    def test_register_user_mock(self, api_manager: ApiManager, test_user: UserTest, mocker, check):
        with allure.step("Мокаем метод register_user в auth_api"):
            mock_response = RegisterUserResponse(  # Фиктивный ответ
                    id="id",
                    email="email@email.com",
                    fullName="fullName",
                    verified=True,
                    banned=False,
                    roles=["SUPER_ADMIN"],
                    createdAt=str(datetime.datetime.now())
                )

            mocker.patch.object(
                api_manager.auth_api, # Объект который нужно замокать
                "register_user", # Метод, который нужно замокать
                return_value=mock_response # Фиктивный ответ
            )
        with allure.step("Вызываем метод, который должен быть замокан"):
            register_user_response = api_manager.auth_api.register_user(test_user)

        with allure.step("Проверяем, что ответ соответствует ожидаемому"):
            with allure.step("Проверка поля персональных данных"):
                with check:
                    # check.equal(register_user_response.fullName, "INCORRECT_NAME", "Несовпадение fullName") оставил из учебного варианта
                    check.equal(register_user_response.fullName, mock_response.fullName)
                    check.equal(register_user_response.email, mock_response.email)

            with allure.step("Проверка поля banned"):
                with check("Проверка поля banned"): # Можно использовать вместо allure.step
                    check.equal(register_user_response.banned, mock_response.banned)

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

    @allure.title("Успешное подтверждение через email (Mock)")
    def test_confirm_email_positive(self, api_manager, test_user, check, mocker):
        # 1. Данные для имитации
        fake_token = "12345-fake-token-67890"

        with allure.step("Мокаем получение токена из БД"):
            # Патчим функцию в том месте, где она импортирована или используется
            mocker.patch(
                f"{__name__}.get_confirmation_token_by_email",
                return_value = fake_token
            )

        with allure.step("Мокаем ответ API подтверждения"):
            # Создаем фейковый объект ответа
            mock_response = mocker.Mock()
            mock_response.status_code = 200
            mock_response.text = "Пользователь подтверждён"

            mocker.patch.object(
                api_manager.auth_api,
                "confirm_email",
                return_value=mock_response
            )

        with allure.step("Выполнение шагов теста с моками"):
            # Регистрация (ее также можно замокать, если нужно)
            api_manager.auth_api.register_user(test_user)

            # Получаем токен (вызывается наш мок)
            token = get_confirmation_token_by_email(test_user.email)

            # Подтверждаем
            resp = api_manager.auth_api.confirm_email(token)

        with allure.step("Проверка результата"):
            with check:
                check.equal(token, fake_token, "Токен не совпадает с фейковым")
                check.equal(resp.text, "Пользователь подтверждён")



@allure.feature("Негативные тесты AuthAPI")
class TestAuthNegative:

    @allure.title("Регигстрация пользователя с уже существующим email")
    def test_register_user_negative_409(self, api_manager, registered_user, check):
        with allure.step("Подготовка данных: дубликат email"):
            # Берем email уже созданного юзера
            dublicated_req = RegisterUserRequest(
                email=registered_user.email,  # тот же email
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

    @allure.title("Регистрация с некорректным форматом email")
    def test_register_user_wrong_data_400(self, api_manager, check):
        with allure.step("Подготовка данных: некорректный email"):
            # придется использовать словарь, чтобы Pydantic не остановил нас раньше времени
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
            # Используем модель ErrorRegisterResponse
            error_data = ErrorRegisterResponse.model_validate(resp.json())
            with check:
                check.is_in("Некорректный email", error_data.message)


    @allure.title("Тест логина с неверными кредами")
    def test_login_bad_wrong_data_401(self, api_manager, check):
        with allure.step("Подготовка данных"):
            # Подготовка словаря, чтобы Pydantic нас не остановил
            bad_payload = {
              "email": "test1@email.com", # логин верный
              "password": "12345678Aabra" # пароль нет
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

    @allure.title("Тест логина с неподтвержденным пользователем")
    def test_login_unverified_user_403(self, api_manager, super_admin, test_user):
        with allure.step("Подготовка данных"):
            # 1. Регистрируем нового пользователя
            reg_resp = api_manager.auth_api.register_user(test_user, expected_status=201)
            created = RegisterUserResponse.model_validate(reg_resp.json())

        with allure.step("Меняем подтверждение пользователя через админа"):
            # 2. Админ делает verified=false
            patch_data = PatchUserRequest(verified=False)
            patch_resp = super_admin.api.user_api.patch_user(created.id, patch_data, expected_status=200)
            patched = PatchUserResponse.model_validate(patch_resp.json())

        with allure.step("Попытка логиниться под непотвержденным пользователем"):
            login_data = LoginRequest(email=test_user.email, password=test_user.password)
            login_resp = api_manager.auth_api.login_user(login_data, expected_status=403)

    @allure.title("Передача поврежденной структуры JSON при аутентификации")
    def test_login_malformed_json_400(self, api_manager, test_user, check):
        with allure.step("Подготовка данных"):
            # Подготовка словаря, чтобы Pydantic нас не остановил
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

    @allure.title("Обновление токенов без авторизации: ожидаем 401")
    def test_refresh_tokens_negative(self, api_manager, check):
        with allure.step("Отправка запроса на refresh-tokens без токена"):
            # Сразу без авторизации
            resp = api_manager.auth_api.refresh_token(expected_status=401)

        with allure.step("Валидация ответа"):
            error_data = ErrorRegisterResponse.model_validate(resp.json())

            with check:
                check.equal(resp.status_code, 401)
                check.is_in("Пользователь не авторизован", error_data.message)
                check.equal(error_data.error, "Unauthorized")


    @allure.title("Подтверждение email с неверным токеном (Mock)")
    def test_confirm_email_invalid_token_mock(self, api_manager, test_user, check, mocker):
        # 1. Данные для имитации ошибки
        invalid_token = "wrong-token-12345"
        expected_error_body = {
            "message": "Неверный токен",
            "error": "Bad Request",
            "statusCode": 400
        }

        with allure.step("Мокаем получение невалидного токена из БД"):
            # Имитируем, что БД вернула нам плохой токен
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
            resp_json = resp.json() # Вызываем метод .json() у нашего мока
            with check:
                check.equal(resp.status_code, 400, "Ожидался статус-код 400")
                check.equal(resp_json["message"], "Неверный токен", "Неверное сообщение об ошибке")
                check.equal(resp_json["error"], "Bad Request")
                check.equal(resp_json["statusCode"], 400)


