import os
from dotenv import load_dotenv

load_dotenv()

class MovieDbCreds:
    HOST = os.getenv("DB_MOVIES_HOST")
    PORT = os.getenv("DB_MOVIES_PORT")
    DBNAME = os.getenv("DB_MOVIES_NAME")
    USER = os.getenv("DB_MOVIES_USER")
    PASSWORD = os.getenv("DB_MOVIES_USER_PASSWORD")

