import pytest
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from db_requester.db_client import get_db_session
from db_requester.db_helpers import DBHelper
from utils.data_generator import DataGenerator
import uuid
from db_models.transaction_model import Base



# @pytest.fixture(scope="module")
# #def db_session() -> Session:
#     """
#     Фикстура, которая создает и возвращает сессию для работы с базой данных. После завершения теста - сессия автоматически закрывается.
#     """
#     # SessionLocal = get_db_session() # sessionamker
#     # session = SessionLocal()
#     # try:
#     #     yield session
#     # finally:
#     #     session.close()

@pytest.fixture(scope="module")
def db_session() -> Session:
    # get_db_session() уже возвращает объект сессии со скобками
    session = get_db_session()
    yield session
    session.close()

@pytest.fixture
def tx_db_session() -> Session:
    """
    Отдельная фикстура БД в памяти (SQLite)
    для тестов транзакций.
    """
    # 1) создаем engine в памяти
    engine = create_engine("sqlite:///:memory:")

    # 2) создаем таблицы
    Base.metadata.create_all(engine)

    # 3) Создаем сессию
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()



@pytest.fixture(scope="function")
def db_helper(db_session) -> DBHelper:
    """Фикстура для экземпляра хелпера"""
    db_helper = DBHelper(db_session)
    return db_helper


@pytest.fixture(scope="function")
def created_test_user(db_helper):
    """
    Фикстура, которая создает тестового пользователя в ДБ
    и удаляет его после завершения теста
    """
    user = db_helper.create_test_user(DataGenerator.generate_user_data())
    yield user
    # Cleanup после теста
    if db_helper.get_user_by_id(user.id):
        db_helper.delete_user(user)

@pytest.fixture(scope="function")
def created_test_movie(db_helper):
    """
    Фикстура, которая создает тестовый фильм в ДБ и удаляет его после завершения теста.
    """
    movie = db_helper.create_test_movie(DataGenerator.generate_random_movie())
    yield movie

    #Cleanup после теста
    movie_from_db = db_helper.get_movie_by_name(movie.name)
    if movie_from_db:
        db_helper.delete_movie(movie_from_db)

@pytest.fixture(scope="function")
def non_exist_movie_data(db_helper):
    data = DataGenerator.generate_random_movie_for_api()

    # предусловие: такого фильма нет
    assert db_helper.get_movie_by_name(data.name) is None

    return data