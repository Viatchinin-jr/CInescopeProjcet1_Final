import pytest
import requests
from API.api_manager import ApiManager
from constants import BASE_URL, REGISTER_ENDPOINT
from custom_requester.custom_requester import CustomRequester
from resources.user_creds import SuperAdminCreds
from utils.data_generator import DataGenerator
from entities.user import User
from const.roles import Roles
from models.user_model import UserTest, RegisteredUser, RegisterUserResponse, CreateUserRequest, PatchUserRequest


@pytest.fixture
def user_session():
    user_pool = []

    def _create_user_session():
        session = requests.Session()
        user_session = ApiManager(session)
        user_pool.append(user_session)
        return user_session

    yield _create_user_session

    for user in user_pool:
        user.close_session()

@pytest.fixture(scope="session")
def session():
    """
    Фикстура для создания HTTP-сессии.
    """
    http_session = requests.Session()
    yield http_session
    http_session.close()

@pytest.fixture(scope="session")
def api_manager(session):
    """
    Фикстура для создания экземпляра ApiManager.
    """
    return ApiManager(session)

@pytest.fixture
def unauthorized_api_manager():
    """
    ApiManager с новой HTTP-сессией без авторизационных заголовков.
    Используется для негативных тестов, где важно отсутствие токена
    """
    http_session = requests.Session()
    return ApiManager(http_session)

@pytest.fixture
def test_user() -> UserTest:
    """
    Генерация случайного пользователя для тестов.
    """
    random_password = DataGenerator.generate_random_password()

    return UserTest(
        email=DataGenerator.generate_random_email(),
        fullName=DataGenerator.generate_random_name(),
        password=random_password,
        passwordRepeat=random_password,
        roles=[Roles.USER.value]
    )

@pytest.fixture
def common_user(user_session, super_admin, creation_user_data):
    new_session = user_session()

    common_user = User(
        creation_user_data.email,
        creation_user_data.password,
        [Roles.USER.value],
        new_session
    )

    super_admin.api.user_api.create_user(creation_user_data)
    common_user.api.auth_api.authenticate(common_user.creds)
    return common_user



@pytest.fixture(scope="function")
def creation_user_data(test_user: UserTest) -> CreateUserRequest:
    return CreateUserRequest(
        email=test_user.email,
        fullName=test_user.fullName,
        password=test_user.password,
        roles=test_user.roles,
        verified=True,
        banned=False
    )

@pytest.fixture
def super_admin(user_session):
    new_session = user_session()

    super_admin = User(
        SuperAdminCreds.USERNAME,
        SuperAdminCreds.PASSWORD,
        [Roles.SUPER_ADMIN.value],
        new_session
    )

    super_admin.api.auth_api.authenticate(super_admin.creds)
    return super_admin

@pytest.fixture
def admin_user(user_session, super_admin, creation_user_data):
    new_session = user_session()

    # создаем новую модель
    admin_data = creation_user_data.model_copy(update={"roles": [Roles.ADMIN]})

    admin = User(
        creation_user_data.email,
        creation_user_data.password,
        [Roles.ADMIN.value],
        new_session
    )

    # Пользователя создает SUPER_ADMIN
    super_admin.api.user_api.create_user(admin_data)

    # Логинимся под админом
    admin.api.auth_api.authenticate(admin.creds)

    return admin

@pytest.fixture
def registered_user(requester, test_user: UserTest) -> RegisteredUser:
    """
    Фикстура для регистрации и получения данных зарегистрированного пользователя.
    """
    response = requester.send_request(
        method="POST",
        endpoint=REGISTER_ENDPOINT,
        data=test_user,
        expected_status=201
    )

    register_response = RegisterUserResponse.model_validate(response.json())

    return RegisteredUser(
        id=register_response.id,
        email=test_user.email,
        password=test_user.password
    )


@pytest.fixture(scope="session")
def requester():
    """
    Фикстура для создания экземпляра CustomRequester.
    """
    session = requests.Session()
    return CustomRequester(session=session, base_url=BASE_URL)

@pytest.fixture
def movie_payload():
    """
    Генерирует случайный фильм через DataGenerator
    """
    return DataGenerator.generate_random_movie()

@pytest.fixture
def created_movie(api_manager, admin_auth, movie_payload):
    resp = api_manager.movies_api.create_movie(movie_payload)
    assert resp.status_code == 201
    movie = resp.json()

    yield movie # movie["id"], movie["name"], ...

    # очистка
    api_manager.movies_api.delete_movie(movie["id"], expected_status=200)

@pytest.fixture
def create_movie_for_delete(api_manager, admin_auth, movie_payload):
    response = api_manager.movies_api.create_movie(movie_payload)
    assert response.status_code == 201
    return response.json()

@pytest.fixture
def existing_movie(api_manager, admin_auth, movie_payload):
    response = api_manager.movies_api.create_movie(movie_payload)
    assert response.status_code == 201

    movie = response.json() # тянем body с апи
    used_movie_payload = movie_payload.copy() # тут исходный payload

    yield movie, used_movie_payload

    # очистка
    api_manager.movies_api.delete_movie(movie["id"], expected_status=200)

@pytest.fixture(scope="session")
def admin_auth(api_manager):
    """
    Логинится под кредами супер-админа и кладет токен в headers сессии
    """
    creds = ("api1@gmail.com", "asdqwe123Q")
    token = api_manager.auth_api.authenticate(creds)
    assert token, "Не удалось получить токен"
    return token

@pytest.fixture
def patch_movie_payload():
    """
    Генерирует случайный patch
    """
    return DataGenerator.generate_random_patch_data()


@pytest.fixture
def patch_user_data() -> PatchUserRequest:
    return PatchUserRequest(
        roles=[Roles.USER],
        banned=True,
        verified=False
    )

