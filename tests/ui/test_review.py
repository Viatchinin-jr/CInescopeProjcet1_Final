import time
from playwright.sync_api import sync_playwright, Page
import allure
import pytest
from models.page_action import CinescopLoginPage
from models.page_action import MoviePage
from models.page_action import  MainPage


@allure.epic("Тестирование UI")
@allure.feature("Отзывы к фильмам")
@allure.story("Добавление нового отзыва")
@pytest.mark.ui
class TestMovieReview:

    @allure.title("Успешное оставление отзыва")
    def test_send_review(self, page: Page, registered_user):

        with allure.step("Авторизация пользователя"):
            login_page = CinescopLoginPage(page)
            login_page.open()
            login_page.login(registered_user.email, registered_user.password)
            login_page.assert_was_redirect_to_home_page()

        with allure.step("Переход к странице фильма"):
            main_page = MainPage(page)
            main_page.open_first_movie()

        with allure.step("Оставление отзыва"):
            movie_page = MoviePage(page)
            review_text = "Фильм бомба"
            movie_page.enter_review_text(review_text)

        with allure.step("Выставление оценки"):
            movie_page.select_rating(5)

        with allure.step("Отправка оценки"):
            movie_page.send_review()

        with allure.step("Верификация результата"):
            movie_page.check_pop_up_element_with_text("Отзыв успешно создан")
            movie_page.make_screenshot_and_attach_to_allure()

