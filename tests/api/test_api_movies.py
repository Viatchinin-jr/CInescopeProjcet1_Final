import pytest

class TestMoviesAPI:
    def test_get_all_movies(self, common_user):
        response = common_user.api.movies_api.get_list_movies()
        assert response.status_code == 200, "Ожидается статус-код 200"

        # Проверка структуры ответа
        body = response.json()
        assert "movies" in body, "В ответе должно быть поле 'movies'"
        assert isinstance(body["movies"], list), "'movies' должен быть списком"

    @pytest.mark.parametrize(
        "min_price,max_price,location,genre_id",
        [
            (1, 1000, "MSK", 1),
            (1, 1000, "SPB", 1),
            (100, 300, "MSK", 1),
        ],
        ids=[
            "MSK price 1-1000",
            "SPB price 1-1000",
            "MSK price 100-300"
        ]
    )
    def test_get_all_movies_with_params(self, common_user, min_price, max_price, location, genre_id):
        params = {
            "minPrice": min_price,
            "maxPrice": max_price,
            "locations":[location], # array, но с одним значением
            "genreId": genre_id
        }

        response = common_user.api.movies_api.get_list_movies(params=params)
        assert response.status_code == 200

        movies = response.json().get("movies", []) # парсим ответ в формате json и возвращаем в виде питон-словаря. безопасный доступ к ключу 'movies', если его нет вернутся пустой список
        assert isinstance(movies, list) # проверка типа данных. гарантирует, что movies - список

        for movie in movies: # список фильмов который вернул API. каждый movie это один фильм. цикл проверяет каждый вернувшийся фильм.
            assert min_price <= movie["price"] <= max_price # проверка фильтра minPrice-maxPrice. Цена должна быть внутри заданного диапазона.
            assert movie["location"] == location # проверка фильтра location. Проверяет: если в запросе было MSK - в ответе все фильмы должны быть location=MSK.
            assert movie["genreId"] == genre_id # проверка фильтра genreID. Проверяет, что вернулись только фильмы, соответсующие фильтру, в данном случае '1'.

    def test_post_movie(self, super_admin, movie_payload):
        response = super_admin.api.movies_api.create_movie(movie_payload)
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == movie_payload["name"]
        super_admin.api.movies_api.delete_movie(body["id"], expected_status=200)

    @pytest.mark.slow
    def test_get_by_id(self, common_user, created_movie):
        movie_id = created_movie["id"]

        response = common_user.api.movies_api.get_movie_by_id(movie_id)
        assert response.status_code == 200, "Ожидается ответ 200"

        body = response.json()
        assert body["id"] == movie_id
        assert body["name"] == created_movie["name"]


    def test_delete_by_id(self, super_admin, create_movie_for_delete):
        movie_id = create_movie_for_delete["id"]

        del_response = super_admin.api.movies_api.delete_movie(movie_id, expected_status=200)
        assert del_response.status_code == 200, "Фильм не удалился"

        body = del_response.json()
        assert body["id"] == movie_id, "ID удаленного фильма не совпадает"
        assert body["name"] == create_movie_for_delete["name"]

    @pytest.mark.parametrize("user_type, expected_status",
        [
            pytest.param(
                "super_admin",
                200,
                id="SUPER_ADMIN can delete"
            ),
            pytest.param(
                "admin_user",
                403,
                id="ADMIN cannot delete",
                marks=pytest.mark.slow
            ),
            pytest.param(
                "common_user",
                403,
                id="USER cannot DELETE",
                marks=pytest.mark.slow
            ),
        ]
    )
    def test_delete(self, request, super_admin, movie_payload, user_type, expected_status,):
        # Создаем фильм от имени супер админа (каждый прогон будет создавать свой фильм)
        create_response = super_admin.api.movies_api.create_movie(movie_payload)
        assert create_response.status_code == 201
        created = create_response.json()
        movie_id = created["id"]

        # Берем нужный тип юзера
        user_ex = request.getfixturevalue(user_type)

        # Пытаемся удалить фильм этим типом юзера
        del_response = user_ex.api.movies_api.delete_movie(movie_id,expected_status=expected_status)
        assert del_response.status_code == expected_status

        # Если удаление разрешено - проверяем тело ответа
        if expected_status == 200:
            body = del_response.json()
            assert body["id"] == movie_id
            assert body["name"] == created["name"]
        else:
            # Если не удалили - почистим за собой
            super_admin.api.movies_api.delete_movie(movie_id, expected_status=200)


    @pytest.mark.slow
    def test_patch_by_id(self, super_admin, created_movie, patch_movie_payload):
        # Используем заранее созданный фильм из фикстуры
        movie_id = created_movie["id"]

        resp = super_admin.api.movies_api.patch_movie(movie_id, patch_movie_payload)
        assert resp.status_code == 200
        body = resp.json()

        assert body["id"] == movie_id
        assert body["name"] == patch_movie_payload["name"]


class TestGetAllMoviesNegative:
    def test_invalid_page_size(self, common_user):
        response = common_user.api.movies_api.get_list_movies(
            params={"pageSize": "abc"},  # API ожидает число, передаем строку
            expected_status=400
        )
        assert response.status_code == 400, f"Ожидался ответ 400, получен {response.status_code}"

    def test_invalid_page(self, common_user):
        response = common_user.api.movies_api.get_list_movies(
            params={"page": "abc"},  # API ожидает число, передаем строку
            expected_status=400
        )
        assert response.status_code == 400, f"Ожидался ответ 400, получен {response.status_code}"

    def test_invalid_min_price(self, common_user):
        response = common_user.api.movies_api.get_list_movies(
            params={"minPrice": "abc"},  # API ожидает число, передаем строку
            expected_status=400
        )
        assert response.status_code == 400, f"Ожидался ответ 400, получен {response.status_code}"

    def test_invalid_max_price(self, common_user):
        response = common_user.api.movies_api.get_list_movies(
            params={"maxPrice": "abc"},  # API ожидает число, передаем строку
            expected_status=400
        )
        assert response.status_code == 400, f"Ожидался ответ 400, получен {response.status_code}"

    def test_invalid_locations(self, common_user):
        response = common_user.api.movies_api.get_list_movies(
            params={"locations": "NYC"},  # API ожидает одно из значений: MSK или SPB
            expected_status=400
        )
        assert response.status_code == 400, f"Ожидался ответ 400, получен {response.status_code}"

    def test_invalid_published(self, common_user):
        response = common_user.api.movies_api.get_list_movies(
            params={"published": "not_bool_value"},  # API ожидает bool, передаем строку
            expected_status=200  # бэкенд всегда возвращает 200, обойти не удалось
        )
        assert response.status_code == 200, f"Ожидался ответ 200, получен {response.status_code}"

    def test_invalid_genre_id(self, common_user):
        response = common_user.api.movies_api.get_list_movies(
            params={"genreId": "str"},  # API ожидает int, отправляем строку
            expected_status=400
        )
        assert response.status_code == 400, f"Ожидался ответ 400, получен {response.status_code}"

    def test_invalid_created_at(self, common_user):
        response = common_user.api.movies_api.get_list_movies(
            params={"createdAt": 1488},  # API ожидает строку "asc" или "desc", отправляем число
            expected_status=400
        )
        assert response.status_code == 400, f"Ожидался ответ 400, получен {response.status_code}"


class TestPostNegative:
    def test_post_unauthorized(self, unauthorized_api_manager, movie_payload):
        """
        Отправка POST-запроса без авторизации.
        """
        response = unauthorized_api_manager.movies_api.create_movie(
            movie_data=movie_payload,
            expected_status=401
        )
        assert response.status_code == 401, f"Ожидался ответ 401, получен {response.status_code}"

    def test_post_user_cannot_create_movie(self, common_user, movie_payload):
        # USER не может создавать фильм
        response_user = common_user.api.movies_api.create_movie(
            movie_payload,
            expected_status=403
        )
        assert response_user.status_code == 403


    def test_post_invalid_price(self, super_admin, movie_payload):
        bad_payload = movie_payload.copy()
        bad_payload["price"] = "invalid_price"

        response = super_admin.api.movies_api.create_movie(
            movie_data=bad_payload,
            expected_status=400
        )
        assert response.status_code == 400, f"Ожидался ответ 400, получен {response.status_code}"

    def test_post_miss_field(self, super_admin, movie_payload):
        bad_payload = movie_payload.copy()
        bad_payload.pop("price")

        response = super_admin.api.movies_api.create_movie(
            movie_data=bad_payload,
            expected_status=400
        )
        assert response.status_code == 400, f"Ожидался ответ 400, получен {response.status_code}"

    def test_movie_already_exist(self, super_admin, existing_movie):
        movie, payload = existing_movie

        response = super_admin.api.movies_api.create_movie(movie_data=payload, expected_status=409)
        assert response.status_code == 409


class TestGetByIdNegative:
    @pytest.mark.slow
    def test_get_non_exist_id(self, common_user):
        response = common_user.api.movies_api.get_movie_by_id(999777666, expected_status=404)
        assert response.status_code == 404, f"Ожидался ответ 404, получен {response.status_code}"

    def test_get_wrong_type_id(self, common_user):
        response = common_user.api.movies_api.get_movie_by_id("invalid_id", expected_status=500)
        assert response.status_code == 500, f"Ожидался ответ 500, получен {response.status_code}"


class TestDeleteNegative:
    def test_delete_by_wrong_id(self, super_admin):
        del_response = super_admin.api.movies_api.delete_movie(movie_id=999777666, expected_status=404)
        assert del_response.status_code == 404, f"Ожидался ответ 404, получен {del_response.status_code}"

    def test_delete_without_auth(self, unauthorized_api_manager):
        del_response = unauthorized_api_manager.movies_api.delete_movie(movie_id=9999999, expected_status=401)
        assert del_response.status_code == 401, f"Ожидался ответ 401, получен {del_response.status_code}"


class TestPatchNegative:
    def test_patch_by_wrong_id(self, super_admin, patch_movie_payload):
        patch_resp = super_admin.api.movies_api.patch_movie(movie_id=999777666, patch_data=patch_movie_payload, expected_status=404)
        assert patch_resp.status_code == 404, f"Ожидался ответ 404, получен {patch_resp.status_code}"

    def test_patch_invalid_data(self, super_admin, created_movie, patch_movie_payload):
        movie_id = created_movie["id"]
        bad_data = patch_movie_payload.copy()
        bad_data["price"] = "invalid_price"

        response = super_admin.api.movies_api.patch_movie(movie_id=movie_id, patch_data=bad_data, expected_status=400)
        assert response.status_code == 400, f"Ожидался ответ 400, получен {response.status_code}"


