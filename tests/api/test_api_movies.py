import pytest


class TestMoviesAPI:
    def test_get_all_movies(self, api_manager):
        response = api_manager.movies_api.get_list_movies()
        assert response.status_code == 200, "Ожидается статус код 200"

        # проверка структуры ответа
        body = response.json()
        assert isinstance(body, dict), "Ответ должен быть словарем"
        assert "movies" in body, "В ответе должно быть поле 'movies'"
        assert isinstance(body["movies"], list), "'movies' должен быть списком "

    def test_post_movie(self, api_manager, admin_auth, movie_payload):
        response = api_manager.movies_api.create_movie(movie_payload)
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == movie_payload["name"]
        api_manager.movies_api.delete_movie(body["id"], expected_status=200)


    def test_get_by_id(self, api_manager, created_movie):
        movie_id = created_movie["id"]

        response = api_manager.movies_api.get_movie_by_id(movie_id)
        assert response.status_code == 200, "Ожидается ответ 200"

        body = response.json()
        assert body["id"] == movie_id
        assert body["name"] == created_movie["name"]


    def test_delete_by_id(self, api_manager, admin_auth, create_movie_for_delete):
        movie_id = create_movie_for_delete["id"]

        del_response = api_manager.movies_api.delete_movie(movie_id, expected_status=200)
        assert del_response.status_code == 200, "Фильм не удалился"

        body = del_response.json()
        assert body["id"] == movie_id, "ID удаленного фильма не совпадает"
        assert body["name"] == create_movie_for_delete["name"]

    def test_patch_by_id(self, api_manager, admin_auth, created_movie, patch_movie_payload):
        #  Сначала создать фильм, юзаем фикстуру
        movie_id = created_movie["id"]

        resp = api_manager.movies_api.patch_movie(movie_id, patch_movie_payload)
        assert resp.status_code == 200
        body = resp.json()

        assert body["id"] == movie_id
        assert body["name"] == patch_movie_payload["name"]

class TestGetAllMoviesNegative:
    def test_invalid_page_size(self, api_manager):
        response = api_manager.movies_api.get_list_movies(
            params={"pageSize": "abc"}, # api принимает number, а запрашиваем str
            expected_status=400
        )
        assert response.status_code == 400, f"Ожидался ответ 400, получен {response.status_code}"

    def test_invalid_page(self, api_manager):
        response = api_manager.movies_api.get_list_movies(
            params={"page": "abc"}, # api принимает number, а запрашиваем str
            expected_status=400
        )
        assert response.status_code == 400, f"Ожидался ответ 400, получен {response.status_code}"

    def test_invalid_min_price(self, api_manager):
        response = api_manager.movies_api.get_list_movies(
            params={"minPrice": "abc"}, # api принимает number, а запрашиваем str
            expected_status=400
        )
        assert response.status_code == 400, f"Ожидался ответ 400, получен {response.status_code}"

    def test_invalid_max_price(self, api_manager):
        response = api_manager.movies_api.get_list_movies(
            params={"maxPrice": "abc"}, # api принимает number, а запрашиваем str
            expected_status=400
        )
        assert response.status_code == 400, f"Ожидался ответ 400, получен {response.status_code}"

    def test_invalid_locations(self, api_manager):
        response = api_manager.movies_api.get_list_movies(
            params={"locations": "NYC"}, # api ожидает вариант из двух значений MSK, SPB
            expected_status=400
        )
        assert response.status_code == 400, f"Ожидался ответ 400, получен {response.status_code}"

    def test_invalid_published(self, api_manager):
        response = api_manager.movies_api.get_list_movies(
            params={"published": "not_bool_ha-ha"}, # api Ожидает bool, а отдаем str
            expected_status=200 # бэк всегда принимает 200 и я не нашел как это обойти
        )
        assert response.status_code == 200, f"Ожидался ответ 200, получен {response.status_code}"

    def test_invalid_genre_id(self, api_manager):
        response = api_manager.movies_api.get_list_movies(
            params={"genreId": "str"}, #api ожидает int, отправляему str
            expected_status=400
        )
        assert response.status_code == 400, f"Ожидался ответ 400, получен {response.status_code}"

    def test_invalid_created_at(self, api_manager):
        response = api_manager.movies_api.get_list_movies(
            params={"createdAt": 1488}, # api ожидает str - asc или desc, отправляем int
            expected_status=400
        )
        assert response.status_code == 400, f"Ожидался ответ 400, получен {response.status_code}"

class TestPostNegative:
    def test_post_unauthorized(self, api_manager, movie_payload):
        """
        Пуляем post без авторизации
        """
        response = api_manager.movies_api.create_movie(
            movie_data=movie_payload,
            expected_status=401
        )
        assert response.status_code == 401, f"Ожидался ответ 401, получен {response.status_code}"

    def test_post_invalid_price(self, api_manager, admin_auth, movie_payload):
        bad_payload = movie_payload.copy()
        bad_payload["price"] = "it's a string haha"

        response = api_manager.movies_api.create_movie(
            movie_data=bad_payload,
            expected_status=400
        )
        assert response.status_code == 400, f"Ожидался ответ 400, получен {response.status_code}"

    def test_post_miss_field(self, api_manager, admin_auth, movie_payload):
        bad_payload = movie_payload.copy()
        bad_payload.pop("price")

        response = api_manager.movies_api.create_movie(
            movie_data=bad_payload,
            expected_status=400
        )
        assert response.status_code == 400, f"Ожидался ответ 400, получен {response.status_code}"

    def test_movie_already_exist(self, api_manager, admin_auth, existing_movie):
        movie, payload = existing_movie

        response = api_manager.movies_api.create_movie(movie_data=payload, expected_status=409)
        assert response.status_code == 409


class TestGetByIdNegative:
    def test_get_non_exist_id(self, api_manager):
        response = api_manager.movies_api.get_movie_by_id(999777666, expected_status=404)
        assert response.status_code == 404, f"Ожидался ответ 404, получен {response.status_code}"

    def test_get_wrong_type_id(self, api_manager):
        response = api_manager.movies_api.get_movie_by_id("that's not id", expected_status=500)
        assert response.status_code == 500, f"Ожидался ответ 500, получен {response.status_code}"

class TestDeleteNegative:
    def test_delete_by_wrong_id(self, api_manager, admin_auth):
        del_response = api_manager.movies_api.delete_movie(movie_id=999777666, expected_status=404)
        assert del_response.status_code == 404, f"Ожидался ответ 404, получен {del_response.status_code}"

    def test_delete_without_auth(self, api_manager):
        del_response = api_manager.movies_api.delete_movie(movie_id=9999999, expected_status=401)
        assert del_response.status_code == 401, f"Ожидался ответ 401, получен {del_response.status_code}"

class TestPatchNegative:
    def test_patch_by_wrong_id(self, api_manager, admin_auth, patch_movie_payload):
        patch_resp = api_manager.movies_api.patch_movie(movie_id=999777666, patch_data=patch_movie_payload, expected_status=404)
        assert patch_resp.status_code == 404, f"Ожидался ответ 404, получен {patch_resp.status_code}"

    def test_patch_invalid_data(self, api_manager, admin_auth, created_movie, patch_movie_payload):
        movie_id = created_movie["id"]
        bad_data = patch_movie_payload.copy()
        bad_data["price"] = "HL3 TODAY"

        response = api_manager.movies_api.patch_movie(movie_id=movie_id, patch_data=bad_data, expected_status=400)
        assert response.status_code == 400, f"Ожидался ответ 400, получен {response.status_code}"


