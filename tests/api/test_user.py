from http.client import responses
import allure
import pytest
from execnet.script.socketserver import exec_from_one_connection
from pygments.lexers import q
from sqlalchemy.testing.exclusions import succeeds_if
from models.user_model import RegisterUserResponse, PatchUserRequest, PatchUserResponse, GetAllUsersRequest, SortOrder, \
    GetAllUsersResponse, ErrorCreateResponse
from utils.data_generator import DataGenerator

@allure.feature("Позитивные тесты работы с /user")
class TestUser:

    @allure.title("Тест создания пользователя")
    def test_create_user(self, super_admin, creation_user_data, check):
        with allure.step("Попытка создания пользователя"):
            response = super_admin.api.user_api.create_user(creation_user_data, expected_status=201)

        with allure.step("Проверка статус-код 201 Created"):
            assert response.status_code == 201, f"Ошибка! Ожидался ответ 201, а получен {response.status_code}"

        with allure.step("Валидация структуры ответа моделью"):
            # Если структура JSON не совпадает с моделью, тест упадет уже здесь
            user_response = RegisterUserResponse.model_validate(response.json())

        with allure.step("Проверка соответствия ролей созданного пользователя"):
            with check:
                check.is_not_none(user_response.id, "ID пользователя должен быть сгенерирован!")
                check.equal(user_response.email, creation_user_data.email, "Email не совпадает!")
                check.equal(user_response.fullName, creation_user_data.fullName, "Имя не совпадает!")
                check.equal(user_response.roles, creation_user_data.roles, "Роль не совпадает!")
                check.equal(user_response.verified, creation_user_data.verified, "Статус verified не совпадает!")
                check.equal(user_response.banned or False, creation_user_data.banned, "Статус banned не совпадает!")


    @allure.title("Тест получения пользователей по ID и по Email")
    def test_get_user_by_locator(self, super_admin, creation_user_data, check):
        # 1. Создание пользователя (Предусловие)
        with allure.step(f"Предусловие: создание пользователя {creation_user_data.email}"):
            creation_resp = super_admin.api.user_api.create_user(creation_user_data, expected_status=201)
            created = RegisterUserResponse.model_validate(creation_resp.json())

        # 2. Получение по ID
        with allure.step(f"Получение пользователя по ID: {created.id}"):
            resp_id = super_admin.api.user_api.get_user(created.id, expected_status=200)
            assert resp_id.status_code == 200, f"Ожидался 200 по ID, получен {resp_id.status_code}"
            user_by_id = RegisterUserResponse.model_validate(resp_id.json())

        # 3. Получение по Email
        with allure.step(f"Получение пользователя по Email: {created.email}"):
            resp_email = super_admin.api.user_api.get_user(created.email, expected_status=200)
            assert resp_email.status_code == 200, f"Ожидался 200 по Email, получен {resp_email.status_code}"
            user_by_email = RegisterUserResponse.model_validate(resp_email.json())

        # 4. Проверка идентичности и корректности данных
        with allure.step("Сверка данных между отчетами и исходными данными"):
            with check:
                # Проверяем, что оба способа получения вернули идентичный объект
                check.equal(user_by_id, user_by_email, "Объекты, полученные по ID и Email не идентичны!")

                # Сверяем поля с тем, что мы отправляли при создании
                check.equal(user_by_id.email, creation_user_data.email, "Email в базе не совпадает с отправленным!")
                check.equal(user_by_id.fullName, creation_user_data.fullName, "fullName в базе не совпадает с отправленным")
                check.equal(user_by_id.roles, creation_user_data.roles, "Роли в базе не совпадают!")
                check.is_true(user_by_id.verified, "Статус verified должен быть True")

                actual_banned = user_by_id.banned if user_by_id.banned is not None else False
                check.equal(actual_banned, creation_user_data.banned, "Статус banned не совпадает!")


    @allure.title("Удаление пользователя super-admin-ом")
    def test_delete_by_super_admin(self, super_admin, creation_user_data, check):
        """
        Внимание! В свагере указано, что на DELETE - 200 возвращается объект пользователя.
        Но по факту приходит пустое тело. Тест адаптирован под реальную* работу апи.
        """
        with allure.step("Предусловие: создание пользователя"):
            creations_resp = super_admin.api.user_api.create_user(creation_user_data, expected_status=201)
            created = RegisterUserResponse.model_validate(creations_resp.json())

        with allure.step(f"Удаление пользователя по ID {created.id}"):
            resp = super_admin.api.user_api.delete_user(created.id, expected_status=200)
            assert resp.status_code == 200, f"Ожидался ответ 200, получен {resp.status_code}"


        with allure.step("Проверка отсутствия пользователя после удаления"):
            # Тут зафиксируем наше странное поведение: 200 вместо 404
            get_resp = super_admin.api.user_api.get_user(created.id, expected_status=200)

            with check:
                # Проверяем, что тело действительно пустое
                check.equal(get_resp.json(), {}, "После удаления GET должен возвращать пустой объект {}")


    @allure.title("Успешное частичное обновление пользователя (PATCH)")
    def test_patch_by_success(self, super_admin, creation_user_data, patch_user_data, check):
        with allure.step("Предусловие: создание пользователя"):
            creation_resp = super_admin.api.user_api.create_user(creation_user_data, expected_status=201)
            created = RegisterUserResponse.model_validate(creation_resp.json())

        with allure.step(f"Обновление полей (roles, verified, banned) для ID {created.id}"):
            # Отправляем только те поля, которые есть в PatchUserRequest
            patch_response = super_admin.api.user_api.patch_user(created.id, patch_user_data, expected_status=200)
            patched = PatchUserResponse.model_validate(patch_response.json())

        with allure.step("Проверка обновленных и неизмененных полей в ответе"):
            with check:
                # Проверяем то, что меняли:
                check.equal(patched.roles, patch_user_data.roles, "Роли не обновились в ответе!")
                check.equal(patched.verified, patch_user_data.verified, "Статус verified не обновился")

                actual_banned = patched.banned if patched.banned is not None else False
                check.equal(actual_banned, patch_user_data.banned, "Статус banned не совпадает!")

                # Проверка сохранности (email и fullName не должны измениться)
                check.equal(patched.email, created.email, "Email изменился после Patch, хотя не должен был")
                check.equal(patched.fullName, created.fullName, "fullName изменился после Patch, хотя не должен был")

        with allure.step("Верификация состояния пользователя в базе через GET"):
            get_resp = super_admin.api.user_api.get_user(created.id, expected_status=200)
            final_state = RegisterUserResponse.model_validate(get_resp.json())

            with check:
                check.equal(final_state.roles, patch_user_data.roles, "В базе роли не обновились")
                check.equal(final_state.email, created.email, "В базе email изменился после Patch")


    @allure.title("Тест на успешное получение списка всех пользователей")
    def test_get_all_users(self, super_admin, check):
        with allure.step("Подготавливаем query-параметры через модель"):
            request_params = GetAllUsersRequest(
                page=1,
                pageSize=10,
                createdAt=SortOrder.asc
            )

        with allure.step("Выполняем запрос"):
            response = super_admin.api.user_api.get_all_users(request_params)

        with allure.step("Проверяем HTTP-статус"):
            assert response.status_code == 200, f"Ожидался статус код 200, получен {response.status_code}"

        with allure.step("Валидируем ответ моделью"):
            data = GetAllUsersResponse.model_validate(response.json())

        with allure.step("Проверка корректности данных"):
            with check:
                check.equal(data.page, request_params.page, "Номер страницы не совпадает!")
                check.equal(data.pageSize, request_params.pageSize, "Размер страницы не совпадает")
                check.greater_equal(data.count, 0, "Количество пользователей не может быть отрицательным")

                if data.users:
                    with allure.step(f"Проверка структуры первого пользователя из {len(data.users)}"):
                        user = data.users[0]
                        # Проверяем наличие обязательных полей, которые не пустые
                        check.is_not_none(user.id, "ID пользователя отсутсвует")
                        check.is_not_none(user.email, "Email пользователя отсутствует")
                        check.is_instance(user.roles, list, "Поле roles должно быть списком")



@allure.feature("Негативные тесты работы с /user")
class TestUserNegative:


    @allure.title("Тест создания пользователя: ожидаем 403")
    def test_create_user_not_access_403(self, common_user, creation_user_data, check):
        with allure.step("Сразу отправляем запрос на создание"):
            resp = common_user.api.user_api.create_user(creation_user_data, expected_status=403)

        with allure.step("Проверяем статус-код"):
            assert resp.status_code == 403, f"Ожидался ответ 403, получен {resp.status_code}"

        with allure.step("Валидируем тело ответа"):
            error_data = ErrorCreateResponse.model_validate(resp.json())

        with allure.step("Детальная провекра содержимого"):
            with check:
                check.equal(error_data.statusCode, 403, "Код в теле ответа должен быть 403!")
                check.equal(error_data.message, "Forbidden resource", "Сообщение в теле ответа должно быть: 'Forbidden resource'")
                check.equal(error_data.error, "Forbidden", "Тип ошибки должен быть: 'Forbidden'")

    @allure.title("Тест создания пользователя: ожидаем 401 (Unauthorized)")
    def test_create_unauthorized_401(self, api_manager, creation_user_data, check):
        with allure.step("Отправка запроса без заголовка Authorization"):
            resp = api_manager.user_api.create_user(creation_user_data, expected_status=401)

        with allure.step("Провекра статус кода 401"):
            assert resp.status_code == 401, f"Ожидался 401, получен {resp.status_code}"

        with allure.step("Валидация тела ответа"):
            error_data = ErrorCreateResponse.model_validate(resp.json())
            with check:
                check.equal(error_data.message, "Unauthorized", "Сообщение в теле ответа должно быть Unauthorized!")
                check.equal(error_data.statusCode, 401, "Код в теле ответа должен быть 401")

    @allure.title("Тест создания пользователя: ожидаем 400 (Bad Request)")
    def test_create_bad_request_400(self, super_admin, creation_user_data, check):
        with allure.step("Подготовка данных"):
            bad_user_model = creation_user_data.model_copy(update={"fullName": True})
            bad_data = bad_user_model.model_dump()

        with allure.step("Отправка запроса на создание"):
            resp = super_admin.api.user_api.create_user(bad_data, expected_status=400)

        with allure.step("Провекра статус кода: ожидаем 400"):
            assert resp.status_code == 400, f"Ожидался 400, получен {resp.status_code}"

        with allure.step("Валидация тела ответа"):
            error_data = ErrorCreateResponse.model_validate(resp.json())
            with check:
                check.equal(error_data.statusCode, 400, "Код в теле ответа должен быть 400")
                check.equal(error_data.error, "Bad Request", "Ошибка в теле ответа должно быть 'Bad Request'")

    @pytest.mark.xfail(reason="Баг бэка? Возвращает 500 вместо 409 при дубликате email")
    @allure.title("Тест создания пользовавтеля: ожидаем 409 (Conflict)")
    def test_create_conflict_409(self, super_admin, creation_user_data, check):
        with allure.step("Создание первого пользователя"):
            resp_0 = super_admin.api.user_api.create_user(creation_user_data, expected_status=201)

        with allure.step("Повторный запрос с тем же email"):
            resp_1 = super_admin.api.user_api.create_user(creation_user_data, expected_status=409)

        with allure.step("Валидация тела ответа"):
            error_data = ErrorCreateResponse.model_validate(resp_1.json())
            with check:
                check.equal(error_data.statusCode, 409, "Статус код должен быть 409!")


    @allure.title("Удаление пользователя: ошибка 403")
    def test_delete_user_forbidden(self, super_admin, common_user, creation_user_data, check):
        """
        Внимание! Заметил, что тут DELETE не возвращает поле error в ответе.
        """
        with allure.step("Предусловие: создание целевого пользователя администратором"):
            # Генерируем новый случайный email для каждой итерации теста
            random_email = f"forbidden_{DataGenerator.generate_random_email()}"
            unique_data = creation_user_data.model_copy(update={"email": random_email})
            creation_resp = super_admin.api.user_api.create_user(unique_data, expected_status=201)
            target_user_id = creation_resp.json()["id"]

        with allure.step(f"Попытка удаления пользователя {target_user_id} обычным юзером"):
            # Ожидаем 403 Forbidden
            resp = common_user.api.user_api.delete_user(target_user_id, expected_status=403)

        with allure.step("Валидация тела ответа об ошибке"):
            error_data = ErrorCreateResponse.model_validate(resp.json())
            with check:
                check.equal(error_data.statusCode, 403)
                check.equal(error_data.message, "Forbidden")



    @allure.title("Удаление пользователя: ошибка 404 (Не найден)")
    def test_delete_nonexistent_user_404(self, super_admin, check):
        non_existent_id = "00000000-0000-0000-0000-000000000000"

        with allure.step(f"Попытка удаления несуществующего пользователя {non_existent_id}"):
            # Пытаемся удалить и ждем 404
            resp = super_admin.api.user_api.delete_user(non_existent_id, expected_status=404)

        with allure.step("Валидация тела ответа об ошибке"):
            error_data = ErrorCreateResponse.model_validate(resp.json())
            with check:
                check.equal(error_data.statusCode, 404)
                check.equal(error_data.message, "Not Found")


    @allure.title("Обновление пользователя: ошибка 403 (Forbidden)")
    def test_user_cannot_patch_someone_else_403(self, super_admin, common_user, creation_user_data, patch_user_data, check):
        with allure.step("Предусловие: создание целевого пользователя администратором"):
            # Создаем копию данных с уникальным email для этого теста
            unique_email = f"patch_403_{DataGenerator.generate_random_email()}"
            unique_data = creation_user_data.model_copy(update={"email": unique_email})
            creation_resp = super_admin.api.user_api.create_user(unique_data, expected_status=201)
            target_user_id = creation_resp.json()["id"]

        with allure.step(f"Попытка обновления пользователя {target_user_id} обычным юзером"):
            resp = common_user.api.user_api.patch_user(target_user_id, patch_user_data, expected_status=403)

        with allure.step("Валидация тела и ответа"):
            error_data = ErrorCreateResponse.model_validate(resp.json())
            with check:
                check.equal(error_data.statusCode, 403)
                check.equal(error_data.error, "Forbidden")
                check.equal(error_data.message, "Forbidden resource")


    @allure.title("Обновление пользователя: ошибка 400 (Bad Request)")
    def test_patch_user_bad_request_400(self, super_admin, creation_user_data, check):
        with allure.step("Предусловие: создание пользователя"):
            creation_resp = super_admin.api.user_api.create_user(creation_user_data, expected_status=201)
            target_user_id = creation_resp.json()["id"]

        with allure.step("Отправка некорректных данных (невалидная роль)"):
            # Используем словарь, чтобы обойти валидацию Pydantic
            bad_data = {"roles": ["GOD_MODE"]}
            resp = super_admin.api.user_api.patch_user(target_user_id, bad_data, expected_status=400)

        with allure.step("Валидация тела ответа"):
            error_data = ErrorCreateResponse.model_validate(resp.json())
            with check:
                check.equal(error_data.statusCode, 400)
                check.equal(error_data.error, "Bad Request")
                check.is_in("roles", str(error_data.message))


    @pytest.mark.xfail(reason="Бэкенд возвращает 400 вместо 404 для несуществующего ID")
    @allure.title("Обновление пользователя: ошибка 404 (Не найден)")
    def test_patch_user_not_found_404(self, super_admin, creation_user_data, patch_user_data, check):
        # Генерируем ID которого точно нет в базе
        non_existent_id = "00000000-0000-0000-0000-000000000000"

        with allure.step(f"Попытка обновления несуществующего пользователя {non_existent_id}"):
            resp = super_admin.api.user_api.patch_user(non_existent_id, patch_user_data, expected_status=404)


        with allure.step("Валидация тела ответа об ошибке"):
            error_data = ErrorCreateResponse.model_validate(resp.json())
            with check:
                check.equal(error_data.statusCode, 404)
                check.equal(error_data.error, "Not Found")



    @pytest.mark.xfail(reason="Бэкенд возвращает 200 вместо 404 для несуществующего пользователя")
    @allure.title("Получение пользователей: ошибка 404 (Не найден)")
    def test_get_user_not_found_404(self, super_admin, check):
        # Генерируем заведомо несуществующий ID
        non_existent_id = "00000000-0000-0000-0000-000000000000"

        with allure.step(f"Запрос несуществующего пользователя по ID: {non_existent_id}"):
            resp = super_admin.api.user_api.get_user(non_existent_id, expected_status=404)

        with allure.step("Проверка статус кода 404"):
            assert resp.status_code == 404, f"Ожидался 404, а получен {resp.status_code}"

        with allure.step("Валидация тела ошибки"):
            error_data = ErrorCreateResponse.model_validate(resp.json())
            with check:
                check.equal(error_data.statusCode, 404)
                check.is_in("not found", error_data.message.lower())

    @allure.title("Получение пользователя: ошибка 403")
    def test_get_user_forbidden_403(self, super_admin, common_user, creation_user_data, check):
        # 1. Создаем пользователя через админа, чтобы получить реальный ID
        with allure.step("Предусловие: создание целевого пользователя администратором"):
            unique_email = f"foribdden_{DataGenerator.generate_random_email()}"
            unique_data = creation_user_data.model_copy(update={"email": unique_email})
            creation_resp = super_admin.api.user_api.create_user(unique_data, expected_status=201)

            # Получаем ID из ответа
            created_user = RegisterUserResponse.model_validate(creation_resp.json())
            target_user_id = created_user.id

        # 2. Пытаемся получить данные этого пользователя через common_user
        with allure.step(f"Запрос данных пользователя {target_user_id} обычным пользователем"):
            # Ожидаем, что сервер выдаст 403
            resp = common_user.api.user_api.get_user(target_user_id, expected_status=403)

        with allure.step("Проверка статус-кода: ожидаем 403"):
            assert resp.status_code == 403, f"Ожидался 403, а получен {resp.status_code}"

        with allure.step("Валидация тела ответа об ошибке"):
            error_data = ErrorCreateResponse.model_validate(resp.json())
            with check:
                check.equal(error_data.statusCode, 403, "Код в теле ответа должен быть 403!")
                check.equal(error_data.error, "Forbidden", "Поле error должно быть 'Forbidden'")
                check.equal(error_data.message, "Forbidden resource", "Сообщение должно быть 'Forbidden resource'")


    @allure.title("Негативный тест на получение списка всех пользователей. Ожидаем: 400.")
    def test_get_all_users_negative_pagesize_over_limit_400(self, super_admin, check):
        with allure.step("Подготовливаем query-параметры через модель"):
            req_params = GetAllUsersRequest.model_construct(
                page=1,
                pageSize=101,
                roles=None,
                createdAt=SortOrder.asc
            )

        with allure.step("Выполняем запрос"):
            response = super_admin.api.user_api.get_all_users(req_params, expected_status=400)

        with allure.step("Проверяем статус-код: ожидаем 400"):
            assert response.status_code == 400, f"Ожидался ответ 400, получен {response.status_code}"

        with allure.step("Валидация ответа моделью"):
            error_data = ErrorCreateResponse.model_validate(response.json())
            with check:
                check.equal(error_data.statusCode, 400)
                check.equal(error_data.error, "Bad Request")
                check.is_in("Поле pageSize имеет максимальную величину 20", error_data.message)


    @allure.title("Негативный тест на получение списка всех пользователей. Ожидаем 403")
    def test_common_user_cannot_get_all_users_403(self, super_admin, common_user, check):
        with allure.step("Подготовка query-параметров"):
            req_params = GetAllUsersRequest(
                page=1,
                pageSize=10,
                createdAt=SortOrder.asc
            )

        with allure.step("Отправка запроса через обычного пользователя"):
            response = common_user.api.user_api.get_all_users(req_params, expected_status=403)

        with allure.step("Валидация ответа моделью"):
            error_data = ErrorCreateResponse.model_validate(response.json())
            with check:
                check.equal(error_data.statusCode, 403)
                check.equal(error_data.error, "Forbidden")
                check.equal(error_data.message, "Forbidden resource")

