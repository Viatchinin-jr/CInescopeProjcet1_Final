import datetime
import random
import string
from faker import Faker

from models.movies_model import MovieCreateRequest

faker = Faker()


class DataGenerator:

    @staticmethod
    def generate_random_email():
        random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"kek{random_string}@gmail.com"

    @staticmethod
    def generate_random_name():
        return f"{faker.first_name()} {faker.last_name()}"

    @staticmethod
    def generate_random_password():
        """
        Генерация пароля, соответствующего требованиям:
        - Минимум 1 буква.
        - Минимум 1 цифра.
        - Допустимые символы
        - Длина от 8 до 20 символов.
        """
        # Гарантируем наличие хотя бы одной буквы и одной цифры
        letters = random.choice(string.ascii_letters) # одна буква
        digits = random.choice(string.digits) # одна цифра

        # Дополняем пароль случайными символами из допустимого набора
        special_chars = "?@#$%^&*|:"
        all_chars = string.ascii_letters + string.digits + special_chars
        remaining_length = random.randint(6, 18) # Остальная длина пароля
        remaining_chars = ''.join(random.choices(all_chars, k=remaining_length))

        # Перемешиваем пароль для рандомизации
        password = list(letters + digits + remaining_chars)
        random.shuffle(password)

        return ''.join(password)

    @staticmethod
    def generate_random_movie() -> dict:
        """
        Генерация фильма
        """
        return {
            "name": faker.sentence(nb_words=2).rstrip("."),
            "price": faker.random_int(100, 400),
            "description": faker.text(max_nb_chars=10),
            "image_url": "https://image.url",
            "location": random.choice(["MSK", "SPB"]),
            "published": True,
            "rating": round(random.uniform(0,100), 1),
            "genre_id": 1,
            "created_at": datetime.datetime.now()
        }

    @staticmethod
    def generate_random_movie_for_api() -> MovieCreateRequest:
        data = DataGenerator.generate_random_movie()
        data.pop("created_at", None)
        return MovieCreateRequest(**data)

    @staticmethod
    def generate_random_patch_data():
        """
        Генерация рандомных данных для patch запроса
        """
        data = {
            "name": faker.sentence(nb_words=2).rstrip("."),
            "price": faker.random_int(100, 400),
            "description": faker.text(max_nb_chars=10),
        }
        return data


    @staticmethod
    def generate_user_data() -> dict:
        """Генерирует данные для тестового пользователя, которые можно сразу передать в метод создания юзера через ДБ"""
        from uuid import uuid4

        return {
            'id': f"{uuid4()}", # генерируем UUID как строку
            'email': DataGenerator.generate_random_email(),
            'full_name': DataGenerator.generate_random_name(),
            'password': DataGenerator.generate_random_password(),
            'created_at': datetime.datetime.now(),
            'updated_at': datetime.datetime.now(),
            'verified': False,
            'banned': False,
            'roles': '{USER}'
        }

    @staticmethod
    def generate_random_int(min_value: int = 0, max_value: int = 100) -> int:
        """Генерирует случайно число в диапазоне от 1 до 100"""
        return random.randint(min_value, max_value)