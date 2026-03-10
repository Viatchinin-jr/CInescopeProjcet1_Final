from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from resources.db_creds import MovieDbCreds
# 1. Импортируем общий Base
from db_models.base import Base

# 2. Импортируем все модели
from db_models.transaction_model import AccountTransactionTemplate
from db_models.db_token import TokenDbModel
from db_models.db_user import UserDBModel
from db_models.db_movies import MoviesDBModel

# Константы для подключения
USERNAME = MovieDbCreds.USER
PASSWORD = MovieDbCreds.PASSWORD
HOST = MovieDbCreds.HOST
PORT = MovieDbCreds.PORT
DATABASE_NAME = MovieDbCreds.DBNAME

# 1. Движок для подключения к базе данных
engine = create_engine(
    f"postgresql+psycopg2://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DATABASE_NAME}",
    echo=False # Установить True для отладки SQL запросов
)

# Это строка создаст все таблицы (users, movies, tokens), если их нет в БД
Base.metadata.create_all(bind=engine)

# создаем фабрику сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session() -> Session:
    """
    Создает новую сессию для работы с БД
    """
    return SessionLocal()

def get_confirmation_token_by_email(email: str) -> str | None:
    """
    Автоматически находит последний токен подтверждения для пользователя.
    Используется в позитивном тесте регистрации.
    """
    session = get_db_session()
    try:
        # Ищем по email
        db_record = session.query(TokenDbModel).filter(
            TokenDbModel.email == email
        ).first()
        return db_record.token if db_record else None
    finally:
        session.close()
