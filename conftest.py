from faker import Faker
import pytest
import requests
from API.api_manager import ApiManager
from constants import BASE_URL, REGISTER_ENDPOINT
from custom_requester.custom_requester import CustomRequester
from utils.data_generator import DataGenerator



faker = Faker()

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

@pytest.fixture(scope="session")
def test_user():
    """
    Генерация случайного пользователя для тестов.
    """
    random_email = DataGenerator.generate_random_email()
    random_name = DataGenerator.generate_random_name()
    random_password = DataGenerator.generate_random_password()

    return {
        "email": random_email,
        "fullName": random_name,
        "password": random_password,
        "passwordRepeat": random_password,
        "roles": ["USER"]
    }

@pytest.fixture(scope="session")
def registered_user(requester, test_user):
    """
    Фикстура для регистрации и получения данных зарегистрированного пользователя.
    """
    response = requester.send_request(
        method="POST",
        endpoint=REGISTER_ENDPOINT,
        data=test_user,
        expected_status=201
    )
    response_data = response.json()
    registered_user = test_user.copy()
    registered_user["id"] = response_data["id"]
    return registered_user

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


