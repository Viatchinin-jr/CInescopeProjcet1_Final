import time
from playwright.sync_api import sync_playwright, Page
import allure
import pytest
from models.page_action import CinescopLoginPage


@allure.epic("Тестирование UI")
@allure.feature("Авторизация")
@pytest.mark.ui
class TestLoginPage:

   @allure.title("Проведение успешного входа в систему")
   def test_login_by_ui(self, page: Page, registered_user):
       """
       Тест проверяет возможность входа в аккаунт с валидными учетными данными.
       Пользователь предварительно создается через API-фикстуру.
       """
       login_page = CinescopLoginPage(page)

       with allure.step("Подготовка: переход на страницу входа."):
           login_page.open()

       with allure.step("Авторизация пользователя"):
           login_page.login(registered_user.email, registered_user.password)

       with allure.step("Верификация: проверка редиректа и уведомления"):
           login_page.assert_was_redirect_to_home_page()
           login_page.make_screenshot_and_attach_to_allure()
           login_page.assert_allert_was_pop_up()

