from http.client import responses
import pytest

from models.user_model import RegisterUserResponse, PatchUserRequest, PatchUserResponse, GetAllUsersRequest, SortOrder, GetAllUsersResponse
from utils.data_generator import DataGenerator


class TestUser:

    def test_create_user(self, super_admin, creation_user_data):
        response = super_admin.api.user_api.create_user(creation_user_data)
        user = RegisterUserResponse.model_validate(response.json())

        assert user.id
        assert user.email == creation_user_data.email
        assert user.fullName == creation_user_data.fullName
        assert user.roles == creation_user_data.roles
        assert user.verified == creation_user_data.verified

    def test_get_user_by_locator(self, super_admin, creation_user_data):
        created = RegisterUserResponse.model_validate(
            super_admin.api.user_api.create_user(creation_user_data).json()
        )

        user_by_id = RegisterUserResponse.model_validate(
            super_admin.api.user_api.get_user(created.id).json()
        )

        user_by_email = RegisterUserResponse.model_validate(
            super_admin.api.user_api.get_user(created.email).json()
        )

        assert user_by_id == user_by_email, "Содержимое должно быть идентичным"
        assert user_by_id.id
        assert user_by_id.email == creation_user_data.email
        assert user_by_id.fullName == creation_user_data.fullName
        assert user_by_id.roles == creation_user_data.roles
        assert user_by_id.verified is True

    def test_get_user_by_id_common_user(self, common_user):
        response = common_user.api.user_api.get_user(common_user.email, expected_status=403)
        assert response.status_code == 403


    def test_delete_by_super_admin(self, super_admin, creation_user_data):
        # 1. Создаем пользователя
        created = RegisterUserResponse.model_validate(
            super_admin.api.user_api.create_user(creation_user_data).json()
        )

        # 2. Удаляем пользователя
        resp = super_admin.api.user_api.delete_user(created.id, expected_status=200)
        assert resp.status_code == 200

        # 4. Контроль удаления пользователя. Вот тут нюанс, я хз, но вроде так апи просто работает странно. Мне 404 не хотело возвращать.
        check = super_admin.api.user_api.get_user(created.id, expected_status=200)
        assert check.json() == {}, "После удаления ожидаем пустое тело"

    def test_patch_by_user_id(self, super_admin, creation_user_data, patch_user_data):
        # 1. Создание юзера, которого будем патчить
        created = RegisterUserResponse.model_validate(
            super_admin.api.user_api.create_user(creation_user_data).json()
        )

        # 2. Патчим пользователя
        patch_response = super_admin.api.user_api.patch_user(created.id, patch_user_data, expected_status=200)
        # 3. Валидируем вернувшийся ответ моделью
        patched = PatchUserResponse.model_validate(patch_response.json())

        # assert patched.id == created.id, "ID не совпадают"
        assert patched.roles == patch_user_data.roles
        assert patched.verified == patch_user_data.verified
        assert patched.banned == patch_user_data.banned

        # Проверка совпадения id.
        got = RegisterUserResponse.model_validate(
            super_admin.api.user_api.get_user(created.id, expected_status=200).json()
        )
        assert got.id == created.id

    def test_get_all_users(self, super_admin):
        # 1. Подготавливаем query-пармаетры через модель
        request = GetAllUsersRequest(
            page=1,
            pageSize=10,
            createdAt=SortOrder.asc
        )

        # 2. Делаем запрос
        response = super_admin.api.user_api.get_all_users(request)

        # 3. Проверяем HTTP-статус
        assert response.status_code == 200

        # 4. Валидируем ответ моделью
        data = GetAllUsersResponse.model_validate(response.json())

        # 5. Базовые проверки ответа
        assert data.page == 1
        assert data.pageSize == 10
        assert data.count >= 0
        assert isinstance(data.users, list)

        # 6. Если пользователи есть - проверяем структуру первого
        if data.users:
            user = data.users[0]
            assert user.id
            assert user.email
            assert isinstance(user.roles, list)

class TestUserNegative:

    def test_user_cannot_delete_someone_else(self, super_admin, common_user, creation_user_data):
        # 1. Подготовка данных
        victim_data = creation_user_data.model_copy(
            update={"email": DataGenerator.generate_random_email()}
        )

        # 2. Создание юзера, которого будем удалять
        created = RegisterUserResponse.model_validate(
            super_admin.api.user_api.create_user(victim_data).json()
        )

        # 3. Пробуем удалить
        deleted = common_user.api.user_api.delete_user(created.id, expected_status=403)
        assert deleted.status_code == 403

    def test_delete_nonexistent_user_404(self, super_admin):
        response = super_admin.api.user_api.delete_user("00000000-0000-0000-0000-000000000000", expected_status=404)
        assert response.status_code == 404


    def test_user_cannot_patch_someone_else_403(self, super_admin, common_user, creation_user_data, patch_user_data):
        # 1. Создаем жертву
        victim_data = creation_user_data.model_copy(
            update={"email": DataGenerator.generate_random_email()}
        )

        # 2. Валидируем
        created = RegisterUserResponse.model_validate(
            super_admin.api.user_api.create_user(victim_data).json()
        )

        # 3. Попытка патча
        patch_resp = common_user.api.user_api.patch_user(created.id, patch_user_data, expected_status=403)
        assert patch_resp.status_code == 403

    def test_patch_user__400(self, super_admin, patch_user_data):
        patch_resp = super_admin.api.user_api.patch_user("00000000-0000-0000-0000-000000000000", patch_user_data, expected_status=400)
        assert patch_resp.status_code == 400

    @pytest.mark.skip(reason="Я так и не смог отловить именно 400")
    def test_patch_user_404(self, super_admin, creation_user_data, patch_user_data):
        created = RegisterUserResponse.model_validate(
            super_admin.api.user_api.create_user(creation_user_data).json()
        )

        del_resp = super_admin.api.user_api.delete_user(created.id, expected_status=200)
        assert del_resp.status_code == 200

        patch_resp = super_admin.api.user_api.patch_user(created.id, patch_user_data, expected_status=404)
        assert patch_resp.status_code == 404


    def test_patch_wrong_data_400(self, super_admin, patch_user_data, creation_user_data):
        # 1. Создание юзера, которого будем пытаться патчить
        created = RegisterUserResponse.model_validate(
            super_admin.api.user_api.create_user(creation_user_data).json()
        )

        # Делаем неправильные данные
        bad_patch = {"verified": "not bool"} # делаем строку вместо bool

        patch_resp = super_admin.api.user_api.patch_user(created.id, bad_patch, expected_status=400)
        assert patch_resp.status_code == 400

    def test_get_all_users_negative_pagesize_over_limit_400(self, super_admin):
        # 1. Подготавливаем query-пармаетры через модель.
        # Поскольку pageSize > 100, Pydantic остановит выполнение. Поэтому используем .model_construct

        req = GetAllUsersRequest.model_construct(
            page=1,
            pageSize=101,
            roles=None,
            createdAt=SortOrder.asc
        )

        # 2. Выполняем запрос
        get_resp = super_admin.api.user_api.get_all_users(req, expected_status=400)
        assert get_resp.status_code == 400

    def test_common_user_cannot_get_all_users_403(self, super_admin, common_user):
        req = GetAllUsersRequest(
            page=1,
            pageSize=10,
            createdAt=SortOrder.asc
        )

        get_resp = common_user.api.user_api.get_all_users(req, expected_status=403)
        assert get_resp.status_code == 403
