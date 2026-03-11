import pytest
import allure
from models.movies_model import MovieResponse


@allure.epic("Интеграция с БД")
@allure.feature("Валидация данных с БД")
@pytest.mark.db
class TestDb:

    @allure.story("Пользователи в БД")
    @allure.title("Проверка существования созданного пользователя в БД")
    def test_db_requests(self, db_helper, created_test_user):
        with allure.step(f"Запрос пользователя из БД по ID: {created_test_user.id}"):
            user_from_db = db_helper.get_user_by_id(created_test_user.id)

        with allure.step("Проверка корректности данных в БД"):
            assert user_from_db is not None
            assert user_from_db.id == created_test_user.id
            assert user_from_db.email == created_test_user.email
            assert db_helper.users_exists_by_email(created_test_user.email)

    @allure.story("Фильмы в БД")
    @allure.title("Синхронизация данных фильма: API и БД")
    def test_movie_request(self, api_manager, db_helper, created_test_movie):
        with allure.step(f"Запрос фильма через API по ID: {created_test_movie.id}"):
            response = api_manager.movies_api.get_movie_by_id(created_test_movie.id)
            assert response.status_code == 200

        with allure.step("Запрос того же фильма напрямую из БД"):
            movie_from_db = db_helper.get_movie_by_name(created_test_movie.name)

        with allure.step("Сверка данных API и БД"):
            assert movie_from_db is not None
            assert str(movie_from_db.id) == str(created_test_movie.id)


    @allure.story("Фильмы в БД")
    @allure.title("Проверка отсутствия фильма в БД до создания")
    def test_movie_before_created(self, db_helper, non_exist_movie_data):
        with allure.step(f"Поиск фильма '{non_exist_movie_data.name}'"):
            movie = db_helper.get_movie_by_name(non_exist_movie_data.name)
            assert movie is None


    @allure.story("Фильмы в БД")
    @allure.title("Полный цикл: создание через API -> проверка в БД -> удаление")
    def test_movie_created_after_request(self, db_helper, non_exist_movie_data, super_admin):
        with allure.step("Предусловие: убеждаемся, что фильма нет в БД"):
            assert db_helper.get_movie_by_name(non_exist_movie_data.name) is None

        movie_id = None
        try:
            with allure.step("Создание фильма через API"):
                resp = super_admin.api.movies_api.create_movie(non_exist_movie_data)
                assert resp.status_code == 201
                movie_id = int(resp.json()["id"])

            with allure.step("Проверка появления фильма в БД"):
                movie_from_db = db_helper.get_movie_by_name(non_exist_movie_data.name)
                assert movie_from_db is not None
                assert int(movie_from_db.id) == movie_id

            with allure.step(f"Удаление фильма через API по ID: {movie_id}"):
                del_resp = super_admin.api.movies_api.delete_movie_by_id(movie_id)
                assert del_resp.status_code in (200, 204)

            with allure.step("Проверка исчезновения фильма из БД"):
                assert db_helper.get_movie_by_name(non_exist_movie_data.name) is None

        finally:
            with allure.step("Cleanup: страховочное удаление из БД"):
                insurance = db_helper.get_movie_by_name(non_exist_movie_data.name)
                if insurance:
                    db_helper.delete_movie(insurance)