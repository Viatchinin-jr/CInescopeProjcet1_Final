import random
import string
from faker import Faker
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
    def generate_random_movie():
        """
        Генерация фильма
        :return:
        """
        data = {
            "name": faker.sentence(nb_words=2).rstrip("."),
            "imageUrl": "https://image.url",
            "price": faker.random_int(100, 400),
            "description": faker.text(max_nb_chars=10),
            "location": random.choice(["MSK", "SPB"]),
            "published": True,
            "genreId": 1
        }
        return data

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