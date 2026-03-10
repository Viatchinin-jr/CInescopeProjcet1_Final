
from db_models.db_user import UserDBModel
from db_requester.db_client import get_db_session
from utils.data_generator import DataGenerator

class TestDb:

    def test_db_requests(self, db_helper, created_test_user):
        user_from_db = db_helper.get_user_by_id(created_test_user.id)

        assert user_from_db is not None
        assert user_from_db.id == created_test_user.id
        assert user_from_db.email == created_test_user.email
        assert db_helper.users_exists_by_email(created_test_user.email)

    def test_movie_request(self, api_manager, created_test_movie):
        # Сначала проверяем, что в базе нет фильма
        try_get = api_manager.movies_api.get_movie_by_id(created_test_movie.id)
        assert try_get.status_code == 400

    def test_movie_before_created(self, db_helper, non_exist_movie_data):
        assert db_helper.get_movie_by_name(non_exist_movie_data["name"]) is None

    def test_movie_created_after_request(self, db_helper, non_exist_movie_data, super_admin):
        # 1) ДО: В БД фильма нет
        assert db_helper.get_movie_by_name(non_exist_movie_data.name) is None

        movie_id = None
        try:
            # 2) Создание через API
            resp = super_admin.api.movies_api.create_movie(non_exist_movie_data)
            assert resp.status_code == 201
            movie_id = int(resp.json()["id"])


            # 3) Проверка, что в БД появился фильм
            movie_from_db = db_helper.get_movie_by_name(non_exist_movie_data.name)
            assert movie_from_db is not None
            assert int(movie_from_db.id) == movie_id

            # 4) Удаление через API
            del_resp = super_admin.api.movies_api.delete_movie(movie_id)
            assert del_resp.status_code in (200, 204)

            # 5) После удаления: в БД фильма нет
            assert db_helper.get_movie_by_name(non_exist_movie_data.name) is None

        finally:
            # страхуемся, если тест упал ДО удаления или API не сработало
            insurance = db_helper.get_movie_by_name(non_exist_movie_data.name)
            if insurance:
                db_helper.delete_movie(insurance)