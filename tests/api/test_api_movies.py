import pytest
import allure
from models.movies_model import GetListMoviesParams, GetListMoviesResponse, ErrorResponse, MovieCreateRequest, \
    MovieResponse, MovieDetailResponse


@allure.epic("Сервис Movies")
@allure.feature("Операции CRUD (Позитивные)")
@pytest.mark.api
@pytest.mark.movies
@pytest.mark.positive
class TestMoviesAPI:

    @pytest.mark.parametrize(
        "filter_params",
        [
            GetListMoviesParams(min_price=1, max_price=1000, locations=["MSK"], genre_id=1),
            GetListMoviesParams(min_price=1, max_price=1000, locations=["SPB"], genre_id=1),
            GetListMoviesParams(min_price=100, max_price=300, locations=["MSK"], genre_id=2)
        ],
        ids=["MSK 1-1000", "SPB 1-1000", "MSK 100-300 (Genre 2)"]
    )
    @allure.story("Фильтрация списка фильмов")
    @pytest.mark.smoke
    @pytest.mark.positive
    @allure.title("Позитивный тест фильтрации списка фильмов")
    def test_get_all_movies(self, common_user, filter_params, check):
        with allure.step(f"Запрос списка фильмов с фильтрами: {filter_params.model_dump(exclude_unset=True)}"):
            response = common_user.api.movies_api.get_list_movies(params=filter_params, expected_status=200)

        with allure.step("Валидация структуры ответа моделью GetListMoviesParams"):
            data = GetListMoviesResponse.model_validate(response.json())

        with allure.step("Проверка работы фильтров на бэкенде"):
            if not data.movies:
                allure.dynamic.description("Внимание: по заданным фильтрам фильмы не найдены")
                return

            for movie in data.movies:
                with check:
                    check.greater_equal(movie.price, filter_params.min_price, f"Цена фильма {movie.id} меньше minPrice")
                    check.less_equal(movie.price, filter_params.max_price, f"Цена фильма {movie.id} больше maxPrice")

                    if filter_params.locations:
                        check.is_in(movie.location, filter_params.locations, f"Локация фильма {movie.id} не входит в фильтр")

                    if filter_params.genre_id:
                        check.equal(movie.genre_id, filter_params.genre_id, f"Жанр фильма {movie.id} не совпадает")

    @allure.story("Создание фильма")
    @pytest.mark.smoke
    @pytest.mark.positive
    @allure.title("Успешное создание фильма администратором")
    def test_create_movie(self, super_admin, movie_payload, movie_cleanup, check):
        with allure.step(f"Запроос POST /movies с данными: {movie_payload.name}"):
            response = super_admin.api.movies_api.create_movie(movie_payload)

        with allure.step("Валидация ответа"):
            data = MovieResponse.model_validate(response.json())
            movie_cleanup.append(data.id)
            with check:
                check.equal(data.name, movie_payload.name, "Имя не совпало")
                check.equal(data.price, movie_payload.price, "Цена не совпала")
                check.equal(data.location, movie_payload.location, "Локация не совпала")
                check.equal(data.genre_id, movie_payload.genre_id, "ID жанра не совпал")
                check.is_instance(data.id, int, "ID должен быть числом")

    @allure.story("Детальная информация о фильме")
    @pytest.mark.smoke
    @pytest.mark.positive
    @allure.title("Успешное получение деталей фильма по ID")
    def test_get_by_id(self, super_admin, movie_payload, movie_cleanup, check):
        with allure.step("Подготовка: создание тестового фильма"):
            create_resp = super_admin.api.movies_api.create_movie(movie_payload)
            movie_id = create_resp.json()["id"]
            movie_cleanup.append(movie_id)

        with allure.step(f"Запрашиваем GET по ID {movie_id}"):
            get_resp = super_admin.api.movies_api.get_movie_by_id(movie_id, expected_status=200)
            data = MovieDetailResponse.model_validate(get_resp.json())

        with allure.step("Проверяем данные в ответе с созданным фильмом"):
            with check:
                check.equal(data.name, movie_payload.name, "Имя не совпало")
                check.equal(data.price, movie_payload.price, "Цена не совпала")
                check.equal(data.location, movie_payload.location, "Локация не совпала")
                check.equal(data.genre_id, movie_payload.genre_id, "Жанр не совпал")
                check.is_instance(data.reviews, list, "Поле reviews должно быть списком")
                check.equal(len(data.reviews), 0, "У нового фильма не должно быть отзывов")

    @allure.story("Удаление фильма")
    @pytest.mark.smoke
    @pytest.mark.positive
    @allure.title("Успешное удаление фильма по ID")
    def test_delete_by_id_200(self, super_admin, movie_payload, check):
        with allure.step("Подготовка: создание тестового фильма"):
            resp = super_admin.api.movies_api.create_movie(movie_payload, expected_status=201)
            movie_id = resp.json()["id"]

        with allure.step(f"Удаление фильма: {movie_id}"):
            del_resp = super_admin.api.movies_api.delete_movie_by_id(movie_id, expected_status=200)
            deleted_data = MovieResponse.model_validate(del_resp.json())

        with allure.step("Проверка: в ответе DELETE вернулись данные удаленного фильма"):
            check.equal(deleted_data.id, movie_id, "ID в ответе не совпадет")
            check.equal(deleted_data.name, movie_payload.name, "Имя фильма не совпадает")

        with allure.step("Повторный GET-запрос по этому ID возвращает 404"):
            get_resp = super_admin.api.movies_api.get_movie_by_id(movie_id, expected_status=404)

    @allure.story("Частичное обновление фильма")
    @pytest.mark.smoke
    @pytest.mark.positive
    @allure.title("Тест на PATCH (имя и цена)")
    def test_patch_by_id(self, super_admin, movie_payload, patch_movie_payload, movie_cleanup, check):
        with allure.step("Подготовка: создание фильма для теста"):
            create_resp = super_admin.api.movies_api.create_movie(movie_payload, expected_status=201)
            movie_id = create_resp.json()["id"]
            movie_cleanup.append(movie_id)

        with allure.step(f"Действие: PATCH /movies/{movie_id} со случайными данными"):
            patch_resp = super_admin.api.movies_api.patch_movie_by_id(movie_id, patch_movie_payload, expected_status=200)
            updated_data = MovieResponse.model_validate(patch_resp.json())

        with allure.step("Проверка: данные в ответе должны соответсвовать патчу и исходным данным"):
            actual_data_subset = updated_data.model_dump(
                include=set(patch_movie_payload.keys()),
                by_alias=True
            )
            check.equal(actual_data_subset, patch_movie_payload, "Данные в ответе не совпадают с патчем")

@allure.epic("Сервис Movies")
@allure.feature("Обработка ошибок: GET (Negative)")
@pytest.mark.movies
@pytest.mark.negative
class TestGetAllMoviesNegative:

    @pytest.mark.parametrize(
        "invalid_params, expected_error_field",
        [
            ({"pageSize": "abc"}, "pageSize"),
            ({"page": "abc"}, "page"),
            ({"minPrice": "abc"}, "micePrice"),
            ({"maxPrice": "abc"}, "maxPrice"),
            ({"locations": "NYC"}, "locations"),
            ({"genreId": "str"}, "genreId"),
            ({"createdAt": 1488}, "createdAt"),
        ],
        ids=[
            "pageSize as string",
            "page as string",
            "minPrice as string",
            "maxPrice as string",
            "invalid locations value",
            "genreId as string",
            "createdAt as number"
        ]
    )
    @allure.story("Валидация query-параметров")
    @allure.title("Негативный тест фильтрации: ожидаем 400 Bad Request")
    def test_get_all_movies_negative_400(self, common_user, invalid_params, expected_error_field, check):
        with allure.step(f"Запрос списка фильмов с некорректным параметром: {invalid_params}"):
            response = common_user.api.movies_api.get_list_movies(invalid_params, expected_status=400)

        with allure.step("Валидация тела ответа моделью ошибки"):
            error_data = ErrorResponse.model_validate(response.json())

            with check:
                check.equal(error_data.statusCode, 400, "Код в теле ответа должен быть 400!")

    @allure.story("Валидация поля published")
    @pytest.mark.xfail(reason="Баг? Бэкенд возвращает 200")
    @allure.title("Негативный тест: невалидное поле published (BUG)")
    def test_invalid_published_type(self, common_user):
        response = common_user.api.movies_api.get_list_movies(
            params={"published": "abc"},
            expected_status=400
        )
@allure.epic("Сервис Movies")
@allure.feature("Обработка ошибок: POST /movies")
@pytest.mark.movies
@pytest.mark.negative
class TestPostNegative:
    @pytest.mark.parametrize(
        "invalid_data, expected_error_text",
        [
            ({"name": ""}, "name"),
            ({"price": "-100"}, "price"),
            ({"location": "LONDON"}, "location"),
            ({"genreId": 9999}, "Некорректные данные"),
            ({"imageUrl": "not-a-url"}, "Неверная ссылка"),
        ],
        ids=["empty name", "negative price", "invalid location", "non_existent genre", "invalid imageUrl"]
    )
    @allure.story("Валидация полей при создании")
    @allure.title("Негативный тест создания фильма: 400 Bad Request")
    def test_create_movie_400(self, super_admin, movie_payload, invalid_data, expected_error_text, check):
        payload = movie_payload.model_dump(by_alias=True)
        payload.update(invalid_data)

        with allure.step(f"Запрос POST /movies с невалидным полем {expected_error_text}"):
            response = super_admin.api.movies_api.create_movie(payload, expected_status=400)

        with allure.step("Валидация ошибки"):
            error_data = ErrorResponse.model_validate(response.json())
            with check:
                check.equal(error_data.statusCode, 400)
                check.is_in(expected_error_text, str(error_data.message), f"Ожидали {expected_error_text} в ответе сервера")

    @allure.story("Проверка уникальности (дубликаты)")
    @allure.title("Негативный тест: создание дубликата фильма (409 Conflict)")
    def test_create_movie_409(self, super_admin, movie_payload, movie_cleanup, check):
        with allure.step(f"Создание первого фильма с именем {movie_payload.name}"):
            response_first = super_admin.api.movies_api.create_movie(movie_payload, expected_status=201)

            movie_data = MovieResponse.model_validate(response_first.json())
            movie_cleanup.append(movie_data.id)

        with allure.step("Попытка создания фильма с тем же названием (дубликат)"):
            response_duplicate = super_admin.api.movies_api.create_movie(movie_payload, expected_status=409)

        with allure.step("Валидация ответа 409"):
            error_data = ErrorResponse.model_validate(response_duplicate.json())

            with check:
                check.equal(error_data.statusCode, 409)
                check.equal(error_data.message, "Фильм с таким названием уже существует")
                check.equal(error_data.error, "Conflict")

@allure.epic("Сервис Movies")
@allure.feature("Обработка ошибок: GET /movies/{id}")
@pytest.mark.movies
@pytest.mark.negative
class TestGetByIdNegative:
    @allure.story("Поиск несуществующего фильма")
    @allure.title("Запрос по ID несуществующего фильма: ожидаем 404")
    def test_get_movie_404(self, super_admin, check):
        invalid_id = 14888841

        with allure.step(f"Запрос GET по ID: {invalid_id}"):
            response = super_admin.api.movies_api.get_movie_by_id(invalid_id, expected_status=404)

        with allure.step("Валидация ошибки и полей"):
            error_data = ErrorResponse.model_validate(response.json())
            with check:
                check.equal(error_data.statusCode, 404)


@allure.epic("Сервис Movies")
@allure.feature("Обработка ошибок: DELETE /movies/{id}")
@pytest.mark.movies
@pytest.mark.negative
class TestDeleteNegative:
    @allure.story("Повторное удаление")
    @allure.title("Повторное удаление фильма: 404 Not Found")
    def test_delete_by_id_404(self, super_admin, movie_payload, check):
        with allure.step("Подготовка: создание и первое удаление фильма"):
            resp = super_admin.api.movies_api.create_movie(movie_payload, expected_status=201)
            movie_id = resp.json()["id"]
            first_del = super_admin.api.movies_api.delete_movie_by_id(movie_id, expected_status=200)

        with allure.step(f"Повторный запрос DELETE /movies/{movie_id}"):
            response = super_admin.api.movies_api.delete_movie_by_id(movie_id, expected_status=404)

        with allure.step("Валидация ошибок 404"):
            error_data = ErrorResponse.model_validate(response.json())
            with check:
                check.equal(error_data.statusCode, 404)
                check.equal(error_data.message, "Фильм не найден")
                check.equal(error_data.error, "Not Found")

    @allure.story("Валидация формата ID")
    @allure.title("Удаление фильма с некорректным ID: 400 Bad Request")
    @pytest.mark.xfail(reason="Баг? Возвращает 404 вместо 400 на неверный тип данных.")
    def test_delete_by_invalid_id_400(self, super_admin, check):
        invalid_id = "abc-123-stack"

        with allure.step(f"Запрос DELETE /movies/{invalid_id}"):
            response = super_admin.api.movies_api.delete_movie_by_id(invalid_id, expected_status=400)


@allure.epic("Сервис Movies")
@allure.feature("Негативные тесты на PATCH")
@pytest.mark.movies
@pytest.mark.negative
class TestPatchNegative:

    @allure.story("Обновление несуществующего фильма")
    @allure.title("Обновление несуществующего фильма: 404 Not Found")
    def test_patch_movie_404(self, super_admin, patch_movie_payload, check):
        invalid_id = 9991488899

        with allure.step(f"Запрос PATCH /movies/{invalid_id}"):
            response = super_admin.api.movies_api.patch_movie_by_id(invalid_id, patch_movie_payload, expected_status=404)

        with allure.step("Валидация ошибки 404"):
            error_data = ErrorResponse.model_validate(response.json())
            with check:
                check.equal(error_data.statusCode, 404)
                check.equal(error_data.message, "Фильм не найден")
                check.equal(error_data.error, "Not Found")

    @allure.story("Валидация типов данных при PATCH")
    @allure.title("Обновление некорректными данными: 400 Bad Request")
    def test_patch_with_invalid_data_400(self, super_admin, movie_payload, patch_movie_payload, movie_cleanup, check):
        with allure.step("Создаем фильм который будем обновлять"):
            response = super_admin.api.movies_api.create_movie(movie_payload, expected_status=201)
            movie_id = response.json()["id"]
            movie_cleanup.append(movie_id)

        bad_payload = {"price": "free"}

        with allure.step(f"Запрос PATCH /movies/{movie_id} с некорректными типом цены"):
            response = super_admin.api.movies_api.patch_movie_by_id(movie_id, bad_payload, expected_status=400)

        with allure.step("Валидация ошибки 400"):
            error_data = ErrorResponse.model_validate(response.json())
            with check:
                check.equal(error_data.statusCode, 400)
                check.equal(error_data.error, "Bad Request")
                check.is_in("price", str(error_data.message).lower())
